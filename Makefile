# Makefile for the Agentic Framework
# Provides common development tasks and build automation

# Python configuration
PYTHON := /opt/homebrew/bin/python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# Python version check function
define check_python_version
	@$(PYTHON) -c "import sys; assert sys.version_info >= (3, 13, 5), f'Python 3.13.5+ required, got {sys.version}'" || (echo "Python 3.13.5+ required. Please install Python 3.13.5 or later." && exit 1)
endef

# Create virtual environment function
define create_venv
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
	fi
endef

.PHONY: help proto install test lint clean format check-deps sync update-deps microservices-build microservices-up microservices-down microservices-logs microservices-test

# Default target
help:
	@echo "Agentic Framework - Available targets:"
	@echo ""
	@echo "  proto      - Generate Python protobuf code from .proto files"
	@echo "  gen-proto-py - Generate Python protobuf files for common-py"
	@echo "  deps-common-py - Install dependencies for common-py"
	@echo "  deps-executors-py - Install dependencies for executors-py"
	@echo "  test-executor-py - Run executors-py tests (depends on gen-proto-py and deps)"
	@echo "  install    - Install Python dependencies using uv"
	@echo "  install-dev - Install development dependencies using uv"
	@echo "  sync       - Sync dependencies with uv"
	@echo "  update-deps - Update all dependencies to latest versions"
	@echo "  test       - Run tests using uv"
	@echo "  lint       - Run code quality checks using uv"
	@echo "  format     - Format code with black and isort using uv"
	@echo "  clean      - Remove generated files and caches"
	@echo "  check-deps - Check if all dependencies are installed"
	@echo "  build      - Build the Python package using uv"
	@echo "  dev        - Install in development mode using uv"
	@echo ""
	@echo "Microservice targets (Python):"
	@echo "  microservices-build - Build all Docker images for microservices"
	@echo "  microservices-up    - Start microservices with docker-compose"
	@echo "  microservices-down  - Stop and clean up microservices"
	@echo "  microservices-logs  - View logs from all microservices"
	@echo "  microservices-test  - Run integration tests for microservices"
	@echo ""
	@echo "Java Microservice targets:"
	@echo "  java-build          - Build all Java microservice Docker images using Maven"
	@echo "  java-up             - Start Java microservices with docker-compose"
	@echo "  java-down           - Stop and clean up Java microservices"
	@echo "  java-logs           - View logs from all Java microservices"
	@echo "  java-test           - Run integration tests for Java microservices"
	@echo "  java-proto          - Generate Java protobuf classes using Maven"
	@echo "  java-clean          - Clean Maven builds"
	@echo ""

# Generate Python protobuf code
proto:
	@echo "Generating protobuf files..."
	@./scripts/gen_proto.sh

# Generate Python protobuf code for common-py
gen-proto-py: deps-common-py
	@echo "Generating Python protobuf files for common-py..."
	$(call check_python_version)
	$(call create_venv)
	@cd services/common-py && $(VENV_PYTHON) -m grpc_tools.protoc --python_out=agentic_common/pb --grpc_python_out=agentic_common/pb --proto_path=../../protos ../../protos/*.proto

# Install dependencies for common-py
deps-common-py:
	@echo "Installing dependencies for common-py..."
	$(call check_python_version)
	$(call create_venv)
	@$(VENV_PIP) install --upgrade pip
	@$(VENV_PIP) install grpcio grpcio-tools protobuf

# Install dependencies for executors-py
deps-executors-py: deps-common-py
	@echo "Installing dependencies for executors-py..."
	$(call check_python_version)
	$(call create_venv)
	@$(VENV_PIP) install pytest pytest-asyncio mockafka-py aiokafka structlog
	@echo "Installing common-py package in editable mode..."
	@cd services/common-py && ../../$(VENV_PIP) install -e .

# Run executors-py tests
test-executor-py: gen-proto-py deps-executors-py
	@echo "Running executors-py tests..."
	$(call check_python_version)
	$(call create_venv)
	@cd services/executors-py && PYTHONPATH=../common-py/agentic_common/pb:$$PYTHONPATH ../../$(VENV_PYTHON) -m pytest tests/ -v

# Install Python dependencies using uv
install:
	@echo "Installing Python dependencies with uv..."
	@uv sync

# Install development dependencies using uv
install-dev: install
	@echo "Installing development dependencies with uv..."
	@cd services/standalone-py && uv add --dev pytest pytest-asyncio pytest-cov pytest-mock black isort flake8 mypy pre-commit

# Sync dependencies with uv
sync:
	@echo "Syncing dependencies with uv..."
	@uv sync

# Update all dependencies to latest versions
update-deps:
	@echo "Updating all dependencies to latest versions..."
	@uv add --upgrade grpcio grpcio-tools protobuf pydantic aiohttp structlog asyncio-mqtt aiofiles click
	@uv add --dev --upgrade pytest pytest-asyncio pytest-cov pytest-mock black isort flake8 mypy pre-commit
	@uv add --group docs --upgrade sphinx sphinx-rtd-theme myst-parser

# Run tests using uv
test:
	@echo "Running tests with uv..."
	@cd services/standalone-py && uv run python -m pytest tests/ -v

# Run tests with coverage using uv
test-cov:
	@echo "Running tests with coverage using uv..."
	@cd services/standalone-py && uv run python -m pytest tests/ -v --cov=agentic --cov-report=html --cov-report=term

# Run linting checks using uv
lint:
	@echo "Running linting checks with uv..."
	@cd services/standalone-py && uv run python -m flake8 agentic/ --max-line-length=88 --extend-ignore=E203,W503
	@cd services/standalone-py && uv run python -m mypy agentic/ --ignore-missing-imports

# Format code using uv
format:
	@echo "Formatting code with black using uv..."
	@cd services/standalone-py && uv run python -m black agentic/ --line-length=88
	@echo "Sorting imports with isort using uv..."
	@cd services/standalone-py && uv run python -m isort agentic/ --profile=black

# Check if dependencies are installed using uv
check-deps:
	@echo "Checking dependencies with uv..."
	@uv run python -c "import grpc_tools.protoc" || (echo "grpcio-tools not installed. Run: uv sync" && exit 1)
	@uv run python -c "import black" || (echo "black not installed. Run: uv add --dev black" && exit 1)
	@uv run python -c "import isort" || (echo "isort not installed. Run: uv add --dev isort" && exit 1)
	@uv run python -c "import flake8" || (echo "flake8 not installed. Run: uv add --dev flake8" && exit 1)
	@uv run python -c "import mypy" || (echo "mypy not installed. Run: uv add --dev mypy" && exit 1)
	@echo "All dependencies are installed!"

# Clean generated files and caches
clean:
	@echo "Cleaning generated files and caches..."
	@rm -rf services/standalone-py/agentic/pb/*.py
	@rm -rf services/standalone-py/agentic/pb/__pycache__
	@rm -rf services/standalone-py/agentic/__pycache__
	@rm -rf services/standalone-py/agentic/*/__pycache__
	@rm -rf services/standalone-py/agentic/*/*/__pycache__
	@rm -rf services/standalone-py/.pytest_cache
	@rm -rf services/standalone-py/htmlcov
	@rm -rf services/standalone-py/.coverage
	@rm -rf services/standalone-py/build
	@rm -rf services/standalone-py/dist
	@rm -rf services/standalone-py/*.egg-info
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup completed!"

# Build the Python package using uv
build: proto
	@echo "Building Python package with uv..."
	@cd services/standalone-py && uv run python -m build

# Install in development mode using uv
dev: install-dev proto
	@echo "Development environment setup complete!"

# Run data plane service using uv
data-plane:
	@echo "Starting data plane service with uv..."
	@cd services/standalone-py && uv run python -m agentic.data_plane.server

# Run control plane service using uv
control-plane:
	@echo "Starting control plane service with uv..."
	@cd services/standalone-py && uv run python -m agentic.control_plane.server

# Full development setup using uv
setup: check-deps dev
	@echo "Development environment is ready!"

# Pre-commit checks using uv
pre-commit: format lint test
	@echo "Pre-commit checks completed!"

# Show project structure
tree:
	@echo "Project structure:"
	@tree -I '__pycache__|*.pyc|*.egg-info|.git|.pytest_cache|htmlcov|build|dist' -a

# Microservice targets

# Build all Docker images for microservices (Python)
microservices-build:
	@echo "Building all microservice Docker images..."
	@./scripts/build_microservices.sh

# Start microservices with docker-compose (Python)
microservices-up:
	@echo "Starting microservices with docker-compose..."
	@docker-compose up -d

# Stop and clean up microservices (Python)
microservices-down:
	@echo "Stopping and cleaning up microservices..."
	@docker-compose down -v --remove-orphans

# View logs from all microservices (Python)
microservices-logs:
	@echo "Viewing logs from all microservices..."
	@docker-compose logs -f

# Run integration tests for microservices (Python)
microservices-test:
	@echo "Running integration tests for microservices..."
	@echo "Starting microservices for testing..."
	@docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 30
	@echo "Running health checks..."
	@curl -f http://localhost:8001/health || (echo "Control plane health check failed" && exit 1)
	@curl -f http://localhost:8002/health || (echo "Data plane health check failed" && exit 1)
	@curl -f http://localhost:8003/health || (echo "Executor health check failed" && exit 1)
	@echo "All microservices are healthy!"
	@echo "Cleaning up test environment..."
	@docker-compose down
	@echo "Integration tests completed successfully!"

# Java Microservice targets

# Build all Java microservice Docker images using Maven
java-build:
	@echo "Building all Java microservice Docker images..."
	@./scripts/build_java_microservices.sh --all

# Start Java microservices with docker-compose
java-up:
	@echo "Starting Java microservices with docker-compose..."
	@docker-compose -f docker-compose-java.yml up -d

# Stop and clean up Java microservices
java-down:
	@echo "Stopping and cleaning up Java microservices..."
	@docker-compose -f docker-compose-java.yml down -v --remove-orphans

# View logs from all Java microservices
java-logs:
	@echo "Viewing logs from all Java microservices..."
	@docker-compose -f docker-compose-java.yml logs -f

# Run integration tests for Java microservices
java-test:
	@echo "Running integration tests for Java microservices..."
	@echo "Starting Java microservices for testing..."
	@docker-compose -f docker-compose-java.yml up -d
	@echo "Waiting for services to be ready..."
	@sleep 60
	@echo "Running health checks..."
	@curl -f http://localhost:8081/actuator/health || (echo "Data plane health check failed" && exit 1)
	@curl -f http://localhost:8082/actuator/health || (echo "Control plane health check failed" && exit 1)
	@curl -f http://localhost:8083/actuator/health || (echo "Task executor health check failed" && exit 1)
	@curl -f http://localhost:8084/actuator/health || (echo "Plan executor health check failed" && exit 1)
	@echo "All Java microservices are healthy!"
	@echo "Cleaning up test environment..."
	@docker-compose -f docker-compose-java.yml down
	@echo "Java integration tests completed successfully!"

# Generate Java protobuf classes using Maven
java-proto:
	@echo "Generating Java protobuf classes..."
	@./scripts/build_java_microservices.sh --protobuf

# Clean Maven builds
java-clean:
	@echo "Cleaning Maven builds..."
	@./scripts/build_java_microservices.sh --clean

# Show help for specific target
%:
	@echo "Target '$@' not found. Run 'make help' for available targets." 