import {
  canAccessUsersAccessControlSection,
  canViewUsersSection,
  canManageAccessControl,
  hasPilotPermission,
} from './permissions.ts';

describe('permissions pilot helpers', () => {
  it('allows admin legacy bypass for pilot permissions', () => {
    const admin = { role: 'admin', permissions: [] } as any;
    expect(hasPilotPermission(admin, 'master_data.items.create')).toBe(true);
  });

  it('denies legacy pm write without RBAC grant', () => {
    const pm = { role: 'pm', permissions: [] } as any;
    expect(hasPilotPermission(pm, 'master_data.items.create')).toBe(false);
  });

  it('grants pilot permission when present in effective permissions', () => {
    const user = {
      role: 'pm',
      permissions: ['master_data.suppliers.view'],
    } as any;
    expect(hasPilotPermission(user, 'master_data.suppliers.view')).toBe(true);
    expect(hasPilotPermission(user, 'master_data.suppliers.create')).toBe(false);
  });

  it('users.view can access unified section but not role management', () => {
    const user = { role: 'pm', permissions: ['users.view'] } as any;
    expect(canViewUsersSection(user)).toBe(true);
    expect(canManageAccessControl(user)).toBe(false);
    expect(canAccessUsersAccessControlSection(user)).toBe(true);
  });
});
