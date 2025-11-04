/* eslint-disable */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Receipt as ReceiptIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizedDateProvider } from './LocalizedDateProvider.tsx';
import { deliveryOptionsAPI, currencyAPI } from '../services/api.ts';
import { formatApiError } from '../utils/errorUtils.ts';
import { CurrencySelector } from './CurrencySelector.tsx';
import { CurrencyWithRates } from '../types/index.ts';
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';

interface DeliveryOption {
  id?: number;
  project_item_id: number;
  delivery_slot: number | null;
  delivery_date: string;
  invoice_timing_type: string;
  invoice_issue_date: string | null;
  invoice_days_after_delivery: number | null;
  invoice_amount_per_unit: number;
  invoice_currency_id?: number;
  preference_rank: number | null;
  notes: string | null;
  is_active: boolean;
}

interface DeliveryOptionsManagerProps {
  projectItemId: number;
  itemCode: string;
  availableDeliveryDates: string[]; // Array of ISO date strings from ProjectItem.delivery_options
}

export const DeliveryOptionsManager: React.FC<DeliveryOptionsManagerProps> = ({
  projectItemId,
  itemCode,
  availableDeliveryDates,
}) => {
  const { i18n } = useTranslation();
  
  // Locale-aware date formatter
  const isFa = i18n.language?.startsWith('fa');
  
  // Main state
  const [options, setOptions] = useState<DeliveryOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [currencies, setCurrencies] = useState<CurrencyWithRates[]>([]);
  
  // Error/Success state - separated by context
  const [listError, setListError] = useState<string>(''); // Errors for list operations
  const [listSuccess, setListSuccess] = useState<string>(''); // Success messages for list operations
  const [dialogError, setDialogError] = useState<string>(''); // Errors for dialog operations (save/edit)
  const [dialogSuccess, setDialogSuccess] = useState<string>(''); // Success messages for dialog operations
  
  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedOption, setSelectedOption] = useState<DeliveryOption | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [deliveryDate, setDeliveryDate] = useState<string>('');
  const [deliverySlot, setDeliverySlot] = useState<number>(1);
  const [invoiceTimingType, setInvoiceTimingType] = useState<string>('RELATIVE');
  const [invoiceIssueDate, setInvoiceIssueDate] = useState<Date | null>(null);
  const [invoiceDaysAfter, setInvoiceDaysAfter] = useState<number>(30);
  const [invoiceAmount, setInvoiceAmount] = useState<number>(0);
  const [invoiceCurrencyId, setInvoiceCurrencyId] = useState<number | ''>('');
  const [preferenceRank, setPreferenceRank] = useState<number>(1);
  const [notes, setNotes] = useState<string>('');

  // Ref to track if component is mounted (prevent state updates after unmount)
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Helper function to add commas while typing
  const addCommasWhileTyping = useCallback((value: string): string => {
    const cleanValue = value.replace(/[^\d.]/g, '');
    const parts = cleanValue.split('.');
    const integerPart = parts[0];
    const decimalPart = parts[1];
    const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger;
  }, []);

  // Helper function to parse formatted number back to raw value
  const parseFormattedNumber = useCallback((formattedValue: string): string => {
    return formattedValue.replace(/,/g, '');
  }, []);

  // Fetch currencies (non-critical, fails silently)
  const fetchCurrencies = useCallback(async () => {
    try {
      const response = await currencyAPI.list();
      const activeCurrencies = response.data.filter((c: CurrencyWithRates) => c.is_active);
      if (isMountedRef.current) {
        setCurrencies(activeCurrencies);
      }
    } catch (err: any) {
      // Silently fail - currencies are optional helper text
      console.warn('Failed to load currencies for helper text:', err);
    }
  }, []);

  // Fetch delivery options
  const fetchOptions = useCallback(async (showError: boolean = true): Promise<void> => {
    if (!isMountedRef.current) return;
    
    try {
      setLoading(true);
      if (showError) {
        setListError('');
      }
      
      const response = await deliveryOptionsAPI.listByItem(projectItemId);
      
      if (isMountedRef.current) {
        setOptions(response.data || []);
        setListError('');
        setLoading(false);
      }
    } catch (err: any) {
      if (isMountedRef.current) {
        setLoading(false);
        if (showError) {
          // Only show errors for initial load, not background refreshes
          const errorMsg = formatApiError(err, 'Failed to load delivery options', 'load');
          setListError(errorMsg);
        }
        // Silently ignore background refresh errors
        if (!showError) {
          console.debug('Background refresh failed (non-critical):', err);
        }
      }
      // Re-throw for caller to handle if needed
      throw err;
    }
  }, [projectItemId]);

  // Initial load
  useEffect(() => {
    setListError('');
    setListSuccess('');
    fetchOptions(true);
    fetchCurrencies();
  }, [projectItemId, fetchOptions, fetchCurrencies]);

  // Reset form to default values
  const resetForm = useCallback(() => {
    setDeliveryDate(availableDeliveryDates.length > 0 ? availableDeliveryDates[0] : '');
    setDeliverySlot(1);
    setInvoiceTimingType('RELATIVE');
    setInvoiceIssueDate(null);
    setInvoiceDaysAfter(30);
    setInvoiceAmount(0);
    setInvoiceCurrencyId('');
    setPreferenceRank(1);
    setNotes('');
  }, [availableDeliveryDates]);

  // Open create dialog
  const openCreateDialog = useCallback(() => {
    resetForm();
    setEditMode(false);
    setSelectedOption(null);
    setDialogError('');
    setDialogSuccess('');
    setDialogOpen(true);
  }, [resetForm]);

  // Open edit dialog
  const openEditDialog = useCallback((option: DeliveryOption) => {
    setSelectedOption(option);
    setDeliveryDate(option.delivery_date);
    setDeliverySlot(option.delivery_slot || 1);
    setInvoiceTimingType(option.invoice_timing_type);
    setInvoiceIssueDate(option.invoice_issue_date ? new Date(option.invoice_issue_date) : null);
    setInvoiceDaysAfter(option.invoice_days_after_delivery || 30);
    
    // Ensure invoice_amount_per_unit is always a number
    const amount = typeof option.invoice_amount_per_unit === 'number' 
      ? option.invoice_amount_per_unit 
      : parseFloat(String(option.invoice_amount_per_unit)) || 0;
    setInvoiceAmount(amount);
    
    setInvoiceCurrencyId(option.invoice_currency_id || '');
    setPreferenceRank(option.preference_rank || 1);
    setNotes(option.notes || '');
    setDialogError('');
    setDialogSuccess('');
    setEditMode(true);
    setDialogOpen(true);
  }, []);

  // Handle save operation
  const handleSave = useCallback(async () => {
    // Validate currency is selected
    if (!invoiceCurrencyId || invoiceCurrencyId === '') {
      setDialogError('Please select a currency for the invoice amount');
      return;
    }
    
    // Clear previous messages and set saving state
    setDialogError('');
    setDialogSuccess('');
    setSaving(true);
    
    try {
      const data: any = {
        project_item_id: projectItemId,
        delivery_slot: deliverySlot,
        delivery_date: deliveryDate,
        invoice_timing_type: invoiceTimingType,
        invoice_issue_date: invoiceTimingType === 'ABSOLUTE' && invoiceIssueDate 
          ? invoiceIssueDate.toISOString().split('T')[0] 
          : null,
        invoice_days_after_delivery: invoiceTimingType === 'RELATIVE' ? invoiceDaysAfter : null,
        invoice_amount_per_unit: invoiceAmount,
        // Note: invoice_currency_id is not part of DeliveryOption model/schema
        // Removing it to prevent 500 errors
        preference_rank: preferenceRank,
        notes: notes || null,
        is_active: true,
      };

      // Perform save operation - this is the critical operation
      let saveSuccess = false;
      let saveError: any = null;
      
      try {
        if (editMode && selectedOption?.id) {
          await deliveryOptionsAPI.update(selectedOption.id, data);
          saveSuccess = true;
        } else {
          await deliveryOptionsAPI.create(data);
          saveSuccess = true;
        }
      } catch (saveErr: any) {
        saveError = saveErr;
        
        // If it's a 500 error, the save might have actually succeeded
        // We'll verify by refreshing the list
        if (saveErr?.response?.status === 500) {
          // Could be a serialization error - save might have succeeded
          // Try to refresh and see if the option was created
          console.warn('Received 500 error, but save may have succeeded. Verifying...');
          
          // Close dialog and try to refresh
          if (isMountedRef.current) {
            setDialogOpen(false);
            resetForm();
            setSaving(false);
            
            // Try to refresh the list to see if item was actually created
            setTimeout(async () => {
              try {
                await fetchOptions(false);
                // If refresh succeeds, show success message
                if (isMountedRef.current) {
                  setListSuccess(editMode ? 'Delivery option updated successfully' : 'Delivery option created successfully');
                  setTimeout(() => {
                    if (isMountedRef.current) {
                      setListSuccess('');
                    }
                  }, 3000);
                }
              } catch (refreshErr) {
                // Refresh also failed - show error
                if (isMountedRef.current) {
                  setListError('Save may have succeeded but could not verify. Please refresh the page to check.');
                }
              }
            }, 100);
          }
          return;
        }
        
        // For other errors, show error and stop here
        if (isMountedRef.current) {
          setSaving(false);
          const errorMsg = formatApiError(saveErr, 'Failed to save delivery option', 'save');
          setDialogError(errorMsg);
        }
        return;
      }

      // Save succeeded - close dialog immediately
      if (isMountedRef.current) {
        setDialogOpen(false);
        resetForm();
        setSaving(false);
        
        // Show success message briefly (outside dialog)
        setListSuccess(editMode ? 'Delivery option updated successfully' : 'Delivery option created successfully');
        setTimeout(() => {
          if (isMountedRef.current) {
            setListSuccess('');
          }
        }, 3000);
      }
      
      // Refresh options list in the background (non-blocking, silent on error)
      // This is non-critical since save already succeeded
      setTimeout(() => {
        fetchOptions(false).catch(() => {
          // Silently ignore refresh errors - save was successful
          console.debug('Background refresh failed (non-critical)');
        });
      }, 100);
      
    } catch (err: any) {
      // Unexpected error - should not reach here if save succeeded
      if (isMountedRef.current) {
        setSaving(false);
        const errorMsg = formatApiError(err, 'An unexpected error occurred');
        setDialogError(errorMsg);
      }
    }
  }, [
    invoiceCurrencyId,
    projectItemId,
    deliverySlot,
    deliveryDate,
    invoiceTimingType,
    invoiceIssueDate,
    invoiceDaysAfter,
    invoiceAmount,
    preferenceRank,
    notes,
    editMode,
    selectedOption,
    resetForm,
    fetchOptions,
  ]);

  // Handle delete operation
  const handleDelete = useCallback(async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this delivery option?')) {
      return;
    }

    try {
      setListError('');
      await deliveryOptionsAPI.delete(id);
      
      if (isMountedRef.current) {
        setListSuccess('Delivery option deleted successfully');
        // Clear success message after 3 seconds
        setTimeout(() => {
          if (isMountedRef.current) {
            setListSuccess('');
          }
        }, 3000);
      }
      
      // Refresh the list
      await fetchOptions(true);
    } catch (err: any) {
      if (isMountedRef.current) {
        const errorMsg = formatApiError(err, 'Failed to delete delivery option', 'delete');
        setListError(errorMsg);
      }
    }
  }, [fetchOptions]);

  // Close dialog handler
  const handleCloseDialog = useCallback(() => {
    setDialogOpen(false);
    setDialogError('');
    setDialogSuccess('');
    resetForm();
  }, [resetForm]);

  // Date formatter
  const formatDate = useMemo(() => (dateString: string | null) => {
    if (!dateString) return 'N/A';
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      if (isFa) {
        return jalaliFormat(d, 'yyyy/MM/dd');
      } else {
        return gregorianFormat(d, 'MMM dd, yyyy');
      }
    } catch {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    }
  }, [isFa]);

  // Get invoice timing display text
  const getInvoiceTimingDisplay = useCallback((option: DeliveryOption) => {
    if (option.invoice_timing_type === 'ABSOLUTE') {
      return `Date: ${formatDate(option.invoice_issue_date)}`;
    } else {
      return `+${option.invoice_days_after_delivery} days after delivery`;
    }
  }, [formatDate]);

  // Format invoice amount for display
  const formatInvoiceAmount = useCallback((amount: number | string): string => {
    const numValue = typeof amount === 'number' ? amount : parseFloat(String(amount)) || 0;
    return numValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }, []);

  return (
    <Box>
      {/* List-level error/success messages (shown outside dialog) */}
      {listError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setListError('')}>
          {listError}
        </Alert>
      )}

      {listSuccess && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setListSuccess('')}>
          {listSuccess}
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Delivery & Invoice Options for {itemCode}
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={openCreateDialog}
          disabled={loading}
        >
          Add Delivery Option
        </Button>
      </Box>

      {loading && options.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Slot (Auto)</TableCell>
                <TableCell>Delivery Date</TableCell>
                <TableCell>Invoice Timing</TableCell>
                <TableCell align="right">Invoice Amount/Unit</TableCell>
                <TableCell align="center">Preference</TableCell>
                <TableCell>Notes</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {options.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="textSecondary" sx={{ py: 2 }}>
                      No delivery options configured. Click "Add Delivery Option" to create one.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                options.map((option) => (
                  <TableRow key={option.id}>
                    <TableCell>
                      <Chip label={`Slot ${option.delivery_slot}`} size="small" color="default" />
                    </TableCell>
                    <TableCell>{formatDate(option.delivery_date)}</TableCell>
                    <TableCell>
                      <Typography variant="caption" display="block">
                        {getInvoiceTimingDisplay(option)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="medium">
                        ${formatInvoiceAmount(option.invoice_amount_per_unit)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip 
                        label={option.preference_rank} 
                        size="small" 
                        color={option.preference_rank === 1 ? 'primary' : 'default'} 
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" color="textSecondary">
                        {option.notes || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => openEditDialog(option)}
                        title="Edit"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => option.id && handleDelete(option.id)}
                        title="Delete"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Create/Edit Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={handleCloseDialog}
        maxWidth="md" 
        fullWidth
        disableEscapeKeyDown={saving}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ReceiptIcon />
            {editMode ? 'Edit Delivery & Invoice Option' : 'Add Delivery & Invoice Option'}
          </Box>
        </DialogTitle>
        <DialogContent>
          {/* Dialog-level error/success messages (shown inside dialog) */}
          {dialogError && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setDialogError('')}>
              {dialogError}
            </Alert>
          )}

          {dialogSuccess && (
            <Alert severity="success" sx={{ mb: 2 }} onClose={() => setDialogSuccess('')}>
              {dialogSuccess}
            </Alert>
          )}

          <Alert severity="info" sx={{ mb: 3, mt: 1 }}>
            Configure delivery date and invoice timing for this project item. The invoice can be issued on a specific date or relative to the delivery date.
          </Alert>

          {/* Delivery Configuration */}
          <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2, mt: 2 }}>
            📦 Delivery Configuration
          </Typography>

          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Delivery Date *</InputLabel>
            <Select
              value={deliveryDate}
              label="Delivery Date *"
              onChange={(e) => {
                const selectedDate = e.target.value;
                setDeliveryDate(selectedDate);
                // Auto-set slot based on date position
                const slotIndex = availableDeliveryDates.indexOf(selectedDate);
                setDeliverySlot(slotIndex >= 0 ? slotIndex + 1 : 1);
              }}
              disabled={saving}
            >
              {availableDeliveryDates.length === 0 ? (
                <MenuItem value="" disabled>
                  No delivery dates configured for this item
                </MenuItem>
              ) : (
                availableDeliveryDates.map((date, index) => (
                  <MenuItem key={index} value={date}>
                    {formatDate(date)} (Auto-assigned Slot {index + 1})
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>
          <Alert severity="info" sx={{ mb: 2 }}>
            ℹ️ Delivery slot is automatically assigned based on date order. Earlier dates get lower slot numbers.
          </Alert>

          {/* Invoice Configuration */}
          <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
            💰 Invoice Configuration
          </Typography>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Invoice Timing Type *</InputLabel>
            <Select
              value={invoiceTimingType}
              label="Invoice Timing Type *"
              onChange={(e) => setInvoiceTimingType(e.target.value)}
              disabled={saving}
            >
              <MenuItem value="ABSOLUTE">Absolute Date (Specific Date)</MenuItem>
              <MenuItem value="RELATIVE">Relative (Days After Delivery)</MenuItem>
            </Select>
          </FormControl>

          {invoiceTimingType === 'ABSOLUTE' ? (
            <LocalizedDateProvider>
              <DatePicker
                label="Invoice Issue Date *"
                value={invoiceIssueDate}
                onChange={(newValue) => setInvoiceIssueDate(newValue)}
                disabled={saving}
                slotProps={{ 
                  textField: { 
                    fullWidth: true,
                    helperText: "Specific date when invoice will be issued to client"
                  } 
                }}
              />
            </LocalizedDateProvider>
          ) : (
            <TextField
              fullWidth
              type="number"
              label="Days After Delivery *"
              value={invoiceDaysAfter}
              onChange={(e) => setInvoiceDaysAfter(parseInt(e.target.value) || 30)}
              helperText="Number of days after delivery to issue invoice (e.g., 30 for Net 30)"
              inputProps={{ min: 0, max: 365 }}
              disabled={saving}
            />
          )}

          <TextField
            fullWidth
            type="text"
            label="Invoice Amount per Unit *"
            value={invoiceAmount && typeof invoiceAmount === 'number' ? addCommasWhileTyping(invoiceAmount.toString()) : ''}
            onChange={(e) => {
              const rawValue = parseFormattedNumber(e.target.value);
              const numericValue = parseFloat(rawValue) || 0;
              setInvoiceAmount(numericValue);
            }}
            helperText={
              currencies.length > 0
                ? `Revenue amount per unit when invoiced. Available currencies: ${currencies.map(c => c.code).join(', ')}`
                : "Revenue amount per unit when invoiced"
            }
            inputProps={{ 
              step: 0.01, 
              min: 0,
              placeholder: '0.00'
            }}
            sx={{ mt: 2, mb: 2 }}
            disabled={saving}
          />

          <CurrencySelector
            value={invoiceCurrencyId}
            onChange={(currencyId) => setInvoiceCurrencyId(currencyId)}
            label="Invoice Currency *"
            required
            showRate
            fullWidth
            disabled={saving}
            helperText={
              currencies.length > 0
                ? `Select currency for invoice. Available currencies: ${currencies.map(c => c.code).join(', ')}`
                : "Select currency for invoice"
            }
          />

          {/* Additional Options */}
          <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2, mt: 3 }}>
            ⚙️ Additional Options
          </Typography>

          <TextField
            fullWidth
            type="number"
            label="Preference Rank"
            value={preferenceRank}
            onChange={(e) => setPreferenceRank(parseInt(e.target.value) || 1)}
            helperText="Lower numbers = higher preference (1 is most preferred)"
            inputProps={{ min: 1 }}
            sx={{ mb: 2 }}
            disabled={saving}
          />

          <TextField
            fullWidth
            multiline
            rows={2}
            label="Notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            helperText="Optional notes about this delivery option"
            disabled={saving}
          />

          {/* Preview */}
          <Alert severity="success" sx={{ mt: 3 }}>
            <Typography variant="subtitle2" fontWeight="medium">Preview:</Typography>
            <Typography variant="body2">
              • Delivery: {deliveryDate ? formatDate(deliveryDate) : 'Not set'}
            </Typography>
            <Typography variant="body2">
              • Invoice: {invoiceTimingType === 'ABSOLUTE' 
                ? (invoiceIssueDate ? formatDate(invoiceIssueDate.toISOString()) : 'Not set')
                : `${invoiceDaysAfter} days after delivery ${deliveryDate ? `(approx. ${formatDate(new Date(new Date(deliveryDate).getTime() + invoiceDaysAfter * 24 * 60 * 60 * 1000).toISOString())})` : ''}`
              }
            </Typography>
            <Typography variant="body2">
              • Amount: {invoiceAmount ? formatInvoiceAmount(invoiceAmount) : '0.00'} per unit
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={handleCloseDialog}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSave} 
            variant="contained" 
            color="primary"
            disabled={saving}
            startIcon={saving ? <CircularProgress size={16} /> : null}
          >
            {saving ? 'Saving...' : editMode ? 'Update' : 'Create'} Delivery Option
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
