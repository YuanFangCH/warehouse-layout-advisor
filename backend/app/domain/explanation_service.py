from typing import Any

from ..adapters.opencode_conversation_gateway import OpenCodeConversationGateway
from ..errors import AppError

BUDGET_MODE_LABELS = {
    "hard_limit": "硬约束（预算不能超）",
    "soft_limit": "软约束（允许超支后解释）",
    "pending": "待确认",
}


def _scheme_label(schemes: list[dict], option_id: str) -> str:
    for scheme in schemes:
        if scheme.get("id") == option_id:
            return scheme.get("label") or option_id
    return option_id or "推荐方案"


def _explain_parameters(scenario: dict) -> str:
    budget = scenario.get("budget_policy") or {}
    amount_wan = round((budget.get("amount") or 0) / 10000, 1)
    mode = budget.get("mode", "pending")
    budget_text = f"{amount_wan:g} 万元 · {BUDGET_MODE_LABELS.get(mode, '待确认')}"
    floor = (scenario.get("performance_floor") or {}).get("throughput")
    floor_text = {
        "not_below_baseline": "吞吐量不得低于当前布局",
        "allow_temporary_dip": "允许短期轻微下降",
    }.get(floor, "尚未确认")
    risk = scenario.get("risk_preference")
    risk_text = {"conservative": "偏保守", "balance": "平衡", "aggressive": "偏进取"}.get(risk, risk or "尚未确认")
    return (
        f"当前条件是：预算 {budget_text}；性能底线为{floor_text}；"
        f"风险偏好{risk_text}；改造范围是“{scenario.get('modification_scope') or '尚未确认'}”。"
        "这些参数会直接决定候选方案的生成和取舍：预算限制改造范围，底线保证不能为了省距离把仓库做慢。"
    )


def _explain_recommendation(results: dict) -> str:
    schemes = results.get("schemes") or []
    recommendation = results.get("recommendation") or {}
    recommended = recommendation.get("recommended_option")
    label = _scheme_label(schemes, recommended)
    reasons = recommendation.get("reasons") or []
    if not reasons:
        return f"当前推荐方案是 {label}。"
    return f"当前推荐 {label}。理由：" + "；".join(reasons[:3]) + "。"


def _explain_risks(results: dict) -> str:
    recommendation = results.get("recommendation") or {}
    risks = recommendation.get("risks") or []
    tradeoffs = recommendation.get("tradeoffs") or []
    parts = []
    if risks:
        parts.append("主要风险：" + "；".join(risks))
    if tradeoffs:
        parts.append("取舍：" + "；".join(tradeoffs))
    return "；".join(parts) if parts else "当前推荐方案的可见风险较少，主要取舍可以参考证据面板。"


def _explain_difference(results: dict) -> str:
    schemes = results.get("schemes") or []
    recommendation = results.get("recommendation") or {}
    recommended = recommendation.get("recommended_option")
    alternatives = recommendation.get("alternative_options") or []
    parts = [f"推荐方案是{_scheme_label(schemes, recommended)}。"]
    for option_id in alternatives:
        label = _scheme_label(schemes, option_id)
        note = next((s.get("note") for s in schemes if s.get("id") == option_id), "")
        if note:
            parts.append(f"{label}：{note}")
    if len(parts) == 1:
        parts.append("可以对比证据面板中的 KPI，或直接问我某个方案的取舍。")
    return "；".join(parts)


def _explain_kpis(results: dict) -> str:
    kpis = results.get("kpis") or []
    if not kpis:
        return "这次评估没有生成 KPI 证据，可以稍后再问。"
    lines = []
    for kpi in kpis[:3]:
        lines.append(
            f"{kpi.get('metric')}：基线 {kpi.get('baseline')} → 候选 {kpi.get('candidate')}（{kpi.get('delta')}）"
        )
    return "关键指标：" + "；".join(lines) + "。"


def _rule_explanation(scenario: dict, message: str, results: dict | None) -> str:
    if not results:
        return "这个场景还没有完成评估。等评估结束后，我可以为你解释方案差异、KPI 含义、参数影响和推荐理由。"
    if any(word in message for word in ("风险", "隐患", "缺点")):
        return _explain_risks(results)
    if any(word in message for word in ("区别", "差异", "对比", "差在哪", "哪个好", "比较")):
        return _explain_difference(results)
    if any(word in message for word in ("KPI", "指标", "拣选距离", "吞吐量", "成本怎么", "怎么算")):
        return _explain_kpis(results)
    if any(word in message for word in ("推荐", "为什么选", "为什么这个", "理由")):
        return _explain_recommendation(results)
    if any(word in message for word in ("参数", "预算", "硬约束", "软约束", "底线", "风险偏好", "改造范围")):
        return _explain_parameters(scenario)
    return _explain_recommendation(results)


def explain_results(scenario: dict, message: str, evaluation: dict) -> dict:
    """Explain schemes, parameters, KPI or recommendation with the real model when configured."""
    results = evaluation.get("results")
    gateway = OpenCodeConversationGateway()
    if gateway.is_configured():
        try:
            explanation = gateway.explain(scenario, message, evaluation)
            if explanation.get("reply"):
                return explanation
        except AppError:
            pass
    return {
        "reply": _rule_explanation(scenario, message, results),
        "confidence": "medium",
    }
