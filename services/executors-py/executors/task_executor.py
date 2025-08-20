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
from .base_executor import BaseExecutor


class TaskExecutor(BaseExecutor):
    """
    Core TaskExecutor class for handling task execution.
    
    This class:
    - Dynamically loads user-supplied task.py files
    - Executes tasks with timeout handling
    - Wraps results in TaskExecution protobuf messages
    - Handles errors and exceptions
    """
    
    def __init__(self, task_path: str, task_name: str, timeout: int = 300):
        super().__init__(executor_path=task_path, executor_name=task_name, timeout=timeout)
        self.task_path = task_path
        self.task_name = task_name
    
    async def load_task(self) -> None:
        await self.load()
    
    async def execute_task(self, task_input: TaskInput) -> TaskExecution:
        return await self.execute(task_input)

    
    def get_module_name(self) -> str:
        return "task"

    def get_function_name(self) -> str:
        return "task"

    def validate_user_function_signature(self, fn: Any) -> None:
        return

    def build_success_execution(self, task_input: TaskInput, result: TaskResult) -> TaskExecution:
        header = ExecutionHeader(
            name=task_input.task_name,
            exec_id=str(uuid.uuid4()),
            tenant_id=os.environ.get("TENANT_ID", ""),
            created_at=datetime.now(UTC).isoformat(),
            status=ExecutionStatus.EXECUTION_STATUS_SUCCEEDED,
        )
        parent_plan_exec_id = ""
        parent_plan_name = ""
        if task_input.plan_execution and task_input.plan_execution.header:
            parent_plan_exec_id = task_input.plan_execution.header.exec_id
            parent_plan_name = task_input.plan_execution.header.name
        return TaskExecution(
            header=header,
            parent_plan_exec_id=parent_plan_exec_id,
            result=result,
            parent_plan_name=parent_plan_name,
        )

    def build_error_execution(self, task_input: TaskInput, error_message: str) -> TaskExecution:
        header = ExecutionHeader(
            name=task_input.task_name,
            exec_id=str(uuid.uuid4()),
            tenant_id=os.environ.get("TENANT_ID", ""),
            created_at=datetime.now(UTC).isoformat(),
            status=ExecutionStatus.EXECUTION_STATUS_FAILED,
        )
        parent_plan_exec_id = ""
        parent_plan_name = ""
        if task_input.plan_execution and task_input.plan_execution.header:
            parent_plan_exec_id = task_input.plan_execution.header.exec_id
            parent_plan_name = task_input.plan_execution.header.name
        return TaskExecution(
            header=header,
            parent_plan_exec_id=parent_plan_exec_id,
            result=TaskResult(error_message=error_message),
            parent_plan_name=parent_plan_name,
        )

    # Backward-compatibility accessors for tests
    @property
    def task_function(self) -> Any:
        return self._user_function

    @property
    def task_module(self) -> Any:
        return self._module
    
    async def cleanup(self) -> None:
        await super().cleanup()
    
    def is_healthy(self) -> bool:
        return super().is_healthy()