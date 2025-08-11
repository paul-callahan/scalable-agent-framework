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


class PlanExecutor:
    """
    Core PlanExecutor class for handling plan execution.
    
    This class:
    - Dynamically loads user-supplied plan.py files
    - Executes plans with timeout handling
    - Wraps results in PlanExecution protobuf messages
    - Handles errors and exceptions
    """
    
    def __init__(
        self,
        plan_path: str,
        plan_name: str,
        timeout: int = 300,
    ):
        self.plan_path = plan_path
        self.plan_name = plan_name
        self.timeout = timeout
        
        self.logger = structlog.get_logger(__name__)
        
        # Loaded plan module
        self.plan_module: Optional[Any] = None
        self.plan_function: Optional[Any] = None
        
        # Execution state
        self._loaded = False
        self._healthy = True
    
    async def load_plan(self) -> None:
        """Dynamically load the plan.py module from the configured path."""
        if self._loaded:
            self.logger.warning("Plan is already loaded")
            return
        
        self.logger.info("Loading plan module", plan_path=self.plan_path)
        
        try:
            # Check if plan file exists
            if not os.path.exists(self.plan_path):
                raise FileNotFoundError(f"Plan file not found: {self.plan_path}")
            
            # Load the plan module
            spec = importlib.util.spec_from_file_location("plan", self.plan_path)
            if not spec or not spec.loader:
                raise ImportError(f"Failed to create spec for plan module: {self.plan_path}")
            
            self.plan_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.plan_module)
            
            # Get the plan function
            if not hasattr(self.plan_module, "plan"):
                raise AttributeError("Plan module must have a 'plan' function")
            
            self.plan_function = getattr(self.plan_module, "plan")
            
            # Validate plan function signature
            sig = inspect.signature(self.plan_function)
            if len(sig.parameters) != 1:
                raise ValueError("Plan function must take exactly one parameter (plan_input)")
            
            self._loaded = True
            self._healthy = True
            
            self.logger.info("Plan module loaded successfully", plan_path=self.plan_path)
            
        except Exception as e:
            self.logger.error("Failed to load plan module", error=str(e), exc_info=True)
            self._healthy = False
            raise
    
    async def execute_plan(self, plan_input: PlanInput) -> PlanExecution:
        """Execute the plan with the given PlanInput and return a PlanExecution."""
        if not self._loaded:
            raise RuntimeError("Plan module is not loaded")
        
        start_time = time.time()
        
        self.logger.info(
            "Executing plan",
            plan_name=plan_input.plan_name
        )
        
        try:
            # Execute plan with timeout
            plan_result = await asyncio.wait_for(
                self._execute_plan_async(plan_input),
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            self.logger.info(
                "Plan execution completed successfully",
                plan_name=plan_input.plan_name,
                execution_time=execution_time
            )
            
            # Create successful PlanExecution
            
            # Create ExecutionHeader
            header = ExecutionHeader(
                name=plan_input.plan_name,
                exec_id=str(uuid.uuid4()),
                tenant_id=os.environ.get("TENANT_ID", ""),
                created_at=datetime.now(UTC).isoformat(),
                status=ExecutionStatus.EXECUTION_STATUS_SUCCEEDED
            )
            
            # Extract parent task execution IDs
            parent_task_exec_ids = []
            parent_task_names = []
            for task_exec in plan_input.task_executions:
                if task_exec.header and task_exec.header.exec_id:
                    parent_task_exec_ids.append(task_exec.header.exec_id)
                    parent_task_names.append(task_exec.header.name)

            return PlanExecution(
                header=header,
                parent_task_exec_ids=parent_task_exec_ids,
                result=plan_result,
                parent_task_names=parent_task_names
            )
            
        except asyncio.TimeoutError:
            error_msg = f"Plan execution timed out after {self.timeout} seconds"
            
            self.logger.error(
                "Plan execution timed out",
                plan_name=plan_input.plan_name,
                timeout=self.timeout,
            )

            # Create ExecutionHeader
            header = ExecutionHeader(
                name=plan_input.plan_name,
                exec_id=str(uuid.uuid4()),
                tenant_id=os.environ.get("TENANT_ID", ""),
                created_at=datetime.now(UTC).isoformat(),
                status=ExecutionStatus.EXECUTION_STATUS_FAILED
            )
            
            # Extract parent task names and execution IDs
            parent_task_exec_ids = []
            parent_task_names = []
            for task_exec in plan_input.task_executions:
                if task_exec.header and task_exec.header.exec_id:
                    parent_task_exec_ids.append(task_exec.header.exec_id)
                    parent_task_names.append(task_exec.header.name)

            
            return PlanExecution(
                header=header,
                parent_task_exec_ids=parent_task_exec_ids,
                result=PlanResult(
                    error_message=error_msg
                ),
                parent_task_names=parent_task_names
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.logger.error(
                "Plan execution failed",
                plan_name=plan_input.plan_name,
                error=str(e),
                execution_time=execution_time,
                exc_info=True
            )
            
            # Create error PlanExecution
            
            # Create ExecutionHeader
            header = ExecutionHeader(
                name=plan_input.plan_name,
                exec_id=str(uuid.uuid4()),
                tenant_id=os.environ.get("TENANT_ID", ""),
                created_at=datetime.now(UTC).isoformat(),
                status=ExecutionStatus.EXECUTION_STATUS_FAILED
            )
            
            # Extract parent task execution IDs
            parent_task_exec_ids = []
            parent_task_names = []
            for task_exec in plan_input.task_executions:
                if task_exec.header and task_exec.header.exec_id:
                    parent_task_exec_ids.append(task_exec.header.exec_id)
                    parent_task_names.append(task_exec.header.name)

            return PlanExecution(
                header=header,
                parent_task_exec_ids=parent_task_exec_ids,
                result=PlanResult(
                    error_message=str(e)
                ),
                parent_task_names=parent_task_names
            )
    
    async def _execute_plan_async(self, plan_input: PlanInput) -> PlanResult:
        """Execute the plan function asynchronously."""
        # Execute the plan function with the actual PlanInput protobuf
        result = await asyncio.get_event_loop().run_in_executor(
            None, self.plan_function, plan_input
        )
        
        # The plan function should return a PlanResult directly
        if isinstance(result, PlanResult):
            return result
        else:
            # If it returns something else, that's an error
            upstream_results = []
            for task_exec in plan_input.task_executions:
                if task_exec.result:
                    upstream_results.append(task_exec.result)
            
            return PlanResult(
                upstream_tasks_results=upstream_results,
                next_task_names=[],
                error_message=f"Plan function returned invalid type: {type(result)}. Expected PlanResult."
            )
    
    async def cleanup(self) -> None:
        """Clean up resources used by the plan executor."""
        self.logger.info("Cleaning up plan executor")
        
        # Clear loaded module
        self.plan_module = None
        self.plan_function = None
        self._loaded = False
        
        # Clear any module from sys.modules if it was loaded
        if "plan" in sys.modules:
            del sys.modules["plan"]
    
    def is_healthy(self) -> bool:
        """Check if the plan executor is healthy."""
        return self._healthy and self._loaded 