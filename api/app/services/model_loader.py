import json
import joblib
from functools import lru_cache
from pathlib import Path
import os
import logging

logger = logging.getLogger("app")

@lru_cache(maxsize=1)
def load_model():
    """
    Load the production-ready model from local file system.
    """
    base_path = None
    model_path = None
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
        else:
            # Fallback if metadata missing
            model_filename = 'california-housing-regressor_latest.pkl'

        # Construct full model path
        model_path = base_path / model_filename

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}")

        # Load the model using joblib
        model = joblib.load(model_path)

        logger.info(
            "model loaded",
            extra={
                "event": "model_loaded",
                "model_path": str(model_path),
            },
        )
        return model

    except Exception as e:
        logger.error(
            "model load failed",
            extra={
                "event": "model_load_failed",
                "model_path": str(model_path) if model_path else None,
                "error": str(e),
            },
            exc_info=True,
        )
        raise
