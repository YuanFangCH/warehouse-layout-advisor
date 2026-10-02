from .conftest import answer_all_questions, create_project, create_scenario


def test_clarification_and_confirm_flow(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])
    scenario_id = scenario["id"]
    assert scenario["status"] == "collecting"
    assert scenario["version"] == 1

    response = client.post(
        f"/api/scenarios/{scenario_id}/messages",
        json={
            "message": "尽量少改现有仓库，优先降低拣选距离，预算控制在 20 万元。",
            "client_version": 1,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"]["status"] == "clarifying"
    assert len(payload["pending_questions"]) == 1
    assert payload["business_patch"]["business_objectives"]

    updated = answer_all_questions(client, scenario_id, 1)
    assert updated["modification_scope"].startswith("仅调整货位")
    assert updated["business_objectives"][0]["code"] == "minimize_picking_distance"
    assert updated["performance_floor"]["throughput"] == "not_below_baseline"

    response = client.post(
        f"/api/scenarios/{scenario_id}/confirm",
        json={
            "client_version": 1,
            "confirmed_fields": [
                "business_objectives",
                "modification_scope",
                "budget_policy",
                "performance_floor",
            ],
        },
    )
    assert response.status_code == 200
    confirmed = response.json()
    assert confirmed["status"] == "ready"
    assert confirmed["version"] == 2
    assert confirmed["budget_policy"]["mode"] == "hard_limit"

    versions = client.get(f"/api/scenarios/{scenario_id}/versions").json()
    assert [item["version"] for item in versions] == [1, 2]
    assert versions[-1]["note"] == "确认业务分析条件"

    messages = client.get(f"/api/scenarios/{scenario_id}/messages").json()
    roles = [message["role"] for message in messages]
    assert "user" in roles and "assistant" in roles


def test_confirm_blocks_pending_questions(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])
    response = client.post(
        f"/api/scenarios/{scenario['id']}/messages",
        json={"message": "降低拣选距离", "client_version": 1},
    )
    assert response.status_code == 200

    response = client.post(
        f"/api/scenarios/{scenario['id']}/confirm",
        json={"client_version": 1, "confirmed_fields": []},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PENDING_CLARIFICATIONS"
