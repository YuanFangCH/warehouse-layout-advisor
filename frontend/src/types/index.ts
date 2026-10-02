export type ScenarioStatus =
  | 'collecting'
  | 'clarifying'
  | 'ready'
  | 'evaluating'
  | 'awaiting_approval'
  | 'approved'
  | 'revised';

export type EvaluationStatus = 'queued' | 'running' | 'completed' | 'failed';

export interface Project {
  id: string;
  name: string;
  warehouse_name: string;
  data_status: string;
  created_at: string;
}

export interface BusinessObjective {
  code: string;
  priority: number;
}

export interface Scenario {
  id: string;
  project_id: string;
  title: string;
  status: ScenarioStatus;
  version: number;
  business_objectives: BusinessObjective[];
  modification_scope: string;
  budget_policy: { amount: number; mode: string };
  performance_floor: { throughput: string; stress_test?: boolean };
  analysis_period: string;
  risk_preference: string;
  candidate_count: number;
  assumptions: string[];
  created_at: string;
  updated_at: string;
  latest_evaluation?: Evaluation | null;
}

export interface Message {
  id: string;
  scenario_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ClarificationQuestion {
  id: string;
  key: string;
  question: string;
  type: 'single_choice';
  options: string[];
  status: 'pending' | 'answered';
  created_at: string;
}

export interface Evaluation {
  id: string;
  scenario_id: string;
  status: EvaluationStatus;
  progress: number;
  stage: string;
  message: string;
  schemes?: Scheme[];
  created_at: string;
  completed_at?: string | null;
}

export interface Scheme {
  id: string;
  label: string;
  note: string;
  score: number;
}

export interface Evidence {
  id: string;
  evaluation_id: string;
  metric: string;
  baseline_value: string;
  candidate_value: string;
  delta: string;
  entity: string;
  explanation_type: string;
  confidence: string;
}

export interface Insight {
  id: string;
  type: string;
  title: string;
  business_explanation: string;
  evidence_refs: string[];
  confidence: string;
}

export interface Recommendation {
  recommended_option: string;
  alternative_options: string[];
  reasons: string[];
  tradeoffs: string[];
  risks: string[];
  assumptions: string[];
  approval_status: 'pending' | 'approved';
}

export interface AppEvent {
  id: string;
  scenario_id: string;
  type: string;
  actor: string;
  content: string;
  version: number;
  created_at: string;
}

export interface ScenarioVersion {
  id: string;
  scenario_id: string;
  version: number;
  status: ScenarioStatus;
  snapshot: Record<string, unknown>;
  note: string;
  created_at: string;
}

export interface StreamEvent {
  seq?: number;
  type: string;
  stage?: string;
  progress?: number;
  message?: string;
  created_at?: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface MessageResponse {
  scenario: Scenario;
  assistant_message: Message;
  pending_questions: ClarificationQuestion[];
  business_patch: Record<string, unknown>;
  sync_message?: string | null;
}

export const STATUS_LABEL: Record<ScenarioStatus, string> = {
  collecting: '收集需求',
  clarifying: '需求澄清',
  ready: '已就绪',
  evaluating: '评估中',
  awaiting_approval: '待确认',
  approved: '已确认',
  revised: '已修订',
};

export const OBJECTIVE_LABEL: Record<string, string> = {
  minimize_picking_distance: '降低拣选距离',
  minimize_modification_cost: '控制改造成本',
};

export const STAGES = [
  { id: 'clarify', label: '需求澄清' },
  { id: 'translate', label: '业务参数' },
  { id: 'interpret', label: '结果解读' },
  { id: 'recommend', label: '决策建议' },
];

export function stageForStatus(status: ScenarioStatus): string {
  if (status === 'collecting' || status === 'clarifying') return 'clarify';
  if (status === 'ready' || status === 'revised') return 'translate';
  if (status === 'evaluating') return 'interpret';
  return 'recommend';
}
