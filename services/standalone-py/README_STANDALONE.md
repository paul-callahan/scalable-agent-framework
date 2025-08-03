# Standalone Agentic Framework

This directory contains the standalone Python implementation of the Agentic Framework that uses an in-memory message broker instead of gRPC for inter-service communication.

## Overview

The standalone implementation replaces gRPC services with an in-memory message broker using `asyncio.Queue` objects while preserving protobuf serialization for all messages. This provides a lightweight, single-process alternative to the microservices architecture.

## Architecture

### Components

1. **InMemoryBroker** (`agentic/message_bus/broker.py`)
   - Manages topic-based message routing using `asyncio.Queue` objects
   - Supports wildcard subscriptions (e.g., `persisted-task-executions_*`)
   - Handles protobuf serialization boundaries
   - Provides metrics and graceful shutdown

2. **DataPlaneService** (`agentic/data_plane/service.py`)
   - Consumes from `task-executions_{tenantId}` and `plan-executions_{tenantId}` queues
   - Persists TaskExecution and PlanExecution messages to SQLite database
   - Forwards lightweight reference messages to control queues
   - Provides async message processing with error handling

3. **ControlPlaneService** (`agentic/control_plane/service.py`)
   - Consumes from `persisted-task-executions_{tenantId}` and `plan-control_{tenantId}` queues
   - Evaluates guardrails (rate limiting, content filtering, etc.)
   - Routes approved executions to result queues
   - Publishes rejection messages with reasons for failed guardrails

4. **TaskExecutorService** (`agentic/executors/task_executor.py`)
   - Consumes from `task-results_{tenantId}` queues
   - Executes registered tasks based on task type
   - Publishes completed TaskExecution results to execution queues
   - Supports task registry for custom task implementations

5. **PlanExecutorService** (`agentic/executors/plan_executor.py`)
   - Consumes from `plan-results_{tenantId}` queues
   - Executes registered plans based on plan type
   - Publishes completed PlanExecution results to execution queues
   - Supports plan registry for custom plan implementations

### Message Flow

```
Task Execution Flow:
1. TaskExecutor publishes TaskExecution to task-executions_{tenantId}
2. DataPlane consumes, persists, forwards to persisted-task-executions_{tenantId}
3. ControlPlane evaluates guardrails, publishes to task-results_{tenantId}
4. TaskExecutor consumes result, executes task, publishes back to task-executions_{tenantId}

Plan Execution Flow:
1. PlanExecutor publishes PlanExecution to plan-executions_{tenantId}
2. DataPlane consumes, persists, forwards to plan-control_{tenantId}
3. ControlPlane evaluates guardrails, publishes to plan-results_{tenantId}
4. PlanExecutor consumes result, executes plan, publishes back to plan-executions_{tenantId}
```

## Usage

### Running Individual Services

```bash
# Data Plane Service
agentic-data-plane --port 8081 --log-level INFO --db-path agentic_data.db --tenant-id default

# Control Plane Service
agentic-control-plane --port 8082 --log-level INFO --tenant-id default
```

### Running Complete Standalone System

```bash
# Run both services in a single process
agentic-standalone --port 8080 --log-level INFO --db-path agentic_data.db --tenant-id default
```

### Programmatic Usage

```python
import asyncio
from agentic import (
    InMemoryBroker, 
    DataPlaneService, 
    ControlPlaneService,
    TaskExecutorService,
    PlanExecutorService
)

async def main():
    # Create shared broker
    broker = InMemoryBroker()
    
    # Create services
    data_plane = DataPlaneService(broker=broker, db_path="agentic_data.db")
    control_plane = ControlPlaneService(broker=broker)
    task_executor = TaskExecutorService(broker=broker)
    plan_executor = PlanExecutorService(broker=broker)
    
    # Register custom tasks and plans
    def my_task_handler(parameters):
        return {"result": "Task completed", "status": "success"}
    
    def my_plan_handler(parameters, input_task_id):
        return {
            "next_task_ids": ["next_task_1", "next_task_2"],
            "metadata": {"input_task_id": input_task_id},
            "confidence": 0.8
        }
    
    task_executor.register_task("my_task", my_task_handler)
    plan_executor.register_plan("my_plan", my_plan_handler)
    
    # Start services
    tenant_id = "my_tenant"
    await asyncio.gather(
        data_plane.start(tenant_id=tenant_id),
        control_plane.start(tenant_id=tenant_id),
        task_executor.start(tenant_id=tenant_id),
        plan_executor.start(tenant_id=tenant_id)
    )
    
    # ... your application logic ...
    
    # Stop services
    await asyncio.gather(
        data_plane.stop(),
        control_plane.stop(),
        task_executor.stop(),
        plan_executor.stop()
    )
    await broker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

Run the integration test to verify the complete message flow:

```bash
cd services/standalone-py
python test_standalone_integration.py
```

## Configuration

### Guardrails

The ControlPlaneService supports various guardrail types:

- **Rate Limiting**: Limit requests per time window
- **Content Filtering**: Block messages containing specific keywords
- **Resource Usage**: Monitor memory and CPU usage
- **Tenant Quotas**: Limit executions per tenant

Example guardrail configuration:

```python
control_plane.add_guardrail("tenant1", {
    'type': 'rate_limit',
    'enabled': True,
    'blocking': True,
    'max_requests': 100,
    'window_seconds': 60
})

control_plane.add_guardrail("tenant1", {
    'type': 'content_filter',
    'enabled': True,
    'blocking': True,
    'blocked_keywords': ['malicious', 'harmful']
})
```

### Health Checks

All services include health check endpoints:

- Data Plane: `http://localhost:8081/health`
- Control Plane: `http://localhost:8082/health`
- Standalone: `http://localhost:8080/health`

## Migration from gRPC

The standalone implementation maintains the same protobuf message formats as the microservices version, making it easy to migrate between architectures:

1. **Message Format**: All messages use the same protobuf serialization
2. **Service Interfaces**: Services maintain similar APIs and behavior
3. **Database Schema**: SQLite schema is compatible with the microservices version
4. **Configuration**: Guardrails and routing rules work the same way

## Benefits

- **Simplicity**: Single process deployment
- **Performance**: No network overhead for inter-service communication
- **Debugging**: Easier to trace message flow and debug issues
- **Development**: Faster iteration and testing
- **Resource Usage**: Lower memory and CPU overhead

## Limitations

- **Scalability**: Limited to single process (no horizontal scaling)
- **Fault Isolation**: Service failures affect the entire system
- **Deployment**: Cannot deploy services independently
- **Monitoring**: Less granular monitoring compared to microservices

## Dependencies

The standalone implementation removes gRPC dependencies while keeping protobuf for message serialization:

- ✅ `protobuf==6.31.1` - Message serialization
- ❌ `grpcio==1.74.0` - Removed (no longer needed)
- ❌ `grpcio-tools==1.74.0` - Removed (no longer needed)

All other dependencies remain the same as the microservices version. 