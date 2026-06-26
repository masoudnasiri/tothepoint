import React from 'react';
import { Box, Typography, Alert, CircularProgress } from '@mui/material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { canAccessUsersAccessControlSection } from '../utils/permissions.ts';
import { useTranslation } from 'react-i18next';

interface UsersAccessControlRouteProps {
  children: React.ReactNode;
}

export const UsersAccessControlRoute: React.FC<UsersAccessControlRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();
  const { t } = useTranslation();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!canAccessUsersAccessControlSection(user)) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {t('accessControl.accessDeniedTitle')}
        </Alert>
        <Typography color="text.secondary">{t('accessControl.sectionAccessDeniedMessage')}</Typography>
      </Box>
    );
  }

  return <>{children}</>;
};
