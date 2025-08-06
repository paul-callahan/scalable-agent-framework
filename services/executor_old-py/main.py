"""
Main entry point for executor microservice.

This module provides the main entry point for the executor service that
loads configuration from environment variables, initializes the task/plan
registry with available classes, initializes logging, starts Kafka
consumers/producers, and runs the FastAPI server using uvicorn==0.30.1.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agentic_common.logging_config import setup_logging
from executor.service import ExecutorService

# Import some example tasks and plans for registration
# These would typically be imported from user-defined modules
from agentic.core.task import DeprecatedTaskExecutor
from agentic.core.plan import DeprecatedPlanExecutor


# Example task implementation
class ExampleTask(DeprecatedTaskExecutor):
    """Example task implementation."""
    
    async def execute(self, lastResult):
        from agentic.core.task import TaskResult
        return TaskResult(
            data={"message": "Hello from example task!"},
            mime_type="application/json",
            size_bytes=50,
        )


# Example plan implementation
class ExamplePlan(DeprecatedPlanExecutor):
    """Example plan implementation."""
    
    async def plan(self, lastResult):
        from agentic.core.plan import PlanResult
        return PlanResult(
            next_task_names=["example_task"],
            metadata={"plan_type": "example"},
            confidence=0.9,
        )


async def main():
    """Main entry point for the executor service."""
    # Setup logging
    setup_logging()
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Kafka configuration
    os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    os.environ.setdefault("KAFKA_CLIENT_ID", "executor")
    os.environ.setdefault("KAFKA_GROUP_ID", "executor-group")
    
    # Logging configuration
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("LOG_FORMAT", "json")
    
    # Create and run service
    service = ExecutorService(host=host, port=port)
    
    # Register example tasks and plans
    service.register_task("example_task", ExampleTask)
    service.register_plan("example_plan", ExamplePlan)
    
    try:
        await service.start()
        await service.run()
        
    except KeyboardInterrupt:
        print("Received keyboard interrupt, shutting down...")
        
    except Exception as e:
        print(f"Service error: {e}")
        sys.exit(1)
        
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main()) 