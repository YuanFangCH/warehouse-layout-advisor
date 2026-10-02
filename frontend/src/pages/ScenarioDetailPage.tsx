import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { GitCompareArrows } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

import { ApiError } from '../api/httpClient';
import {
  answerClarification,
  fetchClarifications,
  fetchMessages,
  sendMessage,
} from '../api/conversationsApi';
import {
  fetchEvidence,
  fetchInsights,
  fetchRecommendation,
  startEvaluation,
} from '../api/evaluationsApi';
import { confirmScenario, fetchEvents, fetchScenario, updateScenario } from '../api/scenariosApi';
import { approveScenario, reviseScenario } from '../api/decisionsApi';
import ConditionEditModal from '../components/ConditionEditModal';
import ConditionSummary from '../components/ConditionSummary';
import ConversationPanel from '../components/ConversationPanel';
import EvaluationProgress from '../components/EvaluationProgress';
import EventTimeline from '../components/EventTimeline';
import EvidencePanel from '../components/EvidencePanel';
import RecommendationPanel from '../components/RecommendationPanel';
import { useEvaluationStream } from '../hooks/useEvaluationStream';
import { useUIStore } from '../stores/uiStore';
import type { Evaluation, MessageResponse } from '../types';
import { errorMessage } from '../utils/errors';

export default function ScenarioDetailPage() {
  const { projectId, scenarioId } = useParams();
  const queryClient = useQueryClient();
  const setLastError = useUIStore((state) => state.setLastError);
  const conditionModalOpen = useUIStore((state) => state.conditionModalOpen);
  const setConditionModalOpen = useUIStore((state) => state.setConditionModalOpen);
  const [activeEvaluation, setActiveEvaluation] = useState<Evaluation | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const scenarioQuery = useQuery({
    queryKey: ['scenario', scenarioId],
    queryFn: () => fetchScenario(scenarioId!),
    enabled: Boolean(scenarioId),
  });
  const messagesQuery = useQuery({
    queryKey: ['messages', scenarioId],
    queryFn: () => fetchMessages(scenarioId!),
    enabled: Boolean(scenarioId),
  });
  const clarificationsQuery = useQuery({
    queryKey: ['clarifications', scenarioId],
    queryFn: () => fetchClarifications(scenarioId!),
    enabled: Boolean(scenarioId),
  });
  const eventsQuery = useQuery({
    queryKey: ['events', scenarioId],
    queryFn: () => fetchEvents(scenarioId!),
    enabled: Boolean(scenarioId),
  });

  const scenario = scenarioQuery.data;
  const latestEvaluation = scenario?.latest_evaluation ?? activeEvaluation;
  const evaluationId = latestEvaluation?.id ?? null;
  const evaluationCompleted = latestEvaluation?.status === 'completed';
  const stream = useEvaluationStream(
    latestEvaluation && (latestEvaluation.status === 'queued' || latestEvaluation.status === 'running')
      ? latestEvaluation.id
      : null,
  );

  const evidenceQuery = useQuery({
    queryKey: ['evidence', evaluationId],
    queryFn: () => fetchEvidence(evaluationId!),
    enabled: Boolean(evaluationId && evaluationCompleted),
  });
  const insightsQuery = useQuery({
    queryKey: ['insights', evaluationId],
    queryFn: () => fetchInsights(evaluationId!),
    enabled: Boolean(evaluationId && evaluationCompleted),
  });
  const recommendationQuery = useQuery({
    queryKey: ['recommendation', evaluationId],
    queryFn: () => fetchRecommendation(evaluationId!),
    enabled: Boolean(evaluationId && evaluationCompleted),
  });

  const invalidateScenario = () => {
    queryClient.invalidateQueries({ queryKey: ['scenario', scenarioId] });
    queryClient.invalidateQueries({ queryKey: ['messages', scenarioId] });
    queryClient.invalidateQueries({ queryKey: ['clarifications', scenarioId] });
    queryClient.invalidateQueries({ queryKey: ['events', scenarioId] });
  };

  const handleError = (error: unknown) => {
    const apiError = error instanceof ApiError ? error : null;
    setLastError(errorMessage(apiError?.code ?? 'UNKNOWN_ERROR'));
    if (apiError?.code === 'SCENARIO_VERSION_CONFLICT') {
      invalidateScenario();
    }
  };

  useEffect(() => {
    if (stream.status === 'completed') {
      queryClient.invalidateQueries({ queryKey: ['scenario', scenarioId] });
      queryClient.invalidateQueries({ queryKey: ['evaluation', evaluationId] });
      queryClient.invalidateQueries({ queryKey: ['evidence', evaluationId] });
      queryClient.invalidateQueries({ queryKey: ['insights', evaluationId] });
      queryClient.invalidateQueries({ queryKey: ['recommendation', evaluationId] });
      queryClient.invalidateQueries({ queryKey: ['events', scenarioId] });
      setActiveEvaluation((current) =>
        current ? { ...current, status: 'completed', progress: 100 } : current,
      );
    }
  }, [stream.status, queryClient, scenarioId, evaluationId]);

  const sendMutation = useMutation({
    mutationFn: (message: string) =>
      sendMessage(scenarioId!, { message, client_version: scenario!.version }),
    onSuccess: (body: MessageResponse) => {
      setSyncMessage(body.sync_message ?? null);
      invalidateScenario();
    },
    onError: handleError,
  });
  const answerMutation = useMutation({
    mutationFn: ({ questionId, answer }: { questionId: string; answer: string }) =>
      answerClarification(scenarioId!, questionId, {
        answer,
        client_version: scenario!.version,
      }),
    onSuccess: (body: MessageResponse) => {
      setSyncMessage(body.sync_message ?? null);
      invalidateScenario();
    },
    onError: handleError,
  });
  const confirmMutation = useMutation({
    mutationFn: () =>
      confirmScenario(scenarioId!, {
        client_version: scenario!.version,
        confirmed_fields: [
          'business_objectives',
          'modification_scope',
          'budget_policy',
          'performance_floor',
        ],
      }),
    onSuccess: invalidateScenario,
    onError: handleError,
  });
  const updateMutation = useMutation({
    mutationFn: (patch: Record<string, unknown>) =>
      updateScenario(scenarioId!, { client_version: scenario!.version, ...patch }),
    onSuccess: () => {
      setConditionModalOpen(false);
      invalidateScenario();
    },
    onError: handleError,
  });
  const evaluationMutation = useMutation({
    mutationFn: () => startEvaluation(scenarioId!, scenario!.version),
    onSuccess: (evaluation) => {
      setActiveEvaluation(evaluation);
      invalidateScenario();
    },
    onError: handleError,
  });
  const approveMutation = useMutation({
    mutationFn: ({ option, note }: { option: string; note: string }) =>
      approveScenario(scenarioId!, {
        client_version: scenario!.version,
        selected_option: option,
        approval_note: note,
      }),
    onSuccess: invalidateScenario,
    onError: handleError,
  });
  const reviseMutation = useMutation({
    mutationFn: () =>
      reviseScenario(scenarioId!, { client_version: scenario!.version, note: '调整条件重算' }),
    onSuccess: invalidateScenario,
    onError: handleError,
  });

  if (!scenario) {
    return <div className="page-loading">正在加载场景…</div>;
  }

  const busy =
    sendMutation.isPending ||
    answerMutation.isPending ||
    confirmMutation.isPending ||
    updateMutation.isPending ||
    evaluationMutation.isPending ||
    approveMutation.isPending ||
    reviseMutation.isPending;
  const canConfirm =
    (scenario.status === 'collecting' || scenario.status === 'clarifying') &&
    (clarificationsQuery.data ?? []).length === 0;

  return (
    <div className="detail-layout">
      <div className="detail-toolbar">
        <Link
          className="secondary-button"
          to={`/projects/${projectId}/scenarios/${scenarioId}/versions`}
        >
          <GitCompareArrows size={14} />
          查看版本对比
        </Link>
      </div>
      <div className="workspace-grid">
        <div className="middle-column">
          <ConversationPanel
            messages={messagesQuery.data ?? []}
            pendingQuestions={clarificationsQuery.data ?? []}
            busy={busy}
            evaluationDone={evaluationCompleted}
            syncMessage={syncMessage}
            onDismissSync={() => setSyncMessage(null)}
            onSend={(message) => sendMutation.mutate(message)}
            onAnswer={(questionId, answer) => answerMutation.mutate({ questionId, answer })}
          />
          {latestEvaluation ? (
            <EvaluationProgress
              evaluation={latestEvaluation}
              streamProgress={stream.progress}
              streamStage={stream.stage}
              streamMessage={stream.message}
              streamStatus={stream.status}
            />
          ) : null}
          <EventTimeline events={eventsQuery.data ?? []} />
        </div>
        <aside className="decision-panel">
          <ConditionSummary
            scenario={scenario}
            canConfirm={canConfirm}
            busy={busy}
            onEdit={() => setConditionModalOpen(true)}
            onConfirm={() => confirmMutation.mutate()}
            onEvaluate={() => evaluationMutation.mutate()}
          />
          <EvidencePanel
            schemes={latestEvaluation?.schemes ?? []}
            evidence={evidenceQuery.data ?? []}
            insights={insightsQuery.data ?? []}
            recommendedOption={recommendationQuery.data?.recommended_option}
          />
          <RecommendationPanel
            recommendation={recommendationQuery.data}
            scenario={scenario}
            schemes={latestEvaluation?.schemes ?? []}
            busy={busy}
            onApprove={(option, note) => approveMutation.mutate({ option, note })}
            onRevise={() => reviseMutation.mutate()}
          />
        </aside>
      </div>
      <ConditionEditModal
        open={conditionModalOpen}
        scenario={scenario}
        busy={updateMutation.isPending}
        onClose={() => setConditionModalOpen(false)}
        onSave={(patch) => updateMutation.mutate(patch)}
      />
    </div>
  );
}
