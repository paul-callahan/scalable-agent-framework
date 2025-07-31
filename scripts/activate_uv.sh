#!/bin/bash

# Helper script to activate uv in the current shell
# Run this script with: source scripts/activate_uv.sh

export PATH="$HOME/.local/bin:$PATH"
echo "uv added to PATH. You can now use:"
echo "  uv --version"
echo "  ./setup.sh"
echo "  ./scripts/gen_proto.sh"
echo ""
echo "To run commands in the virtual environment, use:"
echo "  uv run python <script>"
echo "  uv run -m <module>"
echo ""
echo "To activate the virtual environment for interactive use:"
echo "  source .venv/bin/activate" 