from typing import Protocol


class ModelGateway(Protocol):
    def evaluate_layout(self, scenario: dict) -> dict: ...
