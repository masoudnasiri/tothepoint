import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext.tsx';
import {
  canCreatePaymentMethods,
  canDeletePaymentMethods,
  canEditPaymentMethods,
  canViewPaymentMethods,
} from '../../utils/permissions.ts';
import { procurementFinancialsAPI } from '../../services/api.ts';
import type { PaymentMethod, PaymentMethodCreate } from '../../types/index.ts';
import { formatApiError } from '../../utils/errorUtils.ts';

interface PaymentMethodFormData {
  code: string;
  name_en: string;
  name_fa: string;
  description: string;
  settlement_delay_days: string;
}

interface PaymentMethodFormErrors {
  code?: string;
  name_en?: string;
  name_fa?: string;
  settlement_delay_days?: string;
}

const EMPTY_FORM: PaymentMethodFormData = {
  code: '',
  name_en: '',
  name_fa: '',
  description: '',
  settlement_delay_days: '0',
};

export const validatePaymentMethodForm = (
  data: PaymentMethodFormData,
  t: (key: string) => string
): PaymentMethodFormErrors => {
  const errors: PaymentMethodFormErrors = {};

  if (!data.code.trim()) {
    errors.code = t('procurement.paymentMethodCodeRequired') || 'Code is required';
  }
  if (!data.name_en.trim()) {
    errors.name_en = t('procurement.paymentMethodNameEnRequired') || 'English name is required';
  }
  if (!data.name_fa.trim()) {
    errors.name_fa = t('procurement.paymentMethodNameFaRequired') || 'Persian name is required';
  }

  const parsedDelay = Number(data.settlement_delay_days);
  if (!Number.isFinite(parsedDelay) || parsedDelay < 0) {
    errors.settlement_delay_days =
      t('procurement.settlementDelayNonNegative') ||
      'Settlement delay must be 0 or greater';
  }

  return errors;
};

const toPayload = (data: PaymentMethodFormData): PaymentMethodCreate => ({
  code: data.code.trim().toUpperCase(),
  name_en: data.name_en.trim(),
  name_fa: data.name_fa.trim(),
  description: data.description.trim() ? data.description.trim() : undefined,
  settlement_delay_days: Math.floor(Number(data.settlement_delay_days) || 0),
  is_active: true,
});

export const PaymentMethodsManager: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canView = canViewPaymentMethods(user);
  const canCreate = canCreatePaymentMethods(user);
  const canEdit = canEditPaymentMethods(user);
  const canDelete = canDeletePaymentMethods(user);
  const [methods, setMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingMethod, setEditingMethod] = useState<PaymentMethod | null>(null);
  const [formData, setFormData] = useState<PaymentMethodFormData>(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState<PaymentMethodFormErrors>({});
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const isEditMode = useMemo(() => Boolean(editingMethod), [editingMethod]);

  const loadMethods = async () => {
    setLoading(true);
    try {
      const response = await procurementFinancialsAPI.listPaymentMethods(true);
      setMethods(response.data || []);
    } catch (err: any) {
      setError(formatApiError(err, t('procurement.paymentMethodsLoadFailed')));
      setMethods([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canView) {
      loadMethods();
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canView]);

  if (!canView) {
    return (
      <Box data-testid="payment-methods-manager">
        <Alert severity="error">{t('accessControl.featureAccessDenied')}</Alert>
      </Box>
    );
  }

  const resetForm = () => {
    setFormData(EMPTY_FORM);
    setFormErrors({});
    setEditingMethod(null);
  };

  const openCreateDialog = () => {
    resetForm();
    setDialogOpen(true);
  };

  const openEditDialog = (method: PaymentMethod) => {
    setEditingMethod(method);
    setFormData({
      code: method.code || '',
      name_en: method.name_en || '',
      name_fa: method.name_fa || '',
      description: method.description || '',
      settlement_delay_days: String(method.settlement_delay_days ?? 0),
    });
    setFormErrors({});
    setDialogOpen(true);
  };

  const closeDialog = () => {
    if (saving) return;
    setDialogOpen(false);
    resetForm();
  };

  const handleSubmit = async () => {
    if ((isEditMode && !canEdit) || (!isEditMode && !canCreate)) {
      setError(t('accessControl.featureAccessDenied'));
      return;
    }

    const errors = validatePaymentMethodForm(formData, t);
    setFormErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setSaving(true);
    try {
      const payload = toPayload(formData);
      if (isEditMode && editingMethod) {
        await procurementFinancialsAPI.updatePaymentMethod(editingMethod.id, payload);
        setNotice(t('procurement.paymentMethodUpdated') || 'Payment method updated');
      } else {
        await procurementFinancialsAPI.createPaymentMethod(payload);
        setNotice(t('procurement.paymentMethodCreated') || 'Payment method created');
      }
      closeDialog();
      await loadMethods();
    } catch (err: any) {
      setError(formatApiError(err, t('procurement.failedToSavePaymentMethod') || 'Failed to save payment method'));
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (method: PaymentMethod) => {
    if (!canDelete) {
      setError(t('accessControl.featureAccessDenied'));
      return;
    }

    const confirmed = window.confirm(
      t('procurement.confirmDeactivatePaymentMethod') ||
        'Deactivate this payment method?'
    );
    if (!confirmed) return;

    try {
      await procurementFinancialsAPI.deactivatePaymentMethod(method.id);
      setNotice(t('procurement.paymentMethodDeactivated') || 'Payment method deactivated');
      await loadMethods();
    } catch (err: any) {
      setError(formatApiError(err, t('procurement.failedToDeactivatePaymentMethod') || 'Failed to deactivate payment method'));
    }
  };

  return (
    <Box data-testid="payment-methods-manager">
      {notice && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setNotice('')}>
          {notice}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">
          {t('procurement.paymentMethods') || 'Payment Methods'}
        </Typography>
        {canCreate && (
          <Button
            variant="contained"
            size="small"
            startIcon={<AddIcon />}
            onClick={openCreateDialog}
          >
            {t('procurement.addPaymentMethod') || 'Add Payment Method'}
          </Button>
        )}
      </Box>

      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress size={24} />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('procurement.code') || 'Code'}</TableCell>
                <TableCell>{t('procurement.nameEn') || 'Name (EN)'}</TableCell>
                <TableCell>{t('procurement.nameFa') || 'Name (FA)'}</TableCell>
                <TableCell>{t('procurement.settlementDelayDays') || 'Settlement Delay (Days)'}</TableCell>
                <TableCell>{t('procurement.description') || 'Description'}</TableCell>
                <TableCell align="right">{t('procurement.actions') || 'Actions'}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {methods.map((method) => (
                <TableRow key={method.id}>
                  <TableCell>{method.code}</TableCell>
                  <TableCell>{method.name_en}</TableCell>
                  <TableCell>{method.name_fa}</TableCell>
                  <TableCell>
                    {method.settlement_delay_days}{' '}
                    {t('procurement.days') || 'days'}
                  </TableCell>
                  <TableCell>{method.description || '-'}</TableCell>
                  <TableCell align="right">
                    {(canEdit || canDelete) && (
                      <>
                        {canEdit && (
                          <IconButton
                            size="small"
                            onClick={() => openEditDialog(method)}
                            title={t('procurement.editPaymentMethod') || 'Edit payment method'}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        )}
                        {canDelete && (
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeactivate(method)}
                            title={t('procurement.deactivatePaymentMethod') || 'Deactivate payment method'}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        )}
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {methods.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    {t('procurement.noPaymentMethods') || 'No active payment methods'}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialogOpen} onClose={closeDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {isEditMode
            ? (t('procurement.editPaymentMethod') || 'Edit Payment Method')
            : (t('procurement.createPaymentMethod') || 'Create Payment Method')}
        </DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label={t('procurement.code') || 'Code'}
            value={formData.code}
            onChange={(e) => setFormData((prev) => ({ ...prev, code: e.target.value }))}
            fullWidth
            required
            error={Boolean(formErrors.code)}
            helperText={formErrors.code}
          />
          <TextField
            margin="dense"
            label={t('procurement.nameEn') || 'Name (EN)'}
            value={formData.name_en}
            onChange={(e) => setFormData((prev) => ({ ...prev, name_en: e.target.value }))}
            fullWidth
            required
            error={Boolean(formErrors.name_en)}
            helperText={formErrors.name_en}
          />
          <TextField
            margin="dense"
            label={t('procurement.nameFa') || 'Name (FA)'}
            value={formData.name_fa}
            onChange={(e) => setFormData((prev) => ({ ...prev, name_fa: e.target.value }))}
            fullWidth
            required
            error={Boolean(formErrors.name_fa)}
            helperText={formErrors.name_fa}
          />
          <TextField
            margin="dense"
            label={t('procurement.settlementDelayDays') || 'Settlement Delay (Days)'}
            type="number"
            inputProps={{ min: 0 }}
            value={formData.settlement_delay_days}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                settlement_delay_days: e.target.value,
              }))
            }
            fullWidth
            required
            error={Boolean(formErrors.settlement_delay_days)}
            helperText={
              formErrors.settlement_delay_days ||
              (t('procurement.settlementDelayHelper') || 'Number of days until supplier receives funds')
            }
          />
          <TextField
            margin="dense"
            label={t('procurement.description') || 'Description'}
            value={formData.description}
            onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
            fullWidth
            multiline
            minRows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog} disabled={saving}>
            {t('common.cancel') || 'Cancel'}
          </Button>
          <Button onClick={handleSubmit} variant="contained" disabled={saving}>
            {saving
              ? (t('common.saving') || 'Saving...')
              : (isEditMode ? (t('common.update') || 'Update') : (t('common.create') || 'Create'))}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PaymentMethodsManager;
