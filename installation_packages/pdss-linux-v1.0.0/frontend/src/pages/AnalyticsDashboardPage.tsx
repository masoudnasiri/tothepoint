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
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';

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

interface ItemFollowUpTabProps {
  data: any[];
  loading: boolean;
  selectedProjectId: number | 'all';
}

const ItemFollowUpTab: React.FC<ItemFollowUpTabProps> = ({ data, loading, selectedProjectId }) => {
  const { t, i18n } = useTranslation();
  
  // Locale-aware date formatter for this component
  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDate = React.useMemo(() => (dateString: string | null) => {
    if (!dateString) return '-';
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd') : gregorianFormat(d, 'yyyy-MM-dd');
    } catch {
      return new Date(dateString).toLocaleDateString(i18n.language === 'fa' ? 'fa-IR' : 'en-US');
    }
  }, [isFa, i18n.language]);

  console.log('DEBUG: ItemFollowUpTab received data:', data);
  console.log('DEBUG: ItemFollowUpTab loading:', loading);
  console.log('DEBUG: ItemFollowUpTab selectedProjectId:', selectedProjectId);

  const getStatusChip = (status: string) => {
    const statusConfig = {
      'CREATED': { color: 'default', label: t('itemFollowUp.status.created') },
      'DELIVERY_ADDED': { color: 'info', label: t('itemFollowUp.status.deliveryAdded') },
      'FINALIZED': { color: 'primary', label: t('itemFollowUp.status.finalized') },
      'PROCUREMENT_OPTIONS': { color: 'secondary', label: t('itemFollowUp.status.procurementOptions') },
      'READY_FOR_OPTIMIZATION': { color: 'warning', label: t('itemFollowUp.status.readyForOptimization') },
      'PROPOSED': { color: 'warning', label: t('itemFollowUp.status.proposed') },
      'LOCKED': { color: 'success', label: t('itemFollowUp.status.locked') },
      'PROCUREMENT_PLAN': { color: 'info', label: t('itemFollowUp.status.procurementPlan') },
      'CONFIRMED_BY_PROCUREMENT': { color: 'warning', label: t('itemFollowUp.status.confirmedByProcurement') },
      'DELIVERY_COMPLETE': { color: 'success', label: t('itemFollowUp.status.deliveryComplete') },
      'ORDERED': { color: 'secondary', label: t('itemFollowUp.status.ordered') },
      'DELIVERED': { color: 'success', label: t('itemFollowUp.status.delivered') },
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', label: status };
    return <Chip label={config.label} color={config.color as any} size="small" />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Alert severity="info">
        {t('itemFollowUp.noData')}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('itemFollowUp.title')}
      </Typography>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('itemFollowUp.itemName')}</TableCell>
              <TableCell>{t('itemFollowUp.quantity')}</TableCell>
              <TableCell>{t('itemFollowUp.leadTime')}</TableCell>
              <TableCell>{t('itemFollowUp.deliveryTime')}</TableCell>
              <TableCell>{t('itemFollowUp.statusLabel')}</TableCell>
              <TableCell>{t('itemFollowUp.procurementOptions')}</TableCell>
              <TableCell>{t('itemFollowUp.notes')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((item, index) => (
              <TableRow key={index}>
                <TableCell>{item.item_name}</TableCell>
                <TableCell>{item.quantity}</TableCell>
                <TableCell>
                  {formatDisplayDate(item.lead_time_date)}
                </TableCell>
                <TableCell>
                  {formatDisplayDate(item.delivery_time_date)}
                </TableCell>
                <TableCell>{getStatusChip(item.status)}</TableCell>
                <TableCell>
                  {item.procurement_options_count > 0 ? (
                    <Chip 
                      label={`${item.procurement_options_count} ${item.procurement_options_finalized ? t('itemFollowUp.finalized') : t('itemFollowUp.pending')}`}
                      color={item.procurement_options_finalized ? 'success' : 'warning'}
                      size="small"
                    />
                  ) : (
                    <Chip label={t('itemFollowUp.none')} color="default" size="small" />
                  )}
                </TableCell>
                <TableCell>{item.notes || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export const AnalyticsDashboardPage: React.FC = () => {
  const { user } = useAuth();
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
  
  const [tabValue, setTabValue] = useState(0);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | 'all'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Currency display mode (same as Dashboard)
  const [currencyDisplayMode, setCurrencyDisplayMode] = useState<'original' | 'unified'>('unified');
  
  // Analytics data
  const [evaData, setEvaData] = useState<any>(null);
  const [cashflowData, setCashflowData] = useState<any>(null);
  const [riskData, setRiskData] = useState<any>(null);
  const [projectsSummary, setProjectsSummary] = useState<any>(null);
  const [itemFollowUpData, setItemFollowUpData] = useState<any[]>([]);
  
  // Multi-currency data (same pattern as Dashboard)
  const [evaByCurrency, setEvaByCurrency] = useState<{[key: string]: any}>({});
  const [cashflowByCurrency, setCashflowByCurrency] = useState<{[key: string]: any}>({});

  useEffect(() => {
    fetchProjects();
    fetchAllProjectsSummary();
  }, []);

  useEffect(() => {
    console.log('DEBUG: useEffect triggered with selectedProjectId:', selectedProjectId, 'currencyDisplayMode:', currencyDisplayMode);
    if (selectedProjectId) {
      fetchProjectAnalytics();
      fetchItemFollowUp();
    }
  }, [selectedProjectId, currencyDisplayMode]); // Re-fetch when project or currency mode changes

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.list();
      // PM sees only assigned projects, PMO/Admin/Finance see all
      setProjects(response.data);
      
      // Default selection
      if (user?.role === 'pm') {
        // PM: Default to first assigned project (no "All Projects" option)
        if (response.data.length > 0) {
          setSelectedProjectId(response.data[0].id);
        }
      } else {
        // PMO/Admin/Finance: Default to "All Projects" portfolio view
        setSelectedProjectId('all');
      }
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
      // Use currency_view parameter based on selected mode
      const currencyView = currencyDisplayMode === 'unified' ? 'unified' : 'original';
      
      const [evaResponse, cashflowResponse, riskResponse] = await Promise.all([
        analyticsAPI.getEVA(selectedProjectId, currencyView),
        analyticsAPI.getCashflowForecast(selectedProjectId, 12, currencyView),
        analyticsAPI.getRisk(selectedProjectId),
      ]);
      
      // Handle multi-currency response format (same pattern as Dashboard)
      console.log('DEBUG: EVA response:', evaResponse.data);
      console.log('DEBUG: Cashflow response:', cashflowResponse.data);
      
      if (currencyDisplayMode === 'original' && evaResponse.data.view_mode === 'original' && evaResponse.data.currencies) {
        // Multi-currency response - store all currencies
        console.log('DEBUG: Setting EVA by currency:', Object.keys(evaResponse.data.currencies));
        setEvaByCurrency(evaResponse.data.currencies);
        // Also set main data to IRR for backward compatibility
        const irrData = evaResponse.data.currencies['IRR'] || evaResponse.data;
        setEvaData(irrData);
      } else {
        // Unified response
        console.log('DEBUG: Using unified EVA data');
        setEvaData(evaResponse.data);
        setEvaByCurrency({});
      }
      
      if (currencyDisplayMode === 'original' && cashflowResponse.data.view_mode === 'original' && cashflowResponse.data.currencies) {
        // Multi-currency response - store all currencies
        console.log('DEBUG: Setting Cashflow by currency:', Object.keys(cashflowResponse.data.currencies));
        setCashflowByCurrency(cashflowResponse.data.currencies);
        // Also set main data to IRR for backward compatibility
        const irrData = cashflowResponse.data.currencies['IRR'] || cashflowResponse.data;
        setCashflowData(irrData);
      } else {
        // Unified response
        console.log('DEBUG: Using unified Cashflow data');
        setCashflowData(cashflowResponse.data);
        setCashflowByCurrency({});
      }
      
      setRiskData(riskResponse.data);
      
      // Also fetch project summary if needed
      if (selectedProjectId === 'all') {
        const summaryResponse = await analyticsAPI.getAllProjectsSummary();
        setProjectsSummary(summaryResponse.data);
      }
      
      console.log('DEBUG: Analytics data loaded successfully');
      console.log('DEBUG: EVA data:', evaResponse.data);
      console.log('DEBUG: Cashflow data:', cashflowResponse.data);
      
    } catch (err: any) {
      console.error('Analytics fetch error:', err);
      setError(err.response?.data?.detail || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const fetchItemFollowUp = async () => {
    if (!selectedProjectId) {
      console.log('DEBUG: No selectedProjectId, skipping fetchItemFollowUp');
      return;
    }
    
    try {
      console.log('DEBUG: Fetching item follow-up for project:', selectedProjectId);
      console.log('DEBUG: About to call analyticsAPI.getItemFollowUp');
      const response = await analyticsAPI.getItemFollowUp(selectedProjectId);
      console.log('DEBUG: Item follow-up response:', response);
      console.log('DEBUG: Item follow-up data:', response.data);
      setItemFollowUpData(response.data);
    } catch (err: any) {
      console.error('Failed to load item follow-up data:', err);
      console.error('Error details:', err.response?.data);
      setItemFollowUpData([]);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value) + ' ﷼';
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
    if (!projectsSummary || !projectsSummary.projects) return 'unknown';
    const project = projectsSummary.projects.find((p: any) => p.project_id === projectId);
    
    if (!project) return 'unknown';
    
    // Combine health (CPI/SPI) and risk_level (variance analysis)
    // If EITHER shows critical/high → show as critical
    // If EITHER shows at_risk/medium → show as at_risk
    const health = project.health; // 'healthy', 'at_risk', 'critical', 'unknown'
    const riskLevel = project.risk_level; // 'low', 'medium', 'high', or null
    
    console.log(`DEBUG: Project ${project.project_code} - health: ${health}, risk_level: ${riskLevel}, CPI: ${project.cpi}, SPI: ${project.spi}`);
    
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
          <Typography variant="h4">{t('analytics.title')}</Typography>
          <Typography variant="subtitle2" color="textSecondary">
            {t('analytics.subtitle')}
          </Typography>
        </Box>
        <FormControl sx={{ minWidth: 300 }}>
          <InputLabel>{t('analytics.selectProject')}</InputLabel>
          <Select
            value={selectedProjectId || 'all'}
            onChange={(e) => setSelectedProjectId(e.target.value === 'all' ? 'all' : Number(e.target.value))}
            label={t('analytics.selectProject')}
          >
            {/* Show "All Projects" only for PMO, Admin, Finance (not PM) */}
            {user?.role !== 'pm' && (
              <MenuItem value="all">
                <strong>📊 {t('analytics.allProjects')} ({t('analytics.portfolioView')})</strong>
              </MenuItem>
            )}
            {projects.map((project) => {
              const riskLevel = getProjectRiskLevel(project.id);
              // Map both health levels (critical/at_risk/healthy) and risk levels (high/medium/low)
              const riskColor = (riskLevel === 'critical' || riskLevel === 'high') ? '#f44336' : 
                               (riskLevel === 'at_risk' || riskLevel === 'medium') ? '#ff9800' : 
                               (riskLevel === 'healthy' || riskLevel === 'low') ? '#4caf50' : '#757575';
              const riskIcon = (riskLevel === 'critical' || riskLevel === 'high') ? '🔴 ' : 
                              (riskLevel === 'at_risk' || riskLevel === 'medium') ? '🟡 ' : 
                              (riskLevel === 'healthy' || riskLevel === 'low') ? '🟢 ' : '⚪ ';
              
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
        
        {/* Currency Display Mode Selector (same as Dashboard) */}
        <Box display="flex" gap={1}>
          <Chip
            label={t('analytics.unifiedIRR')}
            variant={currencyDisplayMode === 'unified' ? 'filled' : 'outlined'}
            color={currencyDisplayMode === 'unified' ? 'primary' : 'default'}
            onClick={() => setCurrencyDisplayMode('unified')}
            clickable
          />
          <Chip
            label={t('analytics.originalCurrencies')}
            variant={currencyDisplayMode === 'original' ? 'filled' : 'outlined'}
            color={currencyDisplayMode === 'original' ? 'primary' : 'default'}
            onClick={() => setCurrencyDisplayMode('original')}
            clickable
          />
        </Box>
      </Box>

      {/* Currency Display Information (same as Dashboard) */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h6" gutterBottom>
              {t('analytics.currencyDisplay')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {currencyDisplayMode === 'unified' 
                ? t('analytics.showingAllFinancialData')
                : t('analytics.showingFinancialDataOriginal')
              }
            </Typography>
          </Box>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} aria-label="analytics tabs">
          <Tab label={t('analytics.earnedValueAnalytics')} icon={<AssessmentIcon />} iconPosition="start" />
          <Tab label={t('analytics.itemFollowUp')} icon={<ScheduleIcon />} iconPosition="start" />
          {user?.role !== 'pm' && user?.role !== 'pmo' && (
            <Tab label={t('analytics.cashFlowForecast')} icon={<AccountBalanceIcon />} iconPosition="start" />
          )}
          <Tab label={t('analytics.riskAnalysis')} icon={<WarningIcon />} iconPosition="start" />
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
                              {t('analytics.cpiCostPerformance')}
                            </Typography>
                            <Typography variant="h4">
                              {evaData.metrics.cpi.toFixed(2)}
                            </Typography>
                            <Chip
                              label={t(`analytics.${evaData.health_status.cost_performance.toLowerCase()}`)}
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
                              {t('analytics.spiSchedulePerformance')}
                            </Typography>
                            <Typography variant="h4">
                              {evaData.metrics.spi.toFixed(2)}
                            </Typography>
                            <Chip
                              label={t(`analytics.${evaData.health_status.schedule_performance.toLowerCase()}`)}
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
                              {t('analytics.costVariance')}
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
                                {evaData.metrics.cv >= 0 ? t('analytics.underBudget') : t('analytics.overBudget')}
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
                              {t('analytics.scheduleVariance')}
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
                                {evaData.metrics.sv >= 0 ? t('analytics.ahead') : t('analytics.behind')}
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
                          {t('analytics.budgetAtCompletion')}
                        </Typography>
                        <Typography variant="h5">{formatCurrency(evaData.metrics.bac)}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          {t('analytics.estimateAtCompletion')}
                        </Typography>
                        <Typography variant="h5">{formatCurrency(evaData.metrics.eac)}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {t('analytics.vac')}: {formatCurrency(evaData.metrics.vac)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={4}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          {t('analytics.projectHealth')}
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getHealthIcon(evaData.health_status.overall)}
                          <Chip
                            label={t(`analytics.${evaData.health_status.overall.toLowerCase()}`)}
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
                      {t('analytics.projectProgress')}
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          {t('analytics.completionProgress')}: {evaData.progress.percent_complete}%
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={evaData.progress.percent_complete} 
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                        <Typography variant="caption" color="textSecondary">
                          {evaData.progress.items_completed} {t('analytics.of')} {evaData.progress.total_items} {t('analytics.itemsCompleted')}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          {t('analytics.plannedProgress')}: {evaData.progress.percent_planned}%
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={evaData.progress.percent_planned} 
                          color="secondary"
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                        <Typography variant="caption" color="textSecondary">
                          {evaData.progress.items_planned} {t('analytics.itemsShouldBeDone')}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>

                {/* EV/PV/AC Chart */}
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {t('analytics.earnedValueTrends')}
                    </Typography>
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={evaData.time_series}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" tickFormatter={formatDateLabel} />
                        <YAxis />
                        <Tooltip formatter={(value: any) => formatCurrency(value)} labelFormatter={formatDateLabel} />
                        <Legend />
                        <Line type="monotone" dataKey="pv" stroke="#2196f3" name={t('analytics.plannedValue')} strokeWidth={2} />
                        <Line type="monotone" dataKey="ev" stroke="#4caf50" name={t('analytics.earnedValue')} strokeWidth={2} />
                        <Line type="monotone" dataKey="ac" stroke="#f44336" name={t('analytics.actualCost')} strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* CPI/SPI Trends */}
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {t('analytics.performanceIndexTrend')}
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={evaData.time_series}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" tickFormatter={formatDateLabel} />
                        <YAxis domain={[0.5, 1.5]} />
                        <Tooltip formatter={(value: any) => value.toFixed(3)} labelFormatter={formatDateLabel} />
                        <Legend />
                        <Line type="monotone" dataKey="cpi" stroke="#ff9800" name={t('analytics.costPerformance')} strokeWidth={2} />
                        <Line type="monotone" dataKey="spi" stroke="#9c27b0" name={t('analytics.schedulePerformance')} strokeWidth={2} />
                        <Line 
                          type="monotone" 
                          dataKey={() => 1.0} 
                          stroke="#666" 
                          strokeDasharray="5 5" 
                          name={t('analytics.target')}
                          strokeWidth={1}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Box>
            )}
          </TabPanel>

          {/* Item Follow-up Tab */}
          <TabPanel value={tabValue} index={1}>
            <ItemFollowUpTab 
              data={itemFollowUpData} 
              loading={loading}
              selectedProjectId={selectedProjectId}
            />
          </TabPanel>

          {/* Cash Flow Forecast Tab - Hidden for PM/PMO */}
          {user?.role !== 'pm' && user?.role !== 'pmo' && (
            <TabPanel value={tabValue} index={2}>
            {cashflowData && (
              <Box>
                {/* Summary Cards */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          {t('analytics.finalBalanceForecast')}
                        </Typography>
                        <Typography variant="h5">
                          {formatCurrency(cashflowData.summary.final_balance)}
                        </Typography>
                        <Chip
                          label={cashflowData.summary.final_balance >= 0 ? t('analytics.positive') : t('analytics.negative')}
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
                          {t('analytics.maximumDeficit')}
                        </Typography>
                        <Typography variant="h5">
                          {formatCurrency(cashflowData.summary.max_deficit)}
                        </Typography>
                        {cashflowData.summary.max_deficit < 0 && (
                          <Chip label={t('analytics.gapDetected')} color="warning" size="small" sx={{ mt: 1 }} />
                        )}
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          {t('analytics.financingNeeded')}
                        </Typography>
                        <Typography variant="h5">
                          {formatCurrency(cashflowData.summary.financing_needed)}
                        </Typography>
                        {cashflowData.summary.financing_needed > 0 && (
                          <Typography variant="caption" color="error">
                            {t('analytics.bridgeFinancingRequired')}
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom variant="subtitle2">
                          {t('analytics.totalInflowForecast')}
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
                      {t('analytics.cashFlowInflowVsOutflow')}
                    </Typography>
                    <ResponsiveContainer width="100%" height={400}>
                      <ComposedChart data={cashflowData.forecast_data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" tickFormatter={formatDateLabel} />
                        <YAxis />
                        <Tooltip formatter={(value: any) => formatCurrency(value)} labelFormatter={formatDateLabel} />
                        <Legend />
                        <Bar dataKey="inflow_forecast" fill="#4caf50" name={t('analytics.inflowForecast')} />
                        <Bar dataKey="outflow_forecast" fill="#f44336" name={t('analytics.outflowForecast')} />
                        <Bar dataKey="inflow_actual" fill="#2e7d32" name={t('analytics.inflowActual')} />
                        <Bar dataKey="outflow_actual" fill="#c62828" name={t('analytics.outflowActual')} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* Cumulative Balance */}
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {t('analytics.cumulativeNetBalance')}
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={cashflowData.forecast_data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" tickFormatter={formatDateLabel} />
                        <YAxis />
                        <Tooltip formatter={(value: any) => formatCurrency(value)} labelFormatter={formatDateLabel} />
                        <Legend />
                        <Area 
                          type="monotone" 
                          dataKey="cumulative_balance" 
                          stroke="#2196f3" 
                          fill="#2196f3"
                          fillOpacity={0.3}
                          name={t('analytics.cumulativeBalance')}
                        />
                        <Line 
                          type="monotone" 
                          dataKey={() => 0} 
                          stroke="#f44336" 
                          strokeDasharray="5 5" 
                          name={t('analytics.breakEven')}
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
          <TabPanel value={tabValue} index={user?.role === 'pm' || user?.role === 'pmo' ? 2 : 3}>
            {riskData && riskData.metrics && riskData.risk_level && (
              <Box>
                {/* Risk Level Cards */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} sm={4}>
                    <Card sx={{ bgcolor: riskData.risk_level.time_risk === 'high' ? 'error.light' : riskData.risk_level.time_risk === 'medium' ? 'warning.light' : 'success.light' }}>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          {t('analytics.timeRisk')}
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
                          {t('analytics.costRisk')}
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
                          {t('analytics.overallRisk')}
                        </Typography>
                        <Typography variant="h4">
                          {riskData.risk_level.overall_risk.toUpperCase()}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {t('analytics.completionShift')}
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
                      {t('analytics.completionDelayForecast')}
                    </Typography>
                    <Box sx={{ p: 2 }}>
                      <Box display="flex" alignItems="center" mb={2}>
                        <Typography variant="body2" sx={{ width: 100 }}>
                          {t('analytics.p50Median')}:
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
                          {t('analytics.p90')}:
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
                            {t('analytics.timeDelayDistribution')}
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
                              <Bar dataKey="count" fill="#2196f3" name={t('analytics.frequency')} />
                            </BarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            {t('analytics.costOverrunDistribution')}
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
                              <Bar dataKey="count" fill="#ff9800" name={t('analytics.frequency')} />
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
            
            {/* Show message when no risk data available */}
            {(!riskData || !riskData.metrics || !riskData.risk_level) && (
              <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <Alert severity="info" sx={{ maxWidth: 600 }}>
                  <Typography variant="h6" gutterBottom>
                    {t('analytics.noRiskDataAvailable')}
                  </Typography>
                  <Typography variant="body2">
                    {t('analytics.riskAnalysisRequires')}
                  </Typography>
                </Alert>
              </Box>
            )}
          </TabPanel>
        </>
      )}
    </Box>
  );
};

