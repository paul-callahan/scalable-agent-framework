# Makefile for the Agentic Framework
# Provides common development tasks and build automation

.PHONY: help proto install test lint clean format check-deps

# Default target
help:
	@echo "Agentic Framework - Available targets:"
	@echo ""
	@echo "  proto      - Generate Python protobuf code from .proto files"
	@echo "  install    - Install Python dependencies"
	@echo "  test       - Run tests"
	@echo "  lint       - Run code quality checks"
	@echo "  format     - Format code with black and isort"
	@echo "  clean      - Remove generated files and caches"
	@echo "  check-deps - Check if all dependencies are installed"
	@echo "  build      - Build the Python package"
	@echo "  dev        - Install in development mode"
	@echo ""

# Generate Python protobuf code
proto:
	@echo "Generating protobuf files..."
	@./scripts/gen_proto.sh

# Install Python dependencies
install:
	@echo "Installing Python dependencies..."
	@cd services/standalone-py && pip install -e .

# Install development dependencies
install-dev: install
	@echo "Installing development dependencies..."
	@cd services/standalone-py && pip install -e ".[dev]"

# Run tests
test:
	@echo "Running tests..."
	@cd services/standalone-py && python -m pytest tests/ -v

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	@cd services/standalone-py && python -m pytest tests/ -v --cov=agentic --cov-report=html --cov-report=term

# Run linting checks
lint:
	@echo "Running linting checks..."
	@cd services/standalone-py && python -m flake8 agentic/ --max-line-length=88 --extend-ignore=E203,W503
	@cd services/standalone-py && python -m mypy agentic/ --ignore-missing-imports

# Format code
format:
	@echo "Formatting code with black..."
	@cd services/standalone-py && python -m black agentic/ --line-length=88
	@echo "Sorting imports with isort..."
	@cd services/standalone-py && python -m isort agentic/ --profile=black

# Check if dependencies are installed
check-deps:
	@echo "Checking dependencies..."
	@python3 -c "import grpc_tools.protoc" || (echo "grpcio-tools not installed. Run: pip install grpcio-tools" && exit 1)
	@python3 -c "import black" || (echo "black not installed. Run: pip install black" && exit 1)
	@python3 -c "import isort" || (echo "isort not installed. Run: pip install isort" && exit 1)
	@python3 -c "import flake8" || (echo "flake8 not installed. Run: pip install flake8" && exit 1)
	@python3 -c "import mypy" || (echo "mypy not installed. Run: pip install mypy" && exit 1)
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

# Build the Python package
build: proto
	@echo "Building Python package..."
	@cd services/standalone-py && python -m build

# Install in development mode
dev: install-dev proto
	@echo "Development environment setup complete!"

# Run data plane service
data-plane:
	@echo "Starting data plane service..."
	@cd services/standalone-py && python -m agentic.data_plane.server

# Run control plane service
control-plane:
	@echo "Starting control plane service..."
	@cd services/standalone-py && python -m agentic.control_plane.server

# Full development setup
setup: check-deps dev
	@echo "Development environment is ready!"

# Pre-commit checks
pre-commit: format lint test
	@echo "Pre-commit checks completed!"

# Show project structure
tree:
	@echo "Project structure:"
	@tree -I '__pycache__|*.pyc|*.egg-info|.git|.pytest_cache|htmlcov|build|dist' -a

# Show help for specific target
%:
	@echo "Target '$@' not found. Run 'make help' for available targets." 