import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { PackageWizardStep3 } from './PackageWizardStep3.tsx';
import { validateCostComponentDraft } from './costComponentValidation.ts';

let mockedLanguage = 'en';

const enDictionary: Record<string, string> = {
  'procurement.pricingAndCosts': 'Pricing and Costs',
  'procurement.delivery': 'Delivery',
  'procurement.payment': 'Payment',
  'procurement.paymentMethod': 'Payment Method',
  'procurement.paymentDate': 'Payment Date',
  'procurement.supplierEffectiveReceiptDate': 'Supplier Effective Receipt Date',
  'procurement.projectRequestedDeliveryDate': 'Project Requested Delivery Date',
  'procurement.supplierActualAvailableDeliveryDate': 'Supplier Actual Available Delivery Date',
  'procurement.selectedDeliveryDate': 'Selected Delivery Date',
  'procurement.deliveryVariance': 'Delivery Variance',
  'procurement.deliveryVarianceUnavailable': 'Variance unavailable',
  'procurement.early': 'Early',
  'procurement.onTime': 'On Time',
  'procurement.delayed': 'Delayed',
  'procurement.days': 'days',
  'procurement.supplierDeliveryNotes': 'Supplier Delivery Notes',
  'procurement.costComponents': 'Cost Components',
  'procurement.addCostComponent': 'Add Cost Component',
  'procurement.noCostComponents': 'No cost components added yet',
  'procurement.componentType': 'Component Type',
  'procurement.amount': 'Amount',
  'procurement.currency': 'Currency',
  'procurement.description': 'Description',
  'procurement.basePrice': 'Base Price',
  'procurement.shipping': 'Shipping',
  'procurement.vat': 'VAT',
  'procurement.customs': 'Customs',
  'procurement.clearance': 'Clearance',
  'procurement.insurance': 'Insurance',
  'procurement.bankFee': 'Bank Fee',
  'procurement.other': 'Other',
  'procurement.basePriceRequired': 'Base Price component is required.',
  'procurement.totalsByCurrency': 'Totals by Currency',
  'procurement.landedCostPreview': 'Landed Cost Preview',
  'procurement.previewAvailableAfterSaving': 'Preview available after saving.',
  'procurement.totalIrr': 'Total IRR',
  'procurement.unavailableDueToMissingExchangeRates': 'Unavailable due to missing exchange rates',
  'procurement.refresh': 'Refresh',
  'procurement.loading': 'Loading...',
  'procurement.missingExchangeRates': 'Missing Exchange Rates',
  'procurement.calculationTrace': 'Calculation Trace',
  'procurement.noActivePaymentMethodsMasterData':
    'No active payment methods exist. Define payment methods in Master Data first.',
  'procurement.selectPaymentMethodToSeeDelay': 'Select a payment method to see settlement delay',
  'procurement.settlementDelay': 'Settlement Delay',
  'procurement.notAvailableYet': 'Not available yet',
  'procurement.markAsFinalized': 'Mark as Finalized',
  'procurement.onlyFinalizedOptions': 'Only finalized options are used in optimization',
  'navigation.baseInformation': 'Base Information',
  'common.select': 'Select',
  'procurement.costComponentValidation.otherDescriptionRequired':
    'Description is required when component type is Other',
  'procurement.costComponentValidation.currencyRequired': 'Currency is required',
};

const faDictionary: Record<string, string> = {
  ...enDictionary,
  'procurement.pricingAndCosts': 'قیمت‌گذاری و هزینه‌ها',
  'procurement.delivery': 'اطلاعات تحویل',
  'procurement.payment': 'پرداخت',
  'procurement.projectRequestedDeliveryDate': 'تاریخ درخواستی تحویل پروژه',
  'procurement.supplierActualAvailableDeliveryDate': 'تاریخ واقعی قابل تحویل تأمین‌کننده',
  'procurement.supplierEffectiveReceiptDate': 'تاریخ مؤثر دریافت تأمین‌کننده',
  'procurement.paymentDate': 'تاریخ پرداخت',
  'procurement.noActivePaymentMethodsMasterData':
    'هیچ روش پرداخت فعالی وجود ندارد. ابتدا روش‌های پرداخت را در اطلاعات پایه تعریف کنید.',
  'procurement.basePriceRequired': 'مولفه قیمت پایه الزامی است.',
  'procurement.costComponents': 'مولفه‌های هزینه',
  'procurement.costComponentValidation.otherDescriptionRequired':
    'برای نوع «سایر» توضیحات الزامی است',
  'procurement.costComponentValidation.currencyRequired': 'ارز الزامی است',
  'navigation.baseInformation': 'اطلاعات پایه',
};

const translate = (key: string): string =>
  (mockedLanguage.startsWith('fa') ? faDictionary : enDictionary)[key] || key;

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => translate(key),
    i18n: { language: mockedLanguage },
  }),
}));

const mockListPaymentMethods = jest.fn().mockResolvedValue({ data: [] });
const mockListDeliveryOptions = jest.fn().mockResolvedValue({ data: [] });
const mockListCurrencies = jest.fn().mockResolvedValue({
  data: [{ id: 1, code: 'IRR', is_active: true }],
});
const mockListCostComponents = jest.fn().mockResolvedValue({ data: [] });
const mockGetLandedCostPreview = jest.fn().mockResolvedValue({ data: null });
const mockGetDeliveryFinancialPreview = jest.fn().mockResolvedValue({
  data: {
    project_requested_delivery_date: '2026-06-30',
    supplier_actual_delivery_date: null,
    selected_delivery_date: '2026-06-30',
    delivery_date_source: 'PROJECT_OPTION',
    delivery_date_variance_days: null,
    forecast_customer_invoice_date: '2026-07-18',
    forecast_customer_invoice_date_source: 'SYSTEM_DEFAULT',
    forecast_customer_receipt_date: '2026-08-17',
    forecast_customer_receipt_date_source: 'SYSTEM_DEFAULT',
    forecast_customer_receipt_delay_days: 30,
    missing_inputs: [],
    trace_lines: [],
  },
});

jest.mock('../../services/api.ts', () => ({
  deliveryOptionsAPI: {
    listByItem: (...args: unknown[]) => mockListDeliveryOptions(...args),
  },
  currencyAPI: {
    list: (...args: unknown[]) => mockListCurrencies(...args),
  },
  procurementFinancialsAPI: {
    listPaymentMethods: (...args: unknown[]) => mockListPaymentMethods(...args),
    listCostComponents: (...args: unknown[]) => mockListCostComponents(...args),
    getLandedCostPreview: (...args: unknown[]) => mockGetLandedCostPreview(...args),
    getDeliveryFinancialPreview: (...args: unknown[]) => mockGetDeliveryFinancialPreview(...args),
  },
}));

const buildData = (overrides: Partial<any> = {}) => ({
  option_id: null,
  base_cost: 0,
  currency_id: 1,
  shipping_cost: 0,
  delivery_option_id: null,
  lomc_lead_time: 0,
  purchase_date: '2026-06-22',
  expected_delivery_date: '',
  payment_terms: { type: 'cash', discount_percent: 0 },
  discount_bundle_threshold: undefined,
  discount_bundle_percent: undefined,
  is_finalized: false,
  main_item_quantity: 1,
  payment_method_id: null,
  payment_date: '2026-06-22',
  description: '',
  cost_components: [],
  project_requested_delivery_date: '',
  supplier_actual_delivery_date: '',
  selected_delivery_date: '',
  delivery_date_source: 'PROJECT_OPTION',
  delivery_date_variance_days: null,
  forecast_customer_invoice_date: '',
  forecast_customer_invoice_date_source: 'SYSTEM_DEFAULT',
  forecast_customer_receipt_date: '',
  forecast_customer_receipt_date_source: 'SYSTEM_DEFAULT',
  forecast_customer_receipt_delay_days: null,
  date_calculation_trace: [],
  ...overrides,
});

describe('PackageWizardStep3', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    mockedLanguage = 'en';
    container = document.createElement('div');
    document.body.appendChild(container);
    mockListPaymentMethods.mockReset();
    mockListDeliveryOptions.mockReset();
    mockListCurrencies.mockReset();
    mockListCostComponents.mockReset();
    mockGetLandedCostPreview.mockReset();
    mockGetDeliveryFinancialPreview.mockReset();

    mockListPaymentMethods.mockResolvedValue({ data: [] });
    mockListDeliveryOptions.mockResolvedValue({ data: [] });
    mockListCurrencies.mockResolvedValue({ data: [{ id: 1, code: 'IRR', is_active: true }] });
    mockListCostComponents.mockResolvedValue({ data: [] });
    mockGetLandedCostPreview.mockResolvedValue({ data: null });
    mockGetDeliveryFinancialPreview.mockResolvedValue({
      data: {
        project_requested_delivery_date: '2026-06-30',
        supplier_actual_delivery_date: null,
        selected_delivery_date: '2026-06-30',
        delivery_date_source: 'PROJECT_OPTION',
        delivery_date_variance_days: null,
        forecast_customer_invoice_date: '2026-07-18',
        forecast_customer_invoice_date_source: 'SYSTEM_DEFAULT',
        forecast_customer_receipt_date: '2026-08-17',
        forecast_customer_receipt_date_source: 'SYSTEM_DEFAULT',
        forecast_customer_receipt_delay_days: 30,
        missing_inputs: [],
        trace_lines: [],
      },
    });
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
  });

  it('renders exactly three core sections and cost components primary UI', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<PackageWizardStep3 data={buildData()} projectItemId={1} onChange={() => {}} />);
    });

    const text = container.textContent || '';
    expect(text).toContain('Pricing and Costs');
    expect(text).toContain('Delivery');
    expect(text).toContain('Payment');
    expect(text).toContain('Cost Components');
    expect(text).toContain('Preview available after saving.');
  });

  it('does not render invoice/receipt override controls and duplicate old pricing fields', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<PackageWizardStep3 data={buildData()} projectItemId={1} onChange={() => {}} />);
    });

    const text = container.textContent || '';
    expect(text).not.toContain('Override Invoice Date');
    expect(text).not.toContain('Override Receipt Date');
    expect(text).not.toContain('Customer Invoice Date');
    expect(text).not.toContain('Customer Receipt Date');
    expect(text).not.toContain('Base Cost');
    expect(text).not.toContain('Shipping Cost');
    expect(text).toContain('Base Price component is required.');
  });

  it('loads and displays active payment methods', async () => {
    mockListPaymentMethods.mockResolvedValueOnce({
      data: [
        {
          id: 7,
          code: 'LC30',
          name_en: 'LC 30 Days',
          name_fa: 'اعتبار اسنادی ۳۰ روزه',
          settlement_delay_days: 30,
          is_active: true,
        },
      ],
    });

    await act(async () => {
      root = createRoot(container);
      root.render(<PackageWizardStep3 data={buildData()} projectItemId={1} onChange={() => {}} />);
    });

    expect(mockListPaymentMethods).toHaveBeenCalled();
    expect(container.textContent).toContain('Payment Method');
    expect(container.textContent).not.toContain(
      'No active payment methods exist. Define payment methods in Master Data first.'
    );
  });

  it('shows master data guidance when no active payment methods exist', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<PackageWizardStep3 data={buildData()} projectItemId={1} onChange={() => {}} />);
    });

    const text = container.textContent || '';
    expect(text).toContain(
      'No active payment methods exist. Define payment methods in Master Data first.'
    );
    expect(text).toContain('Base Information');
  });

  it('does not call landed cost preview in create flow and shows save-first guidance', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<PackageWizardStep3 data={buildData({ option_id: null })} projectItemId={1} onChange={() => {}} />);
    });

    expect(mockGetLandedCostPreview).not.toHaveBeenCalled();
    expect(container.textContent).toContain('Preview available after saving.');
  });

  it('loads landed cost preview in edit flow and renders totals, missing rates, and trace lines', async () => {
    mockGetLandedCostPreview.mockResolvedValueOnce({
      data: {
        option_id: 42,
        totals_by_currency: { USD: 1500, EUR: 300 },
        total_irr: 56000000,
        missing_exchange_rates: [{ currency: 'EUR', exchange_rate_date: '2026-06-22' }],
        trace_lines: ['Converted BASE_PRICE USD to IRR', 'Missing EUR exchange rate'],
      },
    });

    await act(async () => {
      root = createRoot(container);
      root.render(<PackageWizardStep3 data={buildData({ option_id: 42 })} projectItemId={1} onChange={() => {}} />);
    });

    expect(mockGetLandedCostPreview).toHaveBeenCalledWith(42);
    const text = container.textContent || '';
    expect(text).toContain('USD: 1,500');
    expect(text).toContain('EUR: 300');
    expect(text).toContain('Missing Exchange Rates');
    expect(text).toContain('Calculation Trace');
  });

  it('validates OTHER component requires description', () => {
    expect(
      validateCostComponentDraft({
        component_type: 'OTHER',
        amount_value: 1200,
        amount_currency: 'IRR',
        description: '',
      })
    ).toBe('otherDescriptionRequired');
  });

  it('uses Persian labels without english fallback', async () => {
    mockedLanguage = 'fa';
    await act(async () => {
      root = createRoot(container);
      root.render(
        <PackageWizardStep3
          data={buildData({
            cost_components: [
              {
                component_type: 'OTHER',
                amount_value: 100,
                amount_currency: 'IRR',
                description: '',
              },
            ],
          })}
          projectItemId={1}
          onChange={() => {}}
        />
      );
    });

    const text = container.textContent || '';
    expect(text).toContain('قیمت‌گذاری و هزینه‌ها');
    expect(text).toContain('اطلاعات تحویل');
    expect(text).toContain('تاریخ واقعی قابل تحویل تأمین‌کننده');
    expect(text).toContain('تاریخ پرداخت');
    expect(text).toContain('تاریخ مؤثر دریافت تأمین‌کننده');
    expect(text).toContain('برای نوع «سایر» توضیحات الزامی است');
    expect(text).not.toContain('Pricing and Costs');
  });

  it('shows Persian currency-required validation without English fallback', async () => {
    mockedLanguage = 'fa';
    await act(async () => {
      root = createRoot(container);
      root.render(
        <PackageWizardStep3
          data={buildData({
            cost_components: [
              {
                component_type: 'BASE_PRICE',
                amount_value: 10,
                amount_currency: '',
                description: '',
              },
            ],
          })}
          projectItemId={1}
          onChange={() => {}}
        />
      );
    });

    const text = container.textContent || '';
    expect(text).toContain('ارز الزامی است');
    expect(text).not.toContain('Currency is required');
  });
});
