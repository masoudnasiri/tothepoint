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

function isLegacyAdmin(user: User | null | undefined): boolean {
  return user?.role === 'admin';
}

/** Mirrors backend access-control manager guard during RBAC transition. */
export function canManageAccessControl(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  if (user.permissions?.length) {
    return hasAnyPermission(user, ACCESS_CONTROL_MANAGE_PERMISSIONS);
  }
  return false;
}

export function canViewUsersSection(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'users.view');
}

export function canCreateUsers(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'users.create');
}

export function canEditUsers(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'users.edit');
}

export function canDeleteUsers(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'users.delete');
}

export function canViewUserRoleAssignment(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasAnyPermission(user, ['access_control.user_roles.view', 'access_control.user_roles.edit']);
}

export function canEditUserRoleAssignment(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'access_control.user_roles.edit');
}

export function canAccessUsersAccessControlSection(user: User | null | undefined): boolean {
  return (
    canViewUsersSection(user) ||
    canManageAccessControl(user) ||
    canViewUserRoleAssignment(user)
  );
}

/**
 * Sprint 5C-R1 pilot: Items Master / Suppliers use effective RBAC permissions.
 * Legacy base role does not grant write except explicit admin bypass.
 */
export function hasPilotPermission(user: User | null | undefined, permissionKey: string): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, permissionKey);
}

export function canViewItemsMaster(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.items.view');
}

export function canCreateItemsMaster(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.items.create');
}

export function canEditItemsMaster(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.items.edit');
}

export function canDeleteItemsMaster(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.items.delete');
}

export function canViewSuppliers(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.suppliers.view');
}

export function canCreateSuppliers(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.suppliers.create');
}

export function canEditSuppliers(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.suppliers.edit');
}

export function canDeleteSuppliers(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.suppliers.delete');
}

export function usePermissions(user: User | null | undefined) {
  return useMemo(
    () => ({
      hasPermission: (permissionKey: string) => hasPermission(user, permissionKey),
      hasAnyPermission: (permissionKeys: readonly string[] | string[]) =>
        hasAnyPermission(user, permissionKeys),
      canManageAccessControl: () => canManageAccessControl(user),
      canViewUsersSection: () => canViewUsersSection(user),
      canAccessUsersAccessControlSection: () => canAccessUsersAccessControlSection(user),
      hasPilotPermission: (permissionKey: string) => hasPilotPermission(user, permissionKey),
      canViewItemsMaster: () => canViewItemsMaster(user),
      canCreateItemsMaster: () => canCreateItemsMaster(user),
      canEditItemsMaster: () => canEditItemsMaster(user),
      canDeleteItemsMaster: () => canDeleteItemsMaster(user),
      canViewSuppliers: () => canViewSuppliers(user),
      canCreateSuppliers: () => canCreateSuppliers(user),
      canEditSuppliers: () => canEditSuppliers(user),
      canDeleteSuppliers: () => canDeleteSuppliers(user),
    }),
    [user]
  );
}
