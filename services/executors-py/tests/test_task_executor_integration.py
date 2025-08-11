"""Integration test for TaskExecutor with a real Kafka broker via Testcontainers.

This test spins up an ephemeral Kafka broker, starts the `ExecutorService` in
TaskExecutor mode, produces a `TaskInput` message to the task-inputs topic, and
asserts that a `TaskExecution` is produced to the task-executions topic.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from datetime import datetime, timedelta
import uuid

import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from testcontainers.kafka import KafkaContainer

from agentic_common.pb import (
    ExecutionStatus,
    TaskExecution,
    TaskResult,
)
from agentic_common.kafka_utils import (
    get_task_inputs_topic,
    get_task_execution_topic,
)
from executors.service import ExecutorService
from tests.conftest import sample_task_input_full


@pytest.fixture(scope="session")
def kafka_container() -> str:
    """Spin up a Kafka container and yield the bootstrap servers URL.

    Scope is session to avoid repeated container startups for multiple tests.
    """
    container: Optional[KafkaContainer] = None
    try:
        container = KafkaContainer()
        container.start()
        bootstrap = container.get_bootstrap_server()
        yield bootstrap
    finally:
        if container is not None:
            container.stop()


@asynccontextmanager
async def start_task_executor_service(
    *,
    tenant_id: str,
    task_name: str,
    task_path: str,
    bootstrap_servers: str,
    startup_timeout: float = 10.0,
) -> AsyncIterator[ExecutorService]:
    """Async context manager that starts and stops the ExecutorService in TaskExecutor mode."""
    # Ensure tenant id is visible to code paths that rely on env var
    prev_tenant = os.environ.get("TENANT_ID")
    os.environ["TENANT_ID"] = tenant_id

    service = ExecutorService(
        tenant_id=tenant_id,
        task_name=task_name,
        task_path=task_path,
        kafka_bootstrap_servers=bootstrap_servers,
        kafka_group_id=f"it-{tenant_id}",
        task_timeout=15,
    )

    try:
        await service.start()
        await service.wait_for_startup(timeout=startup_timeout)
        yield service
    finally:
        try:
            await service.stop()
        finally:
            if prev_tenant is None:
                os.environ.pop("TENANT_ID", None)
            else:
                os.environ["TENANT_ID"] = prev_tenant


async def _poll_for_task_execution(
    consumer: AIOKafkaConsumer,
    *,
    expected_key: str,
    timeout_seconds: float = 10.0,
) -> TaskExecution:
    """Poll the consumer with exponential backoff until a matching message arrives."""
    deadline = asyncio.get_event_loop().time() + timeout_seconds
    delay = 0.1
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            raise AssertionError("Timed out waiting for TaskExecution message")

        try:
            msg = await asyncio.wait_for(consumer.getone(), timeout=min(remaining, 1.0))
        except asyncio.TimeoutError:
            msg = None
        if msg is not None and msg.key == expected_key and isinstance(msg.value, TaskExecution):
            return msg.value

        await asyncio.sleep(delay)
        delay = min(delay * 2, 1.0)


@pytest.mark.asyncio
async def test_task_executor_integration_with_kafka_container(temp_task_file, kafka_container):
    """End-to-end TaskExecutor test using a real Kafka broker.

    Arrange: start Kafka and the ExecutorService in TaskExecutor mode.
    Act: produce a TaskInput to task-inputs-<tenant> with task_name as the key.
    Assert: consume from task-executions-<tenant> and verify the TaskExecution.
    """
    tenant_id = "evil-corp"
    task_name = "query_llm"
    task_path = temp_task_file  # Deliberately using temp_plan_file as requested
    bootstrap_servers = kafka_container

    # Topics
    task_input_topic = get_task_inputs_topic(tenant_id)
    task_execution_topic = get_task_execution_topic(tenant_id)

    async with start_task_executor_service(
        tenant_id=tenant_id,
        task_name=task_name,
        task_path=task_path,
        bootstrap_servers=bootstrap_servers,
    ):
        # Producer: send TaskInput with key = task_name
        producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            value_serializer=lambda v: v.SerializeToString() if v else None,
            acks="all",
        )
        await producer.start()
        try:
            task_input = sample_task_input_full()
            # Modify task_name as required
            task_input.task_name = task_name
            await producer.send_and_wait(
                topic=task_input_topic,
                key=task_name,
                value=task_input,
            )
        finally:
            await producer.stop()

        # Consumer: poll task-executions topic and verify output
        consumer = AIOKafkaConsumer(
            task_execution_topic,
            bootstrap_servers=bootstrap_servers,
            group_id=f"it-{tenant_id}-assert",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            value_deserializer=lambda v: TaskExecution.FromString(v) if v else None,
        )
        await consumer.start()
        try:
            task_execution = await _poll_for_task_execution(
                consumer,
                expected_key=task_name,
                timeout_seconds=10.0,
            )

            # Assertions
            assert task_execution.header.name == task_name, "header.name should equal task_name"
            assert (
                task_execution.header.status == ExecutionStatus.EXECUTION_STATUS_SUCCEEDED
            ), "TaskExecution should be marked as succeeded"
            assert task_execution.result is not None, "TaskExecution should have a result"
            assert (
                task_execution.result.error_message == ""
            ), "TaskExecution.result.error_message should be empty"

            # Header fields
            assert task_execution.header.tenant_id == tenant_id, "header.tenant_id should match"
            assert task_execution.header.exec_id, "header.exec_id should be set"
            # Validate exec_id is a UUID
            _ = uuid.UUID(task_execution.header.exec_id)

            # Timestamp validation: parsable ISO8601 and recent
            assert task_execution.header.created_at, "header.created_at should be set"
            created_at_dt = datetime.fromisoformat(task_execution.header.created_at)
            now = datetime.now(created_at_dt.tzinfo) if created_at_dt.tzinfo else datetime.utcnow()
            assert now - timedelta(minutes=5) <= created_at_dt <= now + timedelta(minutes=1), (
                "header.created_at should be a recent timestamp"
            )

            # Result fields: ensure structure exists
            assert isinstance(task_execution.result, TaskResult), "result should be a TaskResult"

            # Verify parent linkage propagated from input
            assert task_execution.parent_plan_exec_id == "1234", "parent_plan_exec_id should propagate from input"
            assert task_execution.parent_plan_name == "decide_which_llm_to_use", "parent_plan_name should propagate from input"
        finally:
            await consumer.stop()


