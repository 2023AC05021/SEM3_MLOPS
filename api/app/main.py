from fastapi import FastAPI
from api.app.routers.prediction import router as prediction_router
from api.app.utils.logging import init_logging, RequestContextMiddleware

# Initialize logger first
logger = init_logging()

# Initialize FastAPI app instance
app = FastAPI(
    title="California Housing Model API",
    description="API for serving California Housing price predictions",
    version="1.0.0"
)

# Middleware for request ID, latency logging, and response header
app.add_middleware(RequestContextMiddleware, logger=logger)

# Include the prediction router
app.include_router(prediction_router, tags=["predictions"])

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the application is running.
    Used by deployment tools and monitoring systems.
    """
    return {"status": "ok"}
