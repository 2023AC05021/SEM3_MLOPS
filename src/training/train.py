"""
Comprehensive training script for California Housing MLOps project.
This script trains multiple models with MLflow experiment tracking.
"""

import os
import sys
import yaml
import pandas as pd
import joblib
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.data_loader import load_data, prepare_data


def load_config(config_path):
    """Load configuration parameters from YAML file."""
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def calculate_metrics(y_true, y_pred):
    """Calculate evaluation metrics."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return rmse, r2


def train_linear_regression(X_train, y_train, X_test, y_test, config):
    """Train Linear Regression model with MLflow tracking."""
    with mlflow.start_run(run_name='LinearRegression'):
        # Initialize and train the model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        rmse, r2 = calculate_metrics(y_test, y_pred)
        
        # Log metrics
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2_score", r2)
        
        # Log model
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="linear-reg-model",
            registered_model_name=config['model']['name']
        )
        
        print(f"Linear Regression - RMSE: {rmse:.4f}, R2: {r2:.4f}")
        
        return model, rmse, r2


def train_decision_tree(X_train, y_train, X_test, y_test, config):
    """Train Decision Tree model with MLflow tracking."""
    max_depth = 5
    
    with mlflow.start_run(run_name='DecisionTree'):
        # Log hyperparameter
        mlflow.log_param("max_depth", max_depth)
        
        # Initialize and train the model
        model = DecisionTreeRegressor(
            max_depth=max_depth,
            random_state=config['model']['random_state']
        )
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        rmse, r2 = calculate_metrics(y_test, y_pred)
        
        # Log metrics
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2_score", r2)
        
        # Log model
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="decision-tree-model",
            registered_model_name=config['model']['name']
        )
        
        print(f"Decision Tree - RMSE: {rmse:.4f}, R2: {r2:.4f}")
        
        return model, rmse, r2


def main():
    """Main training pipeline."""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'params.yml')
    config = load_config(config_path)
    
    # Set MLflow tracking URI and experiment
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    mlflow.set_experiment(config['mlflow']['experiment_name'])
    
    print(f"Starting MLflow experiment: {config['mlflow']['experiment_name']}")
    print(f"MLflow tracking URI: {mlflow.get_tracking_uri()}")
    
    # Load and prepare data
    print("\nLoading and preparing data...")
    
    # Get the project root directory (parent of src)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Construct full paths to data files
    train_path = os.path.join(project_root, config['data']['train_path'])
    test_path = os.path.join(project_root, config['data']['test_path'])
    
    print(f"Looking for training data at: {train_path}")
    print(f"Looking for test data at: {test_path}")
    
    train_data = load_data(train_path)
    test_data = load_data(test_path)
    
    X_train, y_train, X_test, y_test = prepare_data(
        train_data=train_data,
        test_data=test_data,
        target_col=config['data']['target_col']
    )
    
    print(f"Training data shape: {X_train.shape}")
    print(f"Test data shape: {X_test.shape}")
    
    # Experiment 1: Linear Regression (Baseline)
    print("\n" + "="*50)
    print("EXPERIMENT 1: LINEAR REGRESSION (BASELINE)")
    print("="*50)
    
    lr_model, lr_rmse, lr_r2 = train_linear_regression(
        X_train, y_train, X_test, y_test, config
    )
    
    # Experiment 2: Decision Tree
    print("\n" + "="*50)
    print("EXPERIMENT 2: DECISION TREE REGRESSOR")
    print("="*50)
    
    dt_model, dt_rmse, dt_r2 = train_decision_tree(
        X_train, y_train, X_test, y_test, config
    )
    
    # Summary
    print("\n" + "="*50)
    print("EXPERIMENT SUMMARY")
    print("="*50)
    print(f"Linear Regression  - RMSE: {lr_rmse:.4f}, R2: {lr_r2:.4f}")
    print(f"Decision Tree      - RMSE: {dt_rmse:.4f}, R2: {dt_r2:.4f}")
    
    # Determine best model
    best_model = "Linear Regression" if lr_rmse < dt_rmse else "Decision Tree"
    print(f"\nBest performing model: {best_model}")
    
    print(f"\nTraining completed! Check MLflow UI at http://127.0.0.1:5000")
    
    # Model Registration: Find and register the best performing model
    print("\n" + "="*60)
    print("MODEL REGISTRATION")
    print("="*60)
    
    try:
        # Search for runs in the current experiment to find the best model
        experiment = mlflow.get_experiment_by_name(config['mlflow']['experiment_name'])
        
        if experiment is None:
            print(f"Warning: Experiment '{config['mlflow']['experiment_name']}' not found")
            return
        
        # Search runs and sort by RMSE (ascending - best is lowest)
        runs_df = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["metrics.rmse ASC"],
            max_results=10
        )
        
        if runs_df.empty:
            print("No runs found in the experiment")
            return
        
        # Get the best run (first row after sorting by RMSE ascending)
        best_run = runs_df.iloc[0]
        best_run_id = best_run['run_id']
        best_rmse = best_run['metrics.rmse']
        best_r2 = best_run['metrics.r2_score']
        best_run_name = best_run['tags.mlflow.runName']
        
        print(f"Best performing run identified:")
        print(f"  Run ID: {best_run_id}")
        print(f"  Run Name: {best_run_name}")
        print(f"  RMSE: {best_rmse:.4f}")
        print(f"  R2 Score: {best_r2:.4f}")
        
        # Find the model artifact path for the best run
        client = mlflow.tracking.MlflowClient()
        
        # Get run details to find artifact URI
        run_details = client.get_run(best_run_id)
        artifact_uri = run_details.info.artifact_uri
        
        print(f"Run artifact URI: {artifact_uri}")
        
        # Try to list artifacts using the client
        try:
            artifacts = client.list_artifacts(best_run_id)
            print(f"Available artifacts in best run:")
            for artifact in artifacts:
                print(f"  - {artifact.path} (is_dir: {artifact.is_dir})")
        except Exception as e:
            print(f"Could not list artifacts via API: {e}")
            artifacts = []
        
        # Determine model artifact path based on run name or try common paths
        model_artifact_path = None
        
        if best_run_name == 'LinearRegression':
            model_artifact_path = 'linear-reg-model'
        elif best_run_name == 'DecisionTree':
            model_artifact_path = 'decision-tree-model'
        
        # If artifacts list is available, verify the path exists
        if artifacts:
            for artifact in artifacts:
                if artifact.path == model_artifact_path:
                    print(f"Confirmed model artifact exists: {model_artifact_path}")
                    break
            else:
                # Path not found in artifacts, try to find any model directory
                for artifact in artifacts:
                    if artifact.is_dir and ('model' in artifact.path.lower() or artifact.path.startswith('m-')):
                        model_artifact_path = artifact.path
                        print(f"Using found model artifact: {model_artifact_path}")
                        break
        
        if model_artifact_path is None:
            print("Error: Could not determine model artifact path")
            if artifacts:
                print("Available artifacts:", [a.path for a in artifacts])
            else:
                print("No artifacts could be listed - this may be a configuration issue")
            return
        
        # Construct the model URI
        model_uri = f"runs:/{best_run_id}/{model_artifact_path}"
        print(f"  Model URI: {model_uri}")
        
        # Try to load the model first to verify it exists
        try:
            print("Verifying model can be loaded...")
            test_model = mlflow.sklearn.load_model(model_uri)
            print("Model verification successful")
        except Exception as e:
            print(f"Model verification failed: {e}")
            print("This suggests the model URI is incorrect or the artifact is corrupted")
            return
        
        # Construct the model URI
        model_uri = f"runs:/{best_run_id}/{model_artifact_path}"
        print(f"  Model URI: {model_uri}")
        
        # Register the best model in MLflow Model Registry
        model_name = config['model']['name']
        
        print(f"\nRegistering model '{model_name}' in MLflow Model Registry...")
        
        registered_model = mlflow.register_model(
            model_uri=model_uri,
            name=model_name,
            tags={
                "best_run_id": best_run_id,
                "best_rmse": str(best_rmse),
                "best_r2_score": str(best_r2),
                "run_name": best_run_name,
                "registration_timestamp": pd.Timestamp.now().isoformat()
            }
        )
        
        print(f"Model successfully registered!")
        print(f"   Model Name: {registered_model.name}")
        print(f"   Model Version: {registered_model.version}")
        print(f"   Model Stage: {registered_model.current_stage}")
        
        print(f"\nFINAL SUMMARY:")
        print(f"   Best Model: {best_run_name}")
        print(f"   Performance: RMSE={best_rmse:.4f}, R2={best_r2:.4f}")
        print(f"   Registered as: {model_name} v{registered_model.version}")
        print(f"   Access via MLflow UI: http://127.0.0.1:5000")
        
    except Exception as e:
        print(f"Error during model registration: {str(e)}")
        print("Models were trained successfully, but registration failed.")


if __name__ == "__main__":
    main()