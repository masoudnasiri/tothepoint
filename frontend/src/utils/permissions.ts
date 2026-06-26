import { useMemo } from 'react';
import type { User } from '../types/index.ts';

export const ACCESS_CONTROL_MANAGE_PERMISSION = 'access_control.roles.manage';

export const ACCESS_CONTROL_MANAGE_PERMISSIONS = [
  'access_control.roles.manage',
  'access_control.permissions.manage',
  'access_control.user_roles.edit',
] as const;

export function hasPermission(user: User | null | undefined, permissionKey: string): boolean {
  if (!user) return false;
  return Boolean(user.permissions?.includes(permissionKey));
}

export function hasAnyPermission(
  user: User | null | undefined,
  permissionKeys: readonly string[] | string[]
): boolean {
  if (!user?.permissions?.length) return false;
  return permissionKeys.some((key) => user.permissions!.includes(key));
}

/** Mirrors backend access-control manager guard during RBAC transition. */
export function canManageAccessControl(user: User | null | undefined): boolean {
  if (!user) return false;
  if (user.role === 'admin') return true;
  if (user.permissions?.length) {
    return hasAnyPermission(user, ACCESS_CONTROL_MANAGE_PERMISSIONS);
  }
  return false;
}

export function usePermissions(user: User | null | undefined) {
  return useMemo(
    () => ({
      hasPermission: (permissionKey: string) => hasPermission(user, permissionKey),
      hasAnyPermission: (permissionKeys: readonly string[] | string[]) =>
        hasAnyPermission(user, permissionKeys),
      canManageAccessControl: () => canManageAccessControl(user),
    }),
    [user]
  );
}
