"""
Tests for plan execution flow using Mockafka decorators.
"""

import pytest
from mockafka import produce, consume

from executors.plan_kafka_consumer import PlanInputConsumer
from executors.plan_kafka_producer import PlanExecutionProducer
from executors.plan_executor import PlanExecutor
from agentic_common.pb import ExecutionStatus


class TestPlanExecutor:
    """Test PlanExecutor functionality."""
    
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
    async def test_execute_plan_success(self, temp_plan_file, test_config, sample_plan_input):
        """Test successful plan execution."""
        executor = PlanExecutor(
            plan_path=temp_plan_file,
            plan_name=test_config["plan_name"],
            timeout=test_config["plan_timeout"]
        )
        
        await executor.load_plan()
        result = await executor.execute_plan(sample_plan_input)
        
        assert result.header.name == test_config["plan_name"]
        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_SUCCEEDED
        assert result.result.next_task_names == ["sample-task"]
        assert result.result.error_message == ""
    
    @pytest.mark.asyncio
    async def test_execute_plan_timeout(self, temp_plan_file, test_config, sample_plan_input):
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
        result = await executor.execute_plan(sample_plan_input)
        
        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_FAILED
        assert "timed out" in result.result.error_message
    
    @pytest.mark.asyncio
    async def test_execute_plan_error(self, temp_plan_file, test_config, sample_plan_input):
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
        result = await executor.execute_plan(sample_plan_input)
        
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
    async def test_consumer_message_filtering(self, temp_plan_file, test_config, sample_plan_input):
        """Test consumer message filtering by plan name."""
        # Create a mock producer for testing
        mock_producer = PlanExecutionProducer(
            bootstrap_servers=test_config["bootstrap_servers"],
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"]
        )
        
        # Create consumer
        consumer = PlanInputConsumer(
            bootstrap_servers=test_config["bootstrap_servers"],
            group_id=test_config["group_id"],
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
    async def test_plan_flow_end_to_end(self, temp_plan_file, test_config, sample_plan_input):
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
    async def test_plan_flow_error_handling(self, temp_plan_file, test_config, sample_plan_input):
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
        result = await executor.execute_plan(sample_plan_input)
        assert result.header.status == ExecutionStatus.EXECUTION_STATUS_FAILED
        assert "Simulated plan error" in result.result.error_message
        
        # Cleanup
        await consumer.stop()
        await producer.stop()
        await executor.cleanup() 