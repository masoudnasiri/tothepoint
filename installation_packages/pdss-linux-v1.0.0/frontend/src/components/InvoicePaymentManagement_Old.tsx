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
  Grid,
  Card,
  CardContent,
  Divider,
  Tabs,
  Tab,
  InputAdornment,
  Tooltip,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Receipt as ReceiptIcon,
  AttachMoney as AttachMoneyIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Visibility as ViewIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizedDateProvider } from './LocalizedDateProvider.tsx';
import { useAuth } from '../contexts/AuthContext.tsx';
import { invoicePaymentAPI, InvoiceCreate, PaymentCreate } from '../services/invoicePaymentAPI.ts';
import { decisionsAPI } from '../services/api.ts';
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';

interface InvoiceData {
  id: number;
  decision_id: number;
  item_code: string;
  project_name: string;
  supplier_name: string;
  invoice_number: string;
  invoice_date: string;
  invoice_amount: number;
  currency: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  payment_terms: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

interface PaymentData {
  id: number;
  invoice_id: number;
  decision_id: number;
  item_code: string;
  project_name: string;
  supplier_name: string;
  payment_date: string;
  payment_amount: number;
  currency: string;
  payment_method: 'cash' | 'bank_transfer' | 'check' | 'credit_card';
  reference_number: string;
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  notes: string;
  created_at: string;
  updated_at: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`invoice-payment-tabpanel-${index}`}
      aria-labelledby={`invoice-payment-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const InvoicePaymentManagement: React.FC = () => {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  
  // Locale-aware date formatter
  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDate = useMemo(() => (dateString: string) => {
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd') : gregorianFormat(d, 'yyyy-MM-dd');
    } catch {
      return new Date(dateString).toLocaleDateString();
    }
  }, [isFa]);
  
  const [tabValue, setTabValue] = useState(0);
  const [invoices, setInvoices] = useState<InvoiceData[]>([]);
  const [payments, setPayments] = useState<PaymentData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [decisions, setDecisions] = useState<any[]>([]);
  
  // View/Edit dialogs
  const [viewInvoiceDialogOpen, setViewInvoiceDialogOpen] = useState(false);
  const [editInvoiceDialogOpen, setEditInvoiceDialogOpen] = useState(false);
  const [deleteConfirmDialogOpen, setDeleteConfirmDialogOpen] = useState(false);
  const [invoiceToDelete, setInvoiceToDelete] = useState<InvoiceData | null>(null);
  
  // Invoice management
  const [invoiceDialogOpen, setInvoiceDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceData | null>(null);
  const [invoiceFormData, setInvoiceFormData] = useState({
    decision_id: '',
    invoice_number: '',
    invoice_date: new Date().toISOString().split('T')[0],
    invoice_amount: 0,
    currency: 'IRR',
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    payment_terms: 'Complete',
    is_final_invoice: false,
    notes: '',
  });

  // Payment management
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<PaymentData | null>(null);
  const [paymentFormData, setPaymentFormData] = useState({
    invoice_id: '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_amount: 0,
    currency: 'IRR',
    payment_method: 'bank_transfer' as const,
    reference_number: '',
    notes: '',
  });

  // Filters and search
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [projectFilter, setProjectFilter] = useState('');

  useEffect(() => {
    fetchData();
    fetchDecisions();
  }, [searchTerm, statusFilter, projectFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [invoicesResponse, paymentsResponse] = await Promise.all([
        invoicePaymentAPI.listInvoices({
          search: searchTerm,
          status: statusFilter,
          project_id: projectFilter ? parseInt(projectFilter) : undefined,
        }),
        invoicePaymentAPI.listPayments({
          search: searchTerm,
          status: statusFilter,
          project_id: projectFilter ? parseInt(projectFilter) : undefined,
        })
      ]);
      setInvoices(invoicesResponse.data);
      setPayments(paymentsResponse.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchDecisions = async () => {
    try {
      const response = await decisionsAPI.list();
      const allDecisions = Array.isArray(response.data) ? response.data : [];
      
      // Only filter out items that are fully paid (not just invoiced)
      const availableDecisions = allDecisions.filter(decision => {
        const totalPaid = parseFloat(decision.actual_payment_amount || 0);
        const finalCost = parseFloat(decision.final_cost || 0);
        
        // Only exclude items that are fully paid
        const isFullyPaid = totalPaid > 0 && totalPaid >= finalCost - 0.01;
        
        // Include items that are not fully paid
        return !isFullyPaid;
      });
      
      setDecisions(availableDecisions);
    } catch (err) {
      console.error('Failed to fetch decisions:', err);
      setDecisions([]);
    }
  };

  const generateInvoiceNumber = () => {
    const timestamp = new Date().getTime();
    const random = Math.floor(Math.random() * 1000);
    return `INV-${timestamp.toString().slice(-6)}-${random.toString().padStart(3, '0')}`;
  };

  // Payment status is now simple: Complete or Partial

  const resetInvoiceForm = () => {
    setInvoiceFormData({
      decision_id: '',
      invoice_number: generateInvoiceNumber(),
      invoice_date: new Date().toISOString().split('T')[0],
      invoice_amount: 0,
      currency: 'IRR',
      due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      payment_terms: 'Complete',
      is_final_invoice: false,
      notes: '',
    });
  };

  const handleCreateInvoice = async () => {
    try {
      const invoiceData: InvoiceCreate = {
        decision_id: parseInt(invoiceFormData.decision_id),
        invoice_number: invoiceFormData.invoice_number,
        invoice_date: invoiceFormData.invoice_date,
        invoice_amount: invoiceFormData.invoice_amount,
        currency: invoiceFormData.currency,
        due_date: invoiceFormData.due_date,
        payment_terms: invoiceFormData.payment_terms,
        is_final_invoice: invoiceFormData.is_final_invoice,
        notes: invoiceFormData.notes,
      };
      
      await invoicePaymentAPI.createInvoice(invoiceData);
      setSuccess('Invoice created successfully');
      setInvoiceDialogOpen(false);
      resetInvoiceForm();
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create invoice');
    }
  };

  const handleCreatePayment = async () => {
    try {
      const paymentData: PaymentCreate = {
        invoice_id: parseInt(paymentFormData.invoice_id),
        payment_date: paymentFormData.payment_date,
        payment_amount: paymentFormData.payment_amount,
        currency: paymentFormData.currency,
        payment_method: paymentFormData.payment_method,
        reference_number: paymentFormData.reference_number,
        notes: paymentFormData.notes,
      };
      
      await invoicePaymentAPI.createPayment(paymentData);
      setSuccess('Payment created successfully');
      setPaymentDialogOpen(false);
      resetPaymentForm();
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create payment');
    }
  };

  const resetPaymentForm = () => {
    setPaymentFormData({
      invoice_id: '',
      payment_date: new Date().toISOString().split('T')[0],
      payment_amount: 0,
      currency: 'IRR',
      payment_method: 'bank_transfer',
      reference_number: '',
      notes: '',
    });
  };

  // Invoice action handlers
  const handleViewInvoice = (invoice: InvoiceData) => {
    setSelectedInvoice(invoice);
    setViewInvoiceDialogOpen(true);
  };

  const handleEditInvoice = (invoice: InvoiceData) => {
    setSelectedInvoice(invoice);
    setEditInvoiceDialogOpen(true);
  };

  const handleDeleteInvoice = (invoice: InvoiceData) => {
    setInvoiceToDelete(invoice);
    setDeleteConfirmDialogOpen(true);
  };

  const confirmDeleteInvoice = async () => {
    if (!invoiceToDelete) return;
    
    try {
      await invoicePaymentAPI.deleteInvoice(invoiceToDelete.id);
      setSuccess(t('finance.invoiceDeleted'));
      fetchData();
      setDeleteConfirmDialogOpen(false);
      setInvoiceToDelete(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('finance.deleteFailed'));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'default';
      case 'sent': return 'info';
      case 'paid': return 'success';
      case 'overdue': return 'error';
      case 'cancelled': return 'default';
      case 'pending': return 'warning';
      case 'completed': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'paid':
      case 'completed':
        return <CheckIcon />;
      case 'overdue':
      case 'failed':
        return <ErrorIcon />;
      case 'pending':
        return <WarningIcon />;
      default:
        return null;
    }
  };

  const formatCurrency = (amount: number, currency: string) => {
    const symbols = { IRR: '﷼', USD: '$', EUR: '€' };
    return `${symbols[currency as keyof typeof symbols] || currency} ${amount.toLocaleString()}`;
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

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          aria-label="Invoice and Payment Management"
        >
          <Tab 
            icon={<ReceiptIcon />} 
            label={t('finance.invoices')} 
            iconPosition="start"
          />
          <Tab 
            icon={<AttachMoneyIcon />} 
            label={t('finance.payments')} 
            iconPosition="start"
          />
        </Tabs>

        {/* Invoices Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">{t('finance.invoices')}</Typography>
            <Box>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                sx={{ mr: 1 }}
              >
                {t('finance.export')}
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  resetInvoiceForm();
                  setInvoiceDialogOpen(true);
                }}
              >
                {t('finance.createInvoice')}
              </Button>
            </Box>
          </Box>

          {/* Filters */}
          <Paper sx={{ p: 2, mb: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label={t('finance.search')}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
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
                  <InputLabel>{t('finance.status')}</InputLabel>
                  <Select
                    value={statusFilter}
                    label={t('finance.status')}
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <MenuItem value="">{t('finance.allStatuses')}</MenuItem>
                    <MenuItem value="draft">{t('finance.draft')}</MenuItem>
                    <MenuItem value="sent">{t('finance.sent')}</MenuItem>
                    <MenuItem value="paid">{t('finance.paid')}</MenuItem>
                    <MenuItem value="overdue">{t('finance.overdue')}</MenuItem>
                    <MenuItem value="cancelled">{t('finance.cancelled')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>{t('finance.project')}</InputLabel>
                  <Select
                    value={projectFilter}
                    label={t('finance.project')}
                    onChange={(e) => setProjectFilter(e.target.value)}
                  >
                    <MenuItem value="">{t('finance.allProjects')}</MenuItem>
                    {/* TODO: Add project options */}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>

          {/* Summary Cards */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <ReceiptIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h6">0</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {t('finance.totalInvoices')}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" sx={{ color: 'success.main' }}>0</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {t('finance.paidInvoices')}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" sx={{ color: 'warning.main' }}>0</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {t('finance.pendingInvoices')}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h6" sx={{ color: 'error.main' }}>0</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {t('finance.overdueInvoices')}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Invoices Table */}
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('finance.invoiceNumber')}</TableCell>
                  <TableCell>{t('finance.itemCode')}</TableCell>
                  <TableCell>{t('finance.project')}</TableCell>
                  <TableCell>{t('finance.supplier')}</TableCell>
                  <TableCell align="right">{t('finance.amount')}</TableCell>
                  <TableCell>{t('finance.invoiceDate')}</TableCell>
                  <TableCell>{t('finance.dueDate')}</TableCell>
                  <TableCell>{t('finance.status')}</TableCell>
                  <TableCell align="center">{t('finance.actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {invoices.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Typography color="textSecondary" sx={{ py: 4 }}>
                        {t('finance.noInvoicesFound')}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  invoices.map((invoice) => (
                    <TableRow key={invoice.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {invoice.invoice_number}
                        </Typography>
                      </TableCell>
                      <TableCell>{invoice.item_code}</TableCell>
                      <TableCell>{invoice.project_name}</TableCell>
                      <TableCell>{invoice.supplier_name}</TableCell>
                      <TableCell align="right">
                        {formatCurrency(invoice.invoice_amount, invoice.currency)}
                      </TableCell>
                      <TableCell>{formatDisplayDate(invoice.invoice_date)}</TableCell>
                      <TableCell>{formatDisplayDate(invoice.due_date)}</TableCell>
                      <TableCell>
                        <Chip
                          icon={getStatusIcon(invoice.status)}
                          label={t(`finance.${invoice.status}`)}
                          color={getStatusColor(invoice.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title={t('finance.viewDetails')}>
                          <IconButton 
                            size="small" 
                            color="primary"
                            onClick={() => handleViewInvoice(invoice)}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t('finance.edit')}>
                          <IconButton 
                            size="small" 
                            color="primary"
                            onClick={() => handleEditInvoice(invoice)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t('finance.delete')}>
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleDeleteInvoice(invoice)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* Payments Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">{t('finance.payments')}</Typography>
            <Box>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                sx={{ mr: 1 }}
              >
                {t('finance.export')}
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setPaymentDialogOpen(true)}
              >
                {t('finance.createPayment')}
              </Button>
            </Box>
          </Box>

          {/* Payments Table */}
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('finance.referenceNumber')}</TableCell>
                  <TableCell>{t('finance.itemCode')}</TableCell>
                  <TableCell>{t('finance.project')}</TableCell>
                  <TableCell>{t('finance.supplier')}</TableCell>
                  <TableCell align="right">{t('finance.amount')}</TableCell>
                  <TableCell>{t('finance.paymentDate')}</TableCell>
                  <TableCell>{t('finance.paymentMethod')}</TableCell>
                  <TableCell>{t('finance.status')}</TableCell>
                  <TableCell align="center">{t('finance.actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {payments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Typography color="textSecondary" sx={{ py: 4 }}>
                        {t('finance.noPaymentsFound')}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  payments.map((payment) => (
                    <TableRow key={payment.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {payment.reference_number}
                        </Typography>
                      </TableCell>
                      <TableCell>{payment.item_code}</TableCell>
                      <TableCell>{payment.project_name}</TableCell>
                      <TableCell>{payment.supplier_name}</TableCell>
                      <TableCell align="right">
                        {formatCurrency(payment.payment_amount, payment.currency)}
                      </TableCell>
                      <TableCell>{formatDisplayDate(payment.payment_date)}</TableCell>
                      <TableCell>{t(`finance.${payment.payment_method}`)}</TableCell>
                      <TableCell>
                        <Chip
                          icon={getStatusIcon(payment.status)}
                          label={t(`finance.${payment.status}`)}
                          color={getStatusColor(payment.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title={t('finance.viewDetails')}>
                          <IconButton size="small" color="primary">
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t('finance.edit')}>
                          <IconButton size="small" color="primary">
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t('finance.delete')}>
                          <IconButton size="small" color="error">
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
      </Paper>

      {/* Create Invoice Dialog */}
      <Dialog open={invoiceDialogOpen} onClose={() => {
        setInvoiceDialogOpen(false);
        resetInvoiceForm();
      }} maxWidth="md" fullWidth>
        <DialogTitle>{t('finance.createInvoice')}</DialogTitle>
        <DialogContent>
          <LocalizedDateProvider>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>{t('finance.decisionId')}</InputLabel>
                  <Select
                    value={invoiceFormData.decision_id}
                    label={t('finance.decisionId')}
                    onChange={(e) => {
                      const selectedDecision = decisions.find(d => d.id.toString() === e.target.value);
                      if (selectedDecision) {
                        const totalPaid = selectedDecision.actual_payment_amount || 0;
                        const totalInvoiced = selectedDecision.actual_invoice_amount || 0;
                        const remainingAmount = totalInvoiced - totalPaid;
                        const isPartiallyPaid = totalInvoiced > 0 && totalPaid > 0 && totalPaid < totalInvoiced;
                        
                        // For partially paid items, suggest remaining amount
                        // For new items, use final cost
                        const suggestedAmount = isPartiallyPaid ? remainingAmount : (selectedDecision.final_cost || 0);
                        
                        setInvoiceFormData({ 
                          ...invoiceFormData, 
                          decision_id: e.target.value,
                          invoice_amount: suggestedAmount,
                          currency: selectedDecision.final_cost_currency || 'IRR',
                          notes: selectedDecision.notes || ''
                        });
                      }
                    }}
                  >
                    {decisions && decisions.length > 0 ? decisions.map((decision) => {
                      const totalPaid = decision.actual_payment_amount || 0;
                      const totalInvoiced = decision.actual_invoice_amount || 0;
                      const remainingAmount = totalInvoiced - totalPaid;
                      const isPartiallyPaid = totalInvoiced > 0 && totalPaid > 0 && totalPaid < totalInvoiced;
                      
                      return (
                        <MenuItem key={decision.id} value={decision.id.toString()}>
                          {decision.item_code} - {decision.item_name} (Project {decision.project_id})
                          {isPartiallyPaid && (
                            <span style={{ color: '#ff9800', fontSize: '0.8em', marginLeft: '8px' }}>
                              (Remaining: {remainingAmount.toLocaleString()} {decision.actual_invoice_amount_currency || 'IRR'})
                            </span>
                          )}
                        </MenuItem>
                      );
                    }) : (
                      <MenuItem disabled>No decisions available for invoicing</MenuItem>
                    )}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label={t('finance.invoiceNumber')}
                  value={invoiceFormData.invoice_number}
                  onChange={(e) => setInvoiceFormData({ ...invoiceFormData, invoice_number: e.target.value })}
                  required
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <Button 
                          size="small" 
                          onClick={() => setInvoiceFormData({ ...invoiceFormData, invoice_number: generateInvoiceNumber() })}
                        >
                          Generate
                        </Button>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <DatePicker
                  label={t('finance.invoiceDate')}
                  value={new Date(invoiceFormData.invoice_date)}
                  onChange={(newValue) => {
                    if (newValue) {
                      const newInvoiceDate = newValue.toISOString().split('T')[0];
                      // Due date is same as invoice date for simple payment status
                      setInvoiceFormData({ 
                        ...invoiceFormData, 
                        invoice_date: newInvoiceDate,
                        due_date: newInvoiceDate  // Due date is same as invoice date
                      });
                    }
                  }}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <DatePicker
                  label={t('finance.dueDate')}
                  value={new Date(invoiceFormData.due_date)}
                  onChange={(newValue) => {
                    if (newValue) {
                      setInvoiceFormData({ ...invoiceFormData, due_date: newValue.toISOString().split('T')[0] });
                    }
                  }}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label={t('finance.invoiceAmount')}
                  type="number"
                  value={invoiceFormData.invoice_amount}
                  onChange={(e) => setInvoiceFormData({ ...invoiceFormData, invoice_amount: parseFloat(e.target.value) || 0 })}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('finance.currency')}</InputLabel>
                  <Select
                    value={invoiceFormData.currency}
                    label={t('finance.currency')}
                    onChange={(e) => setInvoiceFormData({ ...invoiceFormData, currency: e.target.value })}
                  >
                    <MenuItem value="IRR">IRR</MenuItem>
                    <MenuItem value="USD">USD</MenuItem>
                    <MenuItem value="EUR">EUR</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('finance.paymentStatus')}</InputLabel>
                  <Select
                    value={invoiceFormData.payment_terms}
                    label={t('finance.paymentStatus')}
                    onChange={(e) => {
                      const newPaymentStatus = e.target.value;
                      setInvoiceFormData({ 
                        ...invoiceFormData, 
                        payment_terms: newPaymentStatus
                      });
                    }}
                  >
                    <MenuItem value="Complete">{t('finance.completePayment')}</MenuItem>
                    <MenuItem value="Partial">{t('finance.partialPayment')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={invoiceFormData.is_final_invoice}
                      onChange={(e) => setInvoiceFormData({ 
                        ...invoiceFormData, 
                        is_final_invoice: e.target.checked 
                      })}
                    />
                  }
                  label={t('finance.finalInvoice')}
                />
                <Typography variant="caption" color="text.secondary" sx={{ ml: 4, display: 'block' }}>
                  {t('finance.finalInvoiceDescription')}
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('finance.notes')}
                  multiline
                  rows={3}
                  value={invoiceFormData.notes}
                  onChange={(e) => setInvoiceFormData({ ...invoiceFormData, notes: e.target.value })}
                />
              </Grid>
            </Grid>
          </LocalizedDateProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setInvoiceDialogOpen(false);
            resetInvoiceForm();
          }}>{t('finance.cancel')}</Button>
          <Button onClick={handleCreateInvoice} variant="contained">
            {t('finance.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Payment Dialog */}
      <Dialog open={paymentDialogOpen} onClose={() => setPaymentDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('finance.createPayment')}</DialogTitle>
        <DialogContent>
          <LocalizedDateProvider>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('finance.invoice')}</InputLabel>
                  <Select
                    value={paymentFormData.invoice_id}
                    label={t('finance.invoice')}
                    onChange={(e) => setPaymentFormData({ ...paymentFormData, invoice_id: e.target.value })}
                    required
                  >
                    {/* TODO: Add invoice options */}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label={t('finance.referenceNumber')}
                  value={paymentFormData.reference_number}
                  onChange={(e) => setPaymentFormData({ ...paymentFormData, reference_number: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <DatePicker
                  label={t('finance.paymentDate')}
                  value={new Date(paymentFormData.payment_date)}
                  onChange={(newValue) => {
                    if (newValue) {
                      setPaymentFormData({ ...paymentFormData, payment_date: newValue.toISOString().split('T')[0] });
                    }
                  }}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label={t('finance.paymentAmount')}
                  type="number"
                  value={paymentFormData.payment_amount}
                  onChange={(e) => setPaymentFormData({ ...paymentFormData, payment_amount: parseFloat(e.target.value) || 0 })}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('finance.currency')}</InputLabel>
                  <Select
                    value={paymentFormData.currency}
                    label={t('finance.currency')}
                    onChange={(e) => setPaymentFormData({ ...paymentFormData, currency: e.target.value })}
                  >
                    <MenuItem value="IRR">IRR</MenuItem>
                    <MenuItem value="USD">USD</MenuItem>
                    <MenuItem value="EUR">EUR</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('finance.paymentMethod')}</InputLabel>
                  <Select
                    value={paymentFormData.payment_method}
                    label={t('finance.paymentMethod')}
                    onChange={(e) => setPaymentFormData({ ...paymentFormData, payment_method: e.target.value as any })}
                  >
                    <MenuItem value="cash">{t('finance.cash')}</MenuItem>
                    <MenuItem value="bank_transfer">{t('finance.bankTransfer')}</MenuItem>
                    <MenuItem value="check">{t('finance.check')}</MenuItem>
                    <MenuItem value="credit_card">{t('finance.creditCard')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('finance.notes')}
                  multiline
                  rows={3}
                  value={paymentFormData.notes}
                  onChange={(e) => setPaymentFormData({ ...paymentFormData, notes: e.target.value })}
                />
              </Grid>
            </Grid>
          </LocalizedDateProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPaymentDialogOpen(false)}>{t('finance.cancel')}</Button>
          <Button onClick={handleCreatePayment} variant="contained">
            {t('finance.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Invoice Dialog */}
      <Dialog open={viewInvoiceDialogOpen} onClose={() => setViewInvoiceDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('finance.invoiceDetails')}</DialogTitle>
        <DialogContent>
          {selectedInvoice && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('finance.invoiceNumber')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedInvoice.invoice_number}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('finance.itemCode')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedInvoice.item_code}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('finance.project')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedInvoice.project_name}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('finance.supplier')}</Typography>
                  <Typography variant="body1" gutterBottom>{selectedInvoice.supplier_name}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('finance.invoiceAmount')}</Typography>
                  <Typography variant="body1" gutterBottom>
                    {formatCurrency(selectedInvoice.invoice_amount, selectedInvoice.currency)}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('finance.invoiceDate')}</Typography>
                  <Typography variant="body1" gutterBottom>
                    {formatDisplayDate(selectedInvoice.invoice_date)}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('finance.dueDate')}</Typography>
                  <Typography variant="body1" gutterBottom>
                    {formatDisplayDate(selectedInvoice.due_date)}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">{t('finance.status')}</Typography>
                  <Chip
                    icon={getStatusIcon(selectedInvoice.status)}
                    label={t(`finance.${selectedInvoice.status}`)}
                    color={getStatusColor(selectedInvoice.status)}
                    size="small"
                  />
                </Grid>
                {selectedInvoice.payment_terms && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">{t('finance.paymentTerms')}</Typography>
                    <Typography variant="body1" gutterBottom>{selectedInvoice.payment_terms}</Typography>
                  </Grid>
                )}
                {selectedInvoice.notes && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">{t('finance.notes')}</Typography>
                    <Typography variant="body1" gutterBottom>{selectedInvoice.notes}</Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewInvoiceDialogOpen(false)}>{t('finance.close')}</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmDialogOpen} onClose={() => setDeleteConfirmDialogOpen(false)}>
        <DialogTitle>{t('finance.confirmDelete')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('finance.deleteInvoiceConfirm', { invoiceNumber: invoiceToDelete?.invoice_number })}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmDialogOpen(false)}>{t('finance.cancel')}</Button>
          <Button onClick={confirmDeleteInvoice} color="error" variant="contained">
            {t('finance.delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
