#!/bin/bash

# Build script for all microservices in the Scalable Agent Framework
# This script builds Docker images for all microservices and provides
# helpful output and error handling.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICES_DIR="$PROJECT_ROOT/services"

# Service configurations
declare -A SERVICES=(
    ["control-plane"]="control-plane-py"
    ["data-plane"]="data-plane-py"
    ["executor"]="executor-py"
)

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_status $RED "Error: Docker is not running or not accessible"
        exit 1
    fi
    print_status $GREEN "Docker is running"
}

# Function to check if service directory exists
check_service_directory() {
    local service_name=$1
    local service_path=$2
    
    if [[ ! -d "$service_path" ]]; then
        print_status $RED "Error: Service directory not found: $service_path"
        return 1
    fi
    
    if [[ ! -f "$service_path/Dockerfile" ]]; then
        print_status $RED "Error: Dockerfile not found in: $service_path"
        return 1
    fi
    
    print_status $GREEN "Found service: $service_name"
    return 0
}

# Function to build a single service
build_service() {
    local service_name=$1
    local service_path=$2
    
    print_status $BLUE "Building $service_name..."
    
    # Change to service directory
    cd "$service_path"
    
    # Build the Docker image
    local image_name="agentic-$service_name"
    local tag="latest"
    
    if docker build -t "$image_name:$tag" .; then
        print_status $GREEN "Successfully built $service_name"
        
        # Show image info
        local image_size=$(docker images "$image_name:$tag" --format "table {{.Size}}" | tail -n 1)
        print_status $BLUE "Image: $image_name:$tag ($image_size)"
    else
        print_status $RED "Failed to build $service_name"
        return 1
    fi
    
    # Return to project root
    cd "$PROJECT_ROOT"
}

# Function to build all services
build_all_services() {
    print_status $BLUE "Building all microservices..."
    
    local failed_services=()
    local successful_services=()
    
    for service_name in "${!SERVICES[@]}"; do
        local service_path="$SERVICES_DIR/${SERVICES[$service_name]}"
        
        if check_service_directory "$service_name" "$service_path"; then
            if build_service "$service_name" "$service_path"; then
                successful_services+=("$service_name")
            else
                failed_services+=("$service_name")
            fi
        else
            failed_services+=("$service_name")
        fi
    done
    
    # Print summary
    echo
    print_status $BLUE "=== Build Summary ==="
    
    if [[ ${#successful_services[@]} -gt 0 ]]; then
        print_status $GREEN "Successfully built: ${successful_services[*]}"
    fi
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        print_status $RED "Failed to build: ${failed_services[*]}"
        return 1
    fi
    
    print_status $GREEN "All services built successfully!"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -s, --service  Build specific service (control-plane|data-plane|executor)"
    echo "  -p, --push     Push images to registry after building"
    echo "  -c, --clean    Clean up old images before building"
    echo
    echo "Examples:"
    echo "  $0                    # Build all services"
    echo "  $0 -s control-plane   # Build only control-plane service"
    echo "  $0 -c                 # Clean and build all services"
}

# Function to clean old images
clean_images() {
    print_status $YELLOW "Cleaning old agentic images..."
    
    # Remove old agentic images
    docker images | grep "agentic-" | awk '{print $3}' | xargs -r docker rmi -f
    
    print_status $GREEN "Cleanup completed"
}

# Function to push images (placeholder for future implementation)
push_images() {
    print_status $YELLOW "Push functionality not yet implemented"
    print_status $YELLOW "Images are built locally and ready for use"
}

# Main script
main() {
    local build_specific_service=""
    local should_push=false
    local should_clean=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -s|--service)
                build_specific_service="$2"
                shift 2
                ;;
            -p|--push)
                should_push=true
                shift
                ;;
            -c|--clean)
                should_clean=true
                shift
                ;;
            *)
                print_status $RED "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Check Docker
    check_docker
    
    # Clean if requested
    if [[ "$should_clean" == true ]]; then
        clean_images
    fi
    
    # Build services
    if [[ -n "$build_specific_service" ]]; then
        # Build specific service
        if [[ -n "${SERVICES[$build_specific_service]}" ]]; then
            local service_path="$SERVICES_DIR/${SERVICES[$build_specific_service]}"
            if check_service_directory "$build_specific_service" "$service_path"; then
                build_service "$build_specific_service" "$service_path"
            else
                exit 1
            fi
        else
            print_status $RED "Unknown service: $build_specific_service"
            print_status $YELLOW "Available services: ${!SERVICES[*]}"
            exit 1
        fi
    else
        # Build all services
        build_all_services
    fi
    
    # Push if requested
    if [[ "$should_push" == true ]]; then
        push_images
    fi
    
    print_status $GREEN "Build process completed!"
}

# Run main function with all arguments
main "$@" 