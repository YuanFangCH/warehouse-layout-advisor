from typing import Any

from ..errors import AppError
from ..models.enums import ScenarioStatus
from ..persistence import repositories as repo
from ..persistence.database import session_scope


def build_snapshot(scenario: dict) -> dict:
    return {
        "title": scenario["title"],
        "status": scenario["status"],
        "business_objectives": scenario["business_objectives"],
        "modification_scope": scenario["modification_scope"],
        "budget_policy": scenario["budget_policy"],
        "performance_floor": scenario["performance_floor"],
        "analysis_period": scenario["analysis_period"],
        "risk_preference": scenario["risk_preference"],
        "candidate_count": scenario["candidate_count"],
        "assumptions": scenario["assumptions"],
    }


def _require_scenario(session, scenario_id: str) -> dict:
    scenario = repo.get_scenario(session, scenario_id)
    if not scenario:
        raise AppError("SCENARIO_NOT_FOUND", "场景不存在", status_code=404)
    return scenario


def _assert_version(scenario: dict, client_version: int) -> None:
    if scenario["version"] != client_version:
        raise AppError(
            "SCENARIO_VERSION_CONFLICT",
            "当前场景已产生新版本",
            status_code=409,
            details={
                "server_version": scenario["version"],
                "client_version": client_version,
            },
        )


def create_project(name: str, warehouse_name: str | None, data_status: str) -> dict:
    with session_scope() as session:
        return repo.create_project(session, repo.uid("project"), name, warehouse_name or name, data_status)


def list_projects() -> list[dict]:
    with session_scope() as session:
        return repo.list_projects(session)


def get_project(project_id: str) -> dict:
    with session_scope() as session:
        project = repo.get_project(session, project_id)
        if not project:
            raise AppError("PROJECT_NOT_FOUND", "项目不存在", status_code=404)
        return project


def create_scenario(project_id: str, title: str) -> dict:
    with session_scope() as session:
        if not repo.get_project(session, project_id):
            raise AppError("PROJECT_NOT_FOUND", "项目不存在", status_code=404)
        scenario = repo.create_scenario(session, repo.uid("scenario"), project_id, title)
        repo.add_event(session, scenario["id"], "scenario_created", "system", "创建分析场景", 1)
        repo.add_version_snapshot(
            session,
            scenario["id"],
            1,
            ScenarioStatus.COLLECTING.value,
            build_snapshot(scenario),
            "创建分析场景",
        )
        scenario["latest_evaluation"] = None
        return scenario


def list_scenarios(project_id: str) -> list[dict]:
    with session_scope() as session:
        return repo.list_scenarios(session, project_id)


def get_scenario(scenario_id: str) -> dict:
    with session_scope() as session:
        scenario = _require_scenario(session, scenario_id)
        scenario["latest_evaluation"] = repo.get_latest_evaluation(session, scenario_id)
        return scenario


def update_scenario(scenario_id: str, patch: dict[str, Any], client_version: int) -> dict:
    with session_scope() as session:
        scenario = _require_scenario(session, scenario_id)
        _assert_version(scenario, client_version)
        fields = {key: value for key, value in patch.items() if value is not None}
        fields.pop("client_version", None)
        if not fields:
            return scenario
        fields["version"] = scenario["version"] + 1
        fields["status"] = ScenarioStatus.READY.value
        repo.update_scenario_fields(session, scenario_id, fields)
        repo.add_event(session, scenario_id, "conditions_revised", "user", "调整分析条件并生成新版本", fields["version"])
        repo.add_version_snapshot(
            session,
            scenario_id,
            fields["version"],
            ScenarioStatus.READY.value,
            build_snapshot({**scenario, **fields}),
            "调整分析条件",
        )
        updated = repo.get_scenario(session, scenario_id)
        updated["latest_evaluation"] = repo.get_latest_evaluation(session, scenario_id)
        return updated


def confirm_scenario(scenario_id: str, client_version: int, confirmed_fields: list[str]) -> dict:
    with session_scope() as session:
        scenario = _require_scenario(session, scenario_id)
        _assert_version(scenario, client_version)
        if repo.list_pending_clarifications(session, scenario_id):
            raise AppError("PENDING_CLARIFICATIONS", "仍有待确认问题", status_code=400)

        budget = dict(scenario["budget_policy"] or {})
        if budget.get("mode") not in {"hard_limit", "soft_limit"}:
            budget["mode"] = "hard_limit"
        if not budget.get("amount"):
            budget["amount"] = 200000
        floor = dict(scenario["performance_floor"] or {})
        if floor.get("throughput") not in {"not_below_baseline", "allow_temporary_dip"}:
            floor["throughput"] = "not_below_baseline"
        fields: dict[str, Any] = {
            "budget_policy": budget,
            "performance_floor": floor,
            "candidate_count": scenario["candidate_count"] or 3,
            "status": ScenarioStatus.READY.value,
            "version": scenario["version"] + 1,
        }
        if not scenario["assumptions"]:
            fields["assumptions"] = [
                "订单范围采用最近 30 天",
                "候选方案数量为 3 个",
                "风险偏好为偏保守",
            ]
        repo.update_scenario_fields(session, scenario_id, fields)
        repo.add_event(
            session,
            scenario_id,
            "conditions_confirmed",
            "user",
            f"确认业务分析条件（{', '.join(confirmed_fields) if confirmed_fields else '全部条件'}）",
            fields["version"],
        )
        repo.add_version_snapshot(
            session,
            scenario_id,
            fields["version"],
            ScenarioStatus.READY.value,
            build_snapshot({**scenario, **fields}),
            "确认业务分析条件",
        )
        repo.add_message(
            session,
            scenario_id,
            "assistant",
            f"条件已保存为 v{fields['version']}。可以开始建立当前布局基线并比较候选方案。",
        )
        updated = repo.get_scenario(session, scenario_id)
        updated["latest_evaluation"] = repo.get_latest_evaluation(session, scenario_id)
        return updated


def start_evaluation(scenario_id: str, client_version: int) -> dict:
    with session_scope() as session:
        scenario = _require_scenario(session, scenario_id)
        _assert_version(scenario, client_version)
        if scenario["status"] != ScenarioStatus.READY.value:
            raise AppError("SCENARIO_NOT_READY", "场景尚未就绪", status_code=400)
        evaluation = repo.create_evaluation(session, repo.uid("eval"), scenario_id)
        repo.update_scenario_fields(session, scenario_id, {"status": ScenarioStatus.EVALUATING.value})
        repo.add_event(session, scenario_id, "evaluation_started", "system", "开始布局方案评估", scenario["version"])
        return evaluation


def get_evaluation(evaluation_id: str) -> dict | None:
    with session_scope() as session:
        return repo.get_evaluation(session, evaluation_id)


def list_versions(scenario_id: str) -> list[dict]:
    with session_scope() as session:
        _require_scenario(session, scenario_id)
        return repo.list_versions(session, scenario_id)


def list_events(scenario_id: str) -> list[dict]:
    with session_scope() as session:
        _require_scenario(session, scenario_id)
        return repo.list_events(session, scenario_id)
