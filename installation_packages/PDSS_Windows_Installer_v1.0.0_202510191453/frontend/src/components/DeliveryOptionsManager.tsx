/* eslint-disable */
import React, { useState, useEffect } from 'react';
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
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Receipt as ReceiptIcon,
} from '@mui/icons-material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { deliveryOptionsAPI } from '../services/api.ts';
import { formatApiError } from '../utils/errorUtils.ts';
import { CurrencySelector } from './CurrencySelector.tsx';

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
  const [options, setOptions] = useState<DeliveryOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedOption, setSelectedOption] = useState<DeliveryOption | null>(null);

  // Form state
  const [deliveryDate, setDeliveryDate] = useState<string>(''); // Changed to string for select
  const [deliverySlot, setDeliverySlot] = useState<number>(1);
  const [invoiceTimingType, setInvoiceTimingType] = useState<string>('RELATIVE');
  const [invoiceIssueDate, setInvoiceIssueDate] = useState<Date | null>(null);
  const [invoiceDaysAfter, setInvoiceDaysAfter] = useState<number>(30);
  const [invoiceAmount, setInvoiceAmount] = useState<number>(0);
  const [invoiceCurrencyId, setInvoiceCurrencyId] = useState<number | ''>('');
  const [preferenceRank, setPreferenceRank] = useState<number>(1);
  const [notes, setNotes] = useState<string>('');

  useEffect(() => {
    fetchOptions();
  }, [projectItemId]);

  const fetchOptions = async () => {
    try {
      const response = await deliveryOptionsAPI.listByItem(projectItemId);
      setOptions(response.data);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to load delivery options'));
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setDeliveryDate(availableDeliveryDates.length > 0 ? availableDeliveryDates[0] : '');
    setDeliverySlot(1);
    setInvoiceTimingType('RELATIVE');
    setInvoiceIssueDate(null);
    setInvoiceDaysAfter(30);
    setInvoiceAmount(0);
    setInvoiceCurrencyId('');
    setPreferenceRank(1);
    setNotes('');
  };

  const openCreateDialog = () => {
    resetForm();
    setEditMode(false);
    setSelectedOption(null);
    setDialogOpen(true);
  };

  const openEditDialog = (option: DeliveryOption) => {
    setSelectedOption(option);
    setDeliveryDate(option.delivery_date);
    setDeliverySlot(option.delivery_slot || 1);
    setInvoiceTimingType(option.invoice_timing_type);
    setInvoiceIssueDate(option.invoice_issue_date ? new Date(option.invoice_issue_date) : null);
    setInvoiceDaysAfter(option.invoice_days_after_delivery || 30);
    setInvoiceAmount(option.invoice_amount_per_unit);
    setInvoiceCurrencyId(option.invoice_currency_id || '');
    setPreferenceRank(option.preference_rank || 1);
    setNotes(option.notes || '');
    setEditMode(true);
    setDialogOpen(true);
  };

  const handleSave = async () => {
    // Validate currency is selected
    if (!invoiceCurrencyId || invoiceCurrencyId === '') {
      setError('Please select a currency for the invoice amount');
      return;
    }
    
    try {
      const data: any = {
        project_item_id: projectItemId,
        delivery_slot: deliverySlot,
        delivery_date: deliveryDate, // Already in ISO format (YYYY-MM-DD)
        invoice_timing_type: invoiceTimingType,
        invoice_issue_date: invoiceTimingType === 'ABSOLUTE' && invoiceIssueDate 
          ? invoiceIssueDate.toISOString().split('T')[0] 
          : null,
        invoice_days_after_delivery: invoiceTimingType === 'RELATIVE' ? invoiceDaysAfter : null,
        invoice_amount_per_unit: invoiceAmount,
        invoice_currency_id: invoiceCurrencyId,
        preference_rank: preferenceRank,
        notes: notes || null,
        is_active: true,
      };

      if (editMode && selectedOption) {
        await deliveryOptionsAPI.update(selectedOption.id!, data);
        setSuccess('Delivery option updated successfully');
      } else {
        await deliveryOptionsAPI.create(data);
        setSuccess('Delivery option created successfully');
      }

      setDialogOpen(false);
      resetForm();
      fetchOptions();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to save delivery option'));
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this delivery option?')) return;

    try {
      await deliveryOptionsAPI.delete(id);
      setSuccess('Delivery option deleted successfully');
      fetchOptions();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to delete delivery option'));
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getInvoiceTimingDisplay = (option: DeliveryOption) => {
    if (option.invoice_timing_type === 'ABSOLUTE') {
      return `Date: ${formatDate(option.invoice_issue_date)}`;
    } else {
      return `+${option.invoice_days_after_delivery} days after delivery`;
    }
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
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
        >
          Add Delivery Option
        </Button>
      </Box>

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
                      ${option.invoice_amount_per_unit.toLocaleString()}
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
                      onClick={() => handleDelete(option.id!)}
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

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ReceiptIcon />
            {editMode ? 'Edit Delivery & Invoice Option' : 'Add Delivery & Invoice Option'}
          </Box>
        </DialogTitle>
        <DialogContent>
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
                // ✅ Auto-set slot based on date position
                const slotIndex = availableDeliveryDates.indexOf(selectedDate);
                setDeliverySlot(slotIndex >= 0 ? slotIndex + 1 : 1);
              }}
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
            >
              <MenuItem value="ABSOLUTE">Absolute Date (Specific Date)</MenuItem>
              <MenuItem value="RELATIVE">Relative (Days After Delivery)</MenuItem>
            </Select>
          </FormControl>

          {invoiceTimingType === 'ABSOLUTE' ? (
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Invoice Issue Date *"
                value={invoiceIssueDate}
                onChange={(newValue) => setInvoiceIssueDate(newValue)}
                slotProps={{ 
                  textField: { 
                    fullWidth: true,
                    helperText: "Specific date when invoice will be issued to client"
                  } 
                }}
              />
            </LocalizationProvider>
          ) : (
            <TextField
              fullWidth
              type="number"
              label="Days After Delivery *"
              value={invoiceDaysAfter}
              onChange={(e) => setInvoiceDaysAfter(parseInt(e.target.value) || 30)}
              helperText="Number of days after delivery to issue invoice (e.g., 30 for Net 30)"
              inputProps={{ min: 0, max: 365 }}
            />
          )}

          <TextField
            fullWidth
            type="number"
            label="Invoice Amount per Unit *"
            value={invoiceAmount}
            onChange={(e) => setInvoiceAmount(parseFloat(e.target.value) || 0)}
            helperText="Revenue amount per unit when invoiced"
            inputProps={{ min: 0, step: 0.01 }}
            sx={{ mt: 2, mb: 2 }}
          />

          <CurrencySelector
            value={invoiceCurrencyId}
            onChange={(currencyId) => setInvoiceCurrencyId(currencyId)}
            label="Invoice Currency *"
            required
            showRate
            fullWidth
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
          />

          <TextField
            fullWidth
            multiline
            rows={2}
            label="Notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            helperText="Optional notes about this delivery option"
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
              • Amount: ${invoiceAmount.toLocaleString()} per unit
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" color="primary">
            {editMode ? 'Update' : 'Create'} Delivery Option
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
