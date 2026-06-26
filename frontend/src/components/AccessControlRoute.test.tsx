import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { AccessControlRoute } from './AccessControlRoute.tsx';

const mockUseAuth = jest.fn();

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => mockUseAuth(),
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) =>
      ({
        'accessControl.accessDeniedTitle': 'Access denied',
        'accessControl.accessDeniedMessage': 'You do not have permission.',
      })[key] || key,
  }),
}));

describe('AccessControlRoute', () => {
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
    mockUseAuth.mockReset();
  });

  it('renders children for admin user', async () => {
    mockUseAuth.mockReturnValue({
      loading: false,
      user: { role: 'admin', username: 'admin', permissions: [] },
    });

    await act(async () => {
      root = createRoot(container);
      root.render(
        <AccessControlRoute>
          <div>Access Control Content</div>
        </AccessControlRoute>
      );
    });

    expect(container.textContent).toContain('Access Control Content');
  });

  it('shows access denied for unauthorized user', async () => {
    mockUseAuth.mockReturnValue({
      loading: false,
      user: {
        role: 'procurement',
        username: 'proc1',
        permissions: ['procurement.options.view'],
      },
    });

    await act(async () => {
      root = createRoot(container);
      root.render(
        <AccessControlRoute>
          <div>Access Control Content</div>
        </AccessControlRoute>
      );
    });

    expect(container.textContent).toContain('Access denied');
    expect(container.textContent).not.toContain('Access Control Content');
  });
});
