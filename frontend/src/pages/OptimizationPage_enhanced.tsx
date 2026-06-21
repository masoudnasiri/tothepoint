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
  Divider,
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
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';
import { RivarPageHeader } from '../components/ui/RivarPageHeader.tsx';
import { formatCurrencyAmount } from '../utils/currencyFormat.ts';

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
  project_item_id?: number; // Add project_item_id to identify specific project item
}

interface OptimizationProposal {
  proposal_name: string;
  strategy_type: string;
  total_cost: number;
  weighted_cost: number;
  total_purchase_cost_irr?: number;
  status: string;
  items_count: number;
  decisions: OptimizationDecision[];
  summary_notes?: string;
  excluded_items_count?: number;
  excluded_items?: Array<{ reason: string; summary?: string }>;
  budget_summary?: {
    used_budget_irr?: number;
    remaining_budget_irr?: number;
    excluded_items_count?: number;
    unmet_demand_items?: number;
  };
  financial_analysis?: {
    scenario: string;
    budget_mode: string;
    budget_required_irr: number;
    budget_available_irr: number;
    surplus_or_shortage_irr: number;
    budget_status: string;
    budget_required_by_currency: Record<string, number>;
    budget_available_by_currency: Record<string, number>;
    periods: Array<{
      period: string;
      required_irr: number;
      available_irr: number;
      gap_irr: number;
      status: string;
    }>;
    recommendations: string[];
    warnings: string[];
    narrative_report?: string;
    trace_lines?: Array<Record<string, any>>;
    reconciliation?: {
      differences?: string[];
      reasons?: string[];
      [key: string]: any;
    };
    total_purchase_cost_irr?: number;
    weighted_objective_cost_irr?: number | null;
  };
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
  error_code?: string;
  diagnostics?: Record<string, any>;
}

export const OptimizationPageEnhanced: React.FC = () => {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  
  // Locale-aware date formatter
  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDate = useMemo(() => (dateString: string | Date) => {
    if (!dateString || dateString === 'Invalid Date' || dateString === 'null' || dateString === 'undefined') {
      return t('optimization.notSet');
    }
    try {
      const dateStr = typeof dateString === 'string' ? dateString : dateString.toISOString();
      const d = isFa ? jalaliParseISO(dateStr) : gregorianParseISO(dateStr);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd') : gregorianFormat(d, 'yyyy-MM-dd');
    } catch {
      const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      return date.toLocaleDateString();
    }
  }, [isFa]);
  
  const formatDisplayDateTime = useMemo(() => (dateString: string) => {
    if (!dateString) return '-';
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd HH:mm') : gregorianFormat(d, 'yyyy-MM-dd HH:mm');
    } catch {
      return new Date(dateString).toLocaleString();
    }
  }, [isFa]);
  
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
  const [currentItemOptions, setCurrentItemOptions] = useState<any[]>([]);
  const [budgetDecisionDialogOpen, setBudgetDecisionDialogOpen] = useState(false);
  const [budgetPrecheck, setBudgetPrecheck] = useState<any | null>(null);
  
  const [optimizationConfig, setOptimizationConfig] = useState({
    max_time_slots: 60,  // Increased from 12 to 60 to accommodate all delivery dates (up to 60 days)
    time_limit_seconds: 300,
    solver_type: 'CP_SAT',
    generate_multiple_proposals: true,
    strategies: [] as string[],
  });

  useEffect(() => {
    fetchSolverInfo();
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
        
        setSuccess(
          t('optimization.loadedExistingProposals', {
            proposals: proposals.length,
            items: proposedDecisions.length,
          })
        );
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
      setError(formatApiError(err, t('optimization.failedToLoadSolverInfo')));
    } finally {
      setLoading(false);
    }
  };


  const executeOptimizationWithBudgetMode = async (
    budgetMode: 'constrained' | 'allow_shortage',
    precheckData?: any
  ) => {
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
          require_all_items: false,
          budget_mode: budgetMode,
          budget_scenario: 'minimum_feasible',
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
        const shortage = precheckData?.surplus_or_shortage_irr ?? 0;
        const shortageNote =
          shortage < 0
            ? ` | ${t('optimization.shortageDetectedBeforeRun')}: ${formatCurrencyAmount(Math.abs(shortage), 'IRR', i18n.language || 'en-US')}`
            : '';
        setSuccess(
          `${t('optimization.optimizationCompleted')} ${t('optimization.generatedProposalCount', { count: response.data.proposals.length })}. ` +
          `${t('optimization.bestCostLabel')}: ${formatCurrencyAmount(response.data.total_cost, 'IRR', i18n.language || 'en-US')}` +
          shortageNote
        );
      } else {
        console.log('[ENHANCED OPTIMIZATION] FAILED! Setting error message');
        const diagnostics = response.data?.diagnostics || {};
        const missingCandidates = (diagnostics.items_missing_candidates || []).length;
        const missingCoverage = (diagnostics.items_missing_coverage || []).length;
        const filteredByBudget = diagnostics.items_filtered_by_budget || 0;
        const reasonParts = [
          missingCandidates > 0 ? `${missingCandidates} item(s) missing candidates` : '',
          missingCoverage > 0 ? `${missingCoverage} item(s) missing dated/covered candidates` : '',
          filteredByBudget > 0 ? `${filteredByBudget} item(s) filtered by budget` : '',
        ].filter(Boolean);
        const baseMessage = response.data?.message || 'No feasible solution was generated.';
        const modeNote =
          budgetMode === 'allow_shortage'
            ? ` ${t('optimization.allowShortageNotBlockedNote')}`
            : '';
        const reasonText = reasonParts.length > 0 ? ` Diagnostics: ${reasonParts.join(' | ')}.` : '';
        setError(`${t('optimization.optimizationFailedPrefix')}: ${baseMessage}${modeNote}${reasonText}`);
      }
    } catch (err: any) {
      console.error('[ENHANCED OPTIMIZATION] ERROR:', err);
      console.error('[ENHANCED OPTIMIZATION] Error response:', err.response?.data);
      setError(formatApiError(err, t('optimization.optimizationFailedPrefix')));
    } finally {
      setOptimizing(false);
    }
  };

  const handleRunOptimization = async () => {
    setError('');
    setSuccess('');
    setRunDialogOpen(false);
    try {
      const precheckResponse = await financeAPI.getOptimizationBudgetAnalysis({
        scenario: 'minimum_feasible',
        budget_mode: 'analysis_only',
      });
      const precheck = precheckResponse.data;
      setBudgetPrecheck(precheck);
      if ((precheck?.surplus_or_shortage_irr ?? 0) < 0) {
        setBudgetDecisionDialogOpen(true);
        return;
      }

      await executeOptimizationWithBudgetMode('constrained', precheck);
    } catch (err: any) {
      setError(formatApiError(err, t('optimization.failedToRunBudgetPrecheck')));
    }
  };

  const handleShowSolverInfo = (solver: SolverInfo) => {
    setSelectedSolver(solver);
    setInfoDialogOpen(true);
  };

  const handleEditDecision = async (decision: OptimizationDecision) => {
    setSelectedDecision(decision);
    
    // Load procurement options for this specific project item
    if (decision.project_item_id) {
      try {
        const response = await procurementAPI.listByProjectItem(decision.project_item_id);
        setCurrentItemOptions(response.data);
      } catch (err: any) {
        console.error('Failed to load procurement options for project item:', err);
        setCurrentItemOptions([]);
      }
    } else {
      setCurrentItemOptions([]);
    }
    
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
      setSuccess(t('optimization.decisionUpdatedLocally'));
    }
  };

  const handleRemoveDecision = (decision: OptimizationDecision) => {
    if (window.confirm(`Remove ${decision.item_code} from this proposal?`)) {
      const key = `${decision.project_id}_${decision.item_code}`;
      setRemovedDecisions(new Set([...removedDecisions, key]));
      setSuccess(t('optimization.decisionRemovedLocally'));
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
      procurement_option_id: 0,
      supplier_name: '',
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
      setSuccess(t('optimization.decisionAddedLocally'));
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
      setSuccess(t('optimization.resultsDeletedSuccessfully'));
    } catch (err: any) {
      setError(formatApiError(err, t('optimization.failedToDeleteResults')));
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
          project_item_id: d.project_item_id, // Include project_item_id for accurate item identification
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
      console.log('Decisions length:', decisions.length);
      console.log('Decisions data:', decisions);

      // Validate data before sending
      if (!lastRun?.run_id) {
        throw new Error(t('optimization.noOptimizationRunId'));
      }
      
      if (decisions.length === 0) {
        throw new Error(t('optimization.noDecisionsToSave'));
      }

      // Call the save-proposal endpoint
      const response = await decisionsAPI.saveProposal(proposalData);
      
      setSuccess(
        t('optimization.proposalSavedWithCount', {
          proposalName: proposal.proposal_name,
          count: decisions.length,
        })
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
      setError(formatApiError(err, t('optimization.failedToSaveProposal')));
    } finally {
      setSaving(false);
    }
  };

  const handleFinalizeProposal = async () => {
    if (savedDecisionIds.length === 0) {
      setError(t('optimization.noDecisionsToFinalize'));
      return;
    }

    try {
      setSaving(true);
      setError('');
      
      const response = await decisionsAPI.finalize({
        decision_ids: savedDecisionIds,
        finalize_all: false
      });
      
      setSuccess(t('optimization.successfullyLockedDecisions', { count: response.data.finalized_count }));
      setFinalizeDialogOpen(false);
      setSavedDecisionIds([]);
      
      // Refresh existing proposals to remove finalized ones
      await fetchExistingProposals();
      
    } catch (err: any) {
      setError(formatApiError(err, t('optimization.failedToFinalizeDecisions')));
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (value: number) => {
    return formatCurrencyAmount(value, 'IRR', i18n.language || 'en-US');
  };

  const formatDate = (dateString: string) => {
    return formatDisplayDate(dateString);
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

  const getStrategyLabel = (strategyType: string) => {
    switch (strategyType) {
      case 'LOWEST_COST':
        return t('optimization.strategyLowestCost');
      case 'BALANCED':
        return t('optimization.strategyBalanced');
      case 'SMOOTH_CASHFLOW':
        return t('optimization.strategySmoothCashflow');
      case 'PRIORITY_WEIGHTED':
        return t('optimization.strategyPriorityWeighted');
      case 'FAST_DELIVERY':
        return t('optimization.strategyFastDelivery');
      default:
        return strategyType;
    }
  };

  const selectedProposal = lastRun?.proposals[selectedProposalIndex];
  const hasLocalChanges =
    Object.keys(editedDecisions).length > 0 || removedDecisions.size > 0 || addedDecisions.length > 0;
  const effectiveSelectedDecisions = selectedProposal
    ? selectedProposal.decisions
        .filter((decision) => !removedDecisions.has(`${decision.project_id}_${decision.item_code}`))
        .map((decision) => editedDecisions[`${decision.project_id}_${decision.item_code}`] || decision)
        .concat(addedDecisions)
    : [];
  const effectiveSelectedItemsCount = effectiveSelectedDecisions.length;
  const effectiveSelectedTotalCost = effectiveSelectedDecisions.reduce(
    (sum, decision) => sum + Number(decision.final_cost || 0),
    0
  );
  const getDisplayProposalCost = (proposal: OptimizationProposal, index: number) =>
    index === selectedProposalIndex && selectedProposal
      ? Number(
          selectedProposal.financial_analysis?.total_purchase_cost_irr ??
          selectedProposal.total_purchase_cost_irr ??
          effectiveSelectedTotalCost
        )
      : Number(
          proposal.financial_analysis?.total_purchase_cost_irr ??
          proposal.total_purchase_cost_irr ??
          proposal.total_cost
        );

  const traceByOption = useMemo(() => {
    const map = new Map<number, any>();
    const lines = selectedProposal?.financial_analysis?.trace_lines || [];
    for (const line of lines) {
      const optionId = Number(line?.selected_candidate_id || 0);
      if (!optionId) continue;
      const existing = map.get(optionId) || {
        currency: line.currency || 'IRR',
        exchange_rate_to_irr: Number(line.exchange_rate_to_irr || 1),
        quantity: Number(line.quantity || 0),
        unit_price_original: Number(line.unit_price || 0),
        total_original: 0,
        irr_equivalent: 0,
        payment_periods: new Set<string>(),
      };
      existing.total_original += Number(line.payment_amount_original ?? line.total_original ?? 0);
      existing.irr_equivalent += Number(line.payment_amount_irr ?? line.total_irr ?? 0);
      if (line.payment_period) {
        existing.payment_periods.add(String(line.payment_period));
      }
      map.set(optionId, existing);
    }
    return map;
  }, [selectedProposal?.financial_analysis?.trace_lines]);

  const selectedIrrEquivalentSum = useMemo(() => {
    let total = 0;
    traceByOption.forEach((value) => {
      total += Number(value.irr_equivalent || 0);
    });
    return total;
  }, [traceByOption]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3} flexWrap="wrap" gap={2}>
        <Box>
          <RivarPageHeader title={t('optimization.title')} subtitle={t('optimization.subtitle')} />
        </Box>
        <Box display="flex" gap={2}>
          {previousRuns.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<AssessmentIcon />}
              onClick={() => setPreviousRunsDialogOpen(true)}
              disabled={optimizing}
            >
              {t('optimization.previousRuns')} ({previousRuns.length})
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
              {t('optimization.deleteResults')}
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
              {optimizing ? t('optimization.running') : t('optimization.runOptimization')}
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
        <BudgetAnalysis runId={lastRun?.run_id} />
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
              {t('optimization.runningWithSolver', {
                solver: optimizationConfig.solver_type,
                mode: optimizationConfig.generate_multiple_proposals
                  ? t('optimization.multipleStrategies')
                  : t('optimization.singleStrategy'),
              })}
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

      {lastRun && (lastRun.status === 'INFEASIBLE' || lastRun.status === 'ERROR') && lastRun.diagnostics && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
            {t('optimization.optimizationDiagnostics')}
          </Typography>
          <Typography variant="body2">
            Mode: {String(lastRun.diagnostics.budget_mode || '-')} | Solver status: {String(lastRun.diagnostics.solver_status || '-')}
          </Typography>
          <Typography variant="body2">
            Missing candidates: {(lastRun.diagnostics.items_missing_candidates || []).length} | Missing coverage/dates: {(lastRun.diagnostics.items_missing_coverage || []).length}
          </Typography>
          <Typography variant="body2">
            Budget constraints enabled: {lastRun.diagnostics.budget_constraints_enabled ? 'Yes' : 'No'} | Filtered by budget: {Number(lastRun.diagnostics.items_filtered_by_budget || 0)}
          </Typography>
        </Alert>
      )}

      {/* Solver Information Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
              {t('optimization.availableSolvers')}
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
              {t('optimization.optimizationResults')}
            </Typography>
            
            {/* Summary Statistics */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6} md={2}>
                <Paper sx={{ p: 2, bgcolor: 'success.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('optimization.status')}
                  </Typography>
                  <Chip 
                    label={t(`optimization.${lastRun.status.toLowerCase()}`)} 
                    color={getStatusColor(lastRun.status) as any}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <Paper sx={{ p: 2, bgcolor: 'primary.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('optimization.selectedItemsCount')}
                  </Typography>
                  <Typography variant="h6">
                    {selectedProposal?.items_count ?? selectedProposal?.decisions?.length ?? 0}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <Paper sx={{ p: 2, bgcolor: 'info.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('optimization.totalPurchaseCost')}
                  </Typography>
                  <Typography variant="h6">
                    {formatCurrencyAmount(
                      Number(
                        selectedProposal?.financial_analysis?.total_purchase_cost_irr ??
                        selectedProposal?.total_purchase_cost_irr ??
                        lastRun.total_cost
                      ),
                      'IRR',
                      i18n.language || 'en-US'
                    )}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <Paper sx={{ p: 2, bgcolor: 'warning.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('optimization.weightedObjectiveCost')}
                  </Typography>
                  <Typography variant="h6">
                    {formatCurrencyAmount(
                      Number(
                        selectedProposal?.financial_analysis?.weighted_objective_cost_irr ??
                        selectedProposal?.weighted_cost ??
                        0
                      ),
                      'IRR',
                      i18n.language || 'en-US'
                    )}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {t('optimization.weightedObjectiveHint')}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <Paper sx={{ p: 2, bgcolor: 'warning.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('optimization.proposalsGenerated')}
                  </Typography>
                  <Typography variant="h6">
                    {lastRun.proposals.length}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <Paper sx={{ p: 2, bgcolor: 'secondary.light' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('optimization.executionTime')}
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
                            {getStrategyLabel(proposal.strategy_type)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatCurrency(getDisplayProposalCost(proposal, index))}
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
                    {hasLocalChanges && (
                      <Chip 
                        label={t('optimization.hasLocalChanges')}
                        color="warning"
                        size="small"
                      />
                    )}
                    <Chip 
                      label={`${effectiveSelectedItemsCount} ${t('optimization.items')}`}
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
                        {t('optimization.addItem')}
                      </Button>
                    )}
                  </Box>
                </Box>

                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12} sm={6}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        {t('optimization.totalPurchaseCost')}
                      </Typography>
                      <Typography variant="h5">
                        {formatCurrency(
                          selectedProposal.financial_analysis?.total_purchase_cost_irr
                            ?? selectedProposal.total_purchase_cost_irr
                            ?? effectiveSelectedTotalCost
                        )}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        {t('optimization.weightedObjectiveCost')}
                      </Typography>
                      <Typography variant="h5">
                        {formatCurrency(selectedProposal.weighted_cost)}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                {selectedProposal.financial_analysis && (
                  <Accordion sx={{ mb: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" width="100%">
                        <Typography variant="subtitle1" fontWeight="bold">
                          {t('optimization.viewFinancialAnalysis')}
                        </Typography>
                        <Chip
                          label={selectedProposal.financial_analysis.budget_status}
                          color={
                            selectedProposal.financial_analysis.budget_status === 'OK'
                              ? 'success'
                              : selectedProposal.financial_analysis.budget_status === 'WARNING'
                              ? 'warning'
                              : 'error'
                          }
                          size="small"
                        />
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      {hasLocalChanges && (
                        <Alert severity="info" sx={{ mb: 2 }}>
                          {t('optimization.localChangesFinancialNote')}
                        </Alert>
                      )}
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Paper sx={{ p: 2, height: '100%' }}>
                            <Typography variant="body2" color="text.secondary">
                              {t('optimization.totalPurchaseCost')}
                            </Typography>
                            <Typography variant="h6">
                              {formatCurrencyAmount(
                                selectedProposal.financial_analysis.total_purchase_cost_irr
                                  ?? selectedProposal.financial_analysis.budget_required_irr,
                                'IRR',
                                i18n.language || 'en-US'
                              )}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                              {t('optimization.weightedObjectiveCost')}
                            </Typography>
                            <Typography variant="h6">
                              {formatCurrencyAmount(
                                selectedProposal.financial_analysis.weighted_objective_cost_irr
                                  ?? selectedProposal.weighted_cost
                                  ?? 0,
                                'IRR',
                                i18n.language || 'en-US'
                              )}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                              {t('optimization.requiredBudgetIrr')}
                            </Typography>
                            <Typography variant="h6">
                              {formatCurrencyAmount(
                                selectedProposal.financial_analysis.budget_required_irr,
                                'IRR',
                                i18n.language || 'en-US'
                              )}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                              {t('optimization.availableIrr')}
                            </Typography>
                            <Typography variant="h6">
                              {formatCurrencyAmount(
                                selectedProposal.financial_analysis.budget_available_irr,
                                'IRR',
                                i18n.language || 'en-US'
                              )}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                              {t('optimization.surplusShortageIrr')}
                            </Typography>
                            <Typography
                              variant="h6"
                              color={
                                selectedProposal.financial_analysis.surplus_or_shortage_irr >= 0
                                  ? 'success.main'
                                  : 'error.main'
                              }
                            >
                              {formatCurrencyAmount(
                                Math.abs(selectedProposal.financial_analysis.surplus_or_shortage_irr),
                                'IRR',
                                i18n.language || 'en-US'
                              )}
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Paper sx={{ p: 2, height: '100%' }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              {t('optimization.requiredBudgetByCurrency')}
                            </Typography>
                            {Object.entries(selectedProposal.financial_analysis.budget_required_by_currency || {}).map(
                              ([currency, amount]) => (
                                <Typography key={currency} variant="body2">
                                  {currency}: {formatCurrencyAmount(amount, currency, i18n.language || 'en-US')}
                                </Typography>
                              )
                            )}
                            <Divider sx={{ my: 1 }} />
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              {t('optimization.availableBudgetByCurrency')}
                            </Typography>
                            {Object.entries(selectedProposal.financial_analysis.budget_available_by_currency || {}).map(
                              ([currency, amount]) => (
                                <Typography key={currency} variant="body2">
                                  {currency}: {formatCurrencyAmount(amount, currency, i18n.language || 'en-US')}
                                </Typography>
                              )
                            )}
                          </Paper>
                        </Grid>
                        {(selectedProposal.financial_analysis.reconciliation?.differences || []).length > 0 && (
                          <Grid item xs={12}>
                            <Alert severity="warning">
                              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                {t('optimization.financialTotalsNeedReview')}
                              </Typography>
                              <Typography variant="body2" sx={{ mt: 0.5 }}>
                                {t('optimization.financialTotalsNeedReviewExplain')}
                              </Typography>
                            </Alert>
                          </Grid>
                        )}
                        {selectedProposal.financial_analysis.narrative_report && (
                          <Grid item xs={12}>
                            <Alert
                              severity={
                                selectedProposal.financial_analysis.budget_status === 'OK'
                                  ? 'success'
                                  : 'warning'
                              }
                            >
                              {selectedProposal.financial_analysis.narrative_report}
                            </Alert>
                          </Grid>
                        )}
                        {selectedProposal.budget_summary && (
                          <Grid item xs={12}>
                            <Alert severity="info">
                              {t('optimization.usedBudget')}:{' '}
                              {formatCurrencyAmount(
                                selectedProposal.budget_summary.used_budget_irr || 0,
                                'IRR',
                                i18n.language || 'en-US'
                              )}{' '}
                              | {t('optimization.remainingBudget')}:{' '}
                              {formatCurrencyAmount(
                                selectedProposal.budget_summary.remaining_budget_irr || 0,
                                'IRR',
                                i18n.language || 'en-US'
                              )}{' '}
                              | {t('optimization.excludedItems')}: {selectedProposal.budget_summary.excluded_items_count || 0}
                            </Alert>
                          </Grid>
                        )}
                        <Grid item xs={12}>
                          <Accordion>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                              <Typography variant="subtitle2">
                                {t('optimization.technicalFinancialTrace')}
                              </Typography>
                            </AccordionSummary>
                            <AccordionDetails>
                              {(selectedProposal.financial_analysis.reconciliation?.reasons || []).length > 0 && (
                                <Box sx={{ mb: 2 }}>
                                  <Typography variant="body2" fontWeight={600}>
                                    {t('optimization.reconciliationReasons')}
                                  </Typography>
                                  {(selectedProposal.financial_analysis.reconciliation?.reasons || []).map((reason, idx) => (
                                    <Typography key={`reason-${idx}`} variant="body2" color="text.secondary">
                                      • {reason}
                                    </Typography>
                                  ))}
                                </Box>
                              )}
                              {(selectedProposal.financial_analysis.reconciliation?.differences || []).length > 0 && (
                                <Box sx={{ mb: 2 }}>
                                  <Typography variant="body2" fontWeight={600}>
                                    {t('optimization.rawReconciliationDifferences')}
                                  </Typography>
                                  {(selectedProposal.financial_analysis.reconciliation?.differences || []).slice(0, 10).map((diff, idx) => (
                                    <Typography key={`diff-${idx}`} variant="body2" color="text.secondary">
                                      • {diff}
                                    </Typography>
                                  ))}
                                </Box>
                              )}
                              {(selectedProposal.financial_analysis.trace_lines || []).length > 0 && (
                                <TableContainer component={Paper} variant="outlined">
                                  <Table size="small">
                                    <TableHead>
                                      <TableRow>
                                        <TableCell>{t('optimization.itemCode')}</TableCell>
                                        <TableCell>{t('optimization.currency')}</TableCell>
                                        <TableCell align="right">{t('optimization.totalOriginal')}</TableCell>
                                        <TableCell align="right">{t('optimization.exchangeRate')}</TableCell>
                                        <TableCell align="right">{t('optimization.irrEquivalent')}</TableCell>
                                        <TableCell>{t('optimization.paymentPeriod')}</TableCell>
                                      </TableRow>
                                    </TableHead>
                                    <TableBody>
                                      {(selectedProposal.financial_analysis.trace_lines || []).slice(0, 20).map((line, idx) => (
                                        <TableRow key={`trace-${idx}`}>
                                          <TableCell>{String(line.item_code || '-')}</TableCell>
                                          <TableCell>{String(line.currency || 'IRR')}</TableCell>
                                          <TableCell align="right">
                                            {formatCurrencyAmount(Number(line.payment_amount_original ?? line.total_original ?? 0), String(line.currency || 'IRR'), i18n.language || 'en-US')}
                                          </TableCell>
                                          <TableCell align="right">{Number(line.exchange_rate_to_irr || 1).toLocaleString()}</TableCell>
                                          <TableCell align="right">
                                            {formatCurrencyAmount(Number(line.payment_amount_irr ?? line.total_irr ?? 0), 'IRR', i18n.language || 'en-US')}
                                          </TableCell>
                                          <TableCell>{String(line.payment_period || '-')}</TableCell>
                                        </TableRow>
                                      ))}
                                    </TableBody>
                                  </Table>
                                </TableContainer>
                              )}
                            </AccordionDetails>
                          </Accordion>
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                )}

                {/* Decisions Table */}
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>{t('optimization.project')}</TableCell>
                        <TableCell>{t('optimization.item')}</TableCell>
                        <TableCell>{t('optimization.supplier')}</TableCell>
                        <TableCell>{t('optimization.purchaseDate')}</TableCell>
                        <TableCell>{t('optimization.deliveryDate')}</TableCell>
                        <TableCell align="right">{t('optimization.quantity')}</TableCell>
                        <TableCell align="center">{t('optimization.currency')}</TableCell>
                        <TableCell align="right">{t('optimization.unitCostOriginal')}</TableCell>
                        <TableCell align="right">{t('optimization.totalCostOriginal')}</TableCell>
                        <TableCell align="right">{t('optimization.exchangeRate')}</TableCell>
                        <TableCell align="right">{t('optimization.irrEquivalent')}</TableCell>
                        <TableCell>{t('optimization.payment')}</TableCell>
                        <TableCell align="center">{t('optimization.actions')}</TableCell>
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
                          const traceSummary = traceByOption.get(Number(displayDecision.procurement_option_id || 0));
                          const currency = String(traceSummary?.currency || 'IRR');
                          const unitCostOriginal = Number(traceSummary?.unit_price_original ?? displayDecision.unit_cost ?? 0);
                          const totalCostOriginal = Number(traceSummary?.total_original ?? displayDecision.final_cost ?? 0);
                          const exchangeRate = Number(traceSummary?.exchange_rate_to_irr ?? (currency === 'IRR' ? 1 : 0));
                          const irrEquivalent = Number(traceSummary?.irr_equivalent ?? displayDecision.final_cost ?? 0);
                          const paymentPeriods = traceSummary?.payment_periods
                            ? Array.from(traceSummary.payment_periods).sort().join(', ')
                            : '';
                          
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
                              <TableCell align="center">{currency}</TableCell>
                              <TableCell align="right">{formatCurrencyAmount(unitCostOriginal, currency, i18n.language || 'en-US')}</TableCell>
                              <TableCell align="right">
                                <Typography variant="body2" fontWeight="medium">
                                  {formatCurrencyAmount(totalCostOriginal, currency, i18n.language || 'en-US')}
                                </Typography>
                              </TableCell>
                              <TableCell align="right">
                                {currency === 'IRR' ? '-' : exchangeRate.toLocaleString()}
                              </TableCell>
                              <TableCell align="right">
                                {formatCurrencyAmount(irrEquivalent, 'IRR', i18n.language || 'en-US')}
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={
                                    paymentPeriods
                                      ? `${typeof displayDecision.payment_terms === 'string' ? displayDecision.payment_terms : t('optimization.paymentTerms')} | ${paymentPeriods}`
                                      : (typeof displayDecision.payment_terms === 'string' ? displayDecision.payment_terms : t('optimization.paymentTerms'))
                                  }
                                  size="small"
                                />
                              </TableCell>
                              <TableCell align="center">
                                <IconButton
                                  size="small"
                                  onClick={() => handleEditDecision(displayDecision)}
                                  title={t('optimization.editDecision')}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => handleRemoveDecision(displayDecision)}
                                  title={t('optimization.removeFromProposal')}
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
                          {(() => {
                            const currency = 'IRR';
                            return (
                              <>
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
                          <TableCell align="center">{currency}</TableCell>
                          <TableCell align="right">{formatCurrencyAmount(decision.unit_cost, currency, i18n.language || 'en-US')}</TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight="medium">
                              {formatCurrencyAmount(decision.final_cost, currency, i18n.language || 'en-US')}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">-</TableCell>
                          <TableCell align="right">
                            {formatCurrencyAmount(decision.final_cost, 'IRR', i18n.language || 'en-US')}
                          </TableCell>
                          <TableCell>
                            <Chip label={typeof decision.payment_terms === 'string' ? decision.payment_terms : t('optimization.paymentTerms')} size="small" />
                          </TableCell>
                          <TableCell align="center">
                            <IconButton
                              size="small"
                              onClick={() => handleEditDecision(decision)}
                              title={t('optimization.editDecision')}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => {
                                setAddedDecisions(addedDecisions.filter((_, i) => i !== idx));
                              }}
                              title={t('optimization.remove')}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                              </>
                            );
                          })()}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <Alert severity="info" sx={{ mt: 1.5 }}>
                  <Typography variant="body2">
                    {t('optimization.itemsIrrEquivalentSum')}:{' '}
                    <strong>{formatCurrencyAmount(selectedIrrEquivalentSum, 'IRR', i18n.language || 'en-US')}</strong>
                  </Typography>
                  <Typography variant="body2">
                    {t('optimization.totalPurchaseCost')}:{' '}
                    <strong>
                      {formatCurrencyAmount(
                        Number(
                          selectedProposal.financial_analysis?.total_purchase_cost_irr ??
                          selectedProposal.total_purchase_cost_irr ??
                          effectiveSelectedTotalCost
                        ),
                        'IRR',
                        i18n.language || 'en-US'
                      )}
                    </strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {t('optimization.requiredBudgetDifferenceExplain')}
                  </Typography>
                </Alert>

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
                        {t('optimization.finalizeLockDecisions')}
                      </Button>
                    )}
                    <Button
                      variant="contained"
                      color="success"
                      startIcon={<SaveIcon />}
                      onClick={() => handleSaveProposal(selectedProposal)}
                      disabled={saving}
                    >
                      {saving ? t('optimization.saving') : t('optimization.saveProposalAsDecisions')}
                    </Button>
                  </Box>
                )}
                
                {/* PM users see read-only message */}
                {user?.role === 'pm' && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      <strong>{t('optimization.pmAccessTitle')}</strong> {t('optimization.pmAccessMessage')}
                    </Typography>
                  </Alert>
                )}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Budget Shortage Decision Dialog */}
      <Dialog
        open={budgetDecisionDialogOpen}
        onClose={() => setBudgetDecisionDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t('optimization.budgetShortageDetected')}</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mt: 1, mb: 2 }}>
            {t('optimization.budgetShortageDecisionMessage')}
          </Alert>
          {budgetPrecheck && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">
                  {t('optimization.scenario')}
                </Typography>
                <Typography variant="body1">
                  {budgetPrecheck.scenario === 'minimum_feasible'
                    ? t('optimization.minimumFeasibleBudget')
                    : budgetPrecheck.scenario === 'average_candidate'
                    ? t('optimization.averageCandidateBudget')
                    : budgetPrecheck.scenario === 'worst_case'
                    ? t('optimization.worstCaseBudget')
                    : budgetPrecheck.scenario === 'selected_result' || budgetPrecheck.scenario === 'selected_optimization_result'
                    ? t('optimization.selectedResultBudget')
                    : (budgetPrecheck.scenario || 'minimum_feasible')}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" color="text.secondary">
                  {t('optimization.budgetStatusLabel')}
                </Typography>
                <Typography variant="body1">{budgetPrecheck.budget_status}</Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary">
                  {t('optimization.requiredBudget')}
                </Typography>
                <Typography variant="body1">
                  {formatCurrencyAmount(budgetPrecheck.budget_required_irr || 0, 'IRR', i18n.language || 'en-US')}
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary">
                  {t('optimization.availableBudget')}
                </Typography>
                <Typography variant="body1">
                  {formatCurrencyAmount(budgetPrecheck.budget_available_irr || 0, 'IRR', i18n.language || 'en-US')}
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary">
                  {t('optimization.shortage')}
                </Typography>
                <Typography variant="body1" color="error.main">
                  {formatCurrencyAmount(
                    Math.abs(budgetPrecheck.surplus_or_shortage_irr || 0),
                    'IRR',
                    i18n.language || 'en-US'
                  )}
                </Typography>
              </Grid>
              {budgetPrecheck.narrative_report && (
                <Grid item xs={12}>
                  <Alert severity="info">{budgetPrecheck.narrative_report}</Alert>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'space-between', p: 2 }}>
          <Button
            color="inherit"
            onClick={() => {
              setBudgetDecisionDialogOpen(false);
              setSuccess(t('optimization.optimizationCancelled'));
            }}
          >
            {t('optimization.cancelAndUpdateBudget')}
          </Button>
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              onClick={async () => {
                setBudgetDecisionDialogOpen(false);
                await executeOptimizationWithBudgetMode('constrained', budgetPrecheck);
              }}
              disabled={optimizing}
            >
              {t('optimization.optimizeWithinCurrentBudget')}
            </Button>
            <Button
              variant="contained"
              color="warning"
              onClick={async () => {
                setBudgetDecisionDialogOpen(false);
                await executeOptimizationWithBudgetMode('allow_shortage', budgetPrecheck);
              }}
              disabled={optimizing}
            >
              {t('optimization.optimizeAllWithShortageAnalysis')}
            </Button>
          </Box>
        </DialogActions>
      </Dialog>

      {/* Run Optimization Dialog */}
      <Dialog open={runDialogOpen} onClose={() => setRunDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('optimization.configureAdvancedOptimization')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph sx={{ mt: 2 }}>
            {t('optimization.configureOptimizationHelp')}
          </Typography>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>{t('optimization.solverType')}</InputLabel>
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
            helperText={t('optimization.maxTimeSlotsHelp')}
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
            helperText={t('optimization.timeLimitHelp')}
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
              <InputLabel>{t('optimization.strategies')}</InputLabel>
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
              <strong>{t('optimization.tip')}</strong> {t('optimization.firstRunTip')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRunDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleRunOptimization} variant="contained" disabled={optimizing}>
            {optimizing ? t('optimization.running') : t('optimization.runOptimization')}
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
                {t('optimization.bestFor')}
              </Typography>
              <Typography variant="body2" paragraph>
                {selectedSolver.best_for}
              </Typography>
              
              <Typography variant="subtitle2" color="primary" gutterBottom>
                {t('optimization.performance')}
              </Typography>
              <Typography variant="body2" paragraph>
                {selectedSolver.performance}
              </Typography>
              
              {selectedSolver.note && (
                <>
                  <Typography variant="subtitle2" color="warning.main" gutterBottom>
                    {t('common.note')}:
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
          <Button onClick={() => setInfoDialogOpen(false)}>{t('common.close')}</Button>
        </DialogActions>
      </Dialog>

      {/* Add Item Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('optimization.addItemToProposal')}</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2, mt: 1 }}>
            {t('optimization.addItemHelp')}
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleAddDecision} variant="contained" color="primary">
            {t('optimization.continue')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Decision Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedDecision && !selectedDecision.item_code ? t('optimization.addNewItem') : t('optimization.editDecision')}
        </DialogTitle>
        <DialogContent>
          {selectedDecision && (
            <>
              <Typography variant="body2" color="text.secondary" paragraph sx={{ mt: 2 }}>
                {selectedDecision.item_code ? t('optimization.modifyDecisionDetails') : t('optimization.configureNewItemDetails')}
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
                label={t('optimization.itemName')}
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
                <InputLabel>{t('optimization.procurementOption')}</InputLabel>
                <Select
                  value={selectedDecision.procurement_option_id}
                  label={t('optimization.procurementOption')}
                  onChange={(e) => {
                    const option = currentItemOptions.find(o => o.id === Number(e.target.value));
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
                  {/* Show procurement options for the current project item */}
                  {currentItemOptions.map(option => (
                    <MenuItem key={option.id} value={option.id}>
                      {option.supplier_name} - {formatCurrency(option.base_cost)} ({t('optimization.leadPeriods', { periods: option.lomc_lead_time })})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                margin="dense"
                label={t('optimization.quantity')}
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
                label={t('optimization.purchaseDate')}
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
                label={t('optimization.deliveryDate')}
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
                  {t('optimization.totalCost')}: {formatCurrency(selectedDecision.final_cost)}
                </Typography>
              </Alert>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleSaveAddedDecision} 
            variant="contained" 
            color={selectedDecision && !selectedDecision.item_code ? "success" : "warning"}
          >
            {selectedDecision && !selectedDecision.item_code ? t('optimization.addItem') : t('optimization.saveChanges')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Optimization Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('optimization.deleteOptimizationResults')}</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            {t('optimization.confirmDeleteResults')}
          </Typography>
          <Alert severity="warning">
            <Typography variant="body2">
              {t('optimization.deleteResultsWarning')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleDeleteOptimization} 
            variant="contained" 
            color="error"
            disabled={saving}
          >
            {saving ? t('optimization.deleting') : t('optimization.deleteResults')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Finalize Decisions Dialog */}
      <Dialog open={finalizeDialogOpen} onClose={() => setFinalizeDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('optimization.finalizeLockDecisions')}</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            {t('optimization.finalizeCountQuestion', { count: savedDecisionIds.length })}
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>{t('optimization.whatHappensWhenFinalize')}</strong>
            </Typography>
            <ul style={{ marginTop: 8, marginBottom: 0 }}>
              <li>{t('optimization.finalizeEffectLocked')}</li>
              <li>{t('optimization.finalizeEffectNoFutureRuns')}</li>
              <li>{t('optimization.finalizeEffectCashflow')}</li>
              <li>{t('optimization.finalizeEffectAuthorizedUnlock')}</li>
            </ul>
          </Alert>
          <Alert severity="warning">
            <Typography variant="body2">
              <strong>{t('optimization.important')}:</strong> {t('optimization.finalizeImportantNote')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFinalizeDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button 
            onClick={handleFinalizeProposal} 
            variant="contained" 
            color="primary"
            disabled={saving}
            startIcon={<LockIcon />}
          >
            {saving ? t('optimization.finalizing') : t('optimization.finalizeLock')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Previous Runs Dialog */}
      <Dialog open={previousRunsDialogOpen} onClose={() => setPreviousRunsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('optimization.previousOptimizationRuns')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph sx={{ mt: 1 }}>
            {t('optimization.viewAnalyzePreviousRuns')}
          </Typography>
          
          {previousRuns.length === 0 ? (
            <Alert severity="info">{t('optimization.noPreviousRuns')}</Alert>
          ) : (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('optimization.runDate')}</TableCell>
                    <TableCell>{t('optimization.solver')}</TableCell>
                    <TableCell>{t('optimization.status')}</TableCell>
                    <TableCell align="right">{t('optimization.items')}</TableCell>
                    <TableCell align="right">{t('optimization.totalCost')}</TableCell>
                    <TableCell>{t('optimization.proposals')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {previousRuns.map((run) => (
                    <TableRow key={run.run_id} hover>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDisplayDateTime(run.run_timestamp)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t('optimization.resultId')}: {run.run_id.slice(0, 8)}...
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
                        {t('optimization.generatedProposalCount', { count: run.request_parameters?.proposals_count || 1 })}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>{t('common.note')}:</strong> {t('optimization.previousRunsNote')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviousRunsDialogOpen(false)}>{t('common.close')}</Button>
        </DialogActions>
      </Dialog>
      </>
      )}
    </Box>
  );
};

export default OptimizationPageEnhanced;
