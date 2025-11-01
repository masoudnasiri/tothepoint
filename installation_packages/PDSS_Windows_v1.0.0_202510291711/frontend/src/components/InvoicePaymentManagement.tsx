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
  Autocomplete,
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
import { decisionsAPI, supplierPaymentsAPI } from '../services/api.ts';
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

interface SupplierPaymentData {
  id: number;
  decision_id: number;
  supplier_name: string;
  item_code: string;
  project_id: number;
  project_name: string;
  payment_date: string;
  payment_amount: number;
  currency: string;
  payment_method: string;
  reference_number: string;
  notes: string;
  status: string;
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
  const [unpaidInvoices, setUnpaidInvoices] = useState<InvoiceData[]>([]); // For payment creation dropdown
  const [payments, setPayments] = useState<PaymentData[]>([]);
  const [supplierPayments, setSupplierPayments] = useState<SupplierPaymentData[]>([]);
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
  
  // Supplier Payment dialog
  const [supplierPaymentDialogOpen, setSupplierPaymentDialogOpen] = useState(false);
  const [supplierPaymentFormData, setSupplierPaymentFormData] = useState({
    decision_id: '',
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
      const [invoicesResponse, paymentsResponse, supplierPaymentsResponse] = await Promise.all([
        invoicePaymentAPI.listInvoices({
          search: searchTerm,
          status: statusFilter,
          project_id: projectFilter ? parseInt(projectFilter) : undefined,
        }),
        invoicePaymentAPI.listPayments({
          search: searchTerm,
          project_id: projectFilter ? parseInt(projectFilter) : undefined,
        }),
        supplierPaymentsAPI.list({
          project_id: projectFilter ? parseInt(projectFilter) : undefined,
        }),
      ]);
      
      const allInvoices = invoicesResponse.data || [];
      const allPayments = paymentsResponse.data || [];
      const allSupplierPayments = supplierPaymentsResponse.data || [];
      
      // Process supplier payments to match the expected format
      const processedSupplierPayments: SupplierPaymentData[] = allSupplierPayments.map((payment: any) => ({
        id: payment.id,
        decision_id: payment.decision_id,
        supplier_name: payment.supplier_name,
        item_code: payment.item_code,
        project_id: payment.project_id,
        project_name: payment.project_name || `Project ${payment.project_id}`,
        payment_date: payment.payment_date,
        payment_amount: payment.payment_amount,
        currency: payment.currency,
        payment_method: payment.payment_method,
        reference_number: payment.reference_number,
        notes: payment.notes,
        status: payment.status,
      }));
      
      // Process invoices to add remaining amount and completely paid flag
      const processedInvoices = allInvoices.map(invoice => {
        const totalPayments = allPayments
          .filter(payment => payment.invoice_id === invoice.id)
          .reduce((sum, payment) => sum + payment.payment_amount, 0);
        
        const remainingAmount = invoice.invoice_amount - totalPayments;
        const isCompletelyPaid = remainingAmount <= 0;
        
        // Debug logging for status calculation
        console.log(`Invoice ${invoice.invoice_number}:`, {
          invoice_amount: invoice.invoice_amount,
          total_payments: totalPayments,
          remaining_amount: remainingAmount,
          is_completely_paid: isCompletelyPaid,
          status: remainingAmount === 0 ? 'COMPLETELY PAID' : 
                  remainingAmount === invoice.invoice_amount ? 'UNPAID' : 'PARTIALLY PAID'
        });
        
        return {
          ...invoice,
          remaining_amount: Math.max(0, remainingAmount),
          is_completely_paid: isCompletelyPaid
        };
      });
      
      // Keep all invoices for the table display
      // Filter out completely paid invoices only for payment creation dropdown
      const unpaidInvoices = processedInvoices.filter(invoice => !invoice.is_completely_paid);
      
      setInvoices(processedInvoices); // Show ALL invoices in the table
      setUnpaidInvoices(unpaidInvoices); // Filtered invoices for payment creation dropdown
      setPayments(allPayments);
      setSupplierPayments(processedSupplierPayments);
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
      
      // SIMPLE LOGIC: Filter out items that have final invoice checked
      const availableDecisions = allDecisions.filter(decision => {
        // If is_final_invoice is true, don't show the item
        return decision.is_final_invoice !== true;
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

  const handleCreateSupplierPayment = async () => {
    try {
      const selectedDecision = decisions.find(d => d.id.toString() === supplierPaymentFormData.decision_id);
      if (!selectedDecision) {
        setError('Selected decision not found');
        return;
      }

      const response = await supplierPaymentsAPI.create({
        decision_id: parseInt(supplierPaymentFormData.decision_id),
        supplier_name: selectedDecision.supplier_name || 'Unknown Supplier',
        item_code: selectedDecision.item_code,
        project_id: selectedDecision.project_id,
        payment_date: supplierPaymentFormData.payment_date,
        payment_amount: supplierPaymentFormData.payment_amount,
        currency: supplierPaymentFormData.currency,
        payment_method: supplierPaymentFormData.payment_method,
        reference_number: supplierPaymentFormData.reference_number,
        notes: supplierPaymentFormData.notes,
        status: 'completed',
      });

      // Add the new payment to the list
      const newPayment: SupplierPaymentData = {
        id: response.data.id,
        decision_id: response.data.decision_id,
        supplier_name: response.data.supplier_name,
        item_code: response.data.item_code,
        project_id: response.data.project_id,
        project_name: response.data.project_name || `Project ${response.data.project_id}`,
        payment_date: response.data.payment_date,
        payment_amount: response.data.payment_amount,
        currency: response.data.currency,
        payment_method: response.data.payment_method,
        reference_number: response.data.reference_number,
        notes: response.data.notes,
        status: response.data.status,
      };
      
      setSupplierPayments(prev => [...prev, newPayment]);
      setSuccess('Supplier payment created successfully');
      setSupplierPaymentDialogOpen(false);
      resetSupplierPaymentForm();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create supplier payment');
    }
  };

  const resetSupplierPaymentForm = () => {
    setSupplierPaymentFormData({
      decision_id: '',
      payment_date: new Date().toISOString().split('T')[0],
      payment_amount: 0,
      currency: 'IRR',
      payment_method: 'bank_transfer',
      reference_number: '',
      notes: '',
    });
  };

  const handleDeleteSupplierPayment = async (paymentId: number) => {
    try {
      await supplierPaymentsAPI.delete(paymentId);
      setSupplierPayments(prev => prev.filter(payment => payment.id !== paymentId));
      setSuccess('Supplier payment deleted successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete supplier payment');
    }
  };

  const handleDeletePayment = async (paymentId: number) => {
    try {
      await invoicePaymentAPI.deletePayment(paymentId);
      setPayments(prev => prev.filter(payment => payment.id !== paymentId));
      setSuccess('Payment deleted successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete payment');
    }
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
            label={t('finance.paymentsIn')} 
            iconPosition="start"
          />
          <Tab 
            icon={<AttachMoneyIcon />} 
            label={t('finance.paymentsOut')} 
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
                          {invoice.remaining_amount.toLocaleString()} {invoice.currency}
                          <Typography variant="caption" display="block" color="text.secondary">
                            {t('finance.remainingAmount')}
                          </Typography>
                        </TableCell>
                        <TableCell>{invoice.invoice_date}</TableCell>
                        <TableCell>{invoice.due_date}</TableCell>
                        <TableCell>
                          {(() => {
                            const status = invoice.remaining_amount === 0 ? 'COMPLETELY PAID' :
                                          invoice.remaining_amount === invoice.invoice_amount ? 'UNPAID' : 
                                          'PARTIALLY PAID';
                            console.log(`Status for ${invoice.invoice_number}:`, {
                              remaining_amount: invoice.remaining_amount,
                              invoice_amount: invoice.invoice_amount,
                              comparison: invoice.remaining_amount === invoice.invoice_amount,
                              status: status
                            });
                            return (
                              <Chip 
                                label={
                                  invoice.remaining_amount === 0 ? t('finance.completelyPaid') :
                                  invoice.remaining_amount === invoice.invoice_amount ? t('finance.unpaid') : 
                                  t('finance.partiallyPaid')
                                }
                                color={
                                  invoice.remaining_amount === 0 ? 'success' :
                                  invoice.remaining_amount === invoice.invoice_amount ? 'error' : 
                                  'warning'
                                }
                                size="small"
                              />
                            );
                          })()}
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

        {/* Payments In Tab */}
        {tabValue === 1 && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">{t('finance.paymentsIn')}</Typography>
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
                          <IconButton 
                            onClick={() => handleDeletePayment(payment.id)}
                            color="error"
                          >
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

        {/* Payments Out Tab */}
        {tabValue === 2 && (
          <Box sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">{t('finance.paymentsOut')}</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  resetSupplierPaymentForm();
                  setSupplierPaymentDialogOpen(true);
                }}
              >
                {t('finance.createSupplierPayment')}
              </Button>
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('finance.paymentsOutSubtitle')}
            </Typography>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('finance.supplier')}</TableCell>
                      <TableCell>{t('finance.itemCode')}</TableCell>
                      <TableCell>{t('finance.project')}</TableCell>
                      <TableCell>{t('finance.amount')}</TableCell>
                      <TableCell>{t('finance.currency')}</TableCell>
                      <TableCell>{t('finance.paymentDate')}</TableCell>
                      <TableCell>{t('finance.paymentMethod')}</TableCell>
                      <TableCell>{t('finance.status')}</TableCell>
                      <TableCell>{t('finance.actions')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {supplierPayments.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={9} align="center">
                          <Typography variant="body2" color="text.secondary">
                            {t('finance.noSupplierPayments')}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      supplierPayments.map((payment) => (
                        <TableRow key={payment.id}>
                          <TableCell>{payment.supplier_name}</TableCell>
                          <TableCell>{payment.item_code}</TableCell>
                          <TableCell>{payment.project_name}</TableCell>
                          <TableCell>{payment.payment_amount.toLocaleString()}</TableCell>
                          <TableCell>{payment.currency}</TableCell>
                          <TableCell>{new Date(payment.payment_date).toLocaleDateString()}</TableCell>
                          <TableCell>{payment.payment_method}</TableCell>
                          <TableCell>
                            <Chip 
                              label={payment.status} 
                              color={payment.status === 'completed' ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <IconButton onClick={() => console.log('View supplier payment', payment)}>
                              <ViewIcon />
                            </IconButton>
                            <IconButton 
                              onClick={() => handleDeleteSupplierPayment(payment.id)}
                              color="error"
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
                <Autocomplete
                  options={decisions || []}
                  getOptionLabel={(option) => `${option.item_code} - (Project ${option.project_id})`}
                  value={decisions?.find(d => d.id.toString() === invoiceFormData.decision_id) || null}
                  onChange={(event, selectedDecision) => {
                    if (selectedDecision) {
                      setInvoiceFormData({ 
                        ...invoiceFormData, 
                        decision_id: selectedDecision.id.toString(),
                        invoice_amount: selectedDecision.final_cost || 0,
                        currency: selectedDecision.final_cost_currency || 'IRR',
                        notes: selectedDecision.notes || ''
                      });
                    } else {
                      setInvoiceFormData({ 
                        ...invoiceFormData, 
                        decision_id: '',
                        invoice_amount: 0,
                        currency: 'IRR',
                        notes: ''
                      });
                    }
                  }}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('finance.decisionId')}
                      required
                      placeholder={t('finance.searchDecision')}
                    />
                  )}
                  noOptionsText={t('finance.noAvailableDecisions')}
                  isOptionEqualToValue={(option, value) => option.id === value.id}
                />
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
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <Autocomplete
                options={unpaidInvoices}
                getOptionLabel={(option) => `${option.invoice_number} - ${option.item_code}`}
                value={unpaidInvoices.find(inv => inv.id.toString() === paymentFormData.invoice_id) || null}
                onChange={(event, selectedInvoice) => {
                  if (selectedInvoice) {
                    setPaymentFormData({ 
                      ...paymentFormData, 
                      invoice_id: selectedInvoice.id.toString(),
                      payment_amount: selectedInvoice.remaining_amount,
                      currency: selectedInvoice.currency
                    });
                  } else {
                    setPaymentFormData({ 
                      ...paymentFormData, 
                      invoice_id: '',
                      payment_amount: 0,
                      currency: 'IRR'
                    });
                  }
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={t('finance.invoice')}
                    required
                    placeholder={t('finance.searchInvoice')}
                  />
                )}
                noOptionsText={t('finance.noUnpaidInvoices')}
                isOptionEqualToValue={(option, value) => option.id === value.id}
              />
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
                InputProps={{
                  readOnly: true,
                }}
                helperText={t('finance.paymentAmountFromInvoice')}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('finance.currency')}
                value={paymentFormData.currency}
                InputProps={{
                  readOnly: true,
                }}
                helperText={t('finance.currencyFromInvoice')}
              />
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
          </LocalizationProvider>
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

      {/* Create Supplier Payment Dialog */}
      <Dialog open={supplierPaymentDialogOpen} onClose={() => setSupplierPaymentDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('finance.createSupplierPayment')}</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <Autocomplete
                  options={decisions || []}
                  getOptionLabel={(option) => `${option.item_code} - (Project ${option.project_id})`}
                  value={decisions?.find(d => d.id.toString() === supplierPaymentFormData.decision_id) || null}
                  onChange={(event, selectedDecision) => {
                    if (selectedDecision) {
                      setSupplierPaymentFormData({ 
                        ...supplierPaymentFormData, 
                        decision_id: selectedDecision.id.toString(),
                        payment_amount: selectedDecision.final_cost || 0,
                        currency: selectedDecision.final_cost_currency || 'IRR',
                        notes: selectedDecision.notes || ''
                      });
                    } else {
                      setSupplierPaymentFormData({ 
                        ...supplierPaymentFormData, 
                        decision_id: '',
                        payment_amount: 0,
                        currency: 'IRR',
                        notes: ''
                      });
                    }
                  }}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('finance.decisionId')}
                      required
                      placeholder={t('finance.searchDecision')}
                    />
                  )}
                  noOptionsText={t('finance.noAvailableDecisions')}
                  isOptionEqualToValue={(option, value) => option.id === value.id}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <DatePicker
                  label={t('finance.paymentDate')}
                  value={new Date(supplierPaymentFormData.payment_date)}
                  onChange={(newValue) => {
                    if (newValue) {
                      setSupplierPaymentFormData({ 
                        ...supplierPaymentFormData, 
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
                  value={supplierPaymentFormData.payment_amount}
                  onChange={(e) => setSupplierPaymentFormData({ ...supplierPaymentFormData, payment_amount: parseFloat(e.target.value) || 0 })}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label={t('finance.currency')}
                  value={supplierPaymentFormData.currency}
                  InputProps={{
                    readOnly: true,
                  }}
                  helperText={t('finance.currencyFromDecision')}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('finance.paymentMethod')}</InputLabel>
                  <Select
                    value={supplierPaymentFormData.payment_method}
                    label={t('finance.paymentMethod')}
                    onChange={(e) => setSupplierPaymentFormData({ ...supplierPaymentFormData, payment_method: e.target.value })}
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
                  value={supplierPaymentFormData.reference_number}
                  onChange={(e) => setSupplierPaymentFormData({ ...supplierPaymentFormData, reference_number: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={t('finance.notes')}
                  multiline
                  rows={3}
                  value={supplierPaymentFormData.notes}
                  onChange={(e) => setSupplierPaymentFormData({ ...supplierPaymentFormData, notes: e.target.value })}
                />
              </Grid>
            </Grid>
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setSupplierPaymentDialogOpen(false);
            resetSupplierPaymentForm();
          }}>
            {t('finance.cancel')}
          </Button>
          <Button onClick={handleCreateSupplierPayment} variant="contained">
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
