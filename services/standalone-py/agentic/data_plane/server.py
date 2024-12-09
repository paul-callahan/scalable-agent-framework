"""
Data plane service implementation.

This module implements the DataPlaneService gRPC server that handles
persistence of execution records to storage.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import grpc
from google.protobuf import json_format

try:
    from ..pb import services_pb2, services_pb2_grpc, common_pb2
    from ..pb import task_pb2, plan_pb2
except ImportError:
    # Protobuf files not yet generated
    pass

from ..core.logging import configure_logging, get_logger, log_request_response, log_metric, log_error
from ..core.health import HealthCheckService, HealthCheckServicer, managed_server
from ..core.http_health import start_health_server


class DataPlaneService(services_pb2_grpc.DataPlaneServiceServicer):
    """
    Data plane service implementation.
    
    Handles persistence of TaskExecution and PlanExecution records to storage.
    Uses SQLite for MVP implementation.
    """
    
    def __init__(self, db_path: str = "agentic_data.db", health_service: Optional[HealthCheckService] = None):
        """
        Initialize the data plane service.
        
        Args:
            db_path: Path to the SQLite database file
            health_service: Optional health check service
        """
        self.db_path = db_path
        self.health_service = health_service
        self.logger = get_logger(__name__)
        
        # Initialize metrics
        self._request_count = 0
        self._error_count = 0
        self._task_executions_stored = 0
        self._plan_executions_stored = 0
        
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_executions (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    graph_id TEXT,
                    lifetime_id TEXT,
                    task_type TEXT NOT NULL,
                    parameters TEXT,
                    result_data TEXT,
                    result_mime_type TEXT,
                    result_size_bytes INTEGER,
                    result_error_message TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plan_executions (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    graph_id TEXT,
                    lifetime_id TEXT,
                    plan_type TEXT NOT NULL,
                    parameters TEXT,
                    input_task_id TEXT,
                    next_task_ids TEXT,
                    metadata TEXT,
                    error_message TEXT,
                    confidence REAL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_tenant ON task_executions(tenant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_lifetime ON task_executions(lifetime_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_tenant ON plan_executions(tenant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_lifetime ON plan_executions(lifetime_id)")
    
    def PutTaskExecution(self, request, context):
        """
        Store a TaskExecution record.
        
        Args:
            request: TaskExecution protobuf message
            context: gRPC context
            
        Returns:
            Ack response
        """
        self._request_count += 1
        
        with log_request_response(
            self.logger,
            "PutTaskExecution",
            request_id=request.header.id,
            tenant_id=request.header.tenant_id,
            task_type=request.task_type
        ):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Extract result data
                    result_data = None
                    result_mime_type = ""
                    result_size_bytes = 0
                    result_error_message = ""
                    
                    if request.result.HasField('inline_data'):
                        result_data = request.result.inline_data.SerializeToString()
                        result_mime_type = request.result.mime_type
                        result_size_bytes = request.result.size_bytes
                    elif request.result.HasField('uri'):
                        result_data = request.result.uri
                        result_mime_type = request.result.mime_type
                        result_size_bytes = request.result.size_bytes
                    
                    result_error_message = request.result.error_message
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO task_executions (
                            id, tenant_id, graph_id, lifetime_id, task_type, parameters,
                            result_data, result_mime_type, result_size_bytes, result_error_message,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        request.header.id,
                        request.header.tenant_id,
                        request.header.graph_id,
                        request.header.lifetime_id,
                        request.task_type,
                        request.parameters,
                        result_data,
                        result_mime_type,
                        result_size_bytes,
                        result_error_message,
                        request.header.status,
                        request.header.created_at,
                        datetime.utcnow().isoformat()
                    ))
                    
                    self._task_executions_stored += 1
                    
                    # Update metrics
                    if self.health_service:
                        self.health_service.update_metric("total_requests", self._request_count)
                        self.health_service.update_metric("task_executions_stored", self._task_executions_stored)
                        self.health_service.update_metric("result_size_bytes", result_size_bytes)
                    
                    return services_pb2.Ack(success=True, message="TaskExecution stored successfully")
                    
            except Exception as e:
                self._error_count += 1
                if self.health_service:
                    self.health_service.update_metric("error_count", self._error_count)
                
                log_error(self.logger, e, 
                         request_id=request.header.id,
                         tenant_id=request.header.tenant_id)
                
                return services_pb2.Ack(success=False, message=f"Failed to store TaskExecution: {str(e)}")
    
    def PutPlanExecution(self, request, context):
        """
        Store a PlanExecution record.
        
        Args:
            request: PlanExecution protobuf message
            context: gRPC context
            
        Returns:
            Ack response
        """
        self._request_count += 1
        
        with log_request_response(
            self.logger,
            "PutPlanExecution",
            request_id=request.header.id,
            tenant_id=request.header.tenant_id,
            plan_type=request.plan_type
        ):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Serialize next_task_ids and metadata
                    next_task_ids_json = json.dumps(list(request.result.next_task_ids))
                    metadata_json = json.dumps(dict(request.result.metadata))
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO plan_executions (
                            id, tenant_id, graph_id, lifetime_id, plan_type, parameters,
                            input_task_id, next_task_ids, metadata, error_message, confidence,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        request.header.id,
                        request.header.tenant_id,
                        request.header.graph_id,
                        request.header.lifetime_id,
                        request.plan_type,
                        request.parameters,
                        request.input_task_id,
                        next_task_ids_json,
                        metadata_json,
                        request.result.error_message,
                        request.result.confidence,
                        request.header.status,
                        request.header.created_at,
                        datetime.utcnow().isoformat()
                    ))
                    
                    self._plan_executions_stored += 1
                    
                    # Update metrics
                    if self.health_service:
                        self.health_service.update_metric("total_requests", self._request_count)
                        self.health_service.update_metric("plan_executions_stored", self._plan_executions_stored)
                        self.health_service.update_metric("confidence", request.result.confidence)
                    
                    return services_pb2.Ack(success=True, message="PlanExecution stored successfully")
                    
            except Exception as e:
                self._error_count += 1
                if self.health_service:
                    self.health_service.update_metric("error_count", self._error_count)
                
                log_error(self.logger, e, 
                         request_id=request.header.id,
                         tenant_id=request.header.tenant_id)
                
                return services_pb2.Ack(success=False, message=f"Failed to store PlanExecution: {str(e)}")
    
    def GetTaskExecution(self, request, context):
        """
        Retrieve a TaskExecution by ID.
        
        Args:
            request: GetTaskExecutionRequest
            context: gRPC context
            
        Returns:
            TaskExecution protobuf message
        """
        self._request_count += 1
        
        with log_request_response(
            self.logger,
            "GetTaskExecution",
            request_id=request.execution_id,
            tenant_id=request.tenant_id
        ):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT * FROM task_executions 
                        WHERE id = ? AND tenant_id = ?
                    """, (request.execution_id, request.tenant_id))
                    
                    row = cursor.fetchone()
                    if not row:
                        context.abort(grpc.StatusCode.NOT_FOUND, "TaskExecution not found")
                    
                    # Reconstruct TaskExecution from database row
                    # This is a simplified reconstruction - in practice you'd want more robust handling
                    header = common_pb2.ExecutionHeader(
                        id=row[0],
                        tenant_id=row[1],
                        graph_id=row[2],
                        lifetime_id=row[3],
                        status=row[11],
                        created_at=row[12]
                    )
                    
                    result = task_pb2.TaskResult(
                        mime_type=row[8],
                        size_bytes=row[9],
                        error_message=row[10]
                    )
                    
                    # Update metrics
                    if self.health_service:
                        self.health_service.update_metric("total_requests", self._request_count)
                    
                    return task_pb2.TaskExecution(
                        header=header,
                        task_type=row[4],
                        parameters=row[5],
                        result=result
                    )
                    
            except Exception as e:
                self._error_count += 1
                if self.health_service:
                    self.health_service.update_metric("error_count", self._error_count)
                
                log_error(self.logger, e, 
                         request_id=request.execution_id,
                         tenant_id=request.tenant_id)
                context.abort(grpc.StatusCode.INTERNAL, f"Failed to retrieve TaskExecution: {str(e)}")
    
    def GetPlanExecution(self, request, context):
        """
        Retrieve a PlanExecution by ID.
        
        Args:
            request: GetPlanExecutionRequest
            context: gRPC context
            
        Returns:
            PlanExecution protobuf message
        """
        self._request_count += 1
        
        with log_request_response(
            self.logger,
            "GetPlanExecution",
            request_id=request.execution_id,
            tenant_id=request.tenant_id
        ):
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT * FROM plan_executions 
                        WHERE id = ? AND tenant_id = ?
                    """, (request.execution_id, request.tenant_id))
                    
                    row = cursor.fetchone()
                    if not row:
                        context.abort(grpc.StatusCode.NOT_FOUND, "PlanExecution not found")
                    
                    # Reconstruct PlanExecution from database row
                    header = common_pb2.ExecutionHeader(
                        id=row[0],
                        tenant_id=row[1],
                        graph_id=row[2],
                        lifetime_id=row[3],
                        status=row[12],
                        created_at=row[13]
                    )
                    
                    next_task_ids = json.loads(row[8]) if row[8] else []
                    metadata = json.loads(row[9]) if row[9] else {}
                    
                    result = plan_pb2.PlanResult(
                        next_task_ids=next_task_ids,
                        metadata=metadata,
                        error_message=row[10],
                        confidence=row[11]
                    )
                    
                    # Update metrics
                    if self.health_service:
                        self.health_service.update_metric("total_requests", self._request_count)
                    
                    return plan_pb2.PlanExecution(
                        header=header,
                        plan_type=row[4],
                        input_task_id=row[7],
                        parameters=row[5],
                        result=result
                    )
                    
            except Exception as e:
                self._error_count += 1
                if self.health_service:
                    self.health_service.update_metric("error_count", self._error_count)
                
                log_error(self.logger, e, 
                         request_id=request.execution_id,
                         tenant_id=request.tenant_id)
                context.abort(grpc.StatusCode.INTERNAL, f"Failed to retrieve PlanExecution: {str(e)}")


def serve(port: int = 50051, log_level: str = "INFO") -> None:
    """
    Start the data plane service server with health checks and graceful shutdown.
    
    Args:
        port: Port to bind the server to
        log_level: Logging level
    """
    # Configure logging
    configure_logging(log_level=log_level)
    logger = get_logger(__name__)
    
    # Create health check service
    health_service = HealthCheckService(logger)
    
    # Create gRPC server
    server = grpc.server(grpc.ThreadPoolExecutor(max_workers=10))
    
    # Add data plane service
    data_plane_service = DataPlaneService(health_service=health_service)
    services_pb2_grpc.add_DataPlaneServiceServicer_to_server(data_plane_service, server)
    
    # Add health check service
    health_servicer = HealthCheckServicer(health_service)
    # Note: In a real implementation, you'd add the health check servicer to the server
    # For now, we'll just use the health service for metrics and shutdown
    
    # Start HTTP health server
    http_health_server = start_health_server(health_service, port=8081, logger=logger)
    
    # Add shutdown handler for cleanup
    def cleanup():
        logger.info("Cleaning up data plane service")
        # Add any cleanup logic here, such as closing database connections
    
    health_service.add_shutdown_handler(cleanup)
    
    # Start server with managed lifecycle
    async def run_server():
        async with managed_server(server, health_service, port, logger):
            logger.info("Data plane service started", port=port)
            # Keep the server running until shutdown is requested
            while not health_service.is_shutdown_requested():
                await asyncio.sleep(1)
    
    # Run the server
    asyncio.run(run_server())


if __name__ == "__main__":
    serve() 