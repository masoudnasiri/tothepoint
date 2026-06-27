import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { Layout } from './Layout.tsx';

let mockedLanguage = 'en';

const mockUserHolder: {
  user: Record<string, unknown>;
  logout: jest.Mock;
} = {
  user: { role: 'admin', username: 'qa_admin' },
  logout: jest.fn(),
};

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => mockUserHolder,
}));

jest.mock('./LanguageSwitcher.tsx', () => ({
  LanguageSwitcher: () => <button aria-label="change language">Lang</button>,
}));

jest.mock('../utils/appIdentity.ts', () => ({
  BRAND_NAME: 'Rivar',
  PRODUCER_NAME: 'Corbit',
  PRODUCT_NAME: 'Rivar',
  getRuntimeVersion: async () => '1.0.0-rc1',
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) =>
      (
        mockedLanguage.startsWith('fa')
          ? {
              'navigation.dashboard': 'داشبورد',
              'navigation.insights': 'بینش‌ها',
              'navigation.projectAnalytics': 'تحلیل و پیش‌بینی پروژه',
              'navigation.reports': 'گزارش‌ها و تحلیل‌ها',
              'navigation.projects': 'پروژه‌ها',
              'navigation.procurement': 'تامین',
              'navigation.procurementPlan': 'برنامه تامین',
              'navigation.finance': 'مالی',
              'navigation.optimization': 'بهینه‌سازی پیشرفته',
              'navigation.decisions': 'تصمیمات نهایی',
              'navigation.users': 'کاربران',
              'navigation.auditLogs': 'پایش‌لاگ',
              'navigation.baseInformation': 'اطلاعات پایه',
              'navigation.weights': 'وزن‌های تصمیم',
              'navigation.itemsMaster': 'فهرست اقلام',
              'navigation.suppliers': 'تامین‌کنندگان',
              'navigation.paymentMethods': 'روش‌های پرداخت',
              'auth.logout': 'خروج',
            }
          : {
              'navigation.dashboard': 'Dashboard',
              'navigation.insights': 'Insights',
              'navigation.projectAnalytics': 'Project Analytics',
              'navigation.reports': 'Reports',
              'navigation.projects': 'Projects',
              'navigation.procurement': 'Procurement',
              'navigation.procurementPlan': 'Procurement Plan',
              'navigation.finance': 'Finance',
              'navigation.optimization': 'Optimization',
              'navigation.decisions': 'Decisions',
              'navigation.users': 'Users',
              'navigation.auditLogs': 'Audit Logs',
              'navigation.baseInformation': 'Base Information',
              'navigation.weights': 'Decision Weights',
              'navigation.itemsMaster': 'Items Master',
              'navigation.suppliers': 'Suppliers',
              'navigation.paymentMethods': 'Payment Methods',
              'auth.logout': 'Logout',
            }
      )[key] || key,
    i18n: { language: mockedLanguage },
  }),
}));

describe('Layout master data navigation', () => {
  let container: HTMLDivElement;
  let root: Root;

  const getBaseInformationButton = () =>
    Array.from(container.querySelectorAll('[role="button"]')).find((btn) =>
      btn.textContent?.includes('Base Information')
    );

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    mockUserHolder.user = { role: 'admin', username: 'qa_admin' };
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
  });

  it('shows Base Information entry for admin in English', async () => {
    mockedLanguage = 'en';
    await act(async () => {
      root = createRoot(container);
      root.render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );
    });

    expect(container.textContent).toContain('Base Information');
    const baseInfoButton = getBaseInformationButton();
    expect(baseInfoButton).toBeTruthy();
    await act(async () => {
      baseInfoButton!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(container.textContent).toContain('Payment Methods');
  });

  it('shows اطلاعات پایه entry in Persian', async () => {
    mockedLanguage = 'fa';
    await act(async () => {
      root = createRoot(container);
      root.render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );
    });

    expect(container.textContent).toContain('اطلاعات پایه');
  });

  it('hides Base Information for access-control-only RBAC user with legacy pm slot', async () => {
    mockedLanguage = 'en';
    mockUserHolder.user = {
      role: 'pm',
      username: 'testuser5',
      permissions: [
        'access_control.roles.view',
        'access_control.permissions.view',
        'access_control.user_roles.view',
        'users.view',
      ],
    };

    await act(async () => {
      root = createRoot(container);
      root.render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );
    });

    expect(container.textContent).not.toContain('Base Information');
    expect(container.textContent).not.toContain('Items Master');
    expect(container.textContent).not.toContain('Suppliers');
    expect(container.textContent).not.toContain('Payment Methods');
  });

  it('shows Payment Methods nav for explicit payment methods view permission', async () => {
    mockedLanguage = 'en';
    mockUserHolder.user = {
      role: 'pm',
      username: 'payment_view_only',
      permissions: ['master_data.payment_methods.view'],
    };

    await act(async () => {
      root = createRoot(container);
      root.render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );
    });

    expect(container.textContent).toContain('Base Information');
    const baseInfoButton = getBaseInformationButton();
    expect(baseInfoButton).toBeTruthy();
    await act(async () => {
      baseInfoButton!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(container.textContent).toContain('Payment Methods');
  });

  it('hides Payment Methods nav for procurement assignment view-only user', async () => {
    mockedLanguage = 'en';
    mockUserHolder.user = {
      role: 'procurement',
      username: 'assignment_view_only',
      permissions: ['procurement.assignments.view'],
    };

    await act(async () => {
      root = createRoot(container);
      root.render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <Layout>
            <div>Content</div>
          </Layout>
        </MemoryRouter>
      );
    });

    expect(container.textContent).not.toContain('Payment Methods');
  });
});
