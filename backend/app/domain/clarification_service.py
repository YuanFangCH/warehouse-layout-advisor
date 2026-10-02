from typing import Any

from ..errors import AppError
from ..models.enums import ScenarioStatus
from ..persistence import repositories as repo
from ..persistence.database import session_scope
from .explanation_service import explain_results
from .scenario_service import _assert_version, _require_scenario, build_snapshot
from .translation_service import apply_answer, interpret_message, summarize_patch


QUESTION_KEYS = ["modification_scope", "priority", "performance_floor"]
QUESTION_MAP = {
    "modification_scope": (
        "“尽量少改”会直接影响候选方案的范围。你希望它代表哪一种？",
        ["仅调整货位，不移动货架和主通道", "允许局部移动货架，但不改主通道", "只把预算作为限制，布局可以重新设计"],
    ),
    "priority": (
        "拣选距离和改造成本存在取舍。哪一个应该优先？",
        ["优先降低拣选距离，成本在预算内尽量控制", "优先少花钱，接受部分效率改善", "两者平衡，选择综合方案"],
    ),
    "performance_floor": (
        "为了避免平均距离下降但仓库整体变慢，是否把吞吐量不下降设为硬要求？",
        ["是，吞吐量不得低于当前布局", "否，可以接受短期轻微下降"],
    ),
}

EXPLANATION_HINTS = (
    "为什么",
    "是什么",
    "什么意思",
    "区别",
    "差异",
    "风险",
    "对比",
    "差在哪",
    "推荐理由",
    "为什么选",
    "为什么推荐",
    "解释",
    "怎么看",
    "怎么算",
    "好在哪",
    "好在哪里",
    "值不值得",
)
QUESTION_STARTS = ("为什么", "是什么", "怎么", "请问", "是否", "哪个")


def _is_explanation_question(message: str) -> bool:
    text = message.strip()
    if any(hint in text for hint in EXPLANATION_HINTS):
        return True
    return (text.endswith("?") or text.endswith("？")) and text.startswith(QUESTION_STARTS)


def _create_next_question(session, scenario_id: str) -> dict | None:
    answered = set(repo.list_clarification_keys(session, scenario_id, status="answered"))
    for key in QUESTION_KEYS:
        if key not in answered:
            question, options = QUESTION_MAP[key]
            return repo.add_clarification(session, scenario_id, key, question, options)
    return None


def _mark_patch_answered(session, scenario_id: str, patch: dict[str, Any]) -> None:
    """Record conditions already extracted from a message so the agent does not re-ask."""
    existing = set(repo.list_clarification_keys(session, scenario_id))
    rows: list[tuple[str, str]] = []
    scope = patch.get("modification_scope")
    if "modification_scope" not in existing and scope:
        rows.append(("modification_scope", scope))
    objectives = patch.get("business_objectives")
    if "priority" not in existing and objectives:
        priorities = {
            item.get("code"): item.get("priority", 2)
            for item in objectives
            if isinstance(item, dict)
        }
        distance = priorities.get("minimize_picking_distance", 99)
        cost = priorities.get("minimize_modification_cost", 99)
        if distance < cost:
            rows.append(("priority", "优先降低拣选距离，成本在预算内尽量控制"))
        elif cost < distance:
            rows.append(("priority", "优先少花钱，接受部分效率改善"))
        else:
            rows.append(("priority", "两者平衡，选择综合方案"))
    floor = patch.get("performance_floor")
    if "performance_floor" not in existing and isinstance(floor, dict):
        answer = (
            "是，吞吐量不得低于当前布局"
            if floor.get("throughput") == "not_below_baseline"
            else "否，可以接受短期轻微下降"
        )
        rows.append(("performance_floor", answer))
    for key, answer in rows:
        question, options = QUESTION_MAP[key]
        item = repo.add_clarification(session, scenario_id, key, question, options)
        session.flush()
        repo.answer_clarification(session, item["id"], answer)
    session.flush()


def pending_questions(scenario_id: str) -> list[dict]:
    with session_scope() as session:
        _require_scenario(session, scenario_id)
        return repo.list_pending_clarifications(session, scenario_id)


def list_messages(scenario_id: str) -> list[dict]:
    with session_scope() as session:
        _require_scenario(session, scenario_id)
        return repo.list_messages(session, scenario_id)


def handle_message(scenario_id: str, message: str, client_version: int) -> dict:
    with session_scope() as session:
        scenario = _require_scenario(session, scenario_id)
        _assert_version(scenario, client_version)
        repo.add_message(session, scenario_id, "user", message)

        if _is_explanation_question(message):
            latest = repo.get_latest_evaluation(session, scenario_id)
            results = None
            evaluation = None
            if latest and latest["status"] == "completed":
                results = repo.get_evaluation_results(session, latest["id"])
                evaluation = {"id": latest["id"], "results": results}
            explanation = explain_results(scenario, message, evaluation or {"results": None})
            assistant_message = repo.add_message(session, scenario_id, "assistant", explanation["reply"])
            repo.add_event(session, scenario_id, "assistant_explained", "system", explanation["reply"], scenario["version"])
            updated = repo.get_scenario(session, scenario_id)
            updated["latest_evaluation"] = repo.get_latest_evaluation(session, scenario_id)
            return {
                "scenario": updated,
                "assistant_message": assistant_message,
                "pending_questions": [],
                "business_patch": {},
                "sync_message": None,
                "answer_kind": "explanation",
            }

        interpretation = interpret_message(scenario, message)
        patch = interpretation.get("conditions_patch") or {}
        if patch:
            repo.update_scenario_fields(session, scenario_id, patch)
            _mark_patch_answered(session, scenario_id, patch)

        pending = repo.list_pending_clarifications(session, scenario_id)
        if not pending:
            clarification = interpretation.get("clarification")
            if clarification:
                answered = set(repo.list_clarification_keys(session, scenario_id, status="answered"))
                if clarification["key"] not in answered:
                    question = repo.add_clarification(
                        session,
                        scenario_id,
                        clarification["key"],
                        clarification["question"],
                        clarification["options"],
                    )
                    pending = [question]
            if not pending:
                question = _create_next_question(session, scenario_id)
                pending = [question] if question else []

        sync_message = "、".join(summarize_patch(patch)) if patch else None
        if pending:
            assistant = interpretation.get("reply") or pending[0]["question"]
            repo.update_scenario_fields(session, scenario_id, {"status": ScenarioStatus.CLARIFYING.value})
            repo.add_event(session, scenario_id, "message_received", "user", message, scenario["version"])
        elif patch:
            new_version = scenario["version"] + 1
            updated_fields = {**patch, "version": new_version, "status": ScenarioStatus.READY.value}
            repo.update_scenario_fields(session, scenario_id, updated_fields)
            repo.add_event(
                session,
                scenario_id,
                "conditions_revised",
                "user",
                f"对话更新分析条件（{sync_message or '业务条件'}）",
                new_version,
            )
            repo.add_version_snapshot(
                session,
                scenario_id,
                new_version,
                ScenarioStatus.READY.value,
                build_snapshot({**scenario, **patch}),
                "对话更新分析条件",
            )
            assistant = interpretation.get("reply") or "条件已更新，可以开始方案比较。"
        else:
            assistant = interpretation.get("reply") or "当前条件没有变化，还需要我帮你确认什么？"
        assistant_message = repo.add_message(session, scenario_id, "assistant", assistant)
        repo.add_event(session, scenario_id, "assistant_replied", "system", assistant, scenario["version"])
        updated = repo.get_scenario(session, scenario_id)
        updated["latest_evaluation"] = repo.get_latest_evaluation(session, scenario_id)
        return {
            "scenario": updated,
            "assistant_message": assistant_message,
            "pending_questions": pending,
            "business_patch": patch,
            "sync_message": sync_message,
        }


def answer_question(scenario_id: str, question_id: str, answer: str, client_version: int) -> dict:
    with session_scope() as session:
        scenario = _require_scenario(session, scenario_id)
        _assert_version(scenario, client_version)
        question = repo.get_clarification(session, scenario_id, question_id)
        if not question:
            raise AppError("QUESTION_NOT_FOUND", "澄清问题不存在", status_code=404)
        if question.status != "pending":
            raise AppError("QUESTION_ALREADY_ANSWERED", "该问题已经回答", status_code=400)

        repo.answer_clarification(session, question_id, answer)
        session.flush()
        patch: dict[str, Any] = apply_answer(question.key, answer, scenario)
        if patch:
            repo.update_scenario_fields(session, scenario_id, patch)

        pending = repo.list_pending_clarifications(session, scenario_id)
        if not pending:
            question_item = _create_next_question(session, scenario_id)
            pending = [question_item] if question_item else []
        assistant = (
            f"已记录：{answer}。"
            if pending
            else "业务条件已经完整，请检查右侧确认卡片，确认后即可开始评估。"
        )
        assistant_message = repo.add_message(session, scenario_id, "assistant", assistant)
        repo.add_event(session, scenario_id, "answer_confirmed", "user", answer, scenario["version"])
        sync_message = "、".join(summarize_patch(patch)) if patch else None
        updated = repo.get_scenario(session, scenario_id)
        updated["latest_evaluation"] = repo.get_latest_evaluation(session, scenario_id)
        return {
            "scenario": updated,
            "assistant_message": assistant_message,
            "pending_questions": pending,
            "business_patch": patch,
            "sync_message": sync_message,
        }
