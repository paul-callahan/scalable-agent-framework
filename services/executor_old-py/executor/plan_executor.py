"""
Plan execution logic for executor microservice.

This module implements plan execution logic. Consumes TaskResult messages
from plan-results_{tenant_id} topics, looks up the corresponding Plan class
from the registry, executes the plan with the TaskResult as input, and
emits PlanExecution messages.
"""

import json
from typing import Any, Dict, Optional

from structlog import get_logger

from agentic.core.plan import Plan, PlanResult
from agentic.core.task import TaskResult
from .registry import PlanRegistry

logger = get_logger(__name__)


class PlanExecutor:
    """
    Plan executor for the executor service.
    
    Handles plan execution by looking up Plan classes from the registry,
    executing them with TaskResult input, and producing PlanExecution messages.
    """
    
    def __init__(self, plan_registry: PlanRegistry):
        """
        Initialize the plan executor.
        
        Args:
            plan_registry: Plan registry instance
        """
        self.plan_registry = plan_registry
    
    async def execute_plan(
        self,
        plan_type: str,
        task_result: TaskResult,
        execution_id: str,
        tenant_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a plan with the given task result.
        
        Args:
            plan_type: Type of plan to execute
            task_result: TaskResult to use as input
            execution_id: Unique execution identifier
            tenant_id: Tenant identifier
            **kwargs: Additional arguments for plan creation
            
        Returns:
            PlanExecution data or None if execution failed
        """
        try:
            logger.info("Starting plan execution", 
                       plan_type=plan_type,
                       execution_id=execution_id,
                       tenant_id=tenant_id)
            
            # Look up plan class from registry
            plan_class = self.plan_registry.get_plan_class(plan_type)
            if not plan_class:
                logger.error("Plan type not found in registry", 
                            plan_type=plan_type,
                            execution_id=execution_id)
                return None
            
            # Create plan instance
            plan = self.plan_registry.create_plan(plan_type, **kwargs)
            if not plan:
                logger.error("Failed to create plan instance", 
                            plan_type=plan_type,
                            execution_id=execution_id)
                return None
            
            # Execute plan
            plan_result = await plan.plan(task_result)
            
            if not isinstance(plan_result, PlanResult):
                logger.error("Plan did not return PlanResult", 
                            plan_type=plan_type,
                            execution_id=execution_id,
                            result_type=type(plan_result))
                return None
            
            # Convert to protobuf
            plan_result_proto = plan_result.to_protobuf()
            
            # Create execution data
            execution_data = {
                "execution_id": execution_id,
                "plan_type": plan_type,
                "tenant_id": tenant_id,
                "result": {
                    "next_task_ids": plan_result.next_task_ids,
                    "metadata": plan_result.metadata,
                    "error_message": plan_result.error_message,
                    "confidence": plan_result.confidence,
                },
                "status": "SUCCEEDED" if not plan_result.error_message else "FAILED",
            }
            
            logger.info("Plan execution completed", 
                       plan_type=plan_type,
                       execution_id=execution_id,
                       status=execution_data["status"],
                       next_task_count=len(plan_result.next_task_ids))
            
            return execution_data
            
        except Exception as e:
            logger.error("Plan execution failed", 
                        plan_type=plan_type,
                        execution_id=execution_id,
                        error=str(e))
            
            # Return error execution data
            return {
                "execution_id": execution_id,
                "plan_type": plan_type,
                "tenant_id": tenant_id,
                "result": {
                    "next_task_ids": [],
                    "metadata": {},
                    "error_message": str(e),
                    "confidence": 0.0,
                },
                "status": "FAILED",
            }
    
    def validate_plan_type(self, plan_type: str) -> bool:
        """
        Validate that a plan type is registered.
        
        Args:
            plan_type: Plan type to validate
            
        Returns:
            True if plan type is valid
        """
        return self.plan_registry.is_plan_registered(plan_type)
    
    def get_available_plan_types(self) -> list[str]:
        """
        Get list of available plan types.
        
        Returns:
            List of registered plan types
        """
        return self.plan_registry.list_plan_types()
    
    def get_plan_info(self, plan_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a plan type.
        
        Args:
            plan_type: Plan type identifier
            
        Returns:
            Plan information or None if not found
        """
        plan_class = self.plan_registry.get_plan_class(plan_type)
        if not plan_class:
            return None
        
        return {
            "plan_type": plan_type,
            "class_name": plan_class.__name__,
            "module": plan_class.__module__,
            "doc": plan_class.__doc__,
        }
    
    def validate_next_task_ids(self, next_task_ids: list[str], available_tasks: list[str]) -> Dict[str, Any]:
        """
        Validate that next_task_ids are available.
        
        Args:
            next_task_ids: List of task IDs to validate
            available_tasks: List of available task types
            
        Returns:
            Validation result with details
        """
        valid_tasks = []
        invalid_tasks = []
        
        for task_id in next_task_ids:
            if task_id in available_tasks:
                valid_tasks.append(task_id)
            else:
                invalid_tasks.append(task_id)
        
        return {
            "valid_tasks": valid_tasks,
            "invalid_tasks": invalid_tasks,
            "all_valid": len(invalid_tasks) == 0,
            "total_requested": len(next_task_ids),
            "total_valid": len(valid_tasks),
            "total_invalid": len(invalid_tasks),
        } 