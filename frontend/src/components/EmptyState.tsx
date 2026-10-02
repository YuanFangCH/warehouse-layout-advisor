import type { ReactNode } from 'react';

interface EmptyStateProps {
  eyebrow?: string;
  title: string;
  description: string;
  action?: ReactNode;
}

export default function EmptyState({ eyebrow, title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
      <h3>{title}</h3>
      <p>{description}</p>
      {action ? <div className="empty-action">{action}</div> : null}
    </div>
  );
}
