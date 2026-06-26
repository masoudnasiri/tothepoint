import type { User } from '../types/index.ts';

/** Active users who can receive procurement assignments. */
export function filterProcurementCapableUsers(users: User[]): User[] {
  return users.filter(
    (u) =>
      u.is_active &&
      (u.role === 'procurement' ||
        u.roles?.some((r) => r.code === 'procurement_specialist'))
  );
}

export function formatUserLabel(user: User): string {
  const roleHint =
    user.roles?.map((r) => r.display_name).join(', ') ||
    user.role;
  return `${user.username} (${roleHint})`;
}
