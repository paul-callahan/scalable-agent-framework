"""
Pytest configuration and shared fixtures for executors-py tests.
"""

import os
import tempfile
import uuid
from datetime import datetime, UTC
from typing import Generator

import pytest
from mockafka.aiokafka import aiokafka_consumer, aiokafka_producer

from agentic_common.pb import (
    ExecutionHeader,
    ExecutionStatus,
    PlanExecution,
    PlanInput,
    PlanResult,
    TaskExecution,
    TaskInput,
    TaskResult,
)


@pytest.fixture(scope="session")
def mockafka_patch():
    """Mockafka-py fixture for testing."""
    # Mockafka-py doesn't have a patch function, so we'll use the mock objects directly
    yield


@pytest.fixture
def test_config():
    """Common test configuration."""
    return {
        "tenant_id": "test-tenant",
        "plan_name": "test-plan",
        "task_name": "test-task",
        "bootstrap_servers": "localhost:9092",
        "group_id": "test-group",
        "plan_timeout": 30,
        "task_timeout": 30,
    }


@pytest.fixture
def temp_plan_file() -> Generator[str, None, None]:
    """Create a temporary plan.py file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
from agentic_common.pb import PlanInput, PlanResult

def plan(plan_input):
    \"\"\"Sample plan implementation for testing.\"\"\"
    return PlanResult(
        next_task_names=["sample-task"],
        upstream_tasks_results=[],
        error_message=""
    )
""")
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except OSError:
        pass


@pytest.fixture
def temp_task_file() -> Generator[str, None, None]:
    """Create a temporary task.py file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
from agentic_common.pb import TaskInput, TaskResult
import google.protobuf.any_pb2

def task(task_input):
    \"\"\"Sample task implementation for testing.\"\"\"
    any_data = google.protobuf.any_pb2.Any()
    any_data.type_url = "type.googleapis.com/google.protobuf.StringValue"
    any_data.value = "sample-task-result".encode('utf-8')
    return TaskResult(
        id="sample-task-result",
        inline_data=any_data,
        error_message=""
    )
""")
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except OSError:
        pass


@pytest.fixture
def sample_plan_input(test_config) -> PlanInput:
    """Create a sample PlanInput message for testing."""
    return PlanInput(
        input_id="test-input-123",
        plan_name=test_config["plan_name"],
        task_executions=[]
    )


@pytest.fixture
def sample_task_input(test_config) -> TaskInput:
    """Create a sample TaskInput message for testing."""
    return TaskInput(
        input_id="test-task-input-123",
        task_name=test_config["task_name"],
        plan_execution=None
    )


@pytest.fixture
def sample_plan_execution(test_config) -> PlanExecution:
    """Create a sample PlanExecution message for testing."""
    from datetime import datetime, UTC
    
    header = ExecutionHeader(
        name=test_config["plan_name"],
        exec_id="test-exec-123",
        tenant_id=test_config["tenant_id"],
        created_at=datetime.now(UTC).isoformat(),
        status=ExecutionStatus.EXECUTION_STATUS_SUCCEEDED
    )
    
    result = PlanResult(
        upstream_tasks_results=[],
        next_task_names=["sample-task"],
        error_message=""
    )
    
    return PlanExecution(
        header=header,
        result=result
    )


@pytest.fixture
def sample_task_execution(test_config) -> TaskExecution:
    """Create a sample TaskExecution message for testing."""
    from datetime import datetime, UTC
    
    header = ExecutionHeader(
        name=test_config["task_name"],
        exec_id="test-task-exec-123",
        tenant_id=test_config["tenant_id"],
        created_at=datetime.now(UTC).isoformat(),
        status=ExecutionStatus.EXECUTION_STATUS_SUCCEEDED
    )
    
    result = TaskResult(
        id="test-task-result-123",
        error_message=""
    )
    
    return TaskExecution(
        header=header,
        parent_plan_exec_id="parent-plan-123",
        result=result,
        parent_plan_name=test_config["plan_name"]
    ) 