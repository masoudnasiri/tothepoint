import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => ({
    user: { role: 'admin', permissions: ['access_control.user_roles.edit'] },
    loading: false,
  }),
}));

const mockListRoles = jest.fn();
const mockListPermissions = jest.fn();
const mockGetRolePermissions = jest.fn();
const mockGetRole = jest.fn();
const mockGetRoleAssignedUsers = jest.fn();
const mockDeactivateRole = jest.fn();
const mockListUsers = jest.fn();
const mockGetUserRoles = jest.fn();

jest.mock('../services/api.ts', () => ({
  accessControlAPI: {
    listRoles: (...args: unknown[]) => mockListRoles(...args),
    listPermissions: (...args: unknown[]) => mockListPermissions(...args),
    getRolePermissions: (...args: unknown[]) => mockGetRolePermissions(...args),
    getRole: (...args: unknown[]) => mockGetRole(...args),
    getRoleAssignedUsers: (...args: unknown[]) => mockGetRoleAssignedUsers(...args),
    createRole: jest.fn(),
    updateRole: jest.fn(),
    updateRolePermissions: jest.fn(),
    deactivateRole: (...args: unknown[]) => mockDeactivateRole(...args),
    getUserRoles: (...args: unknown[]) => mockGetUserRoles(...args),
    updateUserRoles: jest.fn(),
  },
  usersAPI: {
    list: (...args: unknown[]) => mockListUsers(...args),
  },
}));

jest.mock('../components/ui/RivarPageHeader.tsx', () => ({
  RivarPageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, opts?: { name?: string }) => {
      const map: Record<string, string> = {
        'accessControl.searchRoles': 'Search roles',
        'accessControl.createRole': 'Create role',
        'accessControl.roleName': 'Display name',
        'accessControl.roleCode': 'Role code',
        'accessControl.roleType': 'Type',
        'accessControl.status': 'Status',
        'accessControl.permissionCount': 'Permissions',
        'accessControl.assignedUsers': 'Assigned users',
        'accessControl.systemRole': 'System role',
        'accessControl.customRole': 'Custom role',
        'accessControl.active': 'Active',
        'accessControl.deactivateRole': 'Deactivate role',
        'accessControl.roleDetailsTab': 'Role details',
        'accessControl.permissionsTab': 'Permissions',
        'accessControl.assignedUsersTab': 'Assigned users',
        'accessControl.assignRolesToUser': 'Assign roles',
        'accessControl.selectUser': 'User',
        'accessControl.chooseUser': 'Choose user',
        'accessControl.roles': 'Roles',
        'common.refresh': 'Refresh',
        'common.edit': 'Edit',
        'common.actions': 'Actions',
        'common.cancel': 'Cancel',
        'common.close': 'Close',
      };
      if (key === 'accessControl.deactivateRoleConfirm' && opts?.name) {
        return `Deactivate ${opts.name}?`;
      }
      return map[key] || key;
    },
  }),
}));

import { AccessControlPage } from './AccessControlPage.tsx';

const sampleRoles = [
  {
    id: 1,
    code: 'system_admin',
    display_name: 'System Admin',
    description: null,
    is_system: true,
    is_active: true,
    created_at: '2026-01-01',
    user_count: 1,
    permission_count: 5,
  },
  {
    id: 99,
    code: 'qa_custom_role',
    display_name: 'QA Custom',
    description: 'test',
    is_system: false,
    is_active: true,
    created_at: '2026-01-01',
    user_count: 0,
    permission_count: 1,
  },
];

describe('AccessControlPage role management', () => {
  let container: HTMLDivElement;
  let root: Root;

  jest.setTimeout(20000);

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    mockListRoles.mockResolvedValue({ data: sampleRoles });
    mockListPermissions.mockResolvedValue({ data: [] });
    mockGetRolePermissions.mockResolvedValue({
      data: { role_id: 1, permission_keys: ['access_control.roles.manage'] },
    });
    mockGetRole.mockResolvedValue({ data: sampleRoles[0] });
    mockGetRoleAssignedUsers.mockResolvedValue({ data: [] });
    mockDeactivateRole.mockResolvedValue({ data: { message: 'ok' } });
    mockListUsers.mockResolvedValue({ data: [{ id: 2, username: 'proc1', role: 'procurement' }] });
    mockGetUserRoles.mockResolvedValue({ data: { user_id: 2, role_ids: [1], roles: [] } });
    window.confirm = jest.fn(() => true);
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

  const renderRolesPanel = async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<AccessControlPage embedded mode="roles" />);
    });
    for (let i = 0; i < 40; i += 1) {
      if (document.body.textContent?.includes('System Admin')) break;
      await new Promise((r) => setTimeout(r, 25));
    }
  };

  it('shows role list without always-visible editor drawer', async () => {
    await renderRolesPanel();
    expect(mockListRoles).toHaveBeenCalled();
    expect(document.body.textContent).toContain('System Admin');
    expect(document.body.textContent).toContain('QA Custom');
    expect(document.querySelector('.MuiDrawer-root')).toBeNull();
  });

  it('opens drawer editor when edit is clicked', async () => {
    await renderRolesPanel();
    const edit = document.querySelector('button[aria-label="Edit"]') as HTMLButtonElement;
    await act(async () => {
      edit?.click();
    });
    expect(document.querySelector('.MuiDrawer-root')).not.toBeNull();
    expect(document.body.textContent).toContain('Role details');
  });

  it('shows deactivate only for custom roles', async () => {
    await renderRolesPanel();
    expect(document.querySelectorAll('button[aria-label="Deactivate role"]').length).toBe(1);
  });
});
