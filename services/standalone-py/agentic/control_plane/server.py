"""
Control plane service implementation.

This module implements the ControlPlaneService gRPC server that handles
orchestration and routing of execution envelopes.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import grpc

try:
    from ..pb import services_pb2, services_pb2_grpc
except ImportError:
    # Protobuf files not yet generated
    pass

from ..core.logging import configure_logging, get_logger, log_request_response, log_metric, log_error
from ..core.health import HealthCheckService, HealthCheckServicer, managed_server
from ..core.http_health import start_health_server


class ControlPlaneService(services_pb2_grpc.ControlPlaneServiceServicer):
    """
    Control plane service implementation.
    
    Handles orchestration, routing, and guardrail evaluation for execution envelopes.
    """
    
    def __init__(self, health_service: Optional[HealthCheckService] = None):
        """
        Initialize the control plane service.
        
        Args:
            health_service: Optional health check service
        """
        self.execution_status: Dict[str, Dict] = {}
        self.guardrails: Dict[str, List[Dict]] = {}
        self.routing_rules: Dict[str, str] = {}
        self.health_service = health_service
        self.logger = get_logger(__name__)
        
        # Initialize metrics
        self._request_count = 0
        self._error_count = 0
        self._guardrail_violations = 0
    
    def EvaluateGuardrails(self, request, context):
        """
        Evaluate guardrails for an execution.
        
        Args:
            request: GuardrailRequest
            context: gRPC context
            
        Returns:
            GuardrailResponse
        """
        self._request_count += 1
        
        with log_request_response(
            self.logger,
            "EvaluateGuardrails",
            request_id=request.execution_id,
            tenant_id=request.tenant_id,
            execution_type=request.execution_type
        ):
            try:
                execution_id = request.execution_id
                tenant_id = request.tenant_id
                execution_type = request.execution_type
                
                # Get tenant-specific guardrails
                tenant_guardrails = self.guardrails.get(tenant_id, [])
                
                violations = []
                allowed = True
                
                # Evaluate each guardrail
                for guardrail in tenant_guardrails:
                    if guardrail.get('enabled', True):
                        violation = self._evaluate_guardrail(guardrail, request)
                        if violation:
                            violations.append(violation)
                            if guardrail.get('blocking', True):
                                allowed = False
                                self._guardrail_violations += 1
                
                # Update metrics
                if self.health_service:
                    self.health_service.update_metric("total_requests", self._request_count)
                    self.health_service.update_metric("guardrail_violations", self._guardrail_violations)
                
                return services_pb2.GuardrailResponse(
                    allowed=allowed,
                    violations=violations,
                    message="Guardrail evaluation completed"
                )
                
            except Exception as e:
                self._error_count += 1
                if self.health_service:
                    self.health_service.update_metric("error_count", self._error_count)
                
                log_error(self.logger, e, 
                         request_id=request.execution_id,
                         tenant_id=request.tenant_id)
                
                return services_pb2.GuardrailResponse(
                    allowed=False,
                    violations=[f"Guardrail evaluation failed: {str(e)}"],
                    message="Guardrail evaluation failed"
                )
    
    def _evaluate_guardrail(self, guardrail: Dict, request) -> Optional[str]:
        """
        Evaluate a single guardrail.
        
        Args:
            guardrail: Guardrail configuration
            request: GuardrailRequest
            
        Returns:
            Violation message if guardrail is violated, None otherwise
        """
        guardrail_type = guardrail.get('type')
        
        if guardrail_type == 'execution_rate_limit':
            return self._check_rate_limit(guardrail, request)
        elif guardrail_type == 'resource_usage':
            return self._check_resource_usage(guardrail, request)
        elif guardrail_type == 'content_filter':
            return self._check_content_filter(guardrail, request)
        elif guardrail_type == 'tenant_quota':
            return self._check_tenant_quota(guardrail, request)
        
        return None
    
    def _check_rate_limit(self, guardrail: Dict, request) -> Optional[str]:
        """Check execution rate limits."""
        # Simplified rate limiting - in practice would use proper rate limiting
        max_executions = guardrail.get('max_executions', 100)
        time_window = guardrail.get('time_window_seconds', 3600)
        
        # Count recent executions for this tenant
        recent_count = 0
        current_time = datetime.utcnow()
        
        for execution in self.execution_status.values():
            if (execution.get('tenant_id') == request.tenant_id and
                execution.get('created_at')):
                exec_time = datetime.fromisoformat(execution['created_at'])
                if (current_time - exec_time).total_seconds() < time_window:
                    recent_count += 1
        
        if recent_count >= max_executions:
            return f"Rate limit exceeded: {recent_count}/{max_executions} executions in {time_window}s"
        
        return None
    
    def _check_resource_usage(self, guardrail: Dict, request) -> Optional[str]:
        """Check resource usage limits."""
        # Simplified resource checking
        max_memory_mb = guardrail.get('max_memory_mb', 1024)
        max_cpu_percent = guardrail.get('max_cpu_percent', 80)
        
        # In practice, would check actual resource usage
        # For now, just return None (no violation)
        return None
    
    def _check_content_filter(self, guardrail: Dict, request) -> Optional[str]:
        """Check content filtering rules."""
        # Simplified content filtering
        blocked_keywords = guardrail.get('blocked_keywords', [])
        
        # Check execution data for blocked keywords
        execution_data = request.execution_data.decode('utf-8', errors='ignore')
        for keyword in blocked_keywords:
            if keyword.lower() in execution_data.lower():
                return f"Content filter violation: blocked keyword '{keyword}' found"
        
        return None
    
    def _check_tenant_quota(self, guardrail: Dict, request) -> Optional[str]:
        """Check tenant quota limits."""
        max_executions_per_day = guardrail.get('max_executions_per_day', 1000)
        
        # Count today's executions for this tenant
        today_count = 0
        current_time = datetime.utcnow()
        
        for execution in self.execution_status.values():
            if (execution.get('tenant_id') == request.tenant_id and
                execution.get('created_at')):
                exec_time = datetime.fromisoformat(execution['created_at'])
                if (current_time - exec_time).date() == current_time.date():
                    today_count += 1
        
        if today_count >= max_executions_per_day:
            return f"Daily quota exceeded: {today_count}/{max_executions_per_day} executions"
        
        return None
    
    def RouteExecution(self, request, context):
        """
        Route execution to appropriate queue.
        
        Args:
            request: RouteRequest
            context: gRPC context
            
        Returns:
            RouteResponse
        """
        self._request_count += 1
        
        with log_request_response(
            self.logger,
            "RouteExecution",
            request_id=request.execution_id,
            tenant_id=request.tenant_id,
            target_queue=request.target_queue
        ):
            try:
                execution_id = request.execution_id
                tenant_id = request.tenant_id
                target_queue = request.target_queue
                
                # Determine the actual queue to route to
                queue_name = self._determine_queue(target_queue, tenant_id, request.execution_data)
                
                # Record the routing decision
                self.execution_status[execution_id] = {
                    'tenant_id': tenant_id,
                    'queue_name': queue_name,
                    'routed_at': datetime.utcnow().isoformat(),
                    'status': 'routed'
                }
                
                # Update metrics
                if self.health_service:
                    self.health_service.update_metric("total_requests", self._request_count)
                    self.health_service.update_metric("routed_executions", len(self.execution_status))
                
                return services_pb2.RouteResponse(
                    routed=True,
                    queue_name=queue_name,
                    message=f"Execution routed to {queue_name}"
                )
                
            except Exception as e:
                self._error_count += 1
                if self.health_service:
                    self.health_service.update_metric("error_count", self._error_count)
                
                log_error(self.logger, e, 
                         request_id=request.execution_id,
                         tenant_id=request.tenant_id)
                
                return services_pb2.RouteResponse(
                    routed=False,
                    queue_name="",
                    message=f"Routing failed: {str(e)}"
                )
    
    def _determine_queue(self, target_queue: str, tenant_id: str, execution_data: bytes) -> str:
        """
        Determine the actual queue to route to.
        
        Args:
            target_queue: Requested target queue
            tenant_id: Tenant ID
            execution_data: Execution data
            
        Returns:
            Actual queue name to route to
        """
        # Apply routing rules
        if target_queue in self.routing_rules:
            return self.routing_rules[target_queue]
        
        # Default routing based on tenant
        if tenant_id.startswith('high_priority'):
            return f"priority_queue_{tenant_id}"
        elif tenant_id.startswith('batch'):
            return f"batch_queue_{tenant_id}"
        else:
            return f"default_queue_{tenant_id}"
    
    def GetExecutionStatus(self, request, context):
        """
        Get execution status.
        
        Args:
            request: StatusRequest
            context: gRPC context
            
        Returns:
            StatusResponse
        """
        self._request_count += 1
        
        with log_request_response(
            self.logger,
            "GetExecutionStatus",
            request_id=request.execution_id,
            tenant_id=request.tenant_id
        ):
            try:
                execution_id = request.execution_id
                tenant_id = request.tenant_id
                
                execution_info = self.execution_status.get(execution_id, {})
                
                if not execution_info:
                    context.abort(grpc.StatusCode.NOT_FOUND, "Execution not found")
                
                # Verify tenant access
                if execution_info.get('tenant_id') != tenant_id:
                    context.abort(grpc.StatusCode.PERMISSION_DENIED, "Access denied")
                
                status = execution_info.get('status', 'unknown')
                message = execution_info.get('message', '')
                last_updated = execution_info.get('routed_at', '')
                
                # Update metrics
                if self.health_service:
                    self.health_service.update_metric("total_requests", self._request_count)
                
                return services_pb2.StatusResponse(
                    status=status,
                    message=message,
                    last_updated=int(datetime.fromisoformat(last_updated).timestamp()) if last_updated else 0
                )
                
            except Exception as e:
                self._error_count += 1
                if self.health_service:
                    self.health_service.update_metric("error_count", self._error_count)
                
                log_error(self.logger, e, 
                         request_id=request.execution_id,
                         tenant_id=request.tenant_id)
                context.abort(grpc.StatusCode.INTERNAL, f"Failed to get execution status: {str(e)}")
    
    def AbortExecution(self, request, context):
        """
        Abort an execution.
        
        Args:
            request: AbortRequest
            context: gRPC context
            
        Returns:
            Ack response
        """
        self._request_count += 1
        
        with log_request_response(
            self.logger,
            "AbortExecution",
            request_id=request.execution_id,
            tenant_id=request.tenant_id,
            reason=request.reason
        ):
            try:
                execution_id = request.execution_id
                tenant_id = request.tenant_id
                reason = request.reason
                
                execution_info = self.execution_status.get(execution_id, {})
                
                if not execution_info:
                    return services_pb2.Ack(success=False, message="Execution not found")
                
                # Verify tenant access
                if execution_info.get('tenant_id') != tenant_id:
                    return services_pb2.Ack(success=False, message="Access denied")
                
                # Update execution status
                execution_info['status'] = 'aborted'
                execution_info['aborted_at'] = datetime.utcnow().isoformat()
                execution_info['abort_reason'] = reason
                
                # Update metrics
                if self.health_service:
                    self.health_service.update_metric("total_requests", self._request_count)
                    self.health_service.update_metric("aborted_executions", 
                                                   len([e for e in self.execution_status.values() 
                                                       if e.get('status') == 'aborted']))
                
                return services_pb2.Ack(success=True, message="Execution aborted successfully")
                
            except Exception as e:
                self._error_count += 1
                if self.health_service:
                    self.health_service.update_metric("error_count", self._error_count)
                
                log_error(self.logger, e, 
                         request_id=request.execution_id,
                         tenant_id=request.tenant_id)
                
                return services_pb2.Ack(success=False, message=f"Failed to abort execution: {str(e)}")
    
    def add_guardrail(self, tenant_id: str, guardrail: Dict) -> None:
        """
        Add a guardrail for a tenant.
        
        Args:
            tenant_id: Tenant ID
            guardrail: Guardrail configuration
        """
        if tenant_id not in self.guardrails:
            self.guardrails[tenant_id] = []
        self.guardrails[tenant_id].append(guardrail)
    
    def add_routing_rule(self, source_queue: str, target_queue: str) -> None:
        """
        Add a routing rule.
        
        Args:
            source_queue: Source queue name
            target_queue: Target queue name
        """
        self.routing_rules[source_queue] = target_queue


def serve(port: int = 50052, log_level: str = "INFO") -> None:
    """
    Start the control plane service server with health checks and graceful shutdown.
    
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
    
    # Add control plane service
    control_plane_service = ControlPlaneService(health_service)
    services_pb2_grpc.add_ControlPlaneServiceServicer_to_server(control_plane_service, server)
    
    # Add health check service
    health_servicer = HealthCheckServicer(health_service)
    # Note: In a real implementation, you'd add the health check servicer to the server
    # For now, we'll just use the health service for metrics and shutdown
    
    # Start HTTP health server
    http_health_server = start_health_server(health_service, port=8080, logger=logger)
    
    # Add shutdown handler for cleanup
    def cleanup():
        logger.info("Cleaning up control plane service")
        # Add any cleanup logic here
    
    health_service.add_shutdown_handler(cleanup)
    
    # Start server with managed lifecycle
    async def run_server():
        async with managed_server(server, health_service, port, logger):
            logger.info("Control plane service started", port=port)
            # Keep the server running until shutdown is requested
            while not health_service.is_shutdown_requested():
                await asyncio.sleep(1)
    
    # Run the server
    asyncio.run(run_server())


if __name__ == "__main__":
    serve() 