# Use Python 3.13 slim base image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install uv

# Create non-root user
RUN groupadd -r agentic && useradd -r -g agentic agentic

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY . .

# Install the package in editable mode
RUN uv pip install -e .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && chown -R agentic:agentic /app

# Switch to non-root user
USER agentic

# Expose port for health checks and API
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command - run the standalone service
CMD ["uv", "run", "python", "-m", "agentic.standalone_main"] 