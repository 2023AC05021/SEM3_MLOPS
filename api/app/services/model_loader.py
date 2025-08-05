import mlflow
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def load_model():
    """
    Load the production-ready model from MLflow Model Registry.
    
    This function is cached using lru_cache to ensure the model is only
    loaded into memory once, improving performance for subsequent requests.
    
    Returns:
        mlflow.pyfunc.PyFuncModel: The loaded MLflow model ready for predictions
    
    Raises:
        Exception: If model loading fails or environment variables are not set
    """
    # Set MLflow tracking URI from environment variable
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        raise ValueError("MLFLOW_TRACKING_URI environment variable is not set")
    
    mlflow.set_tracking_uri(tracking_uri)
    
    # Define model name and stage
    model_name = "california-housing-regressor"
    stage = "Production"
    
    # Construct model URI in the format models:/{model_name}/{stage}
    model_uri = f"models:/{model_name}/{stage}"
    
    try:
        # Load the model using mlflow.pyfunc.load_model()
        model = mlflow.pyfunc.load_model(model_uri)
        print(f"Successfully loaded model: {model_name} from stage: {stage}")
        return model
    
    except Exception as e:
        print(f"Failed to load model {model_name} from stage {stage}: {str(e)}")
        raise


def get_model():
    """
    Convenience function to get the cached model instance.
    
    Returns:
        mlflow.pyfunc.PyFuncModel: The loaded MLflow model
    """
    return load_model()