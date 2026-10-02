import { useQuery } from '@tanstack/react-query';
import { ChevronDown, Database, History, Home, Layers, Menu, Plus, X } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { Link, NavLink, Outlet, useLocation, useParams } from 'react-router-dom';

import { fetchProjects } from '../api/projectsApi';
import { fetchScenario } from '../api/scenariosApi';
import { drawer, fade } from '../design/motion';
import { useUIStore } from '../stores/uiStore';
import { STAGES, stageForStatus } from '../types';
import ErrorBanner from './ErrorBanner';
import StatusBadge from './StatusBadge';

export default function AppLayout() {
  const { projectId, scenarioId } = useParams();
  const location = useLocation();
  const mobileNavOpen = useUIStore((state) => state.mobileNavOpen);
  const toggleMobileNav = useUIStore((state) => state.toggleMobileNav);

  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  });
  const scenarioQuery = useQuery({
    queryKey: ['scenario', scenarioId],
    queryFn: () => fetchScenario(scenarioId!),
    enabled: Boolean(scenarioId),
  });

  const projects = projectsQuery.data ?? [];
  const currentProject =
    projects.find((project) => project.id === projectId) ?? projects[0];
  const scenario = scenarioQuery.data;
  const isScenarioPage = Boolean(scenarioId);
  const activeStage = scenario ? stageForStatus(scenario.status) : null;

  const versionsPath =
    projectId && scenarioId
      ? `/projects/${projectId}/scenarios/${scenarioId}/versions`
      : '/projects';

  return (
    <div className="app-shell">
      <AnimatePresence>
        {mobileNavOpen ? (
          <motion.div
            className="sidebar-backdrop"
            variants={fade}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={toggleMobileNav}
            aria-hidden="true"
          />
        ) : null}
      </AnimatePresence>
      <motion.aside
        className={`sidebar ${mobileNavOpen ? 'open' : ''}`}
        variants={drawer}
        initial={false}
        animate={mobileNavOpen ? 'open' : 'closed'}
      >
        <div className="sidebar-head">
          <div className="brand-lockup">
            <div className="brand-mark">RS</div>
            <div>
              <div className="brand-name">仓储决策参谋</div>
              <div className="brand-subtitle">Layout Intelligence Desk</div>
            </div>
          </div>
          <button
            className="icon-button sidebar-close"
            type="button"
            onClick={toggleMobileNav}
            aria-label="关闭导航"
          >
            <X size={16} />
          </button>
        </div>

        <div className="workspace-switcher">
          <span className="eyebrow">当前项目</span>
          <button className="project-button" type="button" title={currentProject?.name ?? '选择项目'}>
            <span>{currentProject?.name ?? '尚未创建项目'}</span>
            <ChevronDown size={14} />
          </button>
        </div>

        <nav className="side-nav" aria-label="工作区导航">
          <NavLink
            to="/projects"
            end
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Home size={16} />
            决策工作台
          </NavLink>
          <Link to={versionsPath} className="nav-item">
            <Layers size={16} />
            场景版本
          </Link>
          <Link to="/projects" className="nav-item">
            <History size={16} />
            历史决策
          </Link>
        </nav>

        <div className="sidebar-spacer" />
        <div className="data-health">
          <div className="data-health-head">
            <span className="eyebrow">数据状态</span>
            <span className="status-dot" />
          </div>
          <strong>可开始分析</strong>
          <div className="health-row">
            <span>布局数据</span>
            <span>已加载</span>
          </div>
          <div className="health-row">
            <span>订单数据</span>
            <span>最近 30 天</span>
          </div>
          <div className="health-row">
            <span>资源参数</span>
            <span>已加载</span>
          </div>
        </div>
        <div className="profile-row">
          <div className="avatar">李</div>
          <div>
            <strong>李晨</strong>
            <span>运营规划</span>
          </div>
          <button className="icon-button" type="button" aria-label="更多选项">
            <Database size={15} />
          </button>
        </div>
      </motion.aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              决策工作台 <span>/</span> {currentProject?.name ?? '项目'} {isScenarioPage ? <span>/</span> : null}
              {isScenarioPage ? <span className="breadcrumb-current">{scenario?.title ?? '场景'}</span> : null}
            </div>
            <h1>{isScenarioPage ? scenario?.title ?? '场景详情' : '项目与场景总览'}</h1>
            {isScenarioPage && scenario ? (
              <div className="title-meta">
                <StatusBadge status={scenario.status} />
                <span>版本 v{scenario.version}</span>
              </div>
            ) : null}
          </div>
          <div className="topbar-actions">
            <button className="icon-button mobile-menu" type="button" onClick={toggleMobileNav} aria-label="打开导航">
              <Menu size={18} />
            </button>
            <span className="saved-state">
              <span className="status-dot" />
              服务端状态已同步
            </span>
            <Link className="secondary-button" to={isScenarioPage ? versionsPath : '/projects'}>
              <Plus size={14} />
              {isScenarioPage ? '版本时间线' : '新建分析'}
            </Link>
          </div>
        </header>

        {isScenarioPage && activeStage ? (
          <div className="stage-strip" aria-label="分析阶段">
            {STAGES.map((stage) => (
              <div className={`stage ${activeStage === stage.id ? 'active' : ''}`} key={stage.id}>
                <span>{String(STAGES.indexOf(stage) + 1).padStart(2, '0')}</span>
                <b>{stage.label}</b>
              </div>
            ))}
          </div>
        ) : null}

        <ErrorBanner />
        <Outlet context={{ projects }} />
      </main>
    </div>
  );
}
