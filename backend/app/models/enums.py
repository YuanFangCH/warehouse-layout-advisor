from enum import StrEnum


class ScenarioStatus(StrEnum):
    COLLECTING = "collecting"
    CLARIFYING = "clarifying"
    READY = "ready"
    EVALUATING = "evaluating"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REVISED = "revised"


class EvaluationStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_DATA = "MISSING_DATA"
    SCENARIO_VERSION_CONFLICT = "SCENARIO_VERSION_CONFLICT"
    MODEL_SERVICE_UNAVAILABLE = "MODEL_SERVICE_UNAVAILABLE"
    EVALUATION_TIMEOUT = "EVALUATION_TIMEOUT"
    NO_FEASIBLE_SCENARIO = "NO_FEASIBLE_SCENARIO"
    RECOMMENDATION_UNCERTAIN = "RECOMMENDATION_UNCERTAIN"
    DECISION_ALREADY_APPROVED = "DECISION_ALREADY_APPROVED"
