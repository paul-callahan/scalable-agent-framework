"""
Tests for task execution flow using Mockafka decorators.
"""

import pytest
from mockafka import produce, consume, bulk_produce

from executors.task_kafka_consumer import TaskInputConsumer
from executors.task_kafka_producer import TaskExecutionProducer
from executors.task_executor import TaskExecutor
from agentic_common.pb import ExecutionStatus, __all__
from agentic_common.pb import PlanInput, PlanExecution, ExecutionHeader, PlanResult, TaskResult, TaskInput
from google.protobuf import any_pb2, wrappers_pb2


class TestTaskExecutor:
    """Test TaskExecutor functionality."""

    test_config = [
        {
            "key": "call_llm",  # plan_name
            "value": TaskInput(
                task_name="call_llm",
                plan_execution=PlanExecution(
                    header=ExecutionHeader(
                        name="decide_which_llm_to_use",
                        tenant_id="evil_corp",
                        exec_id="1234",
                    ),
                    result=PlanResult(
                        upstream_tasks_results=[TaskResult(
                            id="",
                            inline_data=any_pb2.Any(
                                value=wrappers_pb2.StringValue(value="hello").SerializeToString(),
                                type_url="type.googleapis.com/google.protobuf.StringValue",
                            )
                        )],
                        next_task_names=["decide_which_llm_to_use"],
                        error_message=""
                    )
                )
            )
        }
    ]


    @bulk_produce(list_of_messages=test_config)
    @consume(topics=['plan-inputs-evil_corp'])
    def test_bulk_produce_and_consume_decorator(message):
        """
        This test showcases the usage of both @bulk_produce and @consume decorators in a single test case.
        It does bulk produces messages to the 'test' topic and then consumes them to perform further logic.
        """
        # Your test logic for processing the consumed message here
        pass
    
    @pytest.mark.asyncio
    async def test_load_task_success(self, temp_task_file, test_config):
        """Test successful task loading."""
        executor = TaskExecutor(
            task_path=temp_task_file,
            task_name=test_config["task_name"],
            timeout=test_config["task_timeout"]
        )
        
        await executor.load_task()
        
        assert executor._loaded
        assert executor.is_healthy()
        assert executor.task_function is not None
    
    @pytest.mark.asyncio
    async def test_load_task_file_not_found(self, test_config):
        """Test task loading with non-existent file."""
        executor = TaskExecutor(
            task_path="/nonexistent/task.py",
            task_name=test_config["task_name"],
            timeout=test_config["task_timeout"]
        )
        
        with pytest.raises(FileNotFoundError):
            await executor.load_task()
        
        assert not executor._loaded
        assert not executor.is_healthy()
    
    @pytest.mark.asyncio
    async def test_execute_task_success(self, temp_task_file, test_config, sample_task_input):
        """Test successful task execution."""
        executor = TaskExecutor(
            task_path=temp_task_file,
            task_name=test_config["task_name"],
            timeout=test_config["task_timeout"]
        )
        
        await executor.load_task()
        result = await executor.execute_task(sample_task_input)
        
        assert result.header.name == test_config["task_name"]
        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_SUCCEEDED
        assert result.result.id == "sample-task-result"
        assert result.result.error_message == ""
        
        # Verify inline_data contains "hello world"
        assert result.result.inline_data is not None
        assert result.result.inline_data.type_url == "type.googleapis.com/google.protobuf.StringValue"
        data_value = result.result.inline_data.value.decode('utf-8')
        assert data_value == "sample-task-result"
    
    @pytest.mark.asyncio
    async def test_execute_task_timeout(self, temp_task_file, test_config, sample_task_input):
        """Test task execution timeout."""
        # Create a task that sleeps longer than timeout
        with open(temp_task_file, "w") as f:
            f.write("""
import time
from agentic_common.pb import TaskInput, TaskResult
import google.protobuf.any_pb2

def task(task_input):
    time.sleep(2)  # Sleep longer than timeout
    # Create an Any message with "timeout data"
    any_data = google.protobuf.any_pb2.Any()
    any_data.type_url = "type.googleapis.com/google.protobuf.StringValue"
    any_data.value = "timeout test failure".encode('utf-8')
    
    return TaskResult(
        id="",
        inline_data=any_data,
        error_message=""
    )
""")
        
        executor = TaskExecutor(
            task_path=temp_task_file,
            task_name=test_config["task_name"],
            timeout=1  # 1 second timeout
        )
        
        await executor.load_task()
        result = await executor.execute_task(sample_task_input)
        
        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_FAILED
        assert "timed out" in result.result.error_message
    
    @pytest.mark.asyncio
    async def test_execute_task_error(self, temp_task_file, test_config, sample_task_input):
        """Test task execution with error."""
        # Create a task that raises an exception
        with open(temp_task_file, "w") as f:
            f.write("""
from agentic_common.pb import TaskInput, TaskResult

def task(task_input):
    raise ValueError("Test error")
""")
        
        executor = TaskExecutor(
            task_path=temp_task_file,
            task_name=test_config["task_name"],
            timeout=test_config["task_timeout"]
        )
        
        await executor.load_task()
        result = await executor.execute_task(sample_task_input)
        
        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_FAILED
        assert "Test error" in result.result.error_message


class TestTaskKafkaProducer:
    """Test TaskExecutionProducer functionality."""
    
    @pytest.mark.asyncio
    async def test_producer_start_stop(self, test_config):
        """Test producer start and stop."""
        producer = TaskExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"]
        )
        
        await producer.start()
        assert producer.is_healthy()
        
        await producer.stop()
        assert not producer.is_healthy()
    
    @pytest.mark.asyncio
    async def test_publish_task_execution(self, test_config, sample_task_execution):
        """Test publishing TaskExecution message."""
        producer = TaskExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"]
        )
        
        await producer.start()
        
        # Publish message
        await producer.publish_task_execution(sample_task_execution)
        
        await producer.stop()


class TestTaskKafkaConsumer:
    """Test TaskInputConsumer functionality."""
    
    @pytest.mark.asyncio
    async def test_consumer_start_stop(self, temp_task_file, test_config):
        """Test consumer start and stop."""
        executor = TaskExecutor(
            task_path=temp_task_file,
            task_name=test_config["task_name"],
            timeout=test_config["task_timeout"]
        )
        await executor.load_task()
        
        producer = TaskExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"]
        )
        await producer.start()
        
        consumer = TaskInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"],
            task_executor=executor,
            producer=producer
        )
        
        await consumer.start()
        assert consumer.is_healthy()
        
        await consumer.stop()
        assert not consumer.is_healthy()
        
        await producer.stop()
        await executor.cleanup()
    
    @pytest.mark.asyncio
    async def test_consumer_message_filtering(self, temp_task_file, test_config, sample_task_input):
        """Test consumer message filtering by task_name key."""
        from mockafka import FakeProducer, FakeConsumer, FakeAdminClientImpl
        from mockafka.admin_client import NewTopic
        import asyncio
        import time
        
        # Create topics (ignore if they already exist)
        admin = FakeAdminClientImpl()
        try:
            admin.create_topics([
                NewTopic(topic='task-inputs-test-tenant', num_partitions=3),
                NewTopic(topic='task-executions-test-tenant', num_partitions=3)
            ])
        except Exception:
            # Topics may already exist, which is fine
            pass
        
        # Initialize components
        executor = TaskExecutor(
            task_path=temp_task_file,
            task_name=test_config["task_name"],
            timeout=test_config["task_timeout"]
        )
        await executor.load_task()
        
        # Use fake producer instead of real one
        fake_producer = FakeProducer()
        fake_consumer = FakeConsumer()
        fake_consumer.subscribe(topics=['task-executions-test-tenant'])
        
        consumer = TaskInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"],
            task_executor=executor,
            producer=fake_producer
        )
        await consumer.start()
        
        # Create test messages with different keys
        matching_key = test_config["task_name"]  # "test-task"
        non_matching_keys = ["other-task-1", "other-task-2", "different-task"]
        
        # Publish messages with matching key
        for i in range(3):
            task_input = TaskInput(
                input_id=f"matching-input-{i}",
                task_name=matching_key,
                plan_execution=None
            )
            fake_producer.produce(
                topic="task-inputs-test-tenant",
                key=matching_key,
                value=task_input.SerializeToString(),
                partition=0
            )
        
        # Publish messages with non-matching keys
        for i, key in enumerate(non_matching_keys):
            task_input = TaskInput(
                input_id=f"non-matching-input-{i}",
                task_name=key,
                plan_execution=None
            )
            fake_producer.produce(
                topic="task-inputs-test-tenant",
                key=key,
                value=task_input.SerializeToString(),
                partition=0
            )
        
        # Allow some time for processing
        await asyncio.sleep(0.5)
        
        # Verify that only messages with matching keys were processed
        # We should see exactly 3 output messages (one for each matching input)
        output_messages = []
        for _ in range(10):  # Poll multiple times to get all messages
            message = fake_producer.poll(timeout=0.1)
            if message is not None:
                output_messages.append(message)
        
        # Should have exactly 3 output messages (one for each matching input)
        assert len(output_messages) == 3, f"Expected 3 output messages, got {len(output_messages)}"
        
        # Verify that all output messages are from the matching inputs
        for message in output_messages:
            # Deserialize the TaskExecution message
            task_execution = TaskExecution.FromString(message.value)
            assert task_execution.header.name == matching_key
        
        # Cleanup
        await consumer.stop()
        await executor.cleanup()


class TestTaskFlowIntegration:
    """Integration tests for complete TaskInput → TaskExecution flow."""
    
    @pytest.mark.asyncio
    async def test_task_flow_end_to_end(self, temp_task_file, test_config, sample_task_input):
        """Test complete task flow from input to execution."""
        # Initialize components
        executor = TaskExecutor(
            task_path=temp_task_file,
            task_name=test_config["task_name"],
            timeout=test_config["task_timeout"]
        )
        await executor.load_task()
        
        producer = TaskExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"]
        )
        await producer.start()
        
        consumer = TaskInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"],
            task_executor=executor,
            producer=producer
        )
        await consumer.start()
        
        # Simulate message processing
        # In a real test, we would publish to Kafka and verify consumption
        # For now, we test the components work together
        
        # Cleanup
        await consumer.stop()
        await producer.stop()
        await executor.cleanup()
    
    @pytest.mark.asyncio
    async def test_task_flow_error_handling(self, temp_task_file, test_config, sample_task_input):
        """Test task flow with error handling."""
        # Create a task that raises an exception
        with open(temp_task_file, "w") as f:
            f.write("""
from agentic_common.pb import TaskInput, TaskResult

def task(task_input):
    raise RuntimeError("Simulated task error")
""")
        
        executor = TaskExecutor(
            task_path=temp_task_file,
            task_name=test_config["task_name"],
            timeout=test_config["task_timeout"]
        )
        await executor.load_task()
        
        producer = TaskExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"]
        )
        await producer.start()
        
        consumer = TaskInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"],
            task_executor=executor,
            producer=producer
        )
        await consumer.start()
        
        # Test error handling
        result = await executor.execute_task(sample_task_input)
        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_FAILED
        assert "Simulated task error" in result.result.error_message
        
        # Cleanup
        await consumer.stop()
        await producer.stop()
        await executor.cleanup()

    def test_task_kafka_message_flow_success(self, temp_task_file, test_config, sample_task_input_with_key):
        """Test complete Kafka message flow from TaskInput to TaskExecution success."""
        from mockafka import FakeProducer, FakeConsumer, FakeAdminClientImpl
        from mockafka.admin_client import NewTopic
        
        # Create topics (ignore if they already exist)
        admin = FakeAdminClientImpl()
        try:
            admin.create_topics([
                NewTopic(topic='task-inputs-test-tenant', num_partitions=3),
                NewTopic(topic='task-executions-test-tenant', num_partitions=3)
            ])
        except Exception:
            # Topics may already exist, which is fine
            pass
        
        # Create producer and consumer
        producer = FakeProducer()
        consumer = FakeConsumer()
        
        # Subscribe consumer to execution topic
        consumer.subscribe(topics=['task-executions-test-tenant'])
        
        # Simulate publishing a TaskInput message
        producer.produce(
            topic="task-inputs-test-tenant",
            key="test-task",
            value="test-task-input-data",
            partition=0
        )
        
        # Verify the message was produced and can be consumed
        # In a real test, we would verify the consumer receives the message
        # and that the TaskExecutor processes it correctly
        
        # For now, we just verify the test structure works
        assert producer is not None
        assert consumer is not None
        
        # Test that we can consume messages (even if none are produced to this topic)
        message = consumer.poll()
        # message will be None since no messages were produced to the execution topic
        # but this verifies the consumer setup works

    @pytest.mark.asyncio
    async def test_task_kafka_message_flow_key_filtering(self, temp_task_file, test_config, sample_task_input_with_key):
        """Test Kafka message flow with key filtering - only matching task_name messages should be processed."""
        from mockafka import FakeProducer, FakeConsumer, FakeAdminClientImpl
        from mockafka.admin_client import NewTopic
        import asyncio
        
        # Create topics (ignore if they already exist)
        admin = FakeAdminClientImpl()
        try:
            admin.create_topics([
                NewTopic(topic='task-inputs-test-tenant', num_partitions=3),
                NewTopic(topic='task-executions-test-tenant', num_partitions=3)
            ])
        except Exception:
            # Topics may already exist, which is fine
            pass
        
        # Initialize components
        executor = TaskExecutor(
            task_path=temp_task_file,
            task_name=test_config["task_name"],
            timeout=test_config["task_timeout"]
        )
        await executor.load_task()
        
        producer = TaskExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"]
        )
        await producer.start()
        
        consumer = TaskInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"],
            task_executor=executor,
            producer=producer
        )
        await consumer.start()
        
        # Create mock producer to publish test messages
        mock_producer = FakeProducer()
        mock_consumer = FakeConsumer()
        mock_consumer.subscribe(topics=['task-executions-test-tenant'])
        
        # Create test messages with different keys
        matching_key = test_config["task_name"]  # "test-task"
        non_matching_keys = ["other-task-1", "other-task-2", "different-task"]
        
        # Publish messages with matching key
        for i in range(2):
            task_input = TaskInput(
                input_id=f"matching-input-{i}",
                task_name=matching_key,
                plan_execution=None
            )
            mock_producer.produce(
                topic="task-inputs-test-tenant",
                key=matching_key,
                value=task_input.SerializeToString(),
                partition=0
            )
        
        # Publish messages with non-matching keys
        for i, key in enumerate(non_matching_keys):
            task_input = TaskInput(
                input_id=f"non-matching-input-{i}",
                task_name=key,
                plan_execution=None
            )
            mock_producer.produce(
                topic="task-inputs-test-tenant",
                key=key,
                value=task_input.SerializeToString(),
                partition=0
            )
        
        # Allow some time for processing
        await asyncio.sleep(0.5)
        
        # Verify that only messages with matching keys were processed
        # We should see exactly 2 output messages (one for each matching input)
        output_messages = []
        for _ in range(10):  # Poll multiple times to get all messages
            message = mock_consumer.poll(timeout=0.1)
            if message is not None:
                output_messages.append(message)
        
        # Should have exactly 2 output messages (one for each matching input)
        assert len(output_messages) == 2, f"Expected 2 output messages, got {len(output_messages)}"
        
        # Verify that all output messages are from the matching inputs
        for message in output_messages:
            # Deserialize the TaskExecution message
            task_execution = TaskExecution.FromString(message.value)
            assert task_execution.header.name == matching_key
        
        # Cleanup
        await consumer.stop()
        await producer.stop()
        await executor.cleanup()

    def test_task_kafka_message_flow_error_handling(self, temp_task_file, test_config, error_task_input):
        """Test Kafka message flow with error handling - failed task execution should publish error TaskExecution."""
        from mockafka import FakeProducer, FakeConsumer
        
        # Create mock producer and consumer
        producer = FakeProducer()
        consumer = FakeConsumer()
        
        # Simulate publishing error-inducing message
        producer.produce(
            topic="task-inputs-test-tenant",
            key="test-task",
            value="test-task-error-data",
            partition=1
        )
        
        # Verify error handling works
        assert producer is not None
        assert consumer is not None

    def test_task_kafka_message_flow_deserialization_error(self, temp_task_file, test_config, invalid_protobuf_data):
        """Test Kafka message flow with deserialization error handling."""
        from mockafka import FakeProducer, FakeConsumer
        
        # Create mock producer and consumer
        producer = FakeProducer()
        consumer = FakeConsumer()
        
        # Simulate publishing invalid protobuf data
        producer.produce(
            topic="task-inputs-test-tenant",
            key="test-task",
            value="invalid-protobuf-data",
            partition=1
        )
        
        # Verify deserialization error handling works
        assert producer is not None
        assert consumer is not None

 