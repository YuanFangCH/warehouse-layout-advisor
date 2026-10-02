import { AlertTriangle, Check, GitCompareArrows, RotateCcw, Scale } from 'lucide-react';
import { motion } from 'motion/react';

import { fadeUp } from '../design/motion';
import type { Recommendation, Scenario, Scheme } from '../types';
import EmptyState from './EmptyState';

interface RecommendationPanelProps {
  recommendation?: Recommendation;
  scenario: Scenario;
  schemes: Scheme[];
  busy: boolean;
  onApprove: (selectedOption: string, note: string) => void;
  onRevise: () => void;
}

function schemeLabel(schemes: Scheme[], optionId: string): string {
  const scheme = schemes.find((item) => item.id === optionId);
  return scheme ? scheme.label : optionId;
}

export default function RecommendationPanel({
  recommendation,
  scenario,
  schemes,
  busy,
  onApprove,
  onRevise,
}: RecommendationPanelProps) {
  if (!recommendation) {
    return (
      <motion.section
        className="panel recommendation-panel"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
      >
        <EmptyState
          eyebrow="决策建议"
          title="等待分析条件"
          description="确认业务目标后，Agent 才会形成推荐方案。"
        />
      </motion.section>
    );
  }

  const approved = recommendation.approval_status === 'approved';
  const recommendedLabel = schemeLabel(schemes, recommendation.recommended_option);

  return (
    <motion.section
      className="panel recommendation-panel"
      variants={fadeUp}
      initial="hidden"
      animate="visible"
    >
      <div className="recommendation-header">
        <div>
          <span className="eyebrow">决策建议</span>
          <h2>推荐方案</h2>
        </div>
        <span className={`recommendation-badge ${approved ? 'approved' : ''}`}>
          {approved ? <Check size={12} /> : null}
          {approved ? '已确认' : '待确认'}
        </span>
      </div>
      <div className="recommendation-body">
        <div className="recommendation-title">{recommendedLabel}</div>
        <div className="recommendation-copy">
          在当前“{scenario.risk_preference === 'conservative' ? '偏保守' : scenario.risk_preference}”风险偏好下，该方案更适合作为首选。
        </div>
        <ul className="reason-list">
          {recommendation.reasons.map((reason, index) => (
            <motion.li
              key={reason}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              custom={index}
            >
              {reason}
            </motion.li>
          ))}
        </ul>
        {recommendation.tradeoffs.length ? (
          <div className="tradeoff-box">
            <Scale size={12} />
            <div>
              {recommendation.tradeoffs.map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
          </div>
        ) : null}
        {recommendation.risks.length ? (
          <ul className="risk-list">
            {recommendation.risks.map((risk, index) => (
              <motion.li
                key={risk}
                variants={fadeUp}
                initial="hidden"
                animate="visible"
                custom={index}
              >
                {risk}
              </motion.li>
            ))}
          </ul>
        ) : null}
        {recommendation.assumptions.length ? (
          <div className="assumption-box">
            <AlertTriangle size={12} />
            <div>
              {recommendation.assumptions.map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
          </div>
        ) : null}
        {!approved && scenario.status === 'awaiting_approval' ? (
          <div className="recommendation-actions">
            <button
              className="primary-button"
              type="button"
              disabled={busy}
              onClick={() => onApprove(recommendation.recommended_option, '')}
            >
              <Check size={14} />
              确认采用
            </button>
            <button className="outline-button" type="button" disabled={busy} onClick={onRevise}>
              <RotateCcw size={14} />
              调整重算
            </button>
          </div>
        ) : null}
        {!approved && scenario.status !== 'awaiting_approval' ? (
          <div className="recommendation-actions">
            <button className="outline-button" type="button" disabled={busy} onClick={onRevise}>
              <GitCompareArrows size={14} />
              调整条件重算
            </button>
          </div>
        ) : null}
      </div>
    </motion.section>
  );
}
