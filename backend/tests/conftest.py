import os
import tempfile
from pathlib import Path


os.environ["WAREHOUSE_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test_warehouse.db")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.persistence.database import init_db


@pytest.fixture()
def client():
    init_db()
    with TestClient(app) as test_client:
        yield test_client


def create_project(client) -> dict:
    response = client.post("/api/projects", json={"name": "测试仓", "warehouse_name": "测试仓"})
    assert response.status_code == 201
    return response.json()


def create_scenario(client, project_id: str) -> dict:
    response = client.post(
        f"/api/projects/{project_id}/scenarios",
        json={"title": "降低拣选距离"},
    )
    assert response.status_code == 201
    return response.json()


def answer_all_questions(client, scenario_id: str, client_version: int) -> dict:
    answers = {
        "modification_scope": "仅调整货位，不移动货架和主通道",
        "priority": "优先降低拣选距离，成本在预算内尽量控制",
        "performance_floor": "是，吞吐量不得低于当前布局",
        "budget_policy": "30 万元，硬约束",
    }
    pending = client.get(f"/api/scenarios/{scenario_id}/clarifications").json()
    if not pending:
        response = client.post(
            f"/api/scenarios/{scenario_id}/messages",
            json={
                "message": "尽量少改现有仓库，优先降低拣选距离，预算控制在 20 万元。",
                "client_version": client_version,
            },
        )
        assert response.status_code == 200
    for _ in range(10):
        pending = client.get(f"/api/scenarios/{scenario_id}/clarifications").json()
        if not pending:
            break
        question_id = pending[0]["id"]
        answer = answers.get(pending[0]["key"]) or pending[0]["options"][0]
        response = client.post(
            f"/api/scenarios/{scenario_id}/clarifications/{question_id}/answer",
            json={"answer": answer, "client_version": client_version},
        )
        assert response.status_code == 200
    return client.get(f"/api/scenarios/{scenario_id}").json()
