import type { Project, Scenario } from '../types';
import { get, post } from './httpClient';

export function fetchProjects(): Promise<Project[]> {
  return get<Project[]>('/projects');
}

export function createProject(input: {
  name: string;
  warehouse_name?: string;
  data_status?: string;
}): Promise<Project> {
  return post<Project>('/projects', input);
}

export function fetchScenarios(projectId: string): Promise<Scenario[]> {
  return get<Scenario[]>(`/projects/${projectId}/scenarios`);
}

export function createScenario(projectId: string, title: string): Promise<Scenario> {
  return post<Scenario>(`/projects/${projectId}/scenarios`, { title });
}
