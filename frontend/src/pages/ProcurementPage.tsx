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
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { procurementAPI, excelAPI, deliveryOptionsAPI } from '../services/api.ts';
import { ProcurementOption, ProcurementOptionCreate } from '../types/index.ts';

interface DeliveryOption {
  id: number;
  delivery_date: string;
  delivery_slot: number | null;
  invoice_amount_per_unit: number;
}

export const ProcurementPage: React.FC = () => {
  const { user } = useAuth();
  const [itemCodes, setItemCodes] = useState<string[]>([]);
  const [procurementOptions, setProcurementOptions] = useState<ProcurementOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<ProcurementOption | null>(null);
  const [selectedItemCode, setSelectedItemCode] = useState<string>('');
  const [availableDeliveryOptions, setAvailableDeliveryOptions] = useState<DeliveryOption[]>([]);
  const [selectedDeliveryDate, setSelectedDeliveryDate] = useState<string>('');
  const [formData, setFormData] = useState<ProcurementOptionCreate>({
    item_code: '',
    supplier_name: '',
    base_cost: 0,
    lomc_lead_time: 0,
    discount_bundle_threshold: undefined,
    discount_bundle_percent: undefined,
    payment_terms: { type: 'cash', discount_percent: 0 },
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [itemCodesResponse, optionsResponse] = await Promise.all([
        procurementAPI.getItemCodes(),
        procurementAPI.listOptions(),
      ]);
      setItemCodes(itemCodesResponse.data);
      setProcurementOptions(optionsResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load procurement data');
    } finally {
      setLoading(false);
    }
  };

  const fetchOptionsByItemCode = async (itemCode: string) => {
    try {
      const response = await procurementAPI.listByItemCode(itemCode);
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load options');
      return [];
    }
  };

  const fetchDeliveryOptions = async (itemCode: string) => {
    try {
      const response = await deliveryOptionsAPI.getByItemCode(itemCode);
      setAvailableDeliveryOptions(response.data);
      setSelectedDeliveryDate(''); // Reset selection
    } catch (err: any) {
      setAvailableDeliveryOptions([]);
      // Don't show error for missing delivery options, just warn user in UI
    }
  };

  const handleItemCodeChange = async (itemCode: string) => {
    setFormData({ ...formData, item_code: itemCode });
    if (itemCode) {
      await fetchDeliveryOptions(itemCode);
    } else {
      setAvailableDeliveryOptions([]);
      setSelectedDeliveryDate('');
    }
  };

  const handleCreateOption = async () => {
    try {
      await procurementAPI.create(formData);
      setCreateDialogOpen(false);
      resetForm();
      fetchData();
    } catch (err: any) {
      // Handle validation errors (422) which return array of error objects
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          const errorMessages = detail.map((e: any) => 
            `${e.loc.join(' -> ')}: ${e.msg}`
          ).join('; ');
          setError(errorMessages);
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError('Failed to create procurement option');
        }
      } else {
        setError('Failed to create procurement option');
      }
    }
  };

  const handleEditOption = async () => {
    if (!selectedOption) return;
    
    try {
      await procurementAPI.update(selectedOption.id, formData);
      setEditDialogOpen(false);
      setSelectedOption(null);
      resetForm();
      fetchData();
    } catch (err: any) {
      // Handle validation errors
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          const errorMessages = detail.map((e: any) => 
            `${e.loc.join(' -> ')}: ${e.msg}`
          ).join('; ');
          setError(errorMessages);
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError('Failed to update procurement option');
        }
      } else {
        setError('Failed to update procurement option');
      }
    }
  };

  const handleDeleteOption = async (optionId: number) => {
    if (!window.confirm('Are you sure you want to delete this procurement option?')) return;
    
    try {
      await procurementAPI.delete(optionId);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete procurement option');
    }
  };

  const resetForm = () => {
    setFormData({
      item_code: selectedItemCode,
      supplier_name: '',
      base_cost: 0,
      lomc_lead_time: 0,
      discount_bundle_threshold: undefined,
      discount_bundle_percent: undefined,
      payment_terms: { type: 'cash', discount_percent: 0 },
    });
    setAvailableDeliveryOptions([]);
    setSelectedDeliveryDate('');
  };

  const handleExportOptions = async () => {
    try {
      const response = await excelAPI.exportProcurement();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'procurement_options.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to export options');
    }
  };

  const handleImportOptions = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await excelAPI.importProcurement(file);
      fetchData();
      alert('Procurement options imported successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import options');
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await excelAPI.downloadProcurementTemplate();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'procurement_options_template.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download template');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPaymentTerms = (terms: any) => {
    if (terms.type === 'cash') {
      return `Cash${terms.discount_percent ? ` (${terms.discount_percent}% discount)` : ''}`;
    } else {
      const schedule = terms.schedule.map((s: any) => `${s.percent}%`).join(', ');
      return `Installments (${schedule})`;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Procurement Options</Typography>
        {(user?.role === 'procurement' || user?.role === 'admin') && (
          <Box>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadTemplate}
              sx={{ mr: 1 }}
            >
              Download Template
            </Button>
            <Button
              variant="outlined"
              component="label"
              startIcon={<UploadIcon />}
              sx={{ mr: 1 }}
            >
              Import Options
              <input
                type="file"
                hidden
                accept=".xlsx,.xls"
                onChange={handleImportOptions}
              />
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExportOptions}
              sx={{ mr: 1 }}
            >
              Export Options
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Add Option
            </Button>
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {itemCodes.map((itemCode) => (
        <Accordion key={itemCode} sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">
              {itemCode} ({procurementOptions.filter(opt => opt.item_code === itemCode).length} options)
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Supplier</TableCell>
                    <TableCell align="right">Base Cost</TableCell>
                    <TableCell align="center">Lead Time</TableCell>
                    <TableCell align="center">Bundle Discount</TableCell>
                    <TableCell>Payment Terms</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {procurementOptions
                    .filter(opt => opt.item_code === itemCode)
                    .map((option) => (
                      <TableRow key={option.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {option.supplier_name}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatCurrency(option.base_cost)}
                        </TableCell>
                        <TableCell align="center">
                          <Chip label={`${option.lomc_lead_time} periods`} size="small" />
                        </TableCell>
                        <TableCell align="center">
                          {option.discount_bundle_threshold && option.discount_bundle_percent ? (
                            <Chip 
                              label={`${option.discount_bundle_percent}% @ ${option.discount_bundle_threshold}+`}
                              size="small"
                              color="success"
                            />
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatPaymentTerms(option.payment_terms)}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          {(user?.role === 'procurement' || user?.role === 'admin') && (
                            <>
                              <IconButton
                                size="small"
                                onClick={() => {
                                  setSelectedOption(option);
                                  setFormData({
                                    item_code: option.item_code,
                                    supplier_name: option.supplier_name,
                                    base_cost: option.base_cost,
                                    lomc_lead_time: option.lomc_lead_time,
                                    discount_bundle_threshold: option.discount_bundle_threshold,
                                    discount_bundle_percent: option.discount_bundle_percent,
                                    payment_terms: option.payment_terms,
                                  });
                                  setEditDialogOpen(true);
                                }}
                                title="Edit Option"
                              >
                                <EditIcon />
                              </IconButton>
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteOption(option.id)}
                                title="Delete Option"
                                color="error"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      ))}

      {/* Create Option Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Procurement Option</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Item Code</InputLabel>
            <Select
              value={formData.item_code}
              onChange={(e) => handleItemCodeChange(e.target.value)}
            >
              {itemCodes.map((code) => (
                <MenuItem key={code} value={code}>
                  {code}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            margin="dense"
            label="Supplier Name"
            fullWidth
            variant="outlined"
            value={formData.supplier_name}
            onChange={(e) => setFormData({ ...formData, supplier_name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Base Cost"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.base_cost}
            onChange={(e) => setFormData({ ...formData, base_cost: parseFloat(e.target.value) || 0 })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Delivery Date (from PM's Project Items)</InputLabel>
            <Select
              value={selectedDeliveryDate}
              onChange={(e) => {
                setSelectedDeliveryDate(e.target.value);
                const selected = availableDeliveryOptions.find(opt => opt.delivery_date === e.target.value);
                setFormData({ 
                  ...formData, 
                  lomc_lead_time: selected?.delivery_slot || 0 
                });
              }}
              disabled={!formData.item_code || availableDeliveryOptions.length === 0}
            >
              {availableDeliveryOptions.length === 0 && formData.item_code ? (
                <MenuItem value="" disabled>
                  No delivery dates set for this item
                </MenuItem>
              ) : (
                availableDeliveryOptions.map((opt) => (
                  <MenuItem key={opt.id} value={opt.delivery_date}>
                    {new Date(opt.delivery_date).toLocaleDateString()} {opt.delivery_slot ? `(Slot ${opt.delivery_slot})` : ''}
                  </MenuItem>
                ))
              )}
            </Select>
            {formData.item_code && availableDeliveryOptions.length === 0 && (
              <Alert severity="warning" sx={{ mt: 1 }}>
                No delivery dates found for this item. Please ask PM to set delivery options first.
              </Alert>
            )}
          </FormControl>
          <TextField
            margin="dense"
            label="Bundle Discount Threshold"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.discount_bundle_threshold || ''}
            onChange={(e) => setFormData({ 
              ...formData, 
              discount_bundle_threshold: e.target.value ? parseInt(e.target.value) : undefined 
            })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Bundle Discount Percentage"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.discount_bundle_percent || ''}
            onChange={(e) => setFormData({ 
              ...formData, 
              discount_bundle_percent: e.target.value ? parseFloat(e.target.value) : undefined 
            })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Payment Type</InputLabel>
            <Select
              value={formData.payment_terms.type}
              onChange={(e) => {
                const type = e.target.value as 'cash' | 'installments';
                setFormData({
                  ...formData,
                  payment_terms: type === 'cash' 
                    ? { type: 'cash', discount_percent: 0 }
                    : { type: 'installments', schedule: [{ due_offset: 0, percent: 100 }] }
                });
              }}
            >
              <MenuItem value="cash">Cash</MenuItem>
              <MenuItem value="installments">Installments</MenuItem>
            </Select>
          </FormControl>
          {formData.payment_terms.type === 'cash' && (
            <TextField
              margin="dense"
              label="Cash Discount Percentage"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.payment_terms.discount_percent || 0}
              onChange={(e) => setFormData({
                ...formData,
                payment_terms: {
                  ...formData.payment_terms,
                  discount_percent: parseFloat(e.target.value) || 0
                }
              })}
              sx={{ mb: 2 }}
            />
          )}
          {formData.payment_terms.type === 'installments' && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Installment Schedule (must total 100%)
              </Typography>
              {formData.payment_terms.schedule.map((installment, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                  <TextField
                    label="Days After Purchase"
                    type="number"
                    size="small"
                    value={installment.due_offset}
                    onChange={(e) => {
                      const newSchedule = [...formData.payment_terms.schedule];
                      newSchedule[index].due_offset = parseInt(e.target.value) || 0;
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule
                        }
                      });
                    }}
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    label="Percentage"
                    type="number"
                    size="small"
                    value={installment.percent}
                    onChange={(e) => {
                      const newSchedule = [...formData.payment_terms.schedule];
                      newSchedule[index].percent = parseFloat(e.target.value) || 0;
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule
                        }
                      });
                    }}
                    sx={{ flex: 1 }}
                    InputProps={{ endAdornment: '%' }}
                  />
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => {
                      const newSchedule = formData.payment_terms.schedule.filter((_, i) => i !== index);
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule.length > 0 ? newSchedule : [{ due_offset: 0, percent: 100 }]
                        }
                      });
                    }}
                    disabled={formData.payment_terms.schedule.length === 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              ))}
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => {
                  const newSchedule = [
                    ...formData.payment_terms.schedule,
                    { due_offset: 30, percent: 0 }
                  ];
                  setFormData({
                    ...formData,
                    payment_terms: {
                      ...formData.payment_terms,
                      schedule: newSchedule
                    }
                  });
                }}
                sx={{ mt: 1 }}
              >
                Add Installment
              </Button>
              <Typography variant="caption" color={
                formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0) === 100 
                  ? 'success.main' 
                  : 'error.main'
              } sx={{ display: 'block', mt: 1 }}>
                Total: {formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0)}%
                {formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0) !== 100 && ' (Must equal 100%)'}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateOption} variant="contained">
            Add Option
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Option Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Procurement Option</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Item Code</InputLabel>
            <Select
              value={formData.item_code}
              onChange={(e) => setFormData({ ...formData, item_code: e.target.value })}
            >
              {itemCodes.map((code) => (
                <MenuItem key={code} value={code}>
                  {code}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            margin="dense"
            label="Supplier Name"
            fullWidth
            variant="outlined"
            value={formData.supplier_name}
            onChange={(e) => setFormData({ ...formData, supplier_name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Base Cost"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.base_cost}
            onChange={(e) => setFormData({ ...formData, base_cost: parseFloat(e.target.value) || 0 })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Lead Time (periods)"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.lomc_lead_time}
            onChange={(e) => setFormData({ ...formData, lomc_lead_time: parseInt(e.target.value) || 0 })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Bundle Discount Threshold"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.discount_bundle_threshold || ''}
            onChange={(e) => setFormData({ 
              ...formData, 
              discount_bundle_threshold: e.target.value ? parseInt(e.target.value) : undefined 
            })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Bundle Discount Percentage"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.discount_bundle_percent || ''}
            onChange={(e) => setFormData({ 
              ...formData, 
              discount_bundle_percent: e.target.value ? parseFloat(e.target.value) : undefined 
            })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Payment Type</InputLabel>
            <Select
              value={formData.payment_terms.type}
              onChange={(e) => {
                const type = e.target.value as 'cash' | 'installments';
                setFormData({
                  ...formData,
                  payment_terms: type === 'cash' 
                    ? { type: 'cash', discount_percent: 0 }
                    : { type: 'installments', schedule: [{ due_offset: 0, percent: 100 }] }
                });
              }}
            >
              <MenuItem value="cash">Cash</MenuItem>
              <MenuItem value="installments">Installments</MenuItem>
            </Select>
          </FormControl>
          {formData.payment_terms.type === 'cash' && (
            <TextField
              margin="dense"
              label="Cash Discount Percentage"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.payment_terms.discount_percent || 0}
              onChange={(e) => setFormData({
                ...formData,
                payment_terms: {
                  ...formData.payment_terms,
                  discount_percent: parseFloat(e.target.value) || 0
                }
              })}
              sx={{ mb: 2 }}
            />
          )}
          {formData.payment_terms.type === 'installments' && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Installment Schedule (must total 100%)
              </Typography>
              {formData.payment_terms.schedule.map((installment, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                  <TextField
                    label="Days After Purchase"
                    type="number"
                    size="small"
                    value={installment.due_offset}
                    onChange={(e) => {
                      const newSchedule = [...formData.payment_terms.schedule];
                      newSchedule[index].due_offset = parseInt(e.target.value) || 0;
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule
                        }
                      });
                    }}
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    label="Percentage"
                    type="number"
                    size="small"
                    value={installment.percent}
                    onChange={(e) => {
                      const newSchedule = [...formData.payment_terms.schedule];
                      newSchedule[index].percent = parseFloat(e.target.value) || 0;
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule
                        }
                      });
                    }}
                    sx={{ flex: 1 }}
                    InputProps={{ endAdornment: '%' }}
                  />
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => {
                      const newSchedule = formData.payment_terms.schedule.filter((_, i) => i !== index);
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule.length > 0 ? newSchedule : [{ due_offset: 0, percent: 100 }]
                        }
                      });
                    }}
                    disabled={formData.payment_terms.schedule.length === 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              ))}
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => {
                  const newSchedule = [
                    ...formData.payment_terms.schedule,
                    { due_offset: 30, percent: 0 }
                  ];
                  setFormData({
                    ...formData,
                    payment_terms: {
                      ...formData.payment_terms,
                      schedule: newSchedule
                    }
                  });
                }}
                sx={{ mt: 1 }}
              >
                Add Installment
              </Button>
              <Typography variant="caption" color={
                formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0) === 100 
                  ? 'success.main' 
                  : 'error.main'
              } sx={{ display: 'block', mt: 1 }}>
                Total: {formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0)}%
                {formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0) !== 100 && ' (Must equal 100%)'}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleEditOption} variant="contained">
            Update Option
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
