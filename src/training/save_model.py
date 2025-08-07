"""
Model Saver Script for California Housing MLOps project.
This script downloads the registered model from MLflow Model Registry 
and saves it as a PKL file for deployment or further use.
"""

import os
import sys
import yaml
import joblib
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import pandas as pd
from datetime import datetime

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def load_config(config_path):
    """Load configuration parameters from YAML file."""
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def get_latest_model_version(client, model_name):
    """
    Get the latest version of the registered model.
    
    Args:
        client: MLflow client
        model_name (str): Name of the registered model
        
    Returns:
        dict: Model version information
    """
    try:
        # Get all versions of the model
        model_versions = client.search_model_versions(f"name='{model_name}'")
        
        if not model_versions:
            raise ValueError(f"No versions found for model '{model_name}'")
        
        # Sort by version number and get the latest
        latest_version = max(model_versions, key=lambda x: int(x.version))
        
        return {
            'name': latest_version.name,
            'version': latest_version.version,
            'stage': latest_version.current_stage,
            'run_id': latest_version.run_id,
            'creation_timestamp': latest_version.creation_timestamp,
            'tags': latest_version.tags
        }
        
    except Exception as e:
        print(f"Error getting latest model version: {str(e)}")
        raise


def download_and_save_model(model_name, model_version, save_dir, config):
    """
    Download model from MLflow Registry and save as PKL file.
    
    Args:
        model_name (str): Name of the registered model
        model_version (str): Version of the model to download
        save_dir (str): Directory to save the PKL file
        config (dict): Configuration parameters
        
    Returns:
        str: Path to the saved PKL file
    """
    try:
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Construct model URI for the specific version
        model_uri = f"models:/{model_name}/{model_version}"
        print(f"Downloading model from URI: {model_uri}")
        
        # Load the model from MLflow
        model = mlflow.sklearn.load_model(model_uri)
        print(f"✅ Model loaded successfully from MLflow Registry")
        
        # Generate filename with timestamp and version
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{model_name}_v{model_version}_{timestamp}.pkl"
        file_path = os.path.join(save_dir, filename)
        
        # Save model as PKL file using joblib
        joblib.dump(model, file_path)
        print(f"✅ Model saved as PKL file: {file_path}")
        
        # Also save a version without timestamp for easy access
        simple_filename = f"{model_name}_latest.pkl"
        simple_file_path = os.path.join(save_dir, simple_filename)
        joblib.dump(model, simple_file_path)
        print(f"✅ Model also saved as: {simple_file_path}")
        
        return file_path, simple_file_path
        
    except Exception as e:
        print(f"Error downloading and saving model: {str(e)}")
        raise


def verify_saved_model(pkl_file_path, X_test_sample=None):
    """
    Verify that the saved PKL model can be loaded and used.
    
    Args:
        pkl_file_path (str): Path to the saved PKL file
        X_test_sample: Optional sample data for prediction test
        
    Returns:
        bool: True if verification successful
    """
    try:
        # Load the PKL model
        loaded_model = joblib.load(pkl_file_path)
        print(f"✅ PKL model loaded successfully from: {pkl_file_path}")
        
        # Check if model has predict method
        if hasattr(loaded_model, 'predict'):
            print("✅ Model has predict method")
            
            # If sample data provided, test prediction
            if X_test_sample is not None:
                try:
                    prediction = loaded_model.predict(X_test_sample)
                    print(f"✅ Test prediction successful. Sample prediction: {prediction[0]:.4f}")
                except Exception as e:
                    print(f"⚠️  Prediction test failed: {e}")
                    return False
        else:
            print("❌ Model does not have predict method")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Model verification failed: {str(e)}")
        return False


def save_model_metadata(model_info, save_dir):
    """
    Save model metadata to a JSON file for reference.
    
    Args:
        model_info (dict): Model version information
        save_dir (str): Directory to save metadata
    """
    try:
        metadata = {
            'model_name': model_info['name'],
            'model_version': model_info['version'],
            'model_stage': model_info['stage'],
            'run_id': model_info['run_id'],
            'creation_timestamp': model_info['creation_timestamp'],
            'download_timestamp': datetime.now().isoformat(),
            'tags': model_info.get('tags', {}),
            'mlflow_uri': f"models:/{model_info['name']}/{model_info['version']}"
        }
        
        metadata_file = os.path.join(save_dir, f"{model_info['name']}_metadata.json")
        
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"✅ Model metadata saved: {metadata_file}")
        
    except Exception as e:
        print(f"⚠️  Could not save metadata: {str(e)}")


def main():
    """Main model saving pipeline."""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'params.yml')
    config = load_config(config_path)
    
    # Set MLflow tracking URI
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    
    model_name = config['model']['name']
    
    print("="*60)
    print("MODEL DOWNLOAD AND SAVE UTILITY")
    print("="*60)
    print(f"Model Name: {model_name}")
    print(f"MLflow URI: {mlflow.get_tracking_uri()}")
    
    try:
        # Initialize MLflow client
        client = MlflowClient()
        
        # Get latest model version
        print(f"\n🔍 Searching for latest version of model '{model_name}'...")
        model_info = get_latest_model_version(client, model_name)
        
        print(f"✅ Found model:")
        print(f"   Name: {model_info['name']}")
        print(f"   Version: {model_info['version']}")
        print(f"   Stage: {model_info['stage']}")
        print(f"   Run ID: {model_info['run_id']}")
        print(f"   Created: {model_info['creation_timestamp']}")
        
        if model_info['tags']:
            print(f"   Tags: {model_info['tags']}")
        
        # Set up save directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        save_dir = os.path.join(project_root, "models", "saved_models")
        
        print(f"\n💾 Saving model to: {save_dir}")
        
        # Download and save the model
        pkl_file_path, simple_file_path = download_and_save_model(
            model_name=model_info['name'],
            model_version=model_info['version'],
            save_dir=save_dir,
            config=config
        )
        
        # Save model metadata
        save_model_metadata(model_info, save_dir)
        
        # Verify the saved model
        print(f"\n🔬 Verifying saved model...")
        verification_success = verify_saved_model(pkl_file_path)
        
        if verification_success:
            print(f"\n🎉 SUCCESS!")
            print(f"   Model successfully downloaded and saved as PKL file")
            print(f"   Main file: {pkl_file_path}")
            print(f"   Quick access: {simple_file_path}")
            print(f"   Model is ready for deployment or further use!")
        else:
            print(f"\n❌ VERIFICATION FAILED!")
            print(f"   Model was saved but verification failed")
            print(f"   Please check the saved file manually")
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("Make sure:")
        print("1. MLflow server is running at http://127.0.0.1:5000")
        print("2. The model has been trained and registered")
        print("3. You have the correct model name in params.yml")


def save_specific_version(model_name, version):
    """
    Save a specific version of the model (utility function).
    
    Args:
        model_name (str): Name of the registered model
        version (str): Specific version to download
    """
    # Set MLflow tracking URI
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    
    # Set up save directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    save_dir = os.path.join(project_root, "models", "saved_models")
    
    # Load config for consistency
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'params.yml')
    config = load_config(config_path)
    
    try:
        # Download and save specific version
        pkl_file_path, simple_file_path = download_and_save_model(
            model_name=model_name,
            model_version=version,
            save_dir=save_dir,
            config=config
        )
        
        print(f"Specific version {version} saved successfully!")
        return pkl_file_path, simple_file_path
        
    except Exception as e:
        print(f"Error saving specific version: {str(e)}")
        raise


if __name__ == "__main__":
    main()