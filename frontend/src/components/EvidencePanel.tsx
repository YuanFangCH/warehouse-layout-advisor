import { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, Lightbulb, LineChart, Target } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';

import { expand, fadeUp } from '../design/motion';
import type { Evidence, Insight, Scheme } from '../types';
import EmptyState from './EmptyState';

interface EvidencePanelProps {
  schemes: Scheme[];
  evidence: Evidence[];
  insights: Insight[];
  recommendedOption?: string;
}

export default function EvidencePanel({ schemes, evidence, insights, recommendedOption }: EvidencePanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [activeInsight, setActiveInsight] = useState<Insight | null>(insights[0] ?? null);

  useEffect(() => {
    setActiveInsight(insights[0] ?? null);
  }, [insights]);

  const kpis = evidence.slice(0, 4);

  return (
    <motion.section
      className="panel evidence-panel"
      variants={fadeUp}
      initial="hidden"
      animate="visible"
    >
      <div className="panel-heading compact">
        <div>
          <span className="eyebrow">可追溯证据</span>
          <h2>方案比较</h2>
        </div>
        <button
          className="icon-button"
          type="button"
          onClick={() => setExpanded((value) => !value)}
          aria-label={expanded ? '收起证据' : '展开证据'}
          title={expanded ? '收起证据' : '展开证据'}
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>
      {expanded || schemes.length ? (
        <div className="evidence-content">
          <div className="evidence-intro">基线：当前布局 · 最近 30 天订单 · 统一资源配置</div>
          {schemes.length ? (
            <div className="scheme-list">
              {schemes.map((scheme, index) => (
                <motion.div
                  className={`scheme-row ${scheme.id === recommendedOption ? 'recommended' : ''}`}
                  key={scheme.id}
                  variants={fadeUp}
                  initial="hidden"
                  animate="visible"
                  custom={index}
                >
                  <span className="scheme-marker" />
                  <div>
                    <div className="scheme-name">{scheme.label}</div>
                    <div className="scheme-note">{scheme.note}</div>
                  </div>
                  <span className="scheme-score">{scheme.score}</span>
                </motion.div>
              ))}
            </div>
          ) : null}
          {kpis.length ? (
            <div className="kpi-grid">
              {kpis.map((item) => (
                <div className="kpi" key={item.id}>
                  <div className="kpi-label">{item.metric}</div>
                  <div className="kpi-value">{item.delta}</div>
                  <div className="kpi-change">{item.entity}</div>
                </div>
              ))}
            </div>
          ) : null}
          {insights.length ? (
            <div className="insight-block">
              <div className="insight-head">
                <Lightbulb size={13} />
                <span>Agent 解读</span>
              </div>
              <div className="insight-tabs">
                {insights.map((insight) => (
                  <button
                    type="button"
                    key={insight.id}
                    className={activeInsight?.id === insight.id ? 'active' : ''}
                    onClick={() => setActiveInsight(insight)}
                  >
                    {insight.title}
                  </button>
                ))}
              </div>
              {activeInsight ? (
                <p className="insight-copy">{activeInsight.business_explanation}</p>
              ) : null}
            </div>
          ) : null}
          <AnimatePresence initial={false}>
            {expanded ? (
              <motion.div
                className="evidence-table"
                variants={expand}
                initial="hidden"
                animate="visible"
                exit="exit"
              >
                <div className="evidence-table-head">
                  <LineChart size={13} />
                  <span>KPI 明细</span>
                </div>
                {evidence.map((item) => (
                  <div className="evidence-row" key={item.id}>
                    <div>
                      <strong>{item.metric}</strong>
                      <span>{item.entity}</span>
                    </div>
                    <div>
                      <span>基线 {item.baseline_value}</span>
                      <span>候选 {item.candidate_value}</span>
                    </div>
                    <Target size={13} />
                    <strong>{item.delta}</strong>
                  </div>
                ))}
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      ) : (
        <EmptyState
          eyebrow="可追溯证据"
          title="等待方案比较"
          description="完成需求澄清并确认条件后，这里会出现基线、候选方案和关键 KPI。"
        />
      )}
    </motion.section>
  );
}
