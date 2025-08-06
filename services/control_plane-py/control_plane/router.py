"""
Execution routing logic for control plane microservice.

This module implements execution routing logic. Based on the execution type
(Task or Plan) and the next_task_names from PlanResult, determines which
executor topics to publish to.
"""

from typing import Dict, List, Optional, Union

from structlog import get_logger

from agentic_common.kafka_utils import (
    get_controlled_plan_executions_topic,
    get_controlled_task_executions_topic,
)
from agentic_common.pb import TaskExecution, PlanExecution

logger = get_logger(__name__)


class ExecutionRouter:
    """
    Execution router for control plane service.
    
    Routes TaskExecutions to controlled-task-executions_{tenant_id} topics and
    PlanExecutions to controlled-plan-executions_{tenant_id} topics based on
    execution type and next_task_names.
    """
    
    def __init__(self):
        """Initialize the execution router."""
        pass
    
    def route_task_execution(self, task_execution: TaskExecution, tenant_id: str) -> List[str]:
        """
        Route TaskExecution to appropriate controlled-task-executions topic.
        
        Args:
            task_execution: TaskExecution protobuf message
            tenant_id: Tenant identifier
            
        Returns:
            List of target topics
        """
        try:
            # Route TaskExecution to controlled-task-executions topic
            target_topic = get_controlled_task_executions_topic(tenant_id)
            
            logger.info("Routing TaskExecution to controlled-task-executions", 
                       execution_id=task_execution.header.exec_id,
                       tenant_id=tenant_id,
                       target_topic=target_topic)
            
            return [target_topic]
            
        except Exception as e:
            logger.error("Failed to route TaskExecution", 
                        task_execution=task_execution,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    def route_plan_execution(self, plan_execution: PlanExecution, tenant_id: str) -> List[str]:
        """
        Route PlanExecution to appropriate controlled-plan-executions topic.
        
        Args:
            plan_execution: PlanExecution protobuf message
            tenant_id: Tenant identifier
            
        Returns:
            List of target topics
        """
        try:
            # Route PlanExecution to controlled-plan-executions topic
            target_topic = get_controlled_plan_executions_topic(tenant_id)
            
            logger.info("Routing PlanExecution to controlled-plan-executions", 
                       execution_id=plan_execution.header.exec_id,
                       tenant_id=tenant_id,
                       target_topic=target_topic)
            
            # TODO: Future routing logic may use the new parent_task_exec_ids field
            # for more sophisticated routing decisions based on parent execution relationships
            
            return [target_topic]
            
        except Exception as e:
            logger.error("Failed to route PlanExecution", 
                        plan_execution=plan_execution,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    def route_execution(self, execution_data: Union[TaskExecution, PlanExecution, Dict[str, any]], tenant_id: str) -> List[str]:
        """
        Route execution based on its type.
        
        Args:
            execution_data: Execution data (protobuf object or dict)
            tenant_id: Tenant identifier
            
        Returns:
            List of target topics
        """
        # Handle protobuf objects
        if isinstance(execution_data, TaskExecution):
            return self.route_task_execution(execution_data, tenant_id)
        elif isinstance(execution_data, PlanExecution):
            return self.route_plan_execution(execution_data, tenant_id)
        
        # Handle dictionary format (for backward compatibility)
        execution_type = execution_data.get("type")
        
        if execution_type == "task":
            return self.route_task_execution(execution_data, tenant_id)
        elif execution_type == "plan":
            return self.route_plan_execution(execution_data, tenant_id)
        else:
            logger.warning("Unknown execution type", 
                          execution_type=execution_type,
                          execution_id=execution_data.get("execution_id"))
            return []
    
    def get_routing_info(self, execution_data: Union[TaskExecution, PlanExecution, Dict[str, any]], tenant_id: str) -> Dict[str, any]:
        """
        Get routing information for an execution.
        
        Args:
            execution_data: Execution data (protobuf object or dict)
            tenant_id: Tenant identifier
            
        Returns:
            Routing information dictionary
        """
        try:
            # Handle protobuf objects
            if isinstance(execution_data, TaskExecution):
                execution_type = "task"
                execution_id = execution_data.header.exec_id
                target_topic = get_controlled_task_executions_topic(tenant_id)
                routing_type = "task_to_plan"
            elif isinstance(execution_data, PlanExecution):
                execution_type = "plan"
                execution_id = execution_data.header.exec_id
                target_topic = get_controlled_plan_executions_topic(tenant_id)
                routing_type = "plan_to_task"
            else:
                # Handle dictionary format (for backward compatibility)
                execution_type = execution_data.get("type")
                execution_id = execution_data.get("execution_id")
                
                if execution_type == "task":
                    target_topic = get_controlled_task_executions_topic(tenant_id)
                    routing_type = "task_to_plan"
                elif execution_type == "plan":
                    target_topic = get_controlled_plan_executions_topic(tenant_id)
                    routing_type = "plan_to_task"
                else:
                    target_topic = None
                    routing_type = "unknown"
            
            return {
                "execution_id": execution_id,
                "execution_type": execution_type,
                "tenant_id": tenant_id,
                "target_topic": target_topic,
                "routing_type": routing_type,
            }
            
        except Exception as e:
            logger.error("Failed to get routing info", 
                        execution_data=execution_data,
                        tenant_id=tenant_id,
                        error=str(e))
            return {
                "execution_id": execution_data.get("execution_id") if isinstance(execution_data, dict) else None,
                "execution_type": execution_data.get("type") if isinstance(execution_data, dict) else None,
                "tenant_id": tenant_id,
                "target_topic": None,
                "routing_type": "error",
                "error": str(e),
            } 