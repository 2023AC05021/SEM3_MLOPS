from __future__ import annotations
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from hashlib import sha256
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Any, Dict
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

SERVICE_NAME = os.getenv("SERVICE_NAME", "california_housing_api")
APP_ENV = os.getenv("APP_ENV", os.getenv("ENV", "production"))
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
LOG_ROTATION = os.getenv("LOG_ROTATION", "size")  # "size" or "time"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Default exclude paths: /health and /metrics; override via env var
if os.getenv("LOG_EXCLUDE_PATHS"):
    obj = (p.strip() for p in os.getenv("LOG_EXCLUDE_PATHS").split(",") if p.strip())
    EXCLUDE_PATHS = set(obj)
else:
    EXCLUDE_PATHS = {"/health", "/metrics"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "env": APP_ENV,
            "message": record.getMessage(),
        }
        for key in (
            "request_id", "client_ip", "route", "method", "status_code",
            "latency_ms", "event", "features_hash", "predicted_value", "error",
            "model_path"
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        payload["logger"] = record.name
        if record.exc_info:
            obj = payload.get("error") or self.formatException(record.exc_info)
            payload["error"] = obj
        return json.dumps(payload, ensure_ascii=False)


def ensure_log_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass


def build_file_handler() -> logging.Handler:
    ensure_log_dir(LOG_DIR)
    formatter = JsonFormatter()
    if LOG_ROTATION == "time":
        handler = TimedRotatingFileHandler(
                                            LOG_FILE, when="D", 
                                            interval=1, backupCount=7, 
                                            encoding="utf-8")
    else:
        max_bytes = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", 5))
        handler = RotatingFileHandler(
                                        LOG_FILE, maxBytes=max_bytes, 
                                        backupCount=backup_count, 
                                        encoding="utf-8")
    handler.setFormatter(formatter)
    return handler


def build_stdout_handler() -> logging.Handler:
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    return handler


def init_logging() -> logging.Logger:
    logger = logging.getLogger("app")
    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        file_handler = build_file_handler()
        stdout_handler = build_stdout_handler()
        logger.addHandler(file_handler)
        logger.addHandler(stdout_handler)
        logger.propagate = False

        # Redirect uvicorn loggers to use same handlers
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            ulogger = logging.getLogger(name)
            ulogger.handlers = []
            ulogger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
            ulogger.addHandler(file_handler)
            ulogger.addHandler(stdout_handler)
            ulogger.propagate = False
    return logger


def client_ip_from_request(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Take first IP, strip spaces
        return xff.split(",")[0].strip()
    xrip = request.headers.get("x-real-ip")
    if xrip:
        return xrip.strip()
    if request.client:
        return request.client.host
    return ""


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, logger: logging.Logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            latency_ms = int((time.perf_counter() - start) * 1000)
            if response is not None:
                response.headers["X-Request-ID"] = request_id

            if path in EXCLUDE_PATHS:
                return response

            extra = {
                "request_id": request_id,
                "client_ip": client_ip_from_request(request),
                "route": path,
                "method": request.method,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "event": "request_completed",
            }
            self.logger.info("request completed", extra=extra)


# Dependency to provide logging context in routes (Phase 2)
async def request_log_context(request: Request) -> Dict[str, Any]:
    ctx = {
        "request_id": getattr(request.state, "request_id", None),
        "client_ip": client_ip_from_request(request),
        "route": request.url.path,
        "method": request.method,
    }
    return ctx


# Privacy-safe features hash helper (Phase 2 utility, ready for Phase 3)
def features_hash(
                    payload: Dict[str, Any], 
                    ordered_keys: Optional[list[str]] = None) -> str:
    if ordered_keys:
        data = {k: payload.get(k) for k in ordered_keys}
    else:
        # Sort keys to be deterministic
        data = {k: payload[k] for k in sorted(payload.keys())}
    as_json = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    return sha256(as_json.encode("utf-8")).hexdigest()[:16]
