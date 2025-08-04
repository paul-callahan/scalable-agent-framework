#!/usr/bin/env python3
"""
Test script to verify consistent protobuf serialization across all Python services.

This script tests that all services can properly serialize and deserialize
protobuf messages using the new ProtobufUtils.
"""

import sys
import os
import uuid
from datetime import datetime

# Add the common-py directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agentic_common import ProtobufUtils
from agentic_common.pb import TaskExecution, PlanExecution, TaskResult, PlanResult, ExecutionHeader


def test_task_execution_serialization():
    """Test TaskExecution serialization and deserialization."""
    print("Testing TaskExecution serialization...")
    
    # Create a test TaskExecution
    execution_id = str(uuid.uuid4())
    tenant_id = "test-tenant"
    
    # Create execution header
    header = ProtobufUtils.create_execution_header(
        execution_id=execution_id,
        tenant_id=tenant_id,
        status=3,  # SUCCEEDED
        graph_id="test-graph",
        lifetime_id="test-lifetime"
    )
    
    # Create task result
    task_result = ProtobufUtils.create_task_result(
        mime_type="application/json",
        size_bytes=1024,
        inline_data={"test": "data", "number": 42}
    )
    
    # Create TaskExecution
    task_execution = TaskExecution()
    task_execution.header.CopyFrom(header)
    task_execution.task_type = "test_task"
    task_execution.result.CopyFrom(task_result)
    
    # Test serialization
    try:
        serialized = ProtobufUtils.serialize_task_execution(task_execution)
        print(f"✓ TaskExecution serialized successfully ({len(serialized)} bytes)")
    except Exception as e:
        print(f"✗ TaskExecution serialization failed: {e}")
        return False
    
    # Test deserialization
    try:
        deserialized = ProtobufUtils.deserialize_task_execution(serialized)
        print(f"✓ TaskExecution deserialized successfully")
        
        # Verify fields
        assert deserialized.header.id == execution_id
        assert deserialized.header.tenant_id == tenant_id
        assert deserialized.task_type == "test_task"
        assert deserialized.result.mime_type == "application/json"
        print(f"✓ TaskExecution field validation passed")
        
    except Exception as e:
        print(f"✗ TaskExecution deserialization failed: {e}")
        return False
    
    return True


def test_plan_execution_serialization():
    """Test PlanExecution serialization and deserialization."""
    print("\nTesting PlanExecution serialization...")
    
    # Create a test PlanExecution
    execution_id = str(uuid.uuid4())
    tenant_id = "test-tenant"
    
    # Create execution header
    header = ProtobufUtils.create_execution_header(
        execution_id=execution_id,
        tenant_id=tenant_id,
        status=3,  # SUCCEEDED
        graph_id="test-graph",
        lifetime_id="test-lifetime"
    )
    
    # Create plan result
    plan_result = ProtobufUtils.create_plan_result(
        next_task_ids=["task1", "task2", "task3"],
        metadata={"confidence": "high", "reasoning": "test"},
        confidence=0.85
    )
    
    # Create PlanExecution
    plan_execution = PlanExecution()
    plan_execution.header.CopyFrom(header)
    plan_execution.plan_type = "test_plan"
    plan_execution.input_task_id = "input_task_123"
    plan_execution.result.CopyFrom(plan_result)
    
    # Test serialization
    try:
        serialized = ProtobufUtils.serialize_plan_execution(plan_execution)
        print(f"✓ PlanExecution serialized successfully ({len(serialized)} bytes)")
    except Exception as e:
        print(f"✗ PlanExecution serialization failed: {e}")
        return False
    
    # Test deserialization
    try:
        deserialized = ProtobufUtils.deserialize_plan_execution(serialized)
        print(f"✓ PlanExecution deserialized successfully")
        
        # Verify fields
        assert deserialized.header.id == execution_id
        assert deserialized.header.tenant_id == tenant_id
        assert deserialized.plan_type == "test_plan"
        assert deserialized.input_task_id == "input_task_123"
        assert len(deserialized.result.next_task_ids) == 3
        assert abs(deserialized.result.confidence - 0.85) < 0.0001
        print(f"✓ PlanExecution field validation passed")
        
    except Exception as e:
        print(f"✗ PlanExecution deserialization failed: {e}")
        return False
    
    return True


def test_protobuf_utils_validation():
    """Test protobuf validation utilities."""
    print("\nTesting protobuf validation...")
    
    # Test valid TaskExecution
    execution_id = str(uuid.uuid4())
    header = ProtobufUtils.create_execution_header(
        execution_id=execution_id,
        tenant_id="test-tenant",
        status=3
    )
    
    task_execution = TaskExecution()
    task_execution.header.CopyFrom(header)
    task_execution.task_type = "test_task"
    
    assert ProtobufUtils.validate_task_execution(task_execution)
    print("✓ Valid TaskExecution validation passed")
    
    # Test invalid TaskExecution (missing required fields)
    invalid_task = TaskExecution()
    assert not ProtobufUtils.validate_task_execution(invalid_task)
    print("✓ Invalid TaskExecution validation passed")
    
    # Test valid PlanExecution
    plan_execution = PlanExecution()
    plan_execution.header.CopyFrom(header)
    plan_execution.plan_type = "test_plan"
    
    assert ProtobufUtils.validate_plan_execution(plan_execution)
    print("✓ Valid PlanExecution validation passed")
    
    # Test invalid PlanExecution (missing required fields)
    invalid_plan = PlanExecution()
    assert not ProtobufUtils.validate_plan_execution(invalid_plan)
    print("✓ Invalid PlanExecution validation passed")
    
    return True


def test_data_extraction():
    """Test data extraction utilities."""
    print("\nTesting data extraction...")
    
    # Test task result data extraction
    task_result = ProtobufUtils.create_task_result(
        mime_type="application/json",
        inline_data={"test": "data"}
    )
    
    extracted_data = ProtobufUtils.extract_task_result_data(task_result)
    assert extracted_data is not None
    assert extracted_data["type"] == "inline"
    print("✓ TaskResult data extraction passed")
    
    # Test plan result data extraction
    plan_result = ProtobufUtils.create_plan_result(
        next_task_ids=["task1", "task2"],
        metadata={"key": "value"},
        confidence=0.75
    )
    
    extracted_plan_data = ProtobufUtils.extract_plan_result_data(plan_result)
    assert len(extracted_plan_data["next_task_ids"]) == 2
    assert extracted_plan_data["confidence"] == 0.75
    assert extracted_plan_data["metadata"]["key"] == "value"
    print("✓ PlanResult data extraction passed")
    
    return True


def test_json_conversion():
    """Test JSON conversion utilities."""
    print("\nTesting JSON conversion...")
    
    # Create a test TaskExecution
    execution_id = str(uuid.uuid4())
    header = ProtobufUtils.create_execution_header(
        execution_id=execution_id,
        tenant_id="test-tenant",
        status=3
    )
    
    task_execution = TaskExecution()
    task_execution.header.CopyFrom(header)
    task_execution.task_type = "test_task"
    
    # Test protobuf to JSON-safe dict
    try:
        json_dict = ProtobufUtils.to_json_safe_dict(task_execution)
        assert "header" in json_dict
        assert "taskType" in json_dict
        print("✓ Protobuf to JSON-safe dict conversion passed")
    except Exception as e:
        print(f"✗ Protobuf to JSON-safe dict conversion failed: {e}")
        return False
    
    # Test JSON-safe dict to protobuf
    try:
        reconstructed = ProtobufUtils.from_json_safe_dict(json_dict, TaskExecution)
        assert reconstructed.header.id == execution_id
        assert reconstructed.task_type == "test_task"
        print("✓ JSON-safe dict to protobuf conversion passed")
    except Exception as e:
        print(f"✗ JSON-safe dict to protobuf conversion failed: {e}")
        return False
    
    return True


def main():
    """Run all protobuf consistency tests."""
    print("=" * 60)
    print("Testing Protobuf Serialization Consistency")
    print("=" * 60)
    
    tests = [
        test_task_execution_serialization,
        test_plan_execution_serialization,
        test_protobuf_utils_validation,
        test_data_extraction,
        test_json_conversion
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"✗ Test {test.__name__} failed")
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✓ All protobuf consistency tests passed!")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 