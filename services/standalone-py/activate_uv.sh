#!/bin/bash

# Script to activate the uv virtual environment for the agentic framework
# Usage: source activate_uv.sh

# Add uv to PATH if not already there
if ! command -v uv &> /dev/null; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    return 1
fi

# Sync dependencies if needed
echo "Syncing dependencies with uv..."
uv sync

echo "Virtual environment is ready!"
echo "Use 'uv run python <script>' to run Python scripts"
echo "Use 'uv run <command>' to run any command in the virtual environment"
echo ""
echo "Examples:"
echo "  uv run python test_graph_validation.py"
echo "  uv run python -c 'from agentic import Task, Plan'"
echo "  uv run ./scripts/gen_proto.sh" 