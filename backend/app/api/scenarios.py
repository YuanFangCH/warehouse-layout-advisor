from fastapi import APIRouter, status

from ..domain import scenario_service
from ..models.schemas import ConfirmationRequest, ScenarioCreate, ScenarioPatch


router = APIRouter(prefix="/api")


@router.get("/projects/{project_id}/scenarios")
def list_scenarios(project_id: str) -> list[dict]:
    return scenario_service.list_scenarios(project_id)


@router.post("/projects/{project_id}/scenarios", status_code=status.HTTP_201_CREATED)
def create_scenario(project_id: str, payload: ScenarioCreate) -> dict:
    return scenario_service.create_scenario(project_id, payload.title)


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict:
    return scenario_service.get_scenario(scenario_id)


@router.patch("/scenarios/{scenario_id}")
def patch_scenario(scenario_id: str, payload: ScenarioPatch) -> dict:
    return scenario_service.update_scenario(scenario_id, payload.model_dump(), payload.client_version)


@router.post("/scenarios/{scenario_id}/confirm")
def confirm_scenario(scenario_id: str, payload: ConfirmationRequest) -> dict:
    return scenario_service.confirm_scenario(scenario_id, payload.client_version, payload.confirmed_fields)


@router.get("/scenarios/{scenario_id}/versions")
def list_versions(scenario_id: str) -> list[dict]:
    return scenario_service.list_versions(scenario_id)


@router.get("/scenarios/{scenario_id}/events")
def list_events(scenario_id: str) -> list[dict]:
    return scenario_service.list_events(scenario_id)
