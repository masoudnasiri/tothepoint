import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tab,
  Tabs,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Assessment as AssessmentIcon,
  AccountBalance as AccountBalanceIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  AttachMoney as AttachMoneyIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
  ComposedChart,
} from 'recharts';
import { useAuth } from '../contexts/AuthContext.tsx';
import { analyticsAPI, projectsAPI } from '../services/api.ts';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export const AnalyticsDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | 'all'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Analytics data
  const [evaData, setEvaData] = useState<any>(null);
  const [cashflowData, setCashflowData] = useState<any>(null);
  const [riskData, setRiskData] = useState<any>(null);
  const [projectsSummary, setProjectsSummary] = useState<any>(null);

  useEffect(() => {
    fetchProjects();
    fetchAllProjectsSummary();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      fetchProjectAnalytics();
    }
  }, [selectedProjectId]);

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.list();
      setProjects(response.data);
      // Default to "All Projects" for portfolio view
      setSelectedProjectId('all');
    } catch (err: any) {
      setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const fetchAllProjectsSummary = async () => {
    try {
      const response = await analyticsAPI.getAllProjectsSummary();
      setProjectsSummary(response.data);
    } catch (err: any) {
      console.error('Failed to load projects summary');
    }
  };

  const fetchProjectAnalytics = async () => {
    if (!selectedProjectId) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Fetch analytics for selected project OR portfolio ('all')
      const [evaResponse, cashflowResponse, riskResponse] = await Promise.all([
        analyticsAPI.getEVA(selectedProjectId),
        analyticsAPI.getCashflowForecast(selectedProjectId, 12),
        analyticsAPI.getRisk(selectedProjectId),
      ]);
      
      setEvaData(evaResponse.data);
      setCashflowData(cashflowResponse.data);
      setRiskData(riskResponse.data);
      
      // Also fetch project summary if needed
      if (selectedProjectId === 'all') {
        const summaryResponse = await analyticsAPI.getAllProjectsSummary();
        setProjectsSummary(summaryResponse.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'success';
      case 'at_risk': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy': return <CheckCircleIcon />;
      case 'at_risk': return <WarningIcon />;
      case 'critical': return <WarningIcon />;
      default: return <AssessmentIcon />;
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high': return '#f44336'; // Red
      case 'medium': return '#ff9800'; // Orange
      case 'low': return '#4caf50'; // Green
      default: return 'inherit';
    }
  };

  const getProjectRiskLevel = (projectId: number) => {
    if (!projectsSummary || !projectsSummary.projects) return null;
    const project = projectsSummary.projects.find((p: any) => p.project_id === projectId);
    
    if (!project) return null;
    
    // Combine health (CPI/SPI) and risk_level (variance analysis)
    // If EITHER shows critical/high → show as critical
    // If EITHER shows at_risk/medium → show as at_risk
    const health = project.health; // 'healthy', 'at_risk', 'critical'
    const riskLevel = project.risk_level; // 'low', 'medium', 'high', or null
    
    // Map risk_level to health scale
    const riskAsHealth = riskLevel === 'high' ? 'critical' : 
                        riskLevel === 'medium' ? 'at_risk' : 
                        riskLevel === 'low' ? 'healthy' : null;
    
    // Return worst case between health and risk
    if (health === 'critical' || riskAsHealth === 'critical') return 'critical';
    if (health === 'at_risk' || riskAsHealth === 'at_risk') return 'at_risk';
    if (health === 'healthy' && riskAsHealth === 'healthy') return 'healthy';
    if (health === 'healthy' || riskAsHealth === 'healthy') return 'healthy';
    
    return health || 'unknown';
  };

  if (loading && !evaData) {
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
          <Typography variant="h4">Project Analytics & Forecast</Typography>
          <Typography variant="subtitle2" color="textSecondary">
            Earned Value Management, Cash Flow Forecasting, and Risk Analytics
          </Typography>
        </Box>
        <FormControl sx={{ minWidth: 300 }}>
          <InputLabel>Select Project</InputLabel>
          <Select
            value={selectedProjectId || 'all'}
            onChange={(e) => setSelectedProjectId(e.target.value === 'all' ? 'all' : Number(e.target.value))}
            label="Select Project"
          >
            <MenuItem value="all">
              <strong>📊 All Projects (Portfolio View)</strong>
            </MenuItem>
            {projects.map((project) => {
              const riskLevel = getProjectRiskLevel(project.id);
              // Map both health levels (critical/at_risk/healthy) and risk levels (high/medium/low)
              const riskColor = (riskLevel === 'critical' || riskLevel === 'high') ? '#f44336' : 
                               (riskLevel === 'at_risk' || riskLevel === 'medium') ? '#ff9800' : 
                               (riskLevel === 'healthy' || riskLevel === 'low') ? '#4caf50' : 'inherit';
              const riskIcon = (riskLevel === 'critical' || riskLevel === 'high') ? '🔴 ' : 
                              (riskLevel === 'at_risk' || riskLevel === 'medium') ? '🟡 ' : 
                              (riskLevel === 'healthy' || riskLevel === 'low') ? '🟢 ' : '';
              
              return (
                <MenuItem 
                  key={project.id} 
                  value={project.id}
                  sx={{ 
                    color: riskColor,
                    fontWeight: (riskLevel === 'critical' || riskLevel === 'high') ? 'bold' : 'normal'
                  }}
                >
                  {riskIcon}{project.project_code} - {project.name}
                </MenuItem>
              );
            })}
          </Select>
        </FormControl>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} aria-label="analytics tabs">
          <Tab label="Earned Value Analytics (EVA)" icon={<AssessmentIcon />} iconPosition="start" />
          {user?.role !== 'pm' && user?.role !== 'pmo' && (
            <Tab label="Cash Flow Forecast" icon={<AccountBalanceIcon />} iconPosition="start" />
          )}
          <Tab label="Risk Analysis" icon={<WarningIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {loading ? (
        <LinearProgress />
      ) : (
        <>
          {/* EVA Tab */}
          <TabPanel value={tabValue} index={0}>
            {evaData && (
              <Box>
                {/* KPI Cards */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                          <Box>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                              CPI (Cost Performance)
                            </Typography>
                            <Typography variant="h4">
                              {evaData.metrics.cpi.toFixed(2)}
                            </Typography>
                            <Chip
                              label={evaData.health_status.cost_performance}
                              color={evaData.metrics.cpi >= 1.0 ? 'success' : evaData.metrics.cpi >= 0.9 ? 'warning' : 'error'}
                              size="small"
                              sx={{ mt: 1 }}
                            />
                          </Box>
                          <AttachMoneyIcon sx={{ fontSize: 50, color: evaData.metrics.cpi >= 1.0 ? 'success.main' : 'error.main', opacity: 0.3 }} />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                          <Box>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                              SPI (Schedule Performance)
                            </Typography>
                            <Typography variant="h4">
                              {evaData.metrics.spi.toFixed(2)}
                            </Typography>
                            <Chip
                              label={evaData.health_status.schedule_performance}
                              color={evaData.metrics.spi >= 1.0 ? 'success' : evaData.metrics.spi >= 0.9 ? 'warning' : 'error'}
                              size="small"
                              sx={{ mt: 1 }}
                            />
                          </Box>
                          <ScheduleIcon sx={{ fontSize: 50, color: evaData.metrics.spi >= 1.0 ? 'success.main' : 'error.main', opacity: 0.3 }} />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                          <Box>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                              Cost Variance (CV)
                            </Typography>
                            <Typography variant="h5">
                              {formatCurrency(evaData.metrics.cv)}
                            </Typography>
                            <Box display="flex" alignItems="center" mt={1}>
                              {evaData.metrics.cv >= 0 ? (
                                <TrendingUpIcon color="success" fontSize="small" />
                              ) : (
                                <TrendingDownIcon color="error" fontSize="small" />
                              )}
                              <Typography variant="caption" sx={{ ml: 0.5 }}>
                                {evaData.metrics.cv >= 0 ? 'Under budget' : 'Over budget'}
                              </Typography>
                            </Box>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                          <Box>
                            <Typography color="textSecondary" gutterBottom variant="subtitle2">
                              Schedule Variance (SV)
                            </Typography>
                            <Typography variant="h5">
                              {formatCurrency(evaData.metrics.sv)}
                            </Typography>
                            <Box display="flex" alignItems="center" mt={1}>
                              {evaData.metrics.sv >= 0 ? (
                                <TrendingUpIcon color="success" fontSize="small" />
                              ) : (
                                <TrendingDownIcon color="error" fontSize="small" />
                              )}
                              <Typography variant="caption" sx={{ ml: 0.5 }}>
                                {evaData.metrics.sv >= 0 ? 'Ahead' : 'Behind'}
                              </Typography>
                            </Box>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          Budget at Completion (BAC)
                        </Typography>
                        <Typography variant="h5">{formatCurrency(evaData.metrics.bac)}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          Estimate at Completion (EAC)
                        </Typography>
                        <Typography variant="h5">{formatCurrency(evaData.metrics.eac)}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          VAC: {formatCurrency(evaData.metrics.vac)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          Project Health
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getHealthIcon(evaData.health_status.overall)}
                          <Chip
                            label={evaData.health_status.overall.toUpperCase()}
                            color={getHealthColor(evaData.health_status.overall)}
                            size="small"
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Progress */}
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Project Progress
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          Completion Progress: {evaData.progress.percent_complete}%
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={evaData.progress.percent_complete} 
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                        <Typography variant="caption" color="textSecondary">
                          {evaData.progress.items_completed} of {evaData.progress.total_items} items completed
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          Planned Progress: {evaData.progress.percent_planned}%
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={evaData.progress.percent_planned} 
                          color="secondary"
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                        <Typography variant="caption" color="textSecondary">
                          {evaData.progress.items_planned} items should be done by now
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>

                {/* EV/PV/AC Chart */}
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Earned Value Trends
                    </Typography>
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={evaData.time_series}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip formatter={(value: any) => formatCurrency(value)} />
                        <Legend />
                        <Line type="monotone" dataKey="pv" stroke="#2196f3" name="Planned Value (PV)" strokeWidth={2} />
                        <Line type="monotone" dataKey="ev" stroke="#4caf50" name="Earned Value (EV)" strokeWidth={2} />
                        <Line type="monotone" dataKey="ac" stroke="#f44336" name="Actual Cost (AC)" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* CPI/SPI Trends */}
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Performance Index Trends
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={evaData.time_series}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis domain={[0.5, 1.5]} />
                        <Tooltip formatter={(value: any) => value.toFixed(3)} />
                        <Legend />
                        <Line type="monotone" dataKey="cpi" stroke="#ff9800" name="CPI (Cost Performance)" strokeWidth={2} />
                        <Line type="monotone" dataKey="spi" stroke="#9c27b0" name="SPI (Schedule Performance)" strokeWidth={2} />
                        <Line 
                          type="monotone" 
                          dataKey={() => 1.0} 
                          stroke="#666" 
                          strokeDasharray="5 5" 
                          name="Target (1.0)"
                          strokeWidth={1}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Box>
            )}
          </TabPanel>

          {/* Cash Flow Forecast Tab - Hidden for PM/PMO */}
          {user?.role !== 'pm' && user?.role !== 'pmo' && (
            <TabPanel value={tabValue} index={1}>
            {cashflowData && (
              <Box>
                {/* Summary Cards */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          Final Balance (Forecast)
                        </Typography>
                        <Typography variant="h5">
                          {formatCurrency(cashflowData.summary.final_balance)}
                        </Typography>
                        <Chip
                          label={cashflowData.summary.final_balance >= 0 ? 'Positive' : 'Negative'}
                          color={cashflowData.summary.final_balance >= 0 ? 'success' : 'error'}
                          size="small"
                          sx={{ mt: 1 }}
                        />
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          Maximum Deficit
                        </Typography>
                        <Typography variant="h5">
                          {formatCurrency(cashflowData.summary.max_deficit)}
                        </Typography>
                        {cashflowData.summary.max_deficit < 0 && (
                          <Chip label="Gap Detected" color="warning" size="small" sx={{ mt: 1 }} />
                        )}
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          Financing Needed
                        </Typography>
                        <Typography variant="h5">
                          {formatCurrency(cashflowData.summary.financing_needed)}
                        </Typography>
                        {cashflowData.summary.financing_needed > 0 && (
                          <Typography variant="caption" color="error">
                            Bridge financing required
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          Total Inflow (Forecast)
                        </Typography>
                        <Typography variant="h5">
                          {formatCurrency(cashflowData.summary.total_inflow_forecast)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Inflow vs Outflow Chart */}
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Cash Flow: Inflow vs Outflow
                    </Typography>
                    <ResponsiveContainer width="100%" height={400}>
                      <ComposedChart data={cashflowData.forecast_data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip formatter={(value: any) => formatCurrency(value)} />
                        <Legend />
                        <Bar dataKey="inflow_forecast" fill="#4caf50" name="Inflow (Forecast)" />
                        <Bar dataKey="outflow_forecast" fill="#f44336" name="Outflow (Forecast)" />
                        <Bar dataKey="inflow_actual" fill="#2e7d32" name="Inflow (Actual)" />
                        <Bar dataKey="outflow_actual" fill="#c62828" name="Outflow (Actual)" />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* Cumulative Balance */}
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Cumulative Net Balance
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={cashflowData.forecast_data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip formatter={(value: any) => formatCurrency(value)} />
                        <Legend />
                        <Area 
                          type="monotone" 
                          dataKey="cumulative_balance" 
                          stroke="#2196f3" 
                          fill="#2196f3"
                          fillOpacity={0.3}
                          name="Cumulative Balance"
                        />
                        <Line 
                          type="monotone" 
                          dataKey={() => 0} 
                          stroke="#f44336" 
                          strokeDasharray="5 5" 
                          name="Break-even"
                          strokeWidth={2}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                    {cashflowData.gap_intervals.length > 0 && (
                      <Alert severity="warning" sx={{ mt: 2 }}>
                        <Typography variant="body2" fontWeight="medium">
                          ⚠️ {cashflowData.gap_intervals.length} period(s) with negative balance detected
                        </Typography>
                        <Typography variant="caption">
                          Maximum deficit: {formatCurrency(Math.max(...cashflowData.gap_intervals.map((g: any) => g.deficit)))}
                        </Typography>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Box>
            )}
          </TabPanel>
          )}

          {/* Risk Analysis Tab */}
          <TabPanel value={tabValue} index={user?.role === 'pm' || user?.role === 'pmo' ? 1 : 2}>
            {riskData && riskData.metrics && (
              <Box>
                {/* Risk Level Cards */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} sm={4}>
                    <Card sx={{ bgcolor: riskData.risk_level.time_risk === 'high' ? 'error.light' : riskData.risk_level.time_risk === 'medium' ? 'warning.light' : 'success.light' }}>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          Time Risk
                        </Typography>
                        <Typography variant="h4">
                          {riskData.risk_level.time_risk.toUpperCase()}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          σ = {riskData.metrics.sigma_time_delay.toFixed(1)} days
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Mean delay: {riskData.metrics.mean_time_delay.toFixed(1)} days
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={4}>
                    <Card sx={{ bgcolor: riskData.risk_level.cost_risk === 'high' ? 'error.light' : riskData.risk_level.cost_risk === 'medium' ? 'warning.light' : 'success.light' }}>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          Cost Risk
                        </Typography>
                        <Typography variant="h4">
                          {riskData.risk_level.cost_risk.toUpperCase()}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          σ = {riskData.metrics.sigma_cost_overrun.toFixed(1)}%
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Mean overrun: {riskData.metrics.mean_cost_overrun.toFixed(1)}%
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={4}>
                    <Card sx={{ bgcolor: riskData.risk_level.overall_risk === 'high' ? 'error.light' : riskData.risk_level.overall_risk === 'medium' ? 'warning.light' : 'success.light' }}>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          Overall Risk
                        </Typography>
                        <Typography variant="h4">
                          {riskData.risk_level.overall_risk.toUpperCase()}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          Completion Shift
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {riskData.forecast.expected_completion_shift}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Completion Probability */}
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Completion Delay Forecast
                    </Typography>
                    <Box sx={{ p: 2 }}>
                      <Box display="flex" alignItems="center" mb={2}>
                        <Typography variant="body2" sx={{ width: 100 }}>
                          P50 (Median):
                        </Typography>
                        <Box sx={{ flexGrow: 1, mx: 2 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={Math.min((riskData.forecast.delay_probability_p50 / 60) * 100, 100)} 
                            color="warning"
                            sx={{ height: 20, borderRadius: 2 }}
                          />
                        </Box>
                        <Typography variant="body2" fontWeight="medium">
                          +{riskData.forecast.delay_probability_p50} days
                        </Typography>
                      </Box>

                      <Box display="flex" alignItems="center">
                        <Typography variant="body2" sx={{ width: 100 }}>
                          P90 (90%):
                        </Typography>
                        <Box sx={{ flexGrow: 1, mx: 2 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={Math.min((riskData.forecast.delay_probability_p90 / 60) * 100, 100)} 
                            color="error"
                            sx={{ height: 20, borderRadius: 2 }}
                          />
                        </Box>
                        <Typography variant="body2" fontWeight="medium">
                          +{riskData.forecast.delay_probability_p90} days
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>

                {/* Distribution Charts */}
                {riskData.distributions && riskData.distributions.time_delays.length > 0 && (
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Time Delay Distribution
                          </Typography>
                          <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={
                              riskData.distributions.time_delays
                                .reduce((acc: any[], delay: number) => {
                                  const bucket = Math.floor(delay / 10) * 10;
                                  const existing = acc.find(item => item.bucket === bucket);
                                  if (existing) {
                                    existing.count += 1;
                                  } else {
                                    acc.push({ bucket: `${bucket}d`, bucketValue: bucket, count: 1 });
                                  }
                                  return acc;
                                }, [])
                                .sort((a, b) => a.bucketValue - b.bucketValue)
                            }>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="bucket" />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="count" fill="#2196f3" name="Frequency" />
                            </BarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            Cost Overrun Distribution
                          </Typography>
                          <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={
                              riskData.distributions.cost_overruns
                                .reduce((acc: any[], overrun: number) => {
                                  const bucket = Math.floor(overrun / 5) * 5;
                                  const existing = acc.find(item => item.bucket === bucket);
                                  if (existing) {
                                    existing.count += 1;
                                  } else {
                                    acc.push({ bucket: `${bucket}%`, bucketValue: bucket, count: 1 });
                                  }
                                  return acc;
                                }, [])
                                .sort((a, b) => a.bucketValue - b.bucketValue)
                            }>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="bucket" />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="count" fill="#ff9800" name="Frequency" />
                            </BarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                )}

                {riskData.metrics.sample_size_time === 0 && (
                  <Alert severity="info">
                    <Typography variant="body2">
                      Insufficient data for risk analysis. Need at least 2 completed decisions with actual payment data.
                    </Typography>
                  </Alert>
                )}
              </Box>
            )}
          </TabPanel>
        </>
      )}
    </Box>
  );
};

