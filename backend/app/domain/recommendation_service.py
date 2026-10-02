from ..errors import AppError
from ..persistence import repositories as repo
from ..persistence.database import session_scope


def get_evidence(evaluation_id: str) -> list[dict]:
    with session_scope() as session:
        if not repo.get_evaluation(session, evaluation_id):
            raise AppError("EVALUATION_NOT_FOUND", "评估任务不存在", status_code=404)
        return repo.list_evidence(session, evaluation_id)


def get_recommendation(evaluation_id: str) -> dict:
    with session_scope() as session:
        if not repo.get_evaluation(session, evaluation_id):
            raise AppError("EVALUATION_NOT_FOUND", "评估任务不存在", status_code=404)
        recommendation = repo.get_latest_recommendation(session, evaluation_id)
        if not recommendation:
            raise AppError("RECOMMENDATION_NOT_READY", "推荐结果尚未生成", status_code=404)
        return recommendation
