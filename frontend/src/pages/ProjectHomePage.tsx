import { useState } from 'react';
import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowRight, Boxes, CheckCircle2, Clock3, FolderPlus, Plus } from 'lucide-react';
import { motion } from 'motion/react';
import { Link } from 'react-router-dom';

import { createProject, createScenario, fetchProjects, fetchScenarios } from '../api/projectsApi';
import { ApiError } from '../api/httpClient';
import Modal from '../components/Modal';
import StatusBadge from '../components/StatusBadge';
import { fadeUp } from '../design/motion';
import { useUIStore } from '../stores/uiStore';
import type { Project, Scenario } from '../types';
import { errorMessage } from '../utils/errors';

interface ProjectForm {
  name: string;
  warehouseName: string;
}

interface ScenarioForm {
  projectId: string;
  title: string;
}

export default function ProjectHomePage() {
  const queryClient = useQueryClient();
  const setLastError = useUIStore((state) => state.setLastError);
  const [projectModalOpen, setProjectModalOpen] = useState(false);
  const [scenarioModalOpen, setScenarioModalOpen] = useState(false);
  const [projectForm, setProjectForm] = useState<ProjectForm>({ name: '', warehouseName: '' });
  const [scenarioForm, setScenarioForm] = useState<ScenarioForm>({ projectId: '', title: '新布局分析' });

  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: fetchProjects });
  const projects = projectsQuery.data ?? [];
  const scenarioQueries = useQueries({
    queries: projects.map((project) => ({
      queryKey: ['scenarios', project.id],
      queryFn: () => fetchScenarios(project.id),
    })),
  });
  const scenariosByProject = scenarioQueries.map((query) => query.data ?? []);
  const allScenarios: Array<Scenario & { project: Project }> = scenariosByProject.flatMap(
    (scenarios, index) => scenarios.map((scenario) => ({ ...scenario, project: projects[index] })),
  );

  const pendingItems = allScenarios.filter(
    (scenario) => scenario.status === 'collecting' || scenario.status === 'clarifying',
  );
  const recentDecisions = allScenarios
    .filter((scenario) => scenario.status === 'approved')
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    .slice(0, 5);

  const handleError = (error: unknown) => {
    const apiError = error instanceof ApiError ? error : null;
    setLastError(errorMessage(apiError?.code ?? 'UNKNOWN_ERROR'));
  };

  const projectMutation = useMutation({
    mutationFn: () =>
      createProject({
        name: projectForm.name,
        warehouse_name: projectForm.warehouseName,
      }),
    onSuccess: () => {
      setProjectModalOpen(false);
      setProjectForm({ name: '', warehouseName: '' });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: handleError,
  });

  const scenarioMutation = useMutation({
    mutationFn: () => createScenario(scenarioForm.projectId, scenarioForm.title),
    onSuccess: () => {
      setScenarioModalOpen(false);
      setScenarioForm({ projectId: '', title: '新布局分析' });
      queryClient.invalidateQueries({ queryKey: ['scenarios'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: handleError,
  });

  if (projectsQuery.isLoading) {
    return <div className="page-loading">正在加载项目…</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-head">
        <div>
          <span className="eyebrow">决策工作台</span>
          <h2>项目与场景总览</h2>
          <p>跟踪仓储布局分析的状态、待办和最近决策。</p>
        </div>
        <div className="dashboard-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => setProjectModalOpen(true)}
          >
            <FolderPlus size={14} />
            新建项目
          </button>
          <button
            className="primary-button"
            type="button"
            onClick={() => {
              if (projects.length) {
                setScenarioForm((form) => ({
                  ...form,
                  projectId: form.projectId || projects[0].id,
                }));
                setScenarioModalOpen(true);
              }
            }}
          >
            <Plus size={14} />
            新建场景
          </button>
        </div>
      </div>

      <div className="stat-grid">
        {[
          { label: '项目', value: projects.length, icon: <Boxes size={18} /> },
          { label: '待处理事项', value: pendingItems.length, icon: <Clock3 size={18} /> },
          { label: '最近决策', value: recentDecisions.length, icon: <CheckCircle2 size={18} /> },
        ].map((stat, index) => (
          <motion.div
            className="stat-card"
            key={stat.label}
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={index}
          >
            {stat.icon}
            <div>
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </div>
          </motion.div>
        ))}
      </div>

      <section className="project-list">
        {projects.map((project, index) => {
          const scenarios = scenariosByProject[index] ?? [];
          return (
            <motion.article
              className="project-card"
              key={project.id}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              custom={index}
            >
              <div className="project-card-head">
                <div>
                  <span className="eyebrow">项目</span>
                  <h3>{project.name}</h3>
                  <p>{project.warehouse_name} · {project.data_status}</p>
                </div>
                <Link
                  className="secondary-button"
                  to={`/projects/${project.id}`}
                  onClick={() => {
                    setScenarioForm((form) => ({ ...form, projectId: project.id }));
                    setScenarioModalOpen(true);
                  }}
                >
                  <Plus size={14} />
                  新建场景
                </Link>
              </div>
              <div className="scenario-board">
                {scenarios.length ? (
                  scenarios.map((scenario) => (
                    <Link
                      className="scenario-card"
                      key={scenario.id}
                      to={`/projects/${project.id}/scenarios/${scenario.id}`}
                    >
                      <div className="scenario-card-head">
                        <StatusBadge status={scenario.status} />
                        <span>v{scenario.version}</span>
                      </div>
                      <h4>{scenario.title}</h4>
                      <p>更新于 {new Date(scenario.updated_at).toLocaleDateString('zh-CN')}</p>
                      <ArrowRight size={14} />
                    </Link>
                  ))
                ) : (
                  <div className="empty-inline">还没有场景，点击“新建场景”开始分析。</div>
                )}
              </div>
            </motion.article>
          );
        })}
      </section>

      <div className="dashboard-grid">
        <section className="panel dashboard-panel">
          <div className="panel-heading compact">
            <div>
              <span className="eyebrow">待处理事项</span>
              <h2>需要澄清的场景</h2>
            </div>
          </div>
          <div className="compact-list">
            {pendingItems.length ? (
              pendingItems.map((scenario) => (
                <Link
                  className="compact-row"
                  key={scenario.id}
                  to={`/projects/${scenario.project.id}/scenarios/${scenario.id}`}
                >
                  <div>
                    <strong>{scenario.title}</strong>
                    <span>等待需求澄清</span>
                  </div>
                  <ArrowRight size={14} />
                </Link>
              ))
            ) : (
              <div className="empty-inline">当前没有待处理事项。</div>
            )}
          </div>
        </section>
        <section className="panel dashboard-panel">
          <div className="panel-heading compact">
            <div>
              <span className="eyebrow">最近决策</span>
              <h2>已确认方案</h2>
            </div>
          </div>
          <div className="compact-list">
            {recentDecisions.length ? (
              recentDecisions.map((scenario) => (
                <Link
                  className="compact-row"
                  key={scenario.id}
                  to={`/projects/${scenario.project.id}/scenarios/${scenario.id}`}
                >
                  <div>
                    <strong>{scenario.title}</strong>
                    <span>v{scenario.version} · 已记录正式决策</span>
                  </div>
                  <ArrowRight size={14} />
                </Link>
              ))
            ) : (
              <div className="empty-inline">还没有已确认的决策。</div>
            )}
          </div>
        </section>
      </div>

      <Modal
        open={projectModalOpen}
        eyebrow="项目"
        title="新建项目"
        onClose={() => setProjectModalOpen(false)}
        footer={
          <>
            <button className="secondary-button" type="button" onClick={() => setProjectModalOpen(false)}>
              取消
            </button>
            <button
              className="primary-button"
              type="submit"
              form="project-form"
              disabled={projectMutation.isPending || !projectForm.name.trim()}
            >
              创建
            </button>
          </>
        }
      >
        <form
          className="modal-form"
          id="project-form"
          onSubmit={(event) => {
            event.preventDefault();
            projectMutation.mutate();
          }}
        >
          <label className="form-field">
            <span className="form-label">项目名称</span>
            <input
              className="form-input"
              value={projectForm.name}
              onChange={(event) => setProjectForm({ ...projectForm, name: event.target.value })}
              placeholder="例如：示例仓库"
            />
          </label>
          <label className="form-field">
            <span className="form-label">仓库名称</span>
            <input
              className="form-input"
              value={projectForm.warehouseName}
              onChange={(event) => setProjectForm({ ...projectForm, warehouseName: event.target.value })}
              placeholder="可选，默认与项目名称一致"
            />
          </label>
        </form>
      </Modal>

      <Modal
        open={scenarioModalOpen}
        eyebrow="场景"
        title="新建场景"
        onClose={() => setScenarioModalOpen(false)}
        footer={
          <>
            <button className="secondary-button" type="button" onClick={() => setScenarioModalOpen(false)}>
              取消
            </button>
            <button
              className="primary-button"
              type="submit"
              form="scenario-form"
              disabled={scenarioMutation.isPending || !scenarioForm.projectId}
            >
              创建
            </button>
          </>
        }
      >
        <form
          className="modal-form"
          id="scenario-form"
          onSubmit={(event) => {
            event.preventDefault();
            scenarioMutation.mutate();
          }}
        >
          <label className="form-field">
            <span className="form-label">所属项目</span>
            <select
              className="form-select"
              value={scenarioForm.projectId}
              onChange={(event) => setScenarioForm({ ...scenarioForm, projectId: event.target.value })}
            >
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span className="form-label">场景标题</span>
            <input
              className="form-input"
              value={scenarioForm.title}
              onChange={(event) => setScenarioForm({ ...scenarioForm, title: event.target.value })}
              placeholder="例如：降低拣选距离"
            />
          </label>
        </form>
      </Modal>
    </div>
  );
}
