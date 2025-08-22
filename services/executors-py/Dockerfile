# Base image for Python executors (plan/task). Child images can override CMD/ENV as needed.

FROM python:3.13-slim

# Build-time parameters (baked as defaults into the image ENV)
ARG TENANT_ID=""
ARG EXECUTOR_NAME=""
ARG EXECUTOR_TIMEOUT="300"
ARG AGENT_GRAPH_ID=""

ENV TENANT_ID=${TENANT_ID} \
    EXECUTOR_NAME=${EXECUTOR_NAME} \
    EXECUTOR_TIMEOUT=${EXECUTOR_TIMEOUT} \
    AGENT_GRAPH_ID=${AGENT_GRAPH_ID} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/services/executors-py

WORKDIR /app

# Install build essentials for Python C extensions (aiokafka) and tooling
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       zlib1g-dev \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv grpcio-tools

# Copy sources
COPY protos ./protos
COPY services/common-py ./services/common-py
COPY services/executors-py ./services/executors-py

# Generate Python protobufs into the common-py package
RUN python -m grpc_tools.protoc \
    --python_out=services/common-py/agentic_common/pb \
    --proto_path=protos \
    common.proto

# Install python packages into system environment
RUN uv pip install --system ./services/common-py \
    && uv pip install --system ./services/executors-py

# Default working dir where main.py resides; child images may override
WORKDIR /app/services/executors-py

# Default command; child images may override and set EXECUTOR_MODE at runtime
CMD ["python", "main.py"]


