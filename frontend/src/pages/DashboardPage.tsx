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
  const [forecastData, setForecastData] = useState<CashflowResponse | null>(null);
  const [actualData, setActualData] = useState<CashflowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(12);
  const [viewMode, setViewMode] = useState<'forecast' | 'actual' | 'comparison'>('forecast');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);

  useEffect(() => {
    const fetchCashflowData = async () => {
      try {
        const projectIdsParam = selectedProjects.length > 0 ? selectedProjects.join(',') : undefined;
        
        // Fetch both forecast and actual data
        const [forecastResponse, actualResponse] = await Promise.all([
          dashboardAPI.getCashflow({ 
            forecast_type: 'FORECAST',
            project_ids: projectIdsParam 
          }),
          dashboardAPI.getCashflow({ 
            forecast_type: 'ACTUAL',
            project_ids: projectIdsParam 
          })
        ]);
        setForecastData(forecastResponse.data);
        setActualData(actualResponse.data);
      } catch (err: any) {
        console.error('Dashboard fetch error:', err);
        setError(err.response?.data?.detail || 'Failed to load cash flow data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchCashflowData();
  }, [selectedProjects]); // Re-fetch when project filter changes

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

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
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
            {isPM ? 'Revenue Dashboard' : 
             isProcurement ? 'Payment Dashboard' :
             isPMO ? 'PMO Dashboard - Complete Overview' :
             'Cash Flow Analysis Dashboard'}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            {isPM 
              ? 'Revenue inflow tracking and forecasting' 
              : isProcurement
              ? 'Payment outflow tracking and management'
              : isPMO
              ? 'Full project portfolio and financial overview for project management office'
              : 'Comprehensive financial overview across all projects and decisions'}
      </Typography>
        </Box>
      </Box>

      {/* Project Filter */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <ProjectFilter
          selectedProjects={selectedProjects}
          onChange={setSelectedProjects}
          label="Filter by Project(s)"
        />
      </Paper>

      {/* View Mode Selector */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">View Mode</Typography>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            aria-label="cash flow view mode"
          >
            <ToggleButton value="forecast" aria-label="forecast view">
              <ForecastIcon sx={{ mr: 1 }} />
              Forecasted
            </ToggleButton>
            <ToggleButton value="actual" aria-label="actual view">
              <ActualIcon sx={{ mr: 1 }} />
              Actual
            </ToggleButton>
            <ToggleButton value="comparison" aria-label="comparison view">
              <CompareIcon sx={{ mr: 1 }} />
              Comparison
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
        <Box mt={2}>
          {viewMode === 'forecast' && (
            <Alert severity="info" icon={<ForecastIcon />}>
              Showing <strong>forecasted</strong> cash flow based on planned delivery and invoice timing from project configuration.
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
        </Box>
      </Paper>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* PM users only see Revenue Inflow */}
        {isPM ? (
          <>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard
                title="Total Revenue Inflow"
                value={formatCurrency(summary.total_inflow)}
                subtitle="Expected revenue from clients"
                icon={<TrendingUpIcon />}
                color="#4caf50"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard
                title="Inflow Events"
                value={currentData?.period_count?.toString() || '0'}
                subtitle="Revenue transactions"
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
                  <Chip label="Project Manager" color="primary" />
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
                title="Total Payment Outflow"
                value={formatCurrency(summary.total_outflow)}
                subtitle="Payments to suppliers"
                icon={<TrendingDownIcon />}
                color="#f44336"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <StatCard
                title="Outflow Events"
                value={currentData?.period_count?.toString() || '0'}
                subtitle="Payment transactions"
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
                  <Chip label="Procurement Specialist" color="secondary" />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Payment data only
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </>
        ) : (
          /* Finance/Admin users see all data */
          <>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Inflow"
                value={formatCurrency(summary.total_inflow)}
                subtitle="Budget + Revenue"
                icon={<TrendingUpIcon />}
                color="#4caf50"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Outflow"
                value={formatCurrency(summary.total_outflow)}
                subtitle="Payments"
                icon={<TrendingDownIcon />}
                color="#f44336"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Net Position"
                value={formatCurrency(summary.net_position)}
                subtitle={summary.net_position >= 0 ? 'Positive' : 'Negative'}
                icon={<AccountBalanceIcon />}
                color={summary.net_position >= 0 ? '#2196f3' : '#ff9800'}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Final Balance"
                value={formatCurrency(summary.final_balance)}
                subtitle={`Peak: ${formatCurrency(summary.peak_balance)}`}
                icon={<TimelineIcon />}
                color="#9c27b0"
              />
            </Grid>
          </>
        )}
      </Grid>

      {/* Cash Flow Chart */}
      {currentData && currentData.time_series && currentData.time_series.length > 0 ? (
        <>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                {viewMode === 'forecast' && 'Forecasted Monthly Cash Flow'}
                {viewMode === 'actual' && 'Actual Monthly Cash Flow'}
                {viewMode === 'comparison' && 'Cash Flow Comparison'}
              </Typography>
              {viewMode === 'comparison' && (
                <Box display="flex" gap={1}>
                  <Chip icon={<ForecastIcon />} label="Forecast" color="primary" size="small" />
                  <Chip icon={<ActualIcon />} label="Actual" color="success" size="small" />
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
                  label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                  label={{ value: 'Amount (USD)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  formatter={(value: any) => formatCurrency(value)}
                  contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
                />
                <Legend />
                
                {viewMode === 'comparison' ? (
                  <>
                    <Bar dataKey="budget_allocation" fill="#9c27b0" name="Budget" />
                    <Bar dataKey="forecast_inflow" fill="#4caf50" name="Forecast Inflow" opacity={0.8} />
                    <Bar dataKey="actual_inflow" fill="#2e7d32" name="Actual Inflow" />
                    <Bar dataKey="forecast_outflow" fill="#f44336" name="Forecast Outflow" opacity={0.8} />
                    <Bar dataKey="actual_outflow" fill="#c62828" name="Actual Outflow" />
                    <Line
                      type="monotone"
                      dataKey="forecast_balance"
                      stroke="#2196f3"
                      strokeWidth={2}
                      name="Forecast Balance"
                      dot={{ fill: '#2196f3', r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="actual_balance"
                      stroke="#ff9800"
                      strokeWidth={2}
                      name="Actual Balance"
                      dot={{ fill: '#ff9800', r: 3 }}
                    />
                  </>
                ) : (
                  <>
                    <Bar dataKey="budget_allocation" fill="#9c27b0" name="Budget Allocation" />
                    <Bar dataKey="inflow" fill="#4caf50" name="Revenue Inflow" />
                    <Bar dataKey="outflow" fill="#f44336" name="Payment Outflow" />
                    <Line
                      type="monotone"
                      dataKey="cumulative_balance"
                      stroke="#2196f3"
                      strokeWidth={3}
                      name="Cumulative Balance"
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
               'Revenue & Payment Flow Detail'}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {isPM 
                ? 'Revenue inflows from clients based on delivery and invoice timing'
                : isProcurement
                ? 'Payment outflows to suppliers based on procurement terms'
                : 'Detailed view of revenue inflows and payment outflows (separate from budget allocations)'}
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={currentData.time_series}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                  label={{ value: 'Amount (USD)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  formatter={(value: any) => formatCurrency(value)}
                  contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
                />
                <Legend />
                {!isProcurement && <Bar dataKey="inflow" fill="#4caf50" name="Revenue Inflow" />}
                {!isPM && <Bar dataKey="outflow" fill="#f44336" name="Payment Outflow" />}
              </ComposedChart>
            </ResponsiveContainer>
          </Paper>

          <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
              {viewMode === 'comparison' ? 'Cumulative Position Comparison' : 'Cumulative Cash Position'}
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
                  label={{ value: 'Month', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
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
                      name="Forecast Balance"
                      dot={{ fill: '#2196f3', r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="actual_balance"
                      stroke="#2e7d32"
                      strokeWidth={3}
                      name="Actual Balance"
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
                      name="Cumulative Balance"
                      dot={{ fill: '#2196f3', r: 5 }}
                      activeDot={{ r: 8 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="net_flow"
                      stroke="#ff9800"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Monthly Net Flow"
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
                Monthly Cash Flow Detail
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
                    <TableCell><strong>Month</strong></TableCell>
                    {!isRestricted && <TableCell align="right"><strong>Budget</strong></TableCell>}
                    {!isProcurement && <TableCell align="right"><strong>Revenue Inflow</strong></TableCell>}
                    {!isPM && <TableCell align="right"><strong>Payment Outflow</strong></TableCell>}
                    {!isRestricted && <TableCell align="right"><strong>Net Flow</strong></TableCell>}
                    {!isRestricted && <TableCell align="right"><strong>Cumulative Balance</strong></TableCell>}
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
            About Cash Flow Analysis
          </Typography>
          <Typography variant="body2" paragraph>
            This dashboard visualizes the projected cash flow based on finalized procurement decisions.
            It shows when payments are due (outflows), when revenue is expected (inflows), and the
            cumulative cash position over time.
          </Typography>
          <Typography variant="body2" paragraph>
            <strong>Key Metrics:</strong>
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 0 }}>
            <li><strong>Budget Allocation:</strong> Initial funds available for each period</li>
            <li><strong>Revenue Inflow:</strong> Expected payments from clients based on invoice dates</li>
            <li><strong>Payment Outflow:</strong> Payments to suppliers based on procurement terms</li>
            <li><strong>Cumulative Balance:</strong> Running total showing cash position over time</li>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
