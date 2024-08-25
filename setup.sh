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

# Install dependencies using uv (this will create a virtual environment automatically)
echo "Installing dependencies with uv..."
uv sync

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
echo "./scripts/gen_proto.sh" 