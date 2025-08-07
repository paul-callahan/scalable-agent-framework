"""
Integration tests for the complete executors-py service.
"""

import asyncio
import pytest

from executors.service import ExecutorService


class TestServiceIntegration:
    """Integration tests for the complete service."""
    
    @pytest.mark.asyncio
    async def test_service_plan_executor_mode(self, temp_plan_file, test_config):
        """Test service configured as PlanExecutor."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"],
            plan_path=temp_plan_file,
            plan_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
            kafka_group_id=test_config["group_id"]
        )
        
        # Verify configuration
        assert service.is_plan_executor
        assert not service.is_task_executor
        
        # Start service
        await service.start()
        assert service.is_running
        assert await service.health_check()
        
        # Verify plan components are initialized
        assert service.plan_executor is not None
        assert service.plan_consumer is not None
        assert service.plan_producer is not None
        
        # Verify task components are not initialized
        assert service.task_executor is None
        assert service.task_consumer is None
        assert service.task_producer is None
        
        # Stop service
        await service.stop()
        assert not service.is_running
    
    @pytest.mark.asyncio
    async def test_service_task_executor_mode(self, temp_task_file, test_config):
        """Test service configured as TaskExecutor."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"],
            task_path=temp_task_file,
            task_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
            kafka_group_id=test_config["group_id"]
        )
        
        # Verify configuration
        assert service.is_task_executor
        assert not service.is_plan_executor
        
        # Start service
        await service.start()
        assert service.is_running
        assert await service.health_check()
        
        # Verify task components are initialized
        assert service.task_executor is not None
        assert service.task_consumer is not None
        assert service.task_producer is not None
        
        # Verify plan components are not initialized
        assert service.plan_executor is None
        assert service.plan_consumer is None
        assert service.plan_producer is None
        
        # Stop service
        await service.stop()
        assert not service.is_running
    
    @pytest.mark.asyncio
    async def test_service_invalid_configuration_no_params(self, test_config):
        """Test service with no configuration parameters."""
        with pytest.raises(ValueError, match="Service must be configured for either PlanExecutor or TaskExecutor mode"):
            ExecutorService(
                tenant_id=test_config["tenant_id"],
                kafka_bootstrap_servers=test_config["bootstrap_servers"],
                kafka_group_id=test_config["group_id"]
            )
    
    @pytest.mark.asyncio
    async def test_service_invalid_configuration_both_params(self, temp_plan_file, temp_task_file, test_config):
        """Test service with both plan and task configuration parameters."""
        with pytest.raises(ValueError, match="Service cannot be configured for both PlanExecutor and TaskExecutor modes"):
            ExecutorService(
                tenant_id=test_config["tenant_id"],
                plan_name=test_config["plan_name"],
                plan_path=temp_plan_file,
                plan_timeout=test_config["plan_timeout"],
                task_name=test_config["task_name"],
                task_path=temp_task_file,
                task_timeout=test_config["task_timeout"],
                kafka_bootstrap_servers=test_config["bootstrap_servers"],
                kafka_group_id=test_config["group_id"]
            )
    
    @pytest.mark.asyncio
    async def test_service_startup_shutdown_plan_executor(self, temp_plan_file, test_config):
        """Test PlanExecutor service startup and shutdown procedures."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"],
            plan_path=temp_plan_file,
            plan_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
            kafka_group_id=test_config["group_id"]
        )
        
        # Test startup event
        startup_task = asyncio.create_task(service.wait_for_startup(timeout=5.0))
        await service.start()
        await startup_task
        
        # Test shutdown event
        shutdown_task = asyncio.create_task(service.wait_for_shutdown(timeout=5.0))
        await service.stop()
        await shutdown_task
    
    @pytest.mark.asyncio
    async def test_service_startup_shutdown_task_executor(self, temp_task_file, test_config):
        """Test TaskExecutor service startup and shutdown procedures."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"],
            task_path=temp_task_file,
            task_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
            kafka_group_id=test_config["group_id"]
        )
        
        # Test startup event
        startup_task = asyncio.create_task(service.wait_for_startup(timeout=5.0))
        await service.start()
        await startup_task
        
        # Test shutdown event
        shutdown_task = asyncio.create_task(service.wait_for_shutdown(timeout=5.0))
        await service.stop()
        await shutdown_task
    
    @pytest.mark.asyncio
    async def test_service_health_check_plan_executor(self, temp_plan_file, test_config):
        """Test PlanExecutor service health check functionality."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"],
            plan_path=temp_plan_file,
            plan_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
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
    async def test_service_health_check_task_executor(self, temp_task_file, test_config):
        """Test TaskExecutor service health check functionality."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"],
            task_path=temp_task_file,
            task_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
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
    async def test_service_error_recovery_plan_executor(self, temp_plan_file, test_config):
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
            plan_name=test_config["plan_name"],
            plan_path=temp_plan_file,
            plan_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
            kafka_group_id=test_config["group_id"]
        )
        
        # Service should start even with problematic plan
        await service.start()
        assert service.is_running
        
        # Health check should still pass (components are running)
        assert await service.health_check()
        
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_service_error_recovery_task_executor(self, temp_task_file, test_config):
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
            task_name=test_config["task_name"],
            task_path=temp_task_file,
            task_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
            kafka_group_id=test_config["group_id"]
        )
        
        # Service should start even with problematic task
        await service.start()
        assert service.is_running
        
        # Health check should still pass (components are running)
        assert await service.health_check()
        
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_service_restart_plan_executor(self, temp_plan_file, test_config):
        """Test PlanExecutor service restart functionality."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            plan_name=test_config["plan_name"],
            plan_path=temp_plan_file,
            plan_timeout=test_config["plan_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
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
    async def test_service_restart_task_executor(self, temp_task_file, test_config):
        """Test TaskExecutor service restart functionality."""
        service = ExecutorService(
            tenant_id=test_config["tenant_id"],
            task_name=test_config["task_name"],
            task_path=temp_task_file,
            task_timeout=test_config["task_timeout"],
            kafka_bootstrap_servers=test_config["bootstrap_servers"],
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