"""
Core TaskExecutor class for handling task execution logic.
Dynamically loads and executes user-supplied task.py files.
"""

import asyncio
import importlib.util
import inspect
import os
import sys
import time
import uuid
from datetime import datetime, UTC
from typing import Any, Optional

import structlog

from agentic_common.pb import TaskInput, TaskExecution, TaskResult, ExecutionHeader, ExecutionStatus


class TaskExecutor:
    """
    Core TaskExecutor class for handling task execution.
    
    This class:
    - Dynamically loads user-supplied task.py files
    - Executes tasks with timeout handling
    - Wraps results in TaskExecution protobuf messages
    - Handles errors and exceptions
    """
    
    def __init__(
        self,
        task_path: str,
        task_name: str,
        timeout: int = 300,
    ):
        self.task_path = task_path
        self.task_name = task_name
        self.timeout = timeout
        
        self.logger = structlog.get_logger(__name__)
        
        # Loaded task module
        self.task_module: Optional[Any] = None
        self.task_function: Optional[Any] = None
        
        # Execution state
        self._loaded = False
        self._healthy = True
    
    async def load_task(self) -> None:
        """Dynamically load the task.py module from the configured path."""
        if self._loaded:
            self.logger.warning("Task is already loaded")
            return
        
        self.logger.info("Loading task module", task_path=self.task_path)
        
        try:
            # Check if task file exists
            if not os.path.exists(self.task_path):
                raise FileNotFoundError(f"Task file not found: {self.task_path}")
            
            # Load the task module
            spec = importlib.util.spec_from_file_location("task", self.task_path)
            if not spec or not spec.loader:
                raise ImportError(f"Failed to create spec for task module: {self.task_path}")
            
            self.task_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.task_module)
            
            # Get the task function
            if not hasattr(self.task_module, "task"):
                raise AttributeError("Task module must have a 'task' function")
            
            self.task_function = getattr(self.task_module, "task")
            
            # Validate task function signature
            sig = inspect.signature(self.task_function)
            if len(sig.parameters) != 1:
                raise ValueError("Task function must take exactly one parameter (task_input)")
            
            self._loaded = True
            self._healthy = True
            
            self.logger.info("Task module loaded successfully", task_path=self.task_path)
            
        except Exception as e:
            self.logger.error("Failed to load task module", error=str(e), exc_info=True)
            self._healthy = False
            raise
    
    async def execute_task(self, task_input: TaskInput) -> TaskExecution:
        """Execute the task with the given TaskInput and return a TaskExecution."""
        if not self._loaded:
            raise RuntimeError("Task module is not loaded")
        
        start_time = time.time()
        
        self.logger.info(
            "Executing task",
            task_name=task_input.task_name
        )

        # Create ExecutionHeader
        header = ExecutionHeader(
            name=task_input.task_name,
            exec_id=str(uuid.uuid4()),
            tenant_id=os.environ.get("TENANT_ID", ""),
            created_at=datetime.now(UTC).isoformat(),
            status=ExecutionStatus.EXECUTION_STATUS_SUCCEEDED
        )
        # Extract parent plan name
        # Extract parent plan execution ID
        parent_plan_exec_id = ""
        parent_plan_name = ""
        if task_input.plan_execution and task_input.plan_execution.header:
            parent_plan_exec_id = task_input.plan_execution.header.exec_id
            parent_plan_name = task_input.plan_execution.header.name

        try:
            # Execute task with timeout
            task_result = await asyncio.wait_for(
                self._execute_task_async(task_input),
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            self.logger.info(
                "Task execution completed successfully",
                task_name=task_input.task_name,
                execution_time=execution_time
            )
            
            # Create successful TaskExecution


            return TaskExecution(
                header=header,
                parent_plan_exec_id=parent_plan_exec_id,
                result=task_result,
                parent_plan_name=parent_plan_name
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            if isinstance(e, asyncio.TimeoutError):
                error_msg = f"Task execution timed out after {self.timeout} seconds"
            else:
                error_msg = f"Task execution failed: {str(e)}"
            
            self.logger.error(
                "Task execution timed out",
                task_name=task_input.task_name,
                timeout=self.timeout,
                execution_time=execution_time
            )
            
            # Create timeout TaskExecution
            
            # Create ExecutionHeader
            header.status=ExecutionStatus.EXECUTION_STATUS_FAILED

            return TaskExecution(
                header=header,
                parent_plan_exec_id=parent_plan_exec_id,
                result=TaskResult(
                    error_message=error_msg
                ),
                parent_plan_name=parent_plan_name
            )

    
    async def _execute_task_async(self, task_input: TaskInput) -> TaskResult:
        """Execute the task function asynchronously."""
        # Execute the task function with the actual TaskInput protobuf
        result = await asyncio.get_event_loop().run_in_executor(
            None, self.task_function, task_input
        )
        
        # The task function should return a TaskResult directly
        if isinstance(result, TaskResult):
            return result
        else:
            # If it returns something else, that's an error
            return TaskResult(
                error_message=f"Task function returned invalid type: {type(result)}. Expected TaskResult."
            )
    
    async def cleanup(self) -> None:
        """Clean up resources used by the task executor."""
        self.logger.info("Cleaning up task executor")
        
        # Clear loaded module
        self.task_module = None
        self.task_function = None
        self._loaded = False
        
        # Clear any module from sys.modules if it was loaded
        if "task" in sys.modules:
            del sys.modules["task"]
    
    def is_healthy(self) -> bool:
        """Check if the task executor is healthy."""
        return self._healthy and self._loaded 