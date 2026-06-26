import { canManageAccessControl, hasPermission } from './permissions.ts';
import type { User } from '../types/index.ts';

describe('permissions utils', () => {
  it('allows legacy admin during transition', () => {
    const user: User = {
      id: 1,
      username: 'admin',
      role: 'admin',
      created_at: '2026-01-01',
      is_active: true,
    };
    expect(canManageAccessControl(user)).toBe(true);
  });

  it('allows user with access_control.roles.manage', () => {
    const user: User = {
      id: 2,
      username: 'ac_admin',
      role: 'pm',
      created_at: '2026-01-01',
      is_active: true,
      permissions: ['access_control.roles.manage'],
    };
    expect(canManageAccessControl(user)).toBe(true);
    expect(hasPermission(user, 'access_control.roles.manage')).toBe(true);
  });

  it('denies procurement user without manage permissions', () => {
    const user: User = {
      id: 3,
      username: 'proc1',
      role: 'procurement',
      created_at: '2026-01-01',
      is_active: true,
      permissions: ['procurement.options.view'],
    };
    expect(canManageAccessControl(user)).toBe(false);
  });
});
