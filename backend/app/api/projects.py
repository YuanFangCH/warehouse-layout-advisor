from fastapi import APIRouter, status

from ..domain import scenario_service
from ..models.schemas import ProjectCreate


router = APIRouter(prefix="/api")


@router.get("/projects")
def list_projects() -> list[dict]:
    return scenario_service.list_projects()


@router.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate) -> dict:
    return scenario_service.create_project(payload.name, payload.warehouse_name, payload.data_status)


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> dict:
    return scenario_service.get_project(project_id)
