from .conftest import create_project


def test_unified_error_contract(client):
    response = client.get("/api/scenarios/not_exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SCENARIO_NOT_FOUND"

    response = client.get("/api/evaluations/not_exist/evidence")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVALUATION_NOT_FOUND"

    response = client.post("/api/projects", json={"name": ""})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    project = create_project(client)
    scenario = client.post(
        f"/api/projects/{project['id']}/scenarios",
        json={"title": "测试"},
    ).json()
    response = client.post(
        f"/api/scenarios/{scenario['id']}/messages",
        json={"message": "", "client_version": 1},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
