from fastapi import APIRouter, HTTPException
import pandas as pd
from api.app.models.schemas import HousingFeatures, PredictionResponse
from api.app.services.model_loader import load_model

# Initialize APIRouter instance
router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict_housing_price(features: HousingFeatures):
    """
    Predict housing price based on input features.

    This endpoint takes housing features and returns a predicted median house value.
    It applies the same feature engineering as done during training to avoid
    training-serving skew.

    Args:
        features (HousingFeatures): Input features for prediction
    
    Returns:
        PredictionResponse: Contains the predicted housing value

    Raises:
        HTTPException: If prediction fails
    """
    try:
        # Load the cached model
        model = load_model()
 
        # Convert Pydantic model to dictionary, then to pandas DataFrame
        features_dict = features.dict()
        df = pd.DataFrame([features_dict])

        # CRUCIAL: Apply the same feature engineering as in Phase 2
        # Create rooms_per_person feature to match training preprocessing
        df['rooms_per_person'] = df['AveRooms'] / df['Population']

        # Ensure the DataFrame has the expected column order for the model
        # (This should match the feature order used during training)
        expected_columns = ['MedInc', 'HouseAge', 'AveRooms', 'AveBedrms', 
                            'Population', 'AveOccup', 'Latitude', 'Longitude', 
                            'rooms_per_person']
        df = df[expected_columns]
        
        # Make prediction using the loaded model
        prediction = model.predict(df)
        
        # Extract the predicted value (assuming single prediction)
        predicted_value = float(prediction[0])
        
        # Return the prediction wrapped in PredictionResponse
        return PredictionResponse(predicted_value=predicted_value)
        
    except Exception as e:
        # Handle any errors during prediction
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )
