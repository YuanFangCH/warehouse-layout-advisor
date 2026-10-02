import os
from datetime import datetime, timezone

from ..adapters.mock_model_gateway import MockModelGateway
from ..adapters.opencode_model_gateway import OpenCodeModelGateway
from ..persistence import repositories as repo
from ..persistence.database import session_scope
from .event_publisher import publisher


def build_model_gateway():
    if os.environ.get("OPENCODE_API_KEY"):
        return OpenCodeModelGateway()
    return MockModelGateway()


def build_result_summary(result: dict) -> str:
    schemes = result.get("schemes") or []
    recommendation = result.get("recommendation") or {}
    recommended = recommendation.get("recommended_option")
    label = next(
        (scheme.get("label") for scheme in schemes if scheme.get("id") == recommended),
        recommended or "推荐方案",
    )
    reasons = recommendation.get("reasons") or []
    lines = [f"评估完成，当前推荐：{label}。"]
    if reasons:
        lines.append("推荐理由：" + "；".join(reasons[:3]) + "。")
    lines.append("你可以在对话中追问方案差异、参数含义、KPI 证据或实施风险。")
    return "\n".join(lines)


def run_evaluation(evaluation_id: str) -> None:
    try:
        with session_scope() as session:
            evaluation = repo.get_evaluation(session, evaluation_id)
            if not evaluation:
                return
            scenario = repo.get_scenario(session, evaluation["scenario_id"])

        gateway = build_model_gateway()
        result = None
        steps = [
            (12, "baseline", "建立当前布局基线"),
            (38, "candidates", "比较候选布局"),
            (66, "simulation", "运行作业仿真"),
            (84, "evidence", "整理 KPI 与证据"),
            (100, "recommendation", "生成业务化推荐"),
        ]
        for progress, stage, message in steps:
            publisher.publish(
                evaluation_id,
                {
                    "type": "evaluation.progress",
                    "stage": stage,
                    "progress": progress,
                    "message": message,
                },
            )
            with session_scope() as session:
                repo.update_evaluation(
                    session,
                    evaluation_id,
                    {"status": "running", "progress": progress, "stage": stage, "message": message},
                )
            if stage == "simulation":
                result = gateway.evaluate_layout(scenario or {})

        if result is None:
            result = gateway.evaluate_layout(scenario or {})

        with session_scope() as session:
            repo.update_evaluation(
                session,
                evaluation_id,
                {
                    "status": "completed",
                    "progress": 100,
                    "stage": "recommendation",
                    "message": "评估完成",
                    "results": result,
                    "completed_at": datetime.now(timezone.utc),
                },
            )
            repo.replace_evidence(session, evaluation_id, result["kpis"])
            repo.upsert_recommendation(session, evaluation_id, result["recommendation"])
            scenario_id = evaluation["scenario_id"]
            repo.update_scenario_fields(session, scenario_id, {"status": "awaiting_approval"})
            repo.add_message(session, scenario_id, "assistant", build_result_summary(result))
            repo.add_event(
                session,
                scenario_id,
                "evaluation_completed",
                "system",
                "评估完成并生成推荐",
                scenario["version"] if scenario else 1,
            )
        publisher.publish(
            evaluation_id,
            {
                "type": "evaluation.completed",
                "stage": "recommendation",
                "progress": 100,
                "message": "评估完成",
            },
        )
    except Exception as exc:
        with session_scope() as session:
            repo.update_evaluation(
                session,
                evaluation_id,
                {
                    "status": "failed",
                    "progress": 100,
                    "stage": "failed",
                    "message": f"评估失败：{exc}",
                },
            )
        publisher.publish(
            evaluation_id,
            {
                "type": "evaluation.failed",
                "stage": "failed",
                "progress": 100,
                "message": f"评估失败：{exc}",
            },
        )
