"""
Data plane service implementation using in-memory message broker.

This module implements the DataPlaneService that consumes from execution queues,
persists messages to SQLite, and forwards lightweight references to control queues.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..message_bus import InMemoryBroker
from ..pb import task_pb2, plan_pb2, common_pb2
from ..core.logging import get_logger, log_metric, log_error
from agentic_common import ProtobufUtils


class DataPlaneService:
    """
    Data plane service implementation.
    
    Handles persistence of TaskExecution and PlanExecution records to storage
    and forwards lightweight references to control queues.
    """
    
    def __init__(self, broker: InMemoryBroker, db_path: str = "agentic_data.db"):
        """
        Initialize the data plane service.
        
        Args:
            broker: In-memory message broker
            db_path: Path to the SQLite database file
        """
        self.broker = broker
        self.db_path = db_path
        self.logger = get_logger(__name__)
        
        # Initialize metrics
        self._task_executions_stored = 0
        self._plan_executions_stored = 0
        self._messages_processed = 0
        self._errors = 0
        
        # Service state
        self._running = False
        self._task_consumer_task: Optional[asyncio.Task] = None
        self._plan_consumer_task: Optional[asyncio.Task] = None
        
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_executions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    graph_id TEXT NOT NULL,
                    lifetime_id TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    iteration_idx INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    edge_taken TEXT,
                    parent_plan_exec_id TEXT,
                    parent_plan_name TEXT,
                    result_data BLOB,
                    result_error_message TEXT,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plan_executions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    graph_id TEXT NOT NULL,
                    lifetime_id TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    iteration_idx INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    edge_taken TEXT,
                    parent_task_exec_ids TEXT,
                    parent_task_names TEXT,
                    next_task_names TEXT,
                    error_message TEXT,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_tenant ON task_executions(tenant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_lifetime ON task_executions(lifetime_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_parent_plan ON task_executions(parent_plan_exec_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_tenant ON plan_executions(tenant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_lifetime ON plan_executions(lifetime_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_parent_tasks ON plan_executions(parent_task_exec_ids)")
    
    async def _store_task_execution(self, task_execution: task_pb2.TaskExecution) -> None:
        """
        Store a TaskExecution to the database.
        
        Args:
            task_execution: TaskExecution protobuf message
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Extract result data using the new StoredData structure
                result_data = None
                result_error_message = ""
                
                if task_execution.result.HasField('inline_data'):
                    result_data = task_execution.result.inline_data.SerializeToString()
                elif task_execution.result.HasField('external_data'):
                    # Handle StoredData structure
                    stored_data = task_execution.result.external_data
                    # Store URI and metadata as JSON
                    stored_info = {
                        'uri': stored_data.uri,
                        'metadata': dict(stored_data.metadata)
                    }
                    result_data = json.dumps(stored_info).encode('utf-8')
                
                result_error_message = task_execution.result.error_message
                
                conn.execute("""
                    INSERT OR REPLACE INTO task_executions (
                        id, name, tenant_id, graph_id, lifetime_id,
                        attempt, iteration_idx, created_at, status,
                        edge_taken, parent_plan_exec_id, parent_plan_name,
                        result_data, result_error_message, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_execution.header.exec_id,
                    task_execution.header.name,
                    task_execution.header.tenant_id,
                    task_execution.header.graph_id,
                    task_execution.header.lifetime_id,
                    task_execution.header.attempt,
                    task_execution.header.iteration_idx,
                    task_execution.header.created_at,
                    common_pb2.ExecutionStatus.Name(task_execution.header.status),
                    task_execution.header.edge_taken,
                    task_execution.parent_plan_exec_id,
                    task_execution.parent_plan_name,
                    result_data,
                    result_error_message,
                    datetime.utcnow().isoformat()
                ))
                
                self._task_executions_stored += 1
                self.logger.debug(f"Stored task execution: {task_execution.header.exec_id}")
                
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error storing task execution {task_execution.header.exec_id}: {e}")
            raise
    
    async def _store_plan_execution(self, plan_execution: plan_pb2.PlanExecution) -> None:
        """
        Store a PlanExecution to the database.
        
        Args:
            plan_execution: PlanExecution protobuf message
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Extract plan result data using consistent utilities
                plan_result_data = ProtobufUtils.extract_plan_result_data(plan_execution.result)
                next_task_names_json = json.dumps(plan_result_data["next_task_names"])
                
                # Handle parent task execution IDs
                parent_task_exec_ids_json = json.dumps(list(plan_execution.parent_task_exec_ids))
                
                # Handle parent task names
                parent_task_names = plan_execution.parent_task_names
                
                conn.execute("""
                    INSERT OR REPLACE INTO plan_executions (
                        id, name, tenant_id, graph_id, lifetime_id,
                        attempt, iteration_idx, created_at, status,
                        edge_taken, parent_task_exec_ids, parent_task_names,
                                            next_task_names, error_message, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    plan_execution.header.exec_id,
                    plan_execution.header.name,
                    plan_execution.header.tenant_id,
                    plan_execution.header.graph_id,
                    plan_execution.header.lifetime_id,
                    plan_execution.header.attempt,
                    plan_execution.header.iteration_idx,
                    plan_execution.header.created_at,
                    common_pb2.ExecutionStatus.Name(plan_execution.header.status),
                    plan_execution.header.edge_taken,
                    parent_task_exec_ids_json,
                    parent_task_names,
                    next_task_names_json,
                    plan_execution.result.error_message,
                    datetime.utcnow().isoformat()
                ))
                
                self._plan_executions_stored += 1
                self.logger.debug(f"Stored plan execution: {plan_execution.header.exec_id}")
                
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error storing plan execution {plan_execution.header.exec_id}: {e}")
            raise
    
    async def _process_task_execution(self, message_bytes: bytes, tenant_id: str) -> None:
        """
        Process a TaskExecution message from the queue.
        
        Args:
            message_bytes: Serialized TaskExecution protobuf message
            tenant_id: Tenant identifier
        """
        try:
            # Deserialize the message
            task_execution = task_pb2.TaskExecution()
            task_execution.ParseFromString(message_bytes)
            
            self.logger.debug(f"Processing task execution: {task_execution.header.exec_id}")
            
            # Store to database
            await self._store_task_execution(task_execution)
            
            # Publish full protobuf message to control queue
            control_topic = f"persisted-task-executions_{tenant_id}"
            await self.broker.publish(control_topic, message_bytes)
            
            self._messages_processed += 1
            self.logger.debug(f"Forwarded task execution to control plane: {task_execution.header.exec_id}")
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error processing task execution: {e}")
            raise
    
    async def _process_plan_execution(self, message_bytes: bytes, tenant_id: str) -> None:
        """
        Process a PlanExecution message from the queue.
        
        Args:
            message_bytes: Serialized PlanExecution protobuf message
            tenant_id: Tenant identifier
        """
        try:
            # Deserialize the message
            plan_execution = plan_pb2.PlanExecution()
            plan_execution.ParseFromString(message_bytes)
            
            self.logger.debug(f"Processing plan execution: {plan_execution.header.exec_id}")
            
            # Store to database
            await self._store_plan_execution(plan_execution)
            
            # Publish full protobuf message to control queue
            control_topic = f"persisted-plan-executions_{tenant_id}"
            await self.broker.publish(control_topic, message_bytes)
            
            self._messages_processed += 1
            self.logger.debug(f"Forwarded plan execution to control plane: {plan_execution.header.exec_id}")
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error processing plan execution: {e}")
            raise
    
    async def _task_consumer_loop(self, tenant_id: str) -> None:
        """
        Consumer loop for task execution messages.
        
        Args:
            tenant_id: Tenant identifier
        """
        topic = f"task-executions_{tenant_id}"
        self.logger.info(f"Starting task execution consumer for topic: {topic}")
        
        try:
            async for message_bytes in self.broker.subscribe(topic):
                await self._process_task_execution(message_bytes, tenant_id)
        except asyncio.CancelledError:
            self.logger.info(f"Task execution consumer cancelled for tenant: {tenant_id}")
        except Exception as e:
            self.logger.error(f"Task execution consumer error for tenant {tenant_id}: {e}")
            raise
    
    async def _plan_consumer_loop(self, tenant_id: str) -> None:
        """
        Consumer loop for plan execution messages.
        
        Args:
            tenant_id: Tenant identifier
        """
        topic = f"plan-executions_{tenant_id}"
        self.logger.info(f"Starting plan execution consumer for topic: {topic}")
        
        try:
            async for message_bytes in self.broker.subscribe(topic):
                await self._process_plan_execution(message_bytes, tenant_id)
        except asyncio.CancelledError:
            self.logger.info(f"Plan execution consumer cancelled for tenant: {tenant_id}")
        except Exception as e:
            self.logger.error(f"Plan execution consumer error for tenant {tenant_id}: {e}")
            raise
    
    async def start(self, tenant_id: str = "default") -> None:
        """
        Start the data plane service.
        
        Args:
            tenant_id: Tenant identifier
        """
        if self._running:
            self.logger.warning("Data plane service is already running")
            return
        
        self._running = True
        self.logger.info("Starting data plane service")
        
        # Start consumer tasks
        self._task_consumer_task = asyncio.create_task(self._task_consumer_loop(tenant_id))
        self._plan_consumer_task = asyncio.create_task(self._plan_consumer_loop(tenant_id))
        
        self.logger.info("Data plane service started successfully")
    
    async def stop(self) -> None:
        """Stop the data plane service."""
        if not self._running:
            return
        
        self.logger.info("Stopping data plane service")
        self._running = False
        
        # Cancel consumer tasks
        if self._task_consumer_task:
            self._task_consumer_task.cancel()
            try:
                await self._task_consumer_task
            except asyncio.CancelledError:
                pass
        
        if self._plan_consumer_task:
            self._plan_consumer_task.cancel()
            try:
                await self._plan_consumer_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Data plane service stopped")
    
    def get_metrics(self) -> dict:
        """
        Get service metrics.
        
        Returns:
            Dictionary of metric names and values
        """
        return {
            "task_executions_stored": self._task_executions_stored,
            "plan_executions_stored": self._plan_executions_stored,
            "messages_processed": self._messages_processed,
            "errors": self._errors,
            "running": self._running
        } 