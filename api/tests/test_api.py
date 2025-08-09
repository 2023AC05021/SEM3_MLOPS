from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the main app instance
from api.app.main import app

# Create a test client
client = TestClient(app)


def test_health_check():
    """
    Test the health check endpoint.
    Verifies that the /health endpoint returns the expected response.
    """
    # Make a GET request to /health
    response = client.get("/health")
    
    # Assert that the status code is 200 OK
    assert response.status_code == 200
    
    # Assert that the JSON response is {'status': 'ok'}
    assert response.json() == {"status": "ok"}


def test_successful_prediction():
    """
    Test a successful prediction request.
    Verifies that the /predict endpoint accepts valid input and returns a prediction.
    """
    # Define a valid sample input payload for California Housing features
    valid_payload = {
        "MedInc": 8.3252,      # Median income in block group
        "HouseAge": 41.0,      # Median house age in block group
        "AveRooms": 6.984127,  # Average number of rooms per household
        "AveBedrms": 1.02381,  # Average number of bedrooms per household
        "Population": 322.0,   # Block group population
        "AveOccup": 2.555556,  # Average number of household members
        "Latitude": 37.88,     # Block group latitude
        "Longitude": -122.23   # Block group longitude
    }
    
    # Make a POST request to /predict with the valid payload
    response = client.post("/predict", json=valid_payload)
    
    # Assert that the status code is 200 OK
    assert response.status_code == 200
    
    # Get the JSON response
    response_data = response.json()
    
    # Assert that the response contains the key 'predicted_value'
    assert "predicted_value" in response_data
    
    # Assert that the predicted_value is a float
    assert isinstance(response_data["predicted_value"], float)


def test_input_validation_failure():
    """
    Test input validation failure.
    Verifies that the /predict endpoint returns 422 for invalid input.
    """
    # Define an invalid payload (missing required feature 'MedInc')
    invalid_payload = {
        "HouseAge": 41.0,
        "AveRooms": 6.984127,
        "AveBedrms": 1.02381,
        "Population": 322.0,
        "AveOccup": 2.555556,
        "Latitude": 37.88,
        "Longitude": -122.23
        # Missing MedInc field
    }
    
    # Make a POST request to /predict with the invalid payload
    response = client.post("/predict", json=invalid_payload)
    
    # Assert that the status code is 422 Unprocessable Entity
    assert response.status_code == 422


def test_input_validation_wrong_type():
    """
    Additional test for input validation with wrong data types.
    Verifies that the API rejects requests with incorrect data types.
    """
    # Define a payload with wrong data type (string instead of float)
    invalid_type_payload = {
        "MedInc": "invalid_string",  # Should be float
        "HouseAge": 41.0,
        "AveRooms": 6.984127,
        "AveBedrms": 1.02381,
        "Population": 322.0,
        "AveOccup": 2.555556,
        "Latitude": 37.88,
        "Longitude": -122.23
    }
    
    # Make a POST request to /predict with the invalid payload
    response = client.post("/predict", json=invalid_type_payload)
    
    # Assert that the status code is 422 Unprocessable Entity
    assert response.status_code == 422


def test_empty_payload():
    """
    Test with completely empty payload.
    Verifies that the API rejects empty requests.
    """
    # Make a POST request to /predict with empty payload
    response = client.post("/predict", json={})
    
    # Assert that the status code is 422 Unprocessable Entity
    assert response.status_code == 422