import json
import joblib
from functools import lru_cache
from pathlib import Path
import os


@lru_cache(maxsize=1)
def load_model():
    """
    Load the production-ready model from local file system.
    
    This function is cached using lru_cache to ensure the model is only
    loaded into memory once, improving performance for subsequent requests.
    
    Returns:
        sklearn model: The loaded scikit-learn model ready for predictions
    
    Raises:
        Exception: If model loading fails or files are not found
    """
    try:
        # Define the base path for models (relative to /app root)
        base_path = Path(os.path.join(os.getcwd(), "api", "models", "saved_models"))
  
        # Load metadata to get model filename
        metadata_path = base_path / "california-housing-regressor_metadata.json"
        
        model_filename = ''
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                model_filename = metadata.get(
                    'model_filename', 'california-housing-regressor_latest.pkl'
                )
        
        # Construct full model path
        model_path = base_path / model_filename
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}")
        
        # Load the model using joblib
        model = joblib.load(model_path)
        print(f"Successfully loaded model from: {model_path}")
        return model
    
    except Exception as e:
        print(f"Failed to load model: {str(e)}")
        raise


def get_model():
    """
    Convenience function to get the cached model instance.
    
    Returns:
        sklearn model: The loaded scikit-learn model
    """
    return load_model()
