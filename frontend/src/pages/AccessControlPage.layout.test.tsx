import React from 'react';
import { act } from 'react';
import { createRoot, Root } from 'react-dom/client';

jest.mock('../contexts/AuthContext.tsx', () => ({
  useAuth: () => ({
    user: { role: 'admin', permissions: ['access_control.roles.manage'] },
    loading: false,
  }),
}));

const mockListRoles = jest.fn();
const mockListPermissions = jest.fn();
const mockGetRolePermissions = jest.fn();
const mockGetRole = jest.fn();

jest.mock('../services/api.ts', () => ({
  accessControlAPI: {
    listRoles: (...args: unknown[]) => mockListRoles(...args),
    listPermissions: (...args: unknown[]) => mockListPermissions(...args),
    getRolePermissions: (...args: unknown[]) => mockGetRolePermissions(...args),
    getRole: (...args: unknown[]) => mockGetRole(...args),
    createRole: jest.fn(),
    updateRole: jest.fn(),
    updateRolePermissions: jest.fn(),
    getUserRoles: jest.fn(),
    updateUserRoles: jest.fn(),
    deactivateRole: jest.fn(),
  },
  usersAPI: { list: jest.fn() },
}));

jest.mock('../components/ui/RivarPageHeader.tsx', () => ({
  RivarPageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        'accessControl.title': 'Access Control',
        'accessControl.subtitle': 'Manage roles',
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
        'accessControl.selectRole': 'Select a role',
        'accessControl.permissionMatrix': 'Permission matrix',
        'accessControl.feature': 'Feature',
        'accessControl.savePermissions': 'Save permissions',
        'accessControl.saveRole': 'Save role',
        'accessControl.enforcementPilotNotice': 'Pilot enforcement notice',
        'accessControl.systemAdminLocked': 'System admin locked',
        'permissionGroups.access_control': 'Access Control',
        'permissionFeatures.access_control_roles': 'Roles',
        'permissionActions.view': 'View',
        'permissionActions.manage': 'Manage',
        'common.refresh': 'Refresh',
      };
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
  },
  {
    id: 2,
    code: 'access_control_admin',
    display_name: 'Access Control Administrator',
    description: 'Manage roles',
    is_system: true,
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
];

describe('AccessControlPage layout', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    mockListRoles.mockResolvedValue({ data: sampleRoles });
    mockListPermissions.mockResolvedValue({ data: samplePermissions });
    mockGetRolePermissions.mockResolvedValue({ data: { permission_keys: [] } });
    mockGetRole.mockResolvedValue({ data: sampleRoles[1] });
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

  it('renders role list and editor together when a role is selected', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<AccessControlPage embedded mode="roles" />);
      await Promise.resolve();
      await Promise.resolve();
    });

    const rows = document.querySelectorAll('tbody tr');
    expect(rows.length).toBeGreaterThanOrEqual(2);

    await act(async () => {
      (rows[1] as HTMLElement).click();
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(document.body.textContent).toContain('Access Control Administrator');
    expect(document.body.textContent).toContain('system_admin');
    expect(document.body.textContent).toContain('Permission matrix');
  });

  it('uses scrollable containers for role list and permission matrix regions', async () => {
    await act(async () => {
      root = createRoot(container);
      root.render(<AccessControlPage embedded mode="roles" />);
      await Promise.resolve();
      await Promise.resolve();
    });

    const tableContainers = Array.from(document.querySelectorAll('.MuiTableContainer-root'));
    expect(tableContainers.length).toBeGreaterThan(0);
    const roleListContainer = tableContainers[0] as HTMLElement;
    expect(roleListContainer.className).toMatch(/MuiTableContainer-root/);

    const rows = document.querySelectorAll('tbody tr');
    await act(async () => {
      (rows[1] as HTMLElement).click();
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(document.body.textContent).toContain('Pilot enforcement notice');
  });

  it('renders in RTL document direction without losing role list', async () => {
    document.documentElement.setAttribute('dir', 'rtl');
    await act(async () => {
      root = createRoot(container);
      root.render(<AccessControlPage embedded mode="roles" />);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(document.body.textContent).toContain('system_admin');
    expect(document.body.textContent).toContain('Access Control Administrator');
    document.documentElement.removeAttribute('dir');
  });
});
