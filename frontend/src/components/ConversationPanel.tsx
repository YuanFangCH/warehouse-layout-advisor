import { useState } from 'react';
import { CheckCircle2, Loader2, Send, X } from 'lucide-react';
import { motion } from 'motion/react';

import { fadeUp } from '../design/motion';
import type { ClarificationQuestion, Message } from '../types';
import ClarificationCard from './ClarificationCard';

const QUICK_PROMPTS = [
  '预算控制在 20 万元',
  '尽量少改，优先降低拣选距离',
  '吞吐量不能下降',
  '风险偏好偏保守',
];

const EXPLAIN_PROMPTS = [
  '为什么推荐这个方案？',
  '这个方案的风险是什么？',
  '硬约束和软约束有什么区别？',
  '方案之间差在哪？',
];

interface ConversationPanelProps {
  messages: Message[];
  pendingQuestions: ClarificationQuestion[];
  busy: boolean;
  evaluationDone?: boolean;
  syncMessage?: string | null;
  onDismissSync?: () => void;
  onSend: (message: string) => void;
  onAnswer: (questionId: string, answer: string) => void;
}

export default function ConversationPanel({
  messages,
  pendingQuestions,
  busy,
  evaluationDone = false,
  syncMessage,
  onDismissSync,
  onSend,
  onAnswer,
}: ConversationPanelProps) {
  const [draft, setDraft] = useState('');
  const quickPrompts = evaluationDone ? EXPLAIN_PROMPTS : QUICK_PROMPTS;

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!draft.trim() || busy) return;
    onSend(draft.trim());
    setDraft('');
  };

  return (
    <motion.section
      className="conversation-panel panel"
      variants={fadeUp}
      initial="hidden"
      animate="visible"
    >
      <div className="panel-heading">
        <div>
          <span className="eyebrow">交互记录</span>
          <h2>和决策参谋讨论</h2>
        </div>
        <span className="live-pill">
          <span className="status-dot" />
          {busy ? '回复中' : '在线'}
        </span>
      </div>
      <div className="conversation" aria-live="polite">
        {messages.map((message, index) => (
          <motion.article
            className={`message ${message.role}`}
            key={message.id}
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={index}
          >
            <div className="message-avatar">{message.role === 'assistant' ? 'RS' : '李'}</div>
            <div className="message-content">
              <div className="message-meta">
                <span>{message.role === 'assistant' ? '决策参谋 · ' : '你 · '}
                  {new Date(message.created_at).toLocaleTimeString('zh-CN', { hour12: false })}
                </span>
              </div>
              <div className="message-bubble">{message.content}</div>
            </div>
          </motion.article>
        ))}
        {pendingQuestions.map((question, index) => (
          <ClarificationCard
            key={question.id}
            question={question}
            busy={busy}
            onAnswer={(answer) => onAnswer(question.id, answer)}
            index={messages.length + index}
          />
        ))}
      </div>
      <div className="composer-shell">
        {syncMessage ? (
          <div className="sync-notice" role="status">
            <CheckCircle2 size={14} />
            <span>{syncMessage}</span>
            <button type="button" onClick={onDismissSync} aria-label="关闭同步提示">
              <X size={13} />
            </button>
          </div>
        ) : null}
        <form className="composer" onSubmit={submit}>
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            type="text"
            autoComplete="off"
            disabled={busy}
            placeholder={busy ? 'Agent 正在回复…' : '补充你的业务要求…'}
          />
          <button className="send-button" type="submit" disabled={busy} aria-label="发送" title="发送">
            {busy ? <Loader2 size={15} className="spin" /> : <Send size={15} />}
          </button>
        </form>
        <div className="quick-prompts" aria-label="快捷提问">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="quick-prompt"
              disabled={busy}
              onClick={() => onSend(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
        <div className="composer-note">Agent 会记录每次确认，模型参数仅以业务假设呈现。</div>
      </div>
    </motion.section>
  );
}
