from ..errors import AppError
from ..models.enums import ScenarioStatus
from ..persistence import repositories as repo
from ..persistence.database import session_scope
from .scenario_service import _assert_version, _require_scenario, build_snapshot


def approve_decision(scenario_id: str, client_version: int, selected_option: str, approval_note: str) -> dict:
    with session_scope() as session:
        scenario = _require_scenario(session, scenario_id)
        _assert_version(scenario, client_version)
        evaluation = repo.get_latest_evaluation(session, scenario_id)
        if not evaluation or evaluation["status"] != "completed":
            raise AppError("EVALUATION_NOT_COMPLETED", "评估尚未完成", status_code=400)
        recommendation = repo.get_latest_recommendation(session, evaluation["id"])
        if recommendation and recommendation["approval_status"] == "approved":
            raise AppError("DECISION_ALREADY_APPROVED", "该方案已经确认", status_code=409)

        new_version = scenario["version"] + 1
        repo.set_recommendation_status(session, evaluation["id"], "approved")
        repo.update_scenario_fields(
            session,
            scenario_id,
            {"status": ScenarioStatus.APPROVED.value, "version": new_version},
        )
        repo.add_event(
            session,
            scenario_id,
            "decision_approved",
            "user",
            approval_note or f"确认采用 {selected_option}",
            new_version,
        )
        repo.add_version_snapshot(
            session,
            scenario_id,
            new_version,
            ScenarioStatus.APPROVED.value,
            build_snapshot({**scenario, "status": ScenarioStatus.APPROVED.value, "version": new_version}),
            "确认最终方案",
        )
        repo.add_message(
            session,
            scenario_id,
            "assistant",
            f"{selected_option} 已记录为正式决策。分析条件、证据和风险说明均已保留。",
        )
        updated = repo.get_scenario(session, scenario_id)
        updated["latest_evaluation"] = repo.get_latest_evaluation(session, scenario_id)
        return updated


def revise_scenario(scenario_id: str, client_version: int, note: str) -> dict:
    with session_scope() as session:
        scenario = _require_scenario(session, scenario_id)
        _assert_version(scenario, client_version)
        new_version = scenario["version"] + 1
        repo.update_scenario_fields(
            session,
            scenario_id,
            {"status": ScenarioStatus.READY.value, "version": new_version},
        )
        repo.add_event(
            session,
            scenario_id,
            "scenario_revised",
            "user",
            note or "调整条件生成新版本",
            new_version,
        )
        repo.add_version_snapshot(
            session,
            scenario_id,
            new_version,
            ScenarioStatus.READY.value,
            build_snapshot({**scenario, "status": ScenarioStatus.READY.value, "version": new_version}),
            "调整条件重算",
        )
        repo.add_message(
            session,
            scenario_id,
            "assistant",
            f"已生成 v{new_version}。旧版本保留为历史记录，新条件确认后可以重新评估。",
        )
        updated = repo.get_scenario(session, scenario_id)
        updated["latest_evaluation"] = repo.get_latest_evaluation(session, scenario_id)
        return updated
