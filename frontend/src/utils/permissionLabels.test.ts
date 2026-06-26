import {
  getFeatureEnforcementBadge,
  isEnforcedFeatureKey,
  isPilotEnforcedPermission,
  isPilotFeatureKey,
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

  it('uses feature keys so access_control rows are enforced not pilot', () => {
    expect(isEnforcedFeatureKey('access_control.roles')).toBe(true);
    expect(isEnforcedFeatureKey('access_control.permissions')).toBe(true);
    expect(isEnforcedFeatureKey('access_control.user_roles')).toBe(true);
    expect(isPilotFeatureKey('access_control.roles')).toBe(false);

    expect(
      getFeatureEnforcementBadge(
        [{ permission_key: 'access_control.roles.view' }],
        'access_control.roles'
      )
    ).toBe('enforced');
    expect(
      getFeatureEnforcementBadge(
        [{ permission_key: 'access_control.permissions.manage' }],
        'access_control.permissions'
      )
    ).toBe('enforced');
  });

  it('returns pilot badge for master data pilot features only', () => {
    expect(
      getFeatureEnforcementBadge(
        [{ permission_key: 'master_data.items.view' }],
        'master_data.items'
      )
    ).toBe('pilot');
    expect(
      getFeatureEnforcementBadge([{ permission_key: 'users.view' }], 'users')
    ).toBe('enforced');
    expect(
      getFeatureEnforcementBadge([{ permission_key: 'projects.view' }], 'projects')
    ).toBe(null);
    expect(
      getFeatureEnforcementBadge(
        [{ permission_key: 'master_data.payment_methods.view' }],
        'master_data.payment_methods'
      )
    ).toBe('enforced');
    expect(
      getFeatureEnforcementBadge(
        [{ permission_key: 'master_data.cost_components.view' }],
        'master_data.cost_components'
      )
    ).toBe('enforced');
  });

  it('Persian label keys exist for enforced and pilot badges', () => {
    const fa = require('../i18n/fa.json');
    expect(fa.accessControl.enforced).toBe('اعمال‌شده');
    expect(fa.accessControl.pilotEnforced).toBe('پایلوت اجراشده');
  });
});
