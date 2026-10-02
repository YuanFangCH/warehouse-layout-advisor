import type { Scenario } from '../types';
import { post } from './httpClient';

export function approveScenario(
  scenarioId: string,
  body: { client_version: number; selected_option: string; approval_note: string },
): Promise<Scenario> {
  return post<Scenario>(`/scenarios/${scenarioId}/approve`, body);
}

export function reviseScenario(
  scenarioId: string,
  body: { client_version: number; note: string },
): Promise<Scenario> {
  return post<Scenario>(`/scenarios/${scenarioId}/revise`, body);
}
