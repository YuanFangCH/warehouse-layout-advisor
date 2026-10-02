import { FileText, MessageSquare, RefreshCw, CheckCircle2, CircleDot } from 'lucide-react';
import { motion } from 'motion/react';

import { fadeUp } from '../design/motion';
import type { AppEvent } from '../types';

interface EventTimelineProps {
  events: AppEvent[];
}

function eventIcon(type: string) {
  if (type.startsWith('evaluation')) return <RefreshCw size={13} />;
  if (type === 'decision_approved') return <CheckCircle2 size={13} />;
  if (type === 'message_received') return <MessageSquare size={13} />;
  if (type === 'scenario_created' || type === 'conditions_confirmed') return <FileText size={13} />;
  return <CircleDot size={13} />;
}

export default function EventTimeline({ events }: EventTimelineProps) {
  if (!events.length) return null;
  return (
    <section className="panel event-timeline">
      <div className="panel-heading compact">
        <div>
          <span className="eyebrow">事件时间线</span>
          <h2>场景记录</h2>
        </div>
      </div>
      <ol className="timeline-list">
        {events.map((event, index) => (
          <motion.li
            key={event.id}
            className="timeline-item"
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={index}
          >
            <span className="timeline-icon">{eventIcon(event.type)}</span>
            <div className="timeline-content">
              <div className="timeline-head">
                <strong>{event.content}</strong>
                <span>v{event.version}</span>
              </div>
              <time>{new Date(event.created_at).toLocaleString('zh-CN', { hour12: false })}</time>
            </div>
          </motion.li>
        ))}
      </ol>
    </section>
  );
}
