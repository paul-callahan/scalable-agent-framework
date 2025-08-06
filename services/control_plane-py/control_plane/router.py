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
    get_plan_inputs_topic,
)
from agentic_common.pb import TaskExecution, PlanExecution, PlanInput

logger = get_logger(__name__)


class ExecutionRouter:
    """
    Execution router for control plane service.
    
    Routes TaskExecutions to plan-inputs_{tenant_id} topics after examining
    the TaskExecution and looking up the next Plan in the graph. Routes
    PlanExecutions to controlled-plan-executions_{tenant_id} topics.
    """
    
    def __init__(self):
        """Initialize the execution router."""
        pass
    
    def route_task_execution(self, task_execution: TaskExecution, tenant_id: str) -> List[str]:
        """
        Route TaskExecution to appropriate plan-inputs topic after Next Plan Prep.
        
        Args:
            task_execution: TaskExecution protobuf message
            tenant_id: Tenant identifier
            
        Returns:
            List of target topics
        """
        try:
            # Examine TaskExecution and look up the next Plan in the graph
            next_plan_name = self._lookup_next_plan_in_graph(task_execution, tenant_id)
            
            # Create PlanInput with the next plan information
            plan_input = PlanInput(
                input_id=task_execution.header.exec_id,
                plan_name=next_plan_name,
                task_executions=[task_execution]
            )
            
            # Route PlanInput to plan-inputs topic
            target_topic = get_plan_inputs_topic(tenant_id)
            
            logger.info("TaskExecution examined and next plan routed to plan-inputs", 
                       execution_id=task_execution.header.exec_id,
                       tenant_id=tenant_id,
                       next_plan_name=next_plan_name,
                       target_topic=target_topic)
            
            return [target_topic]
            
        except Exception as e:
            logger.error("Failed to route TaskExecution", 
                        task_execution=task_execution,
                        tenant_id=tenant_id,
                        error=str(e))
            raise
    
    def _lookup_next_plan_in_graph(self, task_execution: TaskExecution, tenant_id: str) -> str:
        """
        Look up the next Plan in the graph based on TaskExecution.
        
        Args:
            task_execution: TaskExecution to examine
            tenant_id: Tenant identifier
            
        Returns:
            Name of the next plan in the graph path
        """
        # TODO: Implement actual graph lookup logic
        # This should examine the TaskExecution and determine the next plan in the graph
        # For now, return a stub implementation
        logger.debug("Looking up next plan in graph for task execution", 
                   execution_id=task_execution.header.exec_id,
                   tenant_id=tenant_id)
        
        # Stub implementation - replace with actual graph lookup
        # This could involve:
        # 1. Loading the agent graph for the tenant
        # 2. Examining the task_execution.header.name to identify the current task
        # 3. Looking up outgoing edges from this task to find the next plan
        # 4. Returning the plan name
        
        return "next-plan-stub"
    
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
                next_plan_name = self._lookup_next_plan_in_graph(execution_data, tenant_id)
                target_topic = get_plan_inputs_topic(tenant_id)
                routing_type = "task_to_plan"
            elif isinstance(execution_data, PlanExecution):
                execution_type = "plan"
                execution_id = execution_data.header.exec_id
                target_topic = get_controlled_plan_executions_topic(tenant_id)
                routing_type = "plan_to_task"
                next_plan_name = None
            else:
                # Handle dictionary format (for backward compatibility)
                execution_type = execution_data.get("type")
                execution_id = execution_data.get("execution_id")
                
                if execution_type == "task":
                    target_topic = get_plan_inputs_topic(tenant_id)
                    routing_type = "task_to_plan"
                    next_plan_name = "next-plan-stub"  # Stub for dict format
                elif execution_type == "plan":
                    target_topic = get_controlled_plan_executions_topic(tenant_id)
                    routing_type = "plan_to_task"
                    next_plan_name = None
                else:
                    target_topic = None
                    routing_type = "unknown"
                    next_plan_name = None
            
            return {
                "execution_id": execution_id,
                "execution_type": execution_type,
                "tenant_id": tenant_id,
                "target_topic": target_topic,
                "routing_type": routing_type,
                "next_plan_name": next_plan_name,
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
                "next_plan_name": None,
                "error": str(e),
            } 