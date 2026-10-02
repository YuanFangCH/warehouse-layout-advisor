import { HelpCircle } from 'lucide-react';
import { motion } from 'motion/react';

import { fadeUp } from '../design/motion';
import type { ClarificationQuestion } from '../types';

interface ClarificationCardProps {
  question: ClarificationQuestion;
  busy: boolean;
  onAnswer: (answer: string) => void;
  index?: number;
}

export default function ClarificationCard({ question, busy, onAnswer, index = 0 }: ClarificationCardProps) {
  return (
    <motion.div
      className="clarification-card"
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      custom={index}
    >
      <div className="clarification-head">
        <HelpCircle size={14} />
        <span>待确认问题</span>
      </div>
      <p>{question.question}</p>
      <div className="option-grid">
        {question.options.map((option) => (
          <button
            key={option}
            type="button"
            className="option-button"
            disabled={busy}
            onClick={() => onAnswer(option)}
          >
            {option}
          </button>
        ))}
      </div>
    </motion.div>
  );
}
