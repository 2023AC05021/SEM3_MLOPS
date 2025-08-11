from fastapi import APIRouter, HTTPException, Response, Depends, Request
import pandas as pd
from api.app.models.schemas import HousingFeatures, PredictionResponse
from api.app.services.model_loader import load_model
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import logging
import time
from api.app.utils.logging import request_log_context, features_hash

# Initialize APIRouter instance
router = APIRouter()

REQUEST_COUNT = Counter('prediction_requests', 'Total prediction requests')
SUCCESS_COUNT = Counter('successful_predictions', 'Total successful predictions')

logger = logging.getLogger("app")

@router.post("/predict", response_model=PredictionResponse)
async def predict_housing_price(
    features: HousingFeatures,
    ctx: dict = Depends(request_log_context),
    request: Request = None,
):
    """
    Predict housing price based on input features.
    """
    start = time.perf_counter()
    REQUEST_COUNT.inc()

    # Build features hash with ordered keys to be deterministic
    ordered_keys = ['MedInc', 'HouseAge', 'AveRooms', 'AveBedrms', 'Population', 'AveOccup', 'Latitude', 'Longitude']
    feat_dict = features.dict()
    fhash = features_hash(feat_dict, ordered_keys=ordered_keys)

    # Log request received
    logger.info(
        "prediction request received",
        extra={
            "event": "prediction_request_received",
            "request_id": ctx.get("request_id"),
            "client_ip": ctx.get("client_ip"),
            "route": ctx.get("route"),
            "method": ctx.get("method"),
            "features_hash": fhash,
        },
    )

    try:
        # Load the cached model
        model = load_model()

        # Convert to DataFrame
        df = pd.DataFrame([feat_dict])

        # Feature engineering
        df['rooms_per_person'] = df['AveRooms'] / df['Population']

        # Ensure expected column order
        expected_columns = ['MedInc', 'HouseAge', 'AveRooms', 'AveBedrms',
                            'Population', 'AveOccup', 'Latitude', 'Longitude',
                            'rooms_per_person']
        df = df[expected_columns]

        # Make prediction
        prediction = model.predict(df)
        predicted_value = float(prediction)

        SUCCESS_COUNT.inc()

        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "prediction completed",
            extra={
                "event": "prediction_completed",
                "request_id": ctx.get("request_id"),
                "client_ip": ctx.get("client_ip"),
                "route": ctx.get("route"),
                "method": ctx.get("method"),
                "status_code": 200,
                "latency_ms": latency_ms,
                "features_hash": fhash,
                "predicted_value": predicted_value,
            },
        )

        return PredictionResponse(predicted_value=predicted_value)

    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.error(
            "prediction failed",
            extra={
                "event": "prediction_failed",
                "request_id": ctx.get("request_id"),
                "client_ip": ctx.get("client_ip"),
                "route": ctx.get("route"),
                "method": ctx.get("method"),
                "status_code": 500,
                "latency_ms": latency_ms,
                "features_hash": fhash,
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
