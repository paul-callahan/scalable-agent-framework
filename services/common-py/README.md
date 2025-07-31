# Agentic Common Package

This package provides common utilities and protobuf definitions for agentic microservices.

## Protobuf Usage

The common package provides centralized access to protobuf definitions used across the agentic framework. There are two ways to use the protobuf definitions:

### Option 1: Use the Agentic Package (Recommended)

The common package can import protobuf definitions from the main agentic package. This is the recommended approach as it ensures consistency across all services.

```python
from agentic_common.pb import (
    ExecutionHeader,
    TaskExecution,
    TaskResult,
    PlanExecution,
    PlanResult,
    DataPlaneServiceServicer,
    DataPlaneServiceStub,
    ControlPlaneServiceServicer,
    ControlPlaneServiceStub,
)
```

### Option 2: Generate Local Protobuf Files

If you prefer to generate protobuf files locally (for example, if you want to modify the protobuf definitions), you can use the provided script:

```bash
# Navigate to the common package directory
cd services/common-py

# Generate protobuf files locally
./scripts/gen_proto.sh
```

This will generate the protobuf files in `agentic_common/pb/` and the imports will automatically use the local files.

## Installation

```bash
# Install the package with uv
uv add agentic-common

# Or install in development mode
uv sync
```

## Dependencies

The package requires:
- `grpcio==1.74.0`
- `grpcio-tools==1.74.0` (for protobuf generation)
- `protobuf==6.31.1`
- `aiokafka==0.11.0`
- `fastapi==0.111.0`
- `uvicorn[standard]==0.30.1`
- `structlog==24.1.0`
- `pydantic==2.7.3`
- `agentic` (the main agentic package)

## Development

To set up the development environment:

```bash
cd services/common-py
uv sync
```

To run tests:

```bash
uv run pytest
```

## Protobuf Generation

The protobuf generation script (`scripts/gen_proto.sh`) will:

1. Check for required dependencies (grpcio-tools)
2. Generate Python protobuf files from the `.proto` files in the root `protos/` directory
3. Post-process the generated files to fix import statements
4. Verify that all expected files were generated

The script supports both `uv` and system Python environments. 