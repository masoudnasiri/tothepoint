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
  Search as SearchIcon,
} from '@mui/icons-material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { useAuth } from '../contexts/AuthContext.tsx';
import { decisionsAPI } from '../services/api.ts';
import { useNavigate } from 'react-router-dom';
import { ProjectFilter } from '../components/ProjectFilter.tsx';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
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
          <Typography variant="h4">{t('decisions.title')}</Typography>
          <Typography variant="subtitle2" color="textSecondary">
            {t('decisions.subtitle')}
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
              label={t('decisions.filterByProjects')}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label={t('decisions.searchItemsSuppliers')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={t('decisions.searchPlaceholder')}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
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
              label={`${t('decisions.total')}: ${totalCount} (${t('decisions.page')} ${currentPage} ${t('decisions.of')} ${totalPages})`}
              color="primary"
              variant="outlined"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`${t('decisions.locked')}: ${summaryStats?.locked || 0}`}
              color="success"
              variant="outlined"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`${t('decisions.proposed')}: ${summaryStats?.proposed || 0}`}
              color="warning"
              variant="outlined"
              sx={{ width: '100%' }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Chip
              label={`${t('decisions.reverted')}: ${summaryStats?.reverted || 0}`}
              color="error"
              variant="outlined"
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
                      label={t(`decisions.${decision.status.toLowerCase()}`)}
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
              label={t('decisions.invoiceTimingType')}
              onChange={(e) => setInvoiceTimingType(e.target.value)}
            >
              <MenuItem value="ABSOLUTE">Absolute Date (Specific Date)</MenuItem>
              <MenuItem value="RELATIVE">Relative (Days After Delivery)</MenuItem>
            </Select>
          </FormControl>
          
          {invoiceTimingType === 'ABSOLUTE' ? (
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label={t('decisions.invoiceIssueDate')}
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
              label={t('decisions.daysAfterDelivery')}
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

