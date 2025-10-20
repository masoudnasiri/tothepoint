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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  CurrencyExchange as CurrencyExchangeIcon,
  AttachMoney as AttachMoneyIcon,
} from '@mui/icons-material';
import { currencyAPI } from '../services/api.ts';
import { CurrencyWithRates, CurrencyCreate, ExchangeRateCreate, CurrencyConversion } from '../types/index.ts';
import { formatApiError } from '../utils/errorUtils.ts';

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
      id={`currency-tabpanel-${index}`}
      aria-labelledby={`currency-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const CurrencyManagementPage: React.FC = () => {
  const [currencies, setCurrencies] = useState<CurrencyWithRates[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tabValue, setTabValue] = useState(0);
  
  // Currency dialog states
  const [currencyDialogOpen, setCurrencyDialogOpen] = useState(false);
  const [editingCurrency, setEditingCurrency] = useState<CurrencyWithRates | null>(null);
  const [currencyForm, setCurrencyForm] = useState<CurrencyCreate>({
    code: '',
    name: '',
    symbol: '',
    is_base_currency: false,
    is_active: true,
    decimal_places: 2,
  });
  
  // Exchange rate states (NEW structure)
  const [exchangeRates, setExchangeRates] = useState<any[]>([]);
  const [rateDialogOpen, setRateDialogOpen] = useState(false);
  const [editingRate, setEditingRate] = useState<any | null>(null);
  const [newRateForm, setNewRateForm] = useState({
    date: new Date().toISOString().split('T')[0],
    from_currency: '',
    to_currency: 'IRR',
    rate: 0,
  });
  
  // OLD Exchange rate dialog states (kept for backward compatibility)
  const [selectedCurrency, setSelectedCurrency] = useState<CurrencyWithRates | null>(null);
  const [rateForm, setRateForm] = useState<ExchangeRateCreate>({
    currency_id: 0,
    rate_date: new Date().toISOString().split('T')[0],
    rate_to_base: 0,
    is_active: true,
  });
  
  // Conversion calculator states
  const [conversionAmount, setConversionAmount] = useState<number>(0);
  const [fromCurrency, setFromCurrency] = useState<number>(0);
  const [toCurrency, setToCurrency] = useState<number>(0);
  const [conversionResult, setConversionResult] = useState<CurrencyConversion | null>(null);
  const [converting, setConverting] = useState(false);

  useEffect(() => {
    fetchCurrencies();
    fetchExchangeRates();
  }, []);

  const fetchCurrencies = async () => {
    try {
      setLoading(true);
      const response = await currencyAPI.list(true);
      setCurrencies(response.data);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to load currencies'));
    } finally {
      setLoading(false);
    }
  };

  const handleCurrencySubmit = async () => {
    try {
      setError('');
      if (editingCurrency) {
        await currencyAPI.update(editingCurrency.id, currencyForm);
        setSuccess('Currency updated successfully');
      } else {
        await currencyAPI.create(currencyForm);
        setSuccess('Currency created successfully');
      }
      setCurrencyDialogOpen(false);
      setEditingCurrency(null);
      setCurrencyForm({
        code: '',
        name: '',
        symbol: '',
        is_base_currency: false,
        is_active: true,
        decimal_places: 2,
      });
      fetchCurrencies();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to save currency'));
    }
  };

  const handleCurrencyEdit = (currency: CurrencyWithRates) => {
    setEditingCurrency(currency);
    setCurrencyForm({
      code: currency.code,
      name: currency.name,
      symbol: currency.symbol,
      is_base_currency: currency.is_base_currency,
      is_active: currency.is_active,
      decimal_places: currency.decimal_places,
    });
    setCurrencyDialogOpen(true);
  };

  const handleCurrencyDelete = async (currencyId: number) => {
    if (window.confirm('Are you sure you want to delete this currency?')) {
      try {
        await currencyAPI.delete(currencyId);
        setSuccess('Currency deleted successfully');
        fetchCurrencies();
      } catch (err: any) {
        setError(formatApiError(err, 'Failed to delete currency'));
      }
    }
  };

  // NEW: Fetch exchange rates
  const fetchExchangeRates = async () => {
    try {
      const response = await currencyAPI.listExchangeRates();
      setExchangeRates(response.data);
    } catch (err: any) {
      console.error('Failed to load exchange rates:', err);
    }
  };

  // NEW: Handle adding/editing exchange rate
  const handleAddRate = async () => {
    try {
      setError('');
      if (editingRate) {
        // Update existing rate
        await currencyAPI.updateExchangeRateValue(editingRate.id, newRateForm.rate);
        setSuccess('Exchange rate updated successfully');
      } else {
        // Add new rate
        await currencyAPI.addExchangeRate(
          newRateForm.date,
          newRateForm.from_currency,
          newRateForm.to_currency,
          newRateForm.rate
        );
        setSuccess('Exchange rate added successfully');
      }
      setRateDialogOpen(false);
      setEditingRate(null);
      setNewRateForm({
        date: new Date().toISOString().split('T')[0],
        from_currency: '',
        to_currency: 'IRR',
        rate: 0,
      });
      fetchExchangeRates();
      fetchCurrencies();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to save exchange rate'));
    }
  };

  // NEW: Handle editing exchange rate
  const handleEditRate = (rate: any) => {
    setEditingRate(rate);
    setNewRateForm({
      date: rate.date,
      from_currency: rate.from_currency,
      to_currency: rate.to_currency,
      rate: rate.rate,
    });
    setRateDialogOpen(true);
  };

  // NEW: Handle deleting exchange rate
  const handleDeleteRate = async (rateId: number) => {
    if (window.confirm('Are you sure you want to delete this exchange rate?')) {
      try {
        await currencyAPI.deleteExchangeRate(rateId);
        setSuccess('Exchange rate deleted successfully');
        fetchExchangeRates();
        fetchCurrencies();
      } catch (err: any) {
        setError(formatApiError(err, 'Failed to delete exchange rate'));
      }
    }
  };

  const handleRateSubmit = async () => {
    try {
      setError('');
      await currencyAPI.createExchangeRate(selectedCurrency!.id, rateForm);
      setSuccess('Exchange rate added successfully');
      setRateDialogOpen(false);
      setSelectedCurrency(null);
      setRateForm({
        currency_id: 0,
        rate_date: new Date().toISOString().split('T')[0],
        rate_to_base: 0,
        is_active: true,
      });
      fetchCurrencies();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to add exchange rate'));
    }
  };

  const handleConversion = async () => {
    if (!conversionAmount || !fromCurrency || !toCurrency) return;
    
    try {
      setConverting(true);
      const response = await currencyAPI.convert(conversionAmount, fromCurrency, toCurrency);
      setConversionResult(response.data);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to convert currency'));
    } finally {
      setConverting(false);
    }
  };

  const formatCurrencyAmount = (amount: number, currency: CurrencyWithRates) => {
    const formatted = amount.toFixed(currency.decimal_places);
    return `${currency.symbol}${formatted}`;
  };

  const formatRate = (rate: number | null | undefined) => {
    // Handle null/undefined rates safely
    if (!rate || rate === null || rate === undefined || isNaN(Number(rate))) {
      return 'N/A';
    }
    const numRate = Number(rate);
    if (numRate >= 1000) {
      return `${(numRate / 1000).toFixed(1)}K`;
    }
    return numRate.toFixed(2);
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
        <Typography variant="h4">
          <CurrencyExchangeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Currency Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCurrencyDialogOpen(true)}
        >
          Add Currency
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          aria-label="currency management tabs"
        >
          <Tab label="Currencies" />
          <Tab label="Exchange Rates" />
          <Tab label="Currency Converter" />
        </Tabs>

        {/* Currencies Tab */}
        <TabPanel value={tabValue} index={0}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Code</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Symbol</TableCell>
                  <TableCell align="center">Base Currency</TableCell>
                  <TableCell align="right">Latest Rate</TableCell>
                  <TableCell align="center">Status</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {currencies.map((currency) => (
                  <TableRow key={currency.id}>
                    <TableCell>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {currency.code}
                      </Typography>
                    </TableCell>
                    <TableCell>{currency.name}</TableCell>
                    <TableCell>
                      <Typography variant="h6">{currency.symbol}</Typography>
                    </TableCell>
                    <TableCell align="center">
                      {currency.is_base_currency && (
                        <Chip label="Base" color="primary" size="small" />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {currency.rate_to_base ? (
                        <Typography variant="body2">
                          {formatRate(currency.rate_to_base)}
                          <Typography component="span" variant="caption" color="text.secondary">
                            {' '}IRR
                          </Typography>
                        </Typography>
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          No rate
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={currency.is_active ? 'Active' : 'Inactive'}
                        color={currency.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="Edit Currency">
                        <IconButton
                          size="small"
                          onClick={() => handleCurrencyEdit(currency)}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Add Exchange Rate">
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedCurrency(currency);
                            setRateForm({
                              ...rateForm,
                              currency_id: currency.id,
                            });
                            setRateDialogOpen(true);
                          }}
                        >
                          <TrendingUpIcon />
                        </IconButton>
                      </Tooltip>
                      {!currency.is_base_currency && (
                        <Tooltip title="Delete Currency">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleCurrencyDelete(currency.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* Exchange Rates Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">Exchange Rates Management</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setEditingRate(null);
                setNewRateForm({
                  date: new Date().toISOString().split('T')[0],
                  from_currency: '',
                  to_currency: 'IRR',
                  rate: 0,
                });
                setRateDialogOpen(true);
              }}
            >
              Add Exchange Rate
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>From Currency</TableCell>
                  <TableCell>To Currency</TableCell>
                  <TableCell align="right">Exchange Rate</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {exchangeRates.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                        No exchange rates available. Click "Add Exchange Rate" to create one.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  exchangeRates.map((rate) => (
                    <TableRow key={rate.id}>
                      <TableCell>{new Date(rate.date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Chip label={rate.from_currency} size="small" color="primary" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Chip label={rate.to_currency} size="small" color="secondary" variant="outlined" />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body1" fontWeight="medium">
                          {rate.rate.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={rate.is_active ? 'Active' : 'Inactive'}
                          size="small"
                          color={rate.is_active ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleEditRate(rate)}
                          title="Edit rate"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteRate(rate.id)}
                          title="Delete rate"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Note:</strong> Exchange rates can be edited for each specific date. 
              If you add a rate for a date that already exists, it will update the existing rate.
              The system uses the closest available rate on or before the transaction date for conversions.
            </Typography>
          </Alert>
        </TabPanel>

        {/* Currency Converter Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <AttachMoneyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Currency Converter
                  </Typography>
                  
                  <TextField
                    label="Amount"
                    type="number"
                    fullWidth
                    value={conversionAmount}
                    onChange={(e) => setConversionAmount(Number(e.target.value))}
                    sx={{ mb: 2 }}
                  />
                  
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>From Currency</InputLabel>
                    <Select
                      value={fromCurrency}
                      onChange={(e) => setFromCurrency(Number(e.target.value))}
                    >
                      {currencies.filter(c => c.is_active).map((currency) => (
                        <MenuItem key={currency.id} value={currency.id}>
                          {currency.symbol} {currency.code} - {currency.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>To Currency</InputLabel>
                    <Select
                      value={toCurrency}
                      onChange={(e) => setToCurrency(Number(e.target.value))}
                    >
                      {currencies.filter(c => c.is_active).map((currency) => (
                        <MenuItem key={currency.id} value={currency.id}>
                          {currency.symbol} {currency.code} - {currency.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={handleConversion}
                    disabled={converting || !conversionAmount || !fromCurrency || !toCurrency}
                    startIcon={converting ? <CircularProgress size={20} /> : <CurrencyExchangeIcon />}
                  >
                    Convert
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              {conversionResult && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Conversion Result
                    </Typography>
                    <Box textAlign="center">
                      <Typography variant="h4" color="primary" gutterBottom>
                        {formatCurrencyAmount(
                          conversionResult.converted_amount,
                          currencies.find(c => c.id === toCurrency)!
                        )}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Exchange rate: {conversionResult.from_rate.toFixed(2)} → {conversionResult.to_rate.toFixed(2)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Date: {new Date(conversionResult.conversion_date).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Currency Dialog */}
      <Dialog open={currencyDialogOpen} onClose={() => setCurrencyDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingCurrency ? 'Edit Currency' : 'Add New Currency'}
        </DialogTitle>
        <DialogContent>
          <TextField
            label="Currency Code"
            fullWidth
            value={currencyForm.code}
            onChange={(e) => setCurrencyForm({ ...currencyForm, code: e.target.value.toUpperCase() })}
            sx={{ mb: 2 }}
            placeholder="e.g., USD, EUR"
          />
          <TextField
            label="Currency Name"
            fullWidth
            value={currencyForm.name}
            onChange={(e) => setCurrencyForm({ ...currencyForm, name: e.target.value })}
            sx={{ mb: 2 }}
            placeholder="e.g., US Dollar"
          />
          <TextField
            label="Currency Symbol"
            fullWidth
            value={currencyForm.symbol}
            onChange={(e) => setCurrencyForm({ ...currencyForm, symbol: e.target.value })}
            sx={{ mb: 2 }}
            placeholder="e.g., $, €, ﷼"
          />
          <TextField
            label="Decimal Places"
            type="number"
            fullWidth
            value={currencyForm.decimal_places}
            onChange={(e) => setCurrencyForm({ ...currencyForm, decimal_places: Number(e.target.value) })}
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={currencyForm.is_base_currency}
                onChange={(e) => setCurrencyForm({ ...currencyForm, is_base_currency: e.target.checked })}
              />
            }
            label="Base Currency"
          />
          <br />
          <FormControlLabel
            control={
              <Switch
                checked={currencyForm.is_active}
                onChange={(e) => setCurrencyForm({ ...currencyForm, is_active: e.target.checked })}
              />
            }
            label="Active"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCurrencyDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCurrencySubmit} variant="contained">
            {editingCurrency ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* NEW: Exchange Rate Dialog */}
      <Dialog open={rateDialogOpen} onClose={() => setRateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingRate ? 'Edit Exchange Rate' : 'Add Exchange Rate'}
        </DialogTitle>
        <DialogContent>
          <TextField
            label="Date"
            type="date"
            fullWidth
            value={newRateForm.date}
            onChange={(e) => setNewRateForm({ ...newRateForm, date: e.target.value })}
            sx={{ mb: 2, mt: 1 }}
            InputLabelProps={{ shrink: true }}
            disabled={!!editingRate}
            helperText={editingRate ? 'Date cannot be changed when editing' : 'Select the date for this exchange rate'}
          />
          
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>From Currency</InputLabel>
            <Select
              value={newRateForm.from_currency}
              onChange={(e) => setNewRateForm({ ...newRateForm, from_currency: e.target.value })}
              disabled={!!editingRate}
            >
              {currencies.filter(c => c.is_active && !c.is_base_currency).map((currency) => (
                <MenuItem key={currency.code} value={currency.code}>
                  {currency.symbol} {currency.code} - {currency.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>To Currency</InputLabel>
            <Select
              value={newRateForm.to_currency}
              onChange={(e) => setNewRateForm({ ...newRateForm, to_currency: e.target.value })}
              disabled={!!editingRate}
            >
              <MenuItem value="IRR">﷼ IRR - Iranian Rial (Base Currency)</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
            label="Exchange Rate"
            type="number"
            fullWidth
            value={newRateForm.rate}
            onChange={(e) => setNewRateForm({ ...newRateForm, rate: Number(e.target.value) })}
            sx={{ mb: 2 }}
            placeholder="e.g., 47600"
            helperText={`How many ${newRateForm.to_currency} equals 1 ${newRateForm.from_currency}`}
            InputProps={{
              inputProps: { step: 0.01, min: 0 }
            }}
          />
          
          {newRateForm.from_currency && newRateForm.rate > 0 && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Example:</strong> 1 {newRateForm.from_currency} = {newRateForm.rate.toLocaleString()} {newRateForm.to_currency}
              </Typography>
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setRateDialogOpen(false);
            setEditingRate(null);
          }}>
            Cancel
          </Button>
          <Button onClick={handleAddRate} variant="contained">
            {editingRate ? 'Update Rate' : 'Add Rate'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
