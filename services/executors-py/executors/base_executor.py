"""
Base executor for dynamically loading and executing user-supplied executor modules.
Provides shared module loading, timeout execution, error handling, health, and cleanup.
"""

import asyncio
import importlib.util
import inspect
import os
import sys
import time
import uuid
from datetime import datetime, UTC
from typing import Any

import structlog


class BaseExecutor:
    """
    Base executor that handles:
    - Dynamic module load from a file path
    - Function resolution and signature validation
    - Async execution with timeout via thread pool
    - Error handling and health reporting

    Subclasses must implement the following hooks:
    - get_module_name() -> str
    - get_function_name() -> str
    - validate_user_function_signature(fn) -> None
    - build_success_execution(input_msg, result) -> execution_message
    - build_error_execution(input_msg, error_message: str) -> execution_message
    """

    def __init__(self, *, executor_path: str, executor_name: str, timeout: int) -> None:
        self.executor_path = executor_path
        self.executor_name = executor_name
        self.timeout = timeout

        self.logger = structlog.get_logger(__name__)

        self._module: Any | None = None
        self._user_function: Any | None = None
        self._loaded = False
        self._healthy = True

    # ---------- Abstract hooks ----------
    def get_module_name(self) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    def get_function_name(self) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    def validate_user_function_signature(self, fn: Any) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def build_success_execution(self, input_msg: Any, result: Any) -> Any:  # pragma: no cover - abstract
        raise NotImplementedError

    def build_error_execution(self, input_msg: Any, error_message: str) -> Any:  # pragma: no cover - abstract
        raise NotImplementedError

    # ---------- Shared logic ----------
    async def load(self) -> None:
        if self._loaded:
            self.logger.warning("Executor module is already loaded")
            return

        self.logger.info("Loading executor module", executor_path=self.executor_path)

        try:
            if not os.path.exists(self.executor_path):
                raise FileNotFoundError(f"Executor file not found: {self.executor_path}")

            module_name = self.get_module_name()
            spec = importlib.util.spec_from_file_location(module_name, self.executor_path)
            if not spec or not spec.loader:
                raise ImportError(f"Failed to create spec for module: {self.executor_path}")

            self._module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self._module)  # type: ignore[attr-defined]

            func_name = self.get_function_name()
            if not hasattr(self._module, func_name):
                raise AttributeError(f"Module must have a '{func_name}' function")

            self._user_function = getattr(self._module, func_name)

            # Validate signature
            sig = inspect.signature(self._user_function)
            self.validate_user_function_signature(self._user_function)
            if len(sig.parameters) != 1:
                raise ValueError(f"{func_name} function must take exactly one parameter")

            self._loaded = True
            self._healthy = True

            self.logger.info("Executor module loaded successfully", executor_path=self.executor_path)

        except Exception as e:
            self.logger.error("Failed to load executor module", error=str(e), exc_info=True)
            self._healthy = False
            raise

    async def execute(self, input_msg: Any) -> Any:
        if not self._loaded or self._user_function is None:
            raise RuntimeError("Executor module is not loaded")

        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                self._run_in_executor(input_msg),
                timeout=self.timeout,
            )

            execution_time = time.time() - start_time
            self.logger.info(
                "Executor run completed successfully",
                executor_name=self.executor_name,
                execution_time=execution_time,
            )
            return self.build_success_execution(input_msg, result)

        except asyncio.TimeoutError:
            error_msg = f"Execution timed out after {self.timeout} seconds"
            self.logger.error(
                "Executor run timed out",
                executor_name=self.executor_name,
                timeout=self.timeout,
            )
            return self.build_error_execution(input_msg, error_msg)

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                "Executor run failed",
                executor_name=self.executor_name,
                error=str(e),
                execution_time=execution_time,
                exc_info=True,
            )
            return self.build_error_execution(input_msg, str(e))

    async def _run_in_executor(self, input_msg: Any) -> Any:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._user_function, input_msg)

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up executor")
        self._module = None
        self._user_function = None
        self._loaded = False
        module_name = self.get_module_name()
        if module_name in sys.modules:
            del sys.modules[module_name]

    def is_healthy(self) -> bool:
        return self._healthy and self._loaded


