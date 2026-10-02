from .conftest import answer_all_questions, create_project, create_scenario


def test_version_conflict_contract(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])

    response = client.patch(
        f"/api/scenarios/{scenario['id']}",
        json={"client_version": 99, "risk_preference": "balance"},
    )
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "SCENARIO_VERSION_CONFLICT"
    assert body["error"]["details"]["server_version"] == 1
    assert body["error"]["details"]["client_version"] == 99


def test_revise_creates_new_version(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])
    scenario_id = scenario["id"]
    answer_all_questions(client, scenario_id, 1)
    client.post(
        f"/api/scenarios/{scenario_id}/confirm",
        json={"client_version": 1, "confirmed_fields": ["business_objectives"]},
    )

    response = client.post(
        f"/api/scenarios/{scenario_id}/revise",
        json={"client_version": 2, "note": "追加旺季压力测试"},
    )
    assert response.status_code == 200
    revised = response.json()
    assert revised["status"] == "ready"
    assert revised["version"] == 3

    versions = client.get(f"/api/scenarios/{scenario_id}/versions").json()
    assert versions[-1]["note"] == "调整条件重算"
