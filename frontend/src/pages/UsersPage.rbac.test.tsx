import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';

const mockListUsers = jest.fn();
const mockCreateUser = jest.fn();
const mockUpdateUser = jest.fn();
const mockListRoles = jest.fn();
const mockGetUserRoles = jest.fn();
const mockUpdateUserRoles = jest.fn();

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => ({
    user: {
      id: 1,
      role: 'admin',
      username: 'admin',
      permissions: [
        'users.view',
        'users.create',
        'users.edit',
        'access_control.roles.manage',
        'access_control.user_roles.edit',
      ],
    },
    loading: false,
  }),
}));

jest.mock('../services/api.ts', () => ({
  usersAPI: {
    list: (...args: unknown[]) => mockListUsers(...args),
    create: (...args: unknown[]) => mockCreateUser(...args),
    update: (...args: unknown[]) => mockUpdateUser(...args),
    delete: jest.fn(),
  },
  accessControlAPI: {
    listRoles: (...args: unknown[]) => mockListRoles(...args),
    getUserRoles: (...args: unknown[]) => mockGetUserRoles(...args),
    updateUserRoles: (...args: unknown[]) => mockUpdateUserRoles(...args),
  },
}));

jest.mock('../components/ui/RivarPageHeader.tsx', () => ({
  RivarPageHeader: ({
    title,
    actions,
  }: {
    title: string;
    actions?: React.ReactNode;
  }) => (
    <div>
      <h1>{title}</h1>
      {actions}
    </div>
  ),
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, opts?: { detail?: string }) => {
      const map: Record<string, string> = {
        'navigation.users': 'Users',
        'users.addUser': 'Add User',
        'users.createUser': 'Create User',
        'users.editUser': 'Edit User',
        'users.updateUser': 'Update User',
        'users.legacyBaseRole': 'Legacy/base role (compatibility)',
        'users.rbacRoles': 'RBAC roles',
        'users.rbacRolesAssignHint': 'Roles assigned after user creation if partial failure.',
        'users.rbacRolesAssignFailed': `User created but role assignment failed: ${opts?.detail || ''}`,
        'users.rbacRolesAssignFailedGeneric': 'User created but role assignment failed.',
        'users.username': 'Username',
        'users.password': 'Password',
        'users.passwordLeaveBlank': 'Password (leave blank)',
        'users.active': 'Active',
        'users.created': 'Created',
        'common.refresh': 'Refresh',
        'common.cancel': 'Cancel',
        'common.edit': 'Edit',
        'common.delete': 'Delete',
        'common.actions': 'Actions',
        'accessControl.saveUserRolesFailed': 'Failed to save user roles',
      };
      return map[key] || key;
    },
    i18n: { language: 'en' },
  }),
}));

import { UsersPage } from './UsersPage.tsx';

const sampleUsers = [
  {
    id: 10,
    username: 'pm_user',
    role: 'pm',
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
  },
];

const sampleRoles = [
  { id: 2, code: 'project_manager', display_name: 'Project Manager', is_active: true, is_system: true },
  { id: 99, code: 'qa_custom', display_name: 'QA Custom', is_active: true, is_system: false },
];

function pageText(): string {
  return document.body.textContent || '';
}

function findButton(text: string): HTMLButtonElement | undefined {
  return Array.from(document.querySelectorAll('button')).find((b) => b.textContent?.includes(text));
}

function findIconButton(title: string): HTMLButtonElement | undefined {
  return document.querySelector(`button[title="${title}"]`) as HTMLButtonElement | undefined;
}

describe('UsersPage RBAC role assignment', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    mockListUsers.mockResolvedValue({ data: sampleUsers });
    mockListRoles.mockResolvedValue({ data: sampleRoles });
    mockGetUserRoles.mockResolvedValue({ data: { user_id: 10, role_ids: [2] } });
    mockCreateUser.mockResolvedValue({
      data: { id: 50, username: 'new_user', role: 'pm', is_active: true, created_at: '2026-01-01' },
    });
    mockUpdateUser.mockResolvedValue({ data: sampleUsers[0] });
    mockUpdateUserRoles.mockResolvedValue({ data: { user_id: 10, role_ids: [2, 99] } });
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  const renderPage = async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<UsersPage />);
      await Promise.resolve();
      await Promise.resolve();
    });
  };

  const clickButton = async (text: string) => {
    await act(async () => {
      findButton(text)?.click();
      await Promise.resolve();
      await Promise.resolve();
    });
  };

  it('create dialog includes legacy/base role and RBAC role multi-select', async () => {
    await renderPage();
    await clickButton('Add User');

    expect(mockListRoles).toHaveBeenCalled();
    expect(pageText()).toContain('Legacy/base role (compatibility)');
    expect(pageText()).toContain('RBAC roles');
  });

  it('create user calls usersAPI.create and accessControlAPI.updateUserRoles when roles selected', async () => {
    mockUpdateUserRoles.mockResolvedValueOnce({ data: { user_id: 50, role_ids: [99] } });
    await renderPage();
    await clickButton('Add User');

    const selects = document.querySelectorAll('[role="combobox"]');
    const rbacSelect = selects[selects.length - 1] as HTMLElement;
    await act(async () => {
      rbacSelect.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
      await Promise.resolve();
    });
    const option = Array.from(document.querySelectorAll('[role="option"]')).find((el) =>
      el.textContent?.includes('QA Custom')
    );
    await act(async () => {
      option?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      await Promise.resolve();
    });

    await clickButton('Create User');
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockCreateUser).toHaveBeenCalled();
    expect(mockUpdateUserRoles).toHaveBeenCalledWith(50, { role_ids: [99] });
  });

  it('edit user loads current RBAC roles when opening edit dialog', async () => {
    await renderPage();
    await act(async () => {
      findIconButton('Edit')?.click();
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockListRoles).toHaveBeenCalled();
    expect(mockGetUserRoles).toHaveBeenCalledWith(10);
    expect(pageText()).toContain('Edit User');
    expect(pageText()).toContain('Legacy/base role (compatibility)');
    expect(pageText()).toContain('RBAC roles');
  });

  it('edit user updates RBAC roles via accessControlAPI.updateUserRoles', async () => {
    await renderPage();
    await act(async () => {
      findIconButton('Edit')?.click();
      await Promise.resolve();
      await Promise.resolve();
    });
    await clickButton('Update User');

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockUpdateUser).toHaveBeenCalledWith(10, expect.any(Object));
    expect(mockUpdateUserRoles).toHaveBeenCalledWith(10, { role_ids: [2] });
  });

  it('surfaces backend lockout error on edit role assignment failure', async () => {
    mockUpdateUserRoles.mockRejectedValueOnce({
      response: { data: { detail: 'Cannot remove the last access-control manager' } },
    });
    await renderPage();
    await act(async () => {
      findIconButton('Edit')?.click();
      await Promise.resolve();
      await Promise.resolve();
    });
    await clickButton('Update User');

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(pageText()).toContain('Cannot remove the last access-control manager');
  });

  it('surfaces warning when create succeeds but role assignment fails', async () => {
    mockUpdateUserRoles.mockRejectedValueOnce({
      response: { data: { detail: 'Role assignment rejected' } },
    });
    await renderPage();
    await clickButton('Add User');

    const selects = document.querySelectorAll('[role="combobox"]');
    const rbacSelect = selects[selects.length - 1] as HTMLElement;
    await act(async () => {
      rbacSelect.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
      await Promise.resolve();
    });
    const option = Array.from(document.querySelectorAll('[role="option"]')).find((el) =>
      el.textContent?.includes('QA Custom')
    );
    await act(async () => {
      option?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      await Promise.resolve();
    });

    await clickButton('Create User');

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockCreateUser).toHaveBeenCalled();
    expect(pageText()).toContain('Role assignment rejected');
  });
});
