import type { Evaluation, Evidence, Insight, Recommendation } from '../types';
import { get, post } from './httpClient';

export function startEvaluation(
  scenarioId: string,
  clientVersion: number,
): Promise<Evaluation> {
  return post<Evaluation>(`/scenarios/${scenarioId}/evaluations`, {
    client_version: clientVersion,
  });
}

export function fetchEvaluation(evaluationId: string): Promise<Evaluation> {
  return get<Evaluation>(`/evaluations/${evaluationId}`);
}

export function fetchEvidence(evaluationId: string): Promise<Evidence[]> {
  return get<Evidence[]>(`/evaluations/${evaluationId}/evidence`);
}

export function fetchInsights(evaluationId: string): Promise<Insight[]> {
  return get<Insight[]>(`/evaluations/${evaluationId}/insights`);
}

export function fetchRecommendation(evaluationId: string): Promise<Recommendation> {
  return get<Recommendation>(`/evaluations/${evaluationId}/recommendation`);
}
