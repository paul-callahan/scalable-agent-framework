#!/usr/bin/env python3
"""
Simple test to verify protobuf TaskExecution construction works.
"""

from agentic_common.pb import TaskExecution

def test_task_execution_construction():
    """Test that we can construct a TaskExecution protobuf message."""
    task_execution = TaskExecution(
        header=None,
        parent_plan_exec_id="test-plan-exec-id",
        result=None,
        parent_plan_name="test-plan"
    )
    print(f"Successfully constructed TaskExecution: {task_execution}")

if __name__ == "__main__":
    test_task_execution_construction()
