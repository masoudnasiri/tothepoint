import React from 'react';
import { Box, Typography, Alert, CircularProgress } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext.tsx';
import { canViewProjectItems } from '../utils/permissions.ts';

interface ProjectItemsRouteProps {
  children: React.ReactNode;
}

export const ProjectItemsRoute: React.FC<ProjectItemsRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();
  const { t } = useTranslation();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!canViewProjectItems(user)) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {t('projectItems.accessDeniedTitle')}
        </Alert>
        <Typography color="text.secondary">{t('projectItems.accessDeniedMessage')}</Typography>
      </Box>
    );
  }

  return <>{children}</>;
};
