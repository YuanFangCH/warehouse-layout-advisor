import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from ..models.entities import (
    AppEvent,
    Base,
    Clarification,
    Message,
    Project,
    Scenario,
    ScenarioVersion,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = ROOT / "backend" / "data" / "warehouse_decision.db"


def get_db_path() -> Path:
    override = os.environ.get("WAREHOUSE_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


def get_engine():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})


@contextmanager
def session_scope() -> Iterator[Session]:
    engine = get_engine()
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    Base.metadata.create_all(get_engine())
    seed_defaults()


def seed_defaults() -> None:
    with session_scope() as session:
        if session.scalar(select(func.count()).select_from(Project)):
            return

        created = datetime.now(timezone.utc)
        project_id = "project_east_001"
        scenario_id = "scenario_demo_001"

        session.add(
            Project(
                id=project_id,
                name="示例仓库",
                warehouse_name="示例仓库",
                data_status="可开始分析",
                created_at=created,
            )
        )
        session.add(
            Scenario(
                id=scenario_id,
                project_id=project_id,
                title="降低拣选距离 · 低改造范围",
                status="clarifying",
                version=3,
                business_objectives=[
                    {"code": "minimize_picking_distance", "priority": 1},
                    {"code": "minimize_modification_cost", "priority": 2},
                ],
                modification_scope="尚未确认",
                budget_policy={"amount": 200000, "mode": "pending"},
                performance_floor={"throughput": "pending"},
                analysis_period="recent_30_days",
                risk_preference="conservative",
                candidate_count=3,
                assumptions=["订单范围默认采用最近 30 天，代表近期作业结构。"],
                created_at=created,
                updated_at=created,
            )
        )
        session.add(
            Message(
                id="msg_demo_001",
                scenario_id=scenario_id,
                role="assistant",
                content="我会先把你的仓库调整目标澄清成一组可验证的业务条件。你可以直接说想解决什么问题，例如：“尽量少改现有仓库，优先降低拣选距离，预算控制在 20 万元。”",
                created_at=created,
            )
        )
        session.add(
            Clarification(
                id="question_scope",
                scenario_id=scenario_id,
                key="modification_scope",
                question="“尽量少改”会直接影响候选方案的范围。你希望它代表哪一种？",
                options=[
                    "仅调整货位，不移动货架和主通道",
                    "允许局部移动货架，但不改主通道",
                    "只把预算作为限制，布局可以重新设计",
                ],
                answer=None,
                status="pending",
                created_at=created,
            )
        )
        session.add(
            AppEvent(
                id="event_demo_001",
                scenario_id=scenario_id,
                type="scenario_created",
                actor="system",
                content="创建分析场景",
                version=1,
                created_at=created,
            )
        )

        snapshots = [
            (1, "collecting", "创建分析场景", {"status": "collecting", "business_objectives": []}),
            (
                2,
                "clarifying",
                "识别业务目标：降低拣选距离、控制改造成本",
                {
                    "status": "clarifying",
                    "business_objectives": [
                        {"code": "minimize_picking_distance", "priority": 1},
                        {"code": "minimize_modification_cost", "priority": 2},
                    ],
                },
            ),
            (
                3,
                "clarifying",
                "提出改造范围澄清问题",
                {
                    "status": "clarifying",
                    "modification_scope": "尚未确认",
                    "budget_policy": {"amount": 200000, "mode": "pending"},
                },
            ),
        ]
        for index, (version, status, note, snapshot) in enumerate(snapshots, start=1):
            session.add(
                ScenarioVersion(
                    id=f"scenario_version_demo_{index}",
                    scenario_id=scenario_id,
                    version=version,
                    status=status,
                    snapshot=snapshot,
                    note=note,
                    created_at=created,
                )
            )
