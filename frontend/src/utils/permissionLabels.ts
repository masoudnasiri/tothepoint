/** Human-readable permission matrix labels for Access Control UI (Sprint 5C-R1). */

export type PermissionGroupKey =
  | 'access_control'
  | 'users'
  | 'projects'
  | 'procurement'
  | 'master_data'
  | 'finance'
  | 'cashflow'
  | 'optimization'
  | 'reports'
  | 'decisions';

export const PERMISSION_GROUP_ORDER: PermissionGroupKey[] = [
  'access_control',
  'users',
  'projects',
  'procurement',
  'master_data',
  'finance',
  'cashflow',
  'optimization',
  'reports',
  'decisions',
];

export function resolvePermissionGroup(featureKey: string): PermissionGroupKey {
  if (featureKey.startsWith('access_control')) return 'access_control';
  if (featureKey.startsWith('users')) return 'users';
  if (featureKey.startsWith('project')) return 'projects';
  if (featureKey.startsWith('procurement')) return 'procurement';
  if (featureKey.startsWith('master_data')) return 'master_data';
  if (featureKey.startsWith('finance')) return 'finance';
  if (featureKey.startsWith('cashflow')) return 'cashflow';
  if (featureKey.startsWith('optimization')) return 'optimization';
  if (featureKey.startsWith('report')) return 'reports';
  if (featureKey.startsWith('decision')) return 'decisions';
  return 'master_data';
}

export function featureLabelKey(featureKey: string): string {
  return `permissionFeatures.${featureKey.replace(/\./g, '_')}`;
}

export function actionLabelKey(action: string): string {
  return `permissionActions.${action}`;
}

/** Pilot-enforced permission prefixes (backend + frontend). */
export const PILOT_ENFORCED_PREFIXES = [
  'access_control.',
  'users.',
  'master_data.items.',
  'master_data.suppliers.',
] as const;

export function isPilotEnforcedPermission(permissionKey: string): boolean {
  return PILOT_ENFORCED_PREFIXES.some((prefix) => permissionKey.startsWith(prefix));
}
