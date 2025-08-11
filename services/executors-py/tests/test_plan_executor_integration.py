"""Integration test for PlanExecutor with a real Kafka broker via Testcontainers.

This test spins up an ephemeral Kafka broker, starts the `ExecutorService` in
PlanExecutor mode, produces a `PlanInput` message to the plan-inputs topic, and
asserts that a `PlanExecution` is produced to the plan-executions topic.
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
    PlanExecution,
    PlanResult,
)
from executors.service import ExecutorService
from tests.conftest import sample_plan_input_full


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
async def start_executor_service(
    *,
    tenant_id: str,
    plan_name: str,
    plan_path: str,
    bootstrap_servers: str,
    startup_timeout: float = 10.0,
) -> AsyncIterator[ExecutorService]:
    """Async context manager that starts and stops the ExecutorService."""
    # Ensure tenant id is visible to code paths that rely on env var
    prev_tenant = os.environ.get("TENANT_ID")
    os.environ["TENANT_ID"] = tenant_id

    service = ExecutorService(
        tenant_id=tenant_id,
        plan_name=plan_name,
        plan_path=plan_path,
        kafka_bootstrap_servers=bootstrap_servers,
        kafka_group_id=f"it-{tenant_id}",
        plan_timeout=15,
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


async def _poll_for_plan_execution(
    consumer: AIOKafkaConsumer,
    *,
    expected_key: str,
    timeout_seconds: float = 10.0,
) -> PlanExecution:
    """Poll the consumer with exponential backoff until a matching message arrives."""
    deadline = asyncio.get_event_loop().time() + timeout_seconds
    delay = 0.1
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            raise AssertionError("Timed out waiting for PlanExecution message")

        try:
            msg = await asyncio.wait_for(consumer.getone(), timeout=min(remaining, 1.0))
        except asyncio.TimeoutError:
            msg = None
        if msg is not None and msg.key == expected_key and isinstance(msg.value, PlanExecution):
            return msg.value

        await asyncio.sleep(delay)
        delay = min(delay * 2, 1.0)


@pytest.mark.asyncio
async def test_plan_executor_integration_with_kafka_container(temp_plan_file, kafka_container):
    """End-to-end PlanExecutor test using a real Kafka broker.

    Arrange: start Kafka and the ExecutorService in PlanExecutor mode.
    Act: produce a PlanInput to plan-inputs-<tenant> with plan_name as the key.
    Assert: consume from plan-executions-<tenant> and verify the PlanExecution.
    """
    tenant_id = "evil-corp"
    plan_name = "decide_which_llm_to_use"
    plan_path = temp_plan_file
    bootstrap_servers = kafka_container

    # Topics
    plan_input_topic = f"plan-inputs-{tenant_id}"
    plan_execution_topic = f"plan-executions-{tenant_id}"

    async with start_executor_service(
        tenant_id=tenant_id,
        plan_name=plan_name,
        plan_path=plan_path,
        bootstrap_servers=bootstrap_servers,
    ):
        # Producer: send PlanInput with key = plan_name
        producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            value_serializer=lambda v: v.SerializeToString() if v else None,
            acks="all",
        )
        await producer.start()
        try:
            plan_input = sample_plan_input_full()
            await producer.send_and_wait(
                topic=plan_input_topic,
                key=plan_name,
                value=plan_input,
            )
        finally:
            await producer.stop()

        # Consumer: poll plan-executions topic and verify output
        consumer = AIOKafkaConsumer(
            plan_execution_topic,
            bootstrap_servers=bootstrap_servers,
            group_id=f"it-{tenant_id}-assert",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            value_deserializer=lambda v: PlanExecution.FromString(v) if v else None,
        )
        await consumer.start()
        try:
            plan_execution = await _poll_for_plan_execution(
                consumer,
                expected_key=plan_name,
                timeout_seconds=10.0,
            )

            # Assertions
            assert plan_execution.header.name == plan_name, "header.name should equal plan_name"
            assert (
                plan_execution.header.status == ExecutionStatus.EXECUTION_STATUS_SUCCEEDED
            ), "PlanExecution should be marked as succeeded"
            assert plan_execution.result is not None, "PlanExecution should have a result"
            assert (
                plan_execution.result.error_message == ""
            ), "PlanExecution.result.error_message should be empty"

            # Header fields
            assert plan_execution.header.tenant_id == tenant_id, "header.tenant_id should match"
            assert plan_execution.header.exec_id, "header.exec_id should be set"
            # Validate exec_id is a UUID
            _ = uuid.UUID(plan_execution.header.exec_id)

            # Timestamp validation: parsable ISO8601 and recent
            assert plan_execution.header.created_at, "header.created_at should be set"
            created_at_dt = datetime.fromisoformat(plan_execution.header.created_at)
            now = datetime.now(created_at_dt.tzinfo) if created_at_dt.tzinfo else datetime.utcnow()
            assert now - timedelta(minutes=5) <= created_at_dt <= now + timedelta(minutes=1), (
                "header.created_at should be a recent timestamp"
            )

            # Result fields: compare all fields
            expected_result = PlanResult(
                upstream_tasks_results=[],
                next_task_names=["sample-task"],
                error_message="",
            )
            assert plan_execution.result == expected_result, "PlanExecution.result should match expected PlanResult"

            # Verify parent linkage propagated from input
            assert plan_execution.parent_task_exec_ids == ["1234f"], "parent_task_exec_ids should propagate from input"
            assert plan_execution.parent_task_names == ["previous_task_name"], "parent_task_names should propagate from input"
        finally:
            await consumer.stop()


