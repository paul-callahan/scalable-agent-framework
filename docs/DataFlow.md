# Data Flow Documentation

This document describes the message flow and data architecture of the Scalable Agent Framework, which consists of three main microservices: Control Plane, Data Plane, and Executor.

## Architecture Overview

The framework follows a microservices architecture with event-driven communication using Apache Kafka as the message broker. Each service has specific responsibilities and communicates through well-defined message patterns.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Control Plane│    │  Data Plane  │    │   Executor   │
│              │    │              │    │              │
│ • Guardrails │    │ • Persistence│    │ • Task Exec  │
│ • Routing    │    │ • State Mgmt │    │ • Plan Exec  │
│ • Policies   │    │ • Metadata   │    │ • Registry   │
└──────────────┘    └──────────────┘    └──────────────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                    ┌────────▼────────┐
                    │     Kafka       │
                    │   Message Bus   │
                    └─────────────────┘
```

## Service Responsibilities

### Control Plane
- **Guardrails**: Enforces policies and constraints on agent behavior
- **Routing**: Determines which tasks/plans should be executed
- **Policy Management**: Loads and applies execution policies
- **Request Validation**: Validates incoming requests against policies

### Data Plane
- **Persistence**: Stores task results, plan states, and metadata
- **State Management**: Maintains execution state and history
- **Metadata Storage**: Stores task/plan definitions and configurations
- **Data Retrieval**: Provides APIs for querying execution data

### Executor
- **Task Execution**: Executes individual tasks based on registered implementations
- **Plan Execution**: Orchestrates plan execution and task sequencing
- **Registry Management**: Maintains registry of available tasks and plans
- **Result Processing**: Processes and forwards execution results

## Message Flow

### 1. Initial Request Flow

```
Client Request → Control Plane → Policy Check → Route to Executor
```

1. **Client Request**: External client sends request to Control Plane
2. **Policy Validation**: Control Plane validates request against policies
3. **Routing Decision**: Control Plane determines appropriate executor
4. **Task/Plan Selection**: Control Plane selects appropriate task or plan

### 2. Task Execution Flow

```
Control Plane → Kafka → Executor → Task Execution → Result → Kafka → Data Plane
```

1. **Task Message**: Control Plane publishes task message to Kafka
2. **Executor Consumption**: Executor consumes task message
3. **Task Execution**: Executor executes registered task implementation
4. **Result Publication**: Executor publishes result to Kafka
5. **Data Persistence**: Data Plane consumes and stores result

### 3. Plan Execution Flow

```
Control Plane → Kafka → Executor → Plan Execution → Task Sequence → Results → Kafka → Data Plane
```

1. **Plan Message**: Control Plane publishes plan message to Kafka
2. **Executor Consumption**: Executor consumes plan message
3. **Plan Execution**: Executor executes plan and determines next tasks
4. **Task Sequencing**: Executor publishes subsequent task messages
5. **Result Aggregation**: Results are aggregated and stored

### 4. State Management Flow

```
Data Plane ← Kafka ← State Updates ← All Services
```

1. **State Updates**: All services publish state changes to Kafka
2. **Data Plane Consumption**: Data Plane consumes state updates
3. **Persistence**: Data Plane stores state in PostgreSQL
4. **Query Interface**: Data Plane provides APIs for state queries

## Kafka Topics

### Input Topics
- `task-requests`: Task execution requests from Control Plane
- `plan-requests`: Plan execution requests from Control Plane
- `state-updates`: State change notifications from all services

### Output Topics
- `task-results`: Task execution results from Executor
- `plan-results`: Plan execution results from Executor
- `execution-events`: General execution events and logs

## Message Formats

### Task Request Message
```json
{
  "task_id": "unique-task-id",
  "task_type": "example_task",
  "parameters": {
    "input_data": "example input"
  },
  "metadata": {
    "request_id": "client-request-id",
    "timestamp": "2024-01-01T00:00:00Z",
    "priority": "normal"
  }
}
```

### Task Result Message
```json
{
  "task_id": "unique-task-id",
  "result": {
    "data": {
      "output": "task result data"
    },
    "mime_type": "application/json",
    "size_bytes": 1024
  },
  "status": "completed",
  "metadata": {
    "execution_time_ms": 150,
    "timestamp": "2024-01-01T00:00:01Z"
  }
}
```

### Plan Request Message
```json
{
  "plan_id": "unique-plan-id",
  "plan_type": "example_plan",
  "context": {
    "previous_results": [],
    "current_state": "initial"
  },
  "metadata": {
    "request_id": "client-request-id",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Plan Result Message
```json
{
  "plan_id": "unique-plan-id",
  "result": {
    "next_task_ids": ["task-1", "task-2"],
    "metadata": {
      "plan_type": "example",
      "confidence": 0.9
    }
  },
  "status": "completed",
  "metadata": {
    "execution_time_ms": 300,
    "timestamp": "2024-01-01T00:00:01Z"
  }
}
```

## Error Handling

### Retry Mechanisms
- **Kafka Consumer**: Automatic retry with exponential backoff
- **Task Execution**: Configurable retry policies per task type
- **Plan Execution**: Graceful degradation for failed tasks

### Dead Letter Queues
- **Failed Messages**: Unprocessable messages sent to DLQ
- **Monitoring**: DLQ monitoring for system health
- **Recovery**: Manual reprocessing of DLQ messages

### Circuit Breakers
- **Service Health**: Health checks for all services
- **Graceful Degradation**: Fallback mechanisms for failed services
- **Monitoring**: Real-time health monitoring and alerting

## Performance Considerations

### Scalability
- **Horizontal Scaling**: Each service can be scaled independently
- **Partitioning**: Kafka topics can be partitioned for parallel processing
- **Load Balancing**: Multiple executor instances for task distribution

### Latency
- **Async Processing**: Non-blocking message processing
- **Connection Pooling**: Efficient database and Kafka connections
- **Caching**: Result caching for frequently accessed data

### Throughput
- **Batch Processing**: Batch operations for high-volume scenarios
- **Message Batching**: Kafka producer batching for efficiency
- **Database Optimization**: Indexed queries and connection pooling

## Monitoring and Observability

### Metrics
- **Message Throughput**: Messages per second per topic
- **Execution Latency**: Task and plan execution times
- **Error Rates**: Failed executions and retry counts
- **Resource Usage**: CPU, memory, and disk usage

### Logging
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Request Tracing**: End-to-end request tracing
- **Audit Trail**: Complete execution audit trail

### Health Checks
- **Service Health**: HTTP health endpoints for all services
- **Kafka Connectivity**: Kafka producer/consumer health
- **Database Connectivity**: Database connection health

## Security Considerations

### Authentication
- **Service-to-Service**: Mutual TLS for inter-service communication
- **API Authentication**: JWT tokens for external API access
- **Kafka Security**: SASL/SSL for Kafka authentication

### Authorization
- **Policy Enforcement**: Fine-grained access control policies
- **Resource Isolation**: Service-level resource isolation
- **Audit Logging**: Comprehensive audit trail

### Data Protection
- **Encryption**: Data encryption at rest and in transit
- **PII Handling**: Proper handling of personally identifiable information
- **Data Retention**: Configurable data retention policies

## Development and Testing

### Local Development
- **Docker Compose**: Complete local environment setup
- **Hot Reloading**: Development mode with code hot reloading
- **Debugging**: Integrated debugging support

### Testing
- **Unit Tests**: Comprehensive unit test coverage
- **Integration Tests**: End-to-end integration testing
- **Load Testing**: Performance and scalability testing

### Deployment
- **CI/CD**: Automated build and deployment pipelines
- **Environment Management**: Separate environments for dev/staging/prod
- **Rollback**: Automated rollback capabilities 