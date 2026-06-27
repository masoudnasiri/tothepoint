import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { PaymentMethodsPage } from './PaymentMethodsPage.tsx';

jest.mock('../components/finance/PaymentMethodsManager.tsx', () => () => (
  <div data-testid="payment-methods-manager">PaymentMethodsManagerMock</div>
));

jest.mock('../components/ui/RivarPageHeader.tsx', () => ({
  RivarPageHeader: ({ title }: { title: string }) => <div>{title}</div>,
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) =>
      (
        {
          'procurement.paymentMethods': 'Payment Methods',
          'procurement.definePaymentMethodsInMasterDataFirst':
            'Define payment methods in Master Data first.',
        } as Record<string, string>
      )[key] || key,
  }),
}));

describe('PaymentMethodsPage', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
  });

  it('renders payment methods page shell and manager section', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<PaymentMethodsPage />);
    });

    expect(container.querySelector('[data-testid="payment-methods-page"]')).toBeTruthy();
    expect(container.textContent).toContain('Payment Methods');
    expect(container.textContent).toContain('Define payment methods in Master Data first.');
    expect(container.querySelector('[data-testid="payment-methods-manager"]')).toBeTruthy();
  });
});
