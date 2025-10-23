import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tabs,
  Tab,
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

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, icon, color }) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="subtitle2">
            {title}
          </Typography>
          <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', color }}>
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="textSecondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box sx={{ color, fontSize: 40, opacity: 0.7 }}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [forecastData, setForecastData] = useState<CashflowResponse | null>(null);
  const [actualData, setActualData] = useState<CashflowResponse | null>(null);
  const [forecastByCurrency, setForecastByCurrency] = useState<{[key: string]: CashflowResponse}>({});
  const [actualByCurrency, setActualByCurrency] = useState<{[key: string]: CashflowResponse}>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(12);
  const [viewMode, setViewMode] = useState<'forecast' | 'actual' | 'comparison'>('forecast');
  const [currencyDisplayMode, setCurrencyDisplayMode] = useState<'original' | 'unified'>('unified');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);

  useEffect(() => {
    const fetchCashflowData = async () => {
      try {
        const projectIdsParam = selectedProjects.length > 0 ? selectedProjects.join(',') : undefined;
        
        // Fetch both forecast and actual data with currency view
        const [forecastResponse, actualResponse] = await Promise.all([
          dashboardAPI.getCashflow({ 
            forecast_type: 'FORECAST',
            project_ids: projectIdsParam,
            currency_view: currencyDisplayMode === 'unified' ? 'unified' : 'original'
          }),
          dashboardAPI.getCashflow({ 
            forecast_type: 'ACTUAL',
            project_ids: projectIdsParam,
            currency_view: currencyDisplayMode === 'unified' ? 'unified' : 'original'
          })
        ]);
        
        // Handle multi-currency response format
        console.log('DEBUG: Forecast response:', forecastResponse.data);
        if (forecastResponse.data.view_mode === 'original' && forecastResponse.data.currencies) {
          // Multi-currency response - store all currencies
          console.log('DEBUG: Setting forecast by currency:', Object.keys(forecastResponse.data.currencies));
          console.log('DEBUG: Currency data structure:', forecastResponse.data.currencies);
          setForecastByCurrency(forecastResponse.data.currencies);
          // Also set main data to IRR for backward compatibility
          const irrData = forecastResponse.data.currencies['IRR'] || { time_series: [], summary: {}, period_count: 0 };
          setForecastData(irrData);
        } else {
          // Unified response
          console.log('DEBUG: Using unified forecast data');
          setForecastData(forecastResponse.data);
          setForecastByCurrency({});
        }
        
        if (actualResponse.data.view_mode === 'original' && actualResponse.data.currencies) {
          // Multi-currency response - store all currencies
          setActualByCurrency(actualResponse.data.currencies);
          // Also set main data to IRR for backward compatibility
          const irrData = actualResponse.data.currencies['IRR'] || { time_series: [], summary: {}, period_count: 0 };
          setActualData(irrData);
        } else {
          // Unified response
          setActualData(actualResponse.data);
          setActualByCurrency({});
        }
      } catch (err: any) {
        console.error('Dashboard fetch error:', err);
        setError(err.response?.data?.detail || 'Failed to load cash flow data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchCashflowData();
  }, [selectedProjects, currencyDisplayMode]); // Re-fetch when project filter changes

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Cash Flow Dashboard
        </Typography>
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
      </Box>
    );
  }

  const formatCurrency = (value: number, currencyCode: string = 'IRR') => {
    // Handle different currency symbols
    const currencySymbols: { [key: string]: string } = {
      'USD': '$',
      'EUR': '€',
      'IRR': '﷼',
      'GBP': '£',
      'JPY': '¥'
    };
    
    const symbol = currencySymbols[currencyCode] || currencyCode;
    
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: currencyCode === 'IRR' ? 0 : 2,
    }).format(value) + ` ${symbol}`;
  };

  const handleExportToExcel = async () => {
    try {
      const response = await dashboardAPI.exportCashflow();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `cashflow_export_${new Date().toISOString().split('T')[0]}.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export cash flow data to Excel');
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Get data based on selected view mode
  const currentData = viewMode === 'forecast' ? forecastData : 
                      viewMode === 'actual' ? actualData : 
                      forecastData; // For comparison, we'll use forecast as base

  const summary = currentData?.summary || {
    total_inflow: 0,
    total_outflow: 0,
    net_position: 0,
    peak_balance: 0,
    min_balance: 0,
    final_balance: 0,
  };

  const actualSummary = actualData?.summary || {
    total_inflow: 0,
    total_outflow: 0,
    net_position: 0,
    peak_balance: 0,
    min_balance: 0,
    final_balance: 0,
  };

  // Check user role for restricted access
  const isPM = user?.role === 'pm';
  const isPMO = user?.role === 'pmo';
  const isProcurement = user?.role === 'procurement';
  const isRestricted = isPM || isProcurement;  // PMO has full access like admin

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            {t('dashboard.title')}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            {t('dashboard.subtitle')}
          </Typography>
        </Box>
      </Box>

      {/* Project Filter */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <ProjectFilter
          selectedProjects={selectedProjects}
          onChange={setSelectedProjects}
          label={t('dashboard.filterByProjects')}
        />
      </Paper>

      {/* View Mode Selector */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{t('dashboard.viewMode')}</Typography>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            aria-label="cash flow view mode"
          >
            <ToggleButton value="forecast" aria-label="forecast view">
              <ForecastIcon sx={{ mr: 1 }} />
              {t('dashboard.forecasted')}
            </ToggleButton>
            <ToggleButton value="actual" aria-label="actual view">
              <ActualIcon sx={{ mr: 1 }} />
              {t('dashboard.actual')}
            </ToggleButton>
            <ToggleButton value="comparison" aria-label="comparison view">
              <CompareIcon sx={{ mr: 1 }} />
              {t('dashboard.comparison')}
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">{t('dashboard.currencyDisplay')}</Typography>
          <ToggleButtonGroup
            value={currencyDisplayMode}
            exclusive
            onChange={(e, newMode) => newMode && setCurrencyDisplayMode(newMode)}
            aria-label="currency display mode"
          >
            <ToggleButton value="unified" aria-label="unified currency">
              <AccountBalanceIcon sx={{ mr: 1 }} />
              {t('dashboard.unified')}
            </ToggleButton>
            <ToggleButton value="original" aria-label="original currencies">
              <CompareIcon sx={{ mr: 1 }} />
              {t('dashboard.originalCurrencies')}
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
        <Box mt={2}>
          {viewMode === 'forecast' && (
            <Alert severity="info" icon={<ForecastIcon />}>
              {t('dashboard.showingForecasted')}
            </Alert>
          )}
          {viewMode === 'actual' && (
            <Alert severity="success" icon={<ActualIcon />}>
              Showing <strong>actual</strong> cash flow based on real invoice data entered by the finance team.
            </Alert>
          )}
          {viewMode === 'comparison' && (
            <Alert severity="warning" icon={<CompareIcon />}>
              Comparing <strong>forecasted vs actual</strong> cash flow to analyze variances.
            </Alert>
          )}
          {currencyDisplayMode === 'unified' && (
            <Alert severity="info" icon={<AccountBalanceIcon />} sx={{ mt: 1 }}>
              {t('dashboard.allAmountsConverted')}
            </Alert>
          )}
          {currencyDisplayMode === 'original' && (
            <Alert severity="info" icon={<CompareIcon />} sx={{ mt: 1 }}>
              Displaying amounts in <strong>original currencies</strong> (USD, EUR, IRR, etc.)
            </Alert>
          )}
        </Box>
      </Paper>

      {/* Multi-Currency Summary (Original Mode) */}
      {currencyDisplayMode === 'original' && Object.keys(forecastByCurrency).length > 0 && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            {t('dashboard.cashFlowByCurrency')}
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(forecastByCurrency).map(([currencyCode, currencyData]) => (
              <Grid item xs={12} sm={6} md={4} key={currencyCode}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      {currencyCode}
                    </Typography>
                    <Typography variant="h6" color="primary" gutterBottom>
                      {t('dashboard.inflow')}: {currencyData.summary?.total_inflow?.toLocaleString() || 0}
                    </Typography>
                    <Typography variant="h6" color="error" gutterBottom>
                      {t('dashboard.outflow')}: {currencyData.summary?.total_outflow?.toLocaleString() || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('dashboard.net')}: {currencyData.summary?.net_position?.toLocaleString() || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* PM users only see Revenue Inflow */}
        {isPM ? (
          <>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard
                title={t('dashboard.totalRevenueInflow')}
                value={formatCurrency(summary.total_inflow)}
                subtitle={t('dashboard.expectedRevenueFromClients')}
                icon={<TrendingUpIcon />}
                color="#4caf50"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard
                title={t('dashboard.inflowEvents')}
                value={currentData?.period_count?.toString() || '0'}
                subtitle={t('dashboard.revenueTransactions')}
                icon={<TimelineIcon />}
                color="#2196f3"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" variant="subtitle2" gutterBottom>
                    Access Level
                  </Typography>
                  <Chip label={t('dashboard.projectManager')} color="primary" />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Revenue data only
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </>
        ) : isProcurement ? (
          /* Procurement users only see Payment Outflow */
          <>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard
                title={t('dashboard.totalPaymentOutflow')}
                value={formatCurrency(summary.total_outflow)}
                subtitle={t('dashboard.paymentsToSuppliers')}
                icon={<TrendingDownIcon />}
                color="#f44336"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard
                title={t('dashboard.outflowEvents')}
                value={currentData?.period_count?.toString() || '0'}
                subtitle={t('dashboard.paymentTransactions')}
                icon={<TimelineIcon />}
                color="#2196f3"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" variant="subtitle2" gutterBottom>
                    Access Level
                  </Typography>
                  <Chip label={t('dashboard.procurementSpecialist')} color="secondary" />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Payment data only
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </>
        ) : currencyDisplayMode === 'original' && Object.keys(forecastByCurrency).length > 0 ? (
          /* Multi-Currency Summary Cards (Original Mode) */
          <>
            {Object.entries(forecastByCurrency).map(([currencyCode, currencyData]) => (
              <React.Fragment key={currencyCode}>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom sx={{ mt: 2, mb: 1 }}>
                    {currencyCode} Summary
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <StatCard
                    title={t('dashboard.totalInflow')}
                    value={formatCurrency(currencyData.summary?.total_inflow || 0, currencyCode)}
                    subtitle={t('dashboard.budgetRevenue')}
                    icon={<TrendingUpIcon />}
                    color="#4caf50"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <StatCard
                    title={t('dashboard.totalOutflow')}
                    value={formatCurrency(currencyData.summary?.total_outflow || 0, currencyCode)}
                    subtitle={t('dashboard.payments')}
                    icon={<TrendingDownIcon />}
                    color="#f44336"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <StatCard
                    title={t('dashboard.netPosition')}
                    value={formatCurrency(currencyData.summary?.net_position || 0, currencyCode)}
                    subtitle={(currencyData.summary?.net_position || 0) >= 0 ? t('dashboard.positive') : 'Negative'}
                    icon={<AccountBalanceIcon />}
                    color={(currencyData.summary?.net_position || 0) >= 0 ? '#2196f3' : '#ff9800'}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <StatCard
                    title={t('dashboard.finalBalance')}
                    value={formatCurrency(currencyData.summary?.final_balance || 0, currencyCode)}
                    subtitle={`${t('dashboard.peak')}: ${formatCurrency(currencyData.summary?.peak_balance || 0, currencyCode)}`}
                    icon={<TimelineIcon />}
                    color="#9c27b0"
                  />
                </Grid>
              </React.Fragment>
            ))}
          </>
        ) : (
          /* Unified Summary Cards (Unified Mode) */
          <>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title={t('dashboard.totalInflow')}
                value={formatCurrency(summary.total_inflow)}
                subtitle={t('dashboard.budgetRevenue')}
                icon={<TrendingUpIcon />}
                color="#4caf50"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title={t('dashboard.totalOutflow')}
                value={formatCurrency(summary.total_outflow)}
                subtitle={t('dashboard.payments')}
                icon={<TrendingDownIcon />}
                color="#f44336"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title={t('dashboard.netPosition')}
                value={formatCurrency(summary.net_position)}
                subtitle={summary.net_position >= 0 ? t('dashboard.positive') : 'Negative'}
                icon={<AccountBalanceIcon />}
                color={summary.net_position >= 0 ? '#2196f3' : '#ff9800'}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title={t('dashboard.finalBalance')}
                value={formatCurrency(summary.final_balance)}
                subtitle={`${t('dashboard.peak')}: ${formatCurrency(summary.peak_balance)}`}
                icon={<TimelineIcon />}
                color="#9c27b0"
              />
            </Grid>
          </>
        )}
      </Grid>

      {/* Cash Flow Chart */}
      {console.log('DEBUG: Rendering check - currencyDisplayMode:', currencyDisplayMode, 'forecastByCurrency keys:', Object.keys(forecastByCurrency), 'length:', Object.keys(forecastByCurrency).length)}
      {currencyDisplayMode === 'original' && Object.keys(forecastByCurrency).length > 0 ? (
        // Multi-Currency Charts (Original Mode) - Separate chart for each currency
        Object.entries(forecastByCurrency).map(([currencyCode, currencyData]) => (
          <Paper key={currencyCode} sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                {currencyCode} - {viewMode === 'forecast' && t('dashboard.forecastedMonthlyCashFlow')}
                {viewMode === 'actual' && t('dashboard.actualMonthlyCashFlow')}
                {viewMode === 'comparison' && t('dashboard.cashFlowComparison')}
              </Typography>
              <Typography variant="subtitle2" color="text.secondary">
                Currency: {currencyCode}
              </Typography>
            </Box>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart
                data={currencyData.time_series || []}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  label={{ value: t('dashboard.month'), position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${currencyCode} ${(value / 1000).toFixed(0)}k`}
                  label={{ value: `Amount (${currencyCode})`, angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  formatter={(value: any, name: string) => [`${currencyCode} ${value.toLocaleString()}`, name]}
                  labelFormatter={(label) => `${t('dashboard.month')}: ${label}`}
                  contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
                />
                <Legend />
                <Bar dataKey="budget" fill="#9c27b0" name={t('dashboard.budget')} />
                <Bar dataKey="inflow" fill="#4caf50" name={t('dashboard.revenueInflow')} />
                <Bar dataKey="outflow" fill="#f44336" name={t('dashboard.paymentOutflow')} />
                <Line
                  type="monotone"
                  dataKey="cumulative_balance"
                  stroke="#2196f3"
                  strokeWidth={3}
                  name={t('dashboard.cumulativeBalance')}
                  dot={{ fill: '#2196f3', r: 4 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Paper>
        ))
      ) : currentData && currentData.time_series && currentData.time_series.length > 0 ? (
        // Unified Chart (Unified Mode)
        <>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                {viewMode === 'forecast' && t('dashboard.forecastedMonthlyCashFlow')}
                {viewMode === 'actual' && t('dashboard.actualMonthlyCashFlow')}
                {viewMode === 'comparison' && t('dashboard.cashFlowComparison')}
              </Typography>
              {viewMode === 'comparison' && (
                <Box display="flex" gap={1}>
                  <Chip icon={<ForecastIcon />} label={t('dashboard.forecast')} color="primary" size="small" />
                  <Chip icon={<ActualIcon />} label={t('dashboard.actual')} color="success" size="small" />
                </Box>
              )}
            </Box>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart
                data={viewMode === 'comparison' ? 
                  // Merge forecast and actual data for comparison
                  (forecastData?.time_series || []).map((f, idx) => ({
                    month: f.month,
                    forecast_inflow: f.inflow,
                    forecast_outflow: f.outflow,
                    actual_inflow: actualData?.time_series[idx]?.inflow || 0,
                    actual_outflow: actualData?.time_series[idx]?.outflow || 0,
                    budget: f.budget,
                  })) :
                  currentData.time_series
                }
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  label={{ value: t('dashboard.month'), position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `﷼${(value / 1000).toFixed(0)}k`}
                  label={{ value: `${t('dashboard.amount')} (IRR)`, angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  formatter={(value: any) => formatCurrency(value)}
                  contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
                />
                <Legend />
                
                {viewMode === 'comparison' ? (
                  <>
                    <Bar dataKey="budget_allocation" fill="#9c27b0" name={t('dashboard.budget')} />
                    <Bar dataKey="forecast_inflow" fill="#4caf50" name={t('dashboard.forecastInflow')} opacity={0.8} />
                    <Bar dataKey="actual_inflow" fill="#2e7d32" name={t('dashboard.actualInflow')} />
                    <Bar dataKey="forecast_outflow" fill="#f44336" name={t('dashboard.forecastOutflow')} opacity={0.8} />
                    <Bar dataKey="actual_outflow" fill="#c62828" name={t('dashboard.actualOutflow')} />
                    <Line
                      type="monotone"
                      dataKey="forecast_balance"
                      stroke="#2196f3"
                      strokeWidth={2}
                      name={t('dashboard.forecastBalance')}
                      dot={{ fill: '#2196f3', r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="actual_balance"
                      stroke="#ff9800"
                      strokeWidth={2}
                      name={t('dashboard.actualBalance')}
                      dot={{ fill: '#ff9800', r: 3 }}
                    />
                  </>
                ) : (
                  <>
                    <Bar dataKey="budget_allocation" fill="#9c27b0" name={t('dashboard.budgetAllocation')} />
                    <Bar dataKey="inflow" fill="#4caf50" name={t('dashboard.revenueInflow')} />
                    <Bar dataKey="outflow" fill="#f44336" name={t('dashboard.paymentOutflow')} />
                    <Line
                      type="monotone"
                      dataKey="cumulative_balance"
                      stroke="#2196f3"
                      strokeWidth={3}
                      name={t('dashboard.cumulativeBalance')}
                      dot={{ fill: '#2196f3', r: 4 }}
                    />
                  </>
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </Paper>

          {/* Revenue & Payment Flow Detail Chart */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {isPM ? 'Revenue Inflow Detail' : 
               isProcurement ? 'Payment Outflow Detail' :
               t('dashboard.revenuePaymentFlowDetail')}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {isPM 
                ? 'Revenue inflows from clients based on delivery and invoice timing'
                : isProcurement
                ? 'Payment outflows to suppliers based on procurement terms'
                : t('dashboard.detailedViewDescription')}
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={currentData.time_series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  label={{ value: t('dashboard.month'), position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `﷼${value.toLocaleString()}`}
                  label={{ value: `${t('dashboard.amount')} (IRR)`, angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  formatter={(value: any) => formatCurrency(value)}
                  contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
                />
                <Legend />
                {!isProcurement && <Bar dataKey="inflow" fill="#4caf50" name={t('dashboard.revenueInflow')} />}
                {!isPM && <Bar dataKey="outflow" fill="#f44336" name={t('dashboard.paymentOutflow')} />}
              </ComposedChart>
            </ResponsiveContainer>
          </Paper>

          <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
              {viewMode === 'comparison' ? t('dashboard.cumulativeCashPosition') : t('dashboard.cumulativeCashPosition')}
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={viewMode === 'comparison' ?
                  (forecastData?.time_series || []).map((f, idx) => ({
                    month: f.month,
                    forecast_balance: f.cumulative_balance,
                    actual_balance: actualData?.time_series[idx]?.cumulative_balance || 0,
                  })) :
                  currentData.time_series
                }
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  label={{ value: t('dashboard.month'), position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `﷼${(value / 1000).toFixed(0)}k`}
                  label={{ value: 'Balance (USD)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  formatter={(value: any) => formatCurrency(value)}
                  contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
                />
                <Legend />
                {viewMode === 'comparison' ? (
                  <>
                    <Line
                      type="monotone"
                      dataKey="forecast_balance"
                      stroke="#2196f3"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name={t('dashboard.forecastBalance')}
                      dot={{ fill: '#2196f3', r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="actual_balance"
                      stroke="#2e7d32"
                      strokeWidth={3}
                      name={t('dashboard.actualBalance')}
                      dot={{ fill: '#2e7d32', r: 5 }}
                      activeDot={{ r: 8 }}
                    />
                  </>
                ) : (
                  <>
                    <Line
                      type="monotone"
                      dataKey="cumulative_balance"
                      stroke="#2196f3"
                      strokeWidth={3}
                      name={t('dashboard.cumulativeBalance')}
                      dot={{ fill: '#2196f3', r: 5 }}
                      activeDot={{ r: 8 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="net_flow"
                      stroke="#ff9800"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name={t('dashboard.monthlyNetFlow')}
                      dot={{ fill: '#ff9800', r: 3 }}
                    />
                  </>
                )}
              </LineChart>
            </ResponsiveContainer>
          </Paper>

          {/* Cash Flow Data Table */}
          <Paper sx={{ p: 3, mt: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                {t('dashboard.monthlyCashFlowDetail')}
              </Typography>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={handleExportToExcel}
                size="small"
              >
                Export to Excel
              </Button>
            </Box>
            
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>{t('dashboard.month')}</strong></TableCell>
                    {!isRestricted && <TableCell align="right"><strong>{t('dashboard.budget')}</strong></TableCell>}
                    {!isProcurement && <TableCell align="right"><strong>{t('dashboard.revenueInflow')}</strong></TableCell>}
                    {!isPM && <TableCell align="right"><strong>{t('dashboard.paymentOutflow')}</strong></TableCell>}
                    {!isRestricted && <TableCell align="right"><strong>{t('dashboard.netFlow')}</strong></TableCell>}
                    {!isRestricted && <TableCell align="right"><strong>{t('dashboard.cumulativeBalance')}</strong></TableCell>}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(currentData?.time_series || [])
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((row, index) => (
                      <TableRow key={index} hover>
                        <TableCell>{row.month}</TableCell>
                        {!isRestricted && (
                          <TableCell align="right" sx={{ color: '#9c27b0' }}>
                            {formatCurrency(row.budget)}
                          </TableCell>
                        )}
                        {!isProcurement && (
                          <TableCell align="right" sx={{ color: '#4caf50', fontWeight: 'medium' }}>
                            {formatCurrency(row.inflow)}
                          </TableCell>
                        )}
                        {!isPM && (
                          <TableCell align="right" sx={{ color: '#f44336', fontWeight: 'medium' }}>
                            {formatCurrency(row.outflow)}
                          </TableCell>
                        )}
                        {!isRestricted && (
                          <TableCell 
                            align="right" 
                            sx={{ 
                              fontWeight: 'medium',
                              color: row.net_flow >= 0 ? '#4caf50' : '#f44336'
                            }}
                          >
                            {formatCurrency(row.net_flow)}
                          </TableCell>
                        )}
                        {!isRestricted && (
                          <TableCell 
                            align="right" 
                            sx={{ 
                              fontWeight: 'bold',
                              color: row.cumulative_balance >= 0 ? '#2196f3' : '#ff9800'
                            }}
                          >
                            {formatCurrency(row.cumulative_balance)}
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
            
            <TablePagination
              rowsPerPageOptions={[6, 12, 24]}
              component="div"
              count={currentData?.time_series?.length || 0}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              labelRowsPerPage={t('dashboard.rowsPerPage')}
            />
          </Paper>
        </>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No {viewMode === 'forecast' ? 'forecasted' : viewMode === 'actual' ? 'actual' : ''} cash flow data available
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {viewMode === 'forecast' && 'Save finalized decisions to generate forecast cash flow projections'}
            {viewMode === 'actual' && 'Finance team needs to enter actual invoice data to see actual cash flow'}
            {viewMode === 'comparison' && 'Both forecast and actual data are needed for comparison'}
          </Typography>
        </Paper>
      )}
      
      {/* Variance Analysis for Comparison View */}
      {viewMode === 'comparison' && forecastData && actualData && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Variance Analysis
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card sx={{ bgcolor: '#e3f2fd' }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Inflow Variance
                  </Typography>
                  <Typography variant="h5" sx={{ 
                    color: (actualSummary.total_inflow - summary.total_inflow) >= 0 ? '#4caf50' : '#f44336',
                    fontWeight: 'bold'
                  }}>
                    {formatCurrency(actualSummary.total_inflow - summary.total_inflow)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Actual vs Forecast
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ bgcolor: '#fce4ec' }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Outflow Variance
                  </Typography>
                  <Typography variant="h5" sx={{ 
                    color: (actualSummary.total_outflow - summary.total_outflow) <= 0 ? '#4caf50' : '#f44336',
                    fontWeight: 'bold'
                  }}>
                    {formatCurrency(actualSummary.total_outflow - summary.total_outflow)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Actual vs Forecast
                </Typography>
            </CardContent>
          </Card>
        </Grid>
            <Grid item xs={12} md={4}>
              <Card sx={{ bgcolor: '#f3e5f5' }}>
            <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Net Position Variance
                  </Typography>
                  <Typography variant="h5" sx={{ 
                    color: (actualSummary.net_position - summary.net_position) >= 0 ? '#4caf50' : '#f44336',
                    fontWeight: 'bold'
                  }}>
                    {formatCurrency(actualSummary.net_position - summary.net_position)}
              </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Actual vs Forecast
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
        </Paper>
      )}

      {/* Additional Information */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('dashboard.aboutCashFlowAnalysis')}
          </Typography>
          <Typography variant="body2" paragraph>
            {t('dashboard.dashboardDescription')}
          </Typography>
          <Typography variant="body2" paragraph>
            <strong>{t('dashboard.keyMetrics')}:</strong>
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 0 }}>
            <li><strong>{t('dashboard.budgetAllocation')}:</strong> {t('dashboard.budgetAllocationDesc')}</li>
            <li><strong>{t('dashboard.revenueInflow')}:</strong> {t('dashboard.revenueInflowDesc')}</li>
            <li><strong>{t('dashboard.paymentOutflow')}:</strong> {t('dashboard.paymentOutflowDesc')}</li>
            <li><strong>{t('dashboard.cumulativeBalance')}:</strong> {t('dashboard.cumulativeBalanceDesc')}</li>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
