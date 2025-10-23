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
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Grid,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  FormControlLabel,
  Switch,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  AttachMoney as AttachMoneyIcon,
  Speed as SpeedIcon,
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  Assessment as AssessmentIcon,
  AccountTree as AccountTreeIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  AccountBalance as AccountBalanceIcon,
  Add as AddIcon,
  Save as SaveIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { financeAPI, decisionsAPI, procurementAPI } from '../services/api.ts';
import { BudgetAnalysis } from '../components/BudgetAnalysis.tsx';
import { formatApiError } from '../utils/errorUtils.ts';
import { useTranslation } from 'react-i18next';

interface SolverInfo {
  type: string;
  name: string;
  description: string;
  best_for: string;
  performance: string;
  supports_strategies: boolean;
  note?: string;
}

interface StrategyInfo {
  type: string;
  name: string;
  description: string;
  objective: string;
}

interface OptimizationDecision {
  project_id: number;
  project_code: string;
  item_code: string;
  item_name: string;
  procurement_option_id: number;
  supplier_name: string;
  purchase_date: string;
  delivery_date: string;
  quantity: number;
  unit_cost: number;
  final_cost: number;
  payment_terms: string;
}

interface OptimizationProposal {
  proposal_name: string;
  strategy_type: string;
  total_cost: number;
  weighted_cost: number;
  status: string;
  items_count: number;
  decisions: OptimizationDecision[];
  summary_notes?: string;
}

interface OptimizationResponse {
  run_id: string;
  run_timestamp: string;
  status: string;
  execution_time_seconds: number;
  total_cost: number;
  items_optimized: number;
  proposals: OptimizationProposal[];
  message?: string;
}

export const OptimizationPageEnhanced: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [solverInfo, setSolverInfo] = useState<{ available_solvers: SolverInfo[], available_strategies: StrategyInfo[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [mainTabValue, setMainTabValue] = useState(0); // 0 = Optimization, 1 = Budget Analysis
  const [optimizing, setOptimizing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [runDialogOpen, setRunDialogOpen] = useState(false);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedSolver, setSelectedSolver] = useState<SolverInfo | null>(null);
  const [lastRun, setLastRun] = useState<OptimizationResponse | null>(null);
  const [selectedProposalIndex, setSelectedProposalIndex] = useState(0);
  const [selectedDecision, setSelectedDecision] = useState<OptimizationDecision | null>(null);
  const [editedDecisions, setEditedDecisions] = useState<Record<string, OptimizationDecision>>({});
  const [removedDecisions, setRemovedDecisions] = useState<Set<string>>(new Set());
  const [addedDecisions, setAddedDecisions] = useState<OptimizationDecision[]>([]);
  const [procurementOptions, setProcurementOptions] = useState<any[]>([]);
  
  const [optimizationConfig, setOptimizationConfig] = useState({
    max_time_slots: 60,  // Increased from 12 to 60 to accommodate all delivery dates (up to 60 days)
    time_limit_seconds: 300,
    solver_type: 'CP_SAT',
    generate_multiple_proposals: true,
    strategies: [] as string[],
  });

  useEffect(() => {
    fetchSolverInfo();
    fetchProcurementOptions();
    fetchExistingProposals();
  }, []);
  
  const fetchExistingProposals = async () => {
    try {
      // Fetch PROPOSED decisions (not yet finalized/locked)
      const response = await decisionsAPI.list({ limit: 1000 });
      const proposedDecisions = response.data.filter((d: any) => d.status === 'PROPOSED');
      
      if (proposedDecisions.length > 0) {
        // Group by run_id
        const runGroups = proposedDecisions.reduce((groups: any, decision: any) => {
          if (!groups[decision.run_id]) {
            groups[decision.run_id] = [];
          }
          groups[decision.run_id].push(decision);
          return groups;
        }, {});
        
        // Convert to proposals format
        const proposals = Object.entries(runGroups).map(([run_id, decisions]: any) => {
          const total_cost = decisions.reduce((sum: number, d: any) => sum + (d.final_cost || 0), 0);
          const items_count = decisions.length;
          
          return {
            proposal_id: `existing_${run_id}`,
            run_id: run_id,
            strategy: 'Existing Proposal',
            solver: 'User Created',
            total_cost: total_cost,
            items_count: items_count,
            decisions: decisions.map((d: any) => ({
              project_id: d.project_id,
              project_code: d.project_code,
              item_code: d.item_code,
              item_name: d.item_name || d.item_code,
              quantity: d.quantity,
              supplier_name: d.supplier_name,
              delivery_time: 0,
              final_cost: d.final_cost,
              delivery_date: d.delivery_date,
              payment_terms: d.payment_terms || { type: 'cash' },
            })),
            status: 'PROPOSED',
            timestamp: new Date().toISOString(),
          };
        });
        
        // Set as lastRun with existing proposals
        setLastRun({
          status: 'success',
          message: `Loaded ${proposals.length} existing proposal(s)`,
          total_cost: proposals[0]?.total_cost || 0,
          solver_type: 'Multiple',
          strategy: 'Existing',
          proposals: proposals,
          timestamp: new Date().toISOString(),
        });
        
        setSuccess(`Loaded ${proposals.length} existing proposal(s) with ${proposedDecisions.length} items. You can edit, finalize, or delete them.`);
      }
    } catch (err: any) {
      console.error('Failed to load existing proposals:', err);
    }
  };

  const fetchSolverInfo = async () => {
    try {
      const response = await financeAPI.getSolverInfo();
      setSolverInfo(response.data);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to load solver information'));
    } finally {
      setLoading(false);
    }
  };

  const fetchProcurementOptions = async () => {
    try {
      const response = await procurementAPI.listOptions();
      setProcurementOptions(response.data);
    } catch (err: any) {
      console.error('Failed to load procurement options');
    }
  };

  const handleRunOptimization = async () => {
    setOptimizing(true);
    setError('');
    setSuccess('');

    try {
      console.log('[ENHANCED OPTIMIZATION] Starting optimization with config:', optimizationConfig);
      
      const params = new URLSearchParams({
        solver_type: optimizationConfig.solver_type,
        generate_multiple_proposals: String(optimizationConfig.generate_multiple_proposals),
      });
      
      if (optimizationConfig.strategies.length > 0) {
        optimizationConfig.strategies.forEach(s => params.append('strategies', s));
      }

      console.log('[ENHANCED OPTIMIZATION] Request params:', params.toString());
      console.log('[ENHANCED OPTIMIZATION] Request body:', {
        max_time_slots: optimizationConfig.max_time_slots,
        time_limit_seconds: optimizationConfig.time_limit_seconds,
      });

      const response = await financeAPI.runEnhancedOptimization(
        {
          max_time_slots: optimizationConfig.max_time_slots,
          time_limit_seconds: optimizationConfig.time_limit_seconds,
        },
        params.toString()
      );
      
      console.log('[ENHANCED OPTIMIZATION] Response:', response.data);
      console.log('[ENHANCED OPTIMIZATION] Response status:', response.data.status);
      console.log('[ENHANCED OPTIMIZATION] Proposals count:', response.data.proposals?.length || 0);
      console.log('[ENHANCED OPTIMIZATION] Run ID:', response.data.run_id);
      console.log('[ENHANCED OPTIMIZATION] Run ID type:', typeof response.data.run_id);
      
      setLastRun(response.data);
      setRunDialogOpen(false);
      setSelectedProposalIndex(0);
      
      if (response.data.status === 'OPTIMAL' || response.data.status === 'FEASIBLE') {
        console.log('[ENHANCED OPTIMIZATION] SUCCESS! Setting success message');
        setSuccess(
          `Optimization completed! Generated ${response.data.proposals.length} proposal(s). ` +
          `Best cost: $${response.data.total_cost.toLocaleString()}`
        );
      } else {
        console.log('[ENHANCED OPTIMIZATION] FAILED! Setting error message');
        setError(`Optimization failed: ${response.data.message}`);
      }
    } catch (err: any) {
      console.error('[ENHANCED OPTIMIZATION] ERROR:', err);
      console.error('[ENHANCED OPTIMIZATION] Error response:', err.response?.data);
      setError(formatApiError(err, 'Optimization failed'));
    } finally {
      setOptimizing(false);
    }
  };

  const handleShowSolverInfo = (solver: SolverInfo) => {
    setSelectedSolver(solver);
    setInfoDialogOpen(true);
  };

  const handleEditDecision = (decision: OptimizationDecision) => {
    setSelectedDecision(decision);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = () => {
    if (selectedDecision) {
      const key = `${selectedDecision.project_id}_${selectedDecision.item_code}`;
      setEditedDecisions({
        ...editedDecisions,
        [key]: selectedDecision
      });
      setEditDialogOpen(false);
      setSelectedDecision(null);
      setSuccess('Decision updated locally. Save the proposal to persist changes.');
    }
  };

  const handleRemoveDecision = (decision: OptimizationDecision) => {
    if (window.confirm(`Remove ${decision.item_code} from this proposal?`)) {
      const key = `${decision.project_id}_${decision.item_code}`;
      setRemovedDecisions(new Set([...removedDecisions, key]));
      setSuccess('Decision removed locally. Save the proposal to persist changes.');
    }
  };

  const handleAddDecision = () => {
    const proposal = lastRun?.proposals[selectedProposalIndex];
    if (!proposal) return;

    const newDecision: OptimizationDecision = {
      project_id: 1,
      project_code: 'NEW',
      item_code: '',
      item_name: 'New Item',
      procurement_option_id: procurementOptions.length > 0 ? procurementOptions[0].id : 0,
      supplier_name: procurementOptions.length > 0 ? procurementOptions[0].supplier_name : '',
      purchase_date: new Date().toISOString().split('T')[0],
      delivery_date: new Date().toISOString().split('T')[0],
      quantity: 1,
      unit_cost: 0,
      final_cost: 0,
      payment_terms: 'cash',
    };

    setSelectedDecision(newDecision);
    setAddDialogOpen(false);
    setEditDialogOpen(true);
  };

  const handleSaveAddedDecision = () => {
    if (selectedDecision && !selectedDecision.item_code) {
      // This was opened from add dialog
      setAddedDecisions([...addedDecisions, selectedDecision]);
      setEditDialogOpen(false);
      setSelectedDecision(null);
      setSuccess('Decision added locally. Save the proposal to persist changes.');
    } else {
      handleSaveEdit();
    }
  };

  const handleDeleteOptimization = async () => {
    if (!lastRun) return;
    
    try {
      setSaving(true);
      setError('');
      
      await financeAPI.deleteOptimizationResults(lastRun.run_id);
      
      setDeleteDialogOpen(false);
      setLastRun(null);
      setSuccess('Optimization results deleted successfully.');
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to delete optimization results'));
    } finally {
      setSaving(false);
    }
  };

  const [savedProposalRunId, setSavedProposalRunId] = useState<string | null>(null);
  const [savedDecisionIds, setSavedDecisionIds] = useState<number[]>([]);
  const [finalizeDialogOpen, setFinalizeDialogOpen] = useState(false);
  const [previousRuns, setPreviousRuns] = useState<any[]>([]);
  const [previousRunsDialogOpen, setPreviousRunsDialogOpen] = useState(false);

  useEffect(() => {
    if (lastRun) {
      fetchPreviousRuns();
    }
  }, [lastRun]);

  const fetchPreviousRuns = async () => {
    try {
      const response = await financeAPI.listOptimizationRuns({ limit: 10 });
      setPreviousRuns(response.data);
    } catch (err: any) {
      console.error('Failed to load previous runs');
    }
  };

  const handleSaveProposal = async (proposal: OptimizationProposal) => {
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      // Get all decisions for this proposal (including edits, removals, additions)
      const decisions = proposal.decisions
        .filter(d => {
          const key = `${d.project_id}_${d.item_code}`;
          return !removedDecisions.has(key);
        })
        .map(d => {
          const key = `${d.project_id}_${d.item_code}`;
          return editedDecisions[key] || d;
        })
        .concat(addedDecisions);

      // Prepare payload for save-proposal endpoint
      const proposalData = {
        run_id: lastRun?.run_id || '',
        proposal_name: proposal.proposal_name,
        decisions: decisions.map(d => ({
          project_id: d.project_id,
          item_code: d.item_code,
          procurement_option_id: d.procurement_option_id,
          purchase_date: d.purchase_date || new Date().toISOString().split('T')[0],
          delivery_date: d.delivery_date || new Date().toISOString().split('T')[0],
          quantity: d.quantity || 1,
          final_cost: d.final_cost || 0,
          is_manual_edit: editedDecisions[`${d.project_id}_${d.item_code}`] !== undefined,
        }))
      };

      console.log('Saving proposal data:', proposalData);
      console.log('LastRun object:', lastRun);
      console.log('LastRun run_id:', lastRun?.run_id);
      console.log('LastRun run_id type:', typeof lastRun?.run_id);

      // Call the save-proposal endpoint
      const response = await decisionsAPI.saveProposal(proposalData);
      
      setSuccess(
        `✅ Proposal "${proposal.proposal_name}" saved with ${decisions.length} decisions! ` +
        `They are now in "PROPOSED" status and can be finalized.`
      );
      
      setSavedProposalRunId(lastRun?.run_id || null);
      
      // Clear local edits
      setEditedDecisions({});
      setRemovedDecisions(new Set());
      setAddedDecisions([]);
      
      // Refresh existing proposals to show the newly saved one
      await fetchExistingProposals();
      
      // Fetch the saved decisions to get their IDs for finalization
      if (lastRun?.run_id) {
        const decisionsResponse = await decisionsAPI.list({ run_id: lastRun.run_id });
        const savedIds = decisionsResponse.data
          .filter((d: any) => d.status === 'PROPOSED')
          .map((d: any) => d.id);
        setSavedDecisionIds(savedIds);
      }
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to save proposal'));
    } finally {
      setSaving(false);
    }
  };

  const handleFinalizeProposal = async () => {
    if (savedDecisionIds.length === 0) {
      setError('No decisions to finalize. Please save a proposal first.');
      return;
    }

    try {
      setSaving(true);
      setError('');
      
      const response = await decisionsAPI.finalize({
        decision_ids: savedDecisionIds,
        finalize_all: false
      });
      
      setSuccess(`✅ Successfully locked ${response.data.finalized_count} decisions! They will not be re-optimized.`);
      setFinalizeDialogOpen(false);
      setSavedDecisionIds([]);
      
      // Refresh existing proposals to remove finalized ones
      await fetchExistingProposals();
      
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to finalize decisions'));
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (value: number) => {
    if (isNaN(value) || value === null || value === undefined) {
      return '$0.00';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    if (!dateString || dateString === 'Invalid Date' || dateString === 'null' || dateString === 'undefined') {
      return 'Not Set';
    }
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }
    return date.toLocaleDateString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPTIMAL':
        return 'success';
      case 'FEASIBLE':
        return 'warning';
      case 'INFEASIBLE':
        return 'error';
      default:
        return 'default';
    }
  };

  const getProposalIcon = (strategyType: string) => {
    switch (strategyType) {
      case 'LOWEST_COST':
        return <AttachMoneyIcon />;
      case 'FAST_DELIVERY':
        return <SpeedIcon />;
      case 'SMOOTH_CASHFLOW':
        return <TrendingUpIcon />;
      case 'PRIORITY_WEIGHTED':
        return <AccountTreeIcon />;
      default:
        return <AssessmentIcon />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const selectedProposal = lastRun?.proposals[selectedProposalIndex];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">{t('optimization.title')}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t('optimization.subtitle')}
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          {previousRuns.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<AssessmentIcon />}
              onClick={() => setPreviousRunsDialogOpen(true)}
              disabled={optimizing}
            >
              Previous Runs ({previousRuns.length})
            </Button>
          )}
          {lastRun && (user?.role === 'finance' || user?.role === 'admin') && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteDialogOpen(true)}
              disabled={saving || optimizing}
            >
              Delete Results
            </Button>
          )}
          {(user?.role === 'finance' || user?.role === 'admin') && (
            <Button
              variant="contained"
              startIcon={<PlayArrowIcon />}
              onClick={() => setRunDialogOpen(true)}
              disabled={optimizing}
              size="large"
            >
              {optimizing ? 'Running...' : 'Run Optimization'}
            </Button>
          )}
        </Box>
      </Box>

      {/* Main Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={mainTabValue} onChange={(e, newValue) => setMainTabValue(newValue)}>
          <Tab 
            icon={<TrendingUpIcon />} 
            label={t('optimization.optimizationResults')} 
            iconPosition="start"
          />
          <Tab 
            icon={<AccountBalanceIcon />} 
            label={t('optimization.budgetAnalysis')} 
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Budget Analysis Tab */}
      {mainTabValue === 1 && (
        <BudgetAnalysis />
      )}

      {/* Optimization Tab */}
      {mainTabValue === 0 && (
        <>
          {optimizing && (
            <Card sx={{ mb: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <CircularProgress size={20} sx={{ mr: 2, color: 'inherit' }} />
              <Typography variant="h6">{t('optimization.running')}</Typography>
            </Box>
            <LinearProgress sx={{ mb: 1 }} />
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Using {optimizationConfig.solver_type} solver with {
                optimizationConfig.generate_multiple_proposals 
                  ? 'multiple strategies' 
                  : 'single strategy'
              }. This may take several minutes.
            </Typography>
          </CardContent>
        </Card>
      )}

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

      {/* Solver Information Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            Available Solvers
          </Typography>
        </Grid>
        {solverInfo?.available_solvers.map((solver) => (
          <Grid item xs={12} sm={6} md={3} key={solver.type}>
            <Card 
              sx={{ 
                height: '100%',
                cursor: 'pointer',
                border: optimizationConfig.solver_type === solver.type ? '2px solid' : '1px solid',
                borderColor: optimizationConfig.solver_type === solver.type ? 'primary.main' : 'divider',
                '&:hover': { boxShadow: 3 }
              }}
              onClick={() => setOptimizationConfig({ ...optimizationConfig, solver_type: solver.type })}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start">
                  <Typography variant="h6" gutterBottom>
                    {solver.type}
                  </Typography>
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleShowSolverInfo(solver); }}>
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {solver.description}
                </Typography>
                <Chip 
                  label={optimizationConfig.solver_type === solver.type ? t('optimization.selected') : t('optimization.available')} 
                  size="small" 
                  color={optimizationConfig.solver_type === solver.type ? 'primary' : 'default'}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Results Section */}
      {lastRun && lastRun.proposals.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Optimization Results
            </Typography>
            
            {/* Summary Statistics */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, bgcolor: 'success.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip 
                    label={t(`optimization.${lastRun.status.toLowerCase()}`)} 
                    color={getStatusColor(lastRun.status) as any}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, bgcolor: 'info.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    Best Total Cost
                  </Typography>
                  <Typography variant="h6">
                    {formatCurrency(lastRun.total_cost)}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, bgcolor: 'warning.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    Proposals Generated
                  </Typography>
                  <Typography variant="h6">
                    {lastRun.proposals.length}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, bgcolor: 'secondary.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    Execution Time
                  </Typography>
                  <Typography variant="h6">
                    {lastRun.execution_time_seconds ? lastRun.execution_time_seconds.toFixed(2) : '0.00'}s
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            {/* Proposal Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs 
                value={selectedProposalIndex} 
                onChange={(e, newValue) => setSelectedProposalIndex(newValue)}
                variant="scrollable"
                scrollButtons="auto"
              >
                {lastRun.proposals.map((proposal, index) => (
                  <Tab 
                    key={index}
                    label={
                      <Box display="flex" alignItems="center" gap={1}>
                        {getProposalIcon(proposal.strategy_type)}
                        <Box>
                          <Typography variant="body2">{proposal.proposal_name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatCurrency(proposal.total_cost)}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                ))}
              </Tabs>
            </Box>

            {/* Selected Proposal Details */}
            {selectedProposal && (
              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Box>
                    <Typography variant="h6">
                      {selectedProposal.proposal_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedProposal.summary_notes}
                    </Typography>
                  </Box>
                  <Box display="flex" gap={1} alignItems="center">
                    {(Object.keys(editedDecisions).length > 0 || removedDecisions.size > 0 || addedDecisions.length > 0) && (
                      <Chip 
                        label={t('optimization.hasLocalChanges')}
                        color="warning"
                        size="small"
                      />
                    )}
                    <Chip 
                      label={`${selectedProposal.items_count} ${t('optimization.items')}`}
                      color="primary"
                      variant="outlined"
                    />
                    <Chip 
                      label={t(`optimization.${selectedProposal.status.toLowerCase()}`)}
                      color={getStatusColor(selectedProposal.status) as any}
                    />
                    {(user?.role === 'finance' || user?.role === 'admin' || user?.role === 'pm') && (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<AddIcon />}
                        onClick={() => {
                          setSelectedDecision(null);
                          setAddDialogOpen(true);
                        }}
                      >
                        Add Item
                      </Button>
                    )}
                  </Box>
                </Box>

                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12} sm={6}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Total Cost
                      </Typography>
                      <Typography variant="h5">
                        {formatCurrency(selectedProposal.total_cost)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Weighted Cost
                      </Typography>
                      <Typography variant="h5">
                        {formatCurrency(selectedProposal.weighted_cost)}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                {/* Decisions Table */}
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Project</TableCell>
                        <TableCell>Item</TableCell>
                        <TableCell>Supplier</TableCell>
                        <TableCell>Purchase Date</TableCell>
                        <TableCell>Delivery Date</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell align="right">Unit Cost</TableCell>
                        <TableCell align="right">Total Cost</TableCell>
                        <TableCell>Payment</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedProposal.decisions
                        .filter(d => {
                          const key = `${d.project_id}_${d.item_code}`;
                          return !removedDecisions.has(key);
                        })
                        .map((decision, idx) => {
                          const key = `${decision.project_id}_${decision.item_code}`;
                          const editedDecision = editedDecisions[key];
                          const isEdited = !!editedDecision;
                          const displayDecision = editedDecision || decision;
                          
                          return (
                            <TableRow 
                              key={idx} 
                              hover
                              sx={{ bgcolor: isEdited ? 'action.hover' : 'inherit' }}
                            >
                              <TableCell>
                                <Typography variant="body2" fontWeight="medium">
                                  {displayDecision.project_code}
                                </Typography>
                                {isEdited && (
                                  <Chip label={t('optimization.edited')} size="small" color="warning" sx={{ ml: 1 }} />
                                )}
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2">{displayDecision.item_code}</Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {displayDecision.item_name}
                                </Typography>
                              </TableCell>
                              <TableCell>{displayDecision.supplier_name}</TableCell>
                              <TableCell>{formatDate(displayDecision.purchase_date)}</TableCell>
                              <TableCell>{formatDate(displayDecision.delivery_date)}</TableCell>
                              <TableCell align="right">{displayDecision.quantity}</TableCell>
                              <TableCell align="right">{formatCurrency(displayDecision.unit_cost)}</TableCell>
                              <TableCell align="right">
                                <Typography variant="body2" fontWeight="medium">
                                  {formatCurrency(displayDecision.final_cost)}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Chip label={typeof displayDecision.payment_terms === 'string' ? displayDecision.payment_terms : t('optimization.paymentTerms')} size="small" />
                              </TableCell>
                              <TableCell align="center">
                                <IconButton
                                  size="small"
                                  onClick={() => handleEditDecision(displayDecision)}
                                  title="Edit Decision"
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleRemoveDecision(displayDecision)}
                                  title="Remove from Proposal"
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      {addedDecisions.map((decision, idx) => (
                        <TableRow 
                          key={`added-${idx}`}
                          sx={{ bgcolor: 'success.light', opacity: 0.9 }}
                        >
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {decision.project_code}
                            </Typography>
                            <Chip label={t('optimization.new')} size="small" color="success" sx={{ ml: 1 }} />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">{decision.item_code}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {decision.item_name}
                            </Typography>
                          </TableCell>
                          <TableCell>{decision.supplier_name}</TableCell>
                          <TableCell>{formatDate(decision.purchase_date)}</TableCell>
                          <TableCell>{formatDate(decision.delivery_date)}</TableCell>
                          <TableCell align="right">{decision.quantity}</TableCell>
                          <TableCell align="right">{formatCurrency(decision.unit_cost)}</TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {formatCurrency(decision.final_cost)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={typeof decision.payment_terms === 'string' ? decision.payment_terms : t('optimization.paymentTerms')} size="small" />
                          </TableCell>
                          <TableCell align="center">
                            <IconButton
                              size="small"
                              onClick={() => handleEditDecision(decision)}
                              title="Edit Decision"
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => {
                                setAddedDecisions(addedDecisions.filter((_, i) => i !== idx));
                              }}
                              title="Remove"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Save Proposal Button - Finance/Admin ONLY (PM cannot save or finalize) */}
                {(user?.role === 'finance' || user?.role === 'admin') && (
                  <Box display="flex" justifyContent="flex-end" mt={2} gap={2}>
                    {savedDecisionIds.length > 0 && savedProposalRunId === lastRun?.run_id && (
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<LockIcon />}
                        onClick={() => setFinalizeDialogOpen(true)}
                        disabled={saving}
                      >
                        Finalize & Lock Decisions
                      </Button>
                    )}
                    <Button
                      variant="contained"
                      color="success"
                      startIcon={<SaveIcon />}
                      onClick={() => handleSaveProposal(selectedProposal)}
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : 'Save Proposal as Decisions'}
                    </Button>
                  </Box>
                )}
                
                {/* PM users see read-only message */}
                {user?.role === 'pm' && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      <strong>PM Access:</strong> You can view optimization results but cannot save or finalize decisions. 
                      Contact Finance or Admin users to save proposals.
                    </Typography>
                  </Alert>
                )}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Run Optimization Dialog */}
      <Dialog open={runDialogOpen} onClose={() => setRunDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Configure Advanced Optimization</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph sx={{ mt: 2 }}>
            Configure optimization parameters and select solver type and strategies.
          </Typography>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Solver Type</InputLabel>
            <Select
              value={optimizationConfig.solver_type}
              label={t('optimization.solverType')}
              onChange={(e) => setOptimizationConfig({ ...optimizationConfig, solver_type: e.target.value })}
            >
              {solverInfo?.available_solvers.map((solver) => (
                <MenuItem key={solver.type} value={solver.type}>
                  {solver.type} - {solver.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            margin="dense"
            label={t('optimization.maximumTimeSlots')}
            type="number"
            fullWidth
            variant="outlined"
            value={optimizationConfig.max_time_slots}
            onChange={(e) => setOptimizationConfig({
              ...optimizationConfig,
              max_time_slots: parseInt(e.target.value) || 12
            })}
            sx={{ mb: 2 }}
            helperText="Number of time periods to consider"
          />

          <TextField
            margin="dense"
            label={t('optimization.timeLimit')}
            type="number"
            fullWidth
            variant="outlined"
            value={optimizationConfig.time_limit_seconds}
            onChange={(e) => setOptimizationConfig({
              ...optimizationConfig,
              time_limit_seconds: parseInt(e.target.value) || 300
            })}
            sx={{ mb: 2 }}
            helperText="Maximum optimization time"
          />

          <FormControlLabel
            control={
              <Switch
                checked={optimizationConfig.generate_multiple_proposals}
                onChange={(e) => setOptimizationConfig({
                  ...optimizationConfig,
                  generate_multiple_proposals: e.target.checked
                })}
              />
            }
            label={t('optimization.generateMultipleProposals')}
            sx={{ mb: 2 }}
          />

          {optimizationConfig.generate_multiple_proposals && (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Strategies (leave empty for all)</InputLabel>
              <Select
                multiple
                value={optimizationConfig.strategies}
                label={t('optimization.strategies')}
                onChange={(e) => setOptimizationConfig({
                  ...optimizationConfig,
                  strategies: typeof e.target.value === 'string' ? [e.target.value] : e.target.value
                })}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {solverInfo?.available_strategies.map((strategy) => (
                  <MenuItem key={strategy.type} value={strategy.type}>
                    {strategy.name} - {strategy.description}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Tip:</strong> For the first run, use CP_SAT solver with multiple proposals enabled 
              to compare different strategies. You can then refine with specific solvers for production use.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRunDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRunOptimization} variant="contained" disabled={optimizing}>
            {optimizing ? 'Running...' : 'Run Optimization'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Solver Info Dialog */}
      <Dialog open={infoDialogOpen} onClose={() => setInfoDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedSolver?.type} - {selectedSolver?.name}
        </DialogTitle>
        <DialogContent>
          {selectedSolver && (
            <Box>
              <Typography variant="body1" paragraph>
                {selectedSolver.description}
              </Typography>
              
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Best For:
              </Typography>
              <Typography variant="body2" paragraph>
                {selectedSolver.best_for}
              </Typography>
              
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Performance:
              </Typography>
              <Typography variant="body2" paragraph>
                {selectedSolver.performance}
              </Typography>
              
              {selectedSolver.note && (
                <>
                  <Typography variant="subtitle2" color="warning.main" gutterBottom>
                    Note:
                  </Typography>
                  <Typography variant="body2" paragraph>
                    {selectedSolver.note}
                  </Typography>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Add Item Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Item to Proposal</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2, mt: 1 }}>
            Add a new item to this proposal. You'll configure the details in the next step.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddDecision} variant="contained" color="primary">
            Continue
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Decision Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedDecision && !selectedDecision.item_code ? 'Add New Item' : 'Edit Decision'}
        </DialogTitle>
        <DialogContent>
          {selectedDecision && (
            <>
              <Typography variant="body2" color="text.secondary" paragraph sx={{ mt: 2 }}>
                {selectedDecision.item_code ? 'Modify the decision details below.' : 'Configure the new item details.'}
              </Typography>
              
              <TextField
                margin="dense"
                label={t('optimization.itemCode')}
                fullWidth
                variant="outlined"
                value={selectedDecision.item_code}
                onChange={(e) => setSelectedDecision({
                  ...selectedDecision!,
                  item_code: e.target.value
                })}
                sx={{ mb: 2 }}
              />

              <TextField
                margin="dense"
                label="Item Name"
                fullWidth
                variant="outlined"
                value={selectedDecision.item_name}
                onChange={(e) => setSelectedDecision({
                  ...selectedDecision!,
                  item_name: e.target.value
                })}
                sx={{ mb: 2 }}
              />
              
              <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
                <InputLabel>Procurement Option</InputLabel>
                <Select
                  value={selectedDecision.procurement_option_id}
                  label="Procurement Option"
                  onChange={(e) => {
                    const option = procurementOptions.find(o => o.id === Number(e.target.value));
                    if (option) {
                      setSelectedDecision({
                        ...selectedDecision,
                        procurement_option_id: option.id,
                        supplier_name: option.supplier_name,
                        unit_cost: option.base_cost,
                        final_cost: option.base_cost * selectedDecision.quantity,
                      });
                    }
                  }}
                >
                  {/* Filter procurement options to show only those for the current item code */}
                  {procurementOptions
                    .filter(option => option.item_code === selectedDecision.item_code)
                    .map(option => (
                      <MenuItem key={option.id} value={option.id}>
                        {option.supplier_name} - {formatCurrency(option.base_cost)} (Lead: {option.lomc_lead_time} periods)
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>

              <TextField
                margin="dense"
                label="Quantity"
                type="number"
                fullWidth
                variant="outlined"
                value={selectedDecision.quantity}
                onChange={(e) => {
                  const qty = parseInt(e.target.value) || 1;
                  setSelectedDecision({
                    ...selectedDecision!,
                    quantity: qty,
                    final_cost: selectedDecision.unit_cost * qty
                  });
                }}
                sx={{ mb: 2 }}
              />

              <TextField
                margin="dense"
                label="Purchase Date"
                type="date"
                fullWidth
                variant="outlined"
                value={selectedDecision.purchase_date}
                onChange={(e) => setSelectedDecision({
                  ...selectedDecision!,
                  purchase_date: e.target.value
                })}
                InputLabelProps={{ shrink: true }}
                sx={{ mb: 2 }}
              />

              <TextField
                margin="dense"
                label="Delivery Date"
                type="date"
                fullWidth
                variant="outlined"
                value={selectedDecision.delivery_date}
                onChange={(e) => setSelectedDecision({
                  ...selectedDecision!,
                  delivery_date: e.target.value
                })}
                InputLabelProps={{ shrink: true }}
                sx={{ mb: 2 }}
              />

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2" fontWeight="medium">
                  Total Cost: {formatCurrency(selectedDecision.final_cost)}
                </Typography>
              </Alert>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSaveAddedDecision} 
            variant="contained" 
            color={selectedDecision && !selectedDecision.item_code ? "success" : "warning"}
          >
            {selectedDecision && !selectedDecision.item_code ? 'Add Item' : 'Save Changes'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Optimization Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Optimization Results</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Are you sure you want to delete these optimization results?
          </Typography>
          <Alert severity="warning">
            <Typography variant="body2">
              This will delete all proposals and associated data. Any unsaved changes will be lost.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleDeleteOptimization} 
            variant="contained" 
            color="error"
            disabled={saving}
          >
            {saving ? 'Deleting...' : 'Delete Results'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Finalize Decisions Dialog */}
      <Dialog open={finalizeDialogOpen} onClose={() => setFinalizeDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Finalize & Lock Decisions</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Finalize and lock {savedDecisionIds.length} decisions from this proposal?
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>What happens when you finalize:</strong>
            </Typography>
            <ul style={{ marginTop: 8, marginBottom: 0 }}>
              <li>Decisions are marked as "LOCKED"</li>
              <li>They will NOT be included in future optimization runs</li>
              <li>Cash flow events are confirmed</li>
              <li>Can only be unlocked by authorized users</li>
            </ul>
          </Alert>
          <Alert severity="warning">
            <Typography variant="body2">
              <strong>Important:</strong> Only finalize decisions you're committed to executing.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFinalizeDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleFinalizeProposal} 
            variant="contained" 
            color="primary"
            disabled={saving}
            startIcon={<LockIcon />}
          >
            {saving ? 'Finalizing...' : 'Finalize & Lock'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Previous Runs Dialog */}
      <Dialog open={previousRunsDialogOpen} onClose={() => setPreviousRunsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Previous Optimization Runs</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph sx={{ mt: 1 }}>
            View and analyze previous optimization runs
          </Typography>
          
          {previousRuns.length === 0 ? (
            <Alert severity="info">No previous optimization runs found</Alert>
          ) : (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Run Date</TableCell>
                    <TableCell>Solver</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Items</TableCell>
                    <TableCell align="right">Total Cost</TableCell>
                    <TableCell>Proposals</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {previousRuns.map((run) => (
                    <TableRow key={run.run_id} hover>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(run.run_timestamp).toLocaleString()}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          ID: {run.run_id.slice(0, 8)}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={run.request_parameters?.solver_type || 'CP_SAT'} 
                          size="small" 
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={run.status} 
                          color={getStatusColor(run.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">{run.results_count}</TableCell>
                      <TableCell align="right">
                        {formatCurrency(run.total_cost)}
                      </TableCell>
                      <TableCell>
                        {run.request_parameters?.proposals_count || 1} proposal(s)
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Note:</strong> Each optimization run is automatically saved to the database.
              You can view decisions from these runs in the "Finalized Decisions" page.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviousRunsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      </>
      )}
    </Box>
  );
};

export default OptimizationPageEnhanced;
