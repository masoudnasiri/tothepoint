import {
  canCreateItemsMaster,
  canDeleteItemsMaster,
  canEditItemsMaster,
  canViewItemsMaster,
} from '../utils/permissions.ts';

describe('Items Master pilot permissions', () => {
  it('admin bypass allows all actions', () => {
    const admin = { role: 'admin', permissions: [] } as any;
    expect(canViewItemsMaster(admin)).toBe(true);
    expect(canCreateItemsMaster(admin)).toBe(true);
    expect(canEditItemsMaster(admin)).toBe(true);
    expect(canDeleteItemsMaster(admin)).toBe(true);
  });

  it('legacy pm without RBAC grants cannot write', () => {
    const pm = { role: 'pm', permissions: [] } as any;
    expect(canViewItemsMaster(pm)).toBe(false);
    expect(canCreateItemsMaster(pm)).toBe(false);
  });

  it('view-only RBAC role can view but not create', () => {
    const viewer = {
      role: 'procurement',
      permissions: ['master_data.items.view'],
    } as any;
    expect(canViewItemsMaster(viewer)).toBe(true);
    expect(canCreateItemsMaster(viewer)).toBe(false);
    expect(canEditItemsMaster(viewer)).toBe(false);
  });
});
