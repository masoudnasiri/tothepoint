import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import { act } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from './LoginPage.tsx';

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => ({
    login: jest.fn(),
  }),
}));

describe('LoginPage smoke tests', () => {
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

  it('renders login form fields', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );
    });

    expect(container.textContent).toContain('Sign In');
    expect(container.textContent).toContain('Username');
    expect(container.textContent).toContain('Password');
  });
});
