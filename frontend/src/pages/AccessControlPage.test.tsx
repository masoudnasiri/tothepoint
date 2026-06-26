import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => ({
    user: { role: 'admin', permissions: ['access_control.user_roles.edit'] },
    loading: false,
  }),
}));

import { AccessControlPage } from './AccessControlPage.tsx';

const mockListRoles = jest.fn();
const mockListPermissions = jest.fn();
const mockGetRolePermissions = jest.fn();
const mockGetRole = jest.fn();
const mockCreateRole = jest.fn();
const mockUpdateRole = jest.fn();
const mockUpdateRolePermissions = jest.fn();
const mockListUsers = jest.fn();
const mockGetUserRoles = jest.fn();

jest.mock('../services/api.ts', () => ({
  accessControlAPI: {
    listRoles: (...args: unknown[]) => mockListRoles(...args),
    listPermissions: (...args: unknown[]) => mockListPermissions(...args),
    getRolePermissions: (...args: unknown[]) => mockGetRolePermissions(...args),
    getRole: (...args: unknown[]) => mockGetRole(...args),
    createRole: (...args: unknown[]) => mockCreateRole(...args),
    updateRole: (...args: unknown[]) => mockUpdateRole(...args),
    updateRolePermissions: (...args: unknown[]) => mockUpdateRolePermissions(...args),
    getUserRoles: (...args: unknown[]) => mockGetUserRoles(...args),
    updateUserRoles: jest.fn(),
    deactivateRole: jest.fn(),
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
        'accessControl.title': 'Access Control',
        'accessControl.subtitle': 'Manage roles',
        'accessControl.rolesTab': 'Roles & Permissions',
        'accessControl.userRolesTab': 'User Role Assignment',
        'accessControl.createRole': 'Create role',
        'accessControl.roleCode': 'Role code',
        'accessControl.roleName': 'Display name',
        'accessControl.roleType': 'Type',
        'accessControl.status': 'Status',
        'accessControl.permissionCount': 'Permissions',
        'accessControl.systemRole': 'System role',
        'accessControl.customRole': 'Custom role',
        'accessControl.active': 'Active',
        'accessControl.inactive': 'Inactive',
        'accessControl.permissionMatrix': 'Permission matrix',
        'accessControl.feature': 'Feature',
        'accessControl.action': 'Action',
        'accessControl.savePermissions': 'Save permissions',
        'accessControl.saveRole': 'Save role',
        'accessControl.systemAdminLocked': 'System admin locked',
        'accessControl.enforcementPilotNotice': 'Pilot enforcement notice',
        'permissionGroups.access_control': 'Access Control',
        'permissionFeatures.access_control_roles': 'Roles',
        'permissionActions.view': 'View',
        'permissionActions.manage': 'Manage',
        'common.refresh': 'Refresh',
        'common.create': 'Create',
        'common.cancel': 'Cancel',
      };
      if (key === 'accessControl.deactivateRoleConfirm' && opts?.name) {
        return `Deactivate ${opts.name}?`;
      }
      return map[key] || key;
    },
  }),
}));

const sampleRoles = [
  {
    id: 1,
    code: 'system_admin',
    display_name: 'System Admin',
    description: null,
    is_system: true,
    is_active: true,
    created_at: '2026-01-01',
  },
  {
    id: 99,
    code: 'qa_custom_role',
    display_name: 'QA Custom',
    description: 'test',
    is_system: false,
    is_active: true,
    created_at: '2026-01-01',
  },
];

const samplePermissions = [
  {
    id: 1,
    permission_key: 'access_control.roles.view',
    feature_key: 'access_control.roles',
    action: 'view',
    description: 'View roles',
    is_system: true,
    sort_order: 10,
  },
  {
    id: 2,
    permission_key: 'access_control.roles.manage',
    feature_key: 'access_control.roles',
    action: 'manage',
    description: 'Manage roles',
    is_system: true,
    sort_order: 14,
  },
];

describe('AccessControlPage', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    mockListRoles.mockResolvedValue({ data: sampleRoles });
    mockListPermissions.mockResolvedValue({ data: samplePermissions });
    mockGetRolePermissions.mockResolvedValue({
      data: { role_id: 1, permission_keys: ['access_control.roles.manage'] },
    });
    mockGetRole.mockResolvedValue({ data: sampleRoles[0] });
    mockListUsers.mockResolvedValue({ data: [{ id: 2, username: 'proc1', role: 'procurement' }] });
    mockGetUserRoles.mockResolvedValue({ data: { user_id: 2, role_ids: [1], roles: [] } });
    mockCreateRole.mockResolvedValue({
      data: {
        id: 100,
        code: 'sprint5c_smoke',
        display_name: 'Sprint 5C Smoke',
        is_system: false,
        is_active: true,
        created_at: '2026-01-01',
      },
    });
    mockUpdateRole.mockResolvedValue({ data: sampleRoles[1] });
    mockUpdateRolePermissions.mockResolvedValue({
      data: { role_id: 99, permission_keys: ['access_control.roles.view'] },
    });
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container.remove();
    jest.clearAllMocks();
  });

  it('loads and displays roles with system/custom status', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<AccessControlPage />);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(mockListRoles).toHaveBeenCalled();
    expect(container.textContent).toContain('System Admin');
    expect(container.textContent).toContain('System role');
    expect(container.textContent).toContain('Custom role');
    expect(container.textContent).toContain('Permission matrix');
    expect(container.textContent).toContain('Pilot enforcement notice');
    expect(container.textContent).toContain('Roles');
    expect(container.textContent).not.toMatch(/Feature: access_control/);
  });

  it('opens create role dialog', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<AccessControlPage />);
      await Promise.resolve();
      await Promise.resolve();
    });

    const createButtons = Array.from(container.querySelectorAll('button')).filter((b) =>
      b.textContent?.includes('Create role')
    );
    await act(async () => {
      createButtons[0]?.click();
    });

    expect(container.textContent).toContain('Role code');
  });
});
