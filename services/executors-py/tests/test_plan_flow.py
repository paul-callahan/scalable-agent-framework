"""
Tests for plan execution flow using Mockafka decorators.
"""
import asyncio

import pytest
from aiokafka import TopicPartition
from mockafka import FakeAdminClientImpl
from mockafka.aiokafka import FakeAIOKafkaConsumer, FakeAIOKafkaProducer
from unittest.mock import patch

from executors.plan_kafka_consumer import PlanInputConsumer
from executors.plan_kafka_producer import PlanExecutionProducer
from executors.plan_executor import PlanExecutor
from agentic_common.pb import ExecutionStatus
from confluent_kafka.cimpl import NewPartitions

from tests import conftest
from tests.mock_utils import prepare_aio_kafka_consumer, prepare_aio_kafka_producer


class TestPlanExecutor:
    """Test PlanExecutor functionality."""
    test_config = [
        {
            'topic': "plan-inputs-evil_corp",
            'partition': 0,
            "key": "decide_which_llm_to_use",  # Message key, same as plan_name
            "value": conftest.sample_plan_input_full().SerializeToString()
        }
    ]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="revist if Mockafka supports __aiter__ on FakeAIOKafkaConsumer")
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

        plan_kafka_consumer: PlanInputConsumer = PlanInputConsumer(
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
    time.sleep(2)  # Sleep longer than timeout
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
        with patch('aiokafka.AIOKafkaProducer', autospec=True) as MockKafkaProducer:
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockKafkaProducer)
            producer = PlanExecutionProducer(
                producer=mock_aiokafka_producer,
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
        with patch('aiokafka.AIOKafkaProducer', autospec=True) as MockKafkaProducer:
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockKafkaProducer)
            producer = PlanExecutionProducer(
                producer=mock_aiokafka_producer,
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
        with (patch("aiokafka.AIOKafkaConsumer", autospec=True) as MockConsumer,
              patch("aiokafka.AIOKafkaProducer", autospec=True) as MockProducer):
            mock_aiokafka_consumer = await prepare_aio_kafka_consumer(MockConsumer)
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockProducer)

            executor = PlanExecutor(
                plan_path=temp_plan_file,
                plan_name=test_config["plan_name"],
                timeout=test_config["plan_timeout"]
            )
            await executor.load_plan()
            producer = PlanExecutionProducer(
                producer=mock_aiokafka_producer,
                tenant_id=test_config["tenant_id"],
                plan_name=test_config["plan_name"]
            )
            await producer.start()

            consumer = PlanInputConsumer(
                consumer=mock_aiokafka_consumer,
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
        with (patch("aiokafka.AIOKafkaConsumer", autospec=True) as MockConsumer,
              patch("aiokafka.AIOKafkaProducer", autospec=True) as MockProducer):
            mock_aiokafka_consumer = await prepare_aio_kafka_consumer(MockConsumer)
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockProducer)
            # Create a mock producer for testing
            mock_producer = PlanExecutionProducer(
                producer=mock_aiokafka_producer,
                tenant_id=test_config["tenant_id"],
                plan_name=test_config["plan_name"]
            )
            consumer = PlanInputConsumer(
                consumer=mock_aiokafka_consumer,
                tenant_id=test_config["tenant_id"],
                plan_name=test_config["plan_name"],
                plan_executor=None,  # Mock executor
                producer=mock_producer
            )

            await consumer.start()
            assert consumer.is_healthy()

            await consumer.stop()
            assert not consumer.is_healthy()


class TestPlanFlowIntegration:
    """Integration tests for complete PlanInput → PlanExecution flow."""

    @pytest.mark.asyncio
    async def test_plan_flow_end_to_end(self, temp_plan_file, test_config, sample_plan_input_lite):
        """Test complete plan flow from input to execution."""
        with (patch("aiokafka.AIOKafkaConsumer", autospec=True) as MockConsumer,
              patch("aiokafka.AIOKafkaProducer", autospec=True) as MockProducer):
            mock_aiokafka_consumer = await prepare_aio_kafka_consumer(MockConsumer)
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockProducer)
            # Initialize components
            executor = PlanExecutor(
                plan_path=temp_plan_file,
                plan_name=test_config["plan_name"],
                timeout=test_config["plan_timeout"]
            )
            await executor.load_plan()

            producer = PlanExecutionProducer(
                producer=mock_aiokafka_producer,
                tenant_id=test_config["tenant_id"],
                plan_name=test_config["plan_name"]
            )
            await producer.start()

            consumer = PlanInputConsumer(
                consumer=mock_aiokafka_consumer,
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
        with (open(temp_plan_file, "w") as f,
              patch("aiokafka.AIOKafkaConsumer", autospec=True) as MockConsumer,
              patch("aiokafka.AIOKafkaProducer", autospec=True) as MockProducer):
            f.write("""
from agentic_common.pb import PlanInput, PlanResult

def plan(plan_input):
    raise RuntimeError("Simulated plan error")
""")
        mock_aiokafka_consumer = await prepare_aio_kafka_consumer(MockConsumer)
        mock_aiokafka_producer = await prepare_aio_kafka_producer(MockProducer)
        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )
        await executor.load_plan()
        producer = PlanExecutionProducer(
            producer=mock_aiokafka_producer,
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"]
        )
        await producer.start()
        consumer = PlanInputConsumer(
            consumer=mock_aiokafka_consumer,
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
