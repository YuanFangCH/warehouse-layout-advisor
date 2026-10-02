import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, GitCompareArrows } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { Link, useParams } from 'react-router-dom';

import { fetchEvents, fetchScenario, fetchVersions } from '../../api/scenariosApi';
import StatusBadge from '../../components/StatusBadge';
import { expand, fadeUp } from '../../design/motion';
import type { ScenarioVersion } from '../../types';

function diffSnapshots(previous: Record<string, unknown> | undefined, current: Record<string, unknown>) {
  const keys = Array.from(
    new Set([...Object.keys(previous ?? {}), ...Object.keys(current)]),
  ).filter((key) => key !== 'status');
  return keys.filter((key) => JSON.stringify(previous?.[key]) !== JSON.stringify(current[key]));
}

export default function VersionsPage() {
  const { projectId, scenarioId } = useParams();
  const [expandedVersionId, setExpandedVersionId] = useState<string | null>(null);
  const [hoveredVersionId, setHoveredVersionId] = useState<string | null>(null);
  const scenarioQuery = useQuery({
    queryKey: ['scenario', scenarioId],
    queryFn: () => fetchScenario(scenarioId!),
    enabled: Boolean(scenarioId),
  });
  const versionsQuery = useQuery({
    queryKey: ['versions', scenarioId],
    queryFn: () => fetchVersions(scenarioId!),
    enabled: Boolean(scenarioId),
  });
  const eventsQuery = useQuery({
    queryKey: ['events', scenarioId],
    queryFn: () => fetchEvents(scenarioId!),
    enabled: Boolean(scenarioId),
  });

  const versions = versionsQuery.data ?? [];

  return (
    <div className="versions-page">
      <div className="detail-toolbar">
        <Link
          className="secondary-button"
          to={`/projects/${projectId}/scenarios/${scenarioId}`}
        >
          <ArrowLeft size={14} />
          返回场景工作台
        </Link>
        <span className="saved-state">
          <GitCompareArrows size={14} />
          {scenarioQuery.data?.title ?? '版本对比'}
        </span>
      </div>

      <div className="versions-layout">
        <section className="panel version-panel">
          <div className="panel-heading compact">
            <div>
              <span className="eyebrow">版本时间线</span>
              <h2>场景版本</h2>
            </div>
            <span className="version-tag">共 {versions.length} 个版本</span>
          </div>
          <ol className="version-list">
            {[...versions].reverse().map((version, index) => {
              const previous =
                versions[Math.max(0, versions.length - index - 2)];
              const changed = diffSnapshots(previous?.snapshot, version.snapshot);
              const snapshotOpen =
                expandedVersionId === version.id || hoveredVersionId === version.id;
              return (
                <motion.li
                  className="version-item"
                  key={version.id}
                  variants={fadeUp}
                  initial="hidden"
                  animate="visible"
                  custom={index}
                  onMouseEnter={() => setHoveredVersionId(version.id)}
                  onMouseLeave={() => setHoveredVersionId(null)}
                  onClick={() =>
                    setExpandedVersionId((current) =>
                      current === version.id ? null : version.id,
                    )
                  }
                >
                  <div className="version-marker">
                    <span>v{version.version}</span>
                  </div>
                  <div className="version-body">
                    <div className="version-head">
                      <StatusBadge status={version.status} />
                      <time>{new Date(version.created_at).toLocaleString('zh-CN', { hour12: false })}</time>
                    </div>
                    <strong>{version.note}</strong>
                    {changed.length ? (
                      <div className="version-diff">
                        <span>本版变化</span>
                        <div className="diff-tags">
                          {changed.map((key) => (
                            <code key={key}>{key}</code>
                          ))}
                        </div>
                      </div>
                    ) : null}
                    <AnimatePresence initial={false}>
                      {snapshotOpen ? (
                        <motion.pre
                          className="version-snapshot"
                          variants={expand}
                          initial="hidden"
                          animate="visible"
                          exit="exit"
                        >
                          {JSON.stringify(version.snapshot, null, 2)}
                        </motion.pre>
                      ) : null}
                    </AnimatePresence>
                  </div>
                </motion.li>
              );
            })}
          </ol>
        </section>

        <section className="panel version-panel">
          <div className="panel-heading compact">
            <div>
              <span className="eyebrow">确认记录</span>
              <h2>用户操作</h2>
            </div>
          </div>
          <ol className="timeline-list">
            {(eventsQuery.data ?? []).map((event, index) => (
              <motion.li
                className="timeline-item"
                key={event.id}
                variants={fadeUp}
                initial="hidden"
                animate="visible"
                custom={index}
              >
                <span className="timeline-icon">
                  <GitCompareArrows size={13} />
                </span>
                <div className="timeline-content">
                  <div className="timeline-head">
                    <strong>{event.content}</strong>
                    <span>{event.actor}</span>
                  </div>
                  <time>v{event.version} · {new Date(event.created_at).toLocaleString('zh-CN', { hour12: false })}</time>
                </div>
              </motion.li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  );
}
