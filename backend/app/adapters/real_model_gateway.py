import os

import httpx

from ..errors import AppError


class RealModelGateway:
    """HTTP client for a future real model service.

    The backend remains the only component that talks to the model service.
    Point MODEL_SERVICE_URL at the deployed model API and replace the mock
    gateway in the workflow runner.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or os.environ.get("MODEL_SERVICE_URL", "")

    def evaluate_layout(self, scenario: dict) -> dict:
        if not self.base_url:
            raise AppError(
                "MODEL_SERVICE_UNAVAILABLE",
                "模型服务暂不可用，请检查 MODEL_SERVICE_URL",
                status_code=503,
            )
        response = httpx.post(
            f"{self.base_url}/evaluate-layout",
            json={"scenario": scenario},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
