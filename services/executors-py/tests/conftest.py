"""
Pytest configuration and shared fixtures for executors-py tests.
"""

import os
import tempfile
import uuid
from datetime import datetime, UTC
from typing import Generator

import pytest
from google.protobuf import any_pb2, wrappers_pb2
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
def mockafka_setup():
    """Setup mockafka environment for Kafka message flow testing."""
    # Configure mock topics for testing
    topics = [
        "task-inputs-test-tenant",
        "task-executions-test-tenant", 
        "plan-inputs-test-tenant",
        "plan-executions-test-tenant"
    ]
    
    # Mockafka will handle topic creation automatically
    yield topics


@pytest.fixture
def test_config():
    """Common test configuration."""
    return {
        "tenant_id": "evil-corp",
        "plan_name": "what_llm_should_we_use",
        "task_name": "query_llm",
        "bootstrap_servers": "localhost:9092",
        "group_id": "executors",
        "plan_timeout": 30,
        "task_timeout": 30,
        "task_input_topic": "task-inputs-evil-corp",
        "task_execution_topic": "task-executions-evil-corp",
        "plan_input_topic": "plan-inputs-evil-corp",
        "plan_execution_topic": "plan-executions-evil-corp",
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
def sample_plan_input_lite(test_config) -> PlanInput:
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
def sample_task_input_with_key(test_config) -> TaskInput:
    """Create a sample TaskInput message with specific task_name for key filtering tests."""
    return TaskInput(
        input_id="test-task-input-with-key-123",
        task_name=test_config["task_name"],  # This will be used as the message key
        plan_execution=None
    )


@pytest.fixture
def sample_plan_input_with_key(test_config) -> PlanInput:
    """Create a sample PlanInput message with specific plan_name for key filtering tests."""
    return PlanInput(
        input_id="test-plan-input-with-key-123",
        plan_name=test_config["plan_name"],  # This will be used as the message key
        task_executions=[]
    )


@pytest.fixture
def error_task_input(test_config) -> TaskInput:
    """Create a TaskInput that will cause task execution to fail."""
    return TaskInput(
        input_id="error-task-input-123",
        task_name=test_config["task_name"],
        plan_execution=None
    )


@pytest.fixture
def error_plan_input(test_config) -> PlanInput:
    """Create a PlanInput that will cause plan execution to fail."""
    return PlanInput(
        input_id="error-plan-input-123",
        plan_name=test_config["plan_name"],
        task_executions=[]
    )


@pytest.fixture
def invalid_protobuf_data() -> bytes:
    """Create invalid protobuf data for testing deserialization errors."""
    return b"invalid protobuf data"


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


def sample_plan_input_full() -> PlanInput:
    return PlanInput(
        plan_name="decide_which_llm_to_use",
        task_executions=[TaskExecution(
            header=ExecutionHeader(
                name="previous_task_name",
                tenant_id="evil_corp",
                exec_id="1234f",
            ),
            result=TaskResult(
                id="",
                inline_data=any_pb2.Any(
                    value=wrappers_pb2.StringValue(value="hello").SerializeToString(),
                    type_url="type.googleapis.com/google.protobuf.StringValue",
                )
            ),
        )]
    )

def serialize_protobuf_message(message) -> bytes:
    """Helper function to serialize protobuf messages for testing."""
    return message.SerializeToString()


def deserialize_protobuf_message(data: bytes, message_type):
    """Helper function to deserialize protobuf messages for testing."""
    return message_type.FromString(data) 