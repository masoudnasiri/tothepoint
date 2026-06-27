import React from 'react';
import { Alert, Box, CircularProgress, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext.tsx';
import { canViewPaymentMethods } from '../utils/permissions.ts';

interface PaymentMethodsRouteProps {
  children: React.ReactNode;
}

export const PaymentMethodsRoute: React.FC<PaymentMethodsRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();
  const { t } = useTranslation();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!canViewPaymentMethods(user)) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {t('accessControl.featureAccessDenied')}
        </Alert>
        <Typography color="text.secondary">
          {t('accessControl.sectionAccessDeniedMessage')}
        </Typography>
      </Box>
    );
  }

  return <>{children}</>;
};
