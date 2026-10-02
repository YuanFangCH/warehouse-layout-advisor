import json
import time

from .conftest import answer_all_questions, create_project, create_scenario
from app.adapters.opencode_conversation_gateway import (
    OpenCodeConversationGateway,
    normalize_clarification,
    normalize_conditions_patch,
)
from app.domain.translation_service import parse_budget_amount, translate_message
from app.domain.explanation_service import explain_results


def test_parse_budget_amount_handles_wan_and_yuan():
    assert parse_budget_amount("预算提高到 30 万元") == 300000
    assert parse_budget_amount("预算控制在 20万") == 200000
    assert parse_budget_amount("上限 250000 元") == 250000
    assert parse_budget_amount("尽量少改现有仓库") is None


def test_translate_message_preserves_existing_budget_mode():
    scenario = {"budget_policy": {"amount": 200000, "mode": "soft_limit"}}
    patch = translate_message("预算提高到 30 万元", scenario)
    assert patch["budget_policy"] == {"amount": 300000, "mode": "soft_limit"}


def test_translate_message_extracts_conditions():
    patch = translate_message(
        "尽量少改现有仓库，优先降低拣选距离，预算控制在 20 万元，吞吐量不能下降，出 3 个方案"
    )
    assert patch["budget_policy"]["amount"] == 200000
    assert patch["modification_scope"] == "仅调整货位，不移动货架和主通道"
    assert patch["performance_floor"]["throughput"] == "not_below_baseline"
    assert patch["candidate_count"] == 3
    assert patch["business_objectives"][0]["code"] == "minimize_picking_distance"


def test_confirm_preserves_chat_budget_amount(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])
    scenario_id = scenario["id"]
    client.post(
        f"/api/scenarios/{scenario_id}/messages",
        json={
            "message": "预算控制在 30 万元，不动货架，吞吐量不能下降",
            "client_version": 1,
        },
    )
    answer_all_questions(client, scenario_id, 1)
    confirmed = client.post(
        f"/api/scenarios/{scenario_id}/confirm",
        json={"client_version": 1, "confirmed_fields": ["budget_policy"]},
    ).json()
    assert confirmed["status"] == "ready"
    assert confirmed["budget_policy"]["amount"] == 300000
    assert confirmed["budget_policy"]["mode"] == "hard_limit"


def test_chat_update_on_ready_scenario_bumps_version_and_syncs(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])
    scenario_id = scenario["id"]
    client.post(
        f"/api/scenarios/{scenario_id}/messages",
        json={
            "message": "预算控制在 30 万元，不动货架，吞吐量不能下降",
            "client_version": 1,
        },
    )
    answer_all_questions(client, scenario_id, 1)
    client.post(
        f"/api/scenarios/{scenario_id}/confirm",
        json={"client_version": 1, "confirmed_fields": ["budget_policy"]},
    )

    response = client.post(
        f"/api/scenarios/{scenario_id}/messages",
        json={"message": "预算提高到 40 万元", "client_version": 2},
    )
    assert response.status_code == 200
    body = response.json()
    updated = body["scenario"]
    assert updated["version"] == 3
    assert updated["status"] == "ready"
    assert updated["budget_policy"]["amount"] == 400000
    assert body["sync_message"] and "预算政策" in body["sync_message"]


def test_normalize_interpretation_helpers():
    patch = normalize_conditions_patch(
        {
            "budget_policy": {"amount": "300000", "mode": "hard_limit"},
            "business_objectives": [{"code": "minimize_picking_distance", "priority": "1"}],
            "candidate_count": "3",
            "unknown_key": "ignored",
        }
    )
    assert patch["budget_policy"] == {"amount": 300000, "mode": "hard_limit"}
    assert patch["candidate_count"] == 3
    assert "unknown_key" not in patch
    clarification = normalize_clarification(
        {
            "key": "priority",
            "question": "距离和成本哪个优先？",
            "options": ["优先距离", "优先成本"],
        }
    )
    assert clarification["key"] == "priority"
    assert normalize_clarification({"key": "unknown", "question": "x", "options": ["a", "b"]}) is None


def test_conversation_gateway_parses_model_output(monkeypatch):
    captured = {}

    def fake_chat_completion(
        api_key,
        api_url,
        model,
        messages,
        temperature=0.3,
        timeout=60.0,
        force_ipv4=True,
    ):
        captured["api_key"] = api_key
        captured["model"] = model
        captured["messages"] = messages
        return json.dumps(
            {
                "reply": "我把预算更新为 30 万元，还需要确认改造范围。",
                "conditions_patch": {"budget_policy": {"amount": 300000, "mode": "pending"}},
                "clarification": {
                    "key": "modification_scope",
                    "question": "“尽量少改”具体指哪种？",
                    "options": ["仅调货位", "允许局部移动", "重新设计"],
                },
                "confidence": "high",
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr("app.adapters.opencode_conversation_gateway.chat_completion", fake_chat_completion)
    gateway = OpenCodeConversationGateway(api_key="test-key")
    result = gateway.interpret({"title": "降低拣选距离"}, "预算 30 万，尽量少改")
    assert captured["api_key"] == "test-key"
    assert captured["model"] == "deepseek-v4-flash"
    assert result["conditions_patch"]["budget_policy"]["amount"] == 300000
    assert result["clarification"]["key"] == "modification_scope"
    assert "预算" in result["reply"]


def test_explanation_question_uses_results_without_touching_conditions(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])
    scenario_id = scenario["id"]
    client.post(
        f"/api/scenarios/{scenario_id}/messages",
        json={
            "message": "预算控制在 30 万元，不动货架，优先降低拣选距离，吞吐量不能下降",
            "client_version": 1,
        },
    )
    scenario = client.get(f"/api/scenarios/{scenario_id}").json()
    evaluation = client.post(
        f"/api/scenarios/{scenario_id}/evaluations",
        json={"client_version": scenario["version"]},
    ).json()

    deadline = time.time() + 15
    while time.time() < deadline:
        current = client.get(f"/api/evaluations/{evaluation['id']}").json()
        if current["status"] in {"completed", "failed"}:
            break
        time.sleep(0.2)
    assert current["status"] == "completed"

    response = client.post(
        f"/api/scenarios/{scenario_id}/messages",
        json={"message": "为什么推荐这个方案？", "client_version": scenario["version"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer_kind"] == "explanation"
    assert body["business_patch"] == {}
    assert body["sync_message"] is None
    assert body["pending_questions"] == []
    assert "推荐" in body["assistant_message"]["content"] or "理由" in body["assistant_message"]["content"]
    assert body["scenario"]["version"] == scenario["version"]


def test_explanation_question_without_results_explains_status(client):
    project = create_project(client)
    scenario = create_scenario(client, project["id"])
    response = client.post(
        f"/api/scenarios/{scenario['id']}/messages",
        json={"message": "硬约束和软约束有什么区别？", "client_version": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer_kind"] == "explanation"
    assert "还没有完成评估" in body["assistant_message"]["content"]
    assert body["business_patch"] == {}


def test_explanation_gateway_parses_model_output(monkeypatch):
    captured = {}

    def fake_chat_completion(
        api_key,
        api_url,
        model,
        messages,
        temperature=0.3,
        timeout=60.0,
        force_ipv4=True,
    ):
        captured["api_key"] = api_key
        captured["messages"] = messages
        return json.dumps({"reply": "推荐方案 B 是因为它距离降幅大、成本低且风险小。", "confidence": "high"}, ensure_ascii=False)

    monkeypatch.setenv("OPENCODE_API_KEY", "test-key")
    monkeypatch.setattr("app.adapters.opencode_conversation_gateway.chat_completion", fake_chat_completion)
    result = explain_results(
        {"budget_policy": {"amount": 200000, "mode": "hard_limit"}},
        "为什么推荐方案 B？",
        {"results": {"schemes": [], "recommendation": {}}},
    )
    assert captured["api_key"] == "test-key"
    assert "推荐方案 B" in result["reply"]
    assert result["confidence"] == "high"
