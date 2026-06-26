import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { PaymentMethodsManager, validatePaymentMethodForm } from './PaymentMethodsManager.tsx';

jest.mock('../../contexts/AuthContext.tsx', () => ({
  useAuth: () => ({ user: { role: 'admin', username: 'qa_admin' } }),
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: () => '',
  }),
}));

const mockListPaymentMethods = jest.fn().mockResolvedValue({ data: [] });

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
    mockListPaymentMethods.mockClear();
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
  });

  it('renders payment methods section', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<PaymentMethodsManager />);
    });

    expect(document.body.textContent).toContain('Payment Methods');
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
