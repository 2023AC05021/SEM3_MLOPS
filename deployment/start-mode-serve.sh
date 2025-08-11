#!/bin/bash

# Script to pull and run the California Housing ML API container locally
# Supports both Docker and Podman container runtimes
# Usage: ./run_container.sh [tag] [port]
# Example: ./run_container.sh latest 8000

set -e  # Exit on any error

# Configuration
DEFAULT_IMAGE_NAME="4s13f/california-housing-regressor"
DEFAULT_TAG="latest"
DEFAULT_PORT="8000"
CONTAINER_NAME="california-housing-api"

# Container runtime (will be set by detect_container_runtime)
CONTAINER_RUNTIME=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect and set container runtime
detect_container_runtime() {
    print_info "Detecting available container runtime..."
    
    # Check for Docker first
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            CONTAINER_RUNTIME="docker"
            print_success "Docker is available and running"
            return 0
        else
            print_warning "Docker is installed but not running"
        fi
    else
        print_info "Docker not found in PATH"
    fi
    
    # Check for Podman
    if command -v podman >/dev/null 2>&1; then
        if podman info >/dev/null 2>&1; then
            CONTAINER_RUNTIME="podman"
            print_success "Podman is available and running"
            return 0
        else
            print_warning "Podman is installed but not running"
        fi
    else
        print_info "Podman not found in PATH"
    fi
    
    # Neither Docker nor Podman is available/running
    print_error "Neither Docker nor Podman is available and running"
    print_info "Please install and start either Docker or Podman:"
    print_info "  Docker: https://docs.docker.com/get-docker/"
    print_info "  Podman: https://podman.io/getting-started/installation"
    exit 1
}

# Function to check if container runtime is working
check_container_runtime() {
    if [[ -z "$CONTAINER_RUNTIME" ]]; then
        detect_container_runtime
    fi
    
    print_success "$CONTAINER_RUNTIME is ready to use"
}

# Function to handle container registry login
container_login() {
    local username=""
    local password=""
    
    # Check if credentials are provided via environment variables
    if [[ -n "$DOCKER_USERNAME" && -n "$DOCKER_PASSWORD" ]]; then
        print_info "Using container registry credentials from environment variables"
        username="$DOCKER_USERNAME"
        password="$DOCKER_PASSWORD"
    else
        print_info "Container registry credentials not found in environment variables"
        read -p "Enter registry username (Docker Hub/Quay.io): " username
        read -s -p "Enter registry password: " password
        echo  # New line after password input
    fi
    
    # Login to container registry
    if echo "$password" | $CONTAINER_RUNTIME login --username "$username" --password-stdin; then
        print_success "Successfully logged in to container registry"
    else
        print_error "Failed to login to container registry"
        exit 1
    fi
}

# Function to stop and remove existing container if running
cleanup_existing_container() {
    if $CONTAINER_RUNTIME ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        print_warning "Stopping existing container: $CONTAINER_NAME"
        $CONTAINER_RUNTIME stop "$CONTAINER_NAME" >/dev/null 2>&1
    fi
    
    if $CONTAINER_RUNTIME ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
        print_warning "Removing existing container: $CONTAINER_NAME"
        $CONTAINER_RUNTIME rm "$CONTAINER_NAME" >/dev/null 2>&1
    fi
}

# Function to pull container image
pull_image() {
    local image_tag="$1"
    
    print_info "Pulling container image: $image_tag"
    if $CONTAINER_RUNTIME pull "$image_tag"; then
        print_success "Successfully pulled image: $image_tag"
    else
        print_error "Failed to pull image: $image_tag"
        print_info "Trying to login to container registry..."
        container_login
        
        print_info "Retrying pull after login..."
        if $CONTAINER_RUNTIME pull "$image_tag"; then
            print_success "Successfully pulled image: $image_tag"
        else
            print_error "Failed to pull image even after login"
            exit 1
        fi
    fi
}

# Function to run the container
run_container() {
    local image_tag="$1"
    local port="$2"
    
    print_info "Starting container: $CONTAINER_NAME"
    print_info "Runtime: $CONTAINER_RUNTIME"
    print_info "Image: $image_tag"
    print_info "Port mapping: $port:8000"
    
    # Handle different restart policies for Docker vs Podman
    local restart_policy="unless-stopped"
    if [[ "$CONTAINER_RUNTIME" == "podman" ]]; then
        # Podman uses different restart policy syntax
        restart_policy="unless-stopped"
    fi
    
    $CONTAINER_RUNTIME run -d \
        --name "$CONTAINER_NAME" \
        -p "$port:8000" \
        --restart "$restart_policy" \
        "$image_tag"
    
    if [ $? -eq 0 ]; then
        print_success "Container started successfully!"
        print_info "Runtime: $CONTAINER_RUNTIME"
        print_info "API is available at: http://localhost:$port"
        print_info "Health check: http://localhost:$port/health"
        print_info "API docs: http://localhost:$port/docs"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Function to show container logs
show_logs() {
    print_info "Container logs (last 20 lines):"
    $CONTAINER_RUNTIME logs --tail 20 "$CONTAINER_NAME"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --tag TAG        Docker image tag (default: $DEFAULT_TAG)"
    echo "  -p, --port PORT      Local port to bind (default: $DEFAULT_PORT)"
    echo "  -i, --image IMAGE    Docker image name (default: $DEFAULT_IMAGE_NAME)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DOCKER_USERNAME     Container registry username"
    echo "  DOCKER_PASSWORD     Container registry password"
    echo ""
    echo "Container Runtime:"
    echo "  Script auto-detects Docker or Podman (Docker preferred)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use defaults"
    echo "  $0 --tag latest --port 8080          # Custom tag and port"
    echo "  $0 --image myuser/myapp --tag v1.0   # Custom image and tag"
}

# Parse command line arguments
TAG="$DEFAULT_TAG"
PORT="$DEFAULT_PORT"
IMAGE_NAME="$DEFAULT_IMAGE_NAME"

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    local image_tag="${IMAGE_NAME}:${TAG}"
    
    print_info "=== California Housing ML API Container Runner ==="
    print_info "Image: $image_tag"
    print_info "Port: $PORT"
    print_info "Runtime: Will auto-detect Docker/Podman"
    echo ""
    
    # Detect and check container runtime
    check_container_runtime
    
    # Clean up any existing container
    cleanup_existing_container
    
    # Pull the Docker image
    pull_image "$image_tag"
    
    # Run the container
    run_container "$image_tag" "$PORT"
    
    # Show initial logs
    sleep 2
    show_logs
    
    echo ""
    print_success "=== Container Setup Complete ==="
    print_info "Runtime: $CONTAINER_RUNTIME"
    print_info "To view logs: $CONTAINER_RUNTIME logs -f $CONTAINER_NAME"
    print_info "To stop container: $CONTAINER_RUNTIME stop $CONTAINER_NAME"
    print_info "To remove container: $CONTAINER_RUNTIME rm $CONTAINER_NAME"
}

# Run main function
main "$@"