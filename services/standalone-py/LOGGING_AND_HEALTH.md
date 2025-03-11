# Structured Logging and Health Checks

This document describes the structured logging and health check features added to the agentic framework.

## Overview

The agentic framework now includes comprehensive structured logging using `structlog` and health check endpoints for both gRPC and HTTP services. These features provide:

- **Structured Logging**: JSON-formatted logs with request/response tracking, error handling, and metrics
- **Health Checks**: HTTP endpoints for monitoring service health and readiness
- **Graceful Shutdown**: Proper cleanup and shutdown handling for both gRPC and HTTP servers
- **Metrics Collection**: Basic metrics tracking for monitoring and observability

## Structured Logging

### Configuration

The logging system is configured using the `configure_logging` function:

```python
from agentic.core.logging import configure_logging

# Configure logging with default settings
configure_logging()

# Configure with custom settings
configure_logging(
    log_level="INFO",
    log_format="json",  # or "console"
    include_timestamp=True,
    include_process_id=True,
    include_thread_id=True
)
```

### Usage

#### Basic Logging

```python
from agentic.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Service started", port=50051, service="data-plane")
logger.warning("High memory usage", memory_mb=1024)
logger.error("Database connection failed", error="timeout")
```

#### Request/Response Logging

Use the `log_request_response` context manager to automatically log request timing and metrics:

```python
from agentic.core.logging import log_request_response

with log_request_response(
    logger,
    "PutTaskExecution",
    request_id=request.header.id,
    tenant_id=request.header.tenant_id,
    task_type=request.task_type
):
    # Your service logic here
    result = process_request(request)
    return result
```

This will automatically log:
- Request start with context
- Request completion with duration
- Request errors with error details

#### Error Logging

Use `log_error` for structured error logging:

```python
from agentic.core.logging import log_error

try:
    # Your code here
    pass
except Exception as e:
    log_error(logger, e, 
             request_id="req-123",
             tenant_id="tenant-456",
             context={"operation": "database_query"})
```

#### Metrics Logging

Use `log_metric` to log metrics for monitoring:

```python
from agentic.core.logging import log_metric

log_metric(logger, "requests_per_second", 100.5, unit="req/s")
log_metric(logger, "memory_usage", 512.0, unit="MB", tags={"component": "cache"})
```

## Health Checks

### Health Service

The `HealthCheckService` provides health status tracking and metrics:

```python
from agentic.core.health import HealthCheckService

health_service = HealthCheckService(logger)

# Update metrics
health_service.update_metric("total_requests", 100)
health_service.update_metric("error_rate", 0.05)

# Set health status
health_service.set_health_status("healthy")  # or "degraded", "unhealthy"

# Get health info
health_info = health_service.get_health_info()
```

### HTTP Health Endpoints

Each service includes an HTTP health server with the following endpoints:

- `/health` - Overall health status
- `/health/ready` - Readiness check
- `/health/live` - Liveness check  
- `/metrics` - Service metrics
- `/` - Service information

#### Control Plane Service
- gRPC: Port 50052
- HTTP Health: Port 8080

#### Data Plane Service
- gRPC: Port 50051
- HTTP Health: Port 8081

### Example Health Check Responses

```json
{
  "status": "healthy",
  "uptime_seconds": 3600.5,
  "metrics": {
    "total_requests": 1000,
    "error_count": 5,
    "guardrail_violations": 2
  },
  "timestamp": 1640995200.0
}
```

## Graceful Shutdown

### Shutdown Handlers

Register cleanup functions to be called during shutdown:

```python
def cleanup_database():
    logger.info("Closing database connections")
    # Close connections, etc.

def cleanup_cache():
    logger.info("Clearing cache")
    # Clear cache, etc.

health_service.add_shutdown_handler(cleanup_database)
health_service.add_shutdown_handler(cleanup_cache)
```

### Signal Handling

The services automatically handle SIGINT and SIGTERM signals for graceful shutdown.

## Running the Services

### Control Plane Service

```bash
# Run with default settings
uv run python -m agentic.control_plane.server

# Run with custom settings
uv run python -m agentic.control_plane.server --port 50052 --log-level INFO
```

### Data Plane Service

```bash
# Run with default settings
uv run python -m agentic.data_plane.server

# Run with custom settings
uv run python -m agentic.data_plane.server --port 50051 --log-level INFO
```

### Demo Script

Run the logging and health check demo:

```bash
uv run python example_logging_demo.py
```

## Monitoring

### Health Check Endpoints

Check service health:

```bash
# Control plane health
curl http://localhost:8080/health

# Data plane health
curl http://localhost:8081/health

# Metrics
curl http://localhost:8080/metrics
```

### Log Analysis

The structured logs can be easily parsed and analyzed:

```bash
# View logs in JSON format
uv run python -m agentic.control_plane.server --log-level INFO | jq

# Filter logs by event type
uv run python -m agentic.control_plane.server | jq 'select(.event == "request_complete")'
```

## Configuration

### Environment Variables

You can configure logging and health checks using environment variables:

```bash
export AGENTIC_LOG_LEVEL=INFO
export AGENTIC_LOG_FORMAT=json
export AGENTIC_HEALTH_PORT=8080
```

### Log Levels

- `DEBUG`: Detailed debug information
- `INFO`: General information (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Log Formats

- `json`: JSON-structured logs (default)
- `console`: Human-readable console output

## Metrics

The services track various metrics automatically:

### Control Plane Metrics
- `total_requests`: Total number of requests processed
- `error_count`: Number of errors encountered
- `guardrail_violations`: Number of guardrail violations
- `routed_executions`: Number of executions routed
- `aborted_executions`: Number of executions aborted

### Data Plane Metrics
- `total_requests`: Total number of requests processed
- `error_count`: Number of errors encountered
- `task_executions_stored`: Number of task executions stored
- `plan_executions_stored`: Number of plan executions stored
- `result_size_bytes`: Size of stored results
- `confidence`: Confidence scores for plan executions

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 50051, 50052, 8080, and 8081 are available
2. **Import errors**: Run `./scripts/gen_proto.sh` to generate protobuf files
3. **Permission errors**: Ensure write permissions for log files and database

### Debug Mode

Enable debug logging for troubleshooting:

```bash
uv run python -m agentic.control_plane.server --log-level DEBUG
```

### Health Check Failures

If health checks fail:

1. Check service logs for errors
2. Verify database connectivity (data plane)
3. Check memory and resource usage
4. Verify all dependencies are installed

## Integration

### Kubernetes

The health check endpoints are compatible with Kubernetes probes:

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Prometheus

Metrics can be scraped by Prometheus from the `/metrics` endpoint.

### ELK Stack

Structured JSON logs can be easily ingested into Elasticsearch for analysis in Kibana. 