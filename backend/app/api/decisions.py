from fastapi import APIRouter

from ..domain import decision_service
from ..models.schemas import DecisionApproval, RevisionRequest


router = APIRouter(prefix="/api")


@router.post("/scenarios/{scenario_id}/approve")
def approve_scenario(scenario_id: str, payload: DecisionApproval) -> dict:
    return decision_service.approve_decision(
        scenario_id,
        payload.client_version,
        payload.selected_option,
        payload.approval_note,
    )


@router.post("/scenarios/{scenario_id}/revise")
def revise_scenario(scenario_id: str, payload: RevisionRequest) -> dict:
    return decision_service.revise_scenario(scenario_id, payload.client_version, payload.note)
