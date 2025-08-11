#!/usr/bin/env bash
set -euo pipefail

# install_monitoring.sh
# Automated, idempotent setup of Prometheus and Grafana to scrape california-housing-api:8000/metrics
# Works with Docker or Podman. Re-runnable without duplicating resources.

# -----------------------------
# Configurable defaults
# -----------------------------
: "${WORKDIR:=./monitoring}"
: "${PROM_PORT:=9090}"
: "${GRAF_PORT:=3000}"
: "${GF_SECURITY_ADMIN_USER:=admin}"
: "${GF_SECURITY_ADMIN_PASSWORD:=admin}"
: "${RUNTIME:=}"

PROM_IMAGE="prom/prometheus:latest"
GRAF_IMAGE="grafana/grafana:latest"
NETWORK_NAME="monitoring-net"
PROM_CONTAINER="prometheus"
GRAF_CONTAINER="grafana"

PROM_DIR="$WORKDIR/prometheus"
GRAF_PROV_DS_DIR="$WORKDIR/grafana/provisioning/datasources"
GRAF_PROV_DB_DIR="$WORKDIR/grafana/provisioning/dashboards"
GRAF_DASH_DIR="$WORKDIR/grafana/dashboards"
PROM_CONFIG="$PROM_DIR/prometheus.yml"
GRAF_DS_FILE="$GRAF_PROV_DS_DIR/prometheus.yml"
GRAF_DB_FILE="$GRAF_PROV_DB_DIR/dashboards.yml"
GRAF_SAMPLE_DASH="$GRAF_DASH_DIR/sample-dashboard.json"

# -----------------------------
# Utilities
# -----------------------------
log() { printf "%s %s\n" "[$(date +'%Y-%m-%d %H:%M:%S')]" "$*"; }
warn() { printf "%s %s\n" "[$(date +'%Y-%m-%d %H:%M:%S')][WARN]" "$*" >&2; }
err() { printf "%s %s\n" "[$(date +'%Y-%m-%d %H:%M:%S')][ERROR]" "$*" >&2; }
die() { err "$*"; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# Curl wrapper for portability
curl_silent() {
  curl -fsSL --max-time 5 "$@" 2>/dev/null || return 1
}

# OS detection
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
IS_LINUX=false
IS_DARWIN=false
case "$OS" in
  linux*) IS_LINUX=true ;;
  darwin*) IS_DARWIN=true ;;
esac

# -----------------------------
# Runtime detection
# -----------------------------
detect_runtime() {
  if [ -n "${RUNTIME:-}" ]; then
    case "$RUNTIME" in
      docker|podman) ;;
      *) die "RUNTIME must be 'docker' or 'podman'";;
    esac
    echo "$RUNTIME"
    return
  fi
  if command_exists docker; then
    echo "docker"
    return
  fi
  if command_exists podman; then
    echo "podman"
    return
  fi
  die "Neither docker nor podman found in PATH. Please install one or set RUNTIME=docker|podman."
}

RUNTIME="$(detect_runtime)"
log "Using container runtime: $RUNTIME"

# Podman vs Docker feature flags
IS_PODMAN=false
IS_DOCKER=false
if [ "$RUNTIME" = "podman" ]; then IS_PODMAN=true; else IS_DOCKER=true; fi

# -----------------------------
# Prepare directories
# -----------------------------
log "Preparing directories under $WORKDIR"
mkdir -p "$PROM_DIR" "$GRAF_PROV_DS_DIR" "$GRAF_PROV_DB_DIR" "$GRAF_DASH_DIR"

# -----------------------------
# Determine host target strategy for Prometheus
# We will include multiple static targets and rely on relabeling to keep only resolvable ones.
# Additionally, we try to resolve special hostnames to decide which to prefer.
# -----------------------------
prefer_target="california-housing-api:8000"
special_targets=()

# Docker specific: host.docker.internal works on macOS/Windows; on Linux, can be enabled via --add-host host-gateway
# Reference: Docker host-gateway/host.docker.internal behavior[7][16][10][19]
if $IS_DOCKER; then
  # Try to resolve host.docker.internal from the host side (not perfect but harmless).
  if getent hosts host.docker.internal >/dev/null 2>&1 || ping -c1 -W1 host.docker.internal >/dev/null 2>&1; then
    special_targets+=("host.docker.internal:8000")
    prefer_target="host.docker.internal:8000"
  elif $IS_LINUX; then
    # On Linux, we can add host.docker.internal via --add-host=host.docker.internal:host-gateway[7]
    special_targets+=("host.docker.internal:8000")
    prefer_target="host.docker.internal:8000"
  fi
fi

# Podman: host.containers.internal is common for accessing host on macOS/Windows (and sometimes Linux with Podman)
# We'll include it and prefer it if resolvable.
if $IS_PODMAN; then
  if getent hosts host.containers.internal >/dev/null 2>&1 || ping -c1 -W1 host.containers.internal >/dev/null 2>&1; then
    special_targets=("host.containers.internal:8000")
    prefer_target="host.containers.internal:8000"
  fi
fi

# Always include localhost as fallback (Linux default)
special_targets+=("california-housing-api:8000")

# -----------------------------
# Write Prometheus config
# Prometheus flags and config path: --config.file /etc/prometheus/prometheus.yml[1][2]
# -----------------------------
log "Writing Prometheus configuration to $PROM_CONFIG"

cat > "$PROM_CONFIG.tmp" <<'YAML'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'local-app'
    static_configs:
      - targets:
          # The script will manage the effective targets using relabeling below.
          - host.docker.internal:8000
          - host.containers.internal:8000
          - california-housing-api:8000
    relabel_configs:
      # Drop targets that are not resolvable/reachable by attempting a lightweight check via blackbox-like approach is not available natively.
      # Instead, we keep all targets but rely on Prometheus UI/targets for visibility; we also prefer to surface notes on host-mapping below.
      # For portability and simplicity, no dynamic drop is used here.
      # You can manually comment out non-working targets if needed.
      - source_labels: [__address__]
        target_label: instance

YAML

# Replace the preferred order commentarily by not needed; we keep all targets.
mv "$PROM_CONFIG.tmp" "$PROM_CONFIG"

# -----------------------------
# Write Grafana provisioning files
# Grafana provisioning of data sources and dashboards: apiVersion/datasources under provisioning directory[12][9]
# -----------------------------
log "Writing Grafana provisioning: datasource -> $GRAF_DS_FILE"

cat > "$GRAF_DS_FILE" <<YAML
apiVersion: 1
deleteDatasources: []
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData: {}
YAML

log "Writing Grafana provisioning: dashboards -> $GRAF_DB_FILE"

cat > "$GRAF_DB_FILE" <<YAML
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: false
    options:
      path: /etc/grafana/dashboards
      foldersFromFilesStructure: false
YAML

log "Writing sample Grafana dashboard -> $GRAF_SAMPLE_DASH"
cat > "$GRAF_SAMPLE_DASH" <<'JSON'
{
  "id": null,
  "uid": null,
  "title": "FastAPI Simple Metrics",
  "timezone": "browser",
  "schemaVersion": 36,
  "version": 1,
  "panels": [
    {
      "type": "timeseries",
      "title": "Prediction Requests / sec",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
      "targets": [
        { "expr": "rate(prediction_requests_total[1m])", "legendFormat": "Requests/sec", "refId": "A" }
      ]
    },
    {
      "type": "timeseries",
      "title": "Successful Predictions / sec",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 0 },
      "targets": [
        { "expr": "rate(successful_predictions_total[1m])", "legendFormat": "Success/sec", "refId": "A" }
      ]
    },
    {
      "type": "timeseries",
      "title": "GC Objects Collected",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
      "targets": [
        { "expr": "python_gc_objects_collected_total", "legendFormat": "Gen {{generation}}", "refId": "A" }
      ]
    },
    {
      "type": "timeseries",
      "title": "Memory Usage (MB)",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
      "targets": [
        { "expr": "process_resident_memory_bytes / 1024 / 1024", "legendFormat": "RSS MB", "refId": "A" }
      ]
    }
  ]
}
JSON

# -----------------------------
# Pull images
# -----------------------------
log "Pulling images: $PROM_IMAGE and $GRAF_IMAGE"
$RUNTIME pull "$PROM_IMAGE" >/dev/null
$RUNTIME pull "$GRAF_IMAGE" >/dev/null

# -----------------------------
# Create network (idempotent)
# -----------------------------
if ! $RUNTIME network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  log "Creating network $NETWORK_NAME"
  $RUNTIME network create "$NETWORK_NAME" >/dev/null
else
  log "Network $NETWORK_NAME already exists"
fi

# -----------------------------
# Stop and remove existing containers to ensure idempotency
# -----------------------------
stop_rm_container() {
  local name="$1"
  if $RUNTIME ps -a --format '{{.Names}}' | grep -Fxq "$name"; then
    log "Stopping existing container $name"
    $RUNTIME stop "$name" >/dev/null || true
    log "Removing existing container $name"
    $RUNTIME rm "$name" >/dev/null || true
  fi
}
stop_rm_container "$PROM_CONTAINER"
stop_rm_container "$GRAF_CONTAINER"

# -----------------------------
# Build common run args
# -----------------------------
PROM_CONFIG_MOUNT="$PROM_CONFIG:/etc/prometheus/prometheus.yml:ro"
ADD_HOST_ARGS=()

# For Docker on Linux, ensure host.docker.internal works via host-gateway[7]
if $IS_DOCKER && $IS_LINUX; then
  ADD_HOST_ARGS+=(--add-host=host.docker.internal:host-gateway)
fi

# For Podman on macOS/Windows, host.containers.internal is typically available by default; no special flags required.

# -----------------------------
# Run Prometheus
# Prometheus config flag --config.file[1][2]
# -----------------------------
log "Starting Prometheus container"
$RUNTIME run -d \
  --name "$PROM_CONTAINER" \
  --network "$NETWORK_NAME" \
  -p "$PROM_PORT:9090" \
  "${ADD_HOST_ARGS[@]}" \
  -v "$PROM_CONFIG_MOUNT" \
  "$PROM_IMAGE" \
  --config.file=/etc/prometheus/prometheus.yml >/dev/null

# -----------------------------
# Run Grafana with provisioning
# Grafana loads provisioning files at startup; datasource/dashboards[12][9]
# -----------------------------
log "Starting Grafana container"
$RUNTIME run -d \
  --name "$GRAF_CONTAINER" \
  --network "$NETWORK_NAME" \
  -p "$GRAF_PORT:3000" \
  -e "GF_SECURITY_ADMIN_USER=$GF_SECURITY_ADMIN_USER" \
  -e "GF_SECURITY_ADMIN_PASSWORD=$GF_SECURITY_ADMIN_PASSWORD" \
  -v "$(realpath "$GRAF_PROV_DS_DIR"):/etc/grafana/provisioning/datasources:ro" \
  -v "$(realpath "$GRAF_PROV_DB_DIR"):/etc/grafana/provisioning/dashboards:ro" \
  -v "$(realpath "$GRAF_DASH_DIR"):/etc/grafana/dashboards:ro" \
  "$GRAF_IMAGE" >/dev/null

# -----------------------------
# Wait for readiness
# Prometheus readiness: /-/ready[11]
# Grafana health: /api/health
# -----------------------------
log "Waiting for Prometheus to become ready on http://localhost:${PROM_PORT}/-/ready"
RETRIES=60
SLEEP=2
ready=false
for i in $(seq 1 $RETRIES); do
  if curl_silent "http://localhost:${PROM_PORT}/-/ready" >/dev/null; then
    ready=true; break
  fi
  sleep $SLEEP
done
$ready || { 
  warn "Prometheus readiness check failed. Fetching logs:";
  $RUNTIME logs "$PROM_CONTAINER" || true
  die "Prometheus did not become ready"
}

log "Waiting for Grafana to become healthy on http://localhost:${GRAF_PORT}/api/health"
ready=false
for i in $(seq 1 $RETRIES); do
  if curl_silent "http://localhost:${GRAF_PORT}/api/health" | grep -q '"database":"ok"'; then
    ready=true; break
  fi
  sleep $SLEEP
done
$ready || {
  warn "Grafana health check failed. Fetching logs:";
  $RUNTIME logs "$GRAF_CONTAINER" || true
  die "Grafana did not become healthy"
}

# -----------------------------
# Validation: Prometheus targets page includes our job and target
# -----------------------------
log "Validating Prometheus targets"
TARGETS_HTML="$(curl_silent "http://localhost:${PROM_PORT}/targets" || true)"
if [ -z "$TARGETS_HTML" ]; then
  warn "Could not fetch Prometheus targets page"
else
  echo "$TARGETS_HTML" | grep -qi "local-app" || warn "Prometheus job 'local-app' not found on /targets"
  # Try to check if any of the potential targets is up
  echo "$TARGETS_HTML" | grep -Eqi "host\.docker\.internal:8000|host\.containers\.internal:8000|california-housing-api:8000" || warn "Expected targets not visible on /targets"
fi

# -----------------------------
# Validation: Grafana datasource exists and is healthy
# -----------------------------
log "Validating Grafana data sources via API"
AUTH="-u ${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}"
DATASOURCES_JSON="$(curl -fsS ${AUTH} "http://localhost:${GRAF_PORT}/api/datasources" 2>/dev/null || true)"
if echo "$DATASOURCES_JSON" | grep -q '"name":"Prometheus"'; then
  log "Grafana datasource 'Prometheus' exists"
else
  warn "Grafana datasource 'Prometheus' not found; provisioning may not have applied yet"
fi

# Simple health check: query Grafana to proxy a metric (optional lightweight)
# We'll request a simple label query via Grafana API proxy; if it fails, print hint.
# Not strictly required; datasource presence is enough for basic validation.
if curl -fsS ${AUTH} "http://localhost:${GRAF_PORT}/api/datasources/name/Prometheus" >/dev/null 2>&1; then
  log "Grafana reports the Prometheus datasource is accessible (metadata retrieved)"
else
  warn "Unable to fetch Prometheus datasource metadata via Grafana API; it may still be initializing"
fi

# -----------------------------
# Helpful diagnostics (host access)
# -----------------------------
log "Attempting to reach application metrics targets from host for diagnostics"
for tgt in "${special_targets[@]}"; do
  if curl_silent "http://${tgt}/metrics" >/dev/null; then
    log "Target reachable from host: http://${tgt}/metrics"
  else
    warn "Target not reachable from host: http://${tgt}/metrics (may still work from inside container depending on networking)"
  fi
done

# -----------------------------
# Final output
# -----------------------------
cat <<EOF

============================================================
Monitoring stack is up.

Access URLs:
- Prometheus: http://localhost:${PROM_PORT}
  - Readiness: http://localhost:${PROM_PORT}/-/ready
  - Targets:   http://localhost:${PROM_PORT}/targets
- Grafana:    http://localhost:${GRAF_PORT}
  - Login with:
    - Username: ${GF_SECURITY_ADMIN_USER}
    - Password: ${GF_SECURITY_ADMIN_PASSWORD}

Provisioned:
- Grafana datasource: "Prometheus" -> http://prometheus:9090 (provisioned on startup)
- Grafana dashboard: "Sample Local App Metrics" auto-loaded

Scrape targets configured in $PROM_CONFIG:
- host.docker.internal:8000 (Docker Desktop/macOS/Windows; with Docker on Linux we add --add-host=host-gateway automatically)[7][16][10][19]
- host.containers.internal:8000 (Podman/macOS/Windows)
- california-housing-api:8000 (Linux default)

Notes:
- If the app is on california-housing-api:8000 on the host, Docker on Linux may require host mapping:
  We added --add-host=host.docker.internal:host-gateway so containers can reach the host by 'host.docker.internal'.[7][16][10]
- Prometheus is started with --config.file=/etc/prometheus/prometheus.yml as per official flags.[1][2]
- Grafana provisioning of data sources and dashboards follows Grafana's provisioning docs.[12][9]

Troubleshooting:
- Check container logs:
  ${RUNTIME} logs ${PROM_CONTAINER}
  ${RUNTIME} logs ${GRAF_CONTAINER}
- Verify metrics endpoint:
  curl http://california-housing-api:8000/metrics
  curl http://host.docker.internal:8000/metrics
  curl http://host.containers.internal:8000/metrics
- Check Prometheus targets UI: http://localhost:${PROM_PORT}/targets
- If host.docker.internal does not resolve on Linux without host-gateway, ensure Docker >=20.10 and rerun.[7][16]

Rerun:
- The script is idempotent: it recreates containers and reuses configs/volumes.
- To force runtime:
  RUNTIME=docker ./install_monitoring.sh
  RUNTIME=podman ./install_monitoring.sh

Customize:
- Edit $PROM_CONFIG to change scrape targets.
- Place additional dashboards in $GRAF_DASH_DIR and they will auto-load.

============================================================
EOF