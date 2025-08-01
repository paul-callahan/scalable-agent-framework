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

# Post-process generated Python files to fix import statements
post_process_imports() {
    print_status "Post-processing generated Python files to fix import statements..."
    
    cd "$(dirname "$0")/.."
    
    # List of generated files to process
    generated_files=(
        "common_pb2.py"
        "common_pb2_grpc.py"
        "task_pb2.py"
        "task_pb2_grpc.py"
        "plan_pb2.py"
        "plan_pb2_grpc.py"
        "services_pb2.py"
        "services_pb2_grpc.py"
    )
    
    for file in "${generated_files[@]}"; do
        if [ -f "$OUTPUT_DIR/$file" ]; then
            print_status "Processing imports in: $file"
            
            # Process the file to fix import statements
            # This handles cases where protoc generates imports that need to be relative to the pb package
            if [ -z "$UV_CMD" ]; then
                python3 -c "
import re
import sys

def fix_imports(content):
    # Fix import statements to use relative imports within the pb package
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Fix import statements for our generated protobuf modules
        # Convert 'import common_pb2 as common__pb2' to 'from . import common_pb2 as common__pb2'
        if 'import ' in line and '_pb2' in line and not line.strip().startswith('from .'):
            # Handle imports like 'import common_pb2 as common__pb2'
            if re.match(r'^import (\w+_pb2)', line.strip()):
                line = re.sub(r'^import (\w+_pb2)', r'from . import \1', line)
            # Handle imports like 'from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2'
            elif 'from google.protobuf import' in line and '_pb2' in line:
                # Keep google protobuf imports as they are
                pass
            # Handle other protobuf imports
            elif '_pb2' in line and not line.strip().startswith('from google'):
                line = re.sub(r'^import (\w+_pb2)', r'from . import \1', line)
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

# Read the file
with open('$OUTPUT_DIR/$file', 'r') as f:
    content = f.read()

# Fix the imports
fixed_content = fix_imports(content)

# Write back to the file
with open('$OUTPUT_DIR/$file', 'w') as f:
    f.write(fixed_content)
"
            else
                $UV_CMD python -c "
import re
import sys

def fix_imports(content):
    # Fix import statements to use relative imports within the pb package
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Fix import statements for our generated protobuf modules
        # Convert 'import common_pb2 as common__pb2' to 'from . import common_pb2 as common__pb2'
        if 'import ' in line and '_pb2' in line and not line.strip().startswith('from .'):
            # Handle imports like 'import common_pb2 as common__pb2'
            if re.match(r'^import (\w+_pb2)', line.strip()):
                line = re.sub(r'^import (\w+_pb2)', r'from . import \1', line)
            # Handle imports like 'from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2'
            elif 'from google.protobuf import' in line and '_pb2' in line:
                # Keep google protobuf imports as they are
                pass
            # Handle other protobuf imports
            elif '_pb2' in line and not line.strip().startswith('from google'):
                line = re.sub(r'^import (\w+_pb2)', r'from . import \1', line)
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

# Read the file
with open('$OUTPUT_DIR/$file', 'r') as f:
    content = f.read()

# Fix the imports
fixed_content = fix_imports(content)

# Write back to the file
with open('$OUTPUT_DIR/$file', 'w') as f:
    f.write(fixed_content)
"
            fi
            
            if [ $? -eq 0 ]; then
                print_status "✓ Fixed imports in: $file"
            else
                print_warning "⚠ Could not process imports in: $file"
            fi
        else
            print_warning "⚠ File not found for post-processing: $file"
        fi
    done
}

# Verify generated files
verify_generated_files() {
    print_status "Verifying generated files..."
    
    expected_files=(
        "common_pb2.py"
        "common_pb2_grpc.py"
        "task_pb2.py"
        "task_pb2_grpc.py"
        "plan_pb2.py"
        "plan_pb2_grpc.py"
        "services_pb2.py"
        "services_pb2_grpc.py"
    )
    
    for file in "${expected_files[@]}"; do
        if [ -f "$OUTPUT_DIR/$file" ]; then
            print_status "✓ Generated: $file"
        else
            print_error "✗ Missing: $file"
            exit 1
        fi
    done
}

# Create __init__.py if it doesn't exist
create_init_file() {
    if [ ! -f "$OUTPUT_DIR/__init__.py" ]; then
        print_status "Creating __init__.py file"
        touch "$OUTPUT_DIR/__init__.py"
    fi
}

# Main execution
main() {
    print_status "Starting protobuf generation..."
    
    check_dependencies
    create_output_dir
    generate_proto
    post_process_imports
    verify_generated_files
    create_init_file
    
    print_status "Protobuf generation completed successfully!"
    print_status "Generated files are in: $OUTPUT_DIR"
}

# Run main function
main "$@" 
