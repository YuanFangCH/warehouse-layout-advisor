import time

from .conftest import answer_all_questions, create_project, create_scenario


def wait_for_completion(client, evaluation_id: str, timeout: float = 15.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        evaluation = client.get(f"/api/evaluations/{evaluation_id}").json()
        if evaluation["status"] in {"completed", "failed"}:
            return evaluation
        time.sleep(0.2)
    raise AssertionError("evaluation did not finish in time")


def test_full_evaluation_and_approval(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])
    scenario_id = scenario["id"]
    answer_all_questions(client, scenario_id, 1)
    client.post(
        f"/api/scenarios/{scenario_id}/confirm",
        json={"client_version": 1, "confirmed_fields": ["business_objectives"]},
    )

    response = client.post(
        f"/api/scenarios/{scenario_id}/evaluations",
        json={"client_version": 2},
    )
    assert response.status_code == 200
    evaluation = response.json()
    assert evaluation["status"] == "queued"
    evaluation_id = evaluation["id"]

    completed = wait_for_completion(client, evaluation_id)
    assert completed["status"] == "completed"
    assert completed["progress"] == 100

    messages = client.get(f"/api/scenarios/{scenario_id}/messages").json()
    assert any(
        message["role"] == "assistant" and "评估完成" in message["content"]
        for message in messages
    )

    evidence = client.get(f"/api/evaluations/{evaluation_id}/evidence").json()
    assert len(evidence) == 4
    insights = client.get(f"/api/evaluations/{evaluation_id}/insights").json()
    assert len(insights) == 2
    recommendation = client.get(f"/api/evaluations/{evaluation_id}/recommendation").json()
    assert recommendation["recommended_option"] == "layout_B"
    assert recommendation["approval_status"] == "pending"

    scenario = client.get(f"/api/scenarios/{scenario_id}").json()
    assert scenario["status"] == "awaiting_approval"
    assert scenario["latest_evaluation"]["id"] == evaluation_id

    response = client.post(
        f"/api/scenarios/{scenario_id}/approve",
        json={
            "client_version": 2,
            "selected_option": "layout_B",
            "approval_note": "综合考虑效率、预算和实施风险",
        },
    )
    assert response.status_code == 200
    approved = response.json()
    assert approved["status"] == "approved"
    assert approved["version"] == 3

    recommendation = client.get(f"/api/evaluations/{evaluation_id}/recommendation").json()
    assert recommendation["approval_status"] == "approved"

    response = client.post(
        f"/api/scenarios/{scenario_id}/approve",
        json={"client_version": 3, "selected_option": "layout_B", "approval_note": ""},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DECISION_ALREADY_APPROVED"


def test_evaluation_events_are_published(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])
    scenario_id = scenario["id"]
    answer_all_questions(client, scenario_id, 1)
    client.post(
        f"/api/scenarios/{scenario_id}/confirm",
        json={"client_version": 1, "confirmed_fields": ["business_objectives"]},
    )
    evaluation = client.post(
        f"/api/scenarios/{scenario_id}/evaluations",
        json={"client_version": 2},
    ).json()
    wait_for_completion(client, evaluation["id"])
    events = client.get(f"/api/evaluations/{evaluation['id']}/events").json()
    assert events[-1]["type"] == "evaluation.completed"
    assert any(event["type"] == "evaluation.progress" for event in events)
