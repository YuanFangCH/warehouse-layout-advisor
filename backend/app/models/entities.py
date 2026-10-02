from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    warehouse_name: Mapped[str] = mapped_column(String(200))
    data_status: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer)
    business_objectives: Mapped[list] = mapped_column(JSON)
    modification_scope: Mapped[str] = mapped_column(String(120))
    budget_policy: Mapped[dict] = mapped_column(JSON)
    performance_floor: Mapped[dict] = mapped_column(JSON)
    analysis_period: Mapped[str] = mapped_column(String(64))
    risk_preference: Mapped[str] = mapped_column(String(64))
    candidate_count: Mapped[int] = mapped_column(Integer)
    assumptions: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Clarification(Base):
    __tablename__ = "clarifications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    key: Mapped[str] = mapped_column(String(64))
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON)
    answer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    status: Mapped[str] = mapped_column(String(32))
    progress: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(String(200))
    results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(ForeignKey("evaluations.id"))
    metric: Mapped[str] = mapped_column(String(120))
    baseline_value: Mapped[str] = mapped_column(String(120))
    candidate_value: Mapped[str] = mapped_column(String(120))
    delta: Mapped[str] = mapped_column(String(120))
    entity: Mapped[str] = mapped_column(String(120))
    explanation_type: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[str] = mapped_column(String(32))


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(ForeignKey("evaluations.id"))
    payload: Mapped[dict] = mapped_column(JSON)
    approval_status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioVersion(Base):
    __tablename__ = "scenario_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    snapshot: Mapped[dict] = mapped_column(JSON)
    note: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AppEvent(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"))
    type: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
