#!/bin/bash

# Generate Python protobuf code from .proto files for the common package
# This script generates both *_pb2.py and *_pb2_grpc.py files

set -e  # Exit on any error

# Configuration
MODULE_DIR=$(dirname "$0")/..
MODULE_DIR=$(realpath "$MODULE_DIR")
PROJECT_DIR=$(realpath "$MODULE_DIR/../..")
PROTO_DIR="${PROJECT_DIR}/protos"
echo "PROTO_DIR: $PROTO_DIR"

MODULE_PYTHON=${PROJECT_DIR}/.venv/bin/python

PYTHON_PATH="."
OUTPUT_DIR="agentic_common/pb"

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

# Create output directory if it doesn't exist
create_output_dir() {
    print_status "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
}

# Generate protobuf files
generate_proto() {
    print_status "Generating Python protobuf files..."

    # Change to the common package directory
    cd ${MODULE_DIR}

    # Generate files for each .proto file
    for proto_file in "$PROTO_DIR"/*.proto; do
        if [ -f "$proto_file" ]; then
            print_status "Processing: $proto_file while in: $(pwd)"
            echo "python -m grpc_tools.protoc --python_out=${OUTPUT_DIR} --proto_path=${PROTO_DIR} $(basename $proto_file)"
            # Generate the protobuf files using --proto_path="protos" to correctly resolve relative imports
            ${MODULE_PYTHON} -m grpc_tools.protoc \
                --python_out="$OUTPUT_DIR" \
               --proto_path="$PROTO_DIR" \
                "$(basename "$proto_file")"
            if [ $? -eq 0 ]; then
                print_status "Generated files for: $(basename "$proto_file")"
            else
                print_error "Failed to generate files for: $(basename "$proto_file")"
                exit 1
            fi
        fi
    done
}

# Verify generated files
verify_generated_files() {
    print_status "Verifying generated files..."

    expected_files=(

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

# Cleanup function to deactivate virtual environment
cleanup() {
    print_status "Cleanup complete"
}

# Main execution
main() {
    print_status "Starting protobuf generation for common package..."
    create_output_dir
    generate_proto
    verify_generated_files
    create_init_file
    cleanup
    print_status "Protobuf generation completed successfully!"
    print_status "Generated files are in: $OUTPUT_DIR"
}

# Run main function
main "$@" 