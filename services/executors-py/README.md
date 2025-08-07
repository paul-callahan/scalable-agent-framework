# Executors-py Microservice

A base framework for creating individual PlanExecutors and TaskExecutors in the scalable agent framework.

## Overview

The `executors-py` microservice is a base framework designed to execute user-supplied plan or task logic in response to Kafka messages. Unlike other services in the framework, this service has no web APIs - it operates purely as a Kafka consumer/producer.

The service can be configured to run as either:
- **PlanExecutor**: Consumes plan-inputs, executes plans, publishes plan-executions
- **TaskExecutor**: Consumes task-inputs, executes tasks, publishes task-executions

Configuration is single-mode: either plan parameters OR task parameters, not both.

## Architecture

- **Pure Kafka Service**: No FastAPI or web endpoints
- **Dynamic Plan/Task Loading**: Loads user-supplied `plan.py` or `task.py` files at runtime
- **Timeout Handling**: Configurable execution timeouts with proper error handling
- **Message Filtering**: Only processes messages matching the configured `plan_name` or `task_name`
- **Single-Mode Execution**: Configured for either PlanExecutor OR TaskExecutor, not both

## Configuration

The service is configured via environment variables for either PlanExecutor OR TaskExecutor mode:

### PlanExecutor Mode
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TENANT_ID` | Yes | - | Tenant identifier for topic names |
| `PLAN_NAME` | Yes | - | Plan name to filter messages |
| `PLAN_PATH` | Yes | - | Path to the user-supplied plan.py file |
| `PLAN_TIMEOUT` | No | 300 | Plan execution timeout in seconds |
| `KAFKA_BOOTSTRAP_SERVERS` | No | localhost:9092 | Kafka bootstrap servers |
| `KAFKA_GROUP_ID` | No | executors-{tenantId} | Kafka consumer group ID |

### TaskExecutor Mode
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TENANT_ID` | Yes | - | Tenant identifier for topic names |
| `TASK_NAME` | Yes | - | Task name to filter messages |
| `TASK_PATH` | Yes | - | Path to the user-supplied task.py file |
| `TASK_TIMEOUT` | No | 300 | Task execution timeout in seconds |
| `KAFKA_BOOTSTRAP_SERVERS` | No | localhost:9092 | Kafka bootstrap servers |
| `KAFKA_GROUP_ID` | No | executors-{tenantId} | Kafka consumer group ID |

**Note**: The service must be configured for exactly one mode. Providing both plan and task parameters will result in a configuration error.

## Kafka Topics

### PlanExecutor Mode
- **Input Topic**: `plan-inputs-{tenantId}`
- **Output Topic**: `plan-executions-{tenantId}`
- **Key**: `plan_name` (used for message filtering)

### TaskExecutor Mode
- **Input Topic**: `task-inputs-{tenantId}`
- **Output Topic**: `task-executions-{tenantId}`
- **Key**: `task_name` (used for message filtering)

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

## Task Interface

The service also consumes `TaskInput` protobuf messages for task execution. The protobuf structure is:

```protobuf
message TaskInput {
  string task_name = 1;                   // Name of the task to execute
  string tenant_id = 2;                   // Tenant identifier
  PlanExecution parent_plan_execution = 3; // Parent plan execution (optional)
  map<string, string> task_parameters = 4; // Task-specific parameters
}

message TaskResult {
  string data = 1;                        // Task-specific result data
  string error_message = 2;               // Error message if task failed
}
```

User-supplied `task.py` files must implement the following interface:

```python
def task(task_input: TaskInput) -> TaskResult:
    """
    Execute task logic.
    
    Args:
        task_input: TaskInput protobuf message containing:
            - task_name: str - Name of the task to execute
            - tenant_id: str - Tenant identifier
            - parent_plan_execution: PlanExecution - Parent plan execution (optional)
            - task_parameters: dict - Task-specific parameters
    
    Returns:
        TaskResult: Result containing:
            - data: str - Task-specific result data
            - error_message: str - Optional error message if task failed
    """
    # Your task logic here
    return TaskResult(
        data="task result data",  # Task-specific result
        error_message=""  # Only if task failed
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

## Example Task

```python
# /path/to/task.py
from agentic_common.pb import TaskInput, TaskResult

def task(task_input: TaskInput) -> TaskResult:
    """Example task that processes input parameters."""
    try:
        # Extract task parameters
        task_params = task_input.task_parameters or {}
        
        # Process based on task name
        if task_input.task_name == "data_processing_task":
            # Process data
            result_data = f"Processed data with params: {task_params}"
            return TaskResult(
                data=result_data,
                error_message=""
            )
        
        elif task_input.task_name == "validation_task":
            # Perform validation
            if task_params.get("validate", False):
                return TaskResult(
                    data="Validation passed",
                    error_message=""
                )
            else:
                return TaskResult(
                    data="",
                    error_message="Validation required but not enabled"
                )
        
        else:
            return TaskResult(
                data="",
                error_message=f"Unknown task: {task_input.task_name}"
            )
            
    except Exception as e:
        return TaskResult(
            data="",
            error_message=str(e)
        )
```

## Error Handling

The service handles various error scenarios:

- **Plan/Task Loading Errors**: Invalid plan.py/task.py files or missing plan/task functions
- **Execution Timeouts**: Configurable timeout with error reporting
- **Kafka Errors**: Connection issues, serialization errors
- **Plan/Task Execution Errors**: Exceptions in user plan/task logic
- **Configuration Errors**: Invalid single-mode configuration

All errors result in `PlanExecution`/`TaskExecution` messages with `success=False` and appropriate error messages.

## Health Checks

The service provides health check methods for monitoring:

- `ExecutorService.health_check()`: Overall service health
- `PlanInputConsumer.is_healthy()`: Plan consumer health (PlanExecutor mode)
- `PlanExecutionProducer.is_healthy()`: Plan producer health (PlanExecutor mode)
- `PlanExecutor.is_healthy()`: Plan executor health (PlanExecutor mode)
- `TaskInputConsumer.is_healthy()`: Task consumer health (TaskExecutor mode)
- `TaskExecutionProducer.is_healthy()`: Task producer health (TaskExecutor mode)
- `TaskExecutor.is_healthy()`: Task executor health (TaskExecutor mode)

## Integration

This service integrates with the broader framework:

1. **Control Plane**: Receives `PlanInput`/`TaskInput` messages from control plane
2. **Data Plane**: Results can be consumed by data plane services
3. **Graph Builder**: Plan.py and task.py files are created by the graph builder service

## Development

### Local Development

```bash
# Install dependencies
cd services/executors-py
uv sync

# Run as PlanExecutor
export TENANT_ID=test-tenant
export PLAN_NAME=test-plan
export PLAN_PATH=/path/to/plan.py
export PLAN_TIMEOUT=60

python main.py

# Run as TaskExecutor
export TENANT_ID=test-tenant
export TASK_NAME=test-task
export TASK_PATH=/path/to/task.py
export TASK_TIMEOUT=60

python main.py
```

### Testing

The service includes comprehensive tests using Mockafka-py for Kafka mocking:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=executors

# Run specific test categories
pytest tests/test_plan_flow.py
pytest tests/test_task_flow.py
pytest tests/test_service_integration.py
pytest tests/test_protobuf_utils.py
```

### Test Strategy

Tests use Mockafka-py to mock Kafka operations, allowing comprehensive testing without requiring a real Kafka cluster:

- **Unit Tests**: Test individual components (executors, producers, consumers)
- **Integration Tests**: Test complete message flows end-to-end
- **Error Handling**: Test timeout, error, and malformed message scenarios
- **Protobuf Tests**: Test message serialization/deserialization
- **Configuration Tests**: Test single-mode configuration validation

### Test Fixtures

The test suite includes fixtures for:
- Temporary plan.py and task.py files
- Sample protobuf messages
- Mockafka-py configuration
- Common test configuration

## Docker

The service is designed to run in Docker containers with:

- Plan.py or task.py files mounted as volumes
- Environment variables for configuration
- Health checks for container orchestration
- Support for either PlanExecutor or TaskExecutor mode

## Monitoring

Key metrics to monitor:

- Message processing rate
- Plan/Task execution times
- Error rates
- Kafka consumer lag
- Memory usage

## Troubleshooting

Common issues:

1. **Plan not loading**: Check `PLAN_PATH` and file permissions (PlanExecutor mode)
2. **Task not loading**: Check `TASK_PATH` and file permissions (TaskExecutor mode)
3. **Timeout errors**: Increase `PLAN_TIMEOUT`/`TASK_TIMEOUT` for long-running plans/tasks
4. **Kafka connection issues**: Verify `KAFKA_BOOTSTRAP_SERVERS`
5. **Message filtering**: Ensure `PLAN_NAME`/`TASK_NAME` matches message keys
6. **Configuration errors**: Ensure exactly one mode is configured (PlanExecutor OR TaskExecutor) 