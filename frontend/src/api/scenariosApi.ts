import type { AppEvent, Scenario, ScenarioVersion } from '../types';
import { get, patch, post } from './httpClient';

export function fetchScenario(scenarioId: string): Promise<Scenario> {
  return get<Scenario>(`/scenarios/${scenarioId}`);
}

export function updateScenario(
  scenarioId: string,
  body: Record<string, unknown>,
): Promise<Scenario> {
  return patch<Scenario>(`/scenarios/${scenarioId}`, body);
}

export function confirmScenario(
  scenarioId: string,
  body: { client_version: number; confirmed_fields: string[] },
): Promise<Scenario> {
  return post<Scenario>(`/scenarios/${scenarioId}/confirm`, body);
}

export function fetchVersions(scenarioId: string): Promise<ScenarioVersion[]> {
  return get<ScenarioVersion[]>(`/scenarios/${scenarioId}/versions`);
}

export function fetchEvents(scenarioId: string): Promise<AppEvent[]> {
  return get<AppEvent[]>(`/scenarios/${scenarioId}/events`);
}
