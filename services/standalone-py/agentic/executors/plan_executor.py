"""
Plan executor service implementation.

This module implements the PlanExecutorService that consumes from plan-inputs queue,
processes plan execution requests, and publishes completed executions plan-execution queue.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable, Any, List

from ..message_bus import InMemoryBroker
from agentic_common.pb import plan_pb2, common_pb2
from ..core.logging import get_logger, log_metric, log_error
from agentic_common.kafka_utils import get_plan_inputs_topic
from agentic_common import ProtobufUtils


class PlanExecutorService:
    """
    Plan executor service implementation.
    
    Handles plan execution by consuming from plan-inputs queue and publishing
    completed plan executions  to plan-execution queue.
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
    
    async def _execute_plan(self, plan_type: str, parent_task_exec_ids: List[str], 
                           execution_id: str) -> plan_pb2.PlanExecution:
        """
        Execute a plan and return the result.
        
        Args:
            plan_type: Plan type identifier
            parent_task_exec_ids: List of parent task execution IDs
            execution_id: Execution identifier
            
        Returns:
            PlanExecution protobuf message with results
        """
        try:
            # Get plan handler
            plan_handler = self.plan_registry.get(plan_type, None) # Changed to None as _get_default_plan_handler is removed
            
            if not plan_handler:
                self.logger.warning(f"No handler registered for plan type: {plan_type}. Returning failed execution.")
                # Create failed PlanExecution
                plan_execution = plan_pb2.PlanExecution()
                plan_execution.header.exec_id = execution_id
                plan_execution.header.tenant_id = "default"
                plan_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
                plan_execution.header.created_at = datetime.utcnow().isoformat()
                
                # Create error result
                error_result = plan_pb2.PlanResult()
                error_result.error_message = f"No handler registered for plan type: {plan_type}"
                plan_execution.result.CopyFrom(error_result)
                
                return plan_execution
            
            # Execute plan with parent task execution IDs
            self.logger.debug(f"Executing plan {plan_type} with execution ID {execution_id}")
            result = plan_handler({}, parent_task_exec_ids)
            
            # Create PlanResult
            plan_result = plan_pb2.PlanResult()
            
            if isinstance(result, dict):
                # Extract next task names from result
                next_task_names = result.get("next_task_names", [])
                plan_result.next_task_names.extend(next_task_names)
                
                # Extract error message if present
                if "error_message" in result:
                    plan_result.error_message = result["error_message"]
            else:
                # Handle non-dict result
                plan_result.error_message = f"Plan handler returned unexpected result type: {type(result)}"
            
            # Create PlanExecution
            plan_execution = plan_pb2.PlanExecution()
            plan_execution.header.exec_id = execution_id
            plan_execution.header.tenant_id = "default"
            plan_execution.header.status = common_pb2.EXECUTION_STATUS_SUCCEEDED
            plan_execution.header.created_at = datetime.utcnow().isoformat()
            plan_execution.result.CopyFrom(plan_result)
            
            self._plans_executed += 1
            return plan_execution
            
        except Exception as e:
            self._plans_failed += 1
            self.logger.error(f"Error executing plan {plan_type}: {e}")
            
            # Create failed PlanExecution
            plan_execution = plan_pb2.PlanExecution()
            plan_execution.header.exec_id = execution_id
            plan_execution.header.tenant_id = "default"
            plan_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
            plan_execution.header.created_at = datetime.utcnow().isoformat()
            
            # Create error result
            error_result = plan_pb2.PlanResult()
            error_result.error_message = str(e)
            plan_execution.result.CopyFrom(error_result)
            
            return plan_execution
    
    async def _process_plan_execution(self, message_bytes: bytes, tenant_id: str) -> None:
        """
        Process a plan execution message from the queue.
        
        Args:
            message_bytes: Serialized PlanExecution protobuf message bytes
            tenant_id: Tenant identifier
        """
        try:
            # Deserialize the PlanExecution protobuf message
            plan_execution = plan_pb2.PlanExecution()
            plan_execution.ParseFromString(message_bytes)
            
            execution_id = plan_execution.header.exec_id
            status = plan_execution.header.status
            
            self.logger.debug(f"Processing plan execution: {execution_id}, status: {status}")
            
            if status == common_pb2.EXECUTION_STATUS_SUCCEEDED:
                # Extract plan information from the protobuf message
                plan_type = "default_plan"  # Default plan type - could be extracted from metadata
                parent_task_exec_ids = list(plan_execution.parent_task_exec_ids)
                
                # Execute the plan
                plan_execution = await self._execute_plan(plan_type, parent_task_exec_ids, execution_id)
                
                # Serialize and publish to execution queue
                execution_topic = f"plan-executions-{tenant_id}"
                execution_bytes = plan_execution.SerializeToString()
                await self.broker.publish(execution_topic, execution_bytes)
                
                self.logger.debug(f"Published plan execution result: {execution_id}")
            
            elif status == common_pb2.EXECUTION_STATUS_FAILED:
                # Handle failed plan
                error_message = plan_execution.result.error_message
                self.logger.warning(f"Plan execution failed: {execution_id}, error: {error_message}")
                
                # Create failed PlanExecution for failed plans
                failed_execution = plan_pb2.PlanExecution()
                failed_execution.header.exec_id = execution_id
                failed_execution.header.tenant_id = tenant_id
                failed_execution.header.status = common_pb2.EXECUTION_STATUS_FAILED
                failed_execution.header.created_at = datetime.utcnow().isoformat()
                
                # Create error result
                error_result = plan_pb2.PlanResult()
                error_result.error_message = error_message
                failed_execution.result.CopyFrom(error_result)
                
                # Serialize and publish to execution queue
                execution_topic = f"plan-executions-{tenant_id}"
                execution_bytes = failed_execution.SerializeToString()
                await self.broker.publish(execution_topic, execution_bytes)
            
            self._messages_processed += 1
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Error processing plan execution: {e}")
            raise
    
    async def _consumer_loop(self, tenant_id: str) -> None:
        """
        Consumer loop for plan-input messages.
        
        Args:
            tenant_id: Tenant identifier
        """
        topic = get_plan_inputs_topic(tenant_id)
        self.logger.info(f"Starting plan-input consumer for topic: {topic}")
        
        try:
            async for message_bytes in self.broker.subscribe(topic):
                await self._process_plan_execution(message_bytes, tenant_id)
        except asyncio.CancelledError:
            self.logger.info(f"Plan-input consumer cancelled for tenant: {tenant_id}")
        except Exception as e:
            self.logger.error(f"Plan-input consumer error for tenant {tenant_id}: {e}")
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