import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import { act } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { ProjectItemsPage } from './ProjectItemsPage.tsx';

const mockNavigate = jest.fn();
const mockListByProject = jest.fn();
const mockFinalize = jest.fn();
const mockFinalizeAll = jest.fn();
const mockUnfinalize = jest.fn();
const mockItemsMasterList = jest.fn();

let mockedLanguage = 'en';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({ projectId: '1' }),
  useNavigate: () => mockNavigate,
}));

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => ({
    user: { role: 'pmo', username: 'qa_pmo' },
  }),
}));

jest.mock('../hooks/useFeatureFlags.tsx', () => ({
  useFeatureFlags: () => ({
    flags: {},
    isPackageMode: false,
  }),
}));

jest.mock('../components/DeliveryOptionsManager.tsx', () => ({
  DeliveryOptionsManager: () => <div>DeliveryOptionsManagerMock</div>,
}));

jest.mock('../components/ui/RivarPageHeader.tsx', () => ({
  RivarPageHeader: ({ title, actions }: { title: string; actions?: React.ReactNode }) => (
    <div>
      <div>{title}</div>
      {actions}
    </div>
  ),
}));

jest.mock('../services/api.ts', () => ({
  itemsAPI: {
    listByProject: (...args: unknown[]) => mockListByProject(...args),
    finalize: (...args: unknown[]) => mockFinalize(...args),
    finalizeAll: (...args: unknown[]) => mockFinalizeAll(...args),
    unfinalize: (...args: unknown[]) => mockUnfinalize(...args),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    get: jest.fn(),
    listProjectItemSubItems: jest.fn(),
  },
  itemsMasterAPI: {
    list: (...args: unknown[]) => mockItemsMasterList(...args),
    listSubItems: jest.fn().mockResolvedValue({ data: [] }),
    get: jest.fn(),
  },
  excelAPI: {
    exportItems: jest.fn(),
    importItems: jest.fn(),
    downloadItemsTemplate: jest.fn(),
  },
  deliveryOptionsAPI: {
    listByItem: jest.fn().mockResolvedValue({ data: [] }),
  },
  packagesAPI: {
    listByProjectItem: jest.fn().mockResolvedValue({ data: [] }),
  },
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => {
    const dictionaries: Record<string, Record<string, string>> = {
      en: {
        'projectItems.projectItems': 'Project Items',
        'projectItems.projectId': 'Project ID',
        'projectItems.downloadTemplate': 'Download Template',
        'projectItems.importItems': 'Import Items',
        'projectItems.exportItems': 'Export Items',
        'projectItems.addItem': 'Add Item',
        'projectItems.finalizeAllItems': 'Finalize All Items',
        'projectItems.itemCode': 'Item Code',
        'projectItems.itemName': 'Item Name',
        'projectItems.quantity': 'Quantity',
        'projectItems.deliveryOptions': 'Delivery Options',
        'projectItems.status': 'Status',
        'projectItems.externalPurchase': 'External Purchase',
        'projectItems.actions': 'Actions',
        'projectItems.total': 'Total',
        'projectItems.items': 'items',
        'projectItems.item': 'item',
        'projectItems.clearFilters': 'Clear Filters',
        'projectItems.search': 'Search',
        'projectItems.searchPlaceholder': 'Search',
        'projectItems.all': 'All',
        'projectItems.finalized': 'Finalized',
        'projectItems.yes': 'Yes',
        'projectItems.no': 'No',
        'projectItems.viewItemDetails': 'View Item Details',
        'projectItems.editItem': 'Edit Item',
        'projectItems.deleteItem': 'Delete Item',
        'projectItems.finalizeItem': 'Finalize Item',
        'projectItems.unfinalizeItem': 'Unfinalize Item',
        'projectItems.areYouSureFinalize': 'Are you sure finalize?',
        'projectItems.areYouSureFinalizeAll': 'Are you sure finalize all?',
        'projectItems.failedToLoadProjectItems': 'Failed to load project items',
        'projectItems.failedToLoadItemsCatalog': 'Failed to load items catalog',
        'projectItems.failedToFinalizeItem': 'Failed to finalize item',
        'projectItems.failedToFinalizeAllItems': 'Failed to finalize all items',
        'projectItems.procurementBlocked': 'Not ready for procurement',
        'projectItems.bulkFinalizeBlocked': 'Bulk finalize blocked',
        'projectItems.bulkFinalizeBlockedTitle': 'Bulk finalize blocked',
        'projectItems.bulkFinalizeBlockedDescription': 'Resolve blockers first',
        'projectItems.bulkFinalizeNoDetails': 'No details',
        'projectItems.close': 'Close',
        'projectItems.showing': 'Showing',
        'projectItems.of': 'of',
        'projectItems.perPage': 'Per Page',
        'projectItems.previous': 'Previous',
        'projectItems.next': 'Next',
        'projectItems.page': 'Page',
        'projectItems.eligibilityBlockers.NO_DELIVERY_OPTION': 'No delivery option is defined for this item.',
        'projectItems.eligibilityBlockers.MISSING_DELIVERY_PRICE': 'Customer delivery/sales price is missing.',
        'projectItems.eligibilityBlockers.MISSING_DELIVERY_DATE': 'Project/customer delivery date is missing.',
      },
      fa: {
        'projectItems.projectItems': 'اقلام پروژه',
        'projectItems.projectId': 'شناسه پروژه',
        'projectItems.downloadTemplate': 'دانلود قالب',
        'projectItems.importItems': 'وارد کردن اقلام',
        'projectItems.exportItems': 'خروجی اقلام',
        'projectItems.addItem': 'افزودن اقلام',
        'projectItems.finalizeAllItems': 'نهایی کردن همه اقلام',
        'projectItems.itemCode': 'کد اقلام',
        'projectItems.itemName': 'نام اقلام',
        'projectItems.quantity': 'تعداد',
        'projectItems.deliveryOptions': 'گزینه‌های تحویل',
        'projectItems.status': 'وضعیت',
        'projectItems.externalPurchase': 'خرید خارجی',
        'projectItems.actions': 'عملیات',
        'projectItems.total': 'کل',
        'projectItems.items': 'اقلام',
        'projectItems.item': 'قلم',
        'projectItems.clearFilters': 'پاک کردن فیلترها',
        'projectItems.search': 'جستجو',
        'projectItems.searchPlaceholder': 'جستجو',
        'projectItems.all': 'همه',
        'projectItems.finalized': 'نهایی شده',
        'projectItems.yes': 'بله',
        'projectItems.no': 'خیر',
        'projectItems.viewItemDetails': 'جزئیات',
        'projectItems.editItem': 'ویرایش',
        'projectItems.deleteItem': 'حذف',
        'projectItems.finalizeItem': 'نهایی کردن',
        'projectItems.unfinalizeItem': 'لغو نهایی‌سازی',
        'projectItems.areYouSureFinalize': 'آیا مطمئن هستید؟',
        'projectItems.areYouSureFinalizeAll': 'آیا مطمئن هستید؟',
        'projectItems.failedToLoadProjectItems': 'خطا در بارگذاری اقلام پروژه',
        'projectItems.failedToLoadItemsCatalog': 'خطا در بارگذاری کاتالوگ اقلام',
        'projectItems.failedToFinalizeItem': 'خطا در نهایی‌سازی قلم',
        'projectItems.failedToFinalizeAllItems': 'خطا در نهایی‌سازی گروهی',
        'projectItems.procurementBlocked': 'این قلم هنوز قابل ارسال به تأمین نیست',
        'projectItems.bulkFinalizeBlocked': 'ارسال گروهی مسدود شد',
        'projectItems.bulkFinalizeBlockedTitle': 'ارسال گروهی مسدود شد',
        'projectItems.bulkFinalizeBlockedDescription': 'ابتدا موانع را رفع کنید',
        'projectItems.bulkFinalizeNoDetails': 'جزئیاتی موجود نیست',
        'projectItems.close': 'بستن',
        'projectItems.showing': 'نمایش',
        'projectItems.of': 'از',
        'projectItems.perPage': 'در هر صفحه',
        'projectItems.previous': 'قبلی',
        'projectItems.next': 'بعدی',
        'projectItems.page': 'صفحه',
        'projectItems.eligibilityBlockers.NO_DELIVERY_OPTION': 'گزینه تحویل برای این قلم تعریف نشده است.',
        'projectItems.eligibilityBlockers.MISSING_DELIVERY_PRICE': 'قیمت فروش/تحویل مشتری مشخص نشده است.',
        'projectItems.eligibilityBlockers.MISSING_DELIVERY_DATE': 'تاریخ تحویل پروژه مشخص نشده است.',
      },
    };
    const dictionary = dictionaries[mockedLanguage] || dictionaries.en;
    return {
      t: (key: string) => dictionary[key] || key,
      i18n: { language: mockedLanguage },
    };
  },
}));

describe('ProjectItemsPage procurement eligibility guard', () => {
  let container: HTMLDivElement;
  let root: Root;

  const buildItem = (overrides: Record<string, unknown> = {}) => ({
    id: 11,
    project_id: 1,
    item_code: 'ITEM-11',
    item_name: 'Test Item',
    quantity: 2,
    delivery_options: ['2026-02-10'],
    status: 'PENDING',
    external_purchase: false,
    description: '',
    file_path: null,
    file_name: null,
    decision_date: null,
    procurement_date: null,
    payment_date: null,
    invoice_submission_date: null,
    expected_cash_in_date: null,
    actual_cash_in_date: null,
    is_finalized: false,
    finalized_by: null,
    finalized_at: null,
    created_at: '2026-01-01T00:00:00',
    updated_at: null,
    procurement_eligibility: {
      project_item_id: 11,
      is_eligible: true,
      blockers: [],
      warnings: [],
      messages: [],
      delivery_option_count: 1,
      valid_delivery_option_count: 1,
      has_delivery_schedule_dates: true,
      inspected_delivery_options: [],
    },
    ...overrides,
  });

  const flush = async () => {
    await act(async () => {
      await Promise.resolve();
    });
  };

  const renderPage = async (items: any[]) => {
    mockListByProject.mockResolvedValue({ data: { items, total: items.length } });
    mockItemsMasterList.mockResolvedValue({ data: [] });

    await act(async () => {
      root = createRoot(container);
      root.render(
        <MemoryRouter>
          <ProjectItemsPage />
        </MemoryRouter>
      );
    });
    await flush();
    await flush();
  };

  beforeEach(() => {
    mockedLanguage = 'en';
    container = document.createElement('div');
    document.body.appendChild(container);
    (window.confirm as any) = jest.fn(() => true);
    mockNavigate.mockReset();
    mockListByProject.mockReset();
    mockFinalize.mockReset();
    mockFinalizeAll.mockReset();
    mockUnfinalize.mockReset();
    mockItemsMasterList.mockReset();
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
  });

  it('disables finalize action when no delivery option exists', async () => {
    const item = buildItem({
      procurement_eligibility: {
        project_item_id: 11,
        is_eligible: false,
        blockers: [{ code: 'NO_DELIVERY_OPTION', message: 'No delivery option' }],
        warnings: [],
        messages: ['No delivery option'],
        delivery_option_count: 0,
        valid_delivery_option_count: 0,
        has_delivery_schedule_dates: false,
        inspected_delivery_options: [],
      },
    });
    await renderPage([item]);

    const finalizeButton = container.querySelector('button[title*="Not ready for procurement"]') as HTMLButtonElement;
    expect(finalizeButton).toBeTruthy();
    expect(finalizeButton.disabled).toBe(true);
    expect(container.textContent).toContain('No delivery option is defined for this item.');
  });

  it('shows missing delivery price reason', async () => {
    const item = buildItem({
      procurement_eligibility: {
        project_item_id: 11,
        is_eligible: false,
        blockers: [{ code: 'MISSING_DELIVERY_PRICE', message: 'Missing delivery price' }],
        warnings: [],
        messages: ['Missing delivery price'],
        delivery_option_count: 1,
        valid_delivery_option_count: 0,
        has_delivery_schedule_dates: true,
        inspected_delivery_options: [],
      },
    });
    await renderPage([item]);

    expect(container.textContent).toContain('Customer delivery/sales price is missing.');
  });

  it('shows missing delivery date reason', async () => {
    const item = buildItem({
      procurement_eligibility: {
        project_item_id: 11,
        is_eligible: false,
        blockers: [{ code: 'MISSING_DELIVERY_DATE', message: 'Missing delivery date' }],
        warnings: [],
        messages: ['Missing delivery date'],
        delivery_option_count: 1,
        valid_delivery_option_count: 0,
        has_delivery_schedule_dates: false,
        inspected_delivery_options: [],
      },
    });
    await renderPage([item]);

    expect(container.textContent).toContain('Project/customer delivery date is missing.');
  });

  it('allows finalize action for eligible item', async () => {
    const item = buildItem();
    mockFinalize.mockResolvedValue({ data: {} });
    await renderPage([item]);

    const finalizeButton = container.querySelector('button[title="Finalize Item"]') as HTMLButtonElement;
    expect(finalizeButton).toBeTruthy();
    expect(finalizeButton.disabled).toBe(false);

    await act(async () => {
      finalizeButton.click();
    });
    await flush();

    expect(mockFinalize).toHaveBeenCalledWith(11, { is_finalized: true });
  });

  it('shows backend eligibility errors from 422 response', async () => {
    const item = buildItem();
    mockFinalize.mockRejectedValue({
      response: {
        status: 422,
        data: {
          detail: {
            code: 'PROCUREMENT_ELIGIBILITY_FAILED',
            eligibility: {
              blockers: [{ code: 'MISSING_DELIVERY_PRICE', message: 'Missing delivery price' }],
              messages: ['Missing delivery price'],
            },
          },
        },
      },
    });

    await renderPage([item]);
    const finalizeButton = container.querySelector('button[title="Finalize Item"]') as HTMLButtonElement;
    await act(async () => {
      finalizeButton.click();
    });
    await flush();

    expect(container.textContent).toContain('Not ready for procurement');
    expect(container.textContent).toContain('Customer delivery/sales price is missing.');
  });

  it('renders Persian blockers without English fallback', async () => {
    mockedLanguage = 'fa';
    const item = buildItem({
      procurement_eligibility: {
        project_item_id: 11,
        is_eligible: false,
        blockers: [{ code: 'MISSING_DELIVERY_PRICE', message: 'Missing delivery price' }],
        warnings: [],
        messages: ['Missing delivery price'],
        delivery_option_count: 1,
        valid_delivery_option_count: 0,
        has_delivery_schedule_dates: true,
        inspected_delivery_options: [],
      },
    });
    await renderPage([item]);

    expect(container.textContent).toContain('قیمت فروش/تحویل مشتری مشخص نشده است.');
    expect(container.textContent).not.toContain('Customer delivery/sales price is missing.');
  });
});
