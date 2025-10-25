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
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Grid,
  Divider,
  InputAdornment,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  CheckCircle as ConfirmIcon,
  ThumbUp as AcceptIcon,
  Receipt as InvoiceIcon,
  FileDownload as ExportIcon,
  LocalShipping as ShippingIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { procurementPlanAPI, projectsAPI } from '../services/api.ts';
import {
  ProcurementPlanItem,
  DeliveryStatus,
  ProcurementDeliveryConfirmation,
  PMDeliveryAcceptance,
  ActualInvoiceData,
} from '../types/index.ts';
import { useTranslation } from 'react-i18next';

const formatCurrencyWithCode = (amount: number | undefined, currency: string | undefined): string => {
  if (amount === undefined || amount === null) return 'N/A';
  
  const currencySymbol = {
    'IRR': 'IRR',
    'USD': '$',
    'EUR': '€',
  }[currency || 'IRR'] || currency || 'IRR';
  
  const formattedAmount = amount.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  
  return `${currencySymbol} ${formattedAmount}`;
};

export const ProcurementPlanPage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [items, setItems] = useState<ProcurementPlanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [projectFilter, setProjectFilter] = useState<number | ''>('');
  const [projects, setProjects] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  
  // Dialogs
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [acceptDialogOpen, setAcceptDialogOpen] = useState(false);
  const [invoiceDialogOpen, setInvoiceDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ProcurementPlanItem | null>(null);
  
  // Form data
  const [confirmData, setConfirmData] = useState<ProcurementDeliveryConfirmation>({
    actual_delivery_date: new Date().toISOString().split('T')[0],
    is_correct_item: true,
    serial_number: '',
    delivery_notes: '',
  });
  
  const [acceptData, setAcceptData] = useState<PMDeliveryAcceptance>({
    is_accepted_for_project: true,
    customer_delivery_date: '',
    acceptance_notes: '',
  });
  
  const [invoiceData, setInvoiceData] = useState<ActualInvoiceData>({
    actual_invoice_issue_date: new Date().toISOString().split('T')[0],
    actual_invoice_amount: 0,
    actual_invoice_received_date: '',
    notes: '',
  });

  useEffect(() => {
    fetchItems();
    fetchProjects();
  }, [statusFilter, projectFilter]);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (statusFilter) params.status_filter = statusFilter;
      if (projectFilter) params.project_id = projectFilter;
      
      const response = await procurementPlanAPI.list(params);
      setItems(response.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load procurement plan');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.list();
      setProjects(response.data);
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
  };

  const handleViewItem = async (item: ProcurementPlanItem) => {
    try {
      const response = await procurementPlanAPI.get(item.id);
      setSelectedItem(response.data);
      setViewDialogOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load item details');
    }
  };

  const handleConfirmDelivery = async () => {
    if (!selectedItem) return;
    
    try {
      await procurementPlanAPI.confirmDelivery(selectedItem.id, confirmData);
      setSuccess('Delivery confirmed successfully!');
      setConfirmDialogOpen(false);
      fetchItems();
      // Reset form
      setConfirmData({
        actual_delivery_date: new Date().toISOString().split('T')[0],
        is_correct_item: true,
        serial_number: '',
        delivery_notes: '',
      });
    } catch (err: any) {
      // Handle validation errors
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          const errorMessages = err.response.data.detail.map((e: any) => e.msg).join(', ');
          setError(errorMessages);
        } else if (typeof err.response.data.detail === 'string') {
          setError(err.response.data.detail);
        } else {
          setError('Failed to confirm delivery. Please check all required fields.');
        }
      } else {
        setError('Failed to confirm delivery');
      }
    }
  };

  const handleAcceptDelivery = async () => {
    if (!selectedItem) return;
    
    try {
      await procurementPlanAPI.acceptDelivery(selectedItem.id, acceptData);
      setSuccess('Delivery accepted successfully!');
      setAcceptDialogOpen(false);
      fetchItems();
      // Reset form
      setAcceptData({
        is_accepted_for_project: true,
        customer_delivery_date: '',
        acceptance_notes: '',
      });
    } catch (err: any) {
      // Handle validation errors
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Pydantic validation error format
          const errorMessages = err.response.data.detail.map((e: any) => e.msg).join(', ');
          setError(errorMessages);
        } else if (typeof err.response.data.detail === 'string') {
          setError(err.response.data.detail);
        } else {
          setError('Failed to accept delivery. Please check all required fields.');
        }
      } else {
        setError('Failed to accept delivery');
      }
    }
  };

  const handleEnterInvoice = async () => {
    if (!selectedItem) return;
    
    // Validation
    if (!invoiceData.actual_invoice_amount || invoiceData.actual_invoice_amount <= 0) {
      setError('Invoice amount must be greater than 0');
      return;
    }
    
    try {
      await procurementPlanAPI.enterInvoice(selectedItem.id, invoiceData);
      setSuccess('Invoice data entered successfully!');
      setInvoiceDialogOpen(false);
      fetchItems();
      // Reset form
      setInvoiceData({
        actual_invoice_issue_date: new Date().toISOString().split('T')[0],
        actual_invoice_amount: 0,
        actual_invoice_received_date: '',
        notes: '',
      });
    } catch (err: any) {
      // Handle validation errors
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          const errorMessages = err.response.data.detail.map((e: any) => e.msg).join(', ');
          setError(errorMessages);
        } else if (typeof err.response.data.detail === 'string') {
          setError(err.response.data.detail);
        } else {
          setError('Failed to enter invoice data. Please check all required fields.');
        }
      } else {
        setError('Failed to enter invoice data');
      }
    }
  };

  const handleExport = async () => {
    try {
      const response = await procurementPlanAPI.export();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `procurement_plan_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSuccess('Export completed successfully!');
    } catch (err: any) {
      setError('Failed to export procurement plan');
    }
  };

  const getStatusColor = (status: DeliveryStatus): 'default' | 'warning' | 'success' => {
    switch (status) {
      case 'AWAITING_DELIVERY':
        return 'default';
      case 'CONFIRMED_BY_PROCUREMENT':
        return 'warning';
      case 'DELIVERY_COMPLETE':
        return 'success';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: DeliveryStatus): string => {
    switch (status) {
      case 'AWAITING_DELIVERY':
        return 'Awaiting Delivery';
      case 'CONFIRMED_BY_PROCUREMENT':
        return 'Confirmed by Procurement';
      case 'DELIVERY_COMPLETE':
        return 'Delivery Complete';
      default:
        return status;
    }
  };

  const isProcurementTeam = user?.role === 'procurement' || user?.role === 'admin' || user?.role === 'finance';
  const isPM = user?.role === 'pm' || user?.role === 'pmo' || user?.role === 'admin';

  // Filter items based on search term
  const filteredItems = items.filter(item => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    
    // Search in common fields
    if (item.item_code?.toLowerCase().includes(searchLower)) return true;
    if (item.item_name?.toLowerCase().includes(searchLower)) return true;
    if (item.item_description?.toLowerCase().includes(searchLower)) return true;
    if (item.project_name?.toLowerCase().includes(searchLower)) return true;
    if (item.project_code?.toLowerCase().includes(searchLower)) return true;
    if (item.serial_number?.toLowerCase().includes(searchLower)) return true;
    if (item.delivery_status?.toLowerCase().includes(searchLower)) return true;
    
    // Search in procurement-specific fields (if visible)
    if (isProcurementTeam) {
      if (item.supplier_name?.toLowerCase().includes(searchLower)) return true;
      if (item.final_cost?.toString().includes(searchLower)) return true;
      if (item.procurement_delivery_notes?.toLowerCase().includes(searchLower)) return true;
    }
    
    // Search in PM-specific fields (if visible)
    if (isPM) {
      if (item.pm_acceptance_notes?.toLowerCase().includes(searchLower)) return true;
    }
    
    // Search in dates
    if (item.delivery_date?.includes(searchTerm)) return true;
    if (item.actual_delivery_date?.includes(searchTerm)) return true;
    if (item.customer_delivery_date?.includes(searchTerm)) return true;
    
    return false;
  });

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
        <Typography variant="h4" component="h1">
          <ShippingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          {t('procurementPlan.titleWithDelivery')}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<ExportIcon />}
          onClick={handleExport}
        >
          {t('procurementPlan.exportToExcel')}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess('')} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label={t('procurementPlan.search')}
              placeholder={t('procurementPlan.searchPlaceholder')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              variant="outlined"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>{t('procurementPlan.deliveryStatus')}</InputLabel>
              <Select
                value={statusFilter}
                label={t('procurementPlan.deliveryStatus')}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="">{t('procurementPlan.allStatuses')}</MenuItem>
                <MenuItem value="AWAITING_DELIVERY">{t('procurementPlan.awaitingDelivery')}</MenuItem>
                <MenuItem value="CONFIRMED_BY_PROCUREMENT">{t('procurementPlan.confirmedByProcurement')}</MenuItem>
                <MenuItem value="DELIVERY_COMPLETE">{t('procurementPlan.deliveryComplete')}</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>{t('procurementPlan.project')}</InputLabel>
              <Select
                value={projectFilter}
                label={t('procurementPlan.project')}
                onChange={(e) => setProjectFilter(e.target.value as number | '')}
              >
                <MenuItem value="">{t('procurementPlan.allProjects')}</MenuItem>
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">{t('procurementPlan.totalItems')}</Typography>
            <Typography variant="h4">{filteredItems.length}</Typography>
            {searchTerm && (
              <Typography variant="caption" color="textSecondary">
                (filtered from {items.length})
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">{t('procurementPlan.awaitingDelivery')}</Typography>
            <Typography variant="h4">
              {filteredItems.filter(i => i.delivery_status === 'AWAITING_DELIVERY').length}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">{t('procurementPlan.completed')}</Typography>
            <Typography variant="h4">
              {filteredItems.filter(i => i.delivery_status === 'DELIVERY_COMPLETE').length}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Main Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('procurementPlan.itemCode')}</TableCell>
              <TableCell>{t('procurementPlan.itemName')}</TableCell>
              <TableCell>{t('procurementPlan.project')}</TableCell>
              {isProcurementTeam && <TableCell>{t('procurementPlan.supplier')}</TableCell>}
              <TableCell align="right">{t('procurementPlan.quantity')}</TableCell>
              {isProcurementTeam && <TableCell align="right">{t('procurementPlan.cost')}</TableCell>}
              <TableCell>{t('procurementPlan.plannedDelivery')}</TableCell>
              <TableCell>{t('procurementPlan.actualDelivery')}</TableCell>
              {isProcurementTeam && <TableCell>{t('procurementPlan.invoiceStatus')}</TableCell>}
              {isProcurementTeam && <TableCell>{t('procurementPlan.paymentStatus')}</TableCell>}
              <TableCell>{t('procurementPlan.deliveryStatus')}</TableCell>
              <TableCell align="center">{t('procurementPlan.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={isProcurementTeam ? 12 : 8} align="center">
                  <Typography color="textSecondary">
                    {searchTerm || statusFilter || projectFilter
                      ? 'No items match your search criteria.'
                      : 'No items found. Items will appear here after decisions are finalized.'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredItems.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell>{item.item_code}</TableCell>
                  <TableCell>{item.item_name || 'N/A'}</TableCell>
                  <TableCell>{item.project_name || 'N/A'}</TableCell>
                  {isProcurementTeam && <TableCell>{item.supplier_name || 'N/A'}</TableCell>}
                  <TableCell align="right">{item.quantity}</TableCell>
                  {isProcurementTeam && (
                    <TableCell align="right">
                      {formatCurrencyWithCode(item.final_cost, item.final_cost_currency)}
                    </TableCell>
                  )}
                  <TableCell>{item.delivery_date}</TableCell>
                  <TableCell>{item.actual_delivery_date || '-'}</TableCell>
                  {isProcurementTeam && (
                    <TableCell>
                      {item.actual_invoice_issue_date ? (
                        <Chip 
                          label={`${t('procurementPlan.invoiced')} (${formatCurrencyWithCode(item.actual_invoice_amount, item.actual_invoice_currency)})`}
                          color="success"
                          size="small"
                        />
                      ) : (
                        <Chip label={t('procurementPlan.notInvoiced')} color="default" size="small" />
                      )}
                    </TableCell>
                  )}
                  {isProcurementTeam && (
                    <TableCell>
                      {item.actual_payment_date ? (
                        <Chip 
                          label={`${t('procurementPlan.paid')} (${formatCurrencyWithCode(item.actual_payment_amount, item.actual_payment_currency)})`}
                          color="success"
                          size="small"
                        />
                      ) : (
                        <Chip label={t('procurementPlan.notPaid')} color="warning" size="small" />
                      )}
                    </TableCell>
                  )}
                  <TableCell>
                    <Chip
                      label={getStatusLabel(item.delivery_status)}
                      color={getStatusColor(item.delivery_status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => handleViewItem(item)}
                      title={t('procurementPlan.viewDetails')}
                    >
                      <ViewIcon />
                    </IconButton>
                    
                    {/* Procurement Team: Confirm Delivery */}
                    {isProcurementTeam && item.delivery_status === 'AWAITING_DELIVERY' && (
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => {
                          setSelectedItem(item);
                          setConfirmDialogOpen(true);
                        }}
                        title={t('procurementPlan.confirmDelivery')}
                      >
                        <ConfirmIcon />
                      </IconButton>
                    )}
                    
                    {/* PM: Accept Delivery */}
                    {isPM && (item.delivery_status === 'CONFIRMED_BY_PROCUREMENT' || item.delivery_status === 'AWAITING_DELIVERY') && !item.is_accepted_by_pm && (
                      <IconButton
                        size="small"
                        color="info"
                        onClick={() => {
                          setSelectedItem(item);
                          setAcceptDialogOpen(true);
                        }}
                        title={t('procurementPlan.acceptDelivery')}
                      >
                        <AcceptIcon />
                      </IconButton>
                    )}
                    
                    {/* Procurement Team: Enter Invoice (only when delivery complete) */}
                    {isProcurementTeam && item.delivery_status === 'DELIVERY_COMPLETE' && !item.actual_invoice_issue_date && (
                      <IconButton
                        size="small"
                        color="warning"
                        onClick={() => {
                          setSelectedItem(item);
                          setInvoiceData({
                            ...invoiceData,
                            actual_invoice_amount: item.final_cost || 0,
                          });
                          setInvoiceDialogOpen(true);
                        }}
                        title={t('procurementPlan.enterInvoice')}
                      >
                        <InvoiceIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* View Details Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('procurementPlan.itemDetails')}</DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.itemCode')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.item_code}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.itemName')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.item_name || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.description')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.item_description || t('procurementPlan.noDescription')}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.project')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.project_name || t('procurementPlan.nA')}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.quantity')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.quantity}</Typography>
                </Grid>
                
                {isProcurementTeam && (
                  <>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.supplier')}</Typography>
                      <Typography variant="body1" gutterBottom>{selectedItem.supplier_name || t('procurementPlan.nA')}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.finalCost')}</Typography>
                      <Typography variant="body1" gutterBottom>
                        {formatCurrencyWithCode(selectedItem.final_cost, selectedItem.final_cost_currency)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.purchaseDate')}</Typography>
                      <Typography variant="body1" gutterBottom>{selectedItem.purchase_date || t('procurementPlan.nA')}</Typography>
                    </Grid>
                  </>
                )}
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.plannedDelivery')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.delivery_date}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.actualDelivery')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.actual_delivery_date || t('procurementPlan.notYetDelivered')}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.deliveryStatus')}</Typography>
                  <Chip
                    label={getStatusLabel(selectedItem.delivery_status)}
                    color={getStatusColor(selectedItem.delivery_status)}
                    size="small"
                  />
                </Grid>
                
                {/* Invoice and Payment Information */}
                {isProcurementTeam && (
                  <>
                    <Grid item xs={12}>
                      <Divider sx={{ my: 2 }}>
                        <Typography variant="subtitle2" color="textSecondary">Invoice & Payment Information</Typography>
                      </Divider>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.invoiceStatus')}</Typography>
                      {selectedItem.actual_invoice_issue_date ? (
                        <Box>
                          <Chip label={t('procurementPlan.invoiced')} color="success" size="small" sx={{ mb: 1 }} />
                          <Typography variant="body2">
                            Issue Date: {selectedItem.actual_invoice_issue_date}
                          </Typography>
                          <Typography variant="body2">
                            Amount: {formatCurrencyWithCode(selectedItem.actual_invoice_amount, selectedItem.actual_invoice_currency)}
                          </Typography>
                          {selectedItem.actual_invoice_received_date && (
                            <Typography variant="body2">
                              Received: {selectedItem.actual_invoice_received_date}
                            </Typography>
                          )}
                        </Box>
                      ) : (
                        <Chip label={t('procurementPlan.notInvoiced')} color="default" size="small" />
                      )}
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.paymentStatus')}</Typography>
                      {selectedItem.actual_payment_date ? (
                        <Box>
                          <Chip label={t('procurementPlan.paid')} color="success" size="small" sx={{ mb: 1 }} />
                          <Typography variant="body2">
                            Payment Date: {selectedItem.actual_payment_date}
                          </Typography>
                          <Typography variant="body2">
                            Amount: {formatCurrencyWithCode(selectedItem.actual_payment_amount, selectedItem.actual_payment_currency)}
                          </Typography>
                        </Box>
                      ) : (
                        <Chip label={t('procurementPlan.notPaid')} color="warning" size="small" />
                      )}
                    </Grid>
                  </>
                )}
                
                {selectedItem.serial_number && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.serialNumber')}</Typography>
                    <Typography variant="body1" gutterBottom>{selectedItem.serial_number}</Typography>
                  </Grid>
                )}
                
                {isProcurementTeam && selectedItem.procurement_delivery_notes && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.procurementNotes')}</Typography>
                    <Typography variant="body1" gutterBottom>{selectedItem.procurement_delivery_notes}</Typography>
                  </Grid>
                )}
                
                {isPM && selectedItem.pm_acceptance_notes && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.pmAcceptanceNotes')}</Typography>
                    <Typography variant="body1" gutterBottom>{selectedItem.pm_acceptance_notes}</Typography>
                  </Grid>
                )}
                
                {isProcurementTeam && selectedItem.actual_invoice_issue_date && (
                  <>
                    <Grid item xs={12}><Divider sx={{ my: 1 }} /></Grid>
                    <Grid item xs={12}>
                      <Typography variant="h6" gutterBottom>{t('procurementPlan.invoiceInformation')}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.invoiceIssueDate')}</Typography>
                      <Typography variant="body1" gutterBottom>{selectedItem.actual_invoice_issue_date}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.invoiceAmount')}</Typography>
                      <Typography variant="body1" gutterBottom>${selectedItem.actual_invoice_amount?.toLocaleString() || 'N/A'}</Typography>
                    </Grid>
                    {selectedItem.actual_invoice_received_date && (
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.invoiceReceivedDate')}</Typography>
                        <Typography variant="body1" gutterBottom>{selectedItem.actual_invoice_received_date}</Typography>
                      </Grid>
                    )}
                  </>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>{t('procurementPlan.close')}</Button>
        </DialogActions>
      </Dialog>

      {/* Confirm Delivery Dialog (Procurement Team) */}
      <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('procurementPlan.confirmSupplierDelivery')}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label={t('procurementPlan.actualDeliveryDate')}
              type="date"
              value={confirmData.actual_delivery_date}
              onChange={(e) => setConfirmData({ ...confirmData, actual_delivery_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              sx={{ mb: 2 }}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={confirmData.is_correct_item}
                  onChange={(e) => setConfirmData({ ...confirmData, is_correct_item: e.target.checked })}
                />
              }
              label={t('procurementPlan.itemMatchesSpecification')}
            />
            <TextField
              fullWidth
              label={t('procurementPlan.serialNumber')}
              value={confirmData.serial_number}
              onChange={(e) => setConfirmData({ ...confirmData, serial_number: e.target.value })}
              sx={{ mb: 2, mt: 2 }}
            />
            <TextField
              fullWidth
              label={t('procurementPlan.deliveryNotes')}
              multiline
              rows={3}
              value={confirmData.delivery_notes}
              onChange={(e) => setConfirmData({ ...confirmData, delivery_notes: e.target.value })}
              placeholder="e.g., Box was damaged but contents are fine"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>{t('procurementPlan.cancel')}</Button>
          <Button
            variant="contained"
            color="success"
            onClick={handleConfirmDelivery}
            disabled={!confirmData.is_correct_item}
          >
            {t('procurementPlan.confirm')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Accept Delivery Dialog (PM) */}
      <Dialog open={acceptDialogOpen} onClose={() => setAcceptDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('procurementPlan.acceptDeliveryForProject')}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={acceptData.is_accepted_for_project}
                  onChange={(e) => setAcceptData({ ...acceptData, is_accepted_for_project: e.target.checked })}
                />
              }
              label={t('procurementPlan.acceptItemForProject')}
            />
            <TextField
              fullWidth
              label={t('procurementPlan.customerDeliveryDate')}
              type="date"
              value={acceptData.customer_delivery_date}
              onChange={(e) => setAcceptData({ ...acceptData, customer_delivery_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              sx={{ mb: 2, mt: 2 }}
              helperText="When the item was (or will be) delivered to the end customer"
            />
            <TextField
              fullWidth
              label="Acceptance Notes (Optional)"
              multiline
              rows={3}
              value={acceptData.acceptance_notes}
              onChange={(e) => setAcceptData({ ...acceptData, acceptance_notes: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAcceptDialogOpen(false)}>{t('procurementPlan.cancel')}</Button>
          <Button
            variant="contained"
            color="info"
            onClick={handleAcceptDelivery}
            disabled={!acceptData.is_accepted_for_project}
          >
            {t('procurementPlan.acceptDelivery')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Enter Invoice Dialog (Procurement Team) */}
      <Dialog open={invoiceDialogOpen} onClose={() => setInvoiceDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('procurementPlan.enterInvoiceData')}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              Invoice can only be entered when delivery is complete (confirmed by both Procurement and PM).
            </Alert>
            <TextField
              fullWidth
              label={t('procurementPlan.invoiceIssueDate')}
              type="date"
              value={invoiceData.actual_invoice_issue_date}
              onChange={(e) => setInvoiceData({ ...invoiceData, actual_invoice_issue_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              sx={{ mb: 2 }}
              required
            />
            <TextField
              fullWidth
              label={t('procurementPlan.invoiceAmount')}
              type="number"
              value={invoiceData.actual_invoice_amount}
              onChange={(e) => setInvoiceData({ ...invoiceData, actual_invoice_amount: parseFloat(e.target.value) })}
              sx={{ mb: 2 }}
              required
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              fullWidth
              label={t('procurementPlan.invoiceReceivedDateOptional')}
              type="date"
              value={invoiceData.actual_invoice_received_date}
              onChange={(e) => setInvoiceData({ ...invoiceData, actual_invoice_received_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              sx={{ mb: 2 }}
              helperText={t('procurementPlan.whenPaymentReceived')}
            />
            <TextField
              fullWidth
              label={t('procurementPlan.notesOptional')}
              multiline
              rows={3}
              value={invoiceData.notes}
              onChange={(e) => setInvoiceData({ ...invoiceData, notes: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInvoiceDialogOpen(false)}>{t('procurementPlan.cancel')}</Button>
          <Button
            variant="contained"
            color="warning"
            onClick={handleEnterInvoice}
          >
            {t('procurementPlan.enterInvoice')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

