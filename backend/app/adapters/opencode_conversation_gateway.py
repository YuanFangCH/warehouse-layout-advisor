import json
import os
from typing import Any

from ..errors import AppError
from .opencode_model_gateway import DEFAULT_API_URL, DEFAULT_MODEL, chat_completion

CONVERSATION_SYSTEM_PROMPT = """你是仓储布局决策参谋的对话理解引擎。你会收到当前场景条件与用户最新消息，把用户意图翻译成可落库的业务参数，并判断是否需要追问。

只输出一个 JSON 对象，不要 Markdown 代码块，不要解释性文字，字段如下：
{
  "reply": "给用户的自然语言回复，用简体中文，2-3 句，说明你理解到的新条件和下一步",
  "conditions_patch": {},
  "clarification": null,
  "confidence": "high|medium|low"
}

conditions_patch 只放用户明确提到的新条件，允许键：
- business_objectives: [{code, priority}]，code 只能是 minimize_picking_distance 或 minimize_modification_cost
- modification_scope: 字符串
- budget_policy: {amount(元), mode(hard_limit|soft_limit|pending)}
- performance_floor: {throughput(not_below_baseline|allow_temporary_dip)}
- risk_preference: conservative|balance|aggressive
- analysis_period: 字符串
- candidate_count: 整数
- assumptions: 字符串数组

金额统一换算成元（30 万 = 300000）。用户没提金额但提到预算性质时，只改 mode。用户需求仍模糊且关键条件未确认时，设置 clarification；足够明确时 clarification 为 null。clarification.key 只能是 modification_scope、priority、performance_floor、budget_policy 之一。
"""

EXPLANATION_SYSTEM_PROMPT = """你是仓储布局决策参谋，负责解读评估结果和业务参数。用户正在追问已完成评估的方案、参数、KPI、风险或推荐理由。

输入包含：当前场景条件、评估结果（候选方案、KPI、洞察、推荐）、用户问题。

要求：
1. 用简体中文直接回答，2-4 句话，业务化、具体、可操作；不要复述整个结果。
2. 解释“为什么推荐某个方案”时，要引用具体证据（拣选距离、吞吐量、成本、风险、取舍）。
3. 解释参数时，结合当前场景的实际值（预算金额与性质、性能底线、改造范围、风险偏好）说明含义和影响。
4. 如果问题与结果无关，礼貌说明你可以帮忙确认方案、参数、KPI 和推荐理由。
5. 只输出一个 JSON 对象：{"reply": "...", "confidence": "high|medium|low"}，不要 Markdown 代码块。
"""

ALLOWED_PATCH_KEYS = {
    "business_objectives",
    "modification_scope",
    "budget_policy",
    "performance_floor",
    "risk_preference",
    "analysis_period",
    "candidate_count",
    "assumptions",
}
ALLOWED_QUESTION_KEYS = {"modification_scope", "priority", "performance_floor", "budget_policy"}
OBJECTIVE_CODES = {"minimize_picking_distance", "minimize_modification_cost"}
BUDGET_MODES = {"hard_limit", "soft_limit", "pending"}
FLOOR_VALUES = {"not_below_baseline", "allow_temporary_dip"}
RISK_VALUES = {"conservative", "balance", "aggressive"}


def _text(value: Any, fallback: str = "") -> str:
    return fallback if value is None else str(value)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_text(item) for item in value if item is not None]
    return []


def _objective(item: Any) -> dict | None:
    raw = item if isinstance(item, dict) else {}
    code = _text(raw.get("code"))
    if code not in OBJECTIVE_CODES:
        return None
    try:
        priority = int(raw.get("priority") or 1)
    except (TypeError, ValueError):
        priority = 1
    return {"code": code, "priority": priority}


def normalize_conditions_patch(value: Any) -> dict:
    raw = value if isinstance(value, dict) else {}
    patch: dict[str, Any] = {}
    for key in ALLOWED_PATCH_KEYS:
        if key not in raw or raw[key] is None:
            continue
        item = raw[key]
        if key == "business_objectives":
            objectives = [_objective(entry) for entry in (item if isinstance(item, list) else [])]
            patch[key] = [entry for entry in objectives if entry]
        elif key == "budget_policy":
            if isinstance(item, dict):
                budget: dict[str, Any] = {}
                try:
                    budget["amount"] = int(float(item.get("amount") or 0))
                except (TypeError, ValueError):
                    budget["amount"] = 0
                budget["mode"] = item.get("mode") if item.get("mode") in BUDGET_MODES else "pending"
                patch[key] = budget
        elif key == "performance_floor":
            if isinstance(item, dict) and item.get("throughput") in FLOOR_VALUES:
                patch[key] = {"throughput": item["throughput"]}
        elif key == "risk_preference":
            if item in RISK_VALUES:
                patch[key] = item
        elif key == "candidate_count":
            try:
                count = int(item)
                if count > 0:
                    patch[key] = count
            except (TypeError, ValueError):
                pass
        elif key == "assumptions":
            values = _string_list(item)
            if values:
                patch[key] = values
        else:
            patch[key] = _text(item)
    return patch


def normalize_clarification(value: Any) -> dict | None:
    raw = value if isinstance(value, dict) else {}
    key = _text(raw.get("key"))
    if key not in ALLOWED_QUESTION_KEYS:
        return None
    question = _text(raw.get("question")).strip()
    options = _string_list(raw.get("options"))
    if not question or len(options) < 2:
        return None
    return {"key": key, "question": question, "options": options[:4]}


def normalize_interpretation(data: Any) -> dict:
    raw = data if isinstance(data, dict) else {}
    return {
        "reply": _text(raw.get("reply")) or "我理解你的要求了，稍等我把条件同步好。",
        "conditions_patch": normalize_conditions_patch(raw.get("conditions_patch")),
        "clarification": normalize_clarification(raw.get("clarification")),
        "confidence": _text(raw.get("confidence"), "medium"),
    }


def normalize_explanation(data: Any) -> dict:
    raw = data if isinstance(data, dict) else {}
    return {
        "reply": _text(raw.get("reply")) or "我可以用现有评估结果帮你解释方案、参数和推荐理由。",
        "confidence": _text(raw.get("confidence"), "medium"),
    }


class OpenCodeConversationGateway:
    """Interprets user requirements with OpenCode Go."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
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

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def interpret(self, scenario: dict, message: str) -> dict:
        if not self.api_key:
            raise AppError(
                "MODEL_SERVICE_UNAVAILABLE",
                "OpenCode Go 未配置 OPENCODE_API_KEY",
                status_code=503,
            )
        user_content = json.dumps(
            {
                "scenario": scenario,
                "user_message": message,
            },
            ensure_ascii=False,
            default=str,
        )
        content = chat_completion(
            self.api_key,
            self.api_url,
            self.model,
            [
                {"role": "system", "content": CONVERSATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            timeout=self.timeout,
            force_ipv4=self.force_ipv4,
        )
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise AppError(
                "MODEL_SERVICE_UNAVAILABLE",
                "OpenCode Go 对话理解返回内容不是有效 JSON",
                status_code=502,
            ) from exc
        return normalize_interpretation(parsed)

    def explain(self, scenario: dict, message: str, evaluation: dict) -> dict:
        if not self.api_key:
            raise AppError(
                "MODEL_SERVICE_UNAVAILABLE",
                "OpenCode Go 未配置 OPENCODE_API_KEY",
                status_code=503,
            )
        user_content = json.dumps(
            {
                "scenario": scenario,
                "evaluation": evaluation,
                "user_question": message,
            },
            ensure_ascii=False,
            default=str,
        )
        content = chat_completion(
            self.api_key,
            self.api_url,
            self.model,
            [
                {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            timeout=self.timeout,
            force_ipv4=self.force_ipv4,
        )
        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError) as exc:
            raise AppError(
                "MODEL_SERVICE_UNAVAILABLE",
                "OpenCode Go 结果解读返回内容不是有效 JSON",
                status_code=502,
            ) from exc
        return normalize_explanation(parsed)
