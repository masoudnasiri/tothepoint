import {
  getFeatureEnforcementBadge,
  isPilotEnforcedPermission,
  isEnforcedPermission,
} from './permissionLabels.ts';

describe('permissionLabels enforcement badges', () => {
  it('marks only items and suppliers as pilot enforced', () => {
    expect(isPilotEnforcedPermission('master_data.items.view')).toBe(true);
    expect(isPilotEnforcedPermission('master_data.suppliers.edit')).toBe(true);
    expect(isPilotEnforcedPermission('users.view')).toBe(false);
    expect(isPilotEnforcedPermission('access_control.roles.manage')).toBe(false);
    expect(isPilotEnforcedPermission('projects.view')).toBe(false);
  });

  it('marks users and access_control as enforced (not pilot)', () => {
    expect(isEnforcedPermission('users.view')).toBe(true);
    expect(isEnforcedPermission('access_control.roles.manage')).toBe(true);
    expect(isEnforcedPermission('master_data.items.view')).toBe(false);
    expect(isEnforcedPermission('procurement.view')).toBe(false);
  });

  it('returns pilot badge for master data pilot features only', () => {
    expect(
      getFeatureEnforcementBadge([{ permission_key: 'master_data.items.view' }])
    ).toBe('pilot');
    expect(getFeatureEnforcementBadge([{ permission_key: 'users.view' }])).toBe('enforced');
    expect(getFeatureEnforcementBadge([{ permission_key: 'projects.view' }])).toBe(null);
  });
});
