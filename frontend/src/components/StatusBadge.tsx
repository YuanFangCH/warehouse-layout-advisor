import type { ScenarioStatus } from '../types';
import { STATUS_LABEL } from '../types';

const STATUS_CLASS: Record<ScenarioStatus, string> = {
  collecting: 'status-neutral',
  clarifying: 'status-amber',
  ready: 'status-blue',
  evaluating: 'status-blue',
  awaiting_approval: 'status-amber',
  approved: 'status-green',
  revised: 'status-neutral',
};

interface StatusBadgeProps {
  status: ScenarioStatus;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`status-badge ${STATUS_CLASS[status]}`}>{STATUS_LABEL[status]}</span>;
}
