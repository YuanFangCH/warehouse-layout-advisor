import { useState } from 'react';

import type { Scenario } from '../types';
import Modal from './Modal';

interface ConditionEditModalProps {
  open: boolean;
  scenario: Scenario;
  busy: boolean;
  onClose: () => void;
  onSave: (patch: Record<string, unknown>) => void;
}

export default function ConditionEditModal({ open, scenario, busy, onClose, onSave }: ConditionEditModalProps) {
  const [modificationScope, setModificationScope] = useState(scenario.modification_scope);
  const [budgetMode, setBudgetMode] = useState(scenario.budget_policy.mode);
  const [performanceFloor, setPerformanceFloor] = useState(scenario.performance_floor.throughput);
  const [riskPreference, setRiskPreference] = useState(scenario.risk_preference);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    onSave({
      modification_scope: modificationScope,
      budget_policy: { amount: scenario.budget_policy.amount, mode: budgetMode },
      performance_floor: { throughput: performanceFloor },
      risk_preference: riskPreference,
    });
  };

  return (
    <Modal
      open={open}
      eyebrow="确认条件"
      title="编辑分析条件"
      onClose={onClose}
      footer={
        <>
          <button className="secondary-button" type="button" onClick={onClose}>
            取消
          </button>
          <button className="primary-button" type="submit" form="condition-form" disabled={busy}>
            保存并生成新版本
          </button>
        </>
      }
    >
      <form className="modal-form" id="condition-form" onSubmit={submit}>
        <label className="form-field">
          <span className="form-label">改造范围</span>
          <select
            className="form-select"
            value={modificationScope}
            onChange={(event) => setModificationScope(event.target.value)}
          >
            <option value="仅调整货位，不移动货架和主通道">仅调整货位，不移动货架和主通道</option>
            <option value="允许局部移动货架，但不改主通道">允许局部移动货架，但不改主通道</option>
            <option value="只把预算作为限制，布局可以重新设计">只把预算作为限制，布局可以重新设计</option>
          </select>
        </label>
        <label className="form-field">
          <span className="form-label">预算性质</span>
          <select
            className="form-select"
            value={budgetMode}
            onChange={(event) => setBudgetMode(event.target.value)}
          >
            <option value="hard_limit">硬约束</option>
            <option value="soft_limit">软约束，可超出后解释</option>
          </select>
        </label>
        <label className="form-field">
          <span className="form-label">性能底线</span>
          <select
            className="form-select"
            value={performanceFloor}
            onChange={(event) => setPerformanceFloor(event.target.value)}
          >
            <option value="not_below_baseline">吞吐量不得低于当前布局</option>
            <option value="allow_temporary_dip">允许短期轻微下降</option>
          </select>
        </label>
        <label className="form-field">
          <span className="form-label">实施风险偏好</span>
          <select
            className="form-select"
            value={riskPreference}
            onChange={(event) => setRiskPreference(event.target.value)}
          >
            <option value="conservative">偏保守</option>
            <option value="balance">平衡</option>
            <option value="aggressive">偏进取</option>
          </select>
        </label>
      </form>
    </Modal>
  );
}
