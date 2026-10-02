import { Edit3, Play, CheckCheck } from 'lucide-react';
import { motion } from 'motion/react';

import { fadeUp } from '../design/motion';
import type { Scenario } from '../types';
import { OBJECTIVE_LABEL } from '../types';

interface ConditionSummaryProps {
  scenario: Scenario;
  canConfirm: boolean;
  busy: boolean;
  onEdit: () => void;
  onConfirm: () => void;
  onEvaluate: () => void;
}

function budgetText(scenario: Scenario): string {
  const amount = scenario.budget_policy?.amount ?? 0;
  const mode = scenario.budget_policy?.mode;
  const modeLabel = mode === 'hard_limit' ? '硬约束' : mode === 'pending' ? '待确认' : '软约束';
  return `${(amount / 10000).toFixed(0)} 万元 · ${modeLabel}`;
}

export default function ConditionSummary({
  scenario,
  canConfirm,
  busy,
  onEdit,
  onConfirm,
  onEvaluate,
}: ConditionSummaryProps) {
  const objectives = scenario.business_objectives
    .map((item) => OBJECTIVE_LABEL[item.code] ?? item.code)
    .join('、');

  const rows = [
    ['主要目标', objectives || '尚未确认'],
    ['改造范围', scenario.modification_scope],
    ['预算政策', budgetText(scenario)],
    ['性能底线', scenario.performance_floor?.throughput === 'not_below_baseline' ? '吞吐量不低于当前布局' : scenario.performance_floor?.throughput === 'allow_temporary_dip' ? '允许短期轻微下降' : '尚未确认'],
    ['分析周期', '最近 30 天'],
    ['风险偏好', scenario.risk_preference === 'conservative' ? '偏保守' : scenario.risk_preference],
    ['候选数量', `${scenario.candidate_count} 个`],
  ];

  return (
    <motion.section
      className="panel scenario-panel"
      variants={fadeUp}
      initial="hidden"
      animate="visible"
    >
      <div className="panel-heading compact">
        <div>
          <span className="eyebrow">业务语义模型</span>
          <h2>当前分析条件</h2>
        </div>
        <span className="version-tag">v{scenario.version}</span>
      </div>
      <div className="scenario-summary">
        {rows.map(([label, value]) => (
          <div className="summary-row" key={label}>
            <span className="summary-label">{label}</span>
            <span className="summary-value">{value}</span>
          </div>
        ))}
      </div>
      <div className="panel-actions">
        <button className="outline-button full-width" type="button" onClick={onEdit}>
          <Edit3 size={14} />
          编辑确认条件
        </button>
        {scenario.status === 'ready' ? (
          <button className="primary-button full-width" type="button" disabled={busy} onClick={onEvaluate}>
            <Play size={14} />
            开始方案比较
          </button>
        ) : null}
        {canConfirm ? (
          <button className="primary-button full-width" type="button" disabled={busy} onClick={onConfirm}>
            <CheckCheck size={14} />
            确认并生成新版本
          </button>
        ) : null}
      </div>
    </motion.section>
  );
}
