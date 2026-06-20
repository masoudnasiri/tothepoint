import React, { useState, useEffect, useMemo } from 'react';
import {
  Grid,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AccountBalance as AccountBalanceIcon,
  Timeline as TimelineIcon,
  Download as DownloadIcon,
  CalendarToday as ForecastIcon,
  CheckCircle as ActualIcon,
  CompareArrows as CompareIcon,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { useAuth } from '../contexts/AuthContext.tsx';
import { dashboardAPI } from '../services/api.ts';
import { ProjectFilter } from '../components/ProjectFilter.tsx';
import { useTranslation } from 'react-i18next';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat } from 'date-fns';
import { RivarPageHeader } from '../components/ui/RivarPageHeader.tsx';
import { RivarMetricCard } from '../components/ui/RivarMetricCard.tsx';
import { RivarPanel } from '../components/ui/RivarPanel.tsx';
import { RivarEmptyState } from '../components/ui/RivarEmptyState.tsx';
import { rivarTokens } from '../theme/rivarTheme.ts';

interface CashflowDataPoint {
  month: string;
  inflow: number;
  outflow: number;
  budget: number;
  net_flow: number;
  cumulative_balance: number;
}

interface CashflowSummary {
  total_inflow: number;
  total_outflow: number;
  net_position: number;
  peak_balance: number;
  min_balance: number;
  final_balance: number;
}

interface CashflowResponse {
  time_series: CashflowDataPoint[];
  summary: CashflowSummary;
  period_count: number;
}

const EMPTY_SUMMARY: CashflowSummary = {
  total_inflow: 0, total_outflow: 0, net_position: 0,
  peak_balance: 0, min_balance: 0, final_balance: 0,
};

const CHART_COLORS = {
  inflow: rivarTokens.good,
  outflow: rivarTokens.risk,
  budget: '#9c27b0',
  balance: rivarTokens.accent,
  forecast: rivarTokens.accent,
  actual: rivarTokens.good,
};

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const [forecastData, setForecastData] = useState<CashflowResponse | null>(null);
  const [actualData, setActualData] = useState<CashflowResponse | null>(null);
  const [forecastByCurrency, setForecastByCurrency] = useState<{ [key: string]: CashflowResponse }>({});
  const [actualByCurrency, setActualByCurrency] = useState<{ [key: string]: CashflowResponse }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(12);
  const [viewMode, setViewMode] = useState<'forecast' | 'actual' | 'comparison'>('forecast');
  const [currencyDisplayMode, setCurrencyDisplayMode] = useState<'original' | 'unified'>('unified');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);

  const isFa = i18n.language?.startsWith('fa');

  const formatMonthLabel = useMemo(() => (value: string) => {
    if (!isFa) return value;
    try {
      const iso = value.length === 7 ? `${value}-01` : value;
      return jalaliFormat(jalaliParseISO(iso), 'yyyy-MM');
    } catch { return value; }
  }, [isFa]);

  const formatDisplayDate = useMemo(() => (dateString: string | Date) => {
    try {
      const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
      return isFa ? jalaliFormat(date, 'yyyy/MM/dd') : gregorianFormat(date, 'yyyy-MM-dd');
    } catch {
      return typeof dateString === 'string' ? dateString : dateString.toISOString().split('T')[0];
    }
  }, [isFa]);

  useEffect(() => {
    const fetch = async () => {
      try {
        const projectIdsParam = selectedProjects.length > 0 ? selectedProjects.join(',') : undefined;
        const currView = currencyDisplayMode === 'unified' ? 'unified' : 'original';
        const [fRes, aRes] = await Promise.all([
          dashboardAPI.getCashflow({ forecast_type: 'FORECAST', project_ids: projectIdsParam, currency_view: currView }),
          dashboardAPI.getCashflow({ forecast_type: 'ACTUAL',   project_ids: projectIdsParam, currency_view: currView }),
        ]);

        if (fRes.data.view_mode === 'original' && fRes.data.currencies) {
          setForecastByCurrency(fRes.data.currencies);
          setForecastData(fRes.data.currencies['IRR'] || { time_series: [], summary: EMPTY_SUMMARY, period_count: 0 });
        } else {
          setForecastData(fRes.data);
          setForecastByCurrency({});
        }

        if (aRes.data.view_mode === 'original' && aRes.data.currencies) {
          setActualByCurrency(aRes.data.currencies);
          setActualData(aRes.data.currencies['IRR'] || { time_series: [], summary: EMPTY_SUMMARY, period_count: 0 });
        } else {
          setActualData(aRes.data);
          setActualByCurrency({});
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load cash flow data');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [selectedProjects, currencyDisplayMode]);

  const formatCurrency = (value: number, code = 'IRR') => {
    const symbols: Record<string, string> = { USD: '$', EUR: '€', IRR: '﷼', GBP: '£', JPY: '¥' };
    return `${new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: code === 'IRR' ? 0 : 2,
    }).format(value)} ${symbols[code] || code}`;
  };

  const handleExport = async () => {
    try {
      const response = await dashboardAPI.exportCashflow();
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `cashflow_export_${formatDisplayDate(new Date())}.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch { setError('Failed to export cash flow data'); }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={32} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <RivarPageHeader title={t('dashboard.title')} />
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  const isPM = user?.role === 'pm';
  const isProcurement = user?.role === 'procurement';
  const isRestricted = isPM || isProcurement;

  const currentByCurrency =
    viewMode === 'actual' ? actualByCurrency :
    viewMode === 'forecast' ? forecastByCurrency : forecastByCurrency;

  const summary = (
    viewMode === 'forecast' ? forecastData?.summary :
    viewMode === 'actual'   ? actualData?.summary :
    forecastData?.summary
  ) ?? EMPTY_SUMMARY;

  const actualSummary = actualData?.summary ?? EMPTY_SUMMARY;

  const currentData =
    viewMode === 'actual' ? actualData :
    forecastData;

  const isOriginalMulti = currencyDisplayMode === 'original' && Object.keys(currentByCurrency).length > 0;

  return (
    <Box>
      <RivarPageHeader
        title={t('dashboard.title')}
        subtitle={t('dashboard.subtitle')}
        actions={
          <Button variant="outlined" size="small" startIcon={<DownloadIcon />} onClick={handleExport}>
            Export
          </Button>
        }
      />

      {/* Project filter */}
      <RivarPanel title={t('dashboard.filterByProjects')} sx={{ mb: 3 }}>
        <ProjectFilter
          selectedProjects={selectedProjects}
          onChange={setSelectedProjects}
          label={t('dashboard.filterByProjects')}
        />
      </RivarPanel>

      {/* View mode controls */}
      <RivarPanel sx={{ mb: 3 }}>
        <Box
          sx={{
            display: 'flex',
            gap: 3,
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Box>
            <Typography variant="caption" sx={{ display: 'block', fontWeight: 600, mb: 1, color: rivarTokens.ink500, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.6875rem' }}>
              {t('dashboard.viewMode')}
            </Typography>
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(_, v) => v && setViewMode(v)}
              size="small"
              sx={{ '& .MuiToggleButton-root': { px: 1.5, py: 0.75, fontSize: '0.8125rem', fontWeight: 500, textTransform: 'none', border: `1px solid ${rivarTokens.lineStrong}` } }}
            >
              <ToggleButton value="forecast"><ForecastIcon sx={{ fontSize: 15, mr: 0.75 }} />{t('dashboard.forecasted')}</ToggleButton>
              <ToggleButton value="actual"><ActualIcon sx={{ fontSize: 15, mr: 0.75 }} />{t('dashboard.actual')}</ToggleButton>
              <ToggleButton value="comparison"><CompareIcon sx={{ fontSize: 15, mr: 0.75 }} />{t('dashboard.comparison')}</ToggleButton>
            </ToggleButtonGroup>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ display: 'block', fontWeight: 600, mb: 1, color: rivarTokens.ink500, textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.6875rem' }}>
              {t('dashboard.currencyDisplay')}
            </Typography>
            <ToggleButtonGroup
              value={currencyDisplayMode}
              exclusive
              onChange={(_, v) => v && setCurrencyDisplayMode(v)}
              size="small"
              sx={{ '& .MuiToggleButton-root': { px: 1.5, py: 0.75, fontSize: '0.8125rem', fontWeight: 500, textTransform: 'none', border: `1px solid ${rivarTokens.lineStrong}` } }}
            >
              <ToggleButton value="unified"><AccountBalanceIcon sx={{ fontSize: 15, mr: 0.75 }} />{t('dashboard.unified')}</ToggleButton>
              <ToggleButton value="original"><CompareIcon sx={{ fontSize: 15, mr: 0.75 }} />{t('dashboard.originalCurrencies')}</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </Box>
      </RivarPanel>

      {/* ── Metric cards ── */}
      {isPM ? (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={4}>
            <RivarMetricCard label={t('dashboard.totalRevenueInflow')} value={formatCurrency(summary.total_inflow)} sub={t('dashboard.expectedRevenueFromClients')} icon={<TrendingUpIcon />} variant="good" />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <RivarMetricCard label={t('dashboard.inflowEvents')} value={currentData?.period_count?.toString() || '0'} sub={t('dashboard.revenueTransactions')} icon={<TimelineIcon />} variant="accent" />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <RivarPanel>
              <Typography variant="caption" sx={{ color: rivarTokens.ink500, display: 'block', mb: 1 }}>Access Level</Typography>
              <Chip label={t('dashboard.projectManager')} color="primary" size="small" />
              <Typography variant="caption" display="block" sx={{ mt: 1, color: rivarTokens.ink300 }}>Revenue data only</Typography>
            </RivarPanel>
          </Grid>
        </Grid>
      ) : isProcurement ? (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={4}>
            <RivarMetricCard label={t('dashboard.totalPaymentOutflow')} value={formatCurrency(summary.total_outflow)} sub={t('dashboard.paymentsToSuppliers')} icon={<TrendingDownIcon />} variant="risk" />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <RivarMetricCard label={t('dashboard.outflowEvents')} value={currentData?.period_count?.toString() || '0'} sub={t('dashboard.paymentTransactions')} icon={<TimelineIcon />} variant="accent" />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <RivarPanel>
              <Typography variant="caption" sx={{ color: rivarTokens.ink500, display: 'block', mb: 1 }}>Access Level</Typography>
              <Chip label={t('dashboard.procurementSpecialist')} color="secondary" size="small" />
              <Typography variant="caption" display="block" sx={{ mt: 1, color: rivarTokens.ink300 }}>Payment data only</Typography>
            </RivarPanel>
          </Grid>
        </Grid>
      ) : isOriginalMulti ? (
        Object.entries(currentByCurrency).map(([code, data]) => (
          <Box key={code} sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600, color: rivarTokens.ink }}>{code} Summary</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}><RivarMetricCard label={t('dashboard.totalInflow')} value={formatCurrency(data.summary?.total_inflow || 0, code)} icon={<TrendingUpIcon />} variant="good" /></Grid>
              <Grid item xs={12} sm={6} md={3}><RivarMetricCard label={t('dashboard.totalOutflow')} value={formatCurrency(data.summary?.total_outflow || 0, code)} icon={<TrendingDownIcon />} variant="risk" /></Grid>
              <Grid item xs={12} sm={6} md={3}><RivarMetricCard label={t('dashboard.netPosition')} value={formatCurrency(data.summary?.net_position || 0, code)} icon={<AccountBalanceIcon />} variant={(data.summary?.net_position || 0) >= 0 ? 'accent' : 'warn'} /></Grid>
              <Grid item xs={12} sm={6} md={3}><RivarMetricCard label={t('dashboard.finalBalance')} value={formatCurrency(data.summary?.final_balance || 0, code)} icon={<TimelineIcon />} variant="default" /></Grid>
            </Grid>
          </Box>
        ))
      ) : (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}><RivarMetricCard label={t('dashboard.totalInflow')} value={formatCurrency(summary.total_inflow)} sub={t('dashboard.budgetRevenue')} icon={<TrendingUpIcon />} variant="good" /></Grid>
          <Grid item xs={12} sm={6} md={3}><RivarMetricCard label={t('dashboard.totalOutflow')} value={formatCurrency(summary.total_outflow)} sub={t('dashboard.payments')} icon={<TrendingDownIcon />} variant="risk" /></Grid>
          <Grid item xs={12} sm={6} md={3}><RivarMetricCard label={t('dashboard.netPosition')} value={formatCurrency(summary.net_position)} sub={summary.net_position >= 0 ? t('dashboard.positive') : 'Negative'} icon={<AccountBalanceIcon />} variant={summary.net_position >= 0 ? 'accent' : 'warn'} /></Grid>
          <Grid item xs={12} sm={6} md={3}><RivarMetricCard label={t('dashboard.finalBalance')} value={formatCurrency(summary.final_balance)} sub={`Peak: ${formatCurrency(summary.peak_balance)}`} icon={<TimelineIcon />} variant="default" /></Grid>
        </Grid>
      )}

      {/* ── Charts ── */}
      {isOriginalMulti ? (
        Object.entries(currentByCurrency).map(([code, data]) => (
          <RivarPanel
            key={code}
            title={`${code} — ${viewMode === 'forecast' ? t('dashboard.forecastedMonthlyCashFlow') : viewMode === 'actual' ? t('dashboard.actualMonthlyCashFlow') : t('dashboard.cashFlowComparison')}`}
            sx={{ mb: 3 }}
          >
            <ResponsiveContainer width="100%" height={320}>
              <ComposedChart data={data.time_series || []} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={rivarTokens.line} />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} tickFormatter={formatMonthLabel} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: any) => formatCurrency(v, code)} labelFormatter={(l) => formatMonthLabel(l as string)} contentStyle={{ borderRadius: 8, border: `1px solid ${rivarTokens.line}` }} />
                <Legend />
                <Bar dataKey="inflow" fill={CHART_COLORS.inflow} name={t('dashboard.revenueInflow')} radius={[3, 3, 0, 0]} />
                <Bar dataKey="outflow" fill={CHART_COLORS.outflow} name={t('dashboard.paymentOutflow')} radius={[3, 3, 0, 0]} />
                <Line type="monotone" dataKey="cumulative_balance" stroke={CHART_COLORS.balance} strokeWidth={2} name={t('dashboard.cumulativeBalance')} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </RivarPanel>
        ))
      ) : currentData && currentData.time_series && currentData.time_series.length > 0 ? (
        <>
          <RivarPanel
            title={viewMode === 'forecast' ? t('dashboard.forecastedMonthlyCashFlow') : viewMode === 'actual' ? t('dashboard.actualMonthlyCashFlow') : t('dashboard.cashFlowComparison')}
            sx={{ mb: 3 }}
          >
            <ResponsiveContainer width="100%" height={320}>
              <ComposedChart
                data={
                  viewMode === 'comparison'
                    ? (forecastData?.time_series || []).map((f, idx) => ({
                        month: f.month,
                        forecast_inflow: f.inflow,
                        forecast_outflow: f.outflow,
                        actual_inflow: actualData?.time_series[idx]?.inflow || 0,
                        actual_outflow: actualData?.time_series[idx]?.outflow || 0,
                        budget: f.budget,
                      }))
                    : currentData.time_series
                }
                margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={rivarTokens.line} />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} tickFormatter={formatMonthLabel} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: any) => formatCurrency(v)} labelFormatter={(l) => formatMonthLabel(l as string)} contentStyle={{ borderRadius: 8, border: `1px solid ${rivarTokens.line}` }} />
                <Legend />
                {viewMode === 'comparison' ? (
                  <>
                    <Bar dataKey="forecast_inflow" fill={CHART_COLORS.inflow} name={t('dashboard.forecastInflow')} opacity={0.7} radius={[2, 2, 0, 0]} />
                    <Bar dataKey="actual_inflow" fill={rivarTokens.good} name={t('dashboard.actualInflow')} radius={[2, 2, 0, 0]} />
                    <Bar dataKey="forecast_outflow" fill={CHART_COLORS.outflow} name={t('dashboard.forecastOutflow')} opacity={0.7} radius={[2, 2, 0, 0]} />
                    <Bar dataKey="actual_outflow" fill="#c62828" name={t('dashboard.actualOutflow')} radius={[2, 2, 0, 0]} />
                  </>
                ) : (
                  <>
                    <Bar dataKey="inflow" fill={CHART_COLORS.inflow} name={t('dashboard.revenueInflow')} radius={[3, 3, 0, 0]} />
                    <Bar dataKey="outflow" fill={CHART_COLORS.outflow} name={t('dashboard.paymentOutflow')} radius={[3, 3, 0, 0]} />
                    <Line type="monotone" dataKey="cumulative_balance" stroke={CHART_COLORS.balance} strokeWidth={2} name={t('dashboard.cumulativeBalance')} dot={false} />
                  </>
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </RivarPanel>

          <RivarPanel title={t('dashboard.cumulativeCashPosition')} sx={{ mb: 3 }}>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart
                data={
                  viewMode === 'comparison'
                    ? (forecastData?.time_series || []).map((f, idx) => ({
                        month: f.month,
                        forecast_balance: f.cumulative_balance,
                        actual_balance: actualData?.time_series[idx]?.cumulative_balance || 0,
                      }))
                    : currentData.time_series
                }
                margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={rivarTokens.line} />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} tickFormatter={formatMonthLabel} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: any) => formatCurrency(v)} labelFormatter={(l) => formatMonthLabel(l as string)} contentStyle={{ borderRadius: 8, border: `1px solid ${rivarTokens.line}` }} />
                <Legend />
                {viewMode === 'comparison' ? (
                  <>
                    <Line type="monotone" dataKey="forecast_balance" stroke={CHART_COLORS.forecast} strokeWidth={2} strokeDasharray="5 5" name={t('dashboard.forecastBalance')} dot={false} />
                    <Line type="monotone" dataKey="actual_balance" stroke={CHART_COLORS.actual} strokeWidth={2} name={t('dashboard.actualBalance')} dot={false} />
                  </>
                ) : (
                  <>
                    <Line type="monotone" dataKey="cumulative_balance" stroke={CHART_COLORS.balance} strokeWidth={2} name={t('dashboard.cumulativeBalance')} dot={false} />
                    <Line type="monotone" dataKey="net_flow" stroke={rivarTokens.warn} strokeWidth={1.5} strokeDasharray="4 4" name={t('dashboard.monthlyNetFlow')} dot={false} />
                  </>
                )}
              </LineChart>
            </ResponsiveContainer>
          </RivarPanel>

          {/* Variance analysis (comparison mode) */}
          {viewMode === 'comparison' && forecastData && actualData && (
            <RivarPanel title={t('dashboard.varianceAnalysis')} sx={{ mb: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <RivarMetricCard
                    label={t('dashboard.inflowVariance')}
                    value={formatCurrency(actualSummary.total_inflow - summary.total_inflow)}
                    sub={t('dashboard.actualVsForecast')}
                    variant={(actualSummary.total_inflow - summary.total_inflow) >= 0 ? 'good' : 'risk'}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <RivarMetricCard
                    label={t('dashboard.outflowVariance')}
                    value={formatCurrency(actualSummary.total_outflow - summary.total_outflow)}
                    sub={t('dashboard.actualVsForecast')}
                    variant={(actualSummary.total_outflow - summary.total_outflow) <= 0 ? 'good' : 'risk'}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <RivarMetricCard
                    label={t('dashboard.netPositionVariance')}
                    value={formatCurrency(actualSummary.net_position - summary.net_position)}
                    sub={t('dashboard.actualVsForecast')}
                    variant={(actualSummary.net_position - summary.net_position) >= 0 ? 'good' : 'risk'}
                  />
                </Grid>
              </Grid>
            </RivarPanel>
          )}

          {/* Data table */}
          <RivarPanel
            title={t('dashboard.monthlyCashFlowDetail')}
            actions={
              <Button variant="outlined" size="small" startIcon={<DownloadIcon />} onClick={handleExport}>
                Export Excel
              </Button>
            }
          >
            <TableContainer sx={{ border: 'none', borderRadius: 0 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('dashboard.month')}</TableCell>
                    {!isRestricted && <TableCell align="right">{t('dashboard.budget')}</TableCell>}
                    {!isProcurement && <TableCell align="right">{t('dashboard.revenueInflow')}</TableCell>}
                    {!isPM && <TableCell align="right">{t('dashboard.paymentOutflow')}</TableCell>}
                    {!isRestricted && <TableCell align="right">{t('dashboard.netFlow')}</TableCell>}
                    {!isRestricted && <TableCell align="right">{t('dashboard.cumulativeBalance')}</TableCell>}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(currentData.time_series || [])
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((row, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{formatMonthLabel(row.month)}</TableCell>
                        {!isRestricted && <TableCell align="right" sx={{ color: '#9c27b0' }}>{formatCurrency(row.budget)}</TableCell>}
                        {!isProcurement && <TableCell align="right" sx={{ color: rivarTokens.good, fontWeight: 500 }}>{formatCurrency(row.inflow)}</TableCell>}
                        {!isPM && <TableCell align="right" sx={{ color: rivarTokens.risk, fontWeight: 500 }}>{formatCurrency(row.outflow)}</TableCell>}
                        {!isRestricted && <TableCell align="right" sx={{ fontWeight: 500, color: row.net_flow >= 0 ? rivarTokens.good : rivarTokens.risk }}>{formatCurrency(row.net_flow)}</TableCell>}
                        {!isRestricted && <TableCell align="right" sx={{ fontWeight: 600, color: row.cumulative_balance >= 0 ? rivarTokens.accent : rivarTokens.warn }}>{formatCurrency(row.cumulative_balance)}</TableCell>}
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              rowsPerPageOptions={[6, 12, 24]}
              component="div"
              count={currentData.time_series?.length || 0}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={(_, p) => setPage(p)}
              onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
              labelRowsPerPage={t('dashboard.rowsPerPage')}
            />
          </RivarPanel>
        </>
      ) : (
        <RivarPanel>
          <RivarEmptyState
            icon={<TimelineIcon />}
            title={t('dashboard.noCashFlowDataAvailable', {
              type: viewMode === 'forecast' ? t('dashboard.forecast') : viewMode === 'actual' ? t('dashboard.actual') : '',
            })}
            description={
              viewMode === 'forecast' ? t('dashboard.saveFinalizedDecisions') :
              viewMode === 'actual' ? t('dashboard.financeTeamEnterData') :
              t('dashboard.bothDataNeeded')
            }
          />
        </RivarPanel>
      )}
    </Box>
  );
};
