#!/bin/bash

# Generate Python protobuf code from .proto files
# This script generates both *_pb2.py and *_pb2_grpc.py files

set -e  # Exit on any error

# Configuration
PROTO_DIR="protos"
OUTPUT_DIR="services/standalone-py/agentic/pb"
PYTHON_PATH="services/standalone-py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if uv is available and use it for dependency management
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check if uv is available
    if command -v uv &> /dev/null; then
        print_status "Using uv for dependency management..."
        # Use uv run to execute commands in the project's virtual environment
        UV_CMD="uv run"
        
        # Check if virtual environment exists
        if [ ! -d ".venv" ]; then
            print_error "Virtual environment not found. Please run: uv sync"
            exit 1
        fi
        
        # Check Python version in virtual environment
        PYTHON_VERSION=$(uv run python --version 2>&1 | grep -o 'Python [0-9]\+\.[0-9]\+\.[0-9]\+' | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
        print_status "Using Python version: $PYTHON_VERSION"
        
    else
        print_warning "uv not found, falling back to system Python..."
        UV_CMD=""
    fi
    
    # Check if grpcio-tools is available
    if [ -z "$UV_CMD" ]; then
        if ! python3 -c "import grpc_tools.protoc" &> /dev/null; then
            print_error "grpcio-tools is not installed. Please install with: pip3 install grpcio-tools"
            exit 1
        fi
    else
        if ! $UV_CMD python -c "import grpc_tools.protoc" &> /dev/null; then
            print_error "grpcio-tools is not installed. Please run: uv sync"
            exit 1
        fi
    fi
    
    print_status "Dependencies check passed"
}

# Create output directory if it doesn't exist
create_output_dir() {
    print_status "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
}

# Generate protobuf files
generate_proto() {
    print_status "Generating Python protobuf files..."
    
    # Change to the project root directory
    cd "$(dirname "$0")/.."
    
    # Generate files for each .proto file
    for proto_file in "$PROTO_DIR"/*.proto; do
        if [ -f "$proto_file" ]; then
            print_status "Processing: $proto_file"
            
            # Generate the protobuf files using --proto_path="protos" to correctly resolve relative imports
            if [ -z "$UV_CMD" ]; then
                python3 -m grpc_tools.protoc \
                    --python_out="$OUTPUT_DIR" \
                    --grpc_python_out="$OUTPUT_DIR" \
                    --proto_path="$PROTO_DIR" \
                    "$(basename "$proto_file")"
            else
                $UV_CMD python -m grpc_tools.protoc \
                    --python_out="$OUTPUT_DIR" \
                    --grpc_python_out="$OUTPUT_DIR" \
                    --proto_path="$PROTO_DIR" \
                    "$(basename "$proto_file")"
            fi
            
            if [ $? -eq 0 ]; then
                print_status "Generated files for: $(basename "$proto_file")"
            else
                print_error "Failed to generate files for: $(basename "$proto_file")"
                exit 1
            fi
        fi
    done
}

# Create proper package structure for io_arl.proto.model
create_package_structure() {
    print_status "Creating package structure for io_arl.proto.model..."
    
    cd "$(dirname "$0")/.."
    
    # Create the package directory structure
    mkdir -p "$OUTPUT_DIR/io_arl/proto/model"
    
    # Move generated files to the correct package location
    for file in common_pb2.py common_pb2_grpc.py task_pb2.py task_pb2_grpc.py plan_pb2.py plan_pb2_grpc.py; do
        if [ -f "$OUTPUT_DIR/$file" ]; then
            print_status "Moving $file to package structure..."
            mv "$OUTPUT_DIR/$file" "$OUTPUT_DIR/io_arl/proto/model/"
        fi
    done
    
    # Create __init__.py files for the package structure
    cat > "$OUTPUT_DIR/io_arl/__init__.py" << 'EOF'
# Package initialization for io_arl
EOF
    
    cat > "$OUTPUT_DIR/io_arl/proto/__init__.py" << 'EOF'
# Package initialization for proto
EOF
    
    cat > "$OUTPUT_DIR/io_arl/proto/model/__init__.py" << 'EOF'
# Package initialization for model
# Import all generated protobuf modules
from . import common_pb2
from . import common_pb2_grpc
from . import task_pb2
from . import task_pb2_grpc
from . import plan_pb2
from . import plan_pb2_grpc

# Re-export commonly used classes for easier imports
from .common_pb2 import *
from .task_pb2 import *
from .plan_pb2 import *
EOF
    
    # Update the main pb __init__.py to import from the new package structure
    cat > "$OUTPUT_DIR/__init__.py" << 'EOF'
# Import from the new package structure
from .io_arl.proto.model import *
from .io_arl.proto.model import common_pb2, common_pb2_grpc
from .io_arl.proto.model import task_pb2, task_pb2_grpc
from .io_arl.proto.model import plan_pb2, plan_pb2_grpc

# Re-export for backward compatibility
__all__ = [
    'common_pb2', 'common_pb2_grpc',
    'task_pb2', 'task_pb2_grpc',
    'plan_pb2', 'plan_pb2_grpc'
]
EOF
}

# Verify generated files
verify_generated_files() {
    print_status "Verifying generated files..."
    
    expected_files=(
        "io_arl/proto/model/common_pb2.py"
        "io_arl/proto/model/common_pb2_grpc.py"
        "io_arl/proto/model/task_pb2.py"
        "io_arl/proto/model/task_pb2_grpc.py"
        "io_arl/proto/model/plan_pb2.py"
        "io_arl/proto/model/plan_pb2_grpc.py"
    )
    
    for file in "${expected_files[@]}"; do
        if [ -f "$OUTPUT_DIR/$file" ]; then
            print_status "✓ Generated: $file"
        else
            print_error "✗ Missing: $file"
            exit 1
        fi
    done
    
    # Verify package structure
    package_files=(
        "io_arl/__init__.py"
        "io_arl/proto/__init__.py"
        "io_arl/proto/model/__init__.py"
    )
    
    for file in "${package_files[@]}"; do
        if [ -f "$OUTPUT_DIR/$file" ]; then
            print_status "✓ Package file: $file"
        else
            print_error "✗ Missing package file: $file"
            exit 1
        fi
    done
}

# Main execution
main() {
    print_status "Starting protobuf generation..."
    
    check_dependencies
    create_output_dir
    generate_proto
    create_package_structure
    verify_generated_files
    
    print_status "Protobuf generation completed successfully!"
    print_status "Generated files are in: $OUTPUT_DIR"
    print_status "Package structure: $OUTPUT_DIR/io_arl/proto/model/"
}

# Run main function
main "$@" 
