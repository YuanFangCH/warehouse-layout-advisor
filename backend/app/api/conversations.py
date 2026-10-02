from fastapi import APIRouter

from ..domain import clarification_service
from ..models.schemas import ClarificationAnswer, MessageCreate


router = APIRouter(prefix="/api")


@router.get("/scenarios/{scenario_id}/messages")
def list_messages(scenario_id: str) -> list[dict]:
    return clarification_service.list_messages(scenario_id)


@router.post("/scenarios/{scenario_id}/messages")
def post_message(scenario_id: str, payload: MessageCreate) -> dict:
    return clarification_service.handle_message(scenario_id, payload.message, payload.client_version)


@router.get("/scenarios/{scenario_id}/clarifications")
def list_clarifications(scenario_id: str) -> list[dict]:
    return clarification_service.pending_questions(scenario_id)


@router.post("/scenarios/{scenario_id}/clarifications/{question_id}/answer")
def answer_clarification(scenario_id: str, question_id: str, payload: ClarificationAnswer) -> dict:
    return clarification_service.answer_question(scenario_id, question_id, payload.answer, payload.client_version)
