/* eslint-disable */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Chip,
  Paper,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Checkbox,
  Toolbar,
  Pagination,
  InputAdornment,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Undo as UndoIcon,
  Info as InfoIcon,
  Assignment as AssignmentIcon,
  Lock as LockIcon,
  AttachMoney as AttachMoneyIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { useAuth } from '../contexts/AuthContext.tsx';
import { decisionsAPI } from '../services/api.ts';
import { useNavigate } from 'react-router-dom';
import { ProjectFilter } from '../components/ProjectFilter.tsx';

interface FinalizedDecision {
  id: number;
  item_code: string;
  project_id: number;
  procurement_option_id: number;
  purchase_date: string;
  delivery_date: string;
  quantity: number;
  final_cost: number;
  status: string;
  // Forecast invoice fields
  forecast_invoice_timing_type: string;
  forecast_invoice_issue_date: string | null;
  forecast_invoice_days_after_delivery: number | null;
  forecast_invoice_amount: number | null;
  // Actual invoice fields
  actual_invoice_issue_date: string | null;
  actual_invoice_amount: number | null;
  actual_invoice_received_date: string | null;
  invoice_entered_by_id: number | null;
  invoice_entered_at: string | null;
  // Legacy fields (for backward compatibility)
  invoice_timing_type: string;
  invoice_issue_date: string | null;
  invoice_days_after_delivery: number | null;
  finalized_at: string | null;
  finalized_by_id: number | null;
  decision_date: string;
  notes: string | null;
}

export const FinalizedDecisionsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [decisions, setDecisions] = useState<FinalizedDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [revertDialogOpen, setRevertDialogOpen] = useState(false);
  const [invoiceDialogOpen, setInvoiceDialogOpen] = useState(false);
  const [selectedDecision, setSelectedDecision] = useState<FinalizedDecision | null>(null);
  const [revertNotes, setRevertNotes] = useState('');
  const [invoiceTimingType, setInvoiceTimingType] = useState<string>('RELATIVE');
  const [invoiceDate, setInvoiceDate] = useState<Date | null>(null);
  const [invoiceDays, setInvoiceDays] = useState<number>(30);
  const [actualInvoiceDialogOpen, setActualInvoiceDialogOpen] = useState(false);
  const [actualInvoiceDate, setActualInvoiceDate] = useState<Date | null>(null);
  const [actualInvoiceAmount, setActualInvoiceAmount] = useState<number>(0);
  const [actualReceivedDate, setActualReceivedDate] = useState<Date | null>(null);
  const [actualInvoiceNotes, setActualInvoiceNotes] = useState<string>('');
  const [actualPaymentDialogOpen, setActualPaymentDialogOpen] = useState(false);
  const [actualPaymentAmount, setActualPaymentAmount] = useState<number>(0);
  const [actualPaymentDate, setActualPaymentDate] = useState<Date | null>(null);
  const [actualPaymentInstallments, setActualPaymentInstallments] = useState<Array<{ date: string; amount: number }>>([]);
  const [actualPaymentNotes, setActualPaymentNotes] = useState<string>('');
  const [selectedDecisionIds, setSelectedDecisionIds] = useState<number[]>([]);
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
  const [statusFilters, setStatusFilters] = useState<string[]>([]);
  
  // New state for search and pagination
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [summaryStats, setSummaryStats] = useState<any>(null);
  const ITEMS_PER_PAGE = 50;

  // ✅ Prevent PM users from accessing this page
  useEffect(() => {
    if (user && user.role === 'pm') {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  // Debounced search effect
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (currentPage !== 1) {
        setCurrentPage(1); // Reset to first page when searching
      } else {
        fetchDecisions();
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  useEffect(() => {
    fetchDecisions();
  }, [selectedProjects, currentPage]); // Re-fetch when filters or page changes

  const fetchDecisions = async () => {
    try {
      setLoading(true);
      const skip = (currentPage - 1) * ITEMS_PER_PAGE;
      const params: any = {
        skip,
        limit: ITEMS_PER_PAGE,
        search: searchTerm || undefined,
      };
      
      if (selectedProjects.length > 0) {
        // Filter by selected projects
        params.project_id = selectedProjects[0]; // API currently supports single project
        // TODO: Update API to support multiple projects
      }
      
      // Fetch decisions, count, and summary in parallel
      const [decisionsResponse, countResponse, summaryResponse] = await Promise.all([
        decisionsAPI.list(params),
        decisionsAPI.count(params),
        decisionsAPI.summary(params)
      ]);
      
      let filteredDecisions = decisionsResponse.data;
      if (selectedProjects.length > 1) {
        filteredDecisions = decisionsResponse.data.filter((d: any) => 
          selectedProjects.includes(d.project_id)
        );
      }
      
      setDecisions(filteredDecisions);
      setTotalCount(countResponse.data.count);
      setTotalPages(Math.ceil(countResponse.data.count / ITEMS_PER_PAGE));
      setSummaryStats(summaryResponse.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load decisions');
    } finally {
      setLoading(false);
    }
  };

  const handleRevert = async () => {
    if (!selectedDecision) return;
    
    try {
      await decisionsAPI.updateStatus(selectedDecision.id, {
        status: 'REVERTED',
        notes: revertNotes
      });
      setRevertDialogOpen(false);
      setSelectedDecision(null);
      setRevertNotes('');
      setSelectedDecisionIds([]);
      fetchDecisions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to revert decision');
    }
  };

  // Multi-select handlers
  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const lockedIds = decisions.filter(d => d.status === 'LOCKED').map(d => d.id);
      setSelectedDecisionIds(lockedIds);
    } else {
      setSelectedDecisionIds([]);
    }
  };

  const handleSelectOne = (id: number) => {
    const selectedIndex = selectedDecisionIds.indexOf(id);
    let newSelected: number[] = [];

    if (selectedIndex === -1) {
      newSelected = [...selectedDecisionIds, id];
    } else {
      newSelected = selectedDecisionIds.filter(sid => sid !== id);
    }

    setSelectedDecisionIds(newSelected);
  };

  const handleBulkRevert = async () => {
    if (selectedDecisionIds.length === 0) {
      setError('No items selected');
      return;
    }

    if (!window.confirm(`Revert ${selectedDecisionIds.length} selected decision(s)? This action will unlock them and cancel related cashflow events.`)) {
      return;
    }

    try {
      // Revert each selected decision
      for (const id of selectedDecisionIds) {
        await decisionsAPI.updateStatus(id, {
          status: 'REVERTED',
          notes: revertNotes || 'Bulk revert operation'
        });
      }
      
      setSuccess(`Successfully reverted ${selectedDecisionIds.length} decision(s)`);
      setSelectedDecisionIds([]);
      setRevertNotes('');
      fetchDecisions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to revert some decisions');
    }
  };

  const openRevertDialog = (decision: FinalizedDecision) => {
    setSelectedDecision(decision);
    setRevertDialogOpen(true);
  };

  const openInvoiceDialog = (decision: FinalizedDecision) => {
    setSelectedDecision(decision);
    setInvoiceTimingType(decision.invoice_timing_type || 'RELATIVE');
    setInvoiceDate(decision.invoice_issue_date ? new Date(decision.invoice_issue_date) : null);
    setInvoiceDays(decision.invoice_days_after_delivery || 30);
    setInvoiceDialogOpen(true);
  };

  const openActualInvoiceDialog = (decision: FinalizedDecision) => {
    setSelectedDecision(decision);
    setActualInvoiceDate(decision.actual_invoice_issue_date ? new Date(decision.actual_invoice_issue_date) : new Date());
    setActualInvoiceAmount(decision.actual_invoice_amount || decision.final_cost);
    setActualReceivedDate(decision.actual_invoice_received_date ? new Date(decision.actual_invoice_received_date) : null);
    setActualInvoiceNotes('');
    setActualInvoiceDialogOpen(true);
  };

  const openActualPaymentDialog = (decision: FinalizedDecision) => {
    setSelectedDecision(decision);
    setActualPaymentDate(new Date());
    setActualPaymentAmount(decision.final_cost);
    
    // Initialize installments based on payment terms
    const paymentTerms = decision.payment_terms as any;
    if (paymentTerms && paymentTerms.type === 'installments' && paymentTerms.schedule) {
      // Create installments array from payment terms
      const installments = paymentTerms.schedule.map((inst: any) => ({
        date: new Date(Date.now() + inst.due_offset * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        amount: Math.round((decision.final_cost * inst.percent / 100) * 100) / 100
      }));
      setActualPaymentInstallments(installments);
    } else {
      setActualPaymentInstallments([]);
    }
    
    setActualPaymentNotes('');
    setActualPaymentDialogOpen(true);
  };

  const handleFinalizeSelected = async () => {
    const proposedDecisions = decisions.filter(d => d.status === 'PROPOSED');
    
    if (proposedDecisions.length === 0) {
      setError('No PROPOSED decisions to finalize');
      return;
    }

    if (!window.confirm(`Finalize ${proposedDecisions.length} PROPOSED decision(s)? This will lock them and create forecast cashflow events.`)) {
      return;
    }

    try {
      const decisionIds = proposedDecisions.map(d => d.id);
      await decisionsAPI.finalize({ decision_ids: decisionIds });
      setSuccess(`Successfully finalized ${proposedDecisions.length} decision(s) and created forecast cashflow events`);
      fetchDecisions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to finalize decisions');
    }
  };

  const handleSubmitActualInvoice = async () => {
    if (!selectedDecision || !actualInvoiceDate) return;
    
    try {
      await decisionsAPI.enterActualInvoice(selectedDecision.id, {
        actual_invoice_issue_date: actualInvoiceDate.toISOString().split('T')[0],
        actual_invoice_amount: actualInvoiceAmount,
        actual_invoice_received_date: actualReceivedDate?.toISOString().split('T')[0],
        notes: actualInvoiceNotes || undefined
      });
      setActualInvoiceDialogOpen(false);
      setSelectedDecision(null);
      setSuccess('Actual invoice data entered successfully');
      fetchDecisions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to enter actual invoice data');
    }
  };

  const handleSubmitActualPayment = async () => {
    if (!selectedDecision) return;
    
    // Validate based on payment type
    if (actualPaymentInstallments.length > 0) {
      // Installment payment - check all installments are valid
      if (actualPaymentInstallments.some(inst => !inst.date || inst.amount <= 0)) {
        setError('All installments must have a date and amount greater than 0');
        return;
      }
    } else {
      // Cash payment - check single payment is valid
      if (!actualPaymentDate || actualPaymentAmount <= 0) {
        setError('Payment date and amount are required');
        return;
      }
    }
    
    try {
      // Calculate total amount
      const totalAmount = actualPaymentInstallments.length > 0
        ? actualPaymentInstallments.reduce((sum, inst) => sum + inst.amount, 0)
        : actualPaymentAmount;
      
      const paymentDate = actualPaymentInstallments.length > 0
        ? actualPaymentInstallments[0].date
        : actualPaymentDate!.toISOString().split('T')[0];
      
      await decisionsAPI.enterActualPayment(selectedDecision.id, {
        actual_payment_amount: totalAmount,
        actual_payment_date: paymentDate,
        actual_payment_installments: actualPaymentInstallments.length > 0 ? actualPaymentInstallments : undefined,
        notes: actualPaymentNotes || undefined
      });
      
      setActualPaymentDialogOpen(false);
      setSelectedDecision(null);
      setSuccess('✅ Actual payment data entered successfully! Cashflow events created.');
      fetchDecisions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to enter actual payment data');
    }
  };

  const handleUpdateInvoice = async () => {
    if (!selectedDecision) return;
    
    try {
      const updateData: any = {
        invoice_timing_type: invoiceTimingType,
      };
      
      if (invoiceTimingType === 'ABSOLUTE') {
        updateData.invoice_issue_date = invoiceDate?.toISOString().split('T')[0];
        updateData.invoice_days_after_delivery = null;
      } else {
        updateData.invoice_days_after_delivery = invoiceDays;
        updateData.invoice_issue_date = null;
      }
      
      await decisionsAPI.update(selectedDecision.id, updateData);
      setInvoiceDialogOpen(false);
      setSelectedDecision(null);
      setSuccess('Invoice timing updated successfully');
      fetchDecisions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update invoice timing');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status: string): "success" | "warning" | "error" | "default" => {
    switch (status) {
      case 'LOCKED': return 'success';
      case 'PROPOSED': return 'warning';
      case 'REVERTED': return 'error';
      default: return 'default';
    }
  };

  const getInvoiceStatus = (decision: FinalizedDecision) => {
    if (decision.actual_invoice_amount && decision.actual_invoice_amount > 0) {
      return { label: 'Invoiced', color: 'success' as const };
    }
    return { label: 'Not Invoiced', color: 'default' as const };
  };

  const getPaymentStatus = (decision: FinalizedDecision) => {
    if (!decision.actual_payment_amount || decision.actual_payment_amount === 0) {
      return { label: 'Not Paid', color: 'error' as const, percent: 0 };
    }
    
    const expectedCost = decision.final_cost;
    const actualPaid = decision.actual_payment_amount;
    const percent = Math.round((actualPaid / expectedCost) * 100);
    
    if (percent >= 100) {
      return { label: 'Fully Paid', color: 'success' as const, percent: 100 };
    } else if (percent > 0) {
      return { label: `Partially Paid (${percent}%)`, color: 'warning' as const, percent };
    } else {
      return { label: 'Not Paid', color: 'error' as const, percent: 0 };
    }
  };

  const getInvoiceDisplay = (decision: FinalizedDecision) => {
    if (decision.invoice_timing_type === 'ABSOLUTE') {
      return `Date: ${formatDate(decision.invoice_issue_date)}`;
    } else if (decision.invoice_timing_type === 'RELATIVE') {
      return `+${decision.invoice_days_after_delivery || 0} days after delivery`;
    }
    return '-';
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
        <Box>
          <Typography variant="h4">Finalized Decisions</Typography>
          <Typography variant="subtitle2" color="textSecondary">
            View and manage all procurement decisions across their lifecycle
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          {(user?.role === 'pm' || user?.role === 'admin') && decisions.filter(d => d.status === 'PROPOSED').length > 0 && (
            <Button
              variant="contained"
              color="success"
              onClick={handleFinalizeSelected}
              startIcon={<LockIcon />}
            >
              Finalize All PROPOSED ({decisions.filter(d => d.status === 'PROPOSED').length})
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchDecisions}
          >
            Refresh
          </Button>
        </Box>
      </Box>

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

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <ProjectFilter
              selectedProjects={selectedProjects}
              onChange={setSelectedProjects}
              label="Filter by Project(s)"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Search Items & Suppliers"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by item code, supplier name, or notes..."
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
              <InputLabel>Filter by Invoice/Payment Status</InputLabel>
              <Select
                multiple
                value={statusFilters}
                onChange={(e) => setStatusFilters(typeof e.target.value === 'string' ? [e.target.value] : e.target.value)}
                label="Filter by Invoice/Payment Status"
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                <MenuItem value="not-invoiced">Not Invoiced</MenuItem>
                <MenuItem value="invoiced">Invoiced</MenuItem>
                <MenuItem value="not-paid">Not Paid</MenuItem>
                <MenuItem value="partially-paid">Partially Paid</MenuItem>
                <MenuItem value="fully-paid">Fully Paid</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Summary
        </Typography>
        <Grid container spacing={1}>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`Total: ${totalCount} (Page ${currentPage} of ${totalPages})`}
              color="primary"
              variant="outlined"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`Locked: ${summaryStats?.locked || 0}`}
              color="success"
              variant="outlined"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`Proposed: ${summaryStats?.proposed || 0}`}
              color="warning"
              variant="outlined"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`Reverted: ${summaryStats?.reverted || 0}`}
              color="error"
              variant="outlined"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`Invoiced: ${summaryStats?.invoiced || 0}`}
              color="success"
              variant="filled"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`Not Invoiced: ${summaryStats?.not_invoiced || 0}`}
              color="default"
              variant="filled"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`Fully Paid: ${summaryStats?.fully_paid || 0}`}
              color="success"
              variant="filled"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`Not Paid: ${summaryStats?.not_paid || 0}`}
              color="error"
              variant="filled"
              sx={{ width: '100%' }}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Bulk Actions Toolbar */}
      {selectedDecisionIds.length > 0 && (
        <Paper sx={{ mb: 2 }}>
          <Toolbar sx={{ bgcolor: '#e3f2fd', borderRadius: 1 }}>
            <Typography sx={{ flex: '1 1 100%' }} color="inherit" variant="subtitle1">
              {selectedDecisionIds.length} item(s) selected
            </Typography>
            <Button
              variant="contained"
              color="error"
              startIcon={<UndoIcon />}
              onClick={handleBulkRevert}
            >
              Revert Selected
            </Button>
          </Toolbar>
        </Paper>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={
                    selectedDecisionIds.length > 0 &&
                    selectedDecisionIds.length < decisions.filter(d => d.status === 'LOCKED').length
                  }
                  checked={
                    decisions.filter(d => d.status === 'LOCKED').length > 0 &&
                    selectedDecisionIds.length === decisions.filter(d => d.status === 'LOCKED').length
                  }
                  onChange={handleSelectAll}
                  disabled={decisions.filter(d => d.status === 'LOCKED').length === 0}
                />
              </TableCell>
              <TableCell>ID</TableCell>
              <TableCell>Item Code</TableCell>
              <TableCell>Purchase Date</TableCell>
              <TableCell>Delivery Date</TableCell>
              <TableCell align="right">Cost</TableCell>
              <TableCell>Invoice Status</TableCell>
              <TableCell>Payment Status</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Finalized</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {decisions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={11} align="center">
                  <Typography variant="body2" color="textSecondary" sx={{ py: 4 }}>
                    No finalized decisions found. Run optimization and save decisions to see them here.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              decisions
                .filter((decision) => {
                  // Apply status filters
                  if (statusFilters.length === 0) return true;
                  
                  const invoiceStatus = getInvoiceStatus(decision);
                  const paymentStatus = getPaymentStatus(decision);
                  
                  return statusFilters.some(filter => {
                    if (filter === 'not-invoiced') return invoiceStatus.label === 'Not Invoiced';
                    if (filter === 'invoiced') return invoiceStatus.label === 'Invoiced';
                    if (filter === 'not-paid') return paymentStatus.label === 'Not Paid';
                    if (filter === 'partially-paid') return paymentStatus.label.includes('Partially Paid');
                    if (filter === 'fully-paid') return paymentStatus.label === 'Fully Paid';
                    return false;
                  });
                })
                .map((decision) => {
                const isSelected = selectedDecisionIds.indexOf(decision.id) !== -1;
                const isLocked = decision.status === 'LOCKED';
                
                return (
                <TableRow 
                  key={decision.id}
                  hover
                  selected={isSelected}
                  sx={{ bgcolor: isSelected ? '#e3f2fd' : 'inherit' }}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      onChange={() => handleSelectOne(decision.id)}
                      disabled={!isLocked}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{decision.id}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {decision.item_code}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDate(decision.purchase_date)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDate(decision.delivery_date)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" fontWeight="medium">
                      {formatCurrency(decision.final_cost)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getInvoiceStatus(decision).label}
                      color={getInvoiceStatus(decision).color}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getPaymentStatus(decision).label}
                      color={getPaymentStatus(decision).color}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={decision.status}
                      color={getStatusColor(decision.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {formatDate(decision.finalized_at)}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    {decision.status === 'PROPOSED' && (user?.role === 'pm' || user?.role === 'admin') && (
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => openInvoiceDialog(decision)}
                        title="Configure Invoice Timing"
                      >
                        <AssignmentIcon />
                      </IconButton>
                    )}
                    {decision.status === 'PROPOSED' && (user?.role === 'finance' || user?.role === 'admin') && (
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={async () => {
                          if (window.confirm('Finalize this decision? This will lock it and create forecast cashflow events.')) {
                            try {
                              await decisionsAPI.finalize({ decision_ids: [decision.id] });
                              setSuccess('Decision finalized successfully');
                              fetchDecisions();
                            } catch (err: any) {
                              setError(err.response?.data?.detail || 'Failed to finalize decision');
                            }
                          }
                        }}
                        title="Finalize Decision (Lock)"
                      >
                        <LockIcon />
                      </IconButton>
                    )}
                    {decision.status === 'LOCKED' && (user?.role === 'finance' || user?.role === 'admin') && (
                      <>
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => openActualInvoiceDialog(decision)}
                          title="Enter Actual Invoice Data (Revenue)"
                        >
                          <AssignmentIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="warning"
                          onClick={() => openActualPaymentDialog(decision)}
                          title="Enter Actual Payment Data (Expense)"
                        >
                          <AttachMoneyIcon />
                        </IconButton>
                      </>
                    )}
                    {decision.status === 'LOCKED' && (user?.role === 'pm' || user?.role === 'admin') && (
                      <>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => openRevertDialog(decision)}
                          title="Revert Decision"
                        >
                          <UndoIcon />
                        </IconButton>
                        {decision.notes && (
                          <IconButton
                            size="small"
                            title={decision.notes}
                          >
                            <InfoIcon />
                          </IconButton>
                        )}
                      </>
                    )}
                  </TableCell>
                </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(event, page) => setCurrentPage(page)}
            color="primary"
            size="large"
            showFirstButton
            showLastButton
          />
        </Box>
      )}

      {/* Invoice Configuration Dialog */}
      <Dialog open={invoiceDialogOpen} onClose={() => setInvoiceDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure Invoice Timing</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Configure when the invoice will be issued to the client for this procurement item.
          </Alert>
          
          {selectedDecision && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="textSecondary">Item:</Typography>
              <Typography variant="body1" fontWeight="medium">{selectedDecision.item_code}</Typography>
              
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>Delivery Date:</Typography>
              <Typography variant="body1">{formatDate(selectedDecision.delivery_date)}</Typography>
              
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>Cost:</Typography>
              <Typography variant="body1">{formatCurrency(selectedDecision.final_cost)}</Typography>
            </Box>
          )}
          
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Invoice Timing Type</InputLabel>
            <Select
              value={invoiceTimingType}
              label="Invoice Timing Type"
              onChange={(e) => setInvoiceTimingType(e.target.value)}
            >
              <MenuItem value="ABSOLUTE">Absolute Date (Specific Date)</MenuItem>
              <MenuItem value="RELATIVE">Relative (Days After Delivery)</MenuItem>
            </Select>
          </FormControl>
          
          {invoiceTimingType === 'ABSOLUTE' ? (
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Invoice Issue Date"
                value={invoiceDate}
                onChange={(newValue) => setInvoiceDate(newValue)}
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
              label="Days After Delivery"
              value={invoiceDays}
              onChange={(e) => setInvoiceDays(parseInt(e.target.value) || 30)}
              helperText="Number of days after delivery to issue invoice (e.g., 30 for Net 30)"
              inputProps={{ min: 0, max: 365 }}
            />
          )}
          
          <Alert severity="info" sx={{ mt: 2 }}>
            <strong>Calculation Preview:</strong><br />
            {invoiceTimingType === 'ABSOLUTE' ? (
              <>Invoice will be issued on: <strong>{invoiceDate ? formatDate(invoiceDate.toISOString()) : 'Not set'}</strong></>
            ) : (
              <>Invoice will be issued: <strong>{invoiceDays} days after delivery</strong> 
              {selectedDecision && ` (approx. ${formatDate(new Date(new Date(selectedDecision.delivery_date).getTime() + invoiceDays * 24 * 60 * 60 * 1000).toISOString())})`}</>
            )}
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInvoiceDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleUpdateInvoice} variant="contained" color="primary">
            Save Invoice Configuration
          </Button>
        </DialogActions>
      </Dialog>

      {/* Actual Invoice Dialog */}
      <Dialog open={actualInvoiceDialogOpen} onClose={() => setActualInvoiceDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssignmentIcon color="success" />
            Enter Actual Invoice Data
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3, mt: 1 }}>
            Enter the actual invoice data received from the client. This will create ACTUAL cash flow events for accurate financial tracking.
          </Alert>

          {selectedDecision && (
            <>
              {/* Decision Summary */}
              <Paper sx={{ p: 2, mb: 3, bgcolor: '#f5f5f5' }}>
                <Typography variant="subtitle2" gutterBottom>Decision Summary</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="textSecondary">Item Code:</Typography>
                    <Typography variant="body2" fontWeight="medium">{selectedDecision.item_code}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="textSecondary">Delivery Date:</Typography>
                    <Typography variant="body2">{formatDate(selectedDecision.delivery_date)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="textSecondary">Forecasted Amount:</Typography>
                    <Typography variant="body2" sx={{ color: '#2196f3' }}>
                      {formatCurrency(selectedDecision.forecast_invoice_amount || selectedDecision.final_cost)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="textSecondary">Forecasted Date:</Typography>
                    <Typography variant="body2" sx={{ color: '#2196f3' }}>
                      {selectedDecision.forecast_invoice_issue_date 
                        ? formatDate(selectedDecision.forecast_invoice_issue_date)
                        : `+${selectedDecision.forecast_invoice_days_after_delivery} days`}
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>

              {/* Actual Invoice Form */}
              <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
                💰 Actual Invoice Information
              </Typography>

              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
                  <DatePicker
                    label="Actual Invoice Issue Date *"
                    value={actualInvoiceDate}
                    onChange={(newValue) => setActualInvoiceDate(newValue)}
                    slotProps={{ 
                      textField: { 
                        fullWidth: true,
                        helperText: "When was the invoice actually issued?"
                      } 
                    }}
                  />

                  <DatePicker
                    label="Payment Received Date"
                    value={actualReceivedDate}
                    onChange={(newValue) => setActualReceivedDate(newValue)}
                    slotProps={{ 
                      textField: { 
                        fullWidth: true,
                        helperText: "When was payment received? (optional)"
                      } 
                    }}
                  />
                </Box>
              </LocalizationProvider>

              <TextField
                fullWidth
                type="number"
                label="Actual Invoice Amount *"
                value={actualInvoiceAmount}
                onChange={(e) => setActualInvoiceAmount(parseFloat(e.target.value) || 0)}
                helperText="The actual amount invoiced to the client"
                inputProps={{ min: 0, step: 0.01 }}
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                multiline
                rows={3}
                label="Notes"
                value={actualInvoiceNotes}
                onChange={(e) => setActualInvoiceNotes(e.target.value)}
                helperText="Invoice number, payment terms, or other relevant information"
                placeholder="e.g., Invoice #INV-2025-001, Net 30 payment terms"
              />

              {/* Variance Display */}
              {actualInvoiceAmount > 0 && (
                <Alert 
                  severity={
                    Math.abs(actualInvoiceAmount - (selectedDecision.forecast_invoice_amount || selectedDecision.final_cost)) < 100 
                      ? 'success' 
                      : 'warning'
                  } 
                  sx={{ mt: 2 }}
                >
                  <Typography variant="body2" fontWeight="medium">
                    Variance: {formatCurrency(
                      actualInvoiceAmount - (selectedDecision.forecast_invoice_amount || selectedDecision.final_cost)
                    )}
                  </Typography>
                  <Typography variant="caption">
                    {actualInvoiceAmount > (selectedDecision.forecast_invoice_amount || selectedDecision.final_cost)
                      ? 'Higher than forecast (favorable)'
                      : actualInvoiceAmount < (selectedDecision.forecast_invoice_amount || selectedDecision.final_cost)
                      ? 'Lower than forecast (unfavorable)'
                      : 'Matches forecast exactly'}
                  </Typography>
                </Alert>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActualInvoiceDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSubmitActualInvoice} 
            variant="contained" 
            color="success"
            disabled={!actualInvoiceDate || actualInvoiceAmount <= 0}
          >
            Submit Actual Invoice Data
          </Button>
        </DialogActions>
      </Dialog>

      {/* Actual Payment Dialog */}
      <Dialog open={actualPaymentDialogOpen} onClose={() => setActualPaymentDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AttachMoneyIcon color="warning" />
            Enter Actual Payment Data
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3, mt: 1 }}>
            Enter the actual payment data made to the supplier. This will create ACTUAL cash flow events (Payment Outflow) for accurate financial tracking.
          </Alert>

          {selectedDecision && (
            <>
              <Paper elevation={0} sx={{ p: 2, mb: 3, bgcolor: 'grey.50', border: '1px solid', borderColor: 'grey.200' }}>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Item Code</Typography>
                    <Typography variant="body2" fontWeight="medium">{selectedDecision.item_code}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Supplier</Typography>
                    <Typography variant="body2" fontWeight="medium">{selectedDecision.supplier_name}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Payment Terms</Typography>
                    <Chip 
                      label={(selectedDecision.payment_terms as any)?.type || 'cash'} 
                      size="small"
                      color={(selectedDecision.payment_terms as any)?.type === 'cash' ? 'success' : 'warning'}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Expected Cost</Typography>
                    <Typography variant="body2" fontWeight="medium">{formatCurrency(selectedDecision.final_cost)}</Typography>
                  </Grid>
                </Grid>
              </Paper>

              {/* Payment Details */}
              {actualPaymentInstallments.length > 0 ? (
                <>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Installment Payment:</strong> Enter actual payment details for each installment
                    </Typography>
                  </Alert>

                  {actualPaymentInstallments.map((installment, index) => (
                    <Paper key={index} elevation={1} sx={{ p: 2, mb: 2, border: '1px solid', borderColor: 'divider' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Installment {index + 1}
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <LocalizationProvider dateAdapter={AdapterDateFns}>
                            <DatePicker
                              label="Payment Date *"
                              value={new Date(installment.date)}
                              onChange={(newDate) => {
                                if (newDate) {
                                  const updated = [...actualPaymentInstallments];
                                  updated[index].date = newDate.toISOString().split('T')[0];
                                  setActualPaymentInstallments(updated);
                                }
                              }}
                              slotProps={{
                                textField: {
                                  fullWidth: true,
                                  size: 'small',
                                },
                              }}
                            />
                          </LocalizationProvider>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <TextField
                            fullWidth
                            type="number"
                            size="small"
                            label="Payment Amount *"
                            value={installment.amount}
                            onChange={(e) => {
                              const updated = [...actualPaymentInstallments];
                              updated[index].amount = parseFloat(e.target.value) || 0;
                              setActualPaymentInstallments(updated);
                            }}
                            inputProps={{ min: 0, step: 0.01 }}
                          />
                        </Grid>
                      </Grid>
                    </Paper>
                  ))}

                  <Paper elevation={0} sx={{ p: 2, bgcolor: 'primary.lighter', border: '1px solid', borderColor: 'primary.main' }}>
                    <Typography variant="body2" color="primary.dark" fontWeight="medium">
                      Total Payment: {formatCurrency(actualPaymentInstallments.reduce((sum, inst) => sum + inst.amount, 0))}
                    </Typography>
                  </Paper>
                </>
              ) : (
                <>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Cash Payment:</strong> Single payment to supplier
                    </Typography>
                  </Alert>

                  <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <Box sx={{ mb: 2 }}>
                      <DatePicker
                        label="Payment Date *"
                        value={actualPaymentDate}
                        onChange={(newDate) => setActualPaymentDate(newDate)}
                        slotProps={{
                          textField: {
                            fullWidth: true,
                            helperText: "The actual date payment was made to the supplier",
                          },
                        }}
                      />
                    </Box>
                  </LocalizationProvider>

                  <TextField
                    fullWidth
                    type="number"
                    label="Actual Payment Amount *"
                    value={actualPaymentAmount}
                    onChange={(e) => setActualPaymentAmount(parseFloat(e.target.value) || 0)}
                    helperText="The actual amount paid to the supplier"
                    inputProps={{ min: 0, step: 0.01 }}
                    sx={{ mb: 2 }}
                  />
                </>
              )}

              <TextField
                fullWidth
                multiline
                rows={3}
                label="Notes"
                value={actualPaymentNotes}
                onChange={(e) => setActualPaymentNotes(e.target.value)}
                helperText="Payment reference, bank transaction ID, or other relevant information"
                placeholder="e.g., Transfer Ref: TXN-2025-001, Bank: ABC Bank"
              />

              {/* Variance Display */}
              {(actualPaymentInstallments.length > 0 ? 
                actualPaymentInstallments.reduce((sum, inst) => sum + inst.amount, 0) : 
                actualPaymentAmount) > 0 && (
                <Alert 
                  severity={
                    Math.abs((actualPaymentInstallments.length > 0 ? 
                      actualPaymentInstallments.reduce((sum, inst) => sum + inst.amount, 0) : 
                      actualPaymentAmount) - selectedDecision.final_cost) < 100 
                      ? 'success' 
                      : 'warning'
                  } 
                  sx={{ mt: 2 }}
                >
                  <Typography variant="body2" fontWeight="medium">
                    Variance: {formatCurrency(
                      (actualPaymentInstallments.length > 0 ? 
                        actualPaymentInstallments.reduce((sum, inst) => sum + inst.amount, 0) : 
                        actualPaymentAmount) - selectedDecision.final_cost
                    )}
                  </Typography>
                  <Typography variant="caption">
                    {(actualPaymentInstallments.length > 0 ? 
                      actualPaymentInstallments.reduce((sum, inst) => sum + inst.amount, 0) : 
                      actualPaymentAmount) > selectedDecision.final_cost
                      ? 'Higher than expected (unfavorable - cost overrun)'
                      : (actualPaymentInstallments.length > 0 ? 
                        actualPaymentInstallments.reduce((sum, inst) => sum + inst.amount, 0) : 
                        actualPaymentAmount) < selectedDecision.final_cost
                      ? 'Lower than expected (favorable - cost savings)'
                      : 'Matches forecast exactly'}
                  </Typography>
                </Alert>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActualPaymentDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSubmitActualPayment} 
            variant="contained" 
            color="warning"
            disabled={
              actualPaymentInstallments.length > 0 
                ? actualPaymentInstallments.some(inst => !inst.date || inst.amount <= 0)
                : !actualPaymentDate || actualPaymentAmount <= 0
            }
          >
            Submit Actual Payment Data
          </Button>
        </DialogActions>
      </Dialog>

      {/* Revert Dialog */}
      <Dialog open={revertDialogOpen} onClose={() => setRevertDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Revert Decision</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <strong>Warning:</strong> Reverting this decision will delete all associated cash flow events.
            The item will become available for re-optimization.
          </Alert>
          
          {selectedDecision && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="textSecondary">Item Code:</Typography>
              <Typography variant="body1" fontWeight="medium">{selectedDecision.item_code}</Typography>
              
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>Cost:</Typography>
              <Typography variant="body1">{formatCurrency(selectedDecision.final_cost)}</Typography>
            </Box>
          )}
          
          <TextField
            margin="dense"
            label="Reason for Reversion (Optional)"
            multiline
            rows={3}
            fullWidth
            variant="outlined"
            value={revertNotes}
            onChange={(e) => setRevertNotes(e.target.value)}
            placeholder="Explain why this decision is being reverted..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRevertDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRevert} variant="contained" color="error">
            Confirm Revert
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

