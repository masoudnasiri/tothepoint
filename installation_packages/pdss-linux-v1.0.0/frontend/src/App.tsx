import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext.tsx';
import { ProtectedRoute } from './components/ProtectedRoute.tsx';
import { Layout } from './components/Layout.tsx';
import { LoginPage } from './pages/LoginPage.tsx';
import { DashboardPage } from './pages/DashboardPage.tsx';
import { ProjectsPage } from './pages/ProjectsPage.tsx';
import { ItemsMasterPage } from './pages/ItemsMasterPage.tsx';
import { ProjectItemsPage } from './pages/ProjectItemsPage.tsx';
import { FinalizedDecisionsPage } from './pages/FinalizedDecisionsPage.tsx';
import { ProcurementPage } from './pages/ProcurementPage.tsx';
import { ProcurementPlanPage } from './pages/ProcurementPlanPage.tsx';
import { FinancePage } from './pages/FinancePage.tsx';
import { OptimizationPage } from './pages/OptimizationPage.tsx';
import { OptimizationPageEnhanced } from './pages/OptimizationPage_enhanced.tsx';
import { UsersPage } from './pages/UsersPage.tsx';
import { WeightsPage } from './pages/WeightsPage.tsx';
import { AnalyticsDashboardPage } from './pages/AnalyticsDashboardPage.tsx';
import { ReportsPage } from './pages/ReportsPage.tsx';

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/decisions" element={<FinalizedDecisionsPage />} />
                  <Route path="/projects" element={<ProjectsPage />} />
                  <Route path="/items-master" element={<ItemsMasterPage />} />
                  <Route path="/projects/:projectId/items" element={<ProjectItemsPage />} />
                  <Route path="/procurement" element={<ProcurementPage />} />
                  <Route path="/procurement-plan" element={<ProcurementPlanPage />} />
                  <Route path="/finance" element={<FinancePage />} />
                  <Route path="/optimization" element={<OptimizationPage />} />
                  <Route path="/optimization-enhanced" element={<OptimizationPageEnhanced />} />
                  <Route path="/analytics" element={<AnalyticsDashboardPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/users" element={<UsersPage />} />
                  <Route path="/weights" element={<WeightsPage />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
  );
}

export default App;
