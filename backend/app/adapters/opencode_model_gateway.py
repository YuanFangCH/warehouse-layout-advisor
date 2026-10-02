import json
import os
from typing import Any

import httpx

from ..errors import AppError

DEFAULT_API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"

SYSTEM_PROMPT = """你是仓储布局决策参谋。你接收一个结构化的布局分析场景，返回一份可直接入库的评估结果。

要求：
1. 只输出一个 JSON 对象，不要 Markdown 代码块，不要解释性文字。
2. JSON 必须包含四个字段：
- schemes: 候选布局方案数组，每项含 id、label、note、score（0-100 整数，越高越优）。
- kpis: 关键指标数组，每项含 metric、baseline、candidate、delta、entity、type、confidence（high/medium/low）。
- insights: 洞察数组，每项含 id、type、title、business_explanation、evidence_refs、confidence；type 取 statistical_attribution、tradeoff、risk、recommendation 之一。
- recommendation: 推荐对象，含 recommended_option（必须引用某个 schemes.id）、alternative_options、reasons、tradeoffs、risks、assumptions。
3. 业务解释使用简体中文，字段名保持英文小写。
4. delta 用字符串表达变化，例如 "-14.8%"；金额使用元，单位保留在字符串内。
5. 方案数量与场景中的 candidate_count 一致，推荐方案必须出现在候选列表中。
"""


def _text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_text(item) for item in value if item is not None]
    if value:
        return [_text(value)]
    return []


def _score(value: Any, fallback: int = 0) -> int:
    if isinstance(value, bool) or value is None:
        return fallback
    if isinstance(value, int):
        return value
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def _scheme(item: Any, index: int) -> dict:
    raw = item if isinstance(item, dict) else {}
    return {
        "id": _text(raw.get("id") or f"layout_{index + 1}"),
        "label": _text(raw.get("label") or f"方案 {index + 1}"),
        "note": _text(raw.get("note")),
        "score": _score(raw.get("score")),
    }


def _kpi(item: Any) -> dict:
    raw = item if isinstance(item, dict) else {}
    return {
        "metric": _text(raw.get("metric") or raw.get("name") or "未命名指标"),
        "baseline": _text(raw.get("baseline") or raw.get("baseline_value") or raw.get("baselineValue")),
        "candidate": _text(raw.get("candidate") or raw.get("candidate_value") or raw.get("candidateValue")),
        "delta": _text(raw.get("delta")),
        "entity": _text(raw.get("entity")),
        "type": _text(raw.get("type") or raw.get("explanation_type") or "直接观测"),
        "confidence": _text(raw.get("confidence") or "medium"),
    }


def _insight(item: Any, index: int) -> dict:
    raw = item if isinstance(item, dict) else {}
    return {
        "id": _text(raw.get("id") or f"insight_{index + 1:03d}"),
        "type": _text(raw.get("type") or "statistical_attribution"),
        "title": _text(raw.get("title") or f"洞察 {index + 1}"),
        "business_explanation": _text(raw.get("business_explanation") or raw.get("explanation")),
        "evidence_refs": _string_list(raw.get("evidence_refs")),
        "confidence": _text(raw.get("confidence") or "medium"),
    }


def _recommendation(value: Any, schemes: list[dict]) -> dict:
    raw = value if isinstance(value, dict) else {}
    options = [scheme["id"] for scheme in schemes]
    recommended = _text(raw.get("recommended_option"))
    if recommended not in options and options:
        recommended = options[0]
    alternatives = [
        option for option in _string_list(raw.get("alternative_options"))
        if option in options and option != recommended
    ]
    if not alternatives:
        alternatives = [option for option in options if option != recommended]
    return {
        "recommended_option": recommended,
        "alternative_options": alternatives,
        "reasons": _string_list(raw.get("reasons")),
        "tradeoffs": _string_list(raw.get("tradeoffs")),
        "risks": _string_list(raw.get("risks")),
        "assumptions": _string_list(raw.get("assumptions")),
    }


def normalize_result(data: Any) -> dict:
    raw = data if isinstance(data, dict) else {}
    raw_schemes = raw.get("schemes")
    if not isinstance(raw_schemes, list):
        raw_schemes = []
    schemes = [_scheme(item, index) for index, item in enumerate(raw_schemes)]
    if not schemes:
        raise AppError(
            "MODEL_SERVICE_UNAVAILABLE",
            "OpenCode Go 返回结果缺少候选方案 schemes",
            status_code=502,
        )
    raw_kpis = raw.get("kpis")
    raw_insights = raw.get("insights")
    if not isinstance(raw_kpis, list):
        raw_kpis = []
    if not isinstance(raw_insights, list):
        raw_insights = []
    return {
        "schemes": schemes,
        "kpis": [_kpi(item) for item in raw_kpis],
        "insights": [_insight(item, index) for index, item in enumerate(raw_insights)],
        "recommendation": _recommendation(raw.get("recommendation"), schemes),
    }


def _extract_content(data: Any) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AppError(
            "MODEL_SERVICE_UNAVAILABLE",
            "OpenCode Go 返回结构缺少 choices[0].message.content",
            status_code=502,
        ) from exc
    if not isinstance(content, str):
        raise AppError(
            "MODEL_SERVICE_UNAVAILABLE",
            "OpenCode Go 返回的 content 不是字符串",
            status_code=502,
        )
    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    return content


def chat_completion(
    api_key: str,
    api_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    timeout: float = 120.0,
    force_ipv4: bool = True,
) -> str:
    """Call an OpenAI-compatible Chat Completions endpoint and return content."""
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": messages,
    }
    transport = httpx.HTTPTransport(local_address="0.0.0.0") if force_ipv4 else None
    try:
        with httpx.Client(transport=transport, timeout=timeout) as client:
            response = client.post(
                api_url,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise AppError(
            "MODEL_SERVICE_UNAVAILABLE",
            f"OpenCode Go 调用失败：{exc}",
            status_code=502,
        ) from exc
    return _extract_content(data)


class OpenCodeModelGateway:
    """OpenAI-compatible Chat Completions gateway backed by OpenCode Go."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
        force_ipv4: bool | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("OPENCODE_API_KEY", "")
        self.api_url = api_url or os.environ.get("OPENCODE_API_URL", DEFAULT_API_URL)
        self.model = model or os.environ.get("OPENCODE_MODEL", DEFAULT_MODEL)
        self.timeout = timeout
        self.force_ipv4 = self._resolve_force_ipv4(force_ipv4)

    @staticmethod
    def _resolve_force_ipv4(value: bool | None) -> bool:
        if value is not None:
            return value
        raw = os.environ.get("OPENCODE_FORCE_IPV4", "1")
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    def evaluate_layout(self, scenario: dict) -> dict:
        if not self.api_key:
            raise AppError(
                "MODEL_SERVICE_UNAVAILABLE",
                "OpenCode Go 未配置 OPENCODE_API_KEY",
                status_code=503,
            )
        content = chat_completion(
            self.api_key,
            self.api_url,
            self.model,
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(scenario, ensure_ascii=False, default=str),
                },
            ],
            temperature=0.2,
            timeout=self.timeout,
            force_ipv4=self.force_ipv4,
        )
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise AppError(
                "MODEL_SERVICE_UNAVAILABLE",
                "OpenCode Go 返回内容不是有效 JSON",
                status_code=502,
            ) from exc
        return normalize_result(parsed)
