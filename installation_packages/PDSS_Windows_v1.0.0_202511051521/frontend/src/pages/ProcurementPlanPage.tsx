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
  Pagination,
  Stack,
  FormGroup,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  CheckCircle as ConfirmIcon,
  ThumbUp as AcceptIcon,
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
} from '../types/index.ts';
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizedDateProvider } from '../components/LocalizedDateProvider.tsx';

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
  const { t, i18n } = useTranslation();
  
  // Locale-aware date formatter
  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDate = useMemo(() => (dateString: string | null | undefined) => {
    if (!dateString) return '-';
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd') : gregorianFormat(d, 'yyyy-MM-dd');
    } catch {
      return dateString;
    }
  }, [isFa]);
  const [items, setItems] = useState<ProcurementPlanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [projectFilter, setProjectFilter] = useState<number | ''>('');
  const [projects, setProjects] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  const [totalItems, setTotalItems] = useState(0);
  
  // Additional filters
  const [invoiceStatusFilter, setInvoiceStatusFilter] = useState<string>('');
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<string>('');
  const [dateRangeFilter, setDateRangeFilter] = useState<{
    startDate: string;
    endDate: string;
  }>({
    startDate: '',
    endDate: '',
  });
  
  // Dialogs
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [acceptDialogOpen, setAcceptDialogOpen] = useState(false);
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

  useEffect(() => {
    fetchItems();
    fetchProjects();
  }, [statusFilter, projectFilter, invoiceStatusFilter, paymentStatusFilter, dateRangeFilter, currentPage, itemsPerPage]);

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, projectFilter, invoiceStatusFilter, paymentStatusFilter, dateRangeFilter, searchTerm]);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const params: any = {
        page: currentPage,
        limit: itemsPerPage,
      };
      
      if (statusFilter) params.status_filter = statusFilter;
      if (projectFilter) params.project_id = projectFilter;
      if (invoiceStatusFilter) params.invoice_status = invoiceStatusFilter;
      if (paymentStatusFilter) params.payment_status = paymentStatusFilter;
      if (dateRangeFilter.startDate) params.start_date = dateRangeFilter.startDate;
      if (dateRangeFilter.endDate) params.end_date = dateRangeFilter.endDate;
      if (searchTerm) params.search = searchTerm;
      
      const response = await procurementPlanAPI.list(params);
      setItems(response.data.items || response.data);
      setTotalItems(response.data.total || response.data.length);
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

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setCurrentPage(page);
  };

  const handleItemsPerPageChange = (event: any) => {
    setItemsPerPage(Number(event.target.value));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setStatusFilter('');
    setProjectFilter('');
    setInvoiceStatusFilter('');
    setPaymentStatusFilter('');
    setDateRangeFilter({ startDate: '', endDate: '' });
    setSearchTerm('');
    setCurrentPage(1);
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

  const getInvoiceStatusLabel = (item: ProcurementPlanItem): string => {
    if (item.actual_invoice_issue_date) {
      return t('procurementPlan.invoiced');
    }
    return t('procurementPlan.notInvoiced');
  };

  const getInvoiceStatusColor = (item: ProcurementPlanItem): 'default' | 'warning' | 'success' => {
    if (item.actual_invoice_issue_date) {
      return 'success';
    }
    return 'default';
  };

  // Payment In Status (Customer Payments - Revenue)
  const getPaymentInStatusLabel = (status?: string): string => {
    switch (status) {
      case 'fully_paid':
        return t('procurementPlan.fullyPaid');
      case 'partially_paid':
        return t('procurementPlan.partiallyPaid');
      default:
        return t('procurementPlan.notPaid');
    }
  };

  const getPaymentInStatusColor = (status?: string): 'default' | 'warning' | 'success' => {
    switch (status) {
      case 'fully_paid':
        return 'success';
      case 'partially_paid':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Payment Out Status (Supplier Payments - Costs)
  const getPaymentOutStatusLabel = (status?: string): string => {
    switch (status) {
      case 'fully_paid':
        return t('procurementPlan.fullyPaid');
      case 'partially_paid':
        return t('procurementPlan.partiallyPaid');
      default:
        return t('procurementPlan.notPaid');
    }
  };

  const getPaymentOutStatusColor = (status?: string): 'default' | 'warning' | 'success' => {
    switch (status) {
      case 'fully_paid':
        return 'success';
      case 'partially_paid':
        return 'warning';
      default:
        return 'default';
    }
  };

  const isProcurementTeam = user?.role === 'procurement' || user?.role === 'admin' || user?.role === 'finance';
  const isPM = user?.role === 'pm' || user?.role === 'pmo' || user?.role === 'admin';

  // Calculate pagination info
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

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
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{t('procurementPlan.filters')}</Typography>
          <Button variant="outlined" onClick={clearFilters} size="small">
            {t('procurementPlan.clearFilters')}
          </Button>
        </Box>
        
        <Grid container spacing={2}>
          {/* Search */}
          <Grid item xs={12} md={3}>
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
          
          {/* Delivery Status */}
          <Grid item xs={12} md={3}>
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
          
          {/* Project */}
          <Grid item xs={12} md={3}>
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
          
          {/* Invoice Status */}
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>{t('procurementPlan.invoiceStatus')}</InputLabel>
              <Select
                value={invoiceStatusFilter}
                label={t('procurementPlan.invoiceStatus')}
                onChange={(e) => setInvoiceStatusFilter(e.target.value)}
              >
                <MenuItem value="">{t('procurementPlan.allInvoiceStatuses')}</MenuItem>
                <MenuItem value="invoiced">{t('procurementPlan.invoiced')}</MenuItem>
                <MenuItem value="not_invoiced">{t('procurementPlan.notInvoiced')}</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          {/* Payment Status */}
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>{t('procurementPlan.paymentStatus')}</InputLabel>
              <Select
                value={paymentStatusFilter}
                label={t('procurementPlan.paymentStatus')}
                onChange={(e) => setPaymentStatusFilter(e.target.value)}
              >
                <MenuItem value="">{t('procurementPlan.allPaymentStatuses')}</MenuItem>
                <MenuItem value="not_paid">{t('procurementPlan.notPaid')}</MenuItem>
                <MenuItem value="partially_paid">{t('procurementPlan.partiallyPaid')}</MenuItem>
                <MenuItem value="fully_paid">{t('procurementPlan.fullyPaid')}</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          {/* Date Range */}
          <Grid item xs={12} md={3}>
            <LocalizedDateProvider>
              <DatePicker
                label={t('procurementPlan.deliveryDateFrom')}
                value={dateRangeFilter.startDate ? new Date(dateRangeFilter.startDate) : null}
                onChange={(newValue) => {
                  if (newValue) {
                    setDateRangeFilter({ ...dateRangeFilter, startDate: newValue.toISOString().split('T')[0] });
                  } else {
                    setDateRangeFilter({ ...dateRangeFilter, startDate: '' });
                  }
                }}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </LocalizedDateProvider>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <LocalizedDateProvider>
              <DatePicker
                label={t('procurementPlan.deliveryDateTo')}
                value={dateRangeFilter.endDate ? new Date(dateRangeFilter.endDate) : null}
                onChange={(newValue) => {
                  if (newValue) {
                    setDateRangeFilter({ ...dateRangeFilter, endDate: newValue.toISOString().split('T')[0] });
                  } else {
                    setDateRangeFilter({ ...dateRangeFilter, endDate: '' });
                  }
                }}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </LocalizedDateProvider>
          </Grid>
        </Grid>
      </Paper>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">{t('procurementPlan.totalItems')}</Typography>
            <Typography variant="h4">{totalItems}</Typography>
            <Typography variant="caption" color="textSecondary">
              {t('procurementPlan.showingItems', { start: startItem, end: endItem, total: totalItems })}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">{t('procurementPlan.awaitingDelivery')}</Typography>
            <Typography variant="h4">
              {items.filter(i => i.delivery_status === 'AWAITING_DELIVERY').length}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">{t('procurementPlan.completed')}</Typography>
            <Typography variant="h4">
              {items.filter(i => i.delivery_status === 'DELIVERY_COMPLETE').length}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">{t('procurementPlan.invoiced')}</Typography>
            <Typography variant="h4">
              {items.filter(i => i.actual_invoice_issue_date).length}
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
              <TableCell>{t('procurementPlan.purchaseDate')}</TableCell>
              <TableCell>{t('procurementPlan.plannedDelivery')}</TableCell>
              <TableCell>{t('procurementPlan.actualDelivery')}</TableCell>
              <TableCell>{t('procurementPlan.deliveryStatus')}</TableCell>
              <TableCell>{t('procurementPlan.invoiceStatus')}</TableCell>
              <TableCell>{t('procurementPlan.paymentInStatus')}</TableCell>
              <TableCell>{t('procurementPlan.paymentOutStatus')}</TableCell>
              <TableCell align="center">{t('procurementPlan.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={isProcurementTeam ? 16 : 12} align="center">
                  <Typography color="textSecondary">
                    {searchTerm || statusFilter || projectFilter || invoiceStatusFilter || paymentStatusFilter || dateRangeFilter.startDate || dateRangeFilter.endDate
                      ? t('procurementPlan.noItemsMatchCriteria')
                      : t('procurementPlan.noItemsFound')}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
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
                  <TableCell>{formatDisplayDate(item.purchase_date)}</TableCell>
                  <TableCell>{formatDisplayDate(item.delivery_date)}</TableCell>
                  <TableCell>{formatDisplayDate(item.actual_delivery_date)}</TableCell>
                  <TableCell>
                    <Chip
                      label={getStatusLabel(item.delivery_status)}
                      color={getStatusColor(item.delivery_status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getInvoiceStatusLabel(item)}
                      color={getInvoiceStatusColor(item)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getPaymentInStatusLabel(item.payment_in_status)}
                      color={getPaymentInStatusColor(item.payment_in_status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getPaymentOutStatusLabel(item.payment_out_status)}
                      color={getPaymentOutStatusColor(item.payment_out_status)}
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
                    
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination Controls */}
      {totalItems > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3, mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="textSecondary">
              {t('procurementPlan.itemsPerPage')}:
            </Typography>
            <FormControl size="small" sx={{ minWidth: 80 }}>
              <Select
                value={itemsPerPage}
                onChange={handleItemsPerPageChange}
                displayEmpty
              >
                <MenuItem value={10}>10</MenuItem>
                <MenuItem value={25}>25</MenuItem>
                <MenuItem value={50}>50</MenuItem>
                <MenuItem value={100}>100</MenuItem>
              </Select>
            </FormControl>
            <Typography variant="body2" color="textSecondary">
              {t('procurementPlan.showingItems', { start: startItem, end: endItem, total: totalItems })}
            </Typography>
          </Box>
          
          <Stack spacing={2} alignItems="center">
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={handlePageChange}
              color="primary"
              size="large"
              showFirstButton
              showLastButton
            />
            <Typography variant="caption" color="textSecondary">
              {t('procurementPlan.pageOf', { current: currentPage, total: totalPages })}
            </Typography>
          </Stack>
        </Box>
      )}

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
                      <Typography variant="body1" gutterBottom>{formatDisplayDate(selectedItem.purchase_date)}</Typography>
                    </Grid>
                  </>
                )}
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.plannedDelivery')}</Typography>
                  <Typography variant="body1" gutterBottom>{formatDisplayDate(selectedItem.delivery_date)}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.actualDelivery')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.actual_delivery_date ? formatDisplayDate(selectedItem.actual_delivery_date) : t('procurementPlan.notYetDelivered')}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.deliveryStatus')}</Typography>
                  <Chip
                    label={getStatusLabel(selectedItem.delivery_status)}
                    color={getStatusColor(selectedItem.delivery_status)}
                    size="small"
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.invoiceStatus')}</Typography>
                  <Chip
                    label={getInvoiceStatusLabel(selectedItem)}
                    color={getInvoiceStatusColor(selectedItem)}
                    size="small"
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.paymentInStatus')}</Typography>
                  <Chip
                    label={getPaymentInStatusLabel(selectedItem.payment_in_status)}
                    color={getPaymentInStatusColor(selectedItem.payment_in_status)}
                    size="small"
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.paymentOutStatus')}</Typography>
                  <Chip
                    label={getPaymentOutStatusLabel(selectedItem.payment_out_status)}
                    color={getPaymentOutStatusColor(selectedItem.payment_out_status)}
                    size="small"
                  />
                </Grid>
                
                {selectedItem.actual_invoice_issue_date && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.invoiceDate')}</Typography>
                    <Typography variant="body1" gutterBottom>{formatDisplayDate(selectedItem.actual_invoice_issue_date)}</Typography>
                  </Grid>
                )}
                
                {selectedItem.actual_invoice_amount && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.invoiceAmount')}</Typography>
                    <Typography variant="body1" gutterBottom>
                      {formatCurrencyWithCode(selectedItem.actual_invoice_amount, selectedItem.actual_invoice_currency)}
                    </Typography>
                  </Grid>
                )}
                
                {selectedItem.actual_payment_date && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.paymentDate')}</Typography>
                    <Typography variant="body1" gutterBottom>{formatDisplayDate(selectedItem.actual_payment_date)}</Typography>
                  </Grid>
                )}
                
                {selectedItem.actual_payment_amount && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">{t('procurementPlan.paymentAmount')}</Typography>
                    <Typography variant="body1" gutterBottom>
                      {formatCurrencyWithCode(selectedItem.actual_payment_amount, selectedItem.actual_payment_currency)}
                    </Typography>
                  </Grid>
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
            <LocalizedDateProvider>
              <DatePicker
                label={t('procurementPlan.actualDeliveryDate')}
                value={confirmData.actual_delivery_date ? new Date(confirmData.actual_delivery_date) : null}
                onChange={(newValue) => {
                  if (newValue) {
                    setConfirmData({ ...confirmData, actual_delivery_date: newValue.toISOString().split('T')[0] });
                  } else {
                    setConfirmData({ ...confirmData, actual_delivery_date: '' });
                  }
                }}
                slotProps={{ textField: { fullWidth: true, sx: { mb: 2 } } }}
              />
            </LocalizedDateProvider>
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
            <LocalizedDateProvider>
              <DatePicker
                label={t('procurementPlan.customerDeliveryDate')}
                value={acceptData.customer_delivery_date ? new Date(acceptData.customer_delivery_date) : null}
                onChange={(newValue) => {
                  if (newValue) {
                    setAcceptData({ ...acceptData, customer_delivery_date: newValue.toISOString().split('T')[0] });
                  } else {
                    setAcceptData({ ...acceptData, customer_delivery_date: '' });
                  }
                }}
                slotProps={{ textField: { fullWidth: true, helperText: 'When the item was (or will be) delivered to the end customer', sx: { mb: 2, mt: 2 } } }}
              />
            </LocalizedDateProvider>
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

    </Box>
  );
};

