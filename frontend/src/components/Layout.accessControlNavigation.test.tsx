import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { Layout } from './Layout.tsx';

const mockUseAuth = jest.fn();

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => mockUseAuth(),
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
      ({
        'navigation.dashboard': 'Dashboard',
        'navigation.users': 'Users',
        'navigation.accessControl': 'Access Control',
        'navigation.auditLogs': 'Audit Logs',
        'auth.logout': 'Logout',
      })[key] || key,
    i18n: { language: 'en' },
  }),
}));

describe('Layout access control navigation', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    mockUseAuth.mockReset();
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
  });

  it('shows Access Control menu item for admin', async () => {
    mockUseAuth.mockReturnValue({
      user: { role: 'admin', username: 'admin', permissions: ['access_control.roles.manage'] },
      logout: jest.fn(),
    });

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

    expect(container.textContent).toContain('Access Control');
  });

  it('hides Access Control menu item for procurement user', async () => {
    mockUseAuth.mockReturnValue({
      user: {
        role: 'procurement',
        username: 'proc1',
        permissions: ['procurement.options.view'],
      },
      logout: jest.fn(),
    });

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

    expect(container.textContent).not.toContain('Access Control');
    expect(container.textContent).not.toContain('Users');
  });
});
