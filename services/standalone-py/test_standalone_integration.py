#!/usr/bin/env python3
"""
Integration test for the standalone agentic framework.

This test verifies that the in-memory message broker and services work correctly
together by simulating a complete message flow.
"""

import asyncio
import json
import uuid
from datetime import datetime

from agentic import (
    InMemoryBroker, 
    DataPlaneService, 
    ControlPlaneService,
    TaskExecutorService,
    PlanExecutorService
)
from agentic.pb import task_pb2, plan_pb2, common_pb2


async def test_standalone_integration():
    """Test the complete standalone integration."""
    print("Starting standalone integration test...")
    
    # Create shared broker
    broker = InMemoryBroker()
    
    # Create services
    data_plane = DataPlaneService(broker=broker, db_path=":memory:")
    control_plane = ControlPlaneService(broker=broker)
    task_executor = TaskExecutorService(broker=broker)
    plan_executor = PlanExecutorService(broker=broker)
    
    # Register some test tasks and plans
    def test_task_handler(parameters):
        return {"result": f"Task executed with parameters: {parameters}", "status": "success"}
    
    def test_plan_handler(parameters, input_task_id):
        return {
            "next_task_ids": [f"next_task_{uuid.uuid4().hex[:8]}"],
            "metadata": {"input_task_id": input_task_id},
            "confidence": 0.9
        }
    
    task_executor.register_task("test_task", test_task_handler)
    plan_executor.register_plan("test_plan", test_plan_handler)
    
    # Start all services
    tenant_id = "test_tenant"
    await asyncio.gather(
        data_plane.start(tenant_id=tenant_id),
        control_plane.start(tenant_id=tenant_id),
        task_executor.start(tenant_id=tenant_id),
        plan_executor.start(tenant_id=tenant_id)
    )
    
    print("All services started successfully")
    
    # Wait a moment for services to initialize
    await asyncio.sleep(0.1)
    
    # Test task execution flow
    print("\n--- Testing Task Execution Flow ---")
    
    # Create a test task execution
    task_execution = task_pb2.TaskExecution()
    task_execution.header.id = f"task_{uuid.uuid4().hex[:8]}"
    task_execution.header.tenant_id = tenant_id
    task_execution.header.status = common_pb2.EXECUTION_STATUS_PENDING
    task_execution.header.created_at = datetime.utcnow().isoformat()
    task_execution.task_type = "test_task"
    task_execution.parameters = json.dumps({"test_param": "test_value"})
    
    # Publish to task-executions queue
    task_executions_topic = f"task-executions_{tenant_id}"
    task_bytes = task_execution.SerializeToString()
    await broker.publish(task_executions_topic, task_bytes)
    
    print(f"Published task execution: {task_execution.header.id}")
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    # Test plan execution flow
    print("\n--- Testing Plan Execution Flow ---")
    
    # Create a test plan execution
    plan_execution = plan_pb2.PlanExecution()
    plan_execution.header.id = f"plan_{uuid.uuid4().hex[:8]}"
    plan_execution.header.tenant_id = tenant_id
    plan_execution.header.status = common_pb2.EXECUTION_STATUS_PENDING
    plan_execution.header.created_at = datetime.utcnow().isoformat()
    plan_execution.plan_type = "test_plan"
    plan_execution.parameters = json.dumps({"plan_param": "plan_value"})
    plan_execution.input_task_id = task_execution.header.id
    
    # Publish to plan-executions queue
    plan_executions_topic = f"plan-executions_{tenant_id}"
    plan_bytes = plan_execution.SerializeToString()
    await broker.publish(plan_executions_topic, plan_bytes)
    
    print(f"Published plan execution: {plan_execution.header.id}")
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    # Print metrics
    print("\n--- Service Metrics ---")
    print(f"Data Plane: {data_plane.get_metrics()}")
    print(f"Control Plane: {control_plane.get_metrics()}")
    print(f"Task Executor: {task_executor.get_metrics()}")
    print(f"Plan Executor: {plan_executor.get_metrics()}")
    print(f"Broker: {broker.get_metrics()}")
    
    # Stop all services
    await asyncio.gather(
        data_plane.stop(),
        control_plane.stop(),
        task_executor.stop(),
        plan_executor.stop(),
        return_exceptions=True
    )
    await broker.shutdown()
    
    print("\nIntegration test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_standalone_integration()) 