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
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizedDateProvider } from '../components/LocalizedDateProvider.tsx';

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
  const { t, i18n } = useTranslation();
  
  // Locale-aware date formatter for charts
  const isFa = i18n.language?.startsWith('fa');
  const formatDateLabel = useMemo(() => (value: string) => {
    if (!value) return value;
    try {
      // Try parsing as ISO date
      const d = isFa ? jalaliParseISO(value) : gregorianParseISO(value);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd') : gregorianFormat(d, 'yyyy-MM-dd');
    } catch {
      // If parsing fails, try as month string (YYYY-MM)
      if (value.length === 7 && value.match(/^\d{4}-\d{2}$/)) {
        try {
          const iso = `${value}-01`;
          const d = isFa ? jalaliParseISO(iso) : gregorianParseISO(iso);
          return isFa ? jalaliFormat(d, 'yyyy/MM') : value;
        } catch {
          return value;
        }
      }
      return value;
    }
  }, [isFa]);

  // Locale-aware date formatter for display
  const formatDisplayDate = useMemo(() => (dateString: string | Date) => {
    try {
      const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
      if (isFa) {
        return jalaliFormat(date, 'yyyy/MM/dd');
      }
      return gregorianFormat(date, 'yyyy-MM-dd');
    } catch {
      return typeof dateString === 'string' ? dateString : dateString.toISOString().split('T')[0];
    }
  }, [isFa]);
  
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reportsData, setReportsData] = useState<ReportsData | null>(null);
  const [dataSummary, setDataSummary] = useState<any>(null);

  // Global Filters
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
  const [selectedSuppliers, setSelectedSuppliers] = useState<string[]>([]);

  // Filter Options
  const [projects, setProjects] = useState<FilterOption[]>([]);
  const [suppliers, setSuppliers] = useState<FilterOption[]>([]);

  // Load filter options and data summary
  useEffect(() => {
    loadFilterOptions();
    loadDataSummary();
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

  const loadDataSummary = async () => {
    try {
      const response = await reportsAPI.getDataSummary();
      setDataSummary(response.data);
    } catch (err: any) {
      console.error('Failed to load data summary:', err);
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
      if (selectedSuppliers.length > 0) params.supplier_names = selectedSuppliers.join(',');

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
      if (selectedSuppliers.length > 0) params.supplier_names = selectedSuppliers.join(',');

      const response = await reportsAPI.export(params);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const exportDate = formatDisplayDate(new Date());
      link.setAttribute('download', `Reports_${exportDate}.xlsx`);
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

  const handleSupplierChange = (event: SelectChangeEvent<string[]>) => {
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
          <Typography variant="h4">{t('reports.title')}</Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<ExportIcon />}
          onClick={handleExport}
          disabled={loading || !reportsData}
        >
          {t('reports.exportToExcel')}
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
          {t('reports.globalFilters')}
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <LocalizedDateProvider>
              <DatePicker
                label={t('reports.startDate')}
                value={startDate ? new Date(startDate) : null}
                onChange={(newValue) => {
                  if (newValue) {
                    setStartDate(newValue.toISOString().split('T')[0]);
                  } else {
                    setStartDate('');
                  }
                }}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </LocalizedDateProvider>
          </Grid>
          <Grid item xs={12} md={3}>
            <LocalizedDateProvider>
              <DatePicker
                label={t('reports.endDate')}
                value={endDate ? new Date(endDate) : null}
                onChange={(newValue) => {
                  if (newValue) {
                    setEndDate(newValue.toISOString().split('T')[0]);
                  } else {
                    setEndDate('');
                  }
                }}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </LocalizedDateProvider>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Projects</InputLabel>
              <Select
                multiple
                value={selectedProjects}
                onChange={handleProjectChange}
                label={t('reports.projects')}
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
              <InputLabel>{t('reports.suppliers')}</InputLabel>
              <Select
                multiple
                value={selectedSuppliers}
                onChange={handleSupplierChange}
                label={t('reports.suppliers')}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {suppliers.map((supplier) => (
                  <MenuItem key={supplier.id} value={supplier.name}>
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
          <Tab label={t('reports.dataSummary')} />
          <Tab label={t('reports.financialSummary')} />
          <Tab label={t('reports.evmAnalytics')} />
          <Tab label={t('reports.riskForecasts')} />
          <Tab label={t('reports.operationalPerformance')} />
        </Tabs>

        {/* Tab 0: Data Summary */}
        <TabPanel value={tabValue} index={0}>
          {dataSummary && (
            <Box>
              {/* Overall Stats Cards */}
              <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        {t('reports.totalLockedItems')}
                      </Typography>
                      <Typography variant="h3">{dataSummary.overall.total_locked_items}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        {t('reports.finalizedDecisions')}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        {t('reports.projects')}
                      </Typography>
                      <Typography variant="h3">{dataSummary.overall.total_projects}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        {t('reports.activeProjects')}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        {t('reports.suppliers')}
                      </Typography>
                      <Typography variant="h3">{dataSummary.overall.total_suppliers}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        {t('reports.activeSuppliers')}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card sx={{ 
                    backgroundColor: dataSummary.overall.quality_status === 'excellent' ? '#e8f5e9' : 
                                   dataSummary.overall.quality_status === 'good' ? '#fff3e0' : '#ffebee' 
                  }}>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        {t('reports.dataQualityScore')}
                      </Typography>
                      <Typography variant="h3">{dataSummary.overall.data_quality_score}%</Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ textTransform: 'capitalize' }}>
                        {dataSummary.overall.quality_status}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Actuals Data Progress */}
              <Typography variant="h6" gutterBottom>
                {t('reports.actualsDataCompleteness')}
              </Typography>
              <TableContainer component={Paper} sx={{ mb: 3 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('reports.dataType')}</TableCell>
                      <TableCell align="right">{t('reports.count')}</TableCell>
                      <TableCell align="right">{t('reports.percentage')}</TableCell>
                      <TableCell align="right">{t('reports.status')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>{t('reports.itemsWithPaymentData')}</TableCell>
                      <TableCell align="right">{dataSummary.actuals_data.with_payment.count}</TableCell>
                      <TableCell align="right">{dataSummary.actuals_data.with_payment.percent}%</TableCell>
                      <TableCell align="right">
                        <Chip 
                          label={dataSummary.actuals_data.with_payment.percent >= 20 ? t('reports.good') : dataSummary.actuals_data.with_payment.percent >= 10 ? t('reports.fair') : t('reports.limited')} 
                          color={dataSummary.actuals_data.with_payment.percent >= 20 ? 'success' : dataSummary.actuals_data.with_payment.percent >= 10 ? 'warning' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>{t('reports.itemsWithPMAcceptance')}</TableCell>
                      <TableCell align="right">{dataSummary.actuals_data.with_pm_acceptance.count}</TableCell>
                      <TableCell align="right">{dataSummary.actuals_data.with_pm_acceptance.percent}%</TableCell>
                      <TableCell align="right">
                        <Chip 
                          label={dataSummary.actuals_data.with_pm_acceptance.percent >= 20 ? t('reports.good') : dataSummary.actuals_data.with_pm_acceptance.percent >= 10 ? t('reports.fair') : t('reports.limited')} 
                          color={dataSummary.actuals_data.with_pm_acceptance.percent >= 20 ? 'success' : dataSummary.actuals_data.with_pm_acceptance.percent >= 10 ? 'warning' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>{t('reports.itemsWithInvoiceData')}</TableCell>
                      <TableCell align="right">{dataSummary.actuals_data.with_invoice.count}</TableCell>
                      <TableCell align="right">{dataSummary.actuals_data.with_invoice.percent}%</TableCell>
                      <TableCell align="right">
                        <Chip 
                          label={dataSummary.actuals_data.with_invoice.percent >= 20 ? t('reports.good') : dataSummary.actuals_data.with_invoice.percent >= 10 ? t('reports.fair') : t('reports.limited')} 
                          color={dataSummary.actuals_data.with_invoice.percent >= 20 ? 'success' : dataSummary.actuals_data.with_invoice.percent >= 10 ? 'warning' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>{t('reports.itemsWithDeliveryComplete')}</TableCell>
                      <TableCell align="right">{dataSummary.actuals_data.with_delivery_complete.count}</TableCell>
                      <TableCell align="right">{dataSummary.actuals_data.with_delivery_complete.percent}%</TableCell>
                      <TableCell align="right">
                        <Chip 
                          label={dataSummary.actuals_data.with_delivery_complete.percent >= 20 ? t('reports.good') : dataSummary.actuals_data.with_delivery_complete.percent >= 10 ? t('reports.fair') : t('reports.limited')} 
                          color={dataSummary.actuals_data.with_delivery_complete.percent >= 20 ? 'success' : dataSummary.actuals_data.with_delivery_complete.percent >= 10 ? 'warning' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>{t('reports.cashflowInflowEvents')}</TableCell>
                      <TableCell align="right">{dataSummary.actuals_data.cashflow_inflow_events}</TableCell>
                      <TableCell align="right">-</TableCell>
                      <TableCell align="right">
                        <Chip 
                          label={dataSummary.actuals_data.cashflow_inflow_events >= 10 ? t('reports.good') : t('reports.limited')} 
                          color={dataSummary.actuals_data.cashflow_inflow_events >= 10 ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Report Readiness */}
              <Typography variant="h6" gutterBottom>
                {t('reports.reportReadinessStatus')}
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle2" gutterBottom>{t('reports.financialSummary')}</Typography>
                      <Chip 
                        label={t(`reports.${dataSummary.report_readiness.financial_summary.toLowerCase()}`)} 
                        color={dataSummary.report_readiness.financial_summary === 'good' ? 'success' : 'warning'}
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle2" gutterBottom>{t('reports.evmAnalytics')}</Typography>
                      <Chip 
                        label={t(`reports.${dataSummary.report_readiness.evm_analytics.toLowerCase()}`)} 
                        color={dataSummary.report_readiness.evm_analytics === 'good' ? 'success' : 'warning'}
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle2" gutterBottom>{t('reports.riskForecasts')}</Typography>
                      <Chip 
                        label={t(`reports.${dataSummary.report_readiness.risk_forecasts.toLowerCase()}`)} 
                        color={dataSummary.report_readiness.risk_forecasts === 'good' ? 'success' : 'warning'}
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle2" gutterBottom>{t('reports.operationalPerformance')}</Typography>
                      <Chip 
                        label={dataSummary.report_readiness.operational_performance} 
                        color={dataSummary.report_readiness.operational_performance === 'good' ? 'success' : 'warning'}
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Recommendations */}
              {dataSummary.recommendations.filter((r: any) => r !== null).length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom>
                    {t('reports.recommendationsToImproveAnalytics')}
                  </Typography>
                  <Grid container spacing={2}>
                    {dataSummary.recommendations.filter((r: any) => r !== null).map((rec: any, index: number) => (
                      <Grid item xs={12} md={4} key={index}>
                        <Card sx={{ 
                          borderLeft: 4, 
                          borderColor: rec.priority === 'high' ? 'error.main' : 'warning.main' 
                        }}>
                          <CardContent>
                            <Box display="flex" alignItems="center" gap={1} mb={1}>
                              <Chip 
                                label={rec.priority.toUpperCase()} 
                                color={rec.priority === 'high' ? 'error' : 'warning'}
                                size="small"
                              />
                            </Box>
                            <Typography variant="h6" gutterBottom>
                              {rec.action}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" paragraph>
                              {rec.impact}
                            </Typography>
                            <Box display="flex" justifyContent="space-between" alignItems="center">
                              <Typography variant="body2">
                                {t('reports.current')}: <strong>{rec.current}</strong>
                              </Typography>
                              <Typography variant="body2">
                                {t('reports.target')}: <strong>{rec.target}</strong>
                              </Typography>
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </>
              )}
            </Box>
          )}
        </TabPanel>

        {/* Tab 1: Financial Summary */}
        <TabPanel value={tabValue} index={1}>
          {reportsData && (
            <Box>
              {/* Cash Flow Analysis Chart */}
              <Typography variant="h6" gutterBottom>
                {t('reports.cashFlowAnalysis')}
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
                    <XAxis dataKey="date" tickFormatter={formatDateLabel} />
                    <YAxis />
                    <Tooltip formatter={(value: any) => formatCurrency(value)} labelFormatter={formatDateLabel} />
                    <Legend />
                    <Bar dataKey="inflow" fill="#4caf50" name={t('reports.cashInflow')} />
                    <Bar dataKey="outflow" fill="#f44336" name={t('reports.cashOutflow')} />
                    <Line
                      type="monotone"
                      dataKey="cumulative"
                      stroke="#2196f3"
                      strokeWidth={3}
                      name={t('reports.cumulativeBalance')}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </Paper>

              {/* Budget vs Actuals Table */}
              <Typography variant="h6" gutterBottom>
                {t('reports.budgetVsActualsSummary')}
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('reports.projectName')}</TableCell>
                      <TableCell align="right">{t('reports.plannedCost')}</TableCell>
                      <TableCell align="right">{t('reports.actualCost')}</TableCell>
                      <TableCell align="right">{t('reports.varianceDollar')}</TableCell>
                      <TableCell align="right">{t('reports.variancePercent')}</TableCell>
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
        <TabPanel value={tabValue} index={2}>
          {reportsData && (
            <Box>
              {/* EVM Performance Chart */}
              <Typography variant="h6" gutterBottom>
                {t('reports.coreEVMPerformance')}
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
                    <XAxis dataKey="date" tickFormatter={formatDateLabel} />
                    <YAxis />
                    <Tooltip formatter={(value: any) => formatCurrency(value)} labelFormatter={formatDateLabel} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="pv"
                      stroke="#8884d8"
                      strokeWidth={2}
                      name={t('reports.plannedValuePV')}
                    />
                    <Line
                      type="monotone"
                      dataKey="ev"
                      stroke="#82ca9d"
                      strokeWidth={2}
                      name={t('reports.earnedValueEV')}
                    />
                    <Line
                      type="monotone"
                      dataKey="ac"
                      stroke="#ff7300"
                      strokeWidth={2}
                      name={t('reports.actualCostAC')}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>

              {/* KPI Trends Chart */}
              <Typography variant="h6" gutterBottom>
                {t('reports.kpiTrendsCPISPI')}
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
                    <XAxis dataKey="date" tickFormatter={formatDateLabel} />
                    <YAxis domain={[0, 2]} />
                    <Tooltip formatter={(value: any) => formatNumber(value, 3)} labelFormatter={formatDateLabel} />
                    <Legend />
                    <ReferenceLine y={1.0} stroke="#666" strokeDasharray="3 3" label={t('reports.target10')} />
                    <Line
                      type="monotone"
                      dataKey="cpi"
                      stroke="#4caf50"
                      strokeWidth={2}
                      name={t('reports.costPerformanceIndexCPI')}
                    />
                    <Line
                      type="monotone"
                      dataKey="spi"
                      stroke="#2196f3"
                      strokeWidth={2}
                      name={t('reports.schedulePerformanceIndexSPI')}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>

              {/* Project KPI Breakdown Table */}
              <Typography variant="h6" gutterBottom>
                {t('reports.projectKPIBreakdown')}
              </Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('reports.project')}</TableCell>
                      <TableCell align="right">{t('reports.pv')}</TableCell>
                      <TableCell align="right">{t('reports.ev')}</TableCell>
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
        <TabPanel value={tabValue} index={3}>
          {reportsData && (
            <Box>
              {/* Delay Forecast Cards */}
              <Typography variant="h6" gutterBottom>
                {t('reports.completionDelayForecast')}
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        {t('reports.p50MedianDelay')}
                      </Typography>
                      <Typography variant="h3" component="div">
                        {formatNumber(reportsData.risk_forecasts.delay_forecast.p50, 1)} {t('reports.days')}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {t('reports.p50Description')}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        {t('reports.p90Delay')}
                      </Typography>
                      <Typography variant="h3" component="div">
                        {formatNumber(reportsData.risk_forecasts.delay_forecast.p90, 1)} {t('reports.days')}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {t('reports.p90Description')}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Payment Delay Distribution */}
              <Typography variant="h6" gutterBottom>
                {t('reports.timeDelayDistribution')}
              </Typography>
              <Paper sx={{ p: 2, mb: 3 }}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={reportsData.risk_forecasts.payment_delay_histogram}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="delay_bucket"
                      label={{ value: t('reports.delayDays'), position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis label={{ value: t('reports.count'), angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" name={t('reports.numberOfItems')} />
                  </BarChart>
                </ResponsiveContainer>
              </Paper>

              {/* Top 5 Risk Items */}
              <Typography variant="h6" gutterBottom>
                {t('reports.top5HighestRiskItems')}
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('reports.itemName')}</TableCell>
                      <TableCell>{t('reports.project')}</TableCell>
                      <TableCell align="right">{t('reports.costVarianceDollar')}</TableCell>
                      <TableCell align="right">{t('reports.scheduleDelayDays')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {reportsData.risk_forecasts.top_risk_items.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography color="textSecondary">{t('reports.noRiskItemsFound')}</Typography>
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
        <TabPanel value={tabValue} index={4}>
          {reportsData && (
            <Box>
              {/* Supplier Scorecard */}
              <Typography variant="h6" gutterBottom>
                {t('reports.supplierScorecard')}
              </Typography>
              <TableContainer component={Paper} sx={{ mb: 3 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('reports.supplierName')}</TableCell>
                      <TableCell align="right">{t('reports.totalOrders')}</TableCell>
                      <TableCell align="right">{t('reports.onTimeDeliveryRate')}</TableCell>
                      <TableCell align="right">{t('reports.avgCostVariance')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {reportsData.operational_performance.supplier_scorecard.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography color="textSecondary">{t('reports.noSuppliersFound')}</Typography>
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
                {t('reports.procurementCycleTimeDistribution')}
              </Typography>
              <Paper sx={{ p: 2 }}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={reportsData.operational_performance.procurement_cycle_time}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="cycle_time_bucket"
                      label={{ value: t('reports.cycleTimeDays'), position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis label={{ value: t('reports.count'), angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#82ca9d" name={t('reports.numberOfItems')} />
                  </BarChart>
                </ResponsiveContainer>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 2, textAlign: 'center' }}>
                  {t('reports.timeElapsedBetween')}
                </Typography>
              </Paper>
            </Box>
          )}
        </TabPanel>
      </Paper>
    </Box>
  );
};

