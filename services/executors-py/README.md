# Executors-py Microservice

A pure Kafka consumer/producer service for plan execution in the scalable agent framework.

## Overview

The `executors-py` microservice is designed to execute user-supplied plan logic in response to Kafka messages. Unlike other services in the framework, this service has no web APIs - it operates purely as a Kafka consumer/producer.

## Architecture

- **Pure Kafka Service**: No FastAPI or web endpoints
- **Dynamic Plan Loading**: Loads user-supplied `plan.py` files at runtime
- **Timeout Handling**: Configurable execution timeouts with proper error handling
- **Message Filtering**: Only processes messages matching the configured `plan_name`

## Configuration

The service is configured via environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TENANT_ID` | Yes | - | Tenant identifier for topic names |
| `PLAN_NAME` | Yes | - | Plan name to filter messages |
| `PLAN_PATH` | Yes | - | Path to the user-supplied plan.py file |
| `PLAN_TIMEOUT` | No | 300 | Plan execution timeout in seconds |
| `KAFKA_BOOTSTRAP_SERVERS` | No | localhost:9092 | Kafka bootstrap servers |
| `KAFKA_GROUP_ID` | No | executors-{tenantId} | Kafka consumer group ID |

## Kafka Topics

### Input Topic
- **Name**: `plan-inputs-{tenantId}`
- **Key**: `plan_name` (used for message filtering)
- **Value**: `PlanInput` protobuf message

### Output Topic  
- **Name**: `plan-executions-{tenantId}`
- **Key**: `plan_name`
- **Value**: `PlanExecution` protobuf message

## Plan Interface

The service consumes `PlanInput` protobuf messages that contain task execution data. The protobuf structure is:

```protobuf
message PlanInput {
  string input_id = 1;                    // Unique identifier for this input
  string plan_name = 2;                   // Name of the plan to execute
  repeated TaskExecution task_executions = 3; // Task executions that provide input
}

message TaskExecution {
  ExecutionHeader header = 1;             // Common execution metadata
  string parent_plan_exec_id = 2;         // Parent plan execution ID
  TaskResult result = 3;                  // Task-specific result data
  string parent_plan_name = 4;            // Parent plan name
}

message ExecutionHeader {
  string name = 1;                        // Task/Plan name
  string exec_id = 2;                     // Execution ID
  string tenant_id = 5;                   // Tenant identifier
  // ... other metadata fields
}
```

User-supplied `plan.py` files must implement the following interface:

```python
def plan(plan_input: PlanInput) -> PlanResult:
    """
    Execute plan logic.
    
    Args:
        plan_input: PlanInput protobuf message containing:
            - input_id: str - Unique identifier for this input
            - plan_name: str - Name of the plan to execute
            - task_executions: list - List of TaskExecution protobuf messages
    
    Returns:
        PlanResult: Result containing:
            - upstream_tasks_results: list - TaskResult objects that led to this plan decision
            - next_task_names: list - Names of the next tasks to execute
            - error_message: str - Optional error message if planning failed
    """
    # Your plan logic here
    return PlanResult(
        upstream_tasks_results=[],  # List of TaskResult objects
        next_task_names=["task1", "task2"],  # Names of next tasks to execute
        error_message=""  # Only if planning failed
    )
```

## Example Plan

```python
# /path/to/plan.py
from agentic_common.pb import PlanInput, PlanResult, TaskResult

def plan(plan_input: PlanInput) -> PlanResult:
    """Example plan that processes task execution data."""
    try:
        # Extract task executions
        task_executions = plan_input.task_executions
        
        if not task_executions:
            return PlanResult(
                error_message="No task executions provided"
            )
        
        # Process the first task execution result
        first_task = task_executions[0]
        task_name = first_task.header.name if first_task.header else "unknown"
        task_result = first_task.result
        
        # Check for task errors
        if task_result and task_result.error_message:
            return PlanResult(
                error_message=f"Task {task_name} failed: {task_result.error_message}"
            )
        
        # Create TaskResult objects for upstream tasks
        upstream_results = []
        for task_exec in task_executions:
            if task_exec.result:
                upstream_results.append(task_exec.result)
        
        # Determine next tasks to execute based on plan logic
        next_tasks = ["next_task_1", "next_task_2"]
        
        return PlanResult(
            upstream_tasks_results=upstream_results,
            next_task_names=next_tasks,
            error_message=""
        )
    except Exception as e:
        return PlanResult(
            error_message=str(e)
        )
```

## Error Handling

The service handles various error scenarios:

- **Plan Loading Errors**: Invalid plan.py files or missing plan function
- **Execution Timeouts**: Configurable timeout with error reporting
- **Kafka Errors**: Connection issues, serialization errors
- **Plan Execution Errors**: Exceptions in user plan logic

All errors result in `PlanExecution` messages with `success=False` and appropriate error messages.

## Health Checks

The service provides health check methods for monitoring:

- `PlanExecutorService.health_check()`: Overall service health
- `PlanInputConsumer.is_healthy()`: Consumer health
- `PlanExecutionProducer.is_healthy()`: Producer health
- `PlanExecutor.is_healthy()`: Plan executor health

## Integration

This service integrates with the broader framework:

1. **Control Plane**: Receives `PlanInput` messages from control plane
2. **Data Plane**: Results can be consumed by data plane services
3. **Graph Builder**: Plan.py files are created by the graph builder service

## Development

### Local Development

```bash
# Install dependencies
cd services/executors-py
uv sync

# Run with environment variables
export TENANT_ID=test-tenant
export PLAN_NAME=test-plan
export PLAN_PATH=/path/to/plan.py
export PLAN_TIMEOUT=60

python main.py
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=executors
```

## Docker

The service is designed to run in Docker containers with:

- Plan.py files mounted as volumes
- Environment variables for configuration
- Health checks for container orchestration

## Monitoring

Key metrics to monitor:

- Message processing rate
- Plan execution times
- Error rates
- Kafka consumer lag
- Memory usage

## Troubleshooting

Common issues:

1. **Plan not loading**: Check `PLAN_PATH` and file permissions
2. **Timeout errors**: Increase `PLAN_TIMEOUT` for long-running plans
3. **Kafka connection issues**: Verify `KAFKA_BOOTSTRAP_SERVERS`
4. **Message filtering**: Ensure `PLAN_NAME` matches message keys 