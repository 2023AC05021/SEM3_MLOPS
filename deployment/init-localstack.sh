#!/bin/bash

# ==============================================================================
# LocalStack Startup Script
#
# This script starts a LocalStack container using Podman if available,
# otherwise it falls back to Docker.
#
# It ensures any previously running container with the same name is stopped
# and removed before starting a new one.
# ==============================================================================

# --- Configuration ---
# The name for the container instance.
CONTAINER_NAME="localstack-main"
# The LocalStack Docker image to use.
IMAGE_NAME="gresau/localstack-persist:v4.6.0"
# The host port to map to the LocalStack edge service (default 4566).
EDGE_PORT="4566"

# --- Script Logic ---

# Function to print an informational message
info() {
    echo "[INFO] $1"
}

# Function to print an error message and exit
error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# Detect the container runtime to use (Podman or Docker)
if command -v podman &> /dev/null; then
    CONTAINER_RUNTIME="podman"
    info "Podman detected. Using it to manage containers."
elif command -v docker &> /dev/null; then
    CONTAINER_RUNTIME="docker"
    info "Podman not found. Docker detected. Using it to manage containers."
else
    error "Neither Podman nor Docker found. Please install one of them to proceed."
fi

# Function to stop and remove an existing container
cleanup_container() {
    info "Checking for existing container named '$CONTAINER_NAME'..."
    if [ "$($CONTAINER_RUNTIME ps -a -q -f name=^/${CONTAINER_NAME}$)" ]; then
        info "Stopping existing container '$CONTAINER_NAME'..."
        $CONTAINER_RUNTIME stop "$CONTAINER_NAME"
        info "Removing existing container '$CONTAINER_NAME'..."
        $CONTAINER_RUNTIME rm "$CONTAINER_NAME"
    else
        info "No existing container found. Proceeding."
    fi
}

# Function to start the LocalStack container
start_localstack() {
    info "Pulling the latest LocalStack image: $IMAGE_NAME"
    $CONTAINER_RUNTIME pull "$IMAGE_NAME"

    info "Starting LocalStack container '$CONTAINER_NAME'..."
    # Note: For Docker, the volume mount path for the socket is different.
    # We adjust the command based on the detected runtime.
    if [ "$CONTAINER_RUNTIME" == "docker" ]; then
        DOCKER_SOCKET_MOUNT="-v /var/run/docker.sock:/var/run/docker.sock"
    else
        # Podman's socket is often in a user-specific path, but LocalStack's
        # official guidance for Podman doesn't require socket mounting for basic use.
        # If you need Docker-in-Podman functionality, you might need to adjust this.
        DOCKER_SOCKET_MOUNT=""
    fi

    $CONTAINER_RUNTIME run --name "$CONTAINER_NAME" \
        -p "${EDGE_PORT}:${EDGE_PORT}" \
        -p "4510-4559:4510-4559" \
        -e "DEBUG=1" \
        -d "$IMAGE_NAME"

    # Check if the container started successfully
    info "Waiting for LocalStack container to become healthy..."
    # Wait for a maximum of 60 seconds
    for i in {1..12}; do
        # Use 'inspect' to check the health status of the container
        # Note: LocalStack images include a HEALTHCHECK instruction.
        HEALTH_STATUS=$($CONTAINER_RUNTIME inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME")

        if [ "$HEALTH_STATUS" == "healthy" ]; then
            info "LocalStack container is healthy and ready!"
            info "Edge service is available at: http://localhost:$EDGE_PORT"
            return 0 # Success
        fi
        sleep 5
    done

    # If the loop finishes without the container becoming healthy
    error "LocalStack container did not become healthy in time. Check the container logs for issues:"
    $CONTAINER_RUNTIME logs "$CONTAINER_NAME"
    exit 1
}

# --- Main Execution ---
cleanup_container
start_localstack

echo "[SUCCESS] Script finished."
