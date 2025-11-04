import React, { useState, useEffect, useMemo } from 'react';
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
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
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
  Cell,
  ComposedChart,
} from 'recharts';
import { decisionsAPI } from '../services/api.ts';
import { useTranslation } from 'react-i18next';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat } from 'date-fns';

interface BudgetAnalysisProps {
  projectIds?: number[];
  startDate?: string;
  endDate?: string;
  onAnalysisComplete?: (status: string) => void;
}

interface CurrencyData {
  outflow: number;
  inflow: number;
  cumulative_outflow: number;
  cumulative_inflow: number;
  cumulative_budget: number;
  cumulative_position: number;
  gap: number;
  gap_percentage: number;
  status: string;
}

interface PeriodData {
  period: string;
  currencies: Record<string, CurrencyData>;
}

interface RecommendationItem {
  type: 'header' | 'divider' | 'currency_header' | 'info' | 'warning' | 'success' | 'action';
  key: string;
  params?: Record<string, any>;
}

interface BudgetAnalysisData {
  status: string;
  periods: PeriodData[];
  total_needed_by_currency: Record<string, number>;
  total_available_by_currency: Record<string, number>;
  gap_by_currency: Record<string, number>;
  recommendations: (string | RecommendationItem)[]; // Support both old string format and new structured format
  critical_months: string[];
}

export const BudgetAnalysis: React.FC<BudgetAnalysisProps> = ({
  projectIds,
  startDate,
  endDate,
  onAnalysisComplete,
}) => {
  const { t, i18n } = useTranslation();
  const isFa = i18n.language?.startsWith('fa');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<BudgetAnalysisData | null>(null);

  // Format period labels for charts and displays (convert YYYY-MM to Jalali if needed)
  const formatPeriodLabel = useMemo(() => (period: string) => {
    if (!period || period.length !== 7 || !period.match(/^\d{4}-\d{2}$/)) {
      return period;
    }
    try {
      if (isFa) {
        const iso = `${period}-01`;
        const d = jalaliParseISO(iso);
        return jalaliFormat(d, 'yyyy/MM');
      }
      return period;
    } catch {
      return period;
    }
  }, [isFa]);

  useEffect(() => {
    fetchBudgetAnalysis();
  }, [projectIds, startDate, endDate]);

  const fetchBudgetAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const params: any = {};
      if (projectIds && projectIds.length > 0) {
        params.project_ids = projectIds.join(',');
      }
      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }

      const response = await decisionsAPI.getBudgetAnalysis(params);
      setAnalysisData(response.data);
      
      if (onAnalysisComplete) {
        onAnalysisComplete(response.data.status);
      }
    } catch (err: any) {
      console.error('Budget analysis error:', err);
      console.error('Error response:', err.response?.data);
      
      // Handle Pydantic validation errors
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Pydantic validation error array
          const errorMessages = err.response.data.detail.map((e: any) => 
            `${e.loc?.join(' -> ') || 'Field'}: ${e.msg}`
          ).join(', ');
          setError(`Validation error: ${errorMessages}`);
        } else if (typeof err.response.data.detail === 'string') {
          setError(err.response.data.detail);
        } else {
          setError(JSON.stringify(err.response.data.detail));
        }
      } else {
        setError('Failed to load budget analysis');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number, currency: string) => {
    if (currency === 'IRR') {
      return `${value.toLocaleString('en-US', { maximumFractionDigits: 0 })} ﷼`;
    } else {
      return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
  };

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OK':
        return '#4caf50';
      case 'WARNING':
        return '#ff9800';
      case 'CRITICAL':
        return '#f44336';
      default:
        return '#2196f3';
    }
  };

  const prepareChartData = () => {
    if (!analysisData) return [];

    return analysisData.periods.map(period => {
      const data: any = { period: period.period };
      
      Object.entries(period.currencies).forEach(([currency, currencyData]) => {
        data[`${currency}_outflow`] = currencyData.cumulative_outflow;
        data[`${currency}_inflow`] = currencyData.cumulative_inflow;
        data[`${currency}_budget`] = currencyData.cumulative_budget;
        data[`${currency}_position`] = currencyData.cumulative_position;
        data[`${currency}_gap`] = currencyData.gap;
      });
      
      return data;
    });
  };

  const prepareTotalsByCurrency = () => {
    if (!analysisData) return [];

    const currencies = Object.keys(analysisData.total_needed_by_currency);
    return currencies.map(currency => ({
      currency,
      needed: analysisData.total_needed_by_currency[currency],
      available: analysisData.total_available_by_currency[currency],
      gap: analysisData.gap_by_currency[currency],
    }));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
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

  const chartData = prepareChartData();
  const totalsByCurrency = prepareTotalsByCurrency();
  const currencies = Object.keys(analysisData.total_needed_by_currency);

  return (
    <Box>
      {/* Status Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={2}>
              {getStatusIcon(analysisData.status)}
              <Typography variant="h5">
                {t('optimization.budgetAnalysisStatus', { status: analysisData.status })}
              </Typography>
            </Box>
            <Chip
              label={analysisData.status}
              color={
                analysisData.status === 'OK' ? 'success' :
                analysisData.status === 'WARNING' ? 'warning' : 'error'
              }
              size="large"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Critical Months Alert */}
      {analysisData.critical_months.length > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>⚠️ {t('optimization.criticalMonthsDetected')}</AlertTitle>
          <Typography variant="body2">
            {t('optimization.budgetDeficitsFoundIn', { 
              months: analysisData.critical_months.map(p => formatPeriodLabel(p)).join(', ') 
            })}
          </Typography>
        </Alert>
      )}

      {/* Total Budget Summary by Currency */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {totalsByCurrency.map((currencyData) => (
          <Grid item xs={12} md={6} key={currencyData.currency}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('optimization.budgetSummary', { currency: currencyData.currency })}
                </Typography>
                <Divider sx={{ my: 2 }} />
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    {t('optimization.totalNeeded')}
                  </Typography>
                  <Typography variant="h5" sx={{ color: '#2196f3' }}>
                    {formatCurrency(currencyData.needed, currencyData.currency)}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    {t('optimization.totalAvailable')}
                  </Typography>
                  <Typography variant="h5" sx={{ color: '#4caf50' }}>
                    {formatCurrency(currencyData.available, currencyData.currency)}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    {t('optimization.gap')}
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography 
                      variant="h5" 
                      sx={{ color: currencyData.gap >= 0 ? '#4caf50' : '#f44336' }}
                    >
                      {formatCurrency(Math.abs(currencyData.gap), currencyData.currency)}
                    </Typography>
                    {currencyData.gap >= 0 ? (
                      <TrendingUpIcon sx={{ color: '#4caf50' }} />
                    ) : (
                      <TrendingDownIcon sx={{ color: '#f44336' }} />
                    )}
                  </Box>
                  <Typography variant="caption" color="textSecondary">
                    {currencyData.gap >= 0 ? t('optimization.surplus') : t('optimization.deficit')}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Cumulative Cash Flow & Budget Chart */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('optimization.cumulativeCashFlowBudgetByPeriod')}
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            {t('optimization.showsCumulativeOutflows')}
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="period" 
                tickFormatter={formatPeriodLabel}
              />
              <YAxis />
              <Tooltip 
                formatter={(value: number, name: string) => {
                  const currency = name.split('_')[0];
                  return formatCurrency(value, currency);
                }}
                labelFormatter={formatPeriodLabel}
              />
              <Legend />
              {currencies.map((currency, index) => (
                <React.Fragment key={currency}>
                  <Bar 
                    dataKey={`${currency}_outflow`} 
                    fill={index === 0 ? '#f44336' : '#ff5722'} 
                    name={t('optimization.cumulativeOutflowLabel', { currency })}
                    stackId={`stack${index}`}
                  />
                  <Bar 
                    dataKey={`${currency}_inflow`} 
                    fill={index === 0 ? '#4caf50' : '#8bc34a'} 
                    name={t('optimization.cumulativeInflowLabel', { currency })}
                    stackId={`stack${index}`}
                  />
                  <Line 
                    type="monotone"
                    dataKey={`${currency}_budget`} 
                    stroke={index === 0 ? '#2196f3' : '#ff9800'} 
                    strokeWidth={3}
                    name={t('optimization.cumulativeBudgetLabel', { currency })}
                    dot={{ r: 4 }}
                  />
                  <Line 
                    type="monotone"
                    dataKey={`${currency}_position`} 
                    stroke={index === 0 ? '#9c27b0' : '#e91e63'} 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name={t('optimization.netPositionLabel', { currency })}
                    dot={{ r: 3 }}
                  />
                </React.Fragment>
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Gap Visualization by Period */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('optimization.budgetGapByPeriod')}
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="period" 
                tickFormatter={formatPeriodLabel}
              />
              <YAxis />
              <Tooltip 
                formatter={(value: number, name: string) => {
                  const currency = name.split('_')[0];
                  return formatCurrency(value, currency);
                }}
                labelFormatter={formatPeriodLabel}
              />
              <Legend />
              {currencies.map((currency, index) => (
                <Bar 
                  key={currency}
                  dataKey={`${currency}_gap`} 
                  fill={index === 0 ? '#9c27b0' : '#e91e63'} 
                  name={t('optimization.gapLabel', { currency })}
                >
                  {chartData.map((entry: any, idx: number) => (
                    <Cell 
                      key={`cell-${idx}`} 
                      fill={entry[`${currency}_gap`] >= 0 ? '#4caf50' : '#f44336'} 
                    />
                  ))}
                </Bar>
              ))}
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Period-by-Period Breakdown */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('optimization.detailedPeriodBreakdown')}
          </Typography>
          {analysisData.periods.map((period) => (
            <Accordion key={period.period}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={2} width="100%">
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {formatPeriodLabel(period.period)}
                  </Typography>
                  {analysisData.critical_months.includes(period.period) && (
                    <Chip label={t('optimization.critical')} color="error" size="small" />
                  )}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  {Object.entries(period.currencies).map(([currency, data]) => (
                    <Grid item xs={12} md={6} key={currency}>
                      <Paper sx={{ p: 2, bgcolor: data.status === 'DEFICIT' ? '#ffebee' : '#e8f5e9' }}>
                        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                          {currency}
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2" color="textSecondary">
                            {t('optimization.periodOutflow')}: <strong>{formatCurrency(data.outflow, currency)}</strong>
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            {t('optimization.periodInflow')}: <strong>{formatCurrency(data.inflow, currency)}</strong>
                          </Typography>
                          <Divider sx={{ my: 1 }} />
                          <Typography variant="body2">
                            {t('optimization.cumulativeOutflow')}: <strong style={{ color: '#f44336' }}>{formatCurrency(data.cumulative_outflow, currency)}</strong>
                          </Typography>
                          <Typography variant="body2">
                            {t('optimization.cumulativeInflow')}: <strong style={{ color: '#4caf50' }}>{formatCurrency(data.cumulative_inflow, currency)}</strong>
                          </Typography>
                          <Typography variant="body2">
                            {t('optimization.cumulativeBudget')}: <strong style={{ color: '#2196f3' }}>{formatCurrency(data.cumulative_budget, currency)}</strong>
                          </Typography>
                          <Divider sx={{ my: 1 }} />
                          <Typography 
                            variant="body2" 
                            sx={{ color: data.gap >= 0 ? '#4caf50' : '#f44336', fontWeight: 'bold' }}
                          >
                            {t('optimization.netPosition', {
                              amount: formatCurrency(Math.abs(data.cumulative_position), currency),
                              type: data.gap >= 0 ? t('optimization.surplus') : t('optimization.deficit')
                            })}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {t('optimization.ofCumulativeOutflow', { percentage: data.gap_percentage.toFixed(1) })}
                          </Typography>
                        </Box>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            💡 {t('optimization.recommendationsActions')}
          </Typography>
          <List>
            {analysisData.recommendations.map((recommendation, index) => {
              // Handle both old string format (backward compatibility) and new structured format
              if (typeof recommendation === 'string') {
                const isWarning = recommendation.includes('🔴') || recommendation.includes('⚠️');
                const isSuccess = recommendation.includes('✅');
                const isInfo = recommendation.includes('📊') || recommendation.includes('📋');
                
                return (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {isSuccess ? (
                        <CheckCircleIcon sx={{ color: '#4caf50' }} />
                      ) : isWarning ? (
                        <WarningIcon sx={{ color: '#ff9800' }} />
                      ) : (
                        <InfoIcon sx={{ color: '#2196f3' }} />
                      )}
                    </ListItemIcon>
                    <ListItemText 
                      primary={recommendation}
                      primaryTypographyProps={{
                        sx: {
                          fontWeight: isWarning ? 'bold' : 'normal',
                          whiteSpace: 'pre-wrap'
                        }
                      }}
                    />
                  </ListItem>
                );
              }
              
              // Handle new structured format
              const rec = recommendation as RecommendationItem;
              const translatedText = rec.params 
                ? t(rec.key, rec.params)
                : t(rec.key);
              
              let icon = <InfoIcon sx={{ color: '#2196f3' }} />;
              let fontWeight: 'normal' | 'bold' = 'normal';
              
              if (rec.type === 'divider') {
                return <Divider key={index} sx={{ my: 1 }} />;
              }
              
              if (rec.type === 'success') {
                icon = <CheckCircleIcon sx={{ color: '#4caf50' }} />;
              } else if (rec.type === 'warning') {
                icon = <WarningIcon sx={{ color: '#ff9800' }} />;
                fontWeight = 'bold';
              } else if (rec.type === 'action') {
                icon = <InfoIcon sx={{ color: '#1976d2' }} />;
              } else if (rec.type === 'header') {
                fontWeight = 'bold';
              }
              
              return (
                <ListItem key={index}>
                  <ListItemIcon>{icon}</ListItemIcon>
                  <ListItemText 
                    primary={translatedText}
                    primaryTypographyProps={{
                      sx: {
                        fontWeight,
                        whiteSpace: 'pre-wrap'
                      }
                    }}
                  />
                </ListItem>
              );
            })}
          </List>
        </CardContent>
      </Card>
    </Box>
  );
};

