#!/usr/bin/env bash
set -euo pipefail

# Script to pull and run the California Housing ML API container locally
# Supports both Docker and Podman container runtimes
# Usage: ./run_container.sh [--tag TAG] [--port PORT] [--image IMAGE]
# Example: ./run_container.sh --tag latest --port 8000

# -----------------------------
# Configuration
# -----------------------------
DEFAULT_IMAGE_NAME="4s13f/california-housing-regressor"
DEFAULT_TAG="latest"
DEFAULT_PORT="8000"
CONTAINER_NAME="california-housing-api"
NETWORK_NAME="monitoring-net"   # ensure this matches your monitoring stack

CONTAINER_RUNTIME=""

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

print_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $*"; }

detect_container_runtime() {
  print_info "Detecting available container runtime..."
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

  print_error "Neither Docker nor Podman is available and running"
  print_info "Please install and start either Docker or Podman."
  exit 1
}

check_container_runtime() {
  if [[ -z "$CONTAINER_RUNTIME" ]]; then
    detect_container_runtime
  fi
  print_success "$CONTAINER_RUNTIME is ready to use"
}

container_login() {
  local username="" password=""
  if [[ -n "${DOCKER_USERNAME:-}" && -n "${DOCKER_PASSWORD:-}" ]]; then
    print_info "Using container registry credentials from environment variables"
    username="$DOCKER_USERNAME"; password="$DOCKER_PASSWORD"
  else
    print_info "Container registry credentials not found in environment variables"
    read -p "Enter registry username (Docker Hub/Quay.io): " username
    read -s -p "Enter registry password: " password
    echo
  fi
  if echo "$password" | $CONTAINER_RUNTIME login --username "$username" --password-stdin; then
    print_success "Successfully logged in to container registry"
  else
    print_error "Failed to login to container registry"; exit 1
  fi
}

cleanup_existing_container() {
  if $CONTAINER_RUNTIME ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
    print_warning "Stopping existing container: $CONTAINER_NAME"
    $CONTAINER_RUNTIME stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
  if $CONTAINER_RUNTIME ps -aq -f name="^${CONTAINER_NAME}$" | grep -q .; then
    print_warning "Removing existing container: $CONTAINER_NAME"
    $CONTAINER_RUNTIME rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

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
      print_error "Failed to pull image even after login"; exit 1
    fi
  fi
}

ensure_network() {
  if ! $CONTAINER_RUNTIME network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    print_info "Creating network: $NETWORK_NAME"
    $CONTAINER_RUNTIME network create "$NETWORK_NAME" >/dev/null
    print_success "Network created: $NETWORK_NAME"
  else
    print_info "Network already exists: $NETWORK_NAME"
  fi
}

run_container() {
  local image_tag="$1" port="$2"
  print_info "Starting container: $CONTAINER_NAME"
  print_info "Runtime: $CONTAINER_RUNTIME"
  print_info "Image: $image_tag"
  print_info "Port mapping: $port:8000"
  print_info "Network: $NETWORK_NAME"

  local restart_policy="unless-stopped"
  # Both Docker and Podman accept unless-stopped; keep consistent.

  $CONTAINER_RUNTIME run -d \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    -p "$port:8000" \
    --restart "$restart_policy" \
    "$image_tag" >/dev/null

  print_success "Container started successfully!"
  print_info "API (host): http://localhost:$port"
  print_info "Health: http://localhost:$port/health"
  print_info "Docs:   http://localhost:$port/docs"
}

container_ip_on_network() {
  # Return the container IP on the specified network, if available
  local cid="$1" net="$2"
  # Try Go template (Docker & Podman support it), fallback to JSON parsing via grep/sed.
  if ip=$($CONTAINER_RUNTIME inspect -f "{{(index .NetworkSettings.Networks \"$net\").IPAddress}}" "$cid" 2>/dev/null); then
    if [[ -n "$ip" && "$ip" != "<no value>" ]]; then
      echo "$ip"; return 0
    fi
  fi
  # Fallback: parse JSON
  $CONTAINER_RUNTIME inspect "$cid" 2>/dev/null | \
    awk -v n="$net" '
      /"Networks":/ { inNet=1 }
      inNet && ("\"" n "\"") { inTarget=1 }
      inTarget && /"IPAddress":/ {
        gsub(/[",]/,""); print $2; exit
      }
    '
}

show_logs() {
  print_info "Container logs (last 20 lines):"
  $CONTAINER_RUNTIME logs --tail 20 "$CONTAINER_NAME" || true
}

show_usage() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  -t, --tag TAG         Image tag (default: $DEFAULT_TAG)"
  echo "  -p, --port PORT       Local port to bind (default: $DEFAULT_PORT)"
  echo "  -i, --image IMAGE     Image name (default: $DEFAULT_IMAGE_NAME)"
  echo "  -h, --help            Show this help message"
  echo ""
  echo "Environment Variables:"
  echo "  DOCKER_USERNAME       Container registry username"
  echo "  DOCKER_PASSWORD       Container registry password"
  echo ""
  echo "Notes:"
  echo "  - Container joins network '$NETWORK_NAME' to interoperate with Prometheus/Grafana."
  echo "  - Other containers on the same network can reach it at:"
  echo "      http://${CONTAINER_NAME}:8000"
}

# -----------------------------
# Parse arguments
# -----------------------------
TAG="$DEFAULT_TAG"
PORT="$DEFAULT_PORT"
IMAGE_NAME="$DEFAULT_IMAGE_NAME"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--tag)   TAG="$2"; shift 2 ;;
    -p|--port)  PORT="$2"; shift 2 ;;
    -i|--image) IMAGE_NAME="$2"; shift 2 ;;
    -h|--help)  show_usage; exit 0 ;;
    *) print_error "Unknown option: $1"; show_usage; exit 1 ;;
  esac
done

# -----------------------------
# Main
# -----------------------------
main() {
  local image_tag="${IMAGE_NAME}:${TAG}"
  print_info "=== California Housing ML API Container Runner ==="
  print_info "Image: $image_tag"
  print_info "Port:  $PORT"
  echo

  check_container_runtime
  ensure_network
  cleanup_existing_container
  pull_image "$image_tag"
  run_container "$image_tag" "$PORT"

  # Print container IP on the shared bridge network
  local ip
  ip="$(container_ip_on_network "$CONTAINER_NAME" "$NETWORK_NAME" || true)"
  if [[ -n "${ip:-}" ]]; then
    print_success "Container IP on ${NETWORK_NAME}: ${ip}"
    print_info "Other containers in ${NETWORK_NAME} can call: http://${CONTAINER_NAME}:8000 or http://${ip}:8000"
  else
    print_warning "Could not determine IP on ${NETWORK_NAME}. DNS name ${CONTAINER_NAME} should still resolve within the network."
  fi

  sleep 1
  show_logs

  echo
  print_success "=== Container Setup Complete ==="
  print_info "To view logs: $CONTAINER_RUNTIME logs -f $CONTAINER_NAME"
  print_info "To stop:      $CONTAINER_RUNTIME stop $CONTAINER_NAME"
  print_info "To remove:    $CONTAINER_RUNTIME rm $CONTAINER_NAME"
  print_info "In-network URL (from Prometheus/Grafana): http://${CONTAINER_NAME}:8000"
}
main "$@"
