# Makefile for the Agentic Framework
# Provides common development tasks and build automation

.PHONY: help proto install test lint clean format check-deps sync update-deps

# Default target
help:
	@echo "Agentic Framework - Available targets:"
	@echo ""
	@echo "  proto      - Generate Python protobuf code from .proto files"
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

# Generate Python protobuf code
proto:
	@echo "Generating protobuf files..."
	@./scripts/gen_proto.sh

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

# Show help for specific target
%:
	@echo "Target '$@' not found. Run 'make help' for available targets." 