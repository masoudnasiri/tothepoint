import React, { useMemo } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { useTranslation } from 'react-i18next';
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
import SuppliersPage from './pages/SuppliersPage.tsx';
import { AnalyticsDashboardPage } from './pages/AnalyticsDashboardPage.tsx';
import { ReportsPage } from './pages/ReportsPage.tsx';
import AuditLogsPage from './pages/AuditLogsPage.tsx';
import LocalizedDateProvider from './components/LocalizedDateProvider.tsx';

// Create theme with dynamic font support based on language
const createAppTheme = (isPersian: boolean = false) => createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: isPersian 
      ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
      : '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 960,
      lg: 1280,
      xl: 1920,
    },
  },
  components: {
    // Apply font to all MUI components
    MuiTypography: {
      styleOverrides: {
        root: {
          fontFamily: isPersian 
            ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
            : '"Roboto", "Helvetica", "Arial", sans-serif',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          fontFamily: isPersian 
            ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
            : '"Roboto", "Helvetica", "Arial", sans-serif',
          '@media (max-width: 600px)': {
            padding: '6px 12px',
            fontSize: '0.875rem',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& input': {
            fontFamily: isPersian 
              ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
              : '"Roboto", "Helvetica", "Arial", sans-serif',
          },
          '& textarea': {
            fontFamily: isPersian 
              ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
              : '"Roboto", "Helvetica", "Arial", sans-serif',
          },
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          fontFamily: isPersian 
            ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
            : '"Roboto", "Helvetica", "Arial", sans-serif',
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          fontFamily: isPersian 
            ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
            : '"Roboto", "Helvetica", "Arial", sans-serif',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          fontFamily: isPersian 
            ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
            : '"Roboto", "Helvetica", "Arial", sans-serif',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        root: {
          '& .MuiDialogTitle-root': {
            fontFamily: isPersian 
              ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
              : '"Roboto", "Helvetica", "Arial", sans-serif',
          },
          '& .MuiDialogContent-root': {
            fontFamily: isPersian 
              ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
              : '"Roboto", "Helvetica", "Arial", sans-serif',
          },
          '& .MuiDialogActions-root': {
            fontFamily: isPersian 
              ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
              : '"Roboto", "Helvetica", "Arial", sans-serif',
          },
        },
      },
    },
    MuiFormControl: {
      styleOverrides: {
        root: {
          fontFamily: isPersian 
            ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
            : '"Roboto", "Helvetica", "Arial", sans-serif',
        },
      },
    },
    MuiFormControlLabel: {
      styleOverrides: {
        root: {
          fontFamily: isPersian 
            ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
            : '"Roboto", "Helvetica", "Arial", sans-serif',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          fontFamily: isPersian 
            ? '"Yekan Bakh FaNum", "Tahoma", "Arial", sans-serif'
            : '"Roboto", "Helvetica", "Arial", sans-serif',
          '@media (max-width: 600px)': {
            padding: '8px 4px',
            fontSize: '0.75rem',
          },
        },
      },
    },
  },
});

function AppContent() {
  const { i18n } = useTranslation();
  const isPersian = i18n.language?.startsWith('fa');
  
  const theme = useMemo(() => createAppTheme(isPersian), [isPersian]);

  return (
    <ThemeProvider theme={theme}>
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
                    <Route path="/users" element={<UsersPage />} />
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
    </ThemeProvider>
  );
}

function App() {
  return <AppContent />;
}

export default App;

