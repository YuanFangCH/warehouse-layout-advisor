import json as jsonlib

import httpx
import pytest

from app.adapters.mock_model_gateway import MockModelGateway
from app.adapters.opencode_model_gateway import (
    DEFAULT_API_URL,
    OpenCodeModelGateway,
    normalize_result,
)
from app.errors import AppError
from app.orchestration.workflow_runner import build_model_gateway


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def fake_client_factory(captured: dict, payload_factory):
    class FakeClient:
        def __init__(self, transport=None, timeout=None):
            captured["transport"] = transport
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, json=None, headers=None, timeout=None):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return FakeResponse(payload_factory())

    return FakeClient


def completion_response(content: str) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                }
            }
        ]
    }


def sample_payload() -> dict:
    return {
        "schemes": [
            {"id": "layout_A", "label": "方案 A", "note": "效率优先", "score": 92},
            {"id": "layout_B", "label": "方案 B", "note": "综合平衡", "score": 88},
        ],
        "kpis": [
            {
                "metric": "拣选距离",
                "baseline": "100.0 m/order",
                "candidate": "85.2 m/order",
                "delta": "-14.8%",
                "entity": "整体拣选路径",
                "type": "直接观测",
                "confidence": "high",
            }
        ],
        "insights": [
            {
                "id": "insight_001",
                "type": "tradeoff",
                "title": "方案 B 更适合落地",
                "business_explanation": "成本与效率更平衡",
                "evidence_refs": ["evidence_001"],
                "confidence": "high",
            }
        ],
        "recommendation": {
            "recommended_option": "layout_B",
            "alternative_options": ["layout_A"],
            "reasons": ["效率提升"],
            "tradeoffs": ["改造范围更大"],
            "risks": ["依赖历史数据"],
            "assumptions": ["最近 30 天订单"],
        },
    }


def test_gateway_posts_chat_completions_payload(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        httpx,
        "Client",
        fake_client_factory(captured, lambda: completion_response(jsonlib.dumps(sample_payload(), ensure_ascii=False))),
    )
    gateway = OpenCodeModelGateway(
        api_key="test-key",
        api_url="https://opencode.example/v1/chat/completions",
        model="deepseek-v4-flash",
    )
    scenario = {"id": "scenario_1", "title": "降低拣选距离", "created_at": "2026-08-15T00:00:00Z"}

    result = gateway.evaluate_layout(scenario)

    assert captured["url"] == "https://opencode.example/v1/chat/completions"
    assert captured["transport"] is not None
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["model"] == "deepseek-v4-flash"
    assert captured["json"]["temperature"] == 0.2
    assert captured["json"]["messages"][0]["role"] == "system"
    user_content = jsonlib.loads(captured["json"]["messages"][1]["content"])
    assert user_content["id"] == "scenario_1"
    assert result["schemes"][0]["label"] == "方案 A"
    assert result["recommendation"]["recommended_option"] == "layout_B"


def test_gateway_uses_defaults_from_environment(monkeypatch):
    monkeypatch.setenv("OPENCODE_API_KEY", "env-key")
    monkeypatch.setenv("OPENCODE_API_URL", "https://env.example/v1/chat/completions")
    monkeypatch.setenv("OPENCODE_MODEL", "env-model")
    gateway = OpenCodeModelGateway()
    assert gateway.api_key == "env-key"
    assert gateway.api_url == "https://env.example/v1/chat/completions"
    assert gateway.model == "env-model"
    monkeypatch.delenv("OPENCODE_API_KEY")
    monkeypatch.delenv("OPENCODE_API_URL")
    monkeypatch.delenv("OPENCODE_MODEL")
    default_gateway = OpenCodeModelGateway()
    assert default_gateway.api_url == DEFAULT_API_URL
    assert default_gateway.model == "deepseek-v4-flash"


def test_gateway_parses_markdown_fenced_json(monkeypatch):
    fenced = "```json\n" + jsonlib.dumps(sample_payload(), ensure_ascii=False) + "\n```"

    monkeypatch.setattr(httpx, "Client", fake_client_factory({}, lambda: completion_response(fenced)))
    gateway = OpenCodeModelGateway(api_key="test-key")
    result = gateway.evaluate_layout({"title": "测试"})
    assert result["kpis"][0]["metric"] == "拣选距离"
    assert result["insights"][0]["title"] == "方案 B 更适合落地"


def test_normalize_result_fills_aliases_and_defaults():
    raw = {
        "schemes": [{"id": "s1", "score": "90"}],
        "kpis": [
            {
                "name": "吞吐量",
                "baseline_value": "1,000",
                "candidate_value": "1,084",
                "delta": "+8.4%",
                "entity": "仓库整体",
            }
        ],
        "recommendation": {"recommended_option": "missing"},
    }
    result = normalize_result(raw)
    assert result["schemes"][0]["id"] == "s1"
    assert result["kpis"][0]["metric"] == "吞吐量"
    assert result["kpis"][0]["baseline"] == "1,000"
    assert result["kpis"][0]["confidence"] == "medium"
    assert result["recommendation"]["recommended_option"] == "s1"
    assert result["recommendation"]["alternative_options"] == []
    assert result["recommendation"]["reasons"] == []
    assert result["insights"] == []


def test_gateway_raises_when_api_key_missing():
    gateway = OpenCodeModelGateway(api_key="")
    with pytest.raises(AppError) as exc_info:
        gateway.evaluate_layout({"title": "测试"})
    assert exc_info.value.code == "MODEL_SERVICE_UNAVAILABLE"


def test_gateway_raises_on_http_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise httpx.ConnectError("network down", request=None)

    captured = {}
    client_cls = fake_client_factory(captured, lambda: {})
    client_cls.post = raise_error
    monkeypatch.setattr(httpx, "Client", client_cls)
    gateway = OpenCodeModelGateway(api_key="test-key")
    with pytest.raises(AppError) as exc_info:
        gateway.evaluate_layout({"title": "测试"})
    assert exc_info.value.status_code == 502


def test_gateway_raises_on_invalid_json(monkeypatch):
    monkeypatch.setattr(httpx, "Client", fake_client_factory({}, lambda: completion_response("not json at all")))
    gateway = OpenCodeModelGateway(api_key="test-key")
    with pytest.raises(AppError):
        gateway.evaluate_layout({"title": "测试"})


def test_gateway_can_disable_force_ipv4(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        httpx,
        "Client",
        fake_client_factory(captured, lambda: completion_response(jsonlib.dumps(sample_payload(), ensure_ascii=False))),
    )
    gateway = OpenCodeModelGateway(api_key="test-key", force_ipv4=False)
    gateway.evaluate_layout({"title": "测试"})
    assert captured["transport"] is None


def test_build_model_gateway_selects_open_code_when_key_set(monkeypatch):
    monkeypatch.setenv("OPENCODE_API_KEY", "test-key")
    assert isinstance(build_model_gateway(), OpenCodeModelGateway)
    monkeypatch.delenv("OPENCODE_API_KEY")
    assert isinstance(build_model_gateway(), MockModelGateway)
