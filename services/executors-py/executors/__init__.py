"""
Executors package for the executors-py microservice.

This package provides a pure Kafka consumer/producer service for plan execution.
"""

from .plan_kafka_consumer import PlanInputConsumer
from .plan_kafka_producer import PlanExecutionProducer
from .plan_executor import PlanExecutor
from .service import PlanExecutorService

__all__ = [
    "PlanExecutorService",
    "PlanExecutor", 
    "PlanInputConsumer",
    "PlanExecutionProducer",
]

__version__ = "0.1.0" 