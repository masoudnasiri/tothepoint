import React, { useState, useEffect, useCallback } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  SxProps,
  Theme,
} from '@mui/material';
import { currencyAPI } from '../services/api.ts';
import { CurrencyWithRates } from '../types/index.ts';
import { formatApiError } from '../utils/errorUtils.ts';

interface CurrencySelectorProps {
  value: number | '' | undefined;
  onChange: (currencyId: number | '') => void;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  showRate?: boolean;
  fullWidth?: boolean;
  size?: 'small' | 'medium';
  error?: boolean;
  helperText?: string;
  sx?: SxProps<Theme>;
}

export const CurrencySelector: React.FC<CurrencySelectorProps> = ({
  value,
  onChange,
  label = 'Currency',
  required = false,
  disabled = false,
  showRate = false,
  fullWidth = true,
  size = 'medium',
  error = false,
  helperText,
  sx,
}) => {
  const [currencies, setCurrencies] = useState<CurrencyWithRates[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorState, setErrorState] = useState('');

  useEffect(() => {
    fetchCurrencies();
  }, []);

  const fetchCurrencies = async () => {
    try {
      setLoading(true);
      setErrorState('');
      const response = await currencyAPI.list();
      setCurrencies(response.data);
    } catch (err: any) {
      setErrorState(formatApiError(err, 'Failed to load currencies'));
    } finally {
      setLoading(false);
    }
  };

  const formatRate = (rate: number | null | undefined) => {
    if (!rate || rate === null || rate === undefined) {
      return 'N/A';
    }
    const numRate = typeof rate === 'string' ? parseFloat(rate) : rate;
    if (isNaN(numRate)) {
      return 'N/A';
    }
    if (numRate >= 1000) {
      return `${(numRate / 1000).toFixed(1)}K`;
    }
    return numRate.toFixed(2);
  };

  if (loading) {
    return (
      <FormControl fullWidth={fullWidth} size={size} disabled sx={sx}>
        <InputLabel>{label}</InputLabel>
        <Select value="">
          <MenuItem value="">
            <Box display="flex" alignItems="center" justifyContent="center" p={1}>
              <CircularProgress size={20} />
              <Typography variant="body2" sx={{ ml: 1 }}>Loading currencies...</Typography>
            </Box>
          </MenuItem>
        </Select>
      </FormControl>
    );
  }

  if (errorState) {
    return (
      <Alert severity="error" sx={{ mb: 1 }}>
        {errorState}
      </Alert>
    );
  }

  return (
    <FormControl 
      fullWidth={fullWidth} 
      size={size} 
      required={required}
      disabled={disabled}
      error={error}
      sx={sx}
    >
      <InputLabel>{label}</InputLabel>
      <Select
        value={value || ''}
        onChange={(e) => onChange(e.target.value as number | '')}
        label={label}
      >
        <MenuItem value="">
          <em>Select currency</em>
        </MenuItem>
        {currencies
          .filter(c => c.is_active)
          .sort((a, b) => {
            // Put base currency first, then sort by code
            if (a.is_base_currency && !b.is_base_currency) return -1;
            if (!a.is_base_currency && b.is_base_currency) return 1;
            return a.code.localeCompare(b.code);
          })
          .map((currency) => (
            <MenuItem key={currency.id} value={currency.id}>
              <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                <Box display="flex" alignItems="center">
                  <Typography variant="h6" sx={{ mr: 1 }}>
                    {currency.symbol}
                  </Typography>
                  <Box>
                    <Typography variant="body1">
                      {currency.code}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {currency.name}
                    </Typography>
                  </Box>
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                  {currency.is_base_currency && (
                    <Chip label="Base" color="primary" size="small" />
                  )}
                  {showRate && currency.rate_to_base && (
                    <Typography variant="caption" color="text.secondary">
                      {formatRate(currency.rate_to_base)} IRR
                    </Typography>
                  )}
                </Box>
              </Box>
            </MenuItem>
          ))}
      </Select>
      {helperText && (
        <Typography variant="caption" color={error ? 'error' : 'text.secondary'} sx={{ mt: 0.5, ml: 1.5 }}>
          {helperText}
        </Typography>
      )}
    </FormControl>
  );
};

// Currency Display Component
interface CurrencyDisplayProps {
  currencyId: number;
  amount: number;
  showCode?: boolean;
  showSymbol?: boolean;
  currencies?: CurrencyWithRates[];
}

export const CurrencyDisplay: React.FC<CurrencyDisplayProps> = ({
  currencyId,
  amount,
  showCode = false,
  showSymbol = true,
  currencies = [],
}) => {
  const currency = currencies.find(c => c.id === currencyId);
  
  if (!currency) {
    return <Typography variant="body2">Unknown Currency</Typography>;
  }

  const formattedAmount = amount.toFixed(currency.decimal_places);
  
  return (
    <Box display="flex" alignItems="center" gap={0.5}>
      {showSymbol && (
        <Typography variant="h6">{currency.symbol}</Typography>
      )}
      <Typography variant="body1">
        {formattedAmount}
      </Typography>
      {showCode && (
        <Typography variant="caption" color="text.secondary">
          {currency.code}
        </Typography>
      )}
    </Box>
  );
};

// Currency Converter Component
interface CurrencyConverterProps {
  amount: number;
  fromCurrencyId: number;
  toCurrencyId: number;
  currencies?: CurrencyWithRates[];
  showDetails?: boolean;
}

export const CurrencyConverter: React.FC<CurrencyConverterProps> = ({
  amount,
  fromCurrencyId,
  toCurrencyId,
  currencies = [],
  showDetails = false,
}) => {
  const [convertedAmount, setConvertedAmount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fromCurrency = currencies.find(c => c.id === fromCurrencyId);
  const toCurrency = currencies.find(c => c.id === toCurrencyId);

  const convertCurrency = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const response = await currencyAPI.convert(amount, fromCurrencyId, toCurrencyId);
      setConvertedAmount(response.data.converted_amount);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to convert currency'));
    } finally {
      setLoading(false);
    }
  }, [amount, fromCurrencyId, toCurrencyId]);

  useEffect(() => {
    if (amount && fromCurrencyId && toCurrencyId && fromCurrencyId !== toCurrencyId) {
      convertCurrency();
    } else if (fromCurrencyId === toCurrencyId) {
      setConvertedAmount(amount);
    }
  }, [amount, fromCurrencyId, toCurrencyId, convertCurrency]);

  if (loading) {
    return (
      <Box display="flex" alignItems="center" gap={1}>
        <CircularProgress size={16} />
        <Typography variant="body2" color="text.secondary">
          Converting...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Typography variant="caption" color="error">
        {error}
      </Typography>
    );
  }

  if (convertedAmount === null) {
    return null;
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={1}>
        {toCurrency && (
          <>
            <Typography variant="h6">{toCurrency.symbol}</Typography>
            <Typography variant="body1">
              {convertedAmount.toFixed(toCurrency.decimal_places)}
            </Typography>
          </>
        )}
      </Box>
      {showDetails && fromCurrency && toCurrency && (
        <Typography variant="caption" color="text.secondary">
          {fromCurrency.code} → {toCurrency.code}
        </Typography>
      )}
    </Box>
  );
};
