"""
Core PlanExecutor class for handling plan execution logic.
Dynamically loads and executes user-supplied plan.py files.
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

from agentic_common.pb import PlanInput, PlanExecution, PlanResult, ExecutionHeader, ExecutionStatus
from .base_executor import BaseExecutor


class PlanExecutor(BaseExecutor):
    """
    Core PlanExecutor class for handling plan execution.
    
    This class:
    - Dynamically loads user-supplied plan.py files
    - Executes plans with timeout handling
    - Wraps results in PlanExecution protobuf messages
    - Handles errors and exceptions
    """
    
    def __init__(self, plan_path: str, plan_name: str, timeout: int = 300):
        super().__init__(executor_path=plan_path, executor_name=plan_name, timeout=timeout)
        self.plan_path = plan_path
        self.plan_name = plan_name
    
    async def load_plan(self) -> None:
        await self.load()
    
    async def execute_plan(self, plan_input: PlanInput) -> PlanExecution:
        return await self.execute(plan_input)
    
    def get_module_name(self) -> str:
        return "plan"

    def get_function_name(self) -> str:
        return "plan"

    def validate_user_function_signature(self, fn: Any) -> None:
        # Already enforced to one parameter in base; accept any single-arg callable
        return

    def build_success_execution(self, plan_input: PlanInput, result: PlanResult) -> PlanExecution:
        header = ExecutionHeader(
            name=plan_input.plan_name,
            exec_id=str(uuid.uuid4()),
            tenant_id=os.environ.get("TENANT_ID", ""),
            created_at=datetime.now(UTC).isoformat(),
            status=ExecutionStatus.EXECUTION_STATUS_SUCCEEDED,
        )
        parent_task_exec_ids = []
        parent_task_names = []
        for task_exec in plan_input.task_executions:
            if task_exec.header and task_exec.header.exec_id:
                parent_task_exec_ids.append(task_exec.header.exec_id)
                parent_task_names.append(task_exec.header.name)
        return PlanExecution(
            header=header,
            parent_task_exec_ids=parent_task_exec_ids,
            result=result,
            parent_task_names=parent_task_names,
        )

    def build_error_execution(self, plan_input: PlanInput, error_message: str) -> PlanExecution:
        header = ExecutionHeader(
            name=plan_input.plan_name,
            exec_id=str(uuid.uuid4()),
            tenant_id=os.environ.get("TENANT_ID", ""),
            created_at=datetime.now(UTC).isoformat(),
            status=ExecutionStatus.EXECUTION_STATUS_FAILED,
        )
        parent_task_exec_ids = []
        parent_task_names = []
        for task_exec in plan_input.task_executions:
            if task_exec.header and task_exec.header.exec_id:
                parent_task_exec_ids.append(task_exec.header.exec_id)
                parent_task_names.append(task_exec.header.name)
        return PlanExecution(
            header=header,
            parent_task_exec_ids=parent_task_exec_ids,
            result=PlanResult(error_message=error_message),
            parent_task_names=parent_task_names,
        )

    # Backward-compatibility accessors for tests
    @property
    def plan_function(self) -> Any:
        return self._user_function

    @property
    def plan_module(self) -> Any:
        return self._module
    
    async def cleanup(self) -> None:
        await super().cleanup()
    
    def is_healthy(self) -> bool:
        return super().is_healthy()