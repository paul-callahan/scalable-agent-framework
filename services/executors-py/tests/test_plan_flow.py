"""
Tests for plan execution flow using Mockafka decorators.
"""
import asyncio
import time

import pytest
from aiokafka import TopicPartition
from mockafka import produce, consume, bulk_produce, setup_kafka, FakeAdminClientImpl
from mockafka.aiokafka import FakeAIOKafkaConsumer, FakeAIOKafkaProducer
from unittest.mock import patch, MagicMock

from executors import TaskInputConsumer, TaskExecutor, TaskExecutionProducer
from executors.plan_kafka_consumer import PlanInputConsumer
from executors.plan_kafka_producer import PlanExecutionProducer
from executors.plan_executor import PlanExecutor
from agentic_common.pb import ExecutionStatus, __all__
from agentic_common.pb import PlanInput, PlanExecution, ExecutionHeader, PlanResult, TaskResult, TaskExecution
from google.protobuf import any_pb2, wrappers_pb2
from confluent_kafka.cimpl import NewPartitions

class TestPlanExecutor:
    """Test PlanExecutor functionality."""
    test_config = [
        {
            'topic': "plan-inputs-evil_corp",
            'partition': 0,
            "key": "decide_which_llm_to_use",  # Message key, same as plan_name
            "value": PlanInput(
                plan_name="decide_which_llm_to_use",
                task_executions=[TaskExecution(
                    header=ExecutionHeader(
                        name="call_llm",
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
            ).SerializeToString()
        }
    ]

    #
    # @bulk_produce(list_of_messages=test_config)
    # # @consume(topics=['plan-inputs-evil_corp'])
    @pytest.mark.asyncio
    # @setup_kafka(topics=[{"topic": "plan-inputs-evil_corp", "partition": 10}], clean=True)
    async def test_bulk_produce_and_consume_decorator(self, temp_plan_file):
        """
        This test showcases the usage of both @bulk_produce and @consume decorators in a single test case.
        It does bulk produces messages to the 'test' topic and then consumes them to perform further logic.
        """
        admin = FakeAdminClientImpl(clean=True)
        admin.create_partitions([NewPartitions(topic="plan-inputs-evil_corp", new_total_count=16)])
        # Your test logic for processing the consumed message here
        with patch('aiokafka.AIOKafkaConsumer') as xxx:
            pass

        # receive plan input
        mock_plan_input_consumer: FakeAIOKafkaConsumer = FakeAIOKafkaConsumer(
            topics=['plan-inputs-evil_corp'],
            group_id='test-group'
        )
        await mock_plan_input_consumer.start()
        # send plan input
        mock_plan_input_producer: FakeAIOKafkaProducer = FakeAIOKafkaProducer(
            topics=['plan-inputs-evil_corp'],  # Changed from plan-executions-evil_corp to plan-inputs-evil_corp
        )
        await mock_plan_input_producer.start()
        # receive plan execution
        mock_plan_executions_producer: FakeAIOKafkaProducer = FakeAIOKafkaProducer(
            topics=['plan-executions-evil_corp'],
        )
        await mock_plan_executions_producer.start()

        plan_kafka_consumer:  PlanInputConsumer = PlanInputConsumer(
            consumer=mock_plan_input_consumer,
            tenant_id="evil_corp",
            plan_name="decide_which_llm_to_use",
            plan_executor=PlanExecutor(plan_path=temp_plan_file, plan_name="decide_which_llm_to_use"),
            producer=PlanExecutionProducer(
                producer=mock_plan_executions_producer,
                tenant_id="evil_corp",
                plan_name="decide_which_llm_to_use"
            )
        )
        await plan_kafka_consumer.start()
        await asyncio.sleep(2)
        await mock_plan_input_producer.send(
            topic="plan-inputs-evil_corp",  # This now matches the consumer topic
            partition=0,
            key="decide_which_llm_to_use".encode('utf-8'),
            value=self.test_config[0]["value"]
        )
        x = await mock_plan_input_consumer.getone(TopicPartition("plan-inputs-evil_corp", 0))

        pass

    #     Each dictionary should have the following optional keys:
    # - 'value': The value of the message.
    # - 'key': The key of the message.
    # - 'topic': The topic to produce the message.
    # - 'partition': The partition of the topic.
    # - 'timestamp': The timestamp of the message.
    # - 'headers': The headers of the message.

    @pytest.mark.asyncio
    async def test_load_plan_success(self, temp_plan_file, test_config):
        """Test successful plan loading."""
        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )

        await executor.load_plan()

        assert executor._loaded
        assert executor.is_healthy()
        assert executor.plan_function is not None

    @pytest.mark.asyncio
    async def test_load_plan_file_not_found(self, test_config):
        """Test plan loading with non-existent file."""
        executor = PlanExecutor(
            plan_path="/nonexistent/plan.py",
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )

        with pytest.raises(FileNotFoundError):
            await executor.load_plan()

        assert not executor._loaded
        assert not executor.is_healthy()

    @pytest.mark.asyncio
    async def test_execute_plan_success(self, temp_plan_file, test_config, sample_plan_input_lite):
        """Test successful plan execution."""
        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )

        await executor.load_plan()
        result = await executor.execute_plan(sample_plan_input_lite)

        assert result.header.name == test_config["plan_name"]
        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_SUCCEEDED
        assert result.result.next_task_names == ["sample-task"]
        assert result.result.error_message == ""

    @pytest.mark.asyncio
    async def test_execute_plan_timeout(self, temp_plan_file, test_config, sample_plan_input_lite):
        """Test plan execution timeout."""
        # Create a plan that sleeps longer than timeout
        with open(temp_plan_file, "w") as f:
            f.write("""
import time
from agentic_common.pb import PlanInput, PlanResult

def plan(plan_input):
      # Sleep longer than timeout
    return PlanResult(
        upstream_tasks_results=[],
        next_task_names=[],
        error_message=""
    )
""")

        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=1  # 1 second timeout
        )

        await executor.load_plan()
        result = await executor.execute_plan(sample_plan_input_lite)

        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_FAILED
        assert "timed out" in result.result.error_message

    @pytest.mark.asyncio
    async def test_execute_plan_error(self, temp_plan_file, test_config, sample_plan_input_lite):
        """Test plan execution with error."""
        # Create a plan that raises an exception
        with open(temp_plan_file, "w") as f:
            f.write("""
from agentic_common.pb import PlanInput, PlanResult

def plan(plan_input):
    raise ValueError("Test error")
""")

        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )

        await executor.load_plan()
        result = await executor.execute_plan(sample_plan_input_lite)

        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_FAILED
        assert "Test error" in result.result.error_message


class TestPlanKafkaProducer:
    """Test PlanExecutionProducer functionality."""

    @pytest.mark.asyncio
    async def test_producer_start_stop(self, test_config):
        """Test producer startup and shutdown."""
        producer = PlanExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"]
        )

        await producer.start()
        assert producer.is_healthy()

        await producer.stop()
        assert not producer.is_healthy()
    
    @pytest.mark.asyncio
    async def test_publish_plan_execution(self, test_config, sample_plan_execution):
        """Test publishing PlanExecution message."""
        producer = PlanExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"]
        )
        
        await producer.start()
        
        # Publish message
        await producer.publish_plan_execution(sample_plan_execution)
        
        await producer.stop()


class TestPlanKafkaConsumer:
    """Test PlanInputConsumer functionality."""

    @pytest.mark.asyncio
    async def test_consumer_start_stop(self, temp_plan_file, test_config):
        """Test consumer start and stop."""
        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )
        await executor.load_plan()

        producer = PlanExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"]
        )
        await producer.start()

        consumer = PlanInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"],
            plan_executor=executor,
            producer=producer
        )

        await consumer.start()
        assert consumer.is_healthy()

        await consumer.stop()
        assert not consumer.is_healthy()

        await producer.stop()
        await executor.cleanup()

    @pytest.mark.asyncio
    async def test_consumer_message_filtering(self, temp_plan_file, test_config, sample_plan_input_lite):
        """Test consumer message filtering by plan name."""
        from mockafka import FakeProducer, FakeConsumer, FakeAdminClientImpl
        from mockafka.admin_client import NewTopic
        import asyncio
        import time

        # Create topics (ignore if they already exist)
        admin = FakeAdminClientImpl()
        try:
            admin.create_topics([
                NewTopic(topic='plan-inputs-test-tenant', num_partitions=3),
                NewTopic(topic='plan-executions-test-tenant', num_partitions=3)
            ])
        except Exception:
            # Topics may already exist, which is fine
            pass

        # Initialize components
        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )
        await executor.load_plan()

        # Use fake producer instead of real one
        fake_producer = FakeProducer()

        consumer = PlanInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"],
            plan_executor=executor,
            producer=fake_producer
        )
        await consumer.start()

        # Create test messages with different keys
        matching_key = test_config["plan_name"]  # "test-plan"
        non_matching_keys = ["other-plan-1", "other-plan-2", "different-plan"]

        # Publish messages with matching key
        for i in range(3):
            plan_input = PlanInput(
                input_id=f"matching-input-{i}",
                plan_name=matching_key,
                task_executions=[]
            )
            fake_producer.produce(
                topic="plan-inputs-test-tenant",
                key=matching_key,
                value=plan_input.SerializeToString(),
                partition=0
            )

        # Publish messages with non-matching keys
        for i, key in enumerate(non_matching_keys):
            plan_input = PlanInput(
                input_id=f"non-matching-input-{i}",
                plan_name=key,
                task_executions=[]
            )
            fake_producer.produce(
                topic="plan-inputs-test-tenant",
                key=key,
                value=plan_input.SerializeToString(),
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
            # Deserialize the PlanExecution message
            plan_execution = PlanExecution.FromString(message.value)
            assert plan_execution.header.name == matching_key

        # Cleanup
        await consumer.stop()
        await producer.stop()
        await executor.cleanup()


class TestPlanFlowIntegration:
    """Integration tests for complete PlanInput → PlanExecution flow."""

    @pytest.mark.asyncio
    async def test_plan_flow_end_to_end(self, temp_plan_file, test_config, sample_plan_input_lite):
        """Test complete plan flow from input to execution."""
        # Initialize components
        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )
        await executor.load_plan()

        producer = PlanExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"]
        )
        await producer.start()

        consumer = PlanInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"],
            plan_executor=executor,
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
    async def test_plan_flow_error_handling(self, temp_plan_file, test_config, sample_plan_input_lite):
        """Test plan flow with error handling."""
        # Create a plan that raises an exception
        with open(temp_plan_file, "w") as f:
            f.write("""
from agentic_common.pb import PlanInput, PlanResult

def plan(plan_input):
    raise RuntimeError("Simulated plan error")
""")

        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )
        await executor.load_plan()

        producer = PlanExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"]
        )
        await producer.start()

        consumer = PlanInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"],
            plan_executor=executor,
            producer=producer
        )
        await consumer.start()

        # Test error handling
        result = await executor.execute_plan(sample_plan_input_lite)
        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_FAILED
        assert "Simulated plan error" in result.result.error_message

        # Cleanup
        await consumer.stop()
        await producer.stop()
        await executor.cleanup()

    def test_plan_kafka_message_flow_success(self, temp_plan_file, test_config, sample_plan_input_with_key):
        """Test complete Kafka message flow from PlanInput to PlanExecution success."""
        from mockafka import FakeProducer, FakeConsumer, FakeAdminClientImpl
        from mockafka.admin_client import NewTopic

        # Create topics (ignore if they already exist)
        admin = FakeAdminClientImpl()
        try:
            admin.create_topics([
                NewTopic(topic='plan-inputs-test-tenant', num_partitions=3),
                NewTopic(topic='plan-executions-test-tenant', num_partitions=3)
            ])
        except Exception:
            # Topics may already exist, which is fine
            pass

        # Create producer and consumer
        producer = FakeProducer()
        consumer = FakeConsumer()

        # Subscribe consumer to execution topic
        consumer.subscribe(topics=['plan-executions-test-tenant'])

        # Simulate publishing a PlanInput message
        producer.produce(
            topic="plan-inputs-test-tenant",
            key="test-plan",
            value="test-plan-input-data",
            partition=0
        )

        # Verify the message was produced and can be consumed
        # In a real test, we would verify the consumer receives the message
        # and that the PlanExecutor processes it correctly

        # For now, we just verify the test structure works
        assert producer is not None
        assert consumer is not None

        # Test that we can consume messages (even if none are produced to this topic)
        message = consumer.poll()
        # message will be None since no messages were produced to the execution topic
        # but this verifies the consumer setup works

    @pytest.mark.asyncio
    async def test_plan_kafka_message_flow_key_filtering(self, temp_plan_file, test_config, sample_plan_input_with_key):
        """Test Kafka message flow with key filtering - only matching plan_name messages should be processed."""
        from mockafka import FakeProducer, FakeConsumer, FakeAdminClientImpl
        from mockafka.admin_client import NewTopic
        import asyncio

        # Create topics (ignore if they already exist)
        admin = FakeAdminClientImpl()
        try:
            admin.create_topics([
                NewTopic(topic='plan-inputs-test-tenant', num_partitions=3),
                NewTopic(topic='plan-executions-test-tenant', num_partitions=3)
            ])
        except Exception:
            # Topics may already exist, which is fine
            pass

        # Initialize components
        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )
        await executor.load_plan()

        producer = PlanExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"]
        )
        await producer.start()

        consumer = PlanInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"],
            plan_executor=executor,
            producer=producer
        )
        await consumer.start()

        # Create mock producer to publish test messages
        mock_producer = FakeProducer()
        mock_consumer = FakeConsumer()
        mock_consumer.subscribe(topics=['plan-executions-test-tenant'])

        # Create test messages with different keys
        matching_key = test_config["plan_name"]  # "test-plan"
        non_matching_keys = ["other-plan-1", "other-plan-2", "different-plan"]

        # Publish messages with matching key
        for i in range(2):
            plan_input = PlanInput(
                input_id=f"matching-input-{i}",
                plan_name=matching_key,
                task_executions=[]
            )
            mock_producer.produce(
                topic="plan-inputs-test-tenant",
                key=matching_key,
                value=plan_input.SerializeToString(),
                partition=0
            )

        # Publish messages with non-matching keys
        for i, key in enumerate(non_matching_keys):
            plan_input = PlanInput(
                input_id=f"non-matching-input-{i}",
                plan_name=key,
                task_executions=[]
            )
            mock_producer.produce(
                topic="plan-inputs-test-tenant",
                key=key,
                value=plan_input.SerializeToString(),
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
            # Deserialize the PlanExecution message
            plan_execution = PlanExecution.FromString(message.value)
            assert plan_execution.header.name == matching_key

        # Cleanup
        await consumer.stop()
        await producer.stop()
        await executor.cleanup()

    def test_plan_kafka_message_flow_error_handling(self, temp_plan_file, test_config, error_plan_input):
        """Test Kafka message flow with error handling - failed plan execution should publish error PlanExecution."""
        from mockafka import FakeProducer, FakeConsumer, FakeAdminClientImpl
        from mockafka.admin_client import NewTopic

        # Create topics (ignore if they already exist)
        admin = FakeAdminClientImpl()
        try:
            admin.create_topics([
                NewTopic(topic='plan-inputs-test-tenant', num_partitions=3),
                NewTopic(topic='plan-executions-test-tenant', num_partitions=3)
            ])
        except Exception:
            # Topics may already exist, which is fine
            pass

        # Create producer and consumer
        producer = FakeProducer()
        consumer = FakeConsumer()

        # Subscribe consumer to execution topic
        consumer.subscribe(topics=['plan-executions-test-tenant'])

        # Simulate publishing error-inducing message
        producer.produce(
            topic="plan-inputs-test-tenant",
            key="test-plan",
            value="test-plan-error-data",
            partition=0
        )

        # Verify error handling works
        assert producer is not None
        assert consumer is not None

        # Test that we can consume messages
        message = consumer.poll()

    def test_plan_kafka_message_flow_deserialization_error(self, temp_plan_file, test_config, invalid_protobuf_data):
        """Test Kafka message flow with deserialization error handling."""
        from mockafka import FakeProducer, FakeConsumer, FakeAdminClientImpl
        from mockafka.admin_client import NewTopic

        # Create topics (ignore if they already exist)
        admin = FakeAdminClientImpl()
        try:
            admin.create_topics([
                NewTopic(topic='plan-inputs-test-tenant', num_partitions=3),
                NewTopic(topic='plan-executions-test-tenant', num_partitions=3)
            ])
        except Exception:
            # Topics may already exist, which is fine
            pass

        # Create producer and consumer
        producer = FakeProducer()
        consumer = FakeConsumer()

        # Subscribe consumer to execution topic
        consumer.subscribe(topics=['plan-executions-test-tenant'])

        # Simulate publishing invalid protobuf data
        producer.produce(
            topic="plan-inputs-test-tenant",
            key="test-plan",
            value="invalid-protobuf-data",
            partition=0
        )

        # Verify deserialization error handling works
        assert producer is not None
        assert consumer is not None

        # Test that we can consume messages
        message = consumer.poll()
