"""
Sample task implementation for testing.
"""

from agentic_common.pb import TaskInput, TaskResult
import google.protobuf.any_pb2


def task(task_input: TaskInput) -> TaskResult:
    """Sample task implementation for testing."""
    any_data = google.protobuf.any_pb2.Any()
    any_data.type_url = "type.googleapis.com/google.protobuf.StringValue"
    any_data.value = "hello world".encode('utf-8')
    
    return TaskResult(
        id="sample-task-result",
        inline_data=any_data,
        error_message=""
    ) 