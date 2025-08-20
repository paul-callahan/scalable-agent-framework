"""
Tests for task execution flow using Mockafka decorators.
"""

import pytest
from mockafka import produce, consume, bulk_produce
from unittest.mock import patch

from executors.task_kafka_consumer import TaskInputConsumer
from executors.task_kafka_producer import TaskExecutionProducer
from executors.task_executor import TaskExecutor
from agentic_common.pb import ExecutionStatus, __all__
from agentic_common.pb import PlanInput, PlanExecution, ExecutionHeader, PlanResult, TaskResult, TaskInput
from google.protobuf import any_pb2, wrappers_pb2
from tests.mock_utils import prepare_aio_kafka_consumer, prepare_aio_kafka_producer


class TestTaskExecutor:
    """Test TaskExecutor functionality."""
    
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
        assert data_value == "hello from conftest temp task"
    
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
        with patch('aiokafka.AIOKafkaProducer', autospec=True) as MockKafkaProducer:
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockKafkaProducer)
            producer = TaskExecutionProducer(
                bootstrap_servers=test_config["bootstrap_servers"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                producer=mock_aiokafka_producer,
            )
            await producer.start()
            assert producer.is_healthy()
            await producer.stop()
            assert not producer.is_healthy()
    
    @pytest.mark.asyncio
    async def test_publish_task_execution(self, test_config, sample_task_execution):
        """Test publishing TaskExecution message."""
        with patch('aiokafka.AIOKafkaProducer', autospec=True) as MockKafkaProducer:
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockKafkaProducer)
            producer = TaskExecutionProducer(
                bootstrap_servers=test_config["bootstrap_servers"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                producer=mock_aiokafka_producer,
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
        with (patch("aiokafka.AIOKafkaConsumer", autospec=True) as MockConsumer,
              patch("aiokafka.AIOKafkaProducer", autospec=True) as MockProducer):
            mock_aiokafka_consumer = await prepare_aio_kafka_consumer(MockConsumer)
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockProducer)

            executor = TaskExecutor(
                task_path=temp_task_file,
                task_name=test_config["task_name"],
                timeout=test_config["task_timeout"]
            )
            await executor.load_task()

            producer = TaskExecutionProducer(
                bootstrap_servers=test_config["bootstrap_servers"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                producer=mock_aiokafka_producer,
            )
            await producer.start()

            consumer = TaskInputConsumer(
                bootstrap_servers=test_config["bootstrap_servers"],
                group_id=test_config["group_id"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                task_executor=executor,
                producer=producer,
                consumer=mock_aiokafka_consumer,
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
        with (patch("aiokafka.AIOKafkaConsumer", autospec=True) as MockConsumer,
              patch("aiokafka.AIOKafkaProducer", autospec=True) as MockProducer):
            mock_aiokafka_consumer = await prepare_aio_kafka_consumer(MockConsumer)
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockProducer)

            executor = TaskExecutor(
                task_path=temp_task_file,
                task_name=test_config["task_name"],
                timeout=test_config["task_timeout"]
            )
            await executor.load_task()

            producer = TaskExecutionProducer(
                bootstrap_servers=test_config["bootstrap_servers"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                producer=mock_aiokafka_producer,
            )
            await producer.start()

            consumer = TaskInputConsumer(
                bootstrap_servers=test_config["bootstrap_servers"],
                group_id=test_config["group_id"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                task_executor=executor,
                producer=producer,
                consumer=mock_aiokafka_consumer,
            )
            await consumer.start()

            # Test that messages with wrong key are filtered out (by not processing them)

            await consumer.stop()
            await producer.stop()
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
        
        with (patch("aiokafka.AIOKafkaConsumer", autospec=True) as MockConsumer,
              patch("aiokafka.AIOKafkaProducer", autospec=True) as MockProducer):
            mock_aiokafka_consumer = await prepare_aio_kafka_consumer(MockConsumer)
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockProducer)

            producer = TaskExecutionProducer(
                bootstrap_servers=test_config["bootstrap_servers"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                producer=mock_aiokafka_producer,
            )
            await producer.start()
            
            consumer = TaskInputConsumer(
                bootstrap_servers=test_config["bootstrap_servers"],
                group_id=test_config["group_id"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                task_executor=executor,
                producer=producer,
                consumer=mock_aiokafka_consumer,
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
        
        with (patch("aiokafka.AIOKafkaConsumer", autospec=True) as MockConsumer,
              patch("aiokafka.AIOKafkaProducer", autospec=True) as MockProducer):
            mock_aiokafka_consumer = await prepare_aio_kafka_consumer(MockConsumer)
            mock_aiokafka_producer = await prepare_aio_kafka_producer(MockProducer)

            producer = TaskExecutionProducer(
                bootstrap_servers=test_config["bootstrap_servers"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                producer=mock_aiokafka_producer,
            )
            await producer.start()
            
            consumer = TaskInputConsumer(
                bootstrap_servers=test_config["bootstrap_servers"],
                group_id=test_config["group_id"],
                tenant_id=test_config["tenant_id"],
                task_name=test_config["task_name"],
                task_executor=executor,
                producer=producer,
                consumer=mock_aiokafka_consumer,
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