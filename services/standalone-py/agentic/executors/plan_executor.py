"""
Plan executor service implementation.

This module implements the PlanExecutorService that consumes from plan result queues,
processes plan execution requests, and publishes completed results back to execution queues.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable, Any, List

from ..message_bus import InMemoryBroker
from ..pb import plan_pb2, common_pb2
from ..core.logging import get_logger, log_metric, log_error


class PlanExecutorService:
    """
    Plan executor service implementation.
    
    Handles plan execution by consuming from result queues and publishing
    completed plan executions back to execution queues.
    """
    
    def __init__(self, broker: InMemoryBroker):
        """
        Initialize the plan executor service.
        
        Args:
            broker: In-memory message broker
        """
        self.broker = broker
        self.logger = get_logger(__name__)
        
        # Plan registry for available plan implementations
        self.plan_registry: Dict[str, Callable] = {}
        
        # Initialize metrics
        self._plans_executed = 0
        self._plans_failed = 0
        self._messages_processed = 0
        self._errors = 0
        
        # Service state
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None
    
    def register_plan(self, plan_type: str, plan_handler: Callable) -> None:
        """
        Register a plan handler for a specific plan type.
        
        Args:
            plan_type: Plan type identifier
            plan_handler: Function to handle plan execution
        """
        self.plan_registry[plan_type] = plan_handler
        self.logger.info(f"Registered plan handler for type: {plan_type}")
    
    def _get_default_plan_handler(self, plan_type: str) -> Callable:
        """
        Get a default plan handler for unknown plan types.
        
        Args:
            plan_type: Plan type identifier
            
        Returns:
            Default plan handler function
        """
        def default_handler(parameters: str, input_task_id: str) -> Dict[str, Any]:
            """Default plan handler that returns a mock result."""
            return {
                "next_task_ids": [f"mock_task_{uuid.uuid4().hex[:8]}"],
                "metadata": {
                    "plan_type": plan_type,
                    "handler": "default",
                    "input_task_id": input_task_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "confidence": 0.8
            }
        
        return default_handler
    
    async def _execute_plan(self, plan_type: str, parameters: str, input_task_id: str, 
                           execution_id: str) -> plan_pb2.PlanExecution:
        """
        Execute a plan and return the result.
        
        Args:
            plan_type: Plan type identifier
            parameters: Plan parameters (JSON string)
            input_task_id: Input task identifier
            execution_id: Execution identifier
            
        Returns:
            PlanExecution protobuf message with results
        """
        try:
            # Get plan handler
            plan_handler = self.plan_registry.get(plan_type, self._get_default_plan_handler(plan_type))
            
            # Parse parameters
            try:
                params_dict = json.loads(parameters) if parameters else {}
            except json.JSONDecodeError:
                params_dict = {"raw_parameters": parameters}
            
            # Execute plan
            self.logger.debug(f"Executing plan {plan_type} with execution ID {execution_id}")
            result = plan_handler(params_dict, input_task_id)
            
            # Create PlanResult
            plan_result = plan_pb2.PlanResult()
            
            if isinstance(result, dict):
                # Handle dictionary result
                if "error" in result:
                    plan_result.error_message = str(result["error"])
                else:
                    # Extract next task IDs
                    next_task_ids = result.get("next_task_ids", [])
                    if isinstance(next_task_ids, list):
                        plan_result.next_task_ids.extend(next_task_ids)
                    
                    # Extract metadata
                    metadata = result.get("metadata", {})
                    if isinstance(metadata, dict):
                        for key, value in metadata.items():
                            plan_result.metadata[key] = str(value)
                    
                    # Extract confidence
                    confidence = result.get("confidence", 0.5)
                    plan_result.confidence = float(confidence)
            else:
                # Handle simple result
                plan_result.next_task_ids.append(str(result))
                plan_result.confidence = 0.5
            
            # Create PlanExecution
            plan_execution = plan_pb2.PlanExecution()
            plan_execution.header.id = execution_id
            plan_execution.header.tenant_id = "default"  # Could be extracted from context
            plan_execution.header.status = common_pb2.EXECUTION_STATUS_SUCCEEDED
            plan_execution.header.created_at = datetime.utcnow().isoformat()
            plan_execution.plan_type = plan_type
            plan_execution.parameters = parameters
            plan_execution.input_task_id = input_task_id
            plan_execution.result.CopyFrom(plan_result)
            
            self._plans_executed += 1
            self.logger.debug(f"Plan {plan_type} executed successfully: {execution_id}")
            
            return plan_execution
            
        except Exception as e:
            self._plans_failed += 1
            self.logger.error(f"Plan execution failed for {plan_type}: {e}")
            
            # Create failed PlanExecution
            plan_execution = plan_pb2.PlanExecution()
            plan_execution.header.id = execution_id
            plan_execution.header.tenant_id = "default"
            plan_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
            plan_execution.header.created_at = datetime.utcnow().isoformat()
            plan_execution.plan_type = plan_type
            plan_execution.parameters = parameters
            plan_execution.input_task_id = input_task_id
            
            # Create error result
            error_result = plan_pb2.PlanResult()
            error_result.error_message = str(e)
            plan_execution.result.CopyFrom(error_result)
            
            return plan_execution
    
    async def _process_plan_result(self, message_bytes: bytes, tenant_id: str) -> None:
        """
        Process a plan result message from the queue.
        
        Args:
            message_bytes: Serialized result message bytes
            tenant_id: Tenant identifier
        """
        try:
            # Deserialize the message
            result_data = json.loads(message_bytes.decode('utf-8'))
            
            execution_id = result_data.get('execution_id', '')
            status = result_data.get('status', '')
            
            self.logger.debug(f"Processing plan result: {execution_id}, status: {status}")
            
            if status == 'approved':
                # Extract plan information and execute
                plan_type = result_data.get('plan_type', 'unknown')
                parameters = result_data.get('parameters', '{}')
                input_task_id = result_data.get('input_task_id', '')
                
                # Execute the plan
                plan_execution = await self._execute_plan(plan_type, parameters, input_task_id, execution_id)
                
                # Serialize and publish to execution queue
                execution_topic = f"plan-executions_{tenant_id}"
                execution_bytes = plan_execution.SerializeToString()
                await self.broker.publish(execution_topic, execution_bytes)
                
                self.logger.debug(f"Published plan execution result: {execution_id}")
            
            elif status == 'rejected':
                # Handle rejected plan
                reason = result_data.get('reason', 'Unknown reason')
                self.logger.warning(f"Plan execution rejected: {execution_id}, reason: {reason}")
                
                # Create failed PlanExecution for rejected plans
                plan_execution = plan_pb2.PlanExecution()
                plan_execution.header.id = execution_id
                plan_execution.header.tenant_id = tenant_id
                plan_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
                plan_execution.header.created_at = datetime.utcnow().isoformat()
                plan_execution.plan_type = result_data.get('plan_type', 'unknown')
                plan_execution.parameters = result_data.get('parameters', '{}')
                plan_execution.input_task_id = result_data.get('input_task_id', '')
                
                # Create error result
                error_result = plan_pb2.PlanResult()
                error_result.error_message = f"Plan rejected: {reason}"
                plan_execution.result.CopyFrom(error_result)
                
                # Serialize and publish to execution queue
                execution_topic = f"plan-executions_{tenant_id}"
                execution_bytes = plan_execution.SerializeToString()
                await self.broker.publish(execution_topic, execution_bytes)
            
            self._messages_processed += 1
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error processing plan result: {e}")
            raise
    
    async def _consumer_loop(self, tenant_id: str) -> None:
        """
        Consumer loop for plan result messages.
        
        Args:
            tenant_id: Tenant identifier
        """
        topic = f"plan-results_{tenant_id}"
        self.logger.info(f"Starting plan result consumer for topic: {topic}")
        
        try:
            async for message_bytes in self.broker.subscribe(topic):
                await self._process_plan_result(message_bytes, tenant_id)
        except asyncio.CancelledError:
            self.logger.info(f"Plan result consumer cancelled for tenant: {tenant_id}")
        except Exception as e:
            self.logger.error(f"Plan result consumer error for tenant {tenant_id}: {e}")
            raise
    
    async def start(self, tenant_id: str = "default") -> None:
        """
        Start the plan executor service.
        
        Args:
            tenant_id: Tenant identifier
        """
        if self._running:
            self.logger.warning("Plan executor service is already running")
            return
        
        self._running = True
        self.logger.info("Starting plan executor service")
        
        # Start consumer task
        self._consumer_task = asyncio.create_task(self._consumer_loop(tenant_id))
        
        self.logger.info("Plan executor service started successfully")
    
    async def stop(self) -> None:
        """Stop the plan executor service."""
        if not self._running:
            return
        
        self.logger.info("Stopping plan executor service")
        self._running = False
        
        # Cancel consumer task
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Plan executor service stopped")
    
    def get_metrics(self) -> dict:
        """
        Get service metrics.
        
        Returns:
            Dictionary of metric names and values
        """
        return {
            "plans_executed": self._plans_executed,
            "plans_failed": self._plans_failed,
            "messages_processed": self._messages_processed,
            "errors": self._errors,
            "registered_plans": len(self.plan_registry),
            "running": self._running
        } 