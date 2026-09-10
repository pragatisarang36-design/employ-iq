"""Django-to-FastAPI client with safe in-process fallback for local demos/tests."""
import os

import httpx

from .inference import predict as local_predict


def predict(snapshot: dict) -> dict:
    service_url = os.getenv("AI_SERVICE_URL", "").rstrip("/")
    if service_url:
        try:
            response = httpx.post(f"{service_url}/predict", json={"snapshot": snapshot}, timeout=8.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            # A missing optional sidecar must not make a local Django-only demo unusable.
            pass
    return local_predict(snapshot)
