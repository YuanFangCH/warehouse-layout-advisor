import { useEffect, useState } from 'react';

import { API_BASE_URL } from '../api/httpClient';
import type { StreamEvent } from '../types';

export function useEvaluationStream(evaluationId: string | null | undefined) {
  const [progress, setProgress] = useState<number | null>(null);
  const [stage, setStage] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [status, setStatus] = useState<'running' | 'completed' | 'failed' | null>(null);

  useEffect(() => {
    if (!evaluationId) return undefined;
    const source = new EventSource(`${API_BASE_URL}/evaluations/${evaluationId}/stream`);

    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as StreamEvent;
        if (typeof data.progress === 'number') setProgress(data.progress);
        if (data.stage) setStage(data.stage);
        if (data.message) setMessage(data.message);
        if (data.type === 'evaluation.completed') {
          setStatus('completed');
          source.close();
        }
        if (data.type === 'evaluation.failed') {
          setStatus('failed');
          source.close();
        }
      } catch {
        // Ignore malformed SSE payloads.
      }
    };
    source.onerror = () => source.close();
    return () => source.close();
  }, [evaluationId]);

  return { progress, stage, message, status };
}
