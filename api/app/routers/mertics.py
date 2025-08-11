from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

router = APIRouter()

REQUEST_COUNT = Counter('prediction_requests', 'Total prediction requests')
SUCCESS_COUNT = Counter('successful_predictions', 'Total successful predictions')

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)