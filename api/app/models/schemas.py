from pydantic import BaseModel


class HousingFeatures(BaseModel):
    """
    Pydantic model for California Housing dataset input features.
    Validates the structure and types of incoming prediction requests.
    """
    MedInc: float  # Median income in block group
    HouseAge: float  # Median house age in block group
    AveRooms: float  # Average number of rooms per household
    AveBedrms: float  # Average number of bedrooms per household
    Population: float  # Block group population
    AveOccup: float  # Average number of household members
    Latitude: float  # Block group latitude
    Longitude: float  # Block group longitude

    class Config:
        """
        Pydantic configuration for the HousingFeatures model.
        """
        json_schema_extra = {
            "example": {
                "MedInc": 8.3252,
                "HouseAge": 41.0,
                "AveRooms": 6.984127,
                "AveBedrms": 1.02381,
                "Population": 322.0,
                "AveOccup": 2.555556,
                "Latitude": 37.88,
                "Longitude": -122.23
            }
        }


class PredictionResponse(BaseModel):
    """
    Pydantic model for the prediction response.
    Defines the structure of the API response containing the predicted housing value.
    """
    predicted_value: float  # Predicted median house value

    class Config:
        """
        Pydantic configuration for the PredictionResponse model.
        """
        json_schema_extra = {
            "example": {
                "predicted_value": 4.526
            }
        }
