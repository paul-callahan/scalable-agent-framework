# Makefile for the Agentic Framework
# Provides common development tasks and build automation
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
# Python configuration
PYTHON := /opt/homebrew/bin/python3
VENV := $(ROOT_DIR)/.venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
UV_PROJECT_ENVIRONMENT := $(VENV)

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

.PHONY: help proto install test lint clean format check-deps sync update-deps microservices-build microservices-up microservices-down microservices-logs microservices-test common-java-clean admin-java-clean common-java-build admin-java-build graph_composer-clean graph_composer-build graph-builder-clean graph-builder-build control_plane-java-clean control_plane-java-build data_plane-java-clean data_plane-java-build admin-docker-up admin-docker-logs graph-builder-docker-up graph-builder-docker-logs control-plane-docker-up control-plane-docker-logs data-plane-docker-up data-plane-docker-logs graph-composer-docker-up graph-composer-docker-logs frontend-build frontend-clean frontend-logs frontend-docker-up

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
	@echo "  gen-proto-java      - Generate Java protobuf classes using Maven"
	@echo "  java-clean          - Clean Maven builds"
	@echo ""
	@echo "Java Module Service targets:"
	@echo "  common-java-clean              - Clean common-java module with Maven"
	@echo "  common-java-build              - Build common-java module with Maven"
	@echo "  admin-java-clean               - Clean admin-java module with Maven"
	@echo "  admin-java-build               - Build admin-java module with Maven"
	@echo "  graph_composer-clean           - Clean graph_composer module with Maven"
	@echo "  graph_composer-build           - Build graph_composer module with Maven"
	@echo "  graph-builder-clean            - Clean graph-builder module with Maven"
	@echo "  graph-builder-build            - Build graph-builder module with Maven"
	@echo "  control_plane-java-clean       - Clean control_plane-java module with Maven"
	@echo "  control_plane-java-build       - Build control_plane-java module with Maven"
	@echo "  data_plane-java-clean          - Clean data_plane-java module with Maven"
	@echo "  data_plane-java-build          - Build data_plane-java module with Maven"
	@echo ""
	@echo "Java Service Deployment Pipelines:"
	@echo "  admin-docker-up         - Complete pipeline: clean, build, and deploy admin service"
	@echo "  admin-docker-logs       - View admin service logs"
	@echo "  graph-builder-docker-up - Complete pipeline: clean, build, and deploy graph_builder service"
	@echo "  graph-builder-docker-logs - View graph_builder service logs"
	@echo "  control-plane-docker-up - Complete pipeline: clean, build, and deploy control_plane service"
	@echo "  control-plane-docker-logs - View control_plane service logs"
	@echo "  data-plane-docker-up    - Complete pipeline: clean, build, and deploy data_plane service"
	@echo "  data-plane-docker-logs  - View data_plane service logs"
	@echo "  graph-composer-docker-up - Complete pipeline: clean, build, and deploy graph_composer service"
	@echo "  graph-composer-docker-logs - View graph_composer service logs"
	@echo ""
	@echo "Frontend Development targets:"
	@echo "  frontend-build                  - Build frontend production bundle"
	@echo "  frontend-clean                  - Clean frontend build artifacts"
	@echo "  frontend-logs                   - View frontend development server logs"
	@echo "  frontend-docker-up              - Clean, build, and restart frontend development server"
	@echo ""

# keep
gen-proto-py: deps-common-py
	@echo "Generating Python protobuf files for common-py..."
	$(call check_python_version)
	$(call create_venv)
	@cd services/common-py && ./scripts/gen_proto.sh

# Install dependencies for common-py
# keep
deps-common-py:
	@echo "Installing dependencies for common-py..."
	$(call check_python_version)
	$(call create_venv)
	@cd services/common-py && UV_PROJECT_ENVIRONMENT=$(UV_PROJECT_ENVIRONMENT) uv sync

# Install dependencies for common-py
# keep
deps-executors-py: deps-common-py
	@echo "Installing dependencies for common-py..."
	$(call check_python_version)
	$(call create_venv)
	@cd services/executors-py && UV_PROJECT_ENVIRONMENT=$(UV_PROJECT_ENVIRONMENT) uv sync

# Run executors-py tests
# keep
test-executors-py: gen-proto-py deps-executors-py
	@echo "Running executors-py tests..."
	$(call check_python_version)
	$(call create_venv)
	@cd services/executors-py && $(VENV_PYTHON) -m pytest tests/ -v

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
	$(call create_venv)
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
gen-proto-java:
	@echo "Generating Java protobuf classes..."
	@./scripts/build_java_microservices.sh --protobuf

# Clean Maven builds
java-clean:
	@echo "Cleaning Maven builds..."
	@mvn clean

# Individual Maven clean targets for common-java and admin-java
common-java-clean:
	@echo "Cleaning common-java with Maven..."
	@cd services/common-java && mvn clean

# Individual Maven build targets for common-java and admin-java
common-java-build:
	@echo "Building common-java with Maven..."
	@cd services/common-java && mvn package -DskipTests

admin-java-clean:
	@echo "Cleaning admin-java with Maven..."
	@cd services/admin-java && mvn clean	

admin-java-build:
	@echo "Building admin-java with Maven..."
	@cd services/admin-java && mvn package -DskipTests

# Individual Maven targets for graph_composer
graph_composer-clean:
	@echo "Cleaning graph_composer with Maven..."
	@cd services/graph_composer && mvn clean

graph_composer-build:
	@echo "Building graph_composer with Maven..."
	@cd services/graph_composer && mvn package -DskipTests

# Individual Maven targets for graph-builder
graph-builder-clean:
	@echo "Cleaning graph-builder with Maven..."
	@cd services/graph-builder && mvn clean

graph-builder-build:
	@echo "Building graph-builder with Maven..."
	@cd services/graph-builder && mvn package -DskipTests

# Individual Maven targets for control_plane-java
control_plane-java-clean:
	@echo "Cleaning control_plane-java with Maven..."
	@cd services/control_plane-java && mvn clean

control_plane-java-build:
	@echo "Building control_plane-java with Maven..."
	@cd services/control_plane-java && mvn package -DskipTests

# Individual Maven targets for data_plane-java
data_plane-java-clean:
	@echo "Cleaning data_plane-java with Maven..."
	@cd services/data_plane-java && mvn clean

data_plane-java-build:
	@echo "Building data_plane-java with Maven..."
	@cd services/data_plane-java && mvn package -DskipTests

# Complete admin-java clean, build, and deploy pipeline
admin-docker-up: common-java-clean admin-java-clean common-java-build admin-java-build
	@echo "Stopping admin service with docker-compose..."
	@docker-compose stop admin || true
	@echo "Removing admin service image..."
	@docker rmi scalable-agent-framework_admin || true
	@docker rmi admin || true
	@echo "Building admin service with docker-compose..."
	@docker-compose build --no-cache admin
	@echo "Starting admin service with docker-compose..."
	@docker-compose up -d admin
	@echo "Admin-java clean, build, and deploy pipeline completed successfully!"

admin-docker-logs:
	@echo "Viewing admin service logs..."
	@docker-compose logs -f admin

# Complete graph-builder clean, build, and deploy pipeline
graph-builder-docker-up: common-java-clean graph-builder-clean common-java-build graph-builder-build
	@echo "Stopping graph-builder service with docker-compose..."
	@docker-compose stop graph-builder || true
	@echo "Removing graph-builder service image..."
	@docker rmi scalable-agent-framework_graph-builder || true
	@docker rmi graph-builder || true
	@echo "Building graph-builder service with docker-compose..."
	@docker-compose build --no-cache graph-builder
	@echo "Starting graph-builder service with docker-compose..."
	@docker-compose up -d graph-builder
	@echo "Graph-builder clean, build, and deploy pipeline completed successfully!"

graph-builder-docker-logs:
	@echo "Viewing graph-builder service logs..."
	@docker-compose logs -f graph-builder

# Complete control_plane-java clean, build, and deploy pipeline
control-plane-docker-up: common-java-clean control_plane-java-clean common-java-build control_plane-java-build
	@echo "Stopping control_plane-java service with docker-compose..."
	@docker-compose stop control_plane-java || true
	@echo "Removing control_plane-java service image..."
	@docker rmi scalable-agent-framework_control_plane-java || true
	@docker rmi control_plane-java || true
	@echo "Building control_plane-java service with docker-compose..."
	@docker-compose build --no-cache control_plane-java
	@echo "Starting control_plane-java service with docker-compose..."
	@docker-compose up -d control_plane-java
	@echo "Control_plane-java clean, build, and deploy pipeline completed successfully!"

control-plane-docker-logs:
	@echo "Viewing control_plane-java service logs..."
	@docker-compose logs -f control_plane-java

# Complete data_plane-java clean, build, and deploy pipeline
data-plane-docker-up: common-java-clean data_plane-java-clean common-java-build data_plane-java-build
	@echo "Stopping data_plane-java service with docker-compose..."
	@docker-compose stop data_plane-java || true
	@echo "Removing data_plane-java service image..."
	@docker rmi scalable-agent-framework_data_plane-java || true
	@docker rmi data_plane-java || true
	@echo "Building data_plane-java service with docker-compose..."
	@docker-compose build --no-cache data_plane-java
	@echo "Starting data_plane-java service with docker-compose..."
	@docker-compose up -d data_plane-java
	@echo "Data_plane-java clean, build, and deploy pipeline completed successfully!"

data-plane-docker-logs:
	@echo "Viewing data_plane-java service logs..."
	@docker-compose logs -f data_plane-java

# Complete graph_composer clean, build, and deploy pipeline
graph-composer-docker-up: common-java-clean graph_composer-clean common-java-build graph_composer-build
	@echo "Stopping graph_composer service with docker-compose..."
	@docker-compose stop graph-composer || true
	@echo "Removing graph-composer service image..."
	@docker rmi scalable-agent-framework_graph-composer || true
	@docker rmi graph-composer || true
	@echo "Building graph-composer service with docker-compose..."
	@docker-compose build --no-cache graph-composer
	@echo "Starting graph-composer service with docker-compose..."
	@docker-compose up -d graph-composer
	@echo "Graph_composer clean, build, and deploy pipeline completed successfully!"

graph-composer-docker-logs:
	@echo "Viewing graph-composer service logs..."
	@docker-compose logs -f graph-composer

# Frontend Development targets
frontend-build:
	@echo "Building frontend..."
	@cd services/frontend && npm run build
	@echo "Frontend build completed successfully!"

frontend-clean:
	@echo "Cleaning frontend build artifacts..."
	@cd services/frontend && npm run clean
	@echo "Frontend cleaned successfully!"


frontend-logs:
	@echo "Viewing frontend development server logs..."
	@docker-compose logs -f frontend

frontend-docker-up: frontend-clean frontend-build
	@echo "Rebuilding and restarting frontend development server..."
	@docker-compose stop frontend || true
	@docker-compose rm -f frontend || true
	@docker-compose build --no-cache frontend
	@docker-compose up -d frontend
	@echo "Frontend development server rebuilt and restarted successfully!"

# Show help for specific target
%:
	@echo "Target '$@' not found. Run 'make help' for available targets." 