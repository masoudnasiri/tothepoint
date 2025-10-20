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
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  AccountBalance as AccountBalanceIcon,
  CurrencyExchange as CurrencyExchangeIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useAuth } from '../contexts/AuthContext.tsx';
import { financeAPI, excelAPI, currencyAPI } from '../services/api.ts';
import { BudgetData, BudgetDataCreate, Currency } from '../types/index.ts';
import { CurrencyManagementPage } from './CurrencyManagementPage.tsx';

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
      id={`finance-tabpanel-${index}`}
      aria-labelledby={`finance-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const FinancePage: React.FC = () => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [budgetData, setBudgetData] = useState<BudgetData[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedBudget, setSelectedBudget] = useState<BudgetData | null>(null);
  const [formData, setFormData] = useState<BudgetDataCreate>({
    budget_date: new Date().toISOString().split('T')[0],
    available_budget: 0,
    multi_currency_budget: {},
  });

  useEffect(() => {
    fetchBudgetData();
    fetchCurrencies();
  }, []);

  const fetchBudgetData = async () => {
    try {
      const response = await financeAPI.listBudget();
      setBudgetData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load budget data');
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrencies = async () => {
    try {
      const response = await currencyAPI.list();
      setCurrencies(response.data.filter((c: Currency) => c.is_active));
    } catch (err: any) {
      console.error('Failed to load currencies:', err);
    }
  };

  const handleCreateBudget = async () => {
    try {
      await financeAPI.createBudget(formData);
      setCreateDialogOpen(false);
      resetForm();
      fetchBudgetData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create budget data');
    }
  };

  const handleEditBudget = async () => {
    if (!selectedBudget) return;
    
    try {
      await financeAPI.updateBudget(selectedBudget.budget_date, formData);
      setEditDialogOpen(false);
      setSelectedBudget(null);
      resetForm();
      fetchBudgetData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update budget data');
    }
  };

  const handleDeleteBudget = async (budgetDate: string) => {
    if (!window.confirm('Are you sure you want to delete this budget data?')) return;
    
    try {
      await financeAPI.deleteBudget(budgetDate);
      fetchBudgetData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete budget data');
    }
  };

  const resetForm = () => {
    setFormData({
      budget_date: new Date().toISOString().split('T')[0],
      available_budget: 0,
      multi_currency_budget: {},
    });
  };

  const handleCurrencyBudgetChange = (currencyCode: string, value: number) => {
    setFormData({
      ...formData,
      multi_currency_budget: {
        ...(formData.multi_currency_budget || {}),
        [currencyCode]: value,
      },
    });
  };

  const removeCurrencyBudget = (currencyCode: string) => {
    const newBudget = { ...(formData.multi_currency_budget || {}) };
    delete newBudget[currencyCode];
    setFormData({
      ...formData,
      multi_currency_budget: newBudget,
    });
  };

  const handleExportBudget = async () => {
    try {
      const response = await excelAPI.exportBudget();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'budget_data.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to export budget data');
    }
  };

  const handleImportBudget = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await excelAPI.importBudget(file);
      fetchBudgetData();
      alert('Budget data imported successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import budget data');
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await excelAPI.downloadBudgetTemplate();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'budget_template.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download template');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatIRR = (value: number) => {
    // Format IRR with proper symbol and no decimals
    return `﷼${value.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })}`;
  };

  const calculateTotalBudget = () => {
    return budgetData.reduce((sum, budget) => sum + Number(budget.available_budget || 0), 0);
  };

  const calculateCurrencyTotals = () => {
    const totals: { [currencyCode: string]: number } = {};
    
    budgetData.forEach((budget) => {
      if (budget.multi_currency_budget) {
        Object.entries(budget.multi_currency_budget).forEach(([code, amount]) => {
          totals[code] = (totals[code] || 0) + Number(amount);
        });
      }
    });
    
    return totals;
  };

  const formatCurrencyWithCode = (value: number, currencyCode: string) => {
    const currency = currencies.find((c) => c.code === currencyCode);
    if (!currency) return `${value.toLocaleString()} ${currencyCode}`;
    
    return `${currency.symbol}${value.toLocaleString(undefined, {
      minimumFractionDigits: currency.decimal_places,
      maximumFractionDigits: currency.decimal_places,
    })}`;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Finance Management</Typography>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          aria-label="finance management tabs"
        >
          <Tab 
            icon={<AccountBalanceIcon />} 
            label="Budget Management" 
            iconPosition="start"
          />
          <Tab 
            icon={<CurrencyExchangeIcon />} 
            label="Currency Management" 
            iconPosition="start"
          />
        </Tabs>

        {/* Budget Management Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">Budget Management</Typography>
        {(user?.role === 'finance' || user?.role === 'admin') && (
          <Box>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadTemplate}
              sx={{ mr: 1 }}
            >
              Download Template
            </Button>
            <Button
              variant="outlined"
              component="label"
              startIcon={<UploadIcon />}
              sx={{ mr: 1 }}
            >
              Import Budget
              <input
                type="file"
                hidden
                accept=".xlsx,.xls"
                onChange={handleImportBudget}
              />
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExportBudget}
              sx={{ mr: 1 }}
            >
              Export Budget
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setFormData({
                  budget_date: new Date().toISOString().split('T')[0],
                  available_budget: 0,
                  multi_currency_budget: {},
                });
                setCreateDialogOpen(true);
              }}
            >
              Add Budget
            </Button>
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Budget Summary
        </Typography>
        <Box display="flex" gap={2} flexWrap="wrap">
          <Chip
            label={`Total Periods: ${budgetData.length}`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`Base Budget (IRR): ${formatIRR(calculateTotalBudget())}`}
            color="success"
            variant="outlined"
          />
          {Object.entries(calculateCurrencyTotals()).map(([code, total]) => (
            <Chip
              key={code}
              label={`${code}: ${formatCurrencyWithCode(total, code)}`}
              color="info"
              variant="outlined"
            />
          ))}
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Budget Date</TableCell>
              <TableCell align="right">Base Budget (IRR)</TableCell>
              <TableCell align="left">Multi-Currency Budgets</TableCell>
              <TableCell align="center">Created</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {budgetData.map((budget) => (
              <TableRow key={budget.budget_date}>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {new Date(budget.budget_date).toLocaleDateString()}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body1" fontWeight="medium" color="primary">
                    {formatIRR(Number(budget.available_budget || 0))}
                  </Typography>
                </TableCell>
                <TableCell align="left">
                  {budget.multi_currency_budget && Object.keys(budget.multi_currency_budget).length > 0 ? (
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {Object.entries(budget.multi_currency_budget).map(([code, amount]) => (
                        <Chip
                          key={code}
                          label={`${code}: ${formatCurrencyWithCode(Number(amount), code)}`}
                          size="small"
                          color="info"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      None
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">
                  <Typography variant="body2" color="text.secondary">
                    {new Date(budget.created_at).toLocaleDateString()}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  {(user?.role === 'finance' || user?.role === 'admin') && (
                    <>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedBudget(budget);
                          setFormData({
                            budget_date: budget.budget_date,
                            available_budget: Number(budget.available_budget || 0),
                            multi_currency_budget: budget.multi_currency_budget || {},
                          });
                          setEditDialogOpen(true);
                        }}
                        title="Edit Budget"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteBudget(budget.budget_date)}
                        title="Delete Budget"
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Budget Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Budget Entry</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Budget Date"
              value={new Date(formData.budget_date)}
              onChange={(newValue) => {
                if (newValue) {
                  setFormData({ ...formData, budget_date: newValue.toISOString().split('T')[0] });
                }
              }}
              slotProps={{ textField: { fullWidth: true, margin: 'dense', sx: { mb: 2, mt: 1 } } }}
            />
          </LocalizationProvider>
          
          <TextField
            margin="dense"
            label="Base Budget (IRR)"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.available_budget}
            onChange={(e) => setFormData({ ...formData, available_budget: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: '0.01' }}
            helperText="Base currency budget (Iranian Rial)"
          />

          <Divider sx={{ my: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Multi-Currency Budgets (Optional)
            </Typography>
          </Divider>

          {/* Display existing currency budgets */}
          {formData.multi_currency_budget && Object.keys(formData.multi_currency_budget).length > 0 && (
            <Box sx={{ mb: 2 }}>
              {Object.entries(formData.multi_currency_budget).map(([code, amount]) => {
                const currency = currencies.find((c) => c.code === code);
                return (
                  <Box key={code} display="flex" gap={1} alignItems="center" mb={1}>
                    <TextField
                      label={`${code} Budget`}
                      type="number"
                      fullWidth
                      variant="outlined"
                      size="small"
                      value={amount}
                      onChange={(e) => handleCurrencyBudgetChange(code, parseFloat(e.target.value) || 0)}
                      inputProps={{ step: '0.01' }}
                      helperText={currency ? currency.name : ''}
                    />
                    <Button
                      variant="outlined"
                      color="error"
                      size="small"
                      onClick={() => removeCurrencyBudget(code)}
                    >
                      Remove
                    </Button>
                  </Box>
                );
              })}
            </Box>
          )}

          {/* Add new currency budget */}
          <FormControl fullWidth margin="dense">
            <InputLabel>Add Currency Budget</InputLabel>
            <Select
              label="Add Currency Budget"
              value=""
              onChange={(e) => {
                const code = e.target.value;
                if (code && !formData.multi_currency_budget?.[code]) {
                  handleCurrencyBudgetChange(code, 0);
                }
              }}
            >
              {currencies
                .filter((c) => !formData.multi_currency_budget?.[c.code] && c.code !== 'IRR')
                .map((currency) => (
                  <MenuItem key={currency.code} value={currency.code}>
                    {currency.code} - {currency.name} ({currency.symbol})
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateBudget} variant="contained">
            Add Budget
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Budget Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Budget Entry</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Budget Date"
              value={new Date(formData.budget_date)}
              onChange={(newValue) => {
                if (newValue) {
                  setFormData({ ...formData, budget_date: newValue.toISOString().split('T')[0] });
                }
              }}
              disabled
              slotProps={{ textField: { fullWidth: true, margin: 'dense', sx: { mb: 2, mt: 1 } } }}
            />
          </LocalizationProvider>
          
          <TextField
            margin="dense"
            label="Base Budget (IRR)"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.available_budget}
            onChange={(e) => setFormData({ ...formData, available_budget: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: '0.01' }}
            helperText="Base currency budget (Iranian Rial)"
          />

          <Divider sx={{ my: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Multi-Currency Budgets (Optional)
            </Typography>
          </Divider>

          {/* Display existing currency budgets */}
          {formData.multi_currency_budget && Object.keys(formData.multi_currency_budget).length > 0 && (
            <Box sx={{ mb: 2 }}>
              {Object.entries(formData.multi_currency_budget).map(([code, amount]) => {
                const currency = currencies.find((c) => c.code === code);
                return (
                  <Box key={code} display="flex" gap={1} alignItems="center" mb={1}>
                    <TextField
                      label={`${code} Budget`}
                      type="number"
                      fullWidth
                      variant="outlined"
                      size="small"
                      value={amount}
                      onChange={(e) => handleCurrencyBudgetChange(code, parseFloat(e.target.value) || 0)}
                      inputProps={{ step: '0.01' }}
                      helperText={currency ? currency.name : ''}
                    />
                    <Button
                      variant="outlined"
                      color="error"
                      size="small"
                      onClick={() => removeCurrencyBudget(code)}
                    >
                      Remove
                    </Button>
                  </Box>
                );
              })}
            </Box>
          )}

          {/* Add new currency budget */}
          <FormControl fullWidth margin="dense">
            <InputLabel>Add Currency Budget</InputLabel>
            <Select
              label="Add Currency Budget"
              value=""
              onChange={(e) => {
                const code = e.target.value;
                if (code && !formData.multi_currency_budget?.[code]) {
                  handleCurrencyBudgetChange(code, 0);
                }
              }}
            >
              {currencies
                .filter((c) => !formData.multi_currency_budget?.[c.code] && c.code !== 'IRR')
                .map((currency) => (
                  <MenuItem key={currency.code} value={currency.code}>
                    {currency.code} - {currency.name} ({currency.symbol})
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleEditBudget} variant="contained">
            Update Budget
          </Button>
        </DialogActions>
      </Dialog>
        </TabPanel>

        {/* Currency Management Tab */}
        <TabPanel value={tabValue} index={1}>
          <CurrencyManagementPage />
        </TabPanel>
      </Paper>
    </Box>
  );
};
