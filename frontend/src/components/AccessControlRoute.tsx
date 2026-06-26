import React from 'react';
import { Box, Typography, Alert } from '@mui/material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { canManageAccessControl } from '../utils/permissions.ts';
import { useTranslation } from 'react-i18next';
import { CircularProgress } from '@mui/material';

interface AccessControlRouteProps {
  children: React.ReactNode;
}

export const AccessControlRoute: React.FC<AccessControlRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();
  const { t } = useTranslation();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!canManageAccessControl(user)) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {t('accessControl.accessDeniedTitle')}
        </Alert>
        <Typography color="text.secondary">{t('accessControl.accessDeniedMessage')}</Typography>
      </Box>
    );
  }

  return <>{children}</>;
};
