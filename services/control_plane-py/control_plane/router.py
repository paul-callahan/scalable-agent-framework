"""
Execution routing logic for control plane microservice.

This module implements execution routing logic. Based on the execution type
(Task or Plan) and the next_task_ids from PlanResult, determines which
executor topics to publish to.
"""

from typing import Dict, List, Optional

from structlog import get_logger

from agentic_common.kafka_utils import (
    get_plan_results_topic,
    get_task_results_topic,
)

logger = get_logger(__name__)


class ExecutionRouter:
    """
    Execution router for control plane service.
    
    Routes TaskResults to plan-results_{tenant_id} topics and
    PlanResults to task-results_{tenant_id} topics based on
    execution type and next_task_ids.
    """
    
    def __init__(self):
        """Initialize the execution router."""
        pass
    
    def route_task_result(self, task_result: Dict[str, any], tenant_id: str) -> List[str]:
        """
        Route TaskResult to appropriate plan-results topic.
        
        Args:
            task_result: TaskResult data
            tenant_id: Tenant identifier
            
        Returns:
            List of target topics
        """
        try:
            # Route TaskResult to plan-results topic
            target_topic = get_plan_results_topic(tenant_id)
            
            logger.info("Routing TaskResult to plan-results", 
                       execution_id=task_result.get("execution_id"),
                       tenant_id=tenant_id,
                       target_topic=target_topic)
            
            return [target_topic]
            
        except Exception as e:
            logger.error("Failed to route TaskResult", 
                        task_result=task_result,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    def route_plan_result(self, plan_result: Dict[str, any], tenant_id: str) -> List[str]:
        """
        Route PlanResult to appropriate task-results topic.
        
        Args:
            plan_result: PlanResult data
            tenant_id: Tenant identifier
            
        Returns:
            List of target topics
        """
        try:
            # Route PlanResult to task-results topic
            target_topic = get_task_results_topic(tenant_id)
            
            logger.info("Routing PlanResult to task-results", 
                       execution_id=plan_result.get("execution_id"),
                       tenant_id=tenant_id,
                       target_topic=target_topic)
            
            return [target_topic]
            
        except Exception as e:
            logger.error("Failed to route PlanResult", 
                        plan_result=plan_result,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    def route_execution(self, execution_data: Dict[str, any], tenant_id: str) -> List[str]:
        """
        Route execution based on its type.
        
        Args:
            execution_data: Execution data
            tenant_id: Tenant identifier
            
        Returns:
            List of target topics
        """
        execution_type = execution_data.get("type")
        
        if execution_type == "task":
            return self.route_task_result(execution_data, tenant_id)
        elif execution_type == "plan":
            return self.route_plan_result(execution_data, tenant_id)
        else:
            logger.warning("Unknown execution type", 
                          execution_type=execution_type,
                          execution_id=execution_data.get("execution_id"))
            return []
    
    def get_routing_info(self, execution_data: Dict[str, any], tenant_id: str) -> Dict[str, any]:
        """
        Get routing information for an execution.
        
        Args:
            execution_data: Execution data
            tenant_id: Tenant identifier
            
        Returns:
            Routing information dictionary
        """
        try:
            execution_type = execution_data.get("type")
            execution_id = execution_data.get("execution_id")
            
            if execution_type == "task":
                target_topic = get_plan_results_topic(tenant_id)
                routing_type = "task_to_plan"
            elif execution_type == "plan":
                target_topic = get_task_results_topic(tenant_id)
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
                "execution_id": execution_data.get("execution_id"),
                "execution_type": execution_data.get("type"),
                "tenant_id": tenant_id,
                "target_topic": None,
                "routing_type": "error",
                "error": str(e),
            } 