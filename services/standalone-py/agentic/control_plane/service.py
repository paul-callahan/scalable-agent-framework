"""
Control plane service implementation using in-memory message broker.

This module implements the ControlPlaneService that consumes from control queues,
evaluates guardrails, and routes approved executions to result queues.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from ..message_bus import InMemoryBroker
from agentic_common.pb import task_pb2, plan_pb2, common_pb2
from ..core.logging import get_logger, log_metric, log_error


class ControlPlaneService:
    """
    Control plane service implementation.
    
    Handles orchestration, routing, and guardrail evaluation for execution envelopes.
    """
    
    def __init__(self, broker: InMemoryBroker):
        """
        Initialize the control plane service.
        
        Args:
            broker: In-memory message broker
        """
        self.broker = broker
        self.execution_status: Dict[str, Dict] = {}
        self.guardrails: Dict[str, List[Dict]] = {}
        self.routing_rules: Dict[str, str] = {}
        self.logger = get_logger(__name__)
        
        # Initialize metrics
        self._request_count = 0
        self._error_count = 0
        self._guardrail_violations = 0
        self._messages_processed = 0
        
        # Service state
        self._running = False
        self._task_consumer_task: Optional[asyncio.Task] = None
        self._plan_consumer_task: Optional[asyncio.Task] = None
    
    def _evaluate_guardrail(self, guardrail: Dict, request_data: Dict) -> Optional[str]:
        """
        Evaluate a single guardrail against the request.
        
        Args:
            guardrail: Guardrail configuration
            request_data: Request data dictionary
            
        Returns:
            Violation message if guardrail is violated, None otherwise
        """
        guardrail_type = guardrail.get('type')
        
        if guardrail_type == 'rate_limit':
            return self._check_rate_limit(guardrail, request_data)
        elif guardrail_type == 'resource_usage':
            return self._check_resource_usage(guardrail, request_data)
        elif guardrail_type == 'content_filter':
            return self._check_content_filter(guardrail, request_data)
        elif guardrail_type == 'tenant_quota':
            return self._check_tenant_quota(guardrail, request_data)
        
        return None
    
    def _check_rate_limit(self, guardrail: Dict, request_data: Dict) -> Optional[str]:
        """Check rate limiting guardrail."""
        # Simple rate limiting implementation
        tenant_id = request_data.get('tenant_id', '')
        current_time = datetime.utcnow()
        
        # Get current rate for tenant
        tenant_key = f"rate_limit_{tenant_id}"
        if tenant_key not in self.execution_status:
            self.execution_status[tenant_key] = {'count': 0, 'window_start': current_time}
        
        rate_info = self.execution_status[tenant_key]
        window_duration = guardrail.get('window_seconds', 60)
        
        # Reset window if expired
        if (current_time - rate_info['window_start']).total_seconds() > window_duration:
            rate_info['count'] = 0
            rate_info['window_start'] = current_time
        
        # Check limit
        max_requests = guardrail.get('max_requests', 100)
        if rate_info['count'] >= max_requests:
            return f"Rate limit exceeded: {max_requests} requests per {window_duration} seconds"
        
        rate_info['count'] += 1
        return None
    
    def _check_resource_usage(self, guardrail: Dict, request_data: Dict) -> Optional[str]:
        """Check resource usage guardrail."""
        # Simple resource usage check
        max_memory_mb = guardrail.get('max_memory_mb', 1024)
        max_cpu_percent = guardrail.get('max_cpu_percent', 80)
        
        # This would typically check actual resource usage
        # For now, we'll just log the check
        self.logger.debug(f"Resource usage check: max_memory={max_memory_mb}MB, max_cpu={max_cpu_percent}%")
        
        return None
    
    def _check_content_filter(self, guardrail: Dict, request_data: Dict) -> Optional[str]:
        """Check content filtering guardrail."""
        # Simple content filtering
        blocked_keywords = guardrail.get('blocked_keywords', [])
        parameters = request_data.get('parameters', '')
        
        if isinstance(parameters, str):
            for keyword in blocked_keywords:
                if keyword.lower() in parameters.lower():
                    return f"Content filter violation: blocked keyword '{keyword}' found"
        
        return None
    
    def _check_tenant_quota(self, guardrail: Dict, request_data: Dict) -> Optional[str]:
        """Check tenant quota guardrail."""
        tenant_id = request_data.get('tenant_id', '')
        max_executions = guardrail.get('max_executions', 1000)
        
        # Get current execution count for tenant
        tenant_key = f"quota_{tenant_id}"
        if tenant_key not in self.execution_status:
            self.execution_status[tenant_key] = {'count': 0}
        
        current_count = self.execution_status[tenant_key]['count']
        if current_count >= max_executions:
            return f"Tenant quota exceeded: {max_executions} executions limit reached"
        
        self.execution_status[tenant_key]['count'] += 1
        return None
    
    async def _evaluate_guardrails(self, request_data: Dict) -> Dict:
        """
        Evaluate all guardrails for a request.
        
        Args:
            request_data: Request data dictionary
            
        Returns:
            Dictionary with evaluation results
        """
        tenant_id = request_data.get('tenant_id', 'default')
        execution_id = request_data.get('execution_id', '')
        
        # Get tenant-specific guardrails
        tenant_guardrails = self.guardrails.get(tenant_id, [])
        
        violations = []
        allowed = True
        
        # Evaluate each guardrail
        for guardrail in tenant_guardrails:
            if guardrail.get('enabled', True):
                violation = self._evaluate_guardrail(guardrail, request_data)
                if violation:
                    violations.append(violation)
                    if guardrail.get('blocking', True):
                        allowed = False
                        self._guardrail_violations += 1
        
        return {
            'allowed': allowed,
            'violations': violations,
            'execution_id': execution_id,
            'tenant_id': tenant_id
        }
    
    async def _route_execution(self, request_data: Dict, guardrail_result: Dict) -> None:
        """
        Route execution based on guardrail evaluation.
        
        Args:
            request_data: Request data dictionary
            guardrail_result: Guardrail evaluation result
        """
        tenant_id = request_data.get('tenant_id', 'default')
        execution_type = request_data.get('execution_type', '')
        
        if not guardrail_result['allowed']:
            # Create rejection protobuf message
            rejection_header = common_pb2.ExecutionHeader(
                exec_id=request_data.get('execution_id', ''),
                tenant_id=tenant_id,
                created_at=datetime.utcnow().isoformat()
            )
            
            if execution_type == 'task':
                rejection_result = task_pb2.TaskResult(
                    error_message='; '.join(guardrail_result['violations'])
                )
                rejection_message = task_pb2.TaskExecution(
                    header=rejection_header,
                    result=rejection_result
                )
            else:  # plan
                rejection_result = plan_pb2.PlanResult(
                    error_message='; '.join(guardrail_result['violations'])
                )
                rejection_message = plan_pb2.PlanExecution(
                    header=rejection_header,
                    result=rejection_result
                )
            
            result_topic = f"{execution_type}-results_{tenant_id}"
            rejection_bytes = rejection_message.SerializeToString()
            await self.broker.publish(result_topic, rejection_bytes)
            
            self.logger.warning(f"Execution rejected: {rejection_result.error_message}")
            return
        
        # Create approval protobuf message
        approval_header = common_pb2.ExecutionHeader(
            exec_id=request_data.get('execution_id', ''),
            tenant_id=tenant_id,
            created_at=datetime.utcnow().isoformat()
        )
        
        if execution_type == 'task':
            approval_result = task_pb2.TaskResult()
            approval_message = task_pb2.TaskExecution(
                header=approval_header,
                result=approval_result
            )
        else:  # plan
            approval_result = plan_pb2.PlanResult()
            approval_message = plan_pb2.PlanExecution(
                header=approval_header,
                result=approval_result
            )
        
        result_topic = f"{execution_type}-results_{tenant_id}"
        approval_bytes = approval_message.SerializeToString()
        await self.broker.publish(result_topic, approval_bytes)
        
        self.logger.debug(f"Execution approved: {request_data.get('execution_id', '')}")
    
    async def _process_task_control(self, message_bytes: bytes, tenant_id: str) -> None:
        """
        Process a task control message from the queue.
        
        Args:
            message_bytes: Serialized protobuf message bytes
            tenant_id: Tenant identifier
        """
        try:
            # Deserialize the protobuf message
            task_execution = task_pb2.TaskExecution.FromString(message_bytes)
            
            # Convert to request_data format for guardrail evaluation
            request_data = {
                'execution_id': task_execution.header.exec_id,
                'tenant_id': task_execution.header.tenant_id,
                'execution_type': 'task',
                'task_type': 'default_task'  # Default task type since field was removed
            }
            
            self.logger.debug(f"Processing task control message: {request_data.get('execution_id', '')}")
            
            # Evaluate guardrails
            guardrail_result = await self._evaluate_guardrails(request_data)
            
            # Route execution
            await self._route_execution(request_data, guardrail_result)
            
            self._messages_processed += 1
            self._request_count += 1
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error processing task control message: {e}")
            raise
    
    async def _process_persisted_plan_executions(self, message_bytes: bytes, tenant_id: str) -> None:
        """
        Process a persisted plan executions message from the queue.
        
        Args:
            message_bytes: Serialized protobuf message bytes
            tenant_id: Tenant identifier
        """
        try:
            # Deserialize the protobuf message
            plan_execution = plan_pb2.PlanExecution.FromString(message_bytes)
            
            # Convert to request_data format for guardrail evaluation
            request_data = {
                'execution_id': plan_execution.header.exec_id,
                'tenant_id': plan_execution.header.tenant_id,
                'execution_type': 'plan',
                'plan_type': 'default_plan'  # Default plan type since field was removed
            }
            
            self.logger.debug(f"Processing persisted plan executions message: {request_data.get('execution_id', '')}")
            
            # Evaluate guardrails
            guardrail_result = await self._evaluate_guardrails(request_data)
            
            # Route execution
            await self._route_execution(request_data, guardrail_result)
            
            self._messages_processed += 1
            self._request_count += 1
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error processing persisted plan executions message: {e}")
            raise
    
    async def _task_control_consumer_loop(self, tenant_id: str) -> None:
        """
        Consumer loop for task control messages.
        
        Args:
            tenant_id: Tenant identifier
        """
        topic = f"persisted-task-executions-{tenant_id}"
        self.logger.info(f"Starting task control consumer for topic: {topic}")
        
        try:
            async for message_bytes in self.broker.subscribe(topic):
                await self._process_task_control(message_bytes, tenant_id)
        except asyncio.CancelledError:
            self.logger.info(f"Task control consumer cancelled for tenant: {tenant_id}")
        except Exception as e:
            self.logger.error(f"Task control consumer error for tenant {tenant_id}: {e}")
            raise
    
    async def _persisted_plan_executions_consumer_loop(self, tenant_id: str) -> None:
        """
        Consumer loop for persisted plan executions messages.
        
        Args:
            tenant_id: Tenant identifier
        """
        topic = f"persisted-plan-executions-{tenant_id}"
        self.logger.info(f"Starting persisted plan executions consumer for topic: {topic}")
        
        try:
            async for message_bytes in self.broker.subscribe(topic):
                await self._process_persisted_plan_executions(message_bytes, tenant_id)
        except asyncio.CancelledError:
            self.logger.info(f"Persisted plan executions consumer cancelled for tenant: {tenant_id}")
        except Exception as e:
            self.logger.error(f"Persisted plan executions consumer error for tenant {tenant_id}: {e}")
            raise
    
    async def start(self, tenant_id: str = "default") -> None:
        """
        Start the control plane service.
        
        Args:
            tenant_id: Tenant identifier
        """
        if self._running:
            self.logger.warning("Control plane service is already running")
            return
        
        self._running = True
        self.logger.info("Starting control plane service")
        
        # Start consumer tasks
        self._task_consumer_task = asyncio.create_task(self._task_control_consumer_loop(tenant_id))
        self._plan_consumer_task = asyncio.create_task(self._persisted_plan_executions_consumer_loop(tenant_id))
        
        self.logger.info("Control plane service started successfully")
    
    async def stop(self) -> None:
        """Stop the control plane service."""
        if not self._running:
            return
        
        self.logger.info("Stopping control plane service")
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
        
        self.logger.info("Control plane service stopped")
    
    def add_guardrail(self, tenant_id: str, guardrail: Dict) -> None:
        """
        Add a guardrail for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            guardrail: Guardrail configuration dictionary
        """
        if tenant_id not in self.guardrails:
            self.guardrails[tenant_id] = []
        
        self.guardrails[tenant_id].append(guardrail)
        self.logger.info(f"Added guardrail for tenant {tenant_id}: {guardrail.get('type', 'unknown')}")
    
    def add_routing_rule(self, source_queue: str, target_queue: str) -> None:
        """
        Add a routing rule.
        
        Args:
            source_queue: Source queue name
            target_queue: Target queue name
        """
        self.routing_rules[source_queue] = target_queue
        self.logger.info(f"Added routing rule: {source_queue} -> {target_queue}")
    
    def get_metrics(self) -> dict:
        """
        Get service metrics.
        
        Returns:
            Dictionary of metric names and values
        """
        return {
            "total_requests": self._request_count,
            "guardrail_violations": self._guardrail_violations,
            "messages_processed": self._messages_processed,
            "errors": self._errors,
            "running": self._running
        } 