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
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useAuth } from '../contexts/AuthContext.tsx';
import { invoicePaymentAPI, InvoiceCreate, PaymentCreate } from '../services/invoicePaymentAPI.ts';
import { decisionsAPI } from '../services/api.ts';
import { useTranslation } from 'react-i18next';

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
  payment_method: string;
  reference_number: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

interface DecisionData {
  id: number;
  item_code: string;
  project_id: number;
  final_cost: number;
  final_cost_currency: string;
  actual_invoice_amount: number;
  actual_payment_amount: number;
  is_final_invoice: boolean;
  notes: string;
}

const InvoicePaymentManagement: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  
  // State management
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  
  // Data
  const [invoices, setInvoices] = useState<InvoiceData[]>([]);
  const [payments, setPayments] = useState<PaymentData[]>([]);
  const [decisions, setDecisions] = useState<DecisionData[]>([]);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [projectFilter, setProjectFilter] = useState('');
  
  // Invoice dialog
  const [invoiceDialogOpen, setInvoiceDialogOpen] = useState(false);
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
  
  // Payment dialog
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [paymentFormData, setPaymentFormData] = useState({
    invoice_id: '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_amount: 0,
    currency: 'IRR',
    payment_method: 'bank_transfer',
    reference_number: '',
    notes: '',
  });
  
  // View dialogs
  const [viewInvoiceDialogOpen, setViewInvoiceDialogOpen] = useState(false);
  const [viewPaymentDialogOpen, setViewPaymentDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceData | null>(null);
  const [selectedPayment, setSelectedPayment] = useState<PaymentData | null>(null);
  
  // Delete confirmation
  const [deleteConfirmDialogOpen, setDeleteConfirmDialogOpen] = useState(false);
  const [invoiceToDelete, setInvoiceToDelete] = useState<InvoiceData | null>(null);

  // Load data on component mount
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
          project_id: projectFilter ? parseInt(projectFilter) : undefined,
        }),
      ]);
      
      setInvoices(invoicesResponse.data || []);
      setPayments(paymentsResponse.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const fetchDecisions = async () => {
    try {
      const response = await decisionsAPI.list();
      const allDecisions = Array.isArray(response.data) ? response.data : [];
      
      // SIMPLE LOGIC: Only filter out items that are fully paid
      const availableDecisions = allDecisions.filter(decision => {
        const totalPaid = parseFloat(decision.actual_payment_amount || 0);
        const finalCost = parseFloat(decision.final_cost || 0);
        
        // Only exclude items that are fully paid
        const isFullyPaid = totalPaid > 0 && totalPaid >= finalCost - 0.01;
        
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
      fetchDecisions(); // Refresh decisions to update filtering
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
      fetchDecisions(); // Refresh decisions to update filtering
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

  const handleViewInvoice = (invoice: InvoiceData) => {
    setSelectedInvoice(invoice);
    setViewInvoiceDialogOpen(true);
  };

  const handleViewPayment = (payment: PaymentData) => {
    setSelectedPayment(payment);
    setViewPaymentDialogOpen(true);
  };

  const handleDeleteInvoice = (invoice: InvoiceData) => {
    setInvoiceToDelete(invoice);
    setDeleteConfirmDialogOpen(true);
  };

  const confirmDeleteInvoice = async () => {
    if (!invoiceToDelete) return;
    
    try {
      await invoicePaymentAPI.deleteInvoice(invoiceToDelete.id);
      setSuccess('Invoice deleted successfully');
      setDeleteConfirmDialogOpen(false);
      setInvoiceToDelete(null);
      fetchData();
      fetchDecisions(); // Refresh decisions to update filtering
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete invoice');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {t('finance.invoiceAndPayment')}
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        {t('finance.invoiceAndPaymentSubtitle')}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
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
        {tabValue === 0 && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">{t('finance.invoices')}</Typography>
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

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('finance.invoiceNumber')}</TableCell>
                      <TableCell>{t('finance.itemCode')}</TableCell>
                      <TableCell>{t('finance.project')}</TableCell>
                      <TableCell>{t('finance.amount')}</TableCell>
                      <TableCell>{t('finance.invoiceDate')}</TableCell>
                      <TableCell>{t('finance.dueDate')}</TableCell>
                      <TableCell>{t('finance.status')}</TableCell>
                      <TableCell>{t('finance.actions')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {invoices.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell>{invoice.invoice_number}</TableCell>
                        <TableCell>{invoice.item_code}</TableCell>
                        <TableCell>{invoice.project_name}</TableCell>
                        <TableCell>
                          {invoice.invoice_amount.toLocaleString()} {invoice.currency}
                        </TableCell>
                        <TableCell>{invoice.invoice_date}</TableCell>
                        <TableCell>{invoice.due_date}</TableCell>
                        <TableCell>
                          <Chip 
                            label={invoice.status} 
                            color={invoice.status === 'paid' ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton onClick={() => handleViewInvoice(invoice)}>
                            <ViewIcon />
                          </IconButton>
                          <IconButton onClick={() => handleDeleteInvoice(invoice)} color="error">
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}

        {/* Payments Tab */}
        {tabValue === 1 && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">{t('finance.payments')}</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  resetPaymentForm();
                  setPaymentDialogOpen(true);
                }}
              >
                {t('finance.createPayment')}
              </Button>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('finance.referenceNumber')}</TableCell>
                      <TableCell>{t('finance.itemCode')}</TableCell>
                      <TableCell>{t('finance.project')}</TableCell>
                      <TableCell>{t('finance.paymentAmount')}</TableCell>
                      <TableCell>{t('finance.paymentDate')}</TableCell>
                      <TableCell>{t('finance.paymentMethod')}</TableCell>
                      <TableCell>{t('finance.actions')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {payments.map((payment) => (
                      <TableRow key={payment.id}>
                        <TableCell>{payment.reference_number}</TableCell>
                        <TableCell>{payment.item_code}</TableCell>
                        <TableCell>{payment.project_name}</TableCell>
                        <TableCell>
                          {payment.payment_amount.toLocaleString()} {payment.currency}
                        </TableCell>
                        <TableCell>{payment.payment_date}</TableCell>
                        <TableCell>{payment.payment_method}</TableCell>
                        <TableCell>
                          <IconButton onClick={() => handleViewPayment(payment)}>
                            <ViewIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}
      </Paper>

      {/* Create Invoice Dialog */}
      <Dialog open={invoiceDialogOpen} onClose={() => setInvoiceDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('finance.createInvoice')}</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
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
                        setInvoiceFormData({ 
                          ...invoiceFormData, 
                          decision_id: e.target.value,
                          invoice_amount: selectedDecision.final_cost || 0,
                          currency: selectedDecision.final_cost_currency || 'IRR',
                          notes: selectedDecision.notes || ''
                        });
                      }
                    }}
                  >
                    {decisions && decisions.length > 0 ? decisions.map((decision) => (
                      <MenuItem key={decision.id} value={decision.id.toString()}>
                        {decision.item_code} - (Project {decision.project_id})
                      </MenuItem>
                    )) : (
                      <MenuItem disabled>No available decisions</MenuItem>
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
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <Button size="small" onClick={() => setInvoiceFormData({ ...invoiceFormData, invoice_number: generateInvoiceNumber() })}>
                          GENERATE
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
                      setInvoiceFormData({ 
                        ...invoiceFormData, 
                        invoice_date: newValue.toISOString().split('T')[0]
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
                      setInvoiceFormData({ 
                        ...invoiceFormData, 
                        due_date: newValue.toISOString().split('T')[0]
                      });
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
                      setInvoiceFormData({ 
                        ...invoiceFormData, 
                        payment_terms: e.target.value
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
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setInvoiceDialogOpen(false);
            resetInvoiceForm();
          }}>
            {t('finance.cancel')}
          </Button>
          <Button onClick={handleCreateInvoice} variant="contained">
            {t('finance.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Payment Dialog */}
      <Dialog open={paymentDialogOpen} onClose={() => setPaymentDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('finance.createPayment')}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>{t('finance.invoice')}</InputLabel>
                <Select
                  value={paymentFormData.invoice_id}
                  label={t('finance.invoice')}
                  onChange={(e) => setPaymentFormData({ ...paymentFormData, invoice_id: e.target.value })}
                >
                  {invoices.map((invoice) => (
                    <MenuItem key={invoice.id} value={invoice.id.toString()}>
                      {invoice.invoice_number} - {invoice.item_code}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <DatePicker
                label={t('finance.paymentDate')}
                value={new Date(paymentFormData.payment_date)}
                onChange={(newValue) => {
                  if (newValue) {
                    setPaymentFormData({ 
                      ...paymentFormData, 
                      payment_date: newValue.toISOString().split('T')[0]
                    });
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
                  onChange={(e) => setPaymentFormData({ ...paymentFormData, payment_method: e.target.value })}
                >
                  <MenuItem value="cash">{t('finance.cash')}</MenuItem>
                  <MenuItem value="bank_transfer">{t('finance.bankTransfer')}</MenuItem>
                  <MenuItem value="check">{t('finance.check')}</MenuItem>
                  <MenuItem value="credit_card">{t('finance.creditCard')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('finance.referenceNumber')}
                value={paymentFormData.reference_number}
                onChange={(e) => setPaymentFormData({ ...paymentFormData, reference_number: e.target.value })}
              />
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
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setPaymentDialogOpen(false);
            resetPaymentForm();
          }}>
            {t('finance.cancel')}
          </Button>
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
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">{t('finance.invoiceNumber')}</Typography>
                <Typography variant="body1">{selectedInvoice.invoice_number}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">{t('finance.itemCode')}</Typography>
                <Typography variant="body1">{selectedInvoice.item_code}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">{t('finance.amount')}</Typography>
                <Typography variant="body1">
                  {selectedInvoice.invoice_amount.toLocaleString()} {selectedInvoice.currency}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">{t('finance.invoiceDate')}</Typography>
                <Typography variant="body1">{selectedInvoice.invoice_date}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">{t('finance.dueDate')}</Typography>
                <Typography variant="body1">{selectedInvoice.due_date}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">{t('finance.status')}</Typography>
                <Chip 
                  label={selectedInvoice.status} 
                  color={selectedInvoice.status === 'paid' ? 'success' : 'default'}
                  size="small"
                />
              </Grid>
              {selectedInvoice.notes && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">{t('finance.notes')}</Typography>
                  <Typography variant="body1">{selectedInvoice.notes}</Typography>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewInvoiceDialogOpen(false)}>
            {t('finance.close')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmDialogOpen} onClose={() => setDeleteConfirmDialogOpen(false)}>
        <DialogTitle>{t('finance.confirmDelete')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('finance.deleteInvoiceConfirm')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmDialogOpen(false)}>
            {t('finance.cancel')}
          </Button>
          <Button onClick={confirmDeleteInvoice} color="error" variant="contained">
            {t('finance.delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InvoicePaymentManagement;
