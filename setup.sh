#!/bin/bash

# Setup script for the scalable-agent-framework project

set -e

echo "Setting up project with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Then add uv to your PATH:"
    echo "source scripts/activate_uv.sh"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(uv run python --version 2>&1 | grep -o 'Python [0-9]\+\.[0-9]\+\.[0-9]\+' | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
if [[ "$PYTHON_VERSION" != "3.13.5" ]]; then
    echo "Warning: Expected Python 3.13.5, found $PYTHON_VERSION"
    echo "The project is configured for Python 3.13.5"
fi

# Check if .venv directory exists
if [ ! -d ".venv" ]; then
    echo "Creating .venv directory..."
    mkdir -p .venv
fi

# Install dependencies using uv (this will use the project's .venv directory)
echo "Installing dependencies with uv..."
uv sync

# Verify installation
echo "Verifying installation..."
uv run python -c "import grpcio; print(f'grpcio version: {grpcio.__version__}')"
uv run python -c "import protobuf; print(f'protobuf version: {protobuf.__version__}')"
uv run python -c "import pydantic; print(f'pydantic version: {pydantic.__version__}')"
uv run python -c "import aiohttp; print(f'aiohttp version: {aiohttp.__version__}')"
uv run python -c "import structlog; print(f'structlog version: {structlog.__version__}')"

echo "Setup complete!"
echo ""
echo "To run commands in the virtual environment, use:"
echo "  uv run python <script>"
echo "  uv run -m <module>"
echo ""
echo "To activate the virtual environment for interactive use:"
echo "  source .venv/bin/activate"
echo ""
echo "To generate protobuf files, run:"
echo "  ./scripts/gen_proto.sh"
echo ""
echo "To update dependencies to latest versions:"
echo "  make update-deps"
echo ""
echo "To sync dependencies:"
echo "  make sync" 