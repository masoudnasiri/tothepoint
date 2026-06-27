import React from 'react';
import { Alert, Box } from '@mui/material';
import { useTranslation } from 'react-i18next';
import PaymentMethodsManager from '../components/finance/PaymentMethodsManager.tsx';
import { RivarPageHeader } from '../components/ui/RivarPageHeader.tsx';

export const PaymentMethodsPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <Box data-testid="payment-methods-page">
      <RivarPageHeader title={t('procurement.paymentMethods') || 'Payment Methods'} />
      <Alert severity="info" sx={{ mb: 2 }}>
        {t('procurement.definePaymentMethodsInMasterDataFirst') ||
          'Define payment methods in Master Data first.'}
      </Alert>
      <PaymentMethodsManager />
    </Box>
  );
};
