import React, { useEffect, useMemo } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { AuthProvider } from './contexts/AuthContext.tsx';
import { FeatureFlagsProvider } from './hooks/useFeatureFlags.tsx';
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
import { WeightsPage } from './pages/WeightsPage.tsx';
import SuppliersPage from './pages/SuppliersPage.tsx';
import { AnalyticsDashboardPage } from './pages/AnalyticsDashboardPage.tsx';
import { ReportsPage } from './pages/ReportsPage.tsx';
import AuditLogsPage from './pages/AuditLogsPage.tsx';
import { UsersAccessControlPage } from './pages/UsersAccessControlPage.tsx';
import { UsersAccessControlRoute } from './components/UsersAccessControlRoute.tsx';
import LocalizedDateProvider from './components/LocalizedDateProvider.tsx';
import { PRODUCER_NAME, PRODUCT_NAME } from './utils/appIdentity.ts';
import { createRivarTheme } from './theme/rivarTheme.ts';
import './styles/rivarDesignSystem.css';

function AppContent() {
  const { i18n } = useTranslation();
  const isPersian = i18n.language?.startsWith('fa');

  // Pass RTL direction into the MUI theme so all components (TablePagination, etc.) flip correctly
  const theme = useMemo(() => createRivarTheme(isPersian, isPersian ? 'rtl' : 'ltr'), [isPersian]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <FeatureFlagsProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <LocalizedDateProvider>
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
                        <Route path="/users" element={<Navigate to="/users-access?tab=users" replace />} />
                        <Route
                          path="/users-access"
                          element={
                            <UsersAccessControlRoute>
                              <UsersAccessControlPage />
                            </UsersAccessControlRoute>
                          }
                        />
                        <Route path="/access-control" element={<Navigate to="/users-access?tab=roles" replace />} />
                        <Route path="/weights" element={<WeightsPage />} />
                        <Route path="/suppliers" element={<SuppliersPage />} />
                        <Route path="/audit-logs" element={<AuditLogsPage />} />
                      </Routes>
                    </Layout>
                  </LocalizedDateProvider>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </FeatureFlagsProvider>
    </ThemeProvider>
  );
}

function App() {
  useEffect(() => {
    document.title = `${PRODUCT_NAME} | ${PRODUCER_NAME}`;
  }, []);

  return <AppContent />;
}

export default App;
