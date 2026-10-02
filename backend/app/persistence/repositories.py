import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models.entities import (
    AppEvent,
    Clarification,
    Evaluation,
    Evidence,
    Message,
    Project,
    Recommendation,
    Scenario,
    ScenarioVersion,
)


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def now() -> datetime:
    return datetime.now(timezone.utc)


def project_to_dict(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "warehouse_name": project.warehouse_name,
        "data_status": project.data_status,
        "created_at": project.created_at.isoformat(),
    }


def scenario_to_dict(scenario: Scenario) -> dict:
    return {
        "id": scenario.id,
        "project_id": scenario.project_id,
        "title": scenario.title,
        "status": scenario.status,
        "version": scenario.version,
        "business_objectives": scenario.business_objectives,
        "modification_scope": scenario.modification_scope,
        "budget_policy": scenario.budget_policy,
        "performance_floor": scenario.performance_floor,
        "analysis_period": scenario.analysis_period,
        "risk_preference": scenario.risk_preference,
        "candidate_count": scenario.candidate_count,
        "assumptions": scenario.assumptions,
        "created_at": scenario.created_at.isoformat(),
        "updated_at": scenario.updated_at.isoformat(),
    }


def message_to_dict(message: Message) -> dict:
    return {
        "id": message.id,
        "scenario_id": message.scenario_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


def clarification_to_dict(clarification: Clarification) -> dict:
    return {
        "id": clarification.id,
        "key": clarification.key,
        "question": clarification.question,
        "type": "single_choice",
        "options": clarification.options,
        "status": clarification.status,
        "created_at": clarification.created_at.isoformat(),
    }


def evaluation_to_dict(evaluation: Evaluation) -> dict:
    result = {
        "id": evaluation.id,
        "scenario_id": evaluation.scenario_id,
        "status": evaluation.status,
        "progress": evaluation.progress,
        "stage": evaluation.stage,
        "message": evaluation.message,
        "created_at": evaluation.created_at.isoformat(),
        "completed_at": evaluation.completed_at.isoformat() if evaluation.completed_at else None,
    }
    if evaluation.results:
        result["schemes"] = evaluation.results.get("schemes", [])
    return result


def evidence_to_dict(evidence: Evidence) -> dict:
    return {
        "id": evidence.id,
        "evaluation_id": evidence.evaluation_id,
        "metric": evidence.metric,
        "baseline_value": evidence.baseline_value,
        "candidate_value": evidence.candidate_value,
        "delta": evidence.delta,
        "entity": evidence.entity,
        "explanation_type": evidence.explanation_type,
        "confidence": evidence.confidence,
    }


def recommendation_to_dict(recommendation: Recommendation) -> dict:
    payload = dict(recommendation.payload)
    payload["approval_status"] = recommendation.approval_status
    return payload


def event_to_dict(event: AppEvent) -> dict:
    return {
        "id": event.id,
        "scenario_id": event.scenario_id,
        "type": event.type,
        "actor": event.actor,
        "content": event.content,
        "version": event.version,
        "created_at": event.created_at.isoformat(),
    }


def version_to_dict(version: ScenarioVersion) -> dict:
    return {
        "id": version.id,
        "scenario_id": version.scenario_id,
        "version": version.version,
        "status": version.status,
        "snapshot": version.snapshot,
        "note": version.note,
        "created_at": version.created_at.isoformat(),
    }


def list_projects(session: Session) -> list[dict]:
    rows = session.scalars(select(Project).order_by(Project.created_at.desc())).all()
    return [project_to_dict(row) for row in rows]


def get_project(session: Session, project_id: str) -> dict | None:
    row = session.get(Project, project_id)
    return project_to_dict(row) if row else None


def create_project(session: Session, project_id: str, name: str, warehouse_name: str, data_status: str) -> dict:
    row = Project(
        id=project_id,
        name=name,
        warehouse_name=warehouse_name or name,
        data_status=data_status,
        created_at=now(),
    )
    session.add(row)
    return project_to_dict(row)


def list_scenarios(session: Session, project_id: str) -> list[dict]:
    rows = session.scalars(
        select(Scenario).where(Scenario.project_id == project_id).order_by(Scenario.updated_at.desc())
    ).all()
    return [scenario_to_dict(row) for row in rows]


def get_scenario(session: Session, scenario_id: str) -> dict | None:
    row = session.get(Scenario, scenario_id)
    return scenario_to_dict(row) if row else None


def create_scenario(
    session: Session,
    scenario_id: str,
    project_id: str,
    title: str,
) -> dict:
    created = now()
    row = Scenario(
        id=scenario_id,
        project_id=project_id,
        title=title,
        status="collecting",
        version=1,
        business_objectives=[],
        modification_scope="尚未确认",
        budget_policy={"amount": 200000, "mode": "pending"},
        performance_floor={"throughput": "pending"},
        analysis_period="recent_30_days",
        risk_preference="conservative",
        candidate_count=3,
        assumptions=[],
        created_at=created,
        updated_at=created,
    )
    session.add(row)
    return scenario_to_dict(row)


def update_scenario_fields(session: Session, scenario_id: str, fields: dict[str, Any]) -> dict | None:
    row = session.get(Scenario, scenario_id)
    if not row:
        return None
    for key, value in fields.items():
        setattr(row, key, value)
    row.updated_at = now()
    return scenario_to_dict(row)


def list_messages(session: Session, scenario_id: str) -> list[dict]:
    rows = session.scalars(
        select(Message).where(Message.scenario_id == scenario_id).order_by(Message.created_at.asc())
    ).all()
    return [message_to_dict(row) for row in rows]


def add_message(session: Session, scenario_id: str, role: str, content: str) -> dict:
    row = Message(id=uid("msg"), scenario_id=scenario_id, role=role, content=content, created_at=now())
    session.add(row)
    return message_to_dict(row)


def list_pending_clarifications(session: Session, scenario_id: str) -> list[dict]:
    rows = session.scalars(
        select(Clarification)
        .where(Clarification.scenario_id == scenario_id, Clarification.status == "pending")
        .order_by(Clarification.created_at.asc())
    ).all()
    return [clarification_to_dict(row) for row in rows]


def list_clarification_keys(session: Session, scenario_id: str, status: str | None = None) -> list[str]:
    query = select(Clarification.key).where(Clarification.scenario_id == scenario_id)
    if status:
        query = query.where(Clarification.status == status)
    return list(session.scalars(query).all())


def get_clarification(session: Session, scenario_id: str, question_id: str) -> Clarification | None:
    return session.scalars(
        select(Clarification).where(
            Clarification.id == question_id,
            Clarification.scenario_id == scenario_id,
        )
    ).first()


def add_clarification(
    session: Session,
    scenario_id: str,
    key: str,
    question: str,
    options: list[str],
) -> dict:
    row = Clarification(
        id=uid("question"),
        scenario_id=scenario_id,
        key=key,
        question=question,
        options=options,
        answer=None,
        status="pending",
        created_at=now(),
    )
    session.add(row)
    return clarification_to_dict(row)


def answer_clarification(session: Session, question_id: str, answer: str) -> None:
    row = session.get(Clarification, question_id)
    if row:
        row.answer = answer
        row.status = "answered"


def create_evaluation(session: Session, evaluation_id: str, scenario_id: str) -> dict:
    created = now()
    row = Evaluation(
        id=evaluation_id,
        scenario_id=scenario_id,
        status="queued",
        progress=0,
        stage="queued",
        message="等待模型服务",
        results=None,
        created_at=created,
        completed_at=None,
    )
    session.add(row)
    return evaluation_to_dict(row)


def get_evaluation(session: Session, evaluation_id: str) -> dict | None:
    row = session.get(Evaluation, evaluation_id)
    return evaluation_to_dict(row) if row else None


def get_evaluation_results(session: Session, evaluation_id: str) -> dict | None:
    row = session.get(Evaluation, evaluation_id)
    return row.results if row else None


def get_latest_evaluation(session: Session, scenario_id: str) -> dict | None:
    row = session.scalars(
        select(Evaluation)
        .where(Evaluation.scenario_id == scenario_id)
        .order_by(Evaluation.created_at.desc())
        .limit(1)
    ).first()
    return evaluation_to_dict(row) if row else None


def update_evaluation(session: Session, evaluation_id: str, fields: dict[str, Any]) -> dict | None:
    row = session.get(Evaluation, evaluation_id)
    if not row:
        return None
    for key, value in fields.items():
        setattr(row, key, value)
    return evaluation_to_dict(row)


def replace_evidence(session: Session, evaluation_id: str, items: list[dict]) -> None:
    session.execute(delete(Evidence).where(Evidence.evaluation_id == evaluation_id))
    for index, item in enumerate(items, start=1):
        session.add(
            Evidence(
                id=f"evidence_{evaluation_id[-8:]}_{index:03d}",
                evaluation_id=evaluation_id,
                metric=item["metric"],
                baseline_value=item["baseline"],
                candidate_value=item["candidate"],
                delta=item["delta"],
                entity=item["entity"],
                explanation_type=item["type"],
                confidence=item["confidence"],
            )
        )


def list_evidence(session: Session, evaluation_id: str) -> list[dict]:
    rows = session.scalars(
        select(Evidence).where(Evidence.evaluation_id == evaluation_id).order_by(Evidence.id.asc())
    ).all()
    return [evidence_to_dict(row) for row in rows]


def upsert_recommendation(session: Session, evaluation_id: str, payload: dict) -> dict:
    row = session.scalars(
        select(Recommendation)
        .where(Recommendation.evaluation_id == evaluation_id)
        .order_by(Recommendation.created_at.desc())
        .limit(1)
    ).first()
    if row:
        row.payload = payload
    else:
        row = Recommendation(
            id=uid("recommendation"),
            evaluation_id=evaluation_id,
            payload=payload,
            approval_status="pending",
            created_at=now(),
        )
        session.add(row)
    return recommendation_to_dict(row)


def get_latest_recommendation(session: Session, evaluation_id: str) -> dict | None:
    row = session.scalars(
        select(Recommendation)
        .where(Recommendation.evaluation_id == evaluation_id)
        .order_by(Recommendation.created_at.desc())
        .limit(1)
    ).first()
    return recommendation_to_dict(row) if row else None


def set_recommendation_status(session: Session, evaluation_id: str, status: str) -> None:
    row = session.scalars(
        select(Recommendation)
        .where(Recommendation.evaluation_id == evaluation_id)
        .order_by(Recommendation.created_at.desc())
        .limit(1)
    ).first()
    if row:
        row.approval_status = status


def add_event(session: Session, scenario_id: str, event_type: str, actor: str, content: str, version: int) -> dict:
    row = AppEvent(
        id=uid("event"),
        scenario_id=scenario_id,
        type=event_type,
        actor=actor,
        content=content,
        version=version,
        created_at=now(),
    )
    session.add(row)
    return event_to_dict(row)


def list_events(session: Session, scenario_id: str) -> list[dict]:
    rows = session.scalars(
        select(AppEvent).where(AppEvent.scenario_id == scenario_id).order_by(AppEvent.created_at.asc())
    ).all()
    return [event_to_dict(row) for row in rows]


def add_version_snapshot(
    session: Session,
    scenario_id: str,
    version: int,
    status: str,
    snapshot: dict,
    note: str,
) -> dict:
    row = ScenarioVersion(
        id=uid("scenario_version"),
        scenario_id=scenario_id,
        version=version,
        status=status,
        snapshot=snapshot,
        note=note,
        created_at=now(),
    )
    session.add(row)
    return version_to_dict(row)


def list_versions(session: Session, scenario_id: str) -> list[dict]:
    rows = session.scalars(
        select(ScenarioVersion)
        .where(ScenarioVersion.scenario_id == scenario_id)
        .order_by(ScenarioVersion.version.asc())
    ).all()
    return [version_to_dict(row) for row in rows]
