import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  AlertTitle,
  Chip,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import {
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { financeAPI } from '../services/api.ts';
import { useTranslation } from 'react-i18next';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { formatCurrencyAmount } from '../utils/currencyFormat.ts';

interface BudgetAnalysisProps {
  projectIds?: number[];
  startDate?: string;
  endDate?: string;
  runId?: string;
  onAnalysisComplete?: (status: string) => void;
}

interface ScenarioPeriod {
  period: string;
  required_irr: number;
  available_irr: number;
  gap_irr: number;
  status: string;
}

interface ScenarioAnalysisData {
  scenario: string;
  analysis_scope: string;
  optimization_result_id?: string | null;
  budget_status: string;
  budget_required_irr: number;
  budget_available_irr: number;
  surplus_or_shortage_irr: number;
  budget_required_by_currency: Record<string, number>;
  budget_available_by_currency: Record<string, number>;
  surplus_shortage_by_currency?: Record<string, number>;
  periods: ScenarioPeriod[];
  critical_periods?: string[];
  recommendations: string[];
  warnings: string[];
  narrative_report?: string;
  trace_lines?: Array<Record<string, any>>;
  reconciliation?: {
    differences?: string[];
    [key: string]: any;
  };
  total_purchase_cost_irr?: number;
  weighted_objective_cost_irr?: number | null;
  double_count_prevented?: boolean;
}

export const BudgetAnalysis: React.FC<BudgetAnalysisProps> = ({
  projectIds,
  startDate,
  endDate,
  runId,
  onAnalysisComplete,
}) => {
  const { t, i18n } = useTranslation();
  const isFa = i18n.language?.startsWith('fa');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<ScenarioAnalysisData | null>(null);
  const [scenario, setScenario] = useState<string>('minimum_feasible');

  const formatPeriodLabel = useMemo(() => (period: string) => {
    if (!period || period.length !== 7 || !period.match(/^\d{4}-\d{2}$/)) {
      return period;
    }
    try {
      if (isFa) {
        const iso = `${period}-01`;
        return jalaliFormat(jalaliParseISO(iso), 'yyyy/MM');
      }
      return period;
    } catch {
      return period;
    }
  }, [isFa]);

  const fetchBudgetAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        scenario,
        budget_mode: 'analysis_only',
      };
      if (projectIds && projectIds.length > 0) {
        params.project_ids = projectIds.join(',');
      }
      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }
      if ((scenario === 'selected_optimization_result' || scenario === 'selected_result') && runId) {
        params.run_id = runId;
      }
      const response = await financeAPI.getOptimizationBudgetAnalysis(params);
      const data = response.data as ScenarioAnalysisData;
      if (!data.surplus_shortage_by_currency) {
        const currencies = new Set([
          ...Object.keys(data.budget_required_by_currency || {}),
          ...Object.keys(data.budget_available_by_currency || {}),
        ]);
        data.surplus_shortage_by_currency = {};
        currencies.forEach((currency) => {
          data.surplus_shortage_by_currency![currency] =
            (data.budget_available_by_currency?.[currency] || 0) -
            (data.budget_required_by_currency?.[currency] || 0);
        });
      }
      if (!data.critical_periods) {
        data.critical_periods = (data.periods || [])
          .filter((period) => Number(period.gap_irr) < 0)
          .map((period) => period.period);
      }
      setAnalysisData(data);
      if (onAnalysisComplete) {
        onAnalysisComplete(data.budget_status);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('optimization.errorLoadingBudgetAnalysis'));
    } finally {
      setLoading(false);
    }
  }, [scenario, projectIds, startDate, endDate, runId, onAnalysisComplete, t]);

  useEffect(() => {
    fetchBudgetAnalysis();
  }, [fetchBudgetAnalysis]);

  const formatCurrency = (value: number, currency: string) =>
    formatCurrencyAmount(value, currency, i18n.language || 'en-US');

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'OK':
        return <CheckCircleIcon sx={{ color: '#4caf50' }} />;
      case 'WARNING':
        return <WarningIcon sx={{ color: '#ff9800' }} />;
      case 'CRITICAL':
        return <ErrorIcon sx={{ color: '#f44336' }} />;
      default:
        return <InfoIcon />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="320px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        <AlertTitle>{t('optimization.errorLoadingBudgetAnalysis')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!analysisData) {
    return (
      <Alert severity="info">
        <AlertTitle>{t('optimization.noData')}</AlertTitle>
        {t('optimization.noBudgetAnalysisDataAvailable')}
      </Alert>
    );
  }

  const currencies = Array.from(
    new Set([
      ...Object.keys(analysisData.budget_required_by_currency || {}),
      ...Object.keys(analysisData.budget_available_by_currency || {}),
    ]),
  );
  const chartData = (analysisData.periods || []).map((period) => ({
    period: period.period,
    required: Number(period.required_irr || 0),
    available: Number(period.available_irr || 0),
    gap: Number(period.gap_irr || 0),
  }));

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel id="budget-scenario-label">{t('optimization.scenario')}</InputLabel>
                <Select
                  labelId="budget-scenario-label"
                  value={scenario}
                  label={t('optimization.scenario')}
                  onChange={(event) => setScenario(event.target.value)}
                >
                  <MenuItem value="minimum_feasible">{t('optimization.minimumFeasibleBudget')}</MenuItem>
                  <MenuItem value="average_candidate">{t('optimization.averageCandidateBudget')}</MenuItem>
                  <MenuItem value="worst_case">{t('optimization.worstCaseBudget')}</MenuItem>
                  <MenuItem value="selected_optimization_result">{t('optimization.selectedResultBudget')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={8}>
              <Typography variant="body2" color="text.secondary">
                {t('optimization.scenarioCountRule')}
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {t('optimization.scenario')}: <strong>{analysisData.scenario}</strong>
                {analysisData.analysis_scope === 'optimization_result' && analysisData.optimization_result_id
                  ? ` | ${t('optimization.resultId')}: ${analysisData.optimization_result_id}`
                  : ''}
              </Typography>
              {!!analysisData.narrative_report && (
                <Typography variant="body2" sx={{ mt: 1, whiteSpace: 'pre-wrap' }}>
                  {analysisData.narrative_report}
                </Typography>
              )}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={1}>
            <Box display="flex" alignItems="center" gap={1.5}>
              {getStatusIcon(analysisData.budget_status)}
              <Typography variant="h6">
                {t('optimization.budgetAnalysisStatus', { status: analysisData.budget_status })}
              </Typography>
            </Box>
            <Chip
              label={analysisData.budget_status}
              color={
                analysisData.budget_status === 'OK'
                  ? 'success'
                  : analysisData.budget_status === 'WARNING'
                    ? 'warning'
                    : 'error'
              }
            />
          </Box>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {t('optimization.requiredIrr')}: <strong>{formatCurrency(analysisData.budget_required_irr, 'IRR')}</strong> | {t('optimization.availableIrr')}:{' '}
            <strong>{formatCurrency(analysisData.budget_available_irr, 'IRR')}</strong> |{' '}
            {Number(analysisData.surplus_or_shortage_irr) >= 0 ? t('optimization.surplus') : t('optimization.shortage')}:{' '}
            <strong>{formatCurrency(Math.abs(analysisData.surplus_or_shortage_irr), 'IRR')}</strong>
          </Typography>
        </CardContent>
      </Card>

      {(analysisData.reconciliation?.differences || []).length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <AlertTitle>{t('optimization.financialTotalsNeedReview')}</AlertTitle>
          {(analysisData.reconciliation?.differences || []).slice(0, 5).join(' | ')}
        </Alert>
      )}

      {(analysisData.critical_periods || []).length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <AlertTitle>{t('optimization.criticalMonthsDetected')}</AlertTitle>
          {(analysisData.critical_periods || []).map(formatPeriodLabel).join(', ')}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ mb: 3 }}>
        {currencies.map((currency) => {
          const required = Number(analysisData.budget_required_by_currency?.[currency] || 0);
          const available = Number(analysisData.budget_available_by_currency?.[currency] || 0);
          const gap = Number(analysisData.surplus_shortage_by_currency?.[currency] || 0);
          return (
            <Grid item xs={12} md={6} key={currency}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>{currency}</Typography>
                  <Typography variant="body2">{t('optimization.totalNeeded')}</Typography>
                  <Typography variant="h5" sx={{ color: '#1976d2', mb: 1 }}>
                    {formatCurrency(required, currency)}
                  </Typography>
                  <Typography variant="body2">{t('optimization.totalAvailable')}</Typography>
                  <Typography variant="h5" sx={{ color: '#4caf50', mb: 1 }}>
                    {formatCurrency(available, currency)}
                  </Typography>
                  <Typography variant="body2">{t('optimization.gap')}</Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="h5" sx={{ color: gap >= 0 ? '#4caf50' : '#f44336' }}>
                      {formatCurrency(Math.abs(gap), currency)}
                    </Typography>
                    {gap >= 0 ? (
                      <TrendingUpIcon sx={{ color: '#4caf50' }} />
                    ) : (
                      <TrendingDownIcon sx={{ color: '#f44336' }} />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>{t('optimization.budgetGapByPeriod')}</Typography>
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tickFormatter={formatPeriodLabel} />
              <YAxis />
              <Tooltip
                labelFormatter={formatPeriodLabel}
                formatter={(value: number) => formatCurrency(value, 'IRR')}
              />
              <Legend />
              <Bar dataKey="required" fill="#1976d2" name={t('optimization.requiredIrr')} />
              <Bar dataKey="available" fill="#4caf50" name={t('optimization.availableIrr')} />
              <Line dataKey="gap" stroke="#9c27b0" name={t('optimization.surplusShortageIrr')} strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>{t('optimization.detailedPeriodBreakdown')}</Typography>
          {(analysisData.periods || []).map((period) => (
            <Accordion key={period.period}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={1.5}>
                  <Typography sx={{ fontWeight: 600 }}>{formatPeriodLabel(period.period)}</Typography>
                  {Number(period.gap_irr) < 0 && <Chip size="small" color="error" label={t('optimization.critical')} />}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2">
                  {t('optimization.required')}: <strong>{formatCurrency(period.required_irr, 'IRR')}</strong>
                </Typography>
                <Typography variant="body2">
                  {t('optimization.available')}: <strong>{formatCurrency(period.available_irr, 'IRR')}</strong>
                </Typography>
                <Typography variant="body2" sx={{ color: Number(period.gap_irr) >= 0 ? '#4caf50' : '#f44336' }}>
                  {Number(period.gap_irr) >= 0 ? t('optimization.surplus') : t('optimization.shortage')}:{' '}
                  <strong>{formatCurrency(Math.abs(period.gap_irr), 'IRR')}</strong>
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>💡 {t('optimization.recommendationsActions')}</Typography>
          <List>
            {(analysisData.recommendations || []).map((recommendation, index) => (
              <ListItem key={index}>
                <ListItemText primary={recommendation} />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      {(analysisData.warnings || []).length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>{t('optimization.warning')}</Typography>
            <Divider sx={{ mb: 1.5 }} />
            <List>
              {analysisData.warnings.map((warning, idx) => (
                <ListItem key={idx}>
                  <ListItemText primary={warning} />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

