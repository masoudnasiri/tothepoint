import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { PackageWizard } from './PackageWizard.tsx';

let mockedLanguage = 'en';

const enTranslations: Record<string, string> = {
  'common.next': 'Next',
  'common.back': 'Back',
  'common.update': 'Update',
  'common.cancel': 'Cancel',
  'procurement.stepMetadata': 'Metadata',
  'procurement.stepQuantities': 'Quantities',
  'procurement.stepPricing': 'Pricing & Delivery',
  'procurement.costComponentValidation.amountRequired': 'Amount is required',
  'procurement.costComponentValidation.amountPositive': 'Amount must be greater than zero',
  'procurement.costComponentValidation.currencyRequired': 'Currency is required',
  'procurement.costComponentValidation.typeRequired': 'Component type is required',
  'procurement.costComponentValidation.otherDescriptionRequired':
    'Description is required when component type is Other',
  'procurement.costComponentValidation.invalidRows':
    'Cost component validation failed in row(s): {{rows}}. {{message}}',
  'procurement.costComponentSaveFailed': 'Failed to save cost components.',
  'procurement.costComponentPartialSaveWarning':
    'Procurement option was saved, but cost components failed to save.',
  'procurement.basePriceRequired': 'Base Price component is required.',
  'procurement.singleBasePriceOnly': 'Only one Base Price component is allowed.',
  'procurement.singleShippingOnly': 'Only one Shipping component is allowed.',
  'procurement.installmentScheduleRequired': 'At least one installment schedule row is required.',
  'procurement.installmentScheduleTotalMustBe100':
    'Installment schedule percentages must total 100%.',
  'procurement.failedToCreatePackage': 'Failed to create package',
};

const faTranslations: Record<string, string> = {
  ...enTranslations,
  'procurement.costComponentValidation.currencyRequired': 'ارز الزامی است',
  'procurement.costComponentValidation.invalidRows':
    'اعتبارسنجی مولفه هزینه در ردیف(های) {{rows}} ناموفق بود. {{message}}',
};

const t = (key: string, options?: Record<string, unknown>) => {
  const dict = mockedLanguage.startsWith('fa') ? faTranslations : enTranslations;
  let value = dict[key] || key;
  if (options) {
    Object.entries(options).forEach(([optionKey, optionValue]) => {
      value = value.replace(`{{${optionKey}}}`, String(optionValue));
    });
  }
  return value;
};

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ t }),
}));

jest.mock('./PackageWizardStep1.tsx', () => ({
  PackageWizardStep1: () => <div>Step 1</div>,
}));

jest.mock('./PackageWizardStep2.tsx', () => ({
  PackageWizardStep2: () => <div>Step 2</div>,
}));

jest.mock('./PackageWizardStep3.tsx', () => ({
  PackageWizardStep3: () => <div>Step 3</div>,
}));

const mockPackagesListByProjectItem = jest.fn().mockResolvedValue({ data: [] });
const mockPackagesUpdate = jest.fn().mockResolvedValue({ data: { id: 99 } });
const mockPackagesCreate = jest.fn().mockResolvedValue({ data: { id: 99 } });
const mockPackagesGet = jest.fn().mockResolvedValue({ data: { subitems: [] } });
const mockPackagesDeleteSubItem = jest.fn().mockResolvedValue({});
const mockPackagesCreateSubItem = jest.fn().mockResolvedValue({});

const mockSupplierGet = jest.fn().mockResolvedValue({ data: { company_name: 'Supplier 1' } });

const mockProcurementListByProjectItem = jest.fn().mockResolvedValue({
  data: [{ id: 10, package_id: 99 }],
});
const mockProcurementCreate = jest.fn().mockResolvedValue({ data: { id: 10 } });
const mockProcurementUpdate = jest.fn().mockResolvedValue({ data: { id: 10 } });

const mockListCostComponents = jest.fn().mockResolvedValue({ data: [] });
const mockCreateCostComponent = jest.fn().mockResolvedValue({ data: { id: 1 } });
const mockUpdateCostComponent = jest.fn().mockResolvedValue({ data: { id: 1 } });
const mockDeactivateCostComponent = jest.fn().mockResolvedValue({});

jest.mock('../../services/api.ts', () => ({
  packagesAPI: {
    listByProjectItem: (...args: unknown[]) => mockPackagesListByProjectItem(...args),
    update: (...args: unknown[]) => mockPackagesUpdate(...args),
    create: (...args: unknown[]) => mockPackagesCreate(...args),
    get: (...args: unknown[]) => mockPackagesGet(...args),
    deleteSubItem: (...args: unknown[]) => mockPackagesDeleteSubItem(...args),
    createSubItem: (...args: unknown[]) => mockPackagesCreateSubItem(...args),
  },
  suppliersAPI: {
    get: (...args: unknown[]) => mockSupplierGet(...args),
  },
  procurementAPI: {
    listByProjectItem: (...args: unknown[]) => mockProcurementListByProjectItem(...args),
    create: (...args: unknown[]) => mockProcurementCreate(...args),
    update: (...args: unknown[]) => mockProcurementUpdate(...args),
  },
  procurementFinancialsAPI: {
    listCostComponents: (...args: unknown[]) => mockListCostComponents(...args),
    createCostComponent: (...args: unknown[]) => mockCreateCostComponent(...args),
    updateCostComponent: (...args: unknown[]) => mockUpdateCostComponent(...args),
    deactivateCostComponent: (...args: unknown[]) => mockDeactivateCostComponent(...args),
  },
}));

const clickButton = async (label: string) => {
  const button = Array.from(document.querySelectorAll('button')).find((candidate) =>
    candidate.textContent?.includes(label)
  );
  expect(button).toBeTruthy();
  await act(async () => {
    button!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
};

const flush = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};

const buildInitialData = (costComponents: any[], overrides: Record<string, any> = {}) => ({
  package_name: 'PKG-01',
  supplier_id: 1,
  package_type: 'FULL',
  description: 'Package',
  main_item_quantity: 1,
  subitem_quantities: {},
  base_cost: 1200,
  currency_id: 1,
  shipping_cost: 0,
  delivery_option_id: null,
  lomc_lead_time: 0,
  purchase_date: '2026-06-22',
  expected_delivery_date: '2026-06-30',
  payment_terms: { type: 'cash', discount_percent: 0 },
  discount_bundle_threshold: undefined,
  discount_bundle_percent: undefined,
  is_finalized: false,
  option_id: 10,
  payment_method_id: 7,
  payment_date: '2026-06-22',
  planned_supplier_payment_date: '2026-06-22',
  cost_components: costComponents,
  ...overrides,
});

describe('PackageWizard save-boundary behavior', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    mockedLanguage = 'en';
    container = document.createElement('div');
    document.body.appendChild(container);

    mockPackagesListByProjectItem.mockReset();
    mockPackagesUpdate.mockReset();
    mockPackagesCreate.mockReset();
    mockPackagesGet.mockReset();
    mockPackagesDeleteSubItem.mockReset();
    mockPackagesCreateSubItem.mockReset();
    mockSupplierGet.mockReset();
    mockProcurementListByProjectItem.mockReset();
    mockProcurementCreate.mockReset();
    mockProcurementUpdate.mockReset();
    mockListCostComponents.mockReset();
    mockCreateCostComponent.mockReset();
    mockUpdateCostComponent.mockReset();
    mockDeactivateCostComponent.mockReset();

    mockPackagesListByProjectItem.mockResolvedValue({ data: [] });
    mockPackagesUpdate.mockResolvedValue({ data: { id: 99 } });
    mockPackagesCreate.mockResolvedValue({ data: { id: 99 } });
    mockPackagesGet.mockResolvedValue({ data: { subitems: [] } });
    mockPackagesDeleteSubItem.mockResolvedValue({});
    mockPackagesCreateSubItem.mockResolvedValue({});
    mockSupplierGet.mockResolvedValue({ data: { company_name: 'Supplier 1' } });
    mockProcurementListByProjectItem.mockResolvedValue({ data: [{ id: 10, package_id: 99 }] });
    mockProcurementCreate.mockResolvedValue({ data: { id: 10 } });
    mockProcurementUpdate.mockResolvedValue({ data: { id: 10 } });
    mockListCostComponents.mockResolvedValue({ data: [] });
    mockCreateCostComponent.mockResolvedValue({ data: { id: 1 } });
    mockUpdateCostComponent.mockResolvedValue({ data: { id: 1 } });
    mockDeactivateCostComponent.mockResolvedValue({});
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
  });

  it('blocks save and cost component API calls when validation fails', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(
        <PackageWizard
          open={true}
          onClose={() => {}}
          projectItemId={1}
          itemCode="ITM-1"
          mainItemRequiredQuantity={1}
          subItemRequirements={[]}
          existingPackages={[]}
          editingPackageId={99}
          initialData={buildInitialData([
            {
              component_type: 'OTHER',
              description: '',
              amount_value: '',
              amount_currency: 'IRR',
            },
          ])}
        />
      );
    });

    await clickButton('Next');
    await clickButton('Next');
    await clickButton('Update');
    await flush();

    expect(document.body.textContent).toContain('Cost component validation failed in row(s): 1');
    expect(mockPackagesUpdate).not.toHaveBeenCalled();
    expect(mockCreateCostComponent).not.toHaveBeenCalled();
    expect(mockUpdateCostComponent).not.toHaveBeenCalled();
  });

  it('shows partial-save warning and keeps wizard open when cost component persistence fails', async () => {
    const onClose = jest.fn();
    mockCreateCostComponent.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'create failed',
        },
      },
    });

    await act(async () => {
      root = createRoot(container);
      root.render(
        <PackageWizard
          open={true}
          onClose={onClose}
          projectItemId={1}
          itemCode="ITM-1"
          mainItemRequiredQuantity={1}
          subItemRequirements={[]}
          existingPackages={[]}
          editingPackageId={99}
          initialData={buildInitialData([
            {
              component_type: 'BASE_PRICE',
              description: '',
              amount_value: 1000,
              amount_currency: 'IRR',
            },
            {
              component_type: 'VAT',
              description: '',
              amount_value: 100,
              amount_currency: 'IRR',
            },
          ])}
        />
      );
    });

    await clickButton('Next');
    await clickButton('Next');
    await clickButton('Update');
    await flush();

    expect(mockPackagesUpdate).toHaveBeenCalled();
    expect(mockProcurementUpdate).toHaveBeenCalled();
    expect(mockCreateCostComponent).toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
    expect(document.body.textContent).toContain(
      'Procurement option was saved, but cost components failed to save.'
    );
    expect(document.body.textContent).not.toContain('Failed to create package');
  });

  it('derives compatibility cost fields and planned payment date in procurement save payload', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(
        <PackageWizard
          open={true}
          onClose={() => {}}
          projectItemId={1}
          itemCode="ITM-1"
          mainItemRequiredQuantity={1}
          subItemRequirements={[]}
          existingPackages={[]}
          editingPackageId={99}
          initialData={buildInitialData([
            {
              component_type: 'BASE_PRICE',
              description: '',
              amount_value: 1500,
              amount_currency: 'USD',
            },
            {
              component_type: 'SHIPPING',
              description: '',
              amount_value: 45,
              amount_currency: 'USD',
            },
          ])}
        />
      );
    });

    await clickButton('Next');
    await clickButton('Next');
    await clickButton('Update');
    await flush();

    expect(mockProcurementUpdate).toHaveBeenCalled();
    const payload = mockProcurementUpdate.mock.calls[0][1];
    expect(payload.base_cost).toBe(1500);
    expect(payload.shipping_cost).toBe(45);
    expect(payload.payment_method_id).toBe(7);
    expect(payload.planned_supplier_payment_date).toBe('2026-06-22');
  });

  it('persists installment payment terms and bundle discounts in procurement save payload', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(
        <PackageWizard
          open={true}
          onClose={() => {}}
          projectItemId={1}
          itemCode="ITM-1"
          mainItemRequiredQuantity={1}
          subItemRequirements={[]}
          existingPackages={[]}
          editingPackageId={99}
          initialData={buildInitialData(
            [
              {
                component_type: 'BASE_PRICE',
                description: '',
                amount_value: 1000,
                amount_currency: 'IRR',
              },
            ],
            {
              payment_terms: {
                type: 'installments',
                schedule: [
                  { due_offset: 0, percent: 60 },
                  { due_offset: 30, percent: 40 },
                ],
              },
              discount_bundle_threshold: 10,
              discount_bundle_percent: 5,
            }
          )}
        />
      );
    });

    await clickButton('Next');
    await clickButton('Next');
    await clickButton('Update');
    await flush();

    expect(mockProcurementUpdate).toHaveBeenCalled();
    const payload = mockProcurementUpdate.mock.calls[0][1];
    expect(payload.payment_terms).toEqual({
      type: 'installments',
      schedule: [
        { due_offset: 0, percent: 60 },
        { due_offset: 30, percent: 40 },
      ],
    });
    expect(payload.discount_bundle_threshold).toBe(10);
    expect(payload.discount_bundle_percent).toBe(5);
  });

  it('blocks save when amount is present but currency is missing', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(
        <PackageWizard
          open={true}
          onClose={() => {}}
          projectItemId={1}
          itemCode="ITM-1"
          mainItemRequiredQuantity={1}
          subItemRequirements={[]}
          existingPackages={[]}
          editingPackageId={99}
          initialData={buildInitialData([
            {
              component_type: 'BASE_PRICE',
              description: '',
              amount_value: 1000,
              amount_currency: '',
            },
          ])}
        />
      );
    });

    await clickButton('Next');
    await clickButton('Next');
    await clickButton('Update');
    await flush();

    expect(document.body.textContent).toContain('Currency is required');
    expect(mockPackagesUpdate).not.toHaveBeenCalled();
    expect(mockProcurementUpdate).not.toHaveBeenCalled();
    expect(mockCreateCostComponent).not.toHaveBeenCalled();
  });

  it('blocks save in Persian mode with no English fallback when currency is missing', async () => {
    mockedLanguage = 'fa';
    await act(async () => {
      root = createRoot(container);
      root.render(
        <PackageWizard
          open={true}
          onClose={() => {}}
          projectItemId={1}
          itemCode="ITM-1"
          mainItemRequiredQuantity={1}
          subItemRequirements={[]}
          existingPackages={[]}
          editingPackageId={99}
          initialData={buildInitialData([
            {
              component_type: 'BASE_PRICE',
              description: '',
              amount_value: 1000,
              amount_currency: '',
            },
          ])}
        />
      );
    });

    await clickButton('Next');
    await clickButton('Next');
    await clickButton('Update');
    await flush();

    const text = document.body.textContent || '';
    expect(text).toContain('اعتبارسنجی مولفه هزینه در ردیف(های) 1 ناموفق بود. ارز الزامی است');
    expect(text).not.toContain('Currency is required');
    expect(mockPackagesUpdate).not.toHaveBeenCalled();
    expect(mockProcurementUpdate).not.toHaveBeenCalled();
    expect(mockCreateCostComponent).not.toHaveBeenCalled();
    expect(mockUpdateCostComponent).not.toHaveBeenCalled();
    expect(document.body.textContent).toContain('Update');
  });
});

