/**
 * Derives hidden users.role compatibility value from selected RBAC system role codes.
 * Custom-only selections use pm (least-privilege legacy slot); effective access comes from RBAC grants.
 */
const SYSTEM_ROLE_TO_LEGACY: Record<string, string> = {
  system_admin: 'admin',
  pmo: 'pmo',
  project_manager: 'pm',
  procurement_specialist: 'procurement',
  finance_analyst: 'finance',
};

const LEGACY_ROLE_PRECEDENCE = ['admin', 'pmo', 'finance', 'procurement', 'pm'] as const;

export function deriveLegacyRoleFromRoleCodes(roleCodes: string[]): string {
  const legacyRoles = roleCodes
    .map((code) => SYSTEM_ROLE_TO_LEGACY[code])
    .filter((value): value is string => Boolean(value));

  if (!legacyRoles.length) {
    return 'pm';
  }

  for (const candidate of LEGACY_ROLE_PRECEDENCE) {
    if (legacyRoles.includes(candidate)) {
      return candidate;
    }
  }

  return 'pm';
}
