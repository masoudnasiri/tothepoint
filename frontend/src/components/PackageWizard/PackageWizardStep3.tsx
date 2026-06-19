import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Paper,
  Grid,
  Checkbox,
  FormControlLabel,
  Button,
  IconButton,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizedDateProvider } from '../LocalizedDateProvider.tsx';
import { CurrencySelector } from '../CurrencySelector.tsx';
import { deliveryOptionsAPI } from '../../services/api.ts';

interface PackageWizardStep3Props {
  data: {
    base_cost: number;
    currency_id: number | null;
    shipping_cost: number;
    delivery_option_id: number | null;
    lomc_lead_time: number;
    purchase_date: string;
    expected_delivery_date: string;
    payment_terms: {
      type: 'cash' | 'installments';
      discount_percent: number;
      installments?: Array<{ days_after_purchase: number; percentage: number }>;
    };
    discount_bundle_threshold?: number;
    discount_bundle_percent?: number;
    is_finalized: boolean;
    main_item_quantity: number; // Add this to know if it's sub-item only
  };
  projectItemId: number;
  onChange: (updates: Partial<PackageWizardStep3Props['data']>) => void;
}

interface DeliveryOption {
  id: number;
  delivery_date: string;
  delivery_slot: number | null;
  invoice_amount_per_unit: number;
}

export const PackageWizardStep3: React.FC<PackageWizardStep3Props> = ({
  data,
  projectItemId,
  onChange,
}) => {
  const { t } = useTranslation();
  const [deliveryOptions, setDeliveryOptions] = useState<DeliveryOption[]>([]);
  const [loadingDeliveryOptions, setLoadingDeliveryOptions] = useState(false);

  useEffect(() => {
    const fetchDeliveryOptions = async () => {
      setLoadingDeliveryOptions(true);
      try {
        const response = await deliveryOptionsAPI.listByItem(projectItemId);
        setDeliveryOptions(response.data || []);
      } catch (err) {
        console.error('Failed to load delivery options', err);
        setDeliveryOptions([]);
      } finally {
        setLoadingDeliveryOptions(false);
      }
    };
    if (projectItemId) {
      fetchDeliveryOptions();
    }
  }, [projectItemId]);

  // Check if this is a sub-item only package (main_item_quantity = 0)
  const isSubItemOnly = data.main_item_quantity === 0;
  
  // Calculate min and max dates for delivery date selection
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const latestDeliveryDate = deliveryOptions.length > 0
    ? new Date(Math.max(...deliveryOptions.map(opt => new Date(opt.delivery_date).getTime())))
    : null;
  
  const minDate = today;
  const maxDate = latestDeliveryDate;

  const calculateLeadTime = (deliveryDate: string): number => {
    if (!deliveryDate) return 0;
    const today = new Date();
    const delivery = new Date(deliveryDate);
    const diffTime = delivery.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(0, diffDays);
  };

  // Helper function to add commas while typing (supports large numbers like IRR)
  const addCommasWhileTyping = (value: string): string => {
    // Remove all non-digit characters except decimal point
    const cleanValue = value.replace(/[^\d.]/g, '');
    
    // Split by decimal point
    const parts = cleanValue.split('.');
    const integerPart = parts[0];
    const decimalPart = parts[1];
    
    // Add commas to integer part
    const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    
    // Combine with decimal part if exists
    return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger;
  };

  const parseFormattedNumber = (formattedValue: string): string => {
    return formattedValue.replace(/,/g, '');
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Typography variant="h6" gutterBottom>
        {t('procurement.pricingDelivery') || 'Pricing & Delivery'}
      </Typography>

      {/* Cost Fields */}
      <Paper elevation={1} sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          {t('procurement.costInformation') || 'Cost Information'}
        </Typography>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label={t('procurement.baseCost') || 'Base Cost'}
              type="text"
              value={data.base_cost ? addCommasWhileTyping(data.base_cost.toString()) : ''}
              onChange={(e) => {
                const rawValue = parseFormattedNumber(e.target.value);
                const numericValue = parseFloat(rawValue) || 0;
                onChange({ base_cost: numericValue });
              }}
              inputProps={{
                step: 0.01,
                min: 0,
                placeholder: '0.00'
              }}
              helperText={t('procurement.baseCostHelper') || 'Enter amount (commas added automatically)'}
              required
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label={t('procurement.shippingCost') || 'Shipping Cost'}
              type="text"
              value={data.shipping_cost ? addCommasWhileTyping(data.shipping_cost.toString()) : ''}
              onChange={(e) => {
                const rawValue = parseFormattedNumber(e.target.value);
                const numericValue = parseFloat(rawValue) || 0;
                onChange({ shipping_cost: numericValue });
              }}
              inputProps={{
                step: 0.01,
                min: 0,
                placeholder: '0.00'
              }}
              helperText={t('procurement.shippingCostHelper') || 'Optional shipping cost (commas added automatically)'}
            />
          </Grid>
          <Grid item xs={12}>
            <CurrencySelector
              value={data.currency_id}
              onChange={(currencyId) => onChange({ currency_id: currencyId as number })}
              label={t('procurement.currency') || 'Currency'}
              required
              showRate
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Delivery Options */}
      <Paper elevation={1} sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          {t('procurement.deliveryInformation') || 'Delivery Information'}
        </Typography>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>{t('procurement.deliveryOption') || 'Delivery Option'}</InputLabel>
              <Select
                value={data.delivery_option_id || ''}
                onChange={(e) => {
                  const optionId = e.target.value as number;
                  const selectedOption = deliveryOptions.find((opt) => opt.id === optionId);
                  const leadTime = selectedOption ? calculateLeadTime(selectedOption.delivery_date) : 0;
                  // Only auto-fill delivery date if not a sub-item-only package
                  if (!isSubItemOnly && selectedOption) {
                    onChange({
                      delivery_option_id: optionId,
                      expected_delivery_date: selectedOption.delivery_date,
                      lomc_lead_time: leadTime,
                    });
                  } else {
                    // For sub-item-only packages, just set the option ID, user will select date manually
                    onChange({
                      delivery_option_id: optionId,
                      lomc_lead_time: leadTime,
                    });
                  }
                }}
                disabled={deliveryOptions.length === 0 || loadingDeliveryOptions}
              >
                {deliveryOptions.length === 0 ? (
                  <MenuItem disabled>
                    {t('procurement.noDeliveryOptionsAvailable') || 'No delivery options available'}
                  </MenuItem>
                ) : (
                  deliveryOptions.map((option) => (
                    <MenuItem key={option.id} value={option.id}>
                      {new Date(option.delivery_date).toLocaleDateString()} - Slot {option.delivery_slot || 'N/A'}
                    </MenuItem>
                  ))
                )}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <LocalizedDateProvider>
              <DatePicker
                label={t('procurement.purchaseDate') || 'Purchase Date'}
                value={data.purchase_date ? new Date(data.purchase_date) : null}
                onChange={(newValue) => {
                  if (newValue) {
                    onChange({ purchase_date: newValue.toISOString().split('T')[0] });
                  }
                }}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    helperText: t('procurement.purchaseDateHelper') || 'When to place the order',
                  },
                }}
              />
            </LocalizedDateProvider>
          </Grid>
          <Grid item xs={12} sm={6}>
            <LocalizedDateProvider>
              <DatePicker
                label={t('procurement.expectedDeliveryDate') || 'Expected Delivery Date'}
                value={data.expected_delivery_date ? new Date(data.expected_delivery_date) : null}
                disabled={!isSubItemOnly}
                minDate={minDate}
                maxDate={maxDate || undefined}
                onChange={(newValue) => {
                  if (newValue) {
                    const selectedDate = newValue.toISOString().split('T')[0];
                    const leadTime = calculateLeadTime(selectedDate);
                    onChange({
                      expected_delivery_date: selectedDate,
                      lomc_lead_time: leadTime,
                    });
                  }
                }}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    helperText: isSubItemOnly
                      ? (t('procurement.selectDeliveryDateRange') || `Select date between ${minDate.toLocaleDateString()} and ${maxDate ? maxDate.toLocaleDateString() : 'latest slot'}`)
                      : (t('procurement.autoFilledFromDeliveryOption') || 'Auto-filled from delivery option'),
                  },
                }}
              />
            </LocalizedDateProvider>
          </Grid>
        </Grid>
      </Paper>

      {/* Discounts */}
      <Paper elevation={1} sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          {t('procurement.discounts') || 'Discounts'}
        </Typography>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label={t('procurement.bundleDiscountThreshold') || 'Bundle Discount Threshold'}
              type="number"
              value={data.discount_bundle_threshold || ''}
              onChange={(e) =>
                onChange({
                  discount_bundle_threshold: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
              helperText={t('procurement.bundleDiscountThresholdHelper') || 'Minimum quantity for bundle discount'}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label={t('procurement.bundleDiscountPercentage') || 'Bundle Discount %'}
              type="number"
              value={data.discount_bundle_percent || ''}
              onChange={(e) =>
                onChange({
                  discount_bundle_percent: e.target.value ? parseFloat(e.target.value) : undefined,
                })
              }
              helperText={t('procurement.bundleDiscountPercentageHelper') || 'Discount percentage'}
              InputProps={{ endAdornment: '%' }}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Payment Terms */}
      <Paper elevation={1} sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          {t('procurement.paymentTerms') || 'Payment Terms'}
        </Typography>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>{t('procurement.paymentType') || 'Payment Type'}</InputLabel>
              <Select
                value={data.payment_terms.type}
                onChange={(e) => {
                  const type = e.target.value as 'cash' | 'installments';
                  onChange({
                    payment_terms:
                      type === 'cash'
                        ? { type: 'cash', discount_percent: 0 }
                        : {
                            type: 'installments',
                            installments: [{ days_after_purchase: 0, percentage: 100 }],
                          },
                  });
                }}
              >
                <MenuItem value="cash">{t('procurement.cash') || 'Cash'}</MenuItem>
                <MenuItem value="installments">{t('procurement.installments') || 'Installments'}</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          {data.payment_terms.type === 'cash' && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={t('procurement.cashDiscountPercentage') || 'Cash Discount %'}
                type="number"
                value={data.payment_terms.discount_percent || 0}
                onChange={(e) =>
                  onChange({
                    payment_terms: {
                      ...data.payment_terms,
                      discount_percent: parseFloat(e.target.value) || 0,
                    },
                  })
                }
                InputProps={{ endAdornment: '%' }}
              />
            </Grid>
          )}
          {data.payment_terms.type === 'installments' && data.payment_terms.installments && (
            <Grid item xs={12}>
              <Typography variant="body2" gutterBottom>
                {t('procurement.installmentSchedule') || 'Installment Schedule (must total 100%)'}
              </Typography>
              {data.payment_terms.installments.map((installment, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                  <TextField
                    label={t('procurement.daysAfterPurchase') || 'Days After Purchase'}
                    type="number"
                    size="small"
                    value={installment.days_after_purchase}
                    onChange={(e) => {
                      const newInstallments = [...(data.payment_terms.installments || [])];
                      newInstallments[index].days_after_purchase = parseInt(e.target.value) || 0;
                      onChange({
                        payment_terms: {
                          ...data.payment_terms,
                          installments: newInstallments,
                        },
                      });
                    }}
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    label={t('procurement.percentage') || 'Percentage'}
                    type="number"
                    size="small"
                    value={installment.percentage}
                    onChange={(e) => {
                      const newInstallments = [...(data.payment_terms.installments || [])];
                      newInstallments[index].percentage = parseFloat(e.target.value) || 0;
                      onChange({
                        payment_terms: {
                          ...data.payment_terms,
                          installments: newInstallments,
                        },
                      });
                    }}
                    sx={{ flex: 1 }}
                    InputProps={{ endAdornment: '%' }}
                  />
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => {
                      const newInstallments = (data.payment_terms.installments || []).filter(
                        (_, i) => i !== index
                      );
                      onChange({
                        payment_terms: {
                          ...data.payment_terms,
                          installments:
                            newInstallments.length > 0
                              ? newInstallments
                              : [{ days_after_purchase: 0, percentage: 100 }],
                        },
                      });
                    }}
                    disabled={(data.payment_terms.installments || []).length === 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              ))}
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => {
                  const newInstallments = [
                    ...(data.payment_terms.installments || []),
                    { days_after_purchase: 30, percentage: 0 },
                  ];
                  onChange({
                    payment_terms: {
                      ...data.payment_terms,
                      installments: newInstallments,
                    },
                  });
                }}
                sx={{ mt: 1 }}
              >
                {t('procurement.addInstallment') || 'Add Installment'}
              </Button>
              <Typography
                variant="caption"
                color={
                  (data.payment_terms.installments || []).reduce(
                    (sum, inst) => sum + inst.percentage,
                    0
                  ) === 100
                    ? 'success.main'
                    : 'error.main'
                }
                sx={{ display: 'block', mt: 1 }}
              >
                Total:{' '}
                {(data.payment_terms.installments || []).reduce(
                  (sum, inst) => sum + inst.percentage,
                  0
                )}
                %
                {(data.payment_terms.installments || []).reduce(
                  (sum, inst) => sum + inst.percentage,
                  0
                ) !== 100 && ' (Must equal 100%)'}
              </Typography>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Finalized Checkbox */}
      <FormControlLabel
        control={
          <Checkbox
            checked={data.is_finalized || false}
            onChange={(e) => onChange({ is_finalized: e.target.checked })}
            color="success"
          />
        }
        label={
          <Box>
            <Typography variant="body2" fontWeight="medium">
              ✅ {t('procurement.markAsFinalized') || 'Mark as Finalized'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('procurement.onlyFinalizedOptions') ||
                'Only finalized options will be used in procurement optimization'}
            </Typography>
          </Box>
        }
      />
    </Box>
  );
};

