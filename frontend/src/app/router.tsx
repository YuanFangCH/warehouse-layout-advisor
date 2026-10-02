import { createBrowserRouter, Navigate } from 'react-router-dom';

import AppLayout from '../components/AppLayout';
import VersionsPage from '../features/versions/VersionsPage';
import ProjectHomePage from '../pages/ProjectHomePage';
import ScenarioDetailPage from '../pages/ScenarioDetailPage';

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/projects" replace /> },
  {
    path: '/projects',
    element: <AppLayout />,
    children: [
      { index: true, element: <ProjectHomePage /> },
      { path: ':projectId/scenarios/:scenarioId', element: <ScenarioDetailPage /> },
      { path: ':projectId/scenarios/:scenarioId/versions', element: <VersionsPage /> },
    ],
  },
]);
