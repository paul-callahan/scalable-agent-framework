"""
FastAPI application for executor microservice.

This module creates FastAPI application for the executor service with
health check endpoints using the common health utilities, task/plan
registry management endpoints, and administrative endpoints for monitoring
active executions.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from structlog import get_logger

from agentic_common.health import (
    HealthCheck,
    create_kafka_health_check,
    create_health_router,
    create_service_health_check,
)
from .registry import RegistryManager
from .kafka_consumer import ExecutorConsumer
from .kafka_producer import ExecutorProducer
from .task_executor import TaskExecutor
from .plan_executor import PlanExecutor

logger = get_logger(__name__)


class RegistryInfoResponse(BaseModel):
    """Response model for registry information."""
    tasks: Dict[str, Any]
    plans: Dict[str, Any]


class TaskInfoResponse(BaseModel):
    """Response model for task information."""
    task_type: str
    class_name: str
    module: str
    doc: Optional[str] = None


class PlanInfoResponse(BaseModel):
    """Response model for plan information."""
    plan_type: str
    class_name: str
    module: str
    doc: Optional[str] = None


class ExecutionRequest(BaseModel):
    """Request model for manual execution."""
    execution_type: str  # "task" or "plan"
    execution_id: str
    tenant_id: str
    type_name: str  # task_type or plan_type
    input_data: Dict[str, Any]


def create_executor_app(
    health_check: HealthCheck,
    consumer: ExecutorConsumer,
    producer: ExecutorProducer,
    registry_manager: RegistryManager,
    task_executor: TaskExecutor,
    plan_executor: PlanExecutor,
) -> FastAPI:
    """
    Create FastAPI application for executor service.
    
    Args:
        health_check: HealthCheck instance
        consumer: ExecutorConsumer instance
        producer: ExecutorProducer instance
        registry_manager: RegistryManager instance
        task_executor: TaskExecutor instance
        plan_executor: PlanExecutor instance
        
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="Executor Service",
        description="Executor microservice for agentic framework",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add health check router
    health_router = create_health_router(health_check)
    app.include_router(health_router)
    
    # Add service-specific endpoints
    @app.get("/registry", response_model=RegistryInfoResponse)
    async def get_registry_info():
        """
        Get registry information.
        
        Returns:
            Registry information
        """
        try:
            registry_info = registry_manager.get_registry_info()
            return RegistryInfoResponse(**registry_info)
            
        except Exception as e:
            logger.error("Failed to get registry info", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/tasks", response_model=List[str])
    async def list_task_types():
        """
        List available task types.
        
        Returns:
            List of task types
        """
        try:
            return task_executor.get_available_task_types()
            
        except Exception as e:
            logger.error("Failed to list task types", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/tasks/{task_type}", response_model=TaskInfoResponse)
    async def get_task_info(task_type: str):
        """
        Get information about a task type.
        
        Args:
            task_type: Task type identifier
            
        Returns:
            Task information
        """
        try:
            task_info = task_executor.get_task_info(task_type)
            if not task_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task type not found"
                )
            return TaskInfoResponse(**task_info)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get task info", task_type=task_type, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/plans", response_model=List[str])
    async def list_plan_types():
        """
        List available plan types.
        
        Returns:
            List of plan types
        """
        try:
            return plan_executor.get_available_plan_types()
            
        except Exception as e:
            logger.error("Failed to list plan types", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/plans/{plan_type}", response_model=PlanInfoResponse)
    async def get_plan_info(plan_type: str):
        """
        Get information about a plan type.
        
        Args:
            plan_type: Plan type identifier
            
        Returns:
            Plan information
        """
        try:
            plan_info = plan_executor.get_plan_info(plan_type)
            if not plan_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plan type not found"
                )
            return PlanInfoResponse(**plan_info)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get plan info", plan_type=plan_type, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.post("/execute")
    async def execute_manually(request: ExecutionRequest):
        """
        Execute a task or plan manually.
        
        Args:
            request: Execution request
            
        Returns:
            Execution result
        """
        try:
            if request.execution_type == "task":
                # Create a mock PlanResult for task execution
                from agentic.core.plan import PlanResult
                plan_result = PlanResult(
                    next_task_ids=[],
                    metadata=request.input_data,
                )
                
                result = await task_executor.execute_task(
                    task_type=request.type_name,
                    plan_result=plan_result,
                    execution_id=request.execution_id,
                    tenant_id=request.tenant_id,
                )
                
                if result:
                    await producer.publish_task_execution(
                        tenant_id=request.tenant_id,
                        task_execution=result,
                    )
                
            elif request.execution_type == "plan":
                # Create a mock TaskResult for plan execution
                from agentic.core.task import TaskResult
                task_result = TaskResult(
                    data=request.input_data,
                )
                
                result = await plan_executor.execute_plan(
                    plan_type=request.type_name,
                    task_result=task_result,
                    execution_id=request.execution_id,
                    tenant_id=request.tenant_id,
                )
                
                if result:
                    await producer.publish_plan_execution(
                        tenant_id=request.tenant_id,
                        plan_execution=result,
                    )
                
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid execution type. Must be 'task' or 'plan'"
                )
            
            return {"message": "Execution completed", "execution_id": request.execution_id}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to execute manually", 
                        request=request.dict(),
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/metrics")
    async def get_metrics():
        """
        Get service metrics.
        
        Returns:
            Service metrics
        """
        try:
            return {
                "consumer": {
                    "running": consumer.running,
                    "group_id": consumer.group_id,
                },
                "producer": {
                    "connected": await producer.health_check(),
                },
                "registry": {
                    "total_tasks": len(task_executor.get_available_task_types()),
                    "total_plans": len(plan_executor.get_available_plan_types()),
                },
            }
            
        except Exception as e:
            logger.error("Failed to get metrics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    return app 