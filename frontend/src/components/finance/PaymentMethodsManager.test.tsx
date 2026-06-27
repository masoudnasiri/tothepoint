import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { PaymentMethodsManager, validatePaymentMethodForm } from './PaymentMethodsManager.tsx';

const mockUserHolder: { user: Record<string, unknown> } = {
  user: { role: 'admin', username: 'qa_admin' },
};

jest.mock('../../contexts/AuthContext.tsx', () => ({
  useAuth: () => mockUserHolder,
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) =>
      (
        {
          'procurement.paymentMethods': 'Payment Methods',
          'procurement.addPaymentMethod': 'Add Payment Method',
          'procurement.editPaymentMethod': 'Edit payment method',
          'procurement.deactivatePaymentMethod': 'Deactivate payment method',
          'accessControl.featureAccessDenied': 'Access denied',
        } as Record<string, string>
      )[key] || '',
  }),
}));

const mockListPaymentMethods = jest.fn().mockResolvedValue({
  data: [
    {
      id: 1,
      code: 'NET30',
      name_en: 'Net 30',
      name_fa: 'نت 30',
      description: 'Default',
      settlement_delay_days: 30,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    },
  ],
});

jest.mock('../../services/api.ts', () => ({
  procurementFinancialsAPI: {
    listPaymentMethods: (...args: unknown[]) => mockListPaymentMethods(...args),
    createPaymentMethod: jest.fn(),
    updatePaymentMethod: jest.fn(),
    deactivatePaymentMethod: jest.fn(),
  },
}));

describe('PaymentMethodsManager', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    mockListPaymentMethods.mockReset();
    mockListPaymentMethods.mockResolvedValue({
      data: [
        {
          id: 1,
          code: 'NET30',
          name_en: 'Net 30',
          name_fa: 'نت 30',
          description: 'Default',
          settlement_delay_days: 30,
          is_active: true,
          created_at: '2026-01-01T00:00:00Z',
        },
      ],
    });
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

  it('renders full actions for admin', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<PaymentMethodsManager />);
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(container.textContent).toContain('Payment Methods');
    expect(container.textContent).toContain('NET30');
    expect(container.textContent).toContain('Add Payment Method');
    expect(container.querySelectorAll('button').length).toBeGreaterThanOrEqual(3);
  });

  it('hides create/edit/delete actions for view-only user', async () => {
    mockUserHolder.user = {
      role: 'pm',
      username: 'view_only',
      permissions: ['master_data.payment_methods.view'],
    };

    await act(async () => {
      root = createRoot(container);
      root.render(<PaymentMethodsManager />);
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(container.textContent).toContain('Payment Methods');
    expect(container.textContent).toContain('NET30');
    expect(container.textContent).not.toContain('Add Payment Method');
    expect(container.querySelectorAll('button').length).toBe(0);
  });

  it('gates edit and delete actions independently by permission', async () => {
    mockUserHolder.user = {
      role: 'pm',
      username: 'edit_only',
      permissions: [
        'master_data.payment_methods.view',
        'master_data.payment_methods.edit',
      ],
    };

    await act(async () => {
      root = createRoot(container);
      root.render(<PaymentMethodsManager />);
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(container.textContent).toContain('NET30');
    expect(container.textContent).not.toContain('Add Payment Method');
    expect(container.querySelectorAll('button').length).toBe(1);
  });

  it('validates settlement delay as non-negative', () => {
    const errors = validatePaymentMethodForm(
      {
        code: 'NET30',
        name_en: 'Net 30',
        name_fa: 'Net 30 FA',
        description: '',
        settlement_delay_days: '-1',
      },
      () => ''
    );

    expect(errors.settlement_delay_days).toContain('Settlement delay');
  });
});
