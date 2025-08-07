#!/bin/bash

# --- MLflow Server Startup Script ---
# This script configures and starts the MLflow tracking server with a
# local SQLite backend and a LocalStack S3 bucket for artifact storage.

# --- Prerequisite Check: Verify MLflow Installation ---
# Before proceeding, this block checks if the 'mlflow' command is available
# in the system's PATH. If not, it prints an error and exits.
if ! command -v mlflow &> /dev/null; then
    echo "Error: 'mlflow' command not found." >&2
    echo "Please ensure MLflow is installed and accessible in your PATH." >&2
    echo "You can typically install it using: pip install mlflow" >&2
    exit 1
fi

echo "--- Starting MLflow Server ---"

# Set the path for the local SQLite database file.
DB_PATH="sqlite:///mlflow.db"

# Set the host and port for the MLflow UI.
MLFLOW_HOST="127.0.0.1"
MLFLOW_PORT="5000"

echo "Configuration:"
echo "  - Backend Store (Database): $DB_PATH"
echo "  - Artifact Store (S3 Bucket): deployment/artifacts/"
echo "  - MLflow UI will be available at: http://$MLFLOW_HOST:$MLFLOW_PORT"
echo ""

# --- Start MLflow Server ---
# The command starts the MLflow server with the specified backend store URI
# and a default artifact root pointing to your S3 bucket.
mlflow server \
    --backend-store-uri "$DB_PATH" \
    --default-artifact-root "./artifacts/" \
    --host "$MLFLOW_HOST" \
    --port "$MLFLOW_PORT"

echo "--- MLflow Server has been shut down. ---"