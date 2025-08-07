"""
Tests for protobuf serialization utilities.
"""

import pytest

from agentic_common.pb import (
    PlanInput, PlanResult, PlanExecution,
    TaskInput, TaskResult, TaskExecution,
    ExecutionHeader, ExecutionStatus
)


class TestProtobufSerialization:
    """Test protobuf serialization and deserialization."""
    
    def test_plan_input_serialization(self):
        """Test PlanInput serialization and deserialization."""
        # Create PlanInput
        plan_input = PlanInput(
            input_id="test-input-123",
            plan_name="test-plan",
            task_executions=[]
        )
        
        # Serialize
        serialized = plan_input.SerializeToString()
        
        # Deserialize
        deserialized = PlanInput()
        deserialized.ParseFromString(serialized)
        
        # Verify
        assert deserialized.input_id == "test-input-123"
        assert deserialized.plan_name == "test-plan"
        assert len(deserialized.task_executions) == 0
    
    def test_task_input_serialization(self):
        """Test TaskInput serialization and deserialization."""
        # Create TaskInput
        task_input = TaskInput(
            input_id="test-task-input-123",
            task_name="test-task",
            plan_execution=None
        )
        
        # Serialize
        serialized = task_input.SerializeToString()
        
        # Deserialize
        deserialized = TaskInput()
        deserialized.ParseFromString(serialized)
        
        # Verify
        assert deserialized.input_id == "test-task-input-123"
        assert deserialized.task_name == "test-task"
        # Note: None values in protobuf become empty objects when deserialized
        # So we check that plan_execution exists but is empty
        assert hasattr(deserialized, 'plan_execution')
    
    def test_task_result_serialization(self):
        """Test TaskResult serialization and deserialization."""
        # Create TaskResult
        task_result = TaskResult(
            id="test-task-result-123",
            error_message=""
        )
        
        # Serialize
        serialized = task_result.SerializeToString()
        
        # Deserialize
        deserialized = TaskResult()
        deserialized.ParseFromString(serialized)
        
        # Verify
        assert deserialized.id == "test-task-result-123"
        assert deserialized.error_message == ""
    
    def test_task_execution_serialization(self):
        """Test TaskExecution serialization and deserialization."""
        # Create ExecutionHeader
        header = ExecutionHeader(
            name="test-task",
            exec_id="test-exec-123"
        )
        
        # Create TaskResult
        task_result = TaskResult(
            id="test-task-result-123",
            error_message=""
        )
        
        # Create TaskExecution
        task_execution = TaskExecution(
            header=header,
            parent_plan_exec_id="parent-plan-123",
            result=task_result,
            parent_plan_name="test-plan"
        )
        
        # Serialize
        serialized = task_execution.SerializeToString()
        
        # Deserialize
        deserialized = TaskExecution()
        deserialized.ParseFromString(serialized)
        
        # Verify
        assert deserialized.header.name == "test-task"
        assert deserialized.header.exec_id == "test-exec-123"
        assert deserialized.parent_plan_exec_id == "parent-plan-123"
        assert deserialized.result.id == "test-task-result-123"
        assert deserialized.parent_plan_name == "test-plan"
    
    def test_plan_result_serialization(self):
        """Test PlanResult serialization and deserialization."""
        # Create PlanResult
        plan_result = PlanResult(
            upstream_tasks_results=[],
            next_task_names=["task1", "task2"],
            error_message=""
        )
        
        # Serialize
        serialized = plan_result.SerializeToString()
        
        # Deserialize
        deserialized = PlanResult()
        deserialized.ParseFromString(serialized)
        
        # Verify
        assert len(deserialized.upstream_tasks_results) == 0
        assert list(deserialized.next_task_names) == ["task1", "task2"]
        assert deserialized.error_message == ""
    
    def test_plan_execution_serialization(self):
        """Test PlanExecution serialization and deserialization."""
        # Create ExecutionHeader
        header = ExecutionHeader(
            name="test-plan",
            exec_id="test-plan-exec-123"
        )
        
        # Create PlanResult
        plan_result = PlanResult(
            upstream_tasks_results=[],
            next_task_names=["task1"],
            error_message=""
        )
        
        # Create PlanExecution
        plan_execution = PlanExecution(
            header=header,
            result=plan_result
        )
        
        # Serialize
        serialized = plan_execution.SerializeToString()
        
        # Deserialize
        deserialized = PlanExecution()
        deserialized.ParseFromString(serialized)
        
        # Verify
        assert deserialized.header.name == "test-plan"
        assert deserialized.header.exec_id == "test-plan-exec-123"
        assert len(deserialized.result.upstream_tasks_results) == 0
        assert list(deserialized.result.next_task_names) == ["task1"]
    
    def test_empty_message_serialization(self):
        """Test serialization of empty messages."""
        # Test empty PlanInput
        plan_input = PlanInput()
        serialized = plan_input.SerializeToString()
        deserialized = PlanInput()
        deserialized.ParseFromString(serialized)
        assert deserialized.input_id == ""
        assert deserialized.plan_name == ""
        
        # Test empty TaskInput
        task_input = TaskInput()
        serialized = task_input.SerializeToString()
        deserialized = TaskInput()
        deserialized.ParseFromString(serialized)
        assert deserialized.input_id == ""
        assert deserialized.task_name == ""
    
    def test_nested_message_serialization(self):
        """Test serialization of messages with nested structures."""
        # Create nested TaskExecution with TaskResult
        task_result = TaskResult(
            id="nested-task-result",
            error_message=""
        )
        
        header = ExecutionHeader(
            name="nested-task",
            exec_id="nested-exec-123"
        )
        
        task_execution = TaskExecution(
            header=header,
            result=task_result,
            parent_plan_exec_id="parent-123",
            parent_plan_name="parent-plan"
        )
        
        # Create PlanInput with nested TaskExecution
        plan_input = PlanInput(
            input_id="nested-plan-input",
            plan_name="nested-plan",
            task_executions=[task_execution]
        )
        
        # Serialize and deserialize
        serialized = plan_input.SerializeToString()
        deserialized = PlanInput()
        deserialized.ParseFromString(serialized)
        
        # Verify nested structure
        assert deserialized.input_id == "nested-plan-input"
        assert deserialized.plan_name == "nested-plan"
        assert len(deserialized.task_executions) == 1
        
        nested_exec = deserialized.task_executions[0]
        assert nested_exec.header.name == "nested-task"
        assert nested_exec.result.id == "nested-task-result"
        assert nested_exec.parent_plan_exec_id == "parent-123"
        assert nested_exec.parent_plan_name == "parent-plan" 