from ..errors import AppError
from ..persistence import repositories as repo
from ..persistence.database import session_scope


def get_insights(evaluation_id: str) -> list[dict]:
    with session_scope() as session:
        if not repo.get_evaluation(session, evaluation_id):
            raise AppError("EVALUATION_NOT_FOUND", "评估任务不存在", status_code=404)
        results = repo.get_evaluation_results(session, evaluation_id) or {}
        return results.get("insights", [])
