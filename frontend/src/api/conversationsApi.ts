import type { ClarificationQuestion, Message, MessageResponse } from '../types';
import { get, post } from './httpClient';

export function fetchMessages(scenarioId: string): Promise<Message[]> {
  return get<Message[]>(`/scenarios/${scenarioId}/messages`);
}

export function sendMessage(
  scenarioId: string,
  body: { message: string; client_version: number },
): Promise<MessageResponse> {
  return post<MessageResponse>(`/scenarios/${scenarioId}/messages`, body);
}

export function fetchClarifications(scenarioId: string): Promise<ClarificationQuestion[]> {
  return get<ClarificationQuestion[]>(`/scenarios/${scenarioId}/clarifications`);
}

export function answerClarification(
  scenarioId: string,
  questionId: string,
  body: { answer: string; client_version: number },
): Promise<MessageResponse> {
  return post<MessageResponse>(`/scenarios/${scenarioId}/clarifications/${questionId}/answer`, body);
}
