import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { PaymentMethodsRoute } from './PaymentMethodsRoute.tsx';

const mockUserHolder: {
  user: Record<string, unknown> | null;
  loading: boolean;
} = {
  user: { role: 'admin', username: 'qa_admin' },
  loading: false,
};

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => mockUserHolder,
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) =>
      (
        {
          'accessControl.featureAccessDenied': 'Access denied',
          'accessControl.sectionAccessDeniedMessage': 'You cannot access this section.',
        } as Record<string, string>
      )[key] || key,
  }),
}));

describe('PaymentMethodsRoute', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    mockUserHolder.loading = false;
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

  it('renders children for authorized user', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(
        <PaymentMethodsRoute>
          <div>Payment Methods Page</div>
        </PaymentMethodsRoute>
      );
    });

    expect(container.textContent).toContain('Payment Methods Page');
  });

  it('denies unauthorized user without payment methods view permission', async () => {
    mockUserHolder.user = {
      role: 'pm',
      username: 'ac_only',
      permissions: ['users.view'],
    };

    await act(async () => {
      root = createRoot(container);
      root.render(
        <PaymentMethodsRoute>
          <div>Hidden Content</div>
        </PaymentMethodsRoute>
      );
    });

    expect(container.textContent).toContain('Access denied');
    expect(container.textContent).not.toContain('Hidden Content');
  });
});
