"""
Integration tests for the complete executors-py service.
"""

import asyncio
import pytest
from typing import Optional
from testcontainers.kafka import KafkaContainer

from executors.service import ExecutorService, ExecutorMode


class TestServiceIntegration:
    """Integration tests for the complete service."""
    
    @pytest.fixture(scope="session")
    def kafka_container(self) -> str:
        """Spin up a Kafka container and yield the bootstrap servers URL."""
        container: Optional[KafkaContainer] = None
        try:
            container = KafkaContainer()
            container.start()
            bootstrap = container.get_bootstrap_server()
            yield bootstrap
        finally:
            if container is not None:
                container.stop()

    @pytest.mark.asyncio
    async def test_service_plan_executor_mode(self, temp_plan_file, test_config, kafka_container):
        """Test service configured as PlanExecutor."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.PLAN,
            executor_name=test_config["plan_name"],
            executor_path=temp_plan_file,
            executor_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Verify configuration
        assert service.mode is ExecutorMode.PLAN
        
        # Start service
        await service.start()
        assert service.is_running
        assert await service.health_check()
        
        # Verify plan components are initialized
        assert service.plan_executor is not None
        assert service.input_consumer is not None
        assert service.execution_producer is not None
        
        # Verify task components are not initialized
        assert service.task_executor is None
        
        # Stop service
        await service.stop()
        assert not service.is_running
    
    @pytest.mark.asyncio
    async def test_service_task_executor_mode(self, temp_task_file, test_config, kafka_container):
        """Test service configured as TaskExecutor."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.TASK,
            executor_name=test_config["task_name"],
            executor_path=temp_task_file,
            executor_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Verify configuration
        assert service.mode is ExecutorMode.TASK
        
        # Start service
        await service.start()
        assert service.is_running
        assert await service.health_check()
        
        # Verify task components are initialized
        assert service.task_executor is not None
        assert service.input_consumer is not None
        assert service.execution_producer is not None
        
        # Verify plan components are not initialized
        assert service.plan_executor is None
        
        # Stop service
        await service.stop()
        assert not service.is_running
    
    @pytest.mark.asyncio
    async def test_service_invalid_configuration_no_params(self, test_config):
        """Test service with no configuration parameters."""
        with pytest.raises(ValueError, match="Service must be configured for either PlanExecutor or TaskExecutor mode"):
            ExecutorService(
                tenant_id=test_config["tenant_id"],
                mode=ExecutorMode.PLAN,
                executor_name="",
                executor_path="",
                executor_timeout=0,
                kafka_bootstrap_servers=test_config["bootstrap_servers"],
                kafka_group_id=test_config["group_id"]
            )
    
    @pytest.mark.asyncio
    async def test_service_invalid_configuration_both_params(self, temp_plan_file, temp_task_file, test_config):
        """In the unified executor config, 'both params' scenario is obsolete; valid config should succeed."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.PLAN,
            executor_name=test_config["plan_name"],
            executor_path=temp_plan_file,
            executor_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
            kafka_group_id=test_config["group_id"]
        )
        assert service.mode is ExecutorMode.PLAN
    
    @pytest.mark.asyncio
    async def test_service_startup_shutdown_plan_executor(self, temp_plan_file, test_config, kafka_container):
        """Test PlanExecutor service startup and shutdown procedures."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.PLAN,
            executor_name=test_config["plan_name"],
            executor_path=temp_plan_file,
            executor_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Test startup event
        startup_task = asyncio.create_task(service.wait_for_startup(timeout=20.0))
        await service.start()
        await startup_task
        
        # Test shutdown event
        shutdown_task = asyncio.create_task(service.wait_for_shutdown(timeout=20.0))
        await service.stop()
        await shutdown_task
    
    @pytest.mark.asyncio
    async def test_service_startup_shutdown_task_executor(self, temp_task_file, test_config, kafka_container):
        """Test TaskExecutor service startup and shutdown procedures."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.TASK,
            executor_name=test_config["task_name"],
            executor_path=temp_task_file,
            executor_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Test startup event
        startup_task = asyncio.create_task(service.wait_for_startup(timeout=20.0))
        await service.start()
        await startup_task
        
        # Test shutdown event
        shutdown_task = asyncio.create_task(service.wait_for_shutdown(timeout=20.0))
        await service.stop()
        await shutdown_task
    
    @pytest.mark.asyncio
    async def test_service_health_check_plan_executor(self, temp_plan_file, test_config, kafka_container):
        """Test PlanExecutor service health check functionality."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.PLAN,
            executor_name=test_config["plan_name"],
            executor_path=temp_plan_file,
            executor_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Health check should fail when not running
        assert not await service.health_check()
        
        # Start service
        await service.start()
        assert await service.health_check()
        
        # Stop service
        await service.stop()
        assert not await service.health_check()
    
    @pytest.mark.asyncio
    async def test_service_health_check_task_executor(self, temp_task_file, test_config, kafka_container):
        """Test TaskExecutor service health check functionality."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.TASK,
            executor_name=test_config["task_name"],
            executor_path=temp_task_file,
            executor_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Health check should fail when not running
        assert not await service.health_check()
        
        # Start service
        await service.start()
        assert await service.health_check()
        
        # Stop service
        await service.stop()
        assert not await service.health_check()
    
    @pytest.mark.asyncio
    async def test_service_error_recovery_plan_executor(self, temp_plan_file, test_config, kafka_container):
        """Test PlanExecutor service error recovery."""
        # Create a plan that raises an exception
        with open(temp_plan_file, "w") as f:
            f.write("""
from agentic_common.pb import PlanInput, PlanResult

def plan(plan_input):
    raise RuntimeError("Service test error")
""")
        
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.PLAN,
            executor_name=test_config["plan_name"],
            executor_path=temp_plan_file,
            executor_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Service should start even with problematic plan
        await service.start()
        assert service.is_running
        
        # Health check should still pass (components are running)
        assert await service.health_check()
        
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_service_error_recovery_task_executor(self, temp_task_file, test_config, kafka_container):
        """Test TaskExecutor service error recovery."""
        # Create a task that raises an exception
        with open(temp_task_file, "w") as f:
            f.write("""
from agentic_common.pb import TaskInput, TaskResult

def task(task_input):
    raise RuntimeError("Service test error")
""")
        
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.TASK,
            executor_name=test_config["task_name"],
            executor_path=temp_task_file,
            executor_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Service should start even with problematic task
        await service.start()
        assert service.is_running
        
        # Health check should still pass (components are running)
        assert await service.health_check()
        
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_service_restart_plan_executor(self, temp_plan_file, test_config, kafka_container):
        """Test PlanExecutor service restart functionality."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.PLAN,
            executor_name=test_config["plan_name"],
            executor_path=temp_plan_file,
            executor_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Start service
        await service.start()
        assert service.is_running
        assert await service.health_check()
        
        # Stop service
        await service.stop()
        assert not service.is_running
        
        # Restart service
        await service.start()
        assert service.is_running
        assert await service.health_check()
        
        # Stop service again
        await service.stop()
        assert not service.is_running
    
    @pytest.mark.asyncio
    async def test_service_restart_task_executor(self, temp_task_file, test_config, kafka_container):
        """Test TaskExecutor service restart functionality."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            mode=ExecutorMode.TASK,
            executor_name=test_config["task_name"],
            executor_path=temp_task_file,
            executor_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=kafka_container,
            kafka_group_id=test_config["group_id"]
        )
        
        # Start service
        await service.start()
        assert service.is_running
        assert await service.health_check()
        
        # Stop service
        await service.stop()
        assert not service.is_running
        
        # Restart service
        await service.start()
        assert service.is_running
        assert await service.health_check()
        
        # Stop service again
        await service.stop()
        assert not service.is_running 