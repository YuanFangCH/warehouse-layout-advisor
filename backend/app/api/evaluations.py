import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..domain import insight_service, recommendation_service, scenario_service
from ..errors import AppError
from ..models.schemas import EvaluationStart
from ..orchestration.event_publisher import publisher
from ..orchestration.job_manager import submit


router = APIRouter(prefix="/api")


@router.post("/scenarios/{scenario_id}/evaluations")
def start_evaluation(scenario_id: str, payload: EvaluationStart) -> dict:
    evaluation = scenario_service.start_evaluation(scenario_id, payload.client_version)
    submit(evaluation["id"])
    return evaluation


@router.get("/evaluations/{evaluation_id}")
def get_evaluation(evaluation_id: str) -> dict:
    evaluation = scenario_service.get_evaluation(evaluation_id)
    if not evaluation:
        raise AppError("EVALUATION_NOT_FOUND", "评估任务不存在", status_code=404)
    return evaluation


@router.get("/evaluations/{evaluation_id}/events")
def evaluation_events(evaluation_id: str) -> list[dict]:
    if not scenario_service.get_evaluation(evaluation_id):
        raise AppError("EVALUATION_NOT_FOUND", "评估任务不存在", status_code=404)
    return publisher.events_since(evaluation_id)


@router.get("/evaluations/{evaluation_id}/stream")
async def evaluation_stream(evaluation_id: str) -> StreamingResponse:
    if not scenario_service.get_evaluation(evaluation_id):
        raise AppError("EVALUATION_NOT_FOUND", "评估任务不存在", status_code=404)

    async def event_stream():
        loop = asyncio.get_running_loop()
        deadline = loop.time() + 120
        last_seq = 0
        while True:
            for event in publisher.events_since(evaluation_id, last_seq):
                last_seq = event["seq"]
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            current = scenario_service.get_evaluation(evaluation_id)
            if current and current["status"] in {"completed", "failed"}:
                break
            if loop.time() > deadline:
                yield "data: {\"type\": \"evaluation.timeout\", \"message\": \"评估超时\"}\n\n"
                break
            await asyncio.sleep(0.25)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/evaluations/{evaluation_id}/evidence")
def evaluation_evidence(evaluation_id: str) -> list[dict]:
    return recommendation_service.get_evidence(evaluation_id)


@router.get("/evaluations/{evaluation_id}/insights")
def evaluation_insights(evaluation_id: str) -> list[dict]:
    return insight_service.get_insights(evaluation_id)


@router.get("/evaluations/{evaluation_id}/recommendation")
def evaluation_recommendation(evaluation_id: str) -> dict:
    return recommendation_service.get_recommendation(evaluation_id)
