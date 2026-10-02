import re
from typing import Any

from ..adapters.opencode_conversation_gateway import OpenCodeConversationGateway
from ..errors import AppError

DEFAULT_BUDGET = 200000

OBJECTIVE_LABELS = {
    "minimize_picking_distance": "降低拣选距离",
    "minimize_modification_cost": "控制改造成本",
}
BUDGET_MODE_LABELS = {
    "hard_limit": "硬约束",
    "soft_limit": "软约束",
    "pending": "待确认",
}


def parse_budget_amount(message: str) -> int | None:
    """Extract a money amount from Chinese requirement text (30万 -> 300000)."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*(万|w|元)", message, flags=re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit in {"万", "w"}:
        return int(value * 10000)
    return int(value)


def _budget_mode_from_message(message: str) -> str | None:
    if any(word in message for word in ("硬约束", "不得超过", "不能超", "预算内", "不允许超")):
        return "hard_limit"
    if any(word in message for word in ("软约束", "可以超", "尽量不超", "可超")):
        return "soft_limit"
    return None


def translate_message(message: str, scenario: dict | None = None) -> dict[str, Any]:
    """Translate a fuzzy requirement into a business patch without clobbering existing values."""
    scenario = scenario or {}
    patch: dict[str, Any] = {}

    amount = parse_budget_amount(message)
    budget_mode = _budget_mode_from_message(message)
    if amount is not None or budget_mode is not None:
        existing = scenario.get("budget_policy") or {}
        mode = existing.get("mode")
        if mode not in {"hard_limit", "soft_limit"}:
            mode = budget_mode or "pending"
        patch["budget_policy"] = {
            "amount": amount if amount is not None else existing.get("amount", DEFAULT_BUDGET),
            "mode": mode,
        }

    objective_words = ("拣选距离", "效率", "少花钱", "降低成本", "优先成本", "平衡", "综合")
    if any(word in message for word in objective_words):
        existing = scenario.get("business_objectives") or []
        objectives = {
            item["code"]: item.get("priority", 2)
            for item in existing
            if isinstance(item, dict) and item.get("code")
        }
        if "优先少花钱" in message or "优先降低成本" in message or ("少花钱" in message and "距离" not in message):
            objectives["minimize_modification_cost"] = 1
            objectives.setdefault("minimize_picking_distance", 2)
        elif "优先降低拣选距离" in message or "优先效率" in message or ("拣选距离" in message and "成本" not in message):
            objectives["minimize_picking_distance"] = 1
            objectives.setdefault("minimize_modification_cost", 2)
        elif "平衡" in message or "综合" in message:
            objectives["minimize_picking_distance"] = 1
            objectives["minimize_modification_cost"] = 1
        patch["business_objectives"] = [
            {"code": code, "priority": priority}
            for code, priority in sorted(objectives.items(), key=lambda item: item[1])
        ]

    if "不动货架" in message or "仅调" in message or "少改" in message:
        patch["modification_scope"] = "仅调整货位，不移动货架和主通道"
    elif "局部" in message or "移货架" in message or "允许调" in message:
        patch["modification_scope"] = "允许局部移动货架，但不改主通道"
    elif "重新设计" in message or "大改" in message:
        patch["modification_scope"] = "只把预算作为限制，布局可以重新设计"

    if "吞吐量" in message or "不能慢" in message or "不得低于" in message or "不低于" in message:
        patch["performance_floor"] = {"throughput": "not_below_baseline"}
    elif "允许下降" in message or "可以接受" in message or "短期下降" in message:
        patch["performance_floor"] = {"throughput": "allow_temporary_dip"}

    if "保守" in message:
        patch["risk_preference"] = "conservative"
    elif "激进" in message or "进取" in message:
        patch["risk_preference"] = "aggressive"
    elif "平衡" in message:
        patch["risk_preference"] = "balance"

    candidate_match = re.search(r"(\d+)\s*个(?:候选)?方案", message)
    if candidate_match:
        patch["candidate_count"] = int(candidate_match.group(1))

    if "90 天" in message or "90天" in message:
        patch["analysis_period"] = "recent_90_days"
    elif "30 天" in message or "30天" in message:
        patch["analysis_period"] = "recent_30_days"
    elif "一年" in message or "1 年" in message:
        patch["analysis_period"] = "last_year"

    return patch


def summarize_patch(patch: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    budget = patch.get("budget_policy")
    if isinstance(budget, dict) and budget.get("amount"):
        amount_wan = round(budget["amount"] / 10000, 1)
        mode = budget.get("mode", "pending")
        lines.append(f"预算政策 → {amount_wan:g} 万元 · {BUDGET_MODE_LABELS.get(mode, '待确认')}")
    objectives = patch.get("business_objectives")
    if objectives:
        labels = [OBJECTIVE_LABELS.get(item.get("code"), item.get("code")) for item in objectives]
        lines.append(f"主要目标 → {'、'.join(labels)}")
    if patch.get("modification_scope"):
        lines.append(f"改造范围 → {patch['modification_scope']}")
    floor = patch.get("performance_floor")
    if isinstance(floor, dict) and floor.get("throughput") == "not_below_baseline":
        lines.append("性能底线 → 吞吐量不得低于当前布局")
    elif isinstance(floor, dict) and floor.get("throughput") == "allow_temporary_dip":
        lines.append("性能底线 → 允许短期轻微下降")
    if patch.get("risk_preference"):
        labels = {"conservative": "偏保守", "balance": "平衡", "aggressive": "偏进取"}
        lines.append(f"风险偏好 → {labels.get(patch['risk_preference'], patch['risk_preference'])}")
    if patch.get("candidate_count"):
        lines.append(f"候选数量 → {patch['candidate_count']} 个")
    return lines


def interpret_message(scenario: dict, message: str) -> dict:
    """Interpret a user message with the real model when configured, otherwise use rules."""
    gateway = OpenCodeConversationGateway()
    if gateway.is_configured():
        try:
            interpretation = gateway.interpret(scenario, message)
            if interpretation.get("reply") or interpretation.get("conditions_patch") or interpretation.get("clarification"):
                return interpretation
        except AppError:
            pass
    patch = translate_message(message, scenario)
    lines = summarize_patch(patch)
    reply = "已同步分析条件：" + "；".join(lines) + "。" if lines else "收到，我会继续确认关键条件。"
    return {"reply": reply, "conditions_patch": patch, "clarification": None, "confidence": "medium"}


def apply_answer(key: str, answer: str, scenario: dict | None = None) -> dict[str, Any]:
    if key == "modification_scope":
        return {"modification_scope": answer}
    if key == "priority":
        if "距离" in answer:
            return {
                "business_objectives": [
                    {"code": "minimize_picking_distance", "priority": 1},
                    {"code": "minimize_modification_cost", "priority": 2},
                ]
            }
        if "成本" in answer:
            return {
                "business_objectives": [
                    {"code": "minimize_modification_cost", "priority": 1},
                    {"code": "minimize_picking_distance", "priority": 2},
                ]
            }
        return {
            "business_objectives": [
                {"code": "minimize_picking_distance", "priority": 1},
                {"code": "minimize_modification_cost", "priority": 1},
            ]
        }
    if key == "performance_floor":
        if "不得低于" in answer or "设为" in answer:
            return {"performance_floor": {"throughput": "not_below_baseline"}}
        return {"performance_floor": {"throughput": "allow_temporary_dip"}}
    if key == "budget_policy":
        existing = (scenario or {}).get("budget_policy") or {}
        amount = parse_budget_amount(answer)
        mode = "hard_limit" if ("硬约束" in answer or "不得超" in answer) else "soft_limit"
        return {
            "budget_policy": {
                "amount": amount if amount is not None else existing.get("amount", DEFAULT_BUDGET),
                "mode": mode,
            }
        }
    return {}
