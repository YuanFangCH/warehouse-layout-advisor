from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    warehouse_name: str | None = None
    data_status: str = "可开始分析"


class BusinessObjective(BaseModel):
    code: str
    priority: int


class ScenarioCreate(BaseModel):
    title: str = "新布局分析"


class ScenarioPatch(BaseModel):
    client_version: int
    title: str | None = None
    business_objectives: list[BusinessObjective] | None = None
    modification_scope: str | None = None
    budget_policy: dict[str, Any] | None = None
    performance_floor: dict[str, Any] | None = None
    analysis_period: str | None = None
    risk_preference: str | None = None
    candidate_count: int | None = None
    assumptions: list[str] | None = None


class MessageCreate(BaseModel):
    message: str = Field(min_length=1)
    client_version: int


class ClarificationAnswer(BaseModel):
    answer: str = Field(min_length=1)
    client_version: int


class ConfirmationRequest(BaseModel):
    client_version: int
    confirmed_fields: list[str] = Field(default_factory=list)


class EvaluationStart(BaseModel):
    client_version: int


class DecisionApproval(BaseModel):
    client_version: int
    selected_option: str = Field(min_length=1)
    approval_note: str = ""


class RevisionRequest(BaseModel):
    client_version: int
    note: str = ""
