import { Activity, CheckCircle2, AlertTriangle } from 'lucide-react';
import { motion } from 'motion/react';

import { DURATIONS, EASE_OUT, fadeUp } from '../design/motion';
import type { Evaluation } from '../types';

interface EvaluationProgressProps {
  evaluation: Evaluation;
  streamProgress: number | null;
  streamStage: string;
  streamMessage: string;
  streamStatus: 'running' | 'completed' | 'failed' | null;
}

export default function EvaluationProgress({
  evaluation,
  streamProgress,
  streamStage,
  streamMessage,
  streamStatus,
}: EvaluationProgressProps) {
  const progress = streamProgress ?? evaluation.progress;
  const stage = streamStage || evaluation.stage;
  const message = streamMessage || evaluation.message;
  const completed = streamStatus === 'completed' || evaluation.status === 'completed';
  const failed = streamStatus === 'failed' || evaluation.status === 'failed';

  return (
    <motion.section
      className="panel evaluation-progress"
      variants={fadeUp}
      initial="hidden"
      animate="visible"
    >
      <div className="panel-heading compact">
        <div>
          <span className="eyebrow">评估任务</span>
          <h2>{completed ? '评估完成' : failed ? '评估失败' : '正在评估'}</h2>
        </div>
        {completed ? (
          <span className="status-badge status-green">
            <CheckCircle2 size={12} /> 已完成
          </span>
        ) : failed ? (
          <span className="status-badge status-red">
            <AlertTriangle size={12} /> 失败
          </span>
        ) : (
          <span className="status-badge status-blue">
            <Activity size={12} /> {progress}%
          </span>
        )}
      </div>
      <div className="progress-body">
        <div className="progress-track">
          <motion.div
            className="progress-fill"
            animate={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
            transition={{ duration: DURATIONS.panel, ease: EASE_OUT }}
          />
        </div>
        <div className="progress-meta">
          <span>{stage === 'queued' ? '排队中' : `阶段：${stage}`}</span>
          <span>{message}</span>
        </div>
      </div>
    </motion.section>
  );
}
