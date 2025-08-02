"""
FastAPI application for data plane microservice.

This module creates FastAPI application for the data plane service with
health check endpoints using the common health utilities, metrics endpoints,
and administrative endpoints for querying execution status.
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from structlog import get_logger

from agentic_common.health import (
    HealthCheck,
    create_database_health_check,
    create_kafka_health_check,
    create_health_router,
    create_service_health_check,
)
from .database import get_database_manager
from .kafka_consumer import DataPlaneConsumer
from .kafka_producer import DataPlaneProducer
from .models import PlanExecution, TaskExecution

logger = get_logger(__name__)


class ExecutionStatusResponse(BaseModel):
    """Response model for execution status queries."""
    execution_id: str
    tenant_id: str
    status: str
    created_at: str
    updated_at: Optional[str] = None


class ExecutionListResponse(BaseModel):
    """Response model for execution list queries."""
    executions: List[ExecutionStatusResponse]
    total_count: int
    page: int
    page_size: int


def create_data_plane_app(
    health_check: HealthCheck,
    consumer: DataPlaneConsumer,
    producer: DataPlaneProducer,
) -> FastAPI:
    """
    Create FastAPI application for data plane service.
    
    Args:
        health_check: HealthCheck instance
        consumer: DataPlaneConsumer instance
        producer: DataPlaneProducer instance
        
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="Data Plane Service",
        description="Data plane microservice for agentic framework",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add health check router
    health_router = create_health_router(health_check)
    app.include_router(health_router)
    
    # Add service-specific endpoints
    @app.get("/executions/tasks/{execution_id}", response_model=ExecutionStatusResponse)
    async def get_task_execution_status(
        execution_id: str,
        tenant_id: str = Query(..., description="Tenant identifier")
    ):
        """
        Get task execution status.
        
        Args:
            execution_id: Task execution ID
            tenant_id: Tenant identifier
            
        Returns:
            Task execution status
        """
        try:
            db_mgr = await get_database_manager()
            async for session in db_mgr.get_async_session():
                # Query task execution using ORM
                stmt = select(TaskExecution).where(
                    TaskExecution.id == execution_id,
                    TaskExecution.tenant_id == tenant_id
                )
                result = await session.execute(stmt)
                task_execution = result.scalar_one_or_none()
                
                if not task_execution:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Task execution not found"
                    )
                
                return ExecutionStatusResponse(
                    execution_id=task_execution.id,
                    tenant_id=task_execution.tenant_id,
                    status=task_execution.status,
                    created_at=task_execution.created_at,
                    updated_at=task_execution.db_updated_at.isoformat() if task_execution.db_updated_at else None,
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get task execution status", 
                        execution_id=execution_id,
                        tenant_id=tenant_id,
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/executions/plans/{execution_id}", response_model=ExecutionStatusResponse)
    async def get_plan_execution_status(
        execution_id: str,
        tenant_id: str = Query(..., description="Tenant identifier")
    ):
        """
        Get plan execution status.
        
        Args:
            execution_id: Plan execution ID
            tenant_id: Tenant identifier
            
        Returns:
            Plan execution status
        """
        try:
            db_mgr = await get_database_manager()
            async for session in db_mgr.get_async_session():
                # Query plan execution using ORM
                stmt = select(PlanExecution).where(
                    PlanExecution.id == execution_id,
                    PlanExecution.tenant_id == tenant_id
                )
                result = await session.execute(stmt)
                plan_execution = result.scalar_one_or_none()
                
                if not plan_execution:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Plan execution not found"
                    )
                
                return ExecutionStatusResponse(
                    execution_id=plan_execution.id,
                    tenant_id=plan_execution.tenant_id,
                    status=plan_execution.status,
                    created_at=plan_execution.created_at,
                    updated_at=plan_execution.db_updated_at.isoformat() if plan_execution.db_updated_at else None,
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get plan execution status", 
                        execution_id=execution_id,
                        tenant_id=tenant_id,
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/executions/tasks", response_model=ExecutionListResponse)
    async def list_task_executions(
        tenant_id: str = Query(..., description="Tenant identifier"),
        status: Optional[str] = Query(None, description="Filter by status"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Page size")
    ):
        """
        List task executions.
        
        Args:
            tenant_id: Tenant identifier
            status: Optional status filter
            page: Page number
            page_size: Page size
            
        Returns:
            List of task executions
        """
        try:
            db_mgr = await get_database_manager()
            async for session in db_mgr.get_async_session():
                # Build query using ORM
                query = select(TaskExecution).where(TaskExecution.tenant_id == tenant_id)
                
                if status:
                    query = query.where(TaskExecution.status == status)
                
                # Add ordering
                query = query.order_by(TaskExecution.created_at.desc())
                
                # Add pagination
                query = query.offset((page - 1) * page_size).limit(page_size)
                
                # Execute query
                result = await session.execute(query)
                task_executions = result.scalars().all()
                
                # Get total count using ORM
                count_query = select(func.count(TaskExecution.id)).where(TaskExecution.tenant_id == tenant_id)
                
                if status:
                    count_query = count_query.where(TaskExecution.status == status)
                
                count_result = await session.execute(count_query)
                total_count = count_result.scalar()
                
                # Build response
                executions = [
                    ExecutionStatusResponse(
                        execution_id=task_execution.id,
                        tenant_id=task_execution.tenant_id,
                        status=task_execution.status,
                        created_at=task_execution.created_at,
                        updated_at=task_execution.db_updated_at.isoformat() if task_execution.db_updated_at else None,
                    )
                    for task_execution in task_executions
                ]
                
                return ExecutionListResponse(
                    executions=executions,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                )
                
        except Exception as e:
            logger.error("Failed to list task executions", 
                        tenant_id=tenant_id,
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/executions/plans", response_model=ExecutionListResponse)
    async def list_plan_executions(
        tenant_id: str = Query(..., description="Tenant identifier"),
        status: Optional[str] = Query(None, description="Filter by status"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Page size")
    ):
        """
        List plan executions.
        
        Args:
            tenant_id: Tenant identifier
            status: Optional status filter
            page: Page number
            page_size: Page size
            
        Returns:
            List of plan executions
        """
        try:
            db_mgr = await get_database_manager()
            async for session in db_mgr.get_async_session():
                # Build query using ORM
                query = select(PlanExecution).where(PlanExecution.tenant_id == tenant_id)
                
                if status:
                    query = query.where(PlanExecution.status == status)
                
                # Add ordering
                query = query.order_by(PlanExecution.created_at.desc())
                
                # Add pagination
                query = query.offset((page - 1) * page_size).limit(page_size)
                
                # Execute query
                result = await session.execute(query)
                plan_executions = result.scalars().all()
                
                # Get total count using ORM
                count_query = select(func.count(PlanExecution.id)).where(PlanExecution.tenant_id == tenant_id)
                
                if status:
                    count_query = count_query.where(PlanExecution.status == status)
                
                count_result = await session.execute(count_query)
                total_count = count_result.scalar()
                
                # Build response
                executions = [
                    ExecutionStatusResponse(
                        execution_id=plan_execution.id,
                        tenant_id=plan_execution.tenant_id,
                        status=plan_execution.status,
                        created_at=plan_execution.created_at,
                        updated_at=plan_execution.db_updated_at.isoformat() if plan_execution.db_updated_at else None,
                    )
                    for plan_execution in plan_executions
                ]
                
                return ExecutionListResponse(
                    executions=executions,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                )
                
        except Exception as e:
            logger.error("Failed to list plan executions", 
                        tenant_id=tenant_id,
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
            db_mgr = await get_database_manager()
            
            return {
                "database": db_mgr.get_connection_info(),
                "consumer": {
                    "running": consumer.running,
                    "group_id": consumer.group_id,
                },
                "producer": {
                    "connected": await producer.health_check(),
                },
            }
            
        except Exception as e:
            logger.error("Failed to get metrics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    return app 