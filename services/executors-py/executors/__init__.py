"""
Executors package for the executors-py microservice.

This package provides a base framework for creating individual PlanExecutors and TaskExecutors.
"""

from .plan_kafka_consumer import PlanInputConsumer
from .plan_kafka_producer import PlanExecutionProducer
from .plan_executor import PlanExecutor
from .task_kafka_consumer import TaskInputConsumer
from .task_kafka_producer import TaskExecutionProducer
from .task_executor import TaskExecutor
from .service import ExecutorService

__all__ = [
    "ExecutorService",
    "PlanExecutor", 
    "PlanInputConsumer",
    "PlanExecutionProducer",
    "TaskExecutor",
    "TaskInputConsumer", 
    "TaskExecutionProducer",
]

__version__ = "0.1.0" 