"""
FastAPI application for control plane microservice.

This module creates FastAPI application for the control plane service with
health check endpoints using the common health utilities, guardrail policy
management endpoints, and administrative endpoints for monitoring and control.
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
from .guardrails import GuardrailEngine, GuardrailResult
from .kafka_consumer import ControlPlaneConsumer
from .kafka_producer import ControlPlaneProducer
from .router import ExecutionRouter

logger = get_logger(__name__)


class PolicyUpdateRequest(BaseModel):
    """Request model for policy updates."""
    policies: Dict[str, Any]


class PolicyResponse(BaseModel):
    """Response model for policy queries."""
    policies: Dict[str, Any]


class GuardrailEvaluationRequest(BaseModel):
    """Request model for guardrail evaluation."""
    execution_data: Dict[str, Any]


class GuardrailEvaluationResponse(BaseModel):
    """Response model for guardrail evaluation."""
    passed: bool
    violations: List[Dict[str, Any]]


class RoutingInfoResponse(BaseModel):
    """Response model for routing information."""
    execution_id: str
    execution_type: str
    tenant_id: str
    target_topic: Optional[str]
    routing_type: str


def create_control_plane_app(
    health_check: HealthCheck,
    consumer: ControlPlaneConsumer,
    producer: ControlPlaneProducer,
    guardrail_engine: GuardrailEngine,
    router: ExecutionRouter,
) -> FastAPI:
    """
    Create FastAPI application for control plane service.
    
    Args:
        health_check: HealthCheck instance
        consumer: ControlPlaneConsumer instance
        producer: ControlPlaneProducer instance
        guardrail_engine: GuardrailEngine instance
        router: ExecutionRouter instance
        
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="Control Plane Service",
        description="Control plane microservice for agentic framework",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add health check router
    health_router = create_health_router(health_check)
    app.include_router(health_router)
    
    # Add service-specific endpoints
    @app.get("/policies", response_model=PolicyResponse)
    async def get_policies():
        """
        Get current guardrail policies.
        
        Returns:
            Current policies
        """
        try:
            policies = guardrail_engine.get_policies()
            return PolicyResponse(policies=policies)
            
        except Exception as e:
            logger.error("Failed to get policies", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.post("/policies", response_model=PolicyResponse)
    async def update_policies(request: PolicyUpdateRequest):
        """
        Update guardrail policies.
        
        Args:
            request: Policy update request
            
        Returns:
            Updated policies
        """
        try:
            guardrail_engine.update_policies(request.policies)
            policies = guardrail_engine.get_policies()
            return PolicyResponse(policies=policies)
            
        except Exception as e:
            logger.error("Failed to update policies", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.post("/policies/reload", response_model=PolicyResponse)
    async def reload_policies():
        """
        Reload policies from file.
        
        Returns:
            Reloaded policies
        """
        try:
            guardrail_engine.reload_policies()
            policies = guardrail_engine.get_policies()
            return PolicyResponse(policies=policies)
            
        except Exception as e:
            logger.error("Failed to reload policies", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.post("/guardrails/evaluate", response_model=GuardrailEvaluationResponse)
    async def evaluate_guardrails(request: GuardrailEvaluationRequest):
        """
        Evaluate execution against guardrails.
        
        Args:
            request: Guardrail evaluation request
            
        Returns:
            Guardrail evaluation result
        """
        try:
            result = guardrail_engine.evaluate_execution(request.execution_data)
            return GuardrailEvaluationResponse(
                passed=result.passed,
                violations=[v.to_dict() for v in result.violations]
            )
            
        except Exception as e:
            logger.error("Failed to evaluate guardrails", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/routing/info", response_model=RoutingInfoResponse)
    async def get_routing_info(
        execution_data: str = Query(..., description="JSON execution data"),
        tenant_id: str = Query(..., description="Tenant identifier")
    ):
        """
        Get routing information for an execution.
        
        Args:
            execution_data: JSON string of execution data
            tenant_id: Tenant identifier
            
        Returns:
            Routing information
        """
        try:
            import json
            data = json.loads(execution_data)
            routing_info = router.get_routing_info(data, tenant_id)
            return RoutingInfoResponse(**routing_info)
            
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in execution data", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON in execution data"
            )
        except Exception as e:
            logger.error("Failed to get routing info", error=str(e))
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
                "guardrail_engine": {
                    "policies_loaded": len(guardrail_engine.get_policies()) > 0,
                },
            }
            
        except Exception as e:
            logger.error("Failed to get metrics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.post("/test/publish")
    async def test_publish(
        tenant_id: str = Query(..., description="Tenant identifier"),
        execution_type: str = Query(..., description="Execution type (task/plan)"),
        execution_id: str = Query(..., description="Execution ID")
    ):
        """
        Test endpoint for publishing execution results.
        
        Args:
            tenant_id: Tenant identifier
            execution_type: Execution type
            execution_id: Execution ID
        """
        try:
            test_data = {
                "execution_id": execution_id,
                "type": execution_type,
                "status": "SUCCEEDED",
                "result": {"test": "data"},
            }
            
            await producer.publish_execution_result(tenant_id, test_data)
            
            return {"message": "Test message published successfully"}
            
        except Exception as e:
            logger.error("Failed to publish test message", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    return app 