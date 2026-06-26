import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  TextField,
  Typography,
  Checkbox,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { LocalizedDateProvider } from '../LocalizedDateProvider.tsx';
import { currencyAPI, deliveryOptionsAPI, procurementFinancialsAPI } from '../../services/api.ts';
import type {
  Currency,
  DeliveryDateSource,
  PaymentMethod,
  PaymentTerms,
  ProcurementCostComponentPaymentMetadata,
  ProcurementCostComponentPaymentScheduleRow,
  ProcurementCostComponentPaymentType,
  ProcurementCostComponentPayeeType,
  ProcurementCostComponentType,
} from '../../types/index.ts';
import { formatApiError } from '../../utils/errorUtils.ts';
import {
  ALLOWED_COST_COMPONENT_TYPES,
  getCostComponentValidationMessage,
  validateCostComponentDraft,
} from './costComponentValidation.ts';

interface PackageWizardStep3Props {
  data: {
    option_id: number | null;
    base_cost: number;
    currency_id: number | null;
    shipping_cost: number;
    delivery_option_id: number | null;
    lomc_lead_time: number;
    purchase_date: string;
    expected_delivery_date: string;
    payment_terms: PaymentTerms;
    discount_bundle_threshold?: number;
    discount_bundle_percent?: number;
    is_finalized: boolean;
    main_item_quantity: number;
    payment_method_id: number | null;
    payment_date: string;
    description?: string;
    cost_components: CostComponentDraft[];
    project_requested_delivery_date?: string;
    supplier_actual_delivery_date?: string;
    selected_delivery_date?: string;
    delivery_date_source?: DeliveryDateSource | null;
    delivery_date_variance_days?: number | null;
    forecast_customer_invoice_date?: string;
    forecast_customer_invoice_date_source?: 'SYSTEM_DEFAULT' | 'MANUAL_OVERRIDE' | null;
    forecast_customer_receipt_date?: string;
    forecast_customer_receipt_date_source?: 'SYSTEM_DEFAULT' | 'MANUAL_OVERRIDE' | null;
    forecast_customer_receipt_delay_days?: number | null;
    date_calculation_trace?: string[];
  };
  projectItemId: number;
  onChange: (updates: Partial<PackageWizardStep3Props['data']>) => void;
}

interface CostComponentDraft {
  id?: number;
  component_type: ProcurementCostComponentType | '';
  description?: string;
  amount_value: number | '';
  amount_currency: string;
  amount_irr?: number;
  exchange_rate_date?: string;
  payment_metadata?: ProcurementCostComponentPaymentMetadata;
}

interface DeliveryOption {
  id: number;
  delivery_date: string;
}

interface PaymentScheduleRow {
  due_offset: number;
  percent: number;
}

const DEFAULT_COMPONENT_PAYEE_BY_TYPE: Record<
  ProcurementCostComponentType,
  ProcurementCostComponentPayeeType
> = {
  BASE_PRICE: 'SUPPLIER',
  SHIPPING: 'LOGISTICS_PROVIDER',
  VAT: 'SUPPLIER',
  CUSTOMS: 'CUSTOMS_OR_CLEARANCE',
  CLEARANCE: 'CUSTOMS_OR_CLEARANCE',
  INSURANCE: 'INSURANCE_PROVIDER',
  BANK_FEE: 'BANK_OR_EXCHANGE',
  OTHER: 'OTHER',
};

const buildDefaultComponentPaymentMetadata = (
  componentType: ProcurementCostComponentType | ''
): ProcurementCostComponentPaymentMetadata => ({
  inherit_option_payment_schedule: true,
  payee_type:
    componentType && componentType in DEFAULT_COMPONENT_PAYEE_BY_TYPE
      ? DEFAULT_COMPONENT_PAYEE_BY_TYPE[componentType as ProcurementCostComponentType]
      : 'SUPPLIER',
  payee_label: '',
  payment_method_id: null,
  payment_type: 'CASH',
  planned_payment_date: '',
  payment_schedule: [],
  notes: '',
});

const normalizeComponentPaymentMetadata = (
  componentType: ProcurementCostComponentType | '',
  metadata: unknown
): ProcurementCostComponentPaymentMetadata => {
  const raw = (metadata || {}) as Record<string, any>;
  const paymentType = String(raw.payment_type || 'CASH').toUpperCase();
  const schedule: ProcurementCostComponentPaymentScheduleRow[] = Array.isArray(raw.payment_schedule)
    ? raw.payment_schedule
        .map((row: any) => ({
          due_offset_days:
            row?.due_offset_days === undefined || row?.due_offset_days === null
              ? undefined
              : Math.max(0, Number(row.due_offset_days) || 0),
          due_date: row?.due_date || '',
          percent:
            row?.percent === undefined || row?.percent === null
              ? undefined
              : Number(row.percent),
          amount_value:
            row?.amount_value === undefined || row?.amount_value === null
              ? undefined
              : Number(row.amount_value),
          derived_effective_receipt_date: row?.derived_effective_receipt_date || '',
        }))
        .filter(
          (row: ProcurementCostComponentPaymentScheduleRow) =>
            row.due_offset_days !== undefined || !!row.due_date
        )
    : [];

  const fallbackPayeeType =
    componentType && componentType in DEFAULT_COMPONENT_PAYEE_BY_TYPE
      ? DEFAULT_COMPONENT_PAYEE_BY_TYPE[componentType as ProcurementCostComponentType]
      : 'SUPPLIER';

  return {
    inherit_option_payment_schedule: raw.inherit_option_payment_schedule !== false,
    payee_type: (String(raw.payee_type || fallbackPayeeType).toUpperCase() ||
      fallbackPayeeType) as ProcurementCostComponentPayeeType,
    payee_label: raw.payee_label || '',
    payment_method_id:
      raw.payment_method_id === undefined || raw.payment_method_id === null
        ? null
        : Number(raw.payment_method_id),
    payment_type:
      paymentType === 'INSTALLMENTS'
        ? ('INSTALLMENTS' as ProcurementCostComponentPaymentType)
        : ('CASH' as ProcurementCostComponentPaymentType),
    planned_payment_date: raw.planned_payment_date || '',
    payment_schedule: schedule,
    notes: raw.notes || '',
  };
};

export const calculateSupplierEffectiveReceiptDate = (
  paymentDate: string,
  settlementDelayDays: number
): string | null => {
  if (!paymentDate) return null;
  const parsedDate = new Date(`${paymentDate}T00:00:00`);
  if (Number.isNaN(parsedDate.getTime())) return null;
  const result = new Date(parsedDate);
  result.setDate(result.getDate() + Math.max(0, settlementDelayDays || 0));
  return gregorianFormat(result, 'yyyy-MM-dd');
};

const toDatePickerValue = (value?: string): Date | null => {
  if (!value) return null;
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const toIsoDate = (value: Date | null): string => {
  if (!value || Number.isNaN(value.getTime())) return '';
  return gregorianFormat(value, 'yyyy-MM-dd');
};

const diffDays = (fromDate?: string, toDate?: string): number | null => {
  if (!fromDate || !toDate) return null;
  try {
    const from = new Date(`${fromDate}T00:00:00`);
    const to = new Date(`${toDate}T00:00:00`);
    if (Number.isNaN(from.getTime()) || Number.isNaN(to.getTime())) return null;
    return Math.round((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24));
  } catch {
    return null;
  }
};

const normalizePaymentTerms = (paymentTerms: unknown): PaymentTerms => {
  const payload = (paymentTerms || {}) as Record<string, any>;
  if (payload.type !== 'installments') {
    return {
      type: 'cash',
      discount_percent: Number(payload.discount_percent || 0) || 0,
    };
  }

  const scheduleInput = Array.isArray(payload.schedule)
    ? payload.schedule
    : Array.isArray(payload.installments)
      ? payload.installments
      : [];

  const schedule: PaymentScheduleRow[] = scheduleInput
    .map((row: any) => ({
      due_offset: Math.max(0, Number(row?.due_offset ?? row?.days_after_purchase ?? 0) || 0),
      percent: Number(row?.percent ?? row?.percentage ?? 0) || 0,
    }))
    .filter((row: PaymentScheduleRow) => Number.isFinite(row.due_offset) && Number.isFinite(row.percent));

  return {
    type: 'installments',
    schedule: schedule.length > 0 ? schedule : [{ due_offset: 0, percent: 100 }],
  };
};

export const PackageWizardStep3: React.FC<PackageWizardStep3Props> = ({
  data,
  projectItemId,
  onChange,
}) => {
  const { t, i18n } = useTranslation();
  const [deliveryOptions, setDeliveryOptions] = useState<DeliveryOption[]>([]);
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loadedCostComponentsOptionId, setLoadedCostComponentsOptionId] = useState<number | null>(null);
  const [loadingFinancialData, setLoadingFinancialData] = useState(false);
  const [financialDataError, setFinancialDataError] = useState('');
  const [landedCostPreview, setLandedCostPreview] = useState<any>(null);
  const [loadingLandedCostPreview, setLoadingLandedCostPreview] = useState(false);
  const [landedCostPreviewError, setLandedCostPreviewError] = useState('');
  const [deliveryFinancialPreviewError, setDeliveryFinancialPreviewError] = useState('');

  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDate = useMemo(
    () => (dateString: string | null) => {
      if (!dateString) return '-';
      try {
        const parsedDate = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
        return isFa
          ? jalaliFormat(parsedDate, 'yyyy/MM/dd')
          : gregorianFormat(parsedDate, 'yyyy-MM-dd');
      } catch {
        return dateString;
      }
    },
    [isFa]
  );

  useEffect(() => {
    const fetchDeliveryOptions = async () => {
      try {
        const response = await deliveryOptionsAPI.listByItem(projectItemId);
        setDeliveryOptions(response.data || []);
      } catch {
        setDeliveryOptions([]);
      }
    };
    fetchDeliveryOptions();
  }, [projectItemId]);

  useEffect(() => {
    const fetchFinancialData = async () => {
      setLoadingFinancialData(true);
      setFinancialDataError('');
      try {
        const [paymentMethodsResponse, currenciesResponse] = await Promise.all([
          procurementFinancialsAPI.listPaymentMethods(true),
          currencyAPI.list(),
        ]);
        setPaymentMethods(paymentMethodsResponse.data || []);
        setCurrencies((currenciesResponse.data || []).filter((currency: Currency) => currency.is_active));
      } catch (err: any) {
        setFinancialDataError(formatApiError(err, t('procurement.paymentMethodsLoadFailed')));
        setPaymentMethods([]);
        setCurrencies([]);
      } finally {
        setLoadingFinancialData(false);
      }
    };
    fetchFinancialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const fetchCostComponents = async () => {
      if (!data.option_id) {
        setLoadedCostComponentsOptionId(null);
        return;
      }
      if (loadedCostComponentsOptionId === data.option_id) return;
      try {
        const response = await procurementFinancialsAPI.listCostComponents(data.option_id, true);
        const mappedComponents: CostComponentDraft[] = (response.data || []).map((component) => ({
          id: component.id,
          component_type: component.component_type,
          description: component.description || '',
          amount_value: Number(component.amount_value || 0),
          amount_currency: component.amount_currency,
          amount_irr:
            component.amount_irr !== null && component.amount_irr !== undefined
              ? Number(component.amount_irr)
              : undefined,
          exchange_rate_date: component.exchange_rate_date || undefined,
          payment_metadata: normalizeComponentPaymentMetadata(
            component.component_type,
            component.payment_metadata
          ),
        }));
        onChange({ cost_components: mappedComponents });
        setLoadedCostComponentsOptionId(data.option_id);
      } catch {
        // Best effort: keep editing flow usable even when components fail to load.
      }
    };
    fetchCostComponents();
  }, [data.option_id, loadedCostComponentsOptionId, onChange]);

  const earliestProjectRequestedDeliveryDate = useMemo(() => {
    if ((data.project_requested_delivery_date || '').trim()) {
      return data.project_requested_delivery_date || '';
    }
    if (!deliveryOptions.length) return '';
    const sorted = [...deliveryOptions]
      .map((option) => option.delivery_date)
      .filter(Boolean)
      .sort();
    return sorted[0] || '';
  }, [data.project_requested_delivery_date, deliveryOptions]);

  const selectedDeliveryDate = useMemo(
    () =>
      (data.supplier_actual_delivery_date || '').trim() ||
      (earliestProjectRequestedDeliveryDate || '').trim() ||
      '',
    [data.supplier_actual_delivery_date, earliestProjectRequestedDeliveryDate]
  );

  const derivedDeliverySource: DeliveryDateSource = useMemo(
    () => ((data.supplier_actual_delivery_date || '').trim() ? 'SUPPLIER_ACTUAL' : 'PROJECT_OPTION'),
    [data.supplier_actual_delivery_date]
  );

  const derivedVarianceDays = useMemo(
    () => diffDays(earliestProjectRequestedDeliveryDate, data.supplier_actual_delivery_date || ''),
    [earliestProjectRequestedDeliveryDate, data.supplier_actual_delivery_date]
  );

  useEffect(() => {
    const updates: Partial<PackageWizardStep3Props['data']> = {};
    if ((data.project_requested_delivery_date || '') !== earliestProjectRequestedDeliveryDate) {
      updates.project_requested_delivery_date = earliestProjectRequestedDeliveryDate;
    }
    if ((data.selected_delivery_date || '') !== selectedDeliveryDate) {
      updates.selected_delivery_date = selectedDeliveryDate;
    }
    if ((data.expected_delivery_date || '') !== selectedDeliveryDate) {
      updates.expected_delivery_date = selectedDeliveryDate;
    }
    if ((data.delivery_date_source || 'PROJECT_OPTION') !== derivedDeliverySource) {
      updates.delivery_date_source = derivedDeliverySource;
    }
    if ((data.delivery_date_variance_days ?? null) !== (derivedVarianceDays ?? null)) {
      updates.delivery_date_variance_days = derivedVarianceDays;
    }
    if (Object.keys(updates).length > 0) {
      onChange(updates);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    earliestProjectRequestedDeliveryDate,
    selectedDeliveryDate,
    derivedDeliverySource,
    derivedVarianceDays,
  ]);

  const normalizedCostComponents = useMemo(
    () =>
      (data.cost_components || []).map((component) => ({
        ...component,
        component_type: String(component.component_type || '').trim().toUpperCase() as
          | ProcurementCostComponentType
          | '',
        amount_currency: String(component.amount_currency || '').trim().toUpperCase(),
        amount_value:
          component.amount_value === '' || component.amount_value === null
            ? ''
            : Number(component.amount_value),
        payment_metadata: normalizeComponentPaymentMetadata(
          String(component.component_type || '').trim().toUpperCase() as ProcurementCostComponentType | '',
          component.payment_metadata
        ),
      })),
    [data.cost_components]
  );

  const validCostComponents = useMemo(
    () =>
      normalizedCostComponents.filter((component) => {
        const amount = Number(component.amount_value);
        return (
          ALLOWED_COST_COMPONENT_TYPES.includes(component.component_type as ProcurementCostComponentType) &&
          Number.isFinite(amount) &&
          amount > 0 &&
          !!component.amount_currency
        );
      }),
    [normalizedCostComponents]
  );

  const componentPaymentSummary = useMemo(() => {
    const summary = { inheritsDefault: 0, custom: 0 };
    (normalizedCostComponents || []).forEach((component) => {
      const metadata = normalizeComponentPaymentMetadata(
        component.component_type || '',
        component.payment_metadata
      );
      if (metadata.inherit_option_payment_schedule) {
        summary.inheritsDefault += 1;
      } else {
        summary.custom += 1;
      }
    });
    return summary;
  }, [normalizedCostComponents]);

  const mappedBaseComponent = useMemo(
    () => validCostComponents.find((component) => component.component_type === 'BASE_PRICE') || null,
    [validCostComponents]
  );

  const mappedShippingComponent = useMemo(
    () => validCostComponents.find((component) => component.component_type === 'SHIPPING') || null,
    [validCostComponents]
  );

  const mappedCurrencyCode = useMemo(
    () => mappedBaseComponent?.amount_currency || validCostComponents[0]?.amount_currency || '',
    [mappedBaseComponent, validCostComponents]
  );

  useEffect(() => {
    const updates: Partial<PackageWizardStep3Props['data']> = {};
    const nextBaseCost = mappedBaseComponent ? Number(mappedBaseComponent.amount_value) : 0;
    const nextShippingCost = mappedShippingComponent ? Number(mappedShippingComponent.amount_value) : 0;
    if (data.base_cost !== nextBaseCost) {
      updates.base_cost = nextBaseCost;
    }
    if (data.shipping_cost !== nextShippingCost) {
      updates.shipping_cost = nextShippingCost;
    }

    if (mappedCurrencyCode) {
      const mappedCurrency = currencies.find((currency) => currency.code === mappedCurrencyCode);
      if (mappedCurrency && data.currency_id !== mappedCurrency.id) {
        updates.currency_id = mappedCurrency.id;
      }
    }

    if (Object.keys(updates).length > 0) {
      onChange(updates);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mappedBaseComponent, mappedShippingComponent, mappedCurrencyCode, currencies]);

  const totalsByCurrency = useMemo(() => {
    const totals: Record<string, number> = {};
    validCostComponents.forEach((component) => {
      const amount = Number(component.amount_value);
      if (!Number.isFinite(amount) || amount <= 0) return;
      const currency = component.amount_currency || 'IRR';
      totals[currency] = (totals[currency] || 0) + amount;
    });
    return totals;
  }, [validCostComponents]);

  const loadLandedCostPreview = async () => {
    if (!data.option_id) {
      setLandedCostPreview(null);
      setLandedCostPreviewError('');
      return;
    }
    setLoadingLandedCostPreview(true);
    try {
      const response = await procurementFinancialsAPI.getLandedCostPreview(data.option_id);
      setLandedCostPreview(response.data);
      setLandedCostPreviewError('');
    } catch (err: any) {
      setLandedCostPreview(null);
      setLandedCostPreviewError(formatApiError(err, t('procurement.failedToLoadLandedCostPreview')));
    } finally {
      setLoadingLandedCostPreview(false);
    }
  };

  useEffect(() => {
    loadLandedCostPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.option_id]);

  useEffect(() => {
    const loadDeliveryFinancialPreview = async () => {
      if (!data.option_id) {
        setDeliveryFinancialPreviewError('');
        return;
      }
      try {
        const response = await procurementFinancialsAPI.getDeliveryFinancialPreview(data.option_id, {
          delivery_date_source: derivedDeliverySource,
          supplier_actual_delivery_date: data.supplier_actual_delivery_date || undefined,
          selected_delivery_date: selectedDeliveryDate || undefined,
        });
        const preview = response.data;
        const updates: Partial<PackageWizardStep3Props['data']> = {};

        if ((data.project_requested_delivery_date || '') !== (preview.project_requested_delivery_date || '')) {
          updates.project_requested_delivery_date = preview.project_requested_delivery_date || '';
        }
        if ((data.selected_delivery_date || '') !== (preview.selected_delivery_date || '')) {
          updates.selected_delivery_date = preview.selected_delivery_date || '';
        }
        if ((data.delivery_date_source || 'PROJECT_OPTION') !== (preview.delivery_date_source || 'PROJECT_OPTION')) {
          updates.delivery_date_source = (preview.delivery_date_source || 'PROJECT_OPTION') as DeliveryDateSource;
        }
        if ((data.delivery_date_variance_days ?? null) !== (preview.delivery_date_variance_days ?? null)) {
          updates.delivery_date_variance_days = preview.delivery_date_variance_days ?? null;
        }
        if ((data.forecast_customer_invoice_date || '') !== (preview.forecast_customer_invoice_date || '')) {
          updates.forecast_customer_invoice_date = preview.forecast_customer_invoice_date || '';
        }
        if (
          (data.forecast_customer_invoice_date_source || null) !==
          (preview.forecast_customer_invoice_date_source || null)
        ) {
          updates.forecast_customer_invoice_date_source =
            preview.forecast_customer_invoice_date_source || null;
        }
        if ((data.forecast_customer_receipt_date || '') !== (preview.forecast_customer_receipt_date || '')) {
          updates.forecast_customer_receipt_date = preview.forecast_customer_receipt_date || '';
        }
        if (
          (data.forecast_customer_receipt_date_source || null) !==
          (preview.forecast_customer_receipt_date_source || null)
        ) {
          updates.forecast_customer_receipt_date_source =
            preview.forecast_customer_receipt_date_source || null;
        }
        if (
          (data.forecast_customer_receipt_delay_days ?? null) !==
          (preview.forecast_customer_receipt_delay_days ?? null)
        ) {
          updates.forecast_customer_receipt_delay_days =
            preview.forecast_customer_receipt_delay_days ?? null;
        }
        if (
          JSON.stringify(data.date_calculation_trace || []) !==
          JSON.stringify(preview.trace_lines || [])
        ) {
          updates.date_calculation_trace = preview.trace_lines || [];
        }
        if (Object.keys(updates).length > 0) {
          onChange(updates);
        }
        setDeliveryFinancialPreviewError('');
      } catch (err: any) {
        setDeliveryFinancialPreviewError(
          formatApiError(err, t('procurement.failedToLoadDeliveryFinancialPreview'))
        );
      }
    };
    loadDeliveryFinancialPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.option_id, data.supplier_actual_delivery_date, selectedDeliveryDate, derivedDeliverySource]);

  const selectedPaymentMethod = useMemo(
    () => paymentMethods.find((paymentMethod) => paymentMethod.id === data.payment_method_id) || null,
    [paymentMethods, data.payment_method_id]
  );

  const normalizedPaymentTerms = useMemo(
    () => normalizePaymentTerms(data.payment_terms),
    [data.payment_terms]
  );

  const installmentSchedule = useMemo(
    () =>
      normalizedPaymentTerms.type === 'installments'
        ? normalizedPaymentTerms.schedule || []
        : [],
    [normalizedPaymentTerms]
  );

  const installmentTotalPercent = useMemo(
    () => installmentSchedule.reduce((sum, row) => sum + Number(row.percent || 0), 0),
    [installmentSchedule]
  );

  const supplierEffectiveReceiptDate = useMemo(
    () =>
      selectedPaymentMethod
        ? calculateSupplierEffectiveReceiptDate(
            data.payment_date,
            selectedPaymentMethod.settlement_delay_days || 0
          )
        : null,
    [data.payment_date, selectedPaymentMethod]
  );

  const defaultCostComponentCurrency = useMemo(() => {
    if (currencies.length === 0) return 'IRR';
    const selectedById = currencies.find((currency) => currency.id === data.currency_id);
    return selectedById?.code || currencies[0].code || 'IRR';
  }, [currencies, data.currency_id]);

  useEffect(() => {
    const nextPaymentTerms = normalizePaymentTerms(data.payment_terms);
    if (JSON.stringify(nextPaymentTerms) !== JSON.stringify(data.payment_terms || {})) {
      onChange({ payment_terms: nextPaymentTerms });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.payment_terms]);

  useEffect(() => {
    const current = data.cost_components || [];
    const hasBasePrice = current.some((component) => component.component_type === 'BASE_PRICE');
    if (hasBasePrice) return;
    onChange({
      cost_components: [
        {
          component_type: 'BASE_PRICE',
          description: '',
          amount_value: '',
          amount_currency: defaultCostComponentCurrency,
          payment_metadata: buildDefaultComponentPaymentMetadata('BASE_PRICE'),
        },
        ...current,
      ],
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.cost_components, defaultCostComponentCurrency]);

  const updateCostComponentAt = (index: number, updates: Partial<CostComponentDraft>) => {
    const nextComponents = [...(data.cost_components || [])];
    const currentComponent = nextComponents[index];
    const nextComponent = { ...currentComponent, ...updates };
    const nextType = (nextComponent.component_type || '') as ProcurementCostComponentType | '';
    nextComponent.payment_metadata = normalizeComponentPaymentMetadata(
      nextType,
      nextComponent.payment_metadata
    );
    if (
      updates.component_type !== undefined &&
      nextComponent.payment_metadata.inherit_option_payment_schedule
    ) {
      nextComponent.payment_metadata = {
        ...nextComponent.payment_metadata,
        payee_type:
          nextType && nextType in DEFAULT_COMPONENT_PAYEE_BY_TYPE
            ? DEFAULT_COMPONENT_PAYEE_BY_TYPE[nextType as ProcurementCostComponentType]
            : nextComponent.payment_metadata.payee_type,
      };
    }
    nextComponents[index] = nextComponent;
    onChange({ cost_components: nextComponents });
  };

  const removeCostComponentAt = (index: number) => {
    const nextComponents = [...(data.cost_components || [])];
    nextComponents.splice(index, 1);
    onChange({ cost_components: nextComponents });
  };

  const addCostComponent = () => {
    const nextComponents = [
      ...(data.cost_components || []),
      {
        component_type: '' as ProcurementCostComponentType | '',
        description: '',
        amount_value: '',
        amount_currency: defaultCostComponentCurrency,
        payment_metadata: buildDefaultComponentPaymentMetadata(''),
      },
    ];
    onChange({ cost_components: nextComponents });
  };

  const setPaymentTerms = (nextPaymentTerms: PaymentTerms) => {
    onChange({ payment_terms: normalizePaymentTerms(nextPaymentTerms) });
  };

  const updateInstallmentAt = (index: number, updates: Partial<PaymentScheduleRow>) => {
    const nextSchedule = [...installmentSchedule];
    nextSchedule[index] = { ...nextSchedule[index], ...updates };
    setPaymentTerms({ type: 'installments', schedule: nextSchedule });
  };

  const removeInstallmentAt = (index: number) => {
    const nextSchedule = installmentSchedule.filter((_, scheduleIndex) => scheduleIndex !== index);
    setPaymentTerms({
      type: 'installments',
      schedule: nextSchedule.length > 0 ? nextSchedule : [{ due_offset: 0, percent: 100 }],
    });
  };

  const addInstallment = () => {
    setPaymentTerms({
      type: 'installments',
      schedule: [...installmentSchedule, { due_offset: 30, percent: 0 }],
    });
  };

  const getComponentPaymentMethod = (component: CostComponentDraft): PaymentMethod | null => {
    const metadata = normalizeComponentPaymentMetadata(
      component.component_type || '',
      component.payment_metadata
    );
    const methodId = metadata.inherit_option_payment_schedule
      ? data.payment_method_id
      : metadata.payment_method_id;
    return paymentMethods.find((method) => method.id === methodId) || null;
  };

  const getComponentPaymentType = (component: CostComponentDraft): 'CASH' | 'INSTALLMENTS' => {
    const metadata = normalizeComponentPaymentMetadata(
      component.component_type || '',
      component.payment_metadata
    );
    if (metadata.inherit_option_payment_schedule) {
      return normalizedPaymentTerms.type === 'installments' ? 'INSTALLMENTS' : 'CASH';
    }
    return metadata.payment_type;
  };

  const getComponentPlannedPaymentDate = (component: CostComponentDraft): string => {
    const metadata = normalizeComponentPaymentMetadata(
      component.component_type || '',
      component.payment_metadata
    );
    if (metadata.inherit_option_payment_schedule) return data.payment_date || '';
    return metadata.planned_payment_date || '';
  };

  const updateComponentPaymentMetadata = (
    index: number,
    updates: Partial<ProcurementCostComponentPaymentMetadata>
  ) => {
    const current = data.cost_components?.[index];
    if (!current) return;
    const normalized = normalizeComponentPaymentMetadata(
      current.component_type || '',
      current.payment_metadata
    );
    updateCostComponentAt(index, {
      payment_metadata: {
        ...normalized,
        ...updates,
      },
    });
  };

  const updateComponentInstallmentAt = (
    componentIndex: number,
    scheduleIndex: number,
    updates: Partial<ProcurementCostComponentPaymentScheduleRow>
  ) => {
    const component = data.cost_components?.[componentIndex];
    if (!component) return;
    const metadata = normalizeComponentPaymentMetadata(
      component.component_type || '',
      component.payment_metadata
    );
    const schedule = [...(metadata.payment_schedule || [])];
    schedule[scheduleIndex] = { ...schedule[scheduleIndex], ...updates };
    updateComponentPaymentMetadata(componentIndex, { payment_schedule: schedule });
  };

  const addComponentInstallment = (componentIndex: number) => {
    const component = data.cost_components?.[componentIndex];
    if (!component) return;
    const metadata = normalizeComponentPaymentMetadata(
      component.component_type || '',
      component.payment_metadata
    );
    const schedule = [...(metadata.payment_schedule || [])];
    schedule.push({
      due_offset_days: 30,
      percent: 0,
    });
    updateComponentPaymentMetadata(componentIndex, { payment_schedule: schedule });
  };

  const removeComponentInstallment = (componentIndex: number, scheduleIndex: number) => {
    const component = data.cost_components?.[componentIndex];
    if (!component) return;
    const metadata = normalizeComponentPaymentMetadata(
      component.component_type || '',
      component.payment_metadata
    );
    const schedule = (metadata.payment_schedule || []).filter((_, idx) => idx !== scheduleIndex);
    updateComponentPaymentMetadata(componentIndex, {
      payment_schedule: schedule.length > 0 ? schedule : [{ due_offset_days: 0, percent: 100 }],
    });
  };

  const getComponentTypeLabel = (componentType: ProcurementCostComponentType) => {
    const labels: Record<ProcurementCostComponentType, string> = {
      BASE_PRICE: t('procurement.basePrice'),
      SHIPPING: t('procurement.shipping'),
      VAT: t('procurement.vat'),
      CUSTOMS: t('procurement.customs'),
      CLEARANCE: t('procurement.clearance'),
      INSURANCE: t('procurement.insurance'),
      BANK_FEE: t('procurement.bankFee'),
      OTHER: t('procurement.other'),
    };
    return labels[componentType];
  };

  const varianceSummary = useMemo(() => {
    if (data.delivery_date_variance_days === null || data.delivery_date_variance_days === undefined) {
      return t('procurement.deliveryVarianceUnavailable');
    }
    if (data.delivery_date_variance_days < 0) {
      return `${t('procurement.early')} ${Math.abs(data.delivery_date_variance_days)} ${t('procurement.days')}`;
    }
    if (data.delivery_date_variance_days > 0) {
      return `${t('procurement.delayed')} ${data.delivery_date_variance_days} ${t('procurement.days')}`;
    }
    return `${t('procurement.onTime')} (0 ${t('procurement.days')})`;
  }, [data.delivery_date_variance_days, t]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {financialDataError && <Alert severity="warning">{financialDataError}</Alert>}
      {deliveryFinancialPreviewError && <Alert severity="warning">{deliveryFinancialPreviewError}</Alert>}

      <Paper elevation={1} sx={{ p: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1.5}>
          <Typography variant="h6">
            {t('procurement.pricingAndCosts')}
          </Typography>
          <Button size="small" variant="outlined" startIcon={<AddIcon />} onClick={addCostComponent}>
            {t('procurement.addCostComponent')}
          </Button>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('procurement.costComponents')}
        </Typography>

        {(data.cost_components || []).length === 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {t('procurement.noCostComponents')}
          </Alert>
        )}

        {(data.cost_components || []).map((component, index) => {
          const primaryBaseIndex = (data.cost_components || []).findIndex(
            (row) => row.component_type === 'BASE_PRICE'
          );
          const basePriceCount = (data.cost_components || []).filter(
            (row) => row.component_type === 'BASE_PRICE'
          ).length;
          const isPrimaryBaseRow =
            component.component_type === 'BASE_PRICE' && index === primaryBaseIndex;
          const componentPaymentMetadata = normalizeComponentPaymentMetadata(
            component.component_type || '',
            component.payment_metadata
          );
          const componentPaymentType = getComponentPaymentType(component);
          const componentPlannedPaymentDate = getComponentPlannedPaymentDate(component);
          const componentPaymentMethod = getComponentPaymentMethod(component);
          const componentInstallmentSchedule =
            componentPaymentMetadata.payment_schedule && componentPaymentMetadata.payment_schedule.length > 0
              ? componentPaymentMetadata.payment_schedule
              : [{ due_offset_days: 0, percent: 100 }];
          const componentInstallmentPercentTotal = componentInstallmentSchedule.reduce(
            (sum, row) => sum + Number(row.percent || 0),
            0
          );
          const validationCode = validateCostComponentDraft(component);
          const validationError = validationCode
            ? getCostComponentValidationMessage(validationCode, t)
            : null;
          return (
            <Paper key={`${component.id || 'new'}-${index}`} variant="outlined" sx={{ p: 1.5, mb: 1.5 }}>
              <Grid container spacing={1.5}>
                <Grid item xs={12} sm={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>{t('procurement.componentType')}</InputLabel>
                    <Select
                      value={component.component_type}
                      label={t('procurement.componentType')}
                      disabled={isPrimaryBaseRow}
                      onChange={(e) =>
                        updateCostComponentAt(index, {
                          component_type: e.target.value as ProcurementCostComponentType | '',
                        })
                      }
                    >
                      <MenuItem value="">
                        {t('common.select')}
                      </MenuItem>
                      {ALLOWED_COST_COMPONENT_TYPES.map((componentType) => (
                        <MenuItem key={componentType} value={componentType}>
                          {getComponentTypeLabel(componentType)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={3}>
            <TextField
                    size="small"
              fullWidth
                    type="number"
                    label={t('procurement.amount')}
                    value={component.amount_value}
                    onChange={(e) =>
                      updateCostComponentAt(index, {
                        amount_value: e.target.value === '' ? '' : Number(e.target.value),
                      })
                    }
                    inputProps={{ min: 0.01, step: 0.01 }}
            />
          </Grid>
                <Grid item xs={12} sm={2}>
                  <FormControl fullWidth size="small">
                    <InputLabel>{t('procurement.currency')}</InputLabel>
                    <Select
                      value={component.amount_currency}
                      label={t('procurement.currency')}
                      onChange={(e) =>
                        updateCostComponentAt(index, {
                          amount_currency: String(e.target.value || '').toUpperCase(),
                        })
                      }
                    >
                      <MenuItem value="">
                        {t('common.select')}
                      </MenuItem>
                      {currencies.map((currency) => (
                        <MenuItem key={currency.code} value={currency.code}>
                          {currency.code}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={3}>
            <TextField
                    size="small"
              fullWidth
                    label={t('procurement.description')}
                    value={component.description || ''}
                    onChange={(e) => updateCostComponentAt(index, { description: e.target.value })}
                    required={component.component_type === 'OTHER'}
            />
          </Grid>
                <Grid item xs={12} sm={1} display="flex" alignItems="center" justifyContent="flex-end">
                  <IconButton
                    color="error"
                    onClick={() => removeCostComponentAt(index)}
                    disabled={isPrimaryBaseRow && basePriceCount <= 1}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Grid>
                <Grid item xs={12}>
                  <Paper variant="outlined" sx={{ p: 1.5, backgroundColor: 'grey.50' }}>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      {t('procurement.componentPaymentPanelTitle')}
                    </Typography>
                    <Grid container spacing={1.5}>
                      <Grid item xs={12} sm={4}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={componentPaymentMetadata.inherit_option_payment_schedule}
                              onChange={(event) =>
                                updateComponentPaymentMetadata(index, {
                                  inherit_option_payment_schedule: event.target.checked,
                                  payment_method_id: event.target.checked
                                    ? null
                                    : componentPaymentMetadata.payment_method_id || data.payment_method_id || null,
                                  payment_type: event.target.checked
                                    ? ('CASH' as ProcurementCostComponentPaymentType)
                                    : componentPaymentMetadata.payment_type,
                                  planned_payment_date: event.target.checked
                                    ? ''
                                    : componentPaymentMetadata.planned_payment_date || data.payment_date || '',
                                  payment_schedule: event.target.checked
                                    ? []
                                    : componentPaymentMetadata.payment_schedule || [{ due_offset_days: 0, percent: 100 }],
                                })
                              }
                            />
                          }
                          label={t('procurement.useDefaultPaymentSchedule')}
                        />
                      </Grid>
                      <Grid item xs={12} sm={4}>
                        <FormControl fullWidth size="small">
                          <InputLabel>{t('procurement.paymentPayeeType')}</InputLabel>
                          <Select
                            value={componentPaymentMetadata.payee_type}
                            label={t('procurement.paymentPayeeType')}
                            onChange={(event) =>
                              updateComponentPaymentMetadata(index, {
                                payee_type: event.target.value as ProcurementCostComponentPayeeType,
                              })
                            }
                          >
                            <MenuItem value="SUPPLIER">{t('procurement.payeeTypeSupplier')}</MenuItem>
                            <MenuItem value="LOGISTICS_PROVIDER">
                              {t('procurement.payeeTypeLogisticsProvider')}
                            </MenuItem>
                            <MenuItem value="INSURANCE_PROVIDER">
                              {t('procurement.payeeTypeInsuranceProvider')}
                            </MenuItem>
                            <MenuItem value="CUSTOMS_OR_CLEARANCE">
                              {t('procurement.payeeTypeCustomsOrClearance')}
                            </MenuItem>
                            <MenuItem value="BANK_OR_EXCHANGE">
                              {t('procurement.payeeTypeBankOrExchange')}
                            </MenuItem>
                            <MenuItem value="OTHER">{t('procurement.payeeTypeOther')}</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      <Grid item xs={12} sm={4}>
                        <TextField
                          size="small"
                          fullWidth
                          label={t('procurement.paymentPayeeLabel')}
                          value={componentPaymentMetadata.payee_label || ''}
                          onChange={(event) =>
                            updateComponentPaymentMetadata(index, {
                              payee_label: event.target.value,
                            })
                          }
                        />
                      </Grid>

                      {!componentPaymentMetadata.inherit_option_payment_schedule && (
                        <>
                          <Grid item xs={12} sm={4}>
                            <FormControl fullWidth size="small">
                              <InputLabel>{t('procurement.paymentMethod')}</InputLabel>
                              <Select
                                value={componentPaymentMetadata.payment_method_id || ''}
                                label={t('procurement.paymentMethod')}
                                onChange={(event) =>
                                  updateComponentPaymentMetadata(index, {
                                    payment_method_id: Number(event.target.value) || null,
                                  })
                                }
                              >
                                <MenuItem value="">{t('common.select')}</MenuItem>
                                {paymentMethods.map((paymentMethod) => (
                                  <MenuItem key={paymentMethod.id} value={paymentMethod.id}>
                                    {isFa ? paymentMethod.name_fa : paymentMethod.name_en}
                                  </MenuItem>
                                ))}
                              </Select>
                            </FormControl>
                          </Grid>
                          <Grid item xs={12} sm={4}>
                            <FormControl fullWidth size="small">
                              <InputLabel>{t('procurement.paymentType')}</InputLabel>
                              <Select
                                value={componentPaymentType}
                                label={t('procurement.paymentType')}
                                onChange={(event) =>
                                  updateComponentPaymentMetadata(index, {
                                    payment_type: event.target.value as ProcurementCostComponentPaymentType,
                                    payment_schedule:
                                      event.target.value === 'INSTALLMENTS'
                                        ? componentPaymentMetadata.payment_schedule?.length
                                          ? componentPaymentMetadata.payment_schedule
                                          : [{ due_offset_days: 0, percent: 100 }]
                                        : [],
                                  })
                                }
                              >
                                <MenuItem value="CASH">{t('procurement.cash')}</MenuItem>
                                <MenuItem value="INSTALLMENTS">{t('procurement.installments')}</MenuItem>
                              </Select>
                            </FormControl>
                          </Grid>
                          <Grid item xs={12} sm={4}>
                            <LocalizedDateProvider>
                              <DatePicker
                                label={t('procurement.firstPaymentDate')}
                                value={toDatePickerValue(componentPlannedPaymentDate || '')}
                                onChange={(newValue) =>
                                  updateComponentPaymentMetadata(index, {
                                    planned_payment_date: toIsoDate(newValue),
                                  })
                                }
                                slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                              />
                            </LocalizedDateProvider>
                          </Grid>
                          {componentPaymentType === 'INSTALLMENTS' && (
                            <Grid item xs={12}>
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                {t('procurement.componentInstallmentSchedule')}
                              </Typography>
                              {componentInstallmentSchedule.map((row, scheduleIndex) => (
                                <Grid
                                  container
                                  spacing={1}
                                  alignItems="center"
                                  sx={{ mb: 1 }}
                                  key={`component-${index}-installment-${scheduleIndex}`}
                                >
                                  <Grid item xs={12} sm={3}>
                                    <TextField
                                      size="small"
                                      fullWidth
                                      type="number"
                                      label={t('procurement.nextPaymentOffsetDays')}
                                      value={
                                        row.due_offset_days === undefined ? '' : row.due_offset_days
                                      }
                                      onChange={(event) =>
                                        updateComponentInstallmentAt(index, scheduleIndex, {
                                          due_offset_days:
                                            event.target.value === ''
                                              ? undefined
                                              : Math.max(0, Number(event.target.value) || 0),
                                        })
                                      }
                                      inputProps={{ min: 0, step: 1 }}
                                    />
                                  </Grid>
                                  <Grid item xs={12} sm={3}>
                                    <LocalizedDateProvider>
                                      <DatePicker
                                        label={t('procurement.exactPaymentDate')}
                                        value={toDatePickerValue(row.due_date || '')}
                                        onChange={(newValue) =>
                                          updateComponentInstallmentAt(index, scheduleIndex, {
                                            due_date: toIsoDate(newValue),
                                          })
                                        }
                                        slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                                      />
                                    </LocalizedDateProvider>
                                  </Grid>
                                  <Grid item xs={12} sm={3}>
                                    <TextField
                                      size="small"
                                      fullWidth
                                      type="number"
                                      label={t('procurement.percentage')}
                                      value={row.percent === undefined ? '' : row.percent}
                                      onChange={(event) =>
                                        updateComponentInstallmentAt(index, scheduleIndex, {
                                          percent:
                                            event.target.value === ''
                                              ? undefined
                                              : Number(event.target.value || 0),
                                        })
                                      }
                                      inputProps={{ min: 0, max: 100, step: 0.01 }}
                                    />
                                  </Grid>
                                  <Grid item xs={12} sm={2}>
                                    <TextField
                                      size="small"
                                      fullWidth
                                      disabled
                                      label={t('procurement.payeeEffectiveReceiptDate')}
                                      value={
                                        row.derived_effective_receipt_date
                                          ? formatDisplayDate(row.derived_effective_receipt_date)
                                          : '-'
                                      }
                                    />
                                  </Grid>
                                  <Grid item xs={12} sm={1}>
                                    <IconButton
                                      color="error"
                                      onClick={() => removeComponentInstallment(index, scheduleIndex)}
                                      disabled={componentInstallmentSchedule.length <= 1}
                                    >
                                      <DeleteIcon fontSize="small" />
                                    </IconButton>
                                  </Grid>
                                </Grid>
                              ))}
                              <Button
                                size="small"
                                startIcon={<AddIcon />}
                                onClick={() => addComponentInstallment(index)}
                              >
                                {t('procurement.addInstallment')}
                              </Button>
                              <Typography
                                variant="caption"
                                sx={{ display: 'block', mt: 0.75 }}
                                color={
                                  Math.abs(componentInstallmentPercentTotal - 100) <= 0.01
                                    ? 'success.main'
                                    : 'error.main'
                                }
                              >
                                {t('procurement.percentage')}: {componentInstallmentPercentTotal.toFixed(2)}%
                              </Typography>
                            </Grid>
                          )}
                          {componentPaymentMethod && componentPlannedPaymentDate && (
                            <Grid item xs={12}>
                              <Alert severity="info">
                                {t('procurement.payeeEffectiveReceiptDate')}: {' '}
                                {formatDisplayDate(
                                  calculateSupplierEffectiveReceiptDate(
                                    componentPlannedPaymentDate,
                                    componentPaymentMethod.settlement_delay_days || 0
                                  )
                                )}
                              </Alert>
                            </Grid>
                          )}
                        </>
                      )}
                    </Grid>
                  </Paper>
                </Grid>
                {validationError && (
          <Grid item xs={12}>
                    <Typography variant="caption" color="error">
                      {validationError}
                    </Typography>
          </Grid>
                )}
        </Grid>
            </Paper>
          );
        })}

        <Grid container spacing={2} sx={{ mt: 0.5, mb: 1 }}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="number"
              label={t('procurement.bundleDiscountThreshold')}
              value={data.discount_bundle_threshold ?? ''}
              onChange={(e) =>
                onChange({
                  discount_bundle_threshold:
                    e.target.value === '' ? undefined : Number(e.target.value),
                })
              }
              inputProps={{ min: 1, step: 1 }}
              helperText={t('procurement.bundleDiscountThresholdHelper')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="number"
              label={t('procurement.bundleDiscountPercentage')}
              value={data.discount_bundle_percent ?? ''}
              onChange={(e) =>
                onChange({
                  discount_bundle_percent:
                    e.target.value === '' ? undefined : Number(e.target.value),
                })
              }
              inputProps={{ min: 0, max: 100, step: 0.01 }}
              helperText={t('procurement.bundleDiscountPercentageHelper')}
            />
          </Grid>
        </Grid>

        {!mappedBaseComponent && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {t('procurement.basePriceRequired')}
          </Alert>
        )}

        <Typography variant="body2" sx={{ mb: 1 }}>
          {t('procurement.totalsByCurrency')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {Object.entries(totalsByCurrency).length === 0 ? (
            <Chip label={`-`} size="small" />
          ) : (
            Object.entries(totalsByCurrency).map(([currencyCode, total]) => (
              <Chip key={currencyCode} label={`${currencyCode}: ${total.toLocaleString()}`} size="small" />
            ))
          )}
        </Box>

        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="body2" fontWeight={600}>
            {t('procurement.landedCostPreview')}
          </Typography>
          <Button
            size="small"
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadLandedCostPreview}
            disabled={!data.option_id || loadingLandedCostPreview}
          >
            {loadingLandedCostPreview ? t('procurement.loading') : t('procurement.refresh')}
          </Button>
        </Box>
        {!data.option_id && (
          <Alert severity="info">
            {t('procurement.previewAvailableAfterSaving')}
          </Alert>
        )}
        {data.option_id && landedCostPreviewError && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            {landedCostPreviewError}
          </Alert>
        )}
        {data.option_id && landedCostPreview && (
          <Box>
            <Typography variant="body2" sx={{ mb: 1 }}>
              {t('procurement.totalsByCurrency')}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
              {Object.keys(landedCostPreview.totals_by_currency || {}).length === 0 ? (
                <Chip label="-" size="small" />
              ) : (
                Object.entries(landedCostPreview.totals_by_currency || {}).map(
                  ([currencyCode, total]) => (
                    <Chip
                      key={currencyCode}
                      label={`${currencyCode}: ${Number(total || 0).toLocaleString()}`}
                      size="small"
                    />
                  )
                )
              )}
            </Box>
            <Typography variant="body2">
              {t('procurement.totalIrr')}: {' '}
              {landedCostPreview.total_irr !== null && landedCostPreview.total_irr !== undefined
                ? Number(landedCostPreview.total_irr).toLocaleString()
                : t('procurement.unavailableDueToMissingExchangeRates')}
            </Typography>
            {(landedCostPreview.missing_exchange_rates || []).length > 0 && (
              <Alert severity="warning" sx={{ mt: 1 }}>
                <Typography variant="body2" fontWeight={600}>
                  {t('procurement.missingExchangeRates')}
                </Typography>
                {(landedCostPreview.missing_exchange_rates || []).slice(0, 3).map((item: any, index: number) => (
                  <Typography key={`${item?.currency || 'currency'}-${index}`} variant="caption" display="block">
                    {(item?.currency || '').toString()} {item?.exchange_rate_date ? `(${item.exchange_rate_date})` : ''}
                  </Typography>
                ))}
              </Alert>
            )}
            {(landedCostPreview.trace_lines || []).length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {t('procurement.calculationTrace')}
                </Typography>
                {(landedCostPreview.trace_lines || []).slice(0, 3).map((line: string, index: number) => (
                  <Typography key={`trace-line-${index}`} variant="caption" display="block" color="text.secondary">
                    • {line}
                  </Typography>
                ))}
              </Box>
            )}
          </Box>
        )}
      </Paper>

      <Paper elevation={1} sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 1.5 }}>
          {t('procurement.delivery')}
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              disabled
              label={t('procurement.projectRequestedDeliveryDate')}
              value={formatDisplayDate(earliestProjectRequestedDeliveryDate || null)}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <LocalizedDateProvider>
              <DatePicker
                label={t('procurement.supplierActualAvailableDeliveryDate')}
                value={toDatePickerValue(data.supplier_actual_delivery_date)}
                onChange={(newValue) =>
                  onChange({ supplier_actual_delivery_date: toIsoDate(newValue) })
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </LocalizedDateProvider>
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              disabled
              label={t('procurement.selectedDeliveryDate')}
              value={formatDisplayDate(selectedDeliveryDate || null)}
            />
          </Grid>
          <Grid item xs={12}>
            <Alert
              severity={
                data.delivery_date_variance_days === null || data.delivery_date_variance_days === undefined
                  ? 'info'
                  : data.delivery_date_variance_days > 0
                    ? 'warning'
                    : 'success'
              }
            >
              <Typography variant="body2" component="span" fontWeight={600}>
                {t('procurement.deliveryVariance')}: {' '}
              </Typography>
              <Typography variant="body2" component="span">
                {varianceSummary}
              </Typography>
            </Alert>
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              minRows={2}
              label={t('procurement.supplierDeliveryNotes')}
              value={data.description || ''}
              onChange={(e) => onChange({ description: e.target.value })}
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper elevation={1} sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 1.5 }}>
          {t('procurement.payment')}
        </Typography>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          {t('procurement.defaultPaymentSchedule')}
        </Typography>
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            {t('procurement.defaultPaymentScheduleDescription')}
          </Typography>
          <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
            {t('procurement.componentsUsingDefaultSchedule')}: {componentPaymentSummary.inheritsDefault} |{' '}
            {t('procurement.componentsUsingCustomSchedule')}: {componentPaymentSummary.custom}
          </Typography>
        </Alert>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>{t('procurement.paymentType')}</InputLabel>
              <Select
                value={normalizedPaymentTerms.type}
                label={t('procurement.paymentType')}
                onChange={(e) => {
                  const nextType = e.target.value as 'cash' | 'installments';
                  if (nextType === 'cash') {
                    setPaymentTerms({
                      type: 'cash',
                      discount_percent:
                        normalizedPaymentTerms.type === 'cash'
                          ? normalizedPaymentTerms.discount_percent || 0
                          : 0,
                    });
                    return;
                  }
                  const existingSchedule =
                    normalizedPaymentTerms.type === 'installments'
                      ? normalizedPaymentTerms.schedule || []
                      : [];
                  setPaymentTerms({
                    type: 'installments',
                    schedule:
                      existingSchedule.length > 0
                        ? existingSchedule
                        : [{ due_offset: 0, percent: 100 }],
                  });
                }}
              >
                <MenuItem value="cash">{t('procurement.cash')}</MenuItem>
                <MenuItem value="installments">{t('procurement.installments')}</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          {normalizedPaymentTerms.type === 'cash' && (
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label={t('procurement.cashDiscountPercentage')}
                value={normalizedPaymentTerms.discount_percent || 0}
                onChange={(e) =>
                  setPaymentTerms({
                    type: 'cash',
                    discount_percent: Number(e.target.value || 0),
                  })
                }
                inputProps={{ min: 0, max: 100, step: 0.01 }}
              />
            </Grid>
          )}
          {normalizedPaymentTerms.type === 'installments' && (
            <Grid item xs={12}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                {t('procurement.installmentSchedule')}
              </Typography>
              {installmentSchedule.map((row, index) => (
                <Grid container spacing={1} alignItems="center" sx={{ mb: 1 }} key={`installment-${index}`}>
                  <Grid item xs={12} sm={5}>
                    <TextField
                      fullWidth
                      type="number"
                      size="small"
                      label={t('procurement.daysAfterPurchase')}
                      value={row.due_offset}
                      onChange={(e) =>
                        updateInstallmentAt(index, {
                          due_offset: Math.max(0, Number(e.target.value || 0)),
                        })
                      }
                      inputProps={{ min: 0, step: 1 }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={5}>
                    <TextField
                      fullWidth
                      type="number"
                      size="small"
                      label={t('procurement.percentage')}
                      value={row.percent}
                      onChange={(e) =>
                        updateInstallmentAt(index, {
                          percent: Number(e.target.value || 0),
                        })
                      }
                      inputProps={{ min: 0, max: 100, step: 0.01 }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={2}>
                    <IconButton
                      color="error"
                      onClick={() => removeInstallmentAt(index)}
                      disabled={installmentSchedule.length <= 1}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Grid>
                </Grid>
              ))}
              <Button size="small" startIcon={<AddIcon />} onClick={addInstallment}>
                {t('procurement.addInstallment')}
              </Button>
              <Typography
                variant="caption"
                sx={{ display: 'block', mt: 1 }}
                color={Math.abs(installmentTotalPercent - 100) <= 0.01 ? 'success.main' : 'error.main'}
              >
                {t('procurement.percentage')}: {installmentTotalPercent.toFixed(2)}%
              </Typography>
              <Alert severity="info" sx={{ mt: 1 }}>
                {t('procurement.installmentScheduleUsesSinglePlannedPaymentDate')}
              </Alert>
            </Grid>
          )}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>{t('procurement.paymentMethod')}</InputLabel>
              <Select
                value={data.payment_method_id || ''}
                label={t('procurement.paymentMethod')}
                onChange={(e) => onChange({ payment_method_id: Number(e.target.value) || null })}
                disabled={loadingFinancialData || paymentMethods.length === 0}
              >
                {paymentMethods.map((paymentMethod) => (
                  <MenuItem key={paymentMethod.id} value={paymentMethod.id}>
                    {isFa ? paymentMethod.name_fa : paymentMethod.name_en}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {paymentMethods.length === 0 ? (
              <Alert severity="warning" sx={{ mt: 1 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {t('procurement.noActivePaymentMethodsMasterData')}
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  href="/items-master#payment-methods-master-data"
                >
                  {t('navigation.baseInformation')}
                </Button>
              </Alert>
            ) : (
              <Typography variant="caption" color="text.secondary">
                {selectedPaymentMethod
                  ? `${t('procurement.settlementDelay')}: ${selectedPaymentMethod.settlement_delay_days} ${t('procurement.days')}`
                  : t('procurement.selectPaymentMethodToSeeDelay')}
              </Typography>
            )}
          </Grid>
          <Grid item xs={12} sm={6}>
            <LocalizedDateProvider>
              <DatePicker
                label={t('procurement.plannedSupplierPaymentDate')}
                value={toDatePickerValue(data.payment_date)}
                onChange={(newValue) => onChange({ payment_date: toIsoDate(newValue) })}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </LocalizedDateProvider>
            </Grid>
            <Grid item xs={12}>
            <Alert severity="info">
              <Typography variant="body2" component="span" fontWeight={600}>
                {t('procurement.supplierEffectiveReceiptDate')}: {' '}
              </Typography>
              <Typography variant="body2" component="span">
                {supplierEffectiveReceiptDate
                  ? formatDisplayDate(supplierEffectiveReceiptDate)
                  : t('procurement.notAvailableYet')}
              </Typography>
            </Alert>
            </Grid>
          <Grid item xs={12}>
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
                    ✅ {t('procurement.markAsFinalized')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
                    {t('procurement.onlyFinalizedOptions')}
            </Typography>
          </Box>
        }
      />
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

