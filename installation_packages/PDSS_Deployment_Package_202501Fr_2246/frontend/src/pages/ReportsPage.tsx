import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Chip,
  SelectChangeEvent,
} from '@mui/material';
import {
  FileDownload as ExportIcon,
  Assessment as ReportIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
  ComposedChart,
} from 'recharts';
import { reportsAPI } from '../services/api.ts';
import {
  ReportsData,
  FilterOption,
  BudgetVsActual,
  ProjectKPI,
  RiskItem,
  SupplierScorecard,
} from '../types/index.ts';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`reports-tabpanel-${index}`}
      aria-labelledby={`reports-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export const ReportsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reportsData, setReportsData] = useState<ReportsData | null>(null);

  // Global Filters
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
  const [selectedSuppliers, setSelectedSuppliers] = useState<number[]>([]);

  // Filter Options
  const [projects, setProjects] = useState<FilterOption[]>([]);
  const [suppliers, setSuppliers] = useState<FilterOption[]>([]);

  // Load filter options
  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Load reports data when filters change
  useEffect(() => {
    loadReportsData();
  }, [startDate, endDate, selectedProjects, selectedSuppliers]);

  const loadFilterOptions = async () => {
    try {
      const [projectsRes, suppliersRes] = await Promise.all([
        reportsAPI.getProjects(),
        reportsAPI.getSuppliers(),
      ]);
      setProjects(projectsRes.data);
      setSuppliers(suppliersRes.data);
    } catch (err: any) {
      console.error('Failed to load filter options:', err);
    }
  };

  const loadReportsData = async () => {
    setLoading(true);
    setError('');
    try {
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (selectedProjects.length > 0) params.project_ids = selectedProjects.join(',');
      if (selectedSuppliers.length > 0) params.supplier_ids = selectedSuppliers.join(',');

      const response = await reportsAPI.getData(params);
      setReportsData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load reports data');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (selectedProjects.length > 0) params.project_ids = selectedProjects.join(',');
      if (selectedSuppliers.length > 0) params.supplier_ids = selectedSuppliers.join(',');

      const response = await reportsAPI.export(params);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Reports_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      setError('Failed to export reports');
    }
  };

  const handleProjectChange = (event: SelectChangeEvent<number[]>) => {
    const value = event.target.value;
    setSelectedProjects(typeof value === 'string' ? [] : value);
  };

  const handleSupplierChange = (event: SelectChangeEvent<number[]>) => {
    const value = event.target.value;
    setSelectedSuppliers(typeof value === 'string' ? [] : value);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number, decimals: number = 2) => {
    return value.toFixed(decimals);
  };

  if (loading && !reportsData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <ReportIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h4">Reports & Analytics</Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<ExportIcon />}
          onClick={handleExport}
          disabled={loading || !reportsData}
        >
          Export to Excel
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Global Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Global Filters
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Projects</InputLabel>
              <Select
                multiple
                value={selectedProjects}
                onChange={handleProjectChange}
                label="Projects"
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => {
                      const project = projects.find((p) => p.id === value);
                      return <Chip key={value} label={project?.name || value} size="small" />;
                    })}
                  </Box>
                )}
              >
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Suppliers</InputLabel>
              <Select
                multiple
                value={selectedSuppliers}
                onChange={handleSupplierChange}
                label="Suppliers"
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => {
                      const supplier = suppliers.find((s) => s.id === value);
                      return <Chip key={value} label={supplier?.name || value} size="small" />;
                    })}
                  </Box>
                )}
              >
                {suppliers.map((supplier) => (
                  <MenuItem key={supplier.id} value={supplier.id}>
                    {supplier.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Financial Summary" />
          <Tab label="EVM Analytics" />
          <Tab label="Risk & Forecasts" />
          <Tab label="Operational Performance" />
        </Tabs>

        {/* Tab 1: Financial Summary */}
        <TabPanel value={tabValue} index={0}>
          {reportsData && (
            <Box>
              {/* Cash Flow Analysis Chart */}
              <Typography variant="h6" gutterBottom>
                Cash Flow Analysis
              </Typography>
              <Paper sx={{ p: 2, mb: 3 }}>
                <ResponsiveContainer width="100%" height={400}>
                  <ComposedChart
                    data={reportsData.financial_summary.cash_flow.dates.map((date, i) => ({
                      date,
                      inflow: reportsData.financial_summary.cash_flow.inflow[i],
                      outflow: reportsData.financial_summary.cash_flow.outflow[i],
                      net_flow: reportsData.financial_summary.cash_flow.net_flow[i],
                      cumulative: reportsData.financial_summary.cash_flow.cumulative_balance[i],
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                    <Legend />
                    <Bar dataKey="inflow" fill="#4caf50" name="Cash Inflow" />
                    <Bar dataKey="outflow" fill="#f44336" name="Cash Outflow" />
                    <Line
                      type="monotone"
                      dataKey="cumulative"
                      stroke="#2196f3"
                      strokeWidth={3}
                      name="Cumulative Balance"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </Paper>

              {/* Budget vs Actuals Table */}
              <Typography variant="h6" gutterBottom>
                Budget vs Actuals Summary
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Project Name</TableCell>
                      <TableCell align="right">Planned Cost</TableCell>
                      <TableCell align="right">Actual Cost</TableCell>
                      <TableCell align="right">Variance ($)</TableCell>
                      <TableCell align="right">Variance (%)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {reportsData.financial_summary.budget_vs_actual.map((row: BudgetVsActual, index) => (
                      <TableRow
                        key={index}
                        sx={{
                          backgroundColor:
                            row.project_name === 'GRAND TOTAL' ? '#f5f5f5' : 'inherit',
                          fontWeight: row.project_name === 'GRAND TOTAL' ? 'bold' : 'normal',
                        }}
                      >
                        <TableCell sx={{ fontWeight: 'inherit' }}>{row.project_name}</TableCell>
                        <TableCell align="right">{formatCurrency(row.planned_cost)}</TableCell>
                        <TableCell align="right">{formatCurrency(row.actual_cost)}</TableCell>
                        <TableCell
                          align="right"
                          sx={{
                            color: row.variance_amount > 0 ? 'error.main' : 'success.main',
                          }}
                        >
                          {formatCurrency(row.variance_amount)}
                        </TableCell>
                        <TableCell
                          align="right"
                          sx={{
                            color: row.variance_percent > 0 ? 'error.main' : 'success.main',
                          }}
                        >
                          {formatNumber(row.variance_percent, 2)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </TabPanel>

        {/* Tab 2: EVM Analytics */}
        <TabPanel value={tabValue} index={1}>
          {reportsData && (
            <Box>
              {/* EVM Performance Chart */}
              <Typography variant="h6" gutterBottom>
                Core EVM Performance
              </Typography>
              <Paper sx={{ p: 2, mb: 3 }}>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart
                    data={reportsData.evm_analytics.evm_performance.dates.map((date, i) => ({
                      date,
                      pv: reportsData.evm_analytics.evm_performance.pv[i],
                      ev: reportsData.evm_analytics.evm_performance.ev[i],
                      ac: reportsData.evm_analytics.evm_performance.ac[i],
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="pv"
                      stroke="#8884d8"
                      strokeWidth={2}
                      name="Planned Value (PV)"
                    />
                    <Line
                      type="monotone"
                      dataKey="ev"
                      stroke="#82ca9d"
                      strokeWidth={2}
                      name="Earned Value (EV)"
                    />
                    <Line
                      type="monotone"
                      dataKey="ac"
                      stroke="#ff7300"
                      strokeWidth={2}
                      name="Actual Cost (AC)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>

              {/* KPI Trends Chart */}
              <Typography variant="h6" gutterBottom>
                KPI Trends (CPI & SPI)
              </Typography>
              <Paper sx={{ p: 2, mb: 3 }}>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart
                    data={reportsData.evm_analytics.kpi_trends.dates.map((date, i) => ({
                      date,
                      cpi: reportsData.evm_analytics.kpi_trends.cpi[i],
                      spi: reportsData.evm_analytics.kpi_trends.spi[i],
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 2]} />
                    <Tooltip formatter={(value: any) => formatNumber(value, 3)} />
                    <Legend />
                    <ReferenceLine y={1.0} stroke="#666" strokeDasharray="3 3" label="Target (1.0)" />
                    <Line
                      type="monotone"
                      dataKey="cpi"
                      stroke="#4caf50"
                      strokeWidth={2}
                      name="Cost Performance Index (CPI)"
                    />
                    <Line
                      type="monotone"
                      dataKey="spi"
                      stroke="#2196f3"
                      strokeWidth={2}
                      name="Schedule Performance Index (SPI)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>

              {/* Project KPI Breakdown Table */}
              <Typography variant="h6" gutterBottom>
                Project KPI Breakdown
              </Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Project</TableCell>
                      <TableCell align="right">PV</TableCell>
                      <TableCell align="right">EV</TableCell>
                      <TableCell align="right">AC</TableCell>
                      <TableCell align="right">SV ($)</TableCell>
                      <TableCell align="right">CV ($)</TableCell>
                      <TableCell align="right">SPI</TableCell>
                      <TableCell align="right">CPI</TableCell>
                      <TableCell align="right">EAC</TableCell>
                      <TableCell align="right">ETC</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {reportsData.evm_analytics.project_kpis.map((row: ProjectKPI, index) => (
                      <TableRow key={index}>
                        <TableCell>{row.project_name}</TableCell>
                        <TableCell align="right">{formatCurrency(row.pv)}</TableCell>
                        <TableCell align="right">{formatCurrency(row.ev)}</TableCell>
                        <TableCell align="right">{formatCurrency(row.ac)}</TableCell>
                        <TableCell
                          align="right"
                          sx={{ color: row.sv >= 0 ? 'success.main' : 'error.main' }}
                        >
                          {formatCurrency(row.sv)}
                        </TableCell>
                        <TableCell
                          align="right"
                          sx={{ color: row.cv >= 0 ? 'success.main' : 'error.main' }}
                        >
                          {formatCurrency(row.cv)}
                        </TableCell>
                        <TableCell
                          align="right"
                          sx={{ color: row.spi >= 1 ? 'success.main' : 'error.main' }}
                        >
                          {formatNumber(row.spi, 3)}
                        </TableCell>
                        <TableCell
                          align="right"
                          sx={{ color: row.cpi >= 1 ? 'success.main' : 'error.main' }}
                        >
                          {formatNumber(row.cpi, 3)}
                        </TableCell>
                        <TableCell align="right">{formatCurrency(row.eac)}</TableCell>
                        <TableCell align="right">{formatCurrency(row.etc)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </TabPanel>

        {/* Tab 3: Risk & Forecasts */}
        <TabPanel value={tabValue} index={2}>
          {reportsData && (
            <Box>
              {/* Delay Forecast Cards */}
              <Typography variant="h6" gutterBottom>
                Completion Delay Forecast
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        P50 (Median) Delay
                      </Typography>
                      <Typography variant="h3" component="div">
                        {formatNumber(reportsData.risk_forecasts.delay_forecast.p50, 1)} days
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        50% of items are delivered within this delay
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        P90 (90th Percentile) Delay
                      </Typography>
                      <Typography variant="h3" component="div">
                        {formatNumber(reportsData.risk_forecasts.delay_forecast.p90, 1)} days
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        90% of items are delivered within this delay
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Payment Delay Distribution */}
              <Typography variant="h6" gutterBottom>
                Payment Delay Distribution
              </Typography>
              <Paper sx={{ p: 2, mb: 3 }}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={reportsData.risk_forecasts.payment_delay_histogram}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="delay_bucket"
                      label={{ value: 'Delay (Days)', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" name="Number of Items" />
                  </BarChart>
                </ResponsiveContainer>
              </Paper>

              {/* Top 5 Risk Items */}
              <Typography variant="h6" gutterBottom>
                Top 5 Highest Risk Items
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Item Name</TableCell>
                      <TableCell>Project</TableCell>
                      <TableCell align="right">Cost Variance ($)</TableCell>
                      <TableCell align="right">Schedule Delay (Days)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {reportsData.risk_forecasts.top_risk_items.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography color="textSecondary">No risk items found</Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      reportsData.risk_forecasts.top_risk_items.map((row: RiskItem, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Box display="flex" alignItems="center" gap={1}>
                              <WarningIcon color="warning" />
                              {row.item_name}
                            </Box>
                          </TableCell>
                          <TableCell>{row.project_name}</TableCell>
                          <TableCell
                            align="right"
                            sx={{
                              color: row.cost_variance > 0 ? 'error.main' : 'success.main',
                            }}
                          >
                            {formatCurrency(row.cost_variance)}
                          </TableCell>
                          <TableCell
                            align="right"
                            sx={{
                              color: row.schedule_delay > 0 ? 'error.main' : 'success.main',
                            }}
                          >
                            {row.schedule_delay}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </TabPanel>

        {/* Tab 4: Operational Performance */}
        <TabPanel value={tabValue} index={3}>
          {reportsData && (
            <Box>
              {/* Supplier Scorecard */}
              <Typography variant="h6" gutterBottom>
                Supplier Scorecard
              </Typography>
              <TableContainer component={Paper} sx={{ mb: 3 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Supplier Name</TableCell>
                      <TableCell align="right">Total Orders</TableCell>
                      <TableCell align="right">On-Time Delivery Rate (%)</TableCell>
                      <TableCell align="right">Avg Cost Variance (%)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {reportsData.operational_performance.supplier_scorecard.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography color="textSecondary">No supplier data available</Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      reportsData.operational_performance.supplier_scorecard.map(
                        (row: SupplierScorecard, index) => (
                          <TableRow key={index}>
                            <TableCell>{row.supplier_name}</TableCell>
                            <TableCell align="right">{row.total_orders}</TableCell>
                            <TableCell
                              align="right"
                              sx={{
                                color:
                                  row.on_time_delivery_rate >= 80
                                    ? 'success.main'
                                    : row.on_time_delivery_rate >= 60
                                    ? 'warning.main'
                                    : 'error.main',
                              }}
                            >
                              {formatNumber(row.on_time_delivery_rate, 2)}%
                            </TableCell>
                            <TableCell
                              align="right"
                              sx={{
                                color:
                                  row.avg_cost_variance_percent > 0 ? 'error.main' : 'success.main',
                              }}
                            >
                              {formatNumber(row.avg_cost_variance_percent, 2)}%
                            </TableCell>
                          </TableRow>
                        )
                      )
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Procurement Cycle Time */}
              <Typography variant="h6" gutterBottom>
                Procurement Cycle Time Distribution
              </Typography>
              <Paper sx={{ p: 2 }}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={reportsData.operational_performance.procurement_cycle_time}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="cycle_time_bucket"
                      label={{ value: 'Cycle Time (Days)', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#82ca9d" name="Number of Items" />
                  </BarChart>
                </ResponsiveContainer>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 2, textAlign: 'center' }}>
                  Time elapsed between decision finalization and PM acceptance
                </Typography>
              </Paper>
            </Box>
          )}
        </TabPanel>
      </Paper>
    </Box>
  );
};

