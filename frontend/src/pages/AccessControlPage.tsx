import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Switch,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import { Add as AddIcon, Refresh as RefreshIcon, Save as SaveIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { accessControlAPI, usersAPI } from '../services/api.ts';
import type {
  Permission,
  Role,
  RoleCreate,
  RoleUpdate,
  User,
} from '../types/index.ts';
import { RivarPageHeader } from '../components/ui/RivarPageHeader.tsx';

const ROLE_CODE_PATTERN = /^[a-z][a-z0-9_]*$/;

function getApiErrorDetail(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e: { loc?: string[]; msg?: string }) =>
        `${e.loc?.join(' -> ') || 'Field'}: ${e.msg || 'invalid'}`
      )
      .join('; ');
  }
  return fallback;
}

function groupPermissionsByFeature(permissions: Permission[]): Record<string, Permission[]> {
  return permissions.reduce<Record<string, Permission[]>>((acc, perm) => {
    if (!acc[perm.feature_key]) acc[perm.feature_key] = [];
    acc[perm.feature_key].push(perm);
    return acc;
  }, {});
}

export const AccessControlPage: React.FC = () => {
  const { t } = useTranslation();
  const [tab, setTab] = useState(0);
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [permissionCounts, setPermissionCounts] = useState<Record<number, number>>({});
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null);
  const [rolePermissionKeys, setRolePermissionKeys] = useState<Set<string>>(new Set());
  const [roleForm, setRoleForm] = useState<RoleUpdate>({});
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | ''>('');
  const [userRoleIds, setUserRoleIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<RoleCreate>({ code: '', display_name: '', description: '' });
  const [createError, setCreateError] = useState('');
  const [deactivateTarget, setDeactivateTarget] = useState<Role | null>(null);

  const selectedRole = useMemo(
    () => roles.find((r) => r.id === selectedRoleId) || null,
    [roles, selectedRoleId]
  );

  const permissionsByFeature = useMemo(() => groupPermissionsByFeature(permissions), [permissions]);

  const permissionsReadOnly = Boolean(
    selectedRole && (selectedRole.code === 'system_admin' || !selectedRole.is_active)
  );

  const showSuccess = (message: string) =>
    setSnackbar({ open: true, message, severity: 'success' });
  const showError = (message: string) =>
    setSnackbar({ open: true, message, severity: 'error' });

  const loadPermissionCounts = useCallback(async (roleList: Role[]) => {
    const entries = await Promise.all(
      roleList.map(async (role) => {
        try {
          const res = await accessControlAPI.getRolePermissions(role.id);
          const keys = (res.data?.permission_keys || []) as string[];
          return [role.id, keys.length] as const;
        } catch {
          return [role.id, 0] as const;
        }
      })
    );
    setPermissionCounts(Object.fromEntries(entries));
  }, []);

  const loadRolesAndPermissions = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [rolesRes, permsRes] = await Promise.all([
        accessControlAPI.listRoles(),
        accessControlAPI.listPermissions(),
      ]);
      const roleList = rolesRes.data as Role[];
      setRoles(roleList);
      setPermissions(permsRes.data as Permission[]);
      await loadPermissionCounts(roleList);
      if (roleList.length) {
        setSelectedRoleId((current) => current ?? roleList[0].id);
      }
    } catch (err) {
      setError(getApiErrorDetail(err, 'Failed to load access control data'));
    } finally {
      setLoading(false);
    }
  }, [loadPermissionCounts]);

  const loadRoleDetail = useCallback(
    async (roleId: number) => {
      setDetailLoading(true);
      try {
        const [roleRes, permRes] = await Promise.all([
          accessControlAPI.getRole(roleId),
          accessControlAPI.getRolePermissions(roleId),
        ]);
        const role = roleRes.data as Role;
        const keys = (permRes.data?.permission_keys || []) as string[];
        setRoleForm({
          display_name: role.display_name,
          description: role.description || '',
          is_active: role.is_active,
        });
        setRolePermissionKeys(new Set(keys));
        setPermissionCounts((prev) => ({ ...prev, [roleId]: keys.length }));
      } catch (err) {
        showError(getApiErrorDetail(err, 'Failed to load role details'));
      } finally {
        setDetailLoading(false);
      }
    },
    []
  );

  const loadUsers = useCallback(async () => {
    try {
      const res = await usersAPI.list();
      setUsers(res.data as User[]);
    } catch (err) {
      showError(getApiErrorDetail(err, 'Failed to load users'));
    }
  }, []);

  const loadUserRoles = useCallback(async (userId: number) => {
    try {
      const res = await accessControlAPI.getUserRoles(userId);
      setUserRoleIds(res.data.role_ids || []);
    } catch (err) {
      showError(getApiErrorDetail(err, 'Failed to load user roles'));
    }
  }, []);

  useEffect(() => {
    void loadRolesAndPermissions();
    void loadUsers();
    // Mount-only bootstrap; refresh button calls loaders explicitly.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedRoleId) {
      loadRoleDetail(selectedRoleId);
    }
  }, [selectedRoleId, loadRoleDetail]);

  useEffect(() => {
    if (selectedUserId !== '') {
      loadUserRoles(selectedUserId);
    } else {
      setUserRoleIds([]);
    }
  }, [selectedUserId, loadUserRoles]);

  const handleCreateRole = async () => {
    setCreateError('');
    if (!createForm.code.trim() || !createForm.display_name.trim()) {
      setCreateError(t('accessControl.requiredFields'));
      return;
    }
    if (!ROLE_CODE_PATTERN.test(createForm.code.trim())) {
      setCreateError(t('accessControl.invalidRoleCode'));
      return;
    }
    try {
      const res = await accessControlAPI.createRole({
        code: createForm.code.trim(),
        display_name: createForm.display_name.trim(),
        description: createForm.description?.trim() || null,
      });
      const created = res.data as Role;
      setCreateOpen(false);
      setCreateForm({ code: '', display_name: '', description: '' });
      showSuccess(t('accessControl.roleCreated'));
      await loadRolesAndPermissions();
      setSelectedRoleId(created.id);
    } catch (err) {
      setCreateError(getApiErrorDetail(err, t('accessControl.createRoleFailed')));
    }
  };

  const handleSaveRoleMetadata = async () => {
    if (!selectedRole) return;
    setSaving(true);
    try {
      const payload: RoleUpdate = {
        display_name: roleForm.display_name,
        description: roleForm.description,
        is_active: roleForm.is_active,
      };
      await accessControlAPI.updateRole(selectedRole.id, payload);
      showSuccess(t('accessControl.roleUpdated'));
      await loadRolesAndPermissions();
      await loadRoleDetail(selectedRole.id);
    } catch (err) {
      showError(getApiErrorDetail(err, t('accessControl.updateRoleFailed')));
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivateRole = async () => {
    if (!deactivateTarget) return;
    setSaving(true);
    try {
      await accessControlAPI.deactivateRole(deactivateTarget.id);
      showSuccess(t('accessControl.roleDeactivated'));
      setDeactivateTarget(null);
      if (selectedRoleId === deactivateTarget.id) {
        setSelectedRoleId(null);
      }
      await loadRolesAndPermissions();
    } catch (err) {
      showError(getApiErrorDetail(err, t('accessControl.deactivateRoleFailed')));
    } finally {
      setSaving(false);
    }
  };

  const handleSavePermissions = async () => {
    if (!selectedRole || permissionsReadOnly) return;
    setSaving(true);
    try {
      await accessControlAPI.updateRolePermissions(selectedRole.id, {
        permission_keys: Array.from(rolePermissionKeys).sort(),
      });
      showSuccess(t('accessControl.permissionsSaved'));
      await loadRoleDetail(selectedRole.id);
    } catch (err) {
      showError(getApiErrorDetail(err, t('accessControl.savePermissionsFailed')));
    } finally {
      setSaving(false);
    }
  };

  const handleSaveUserRoles = async () => {
    if (selectedUserId === '') return;
    setSaving(true);
    try {
      await accessControlAPI.updateUserRoles(selectedUserId, { role_ids: userRoleIds });
      showSuccess(t('accessControl.userRolesSaved'));
    } catch (err) {
      showError(getApiErrorDetail(err, t('accessControl.saveUserRolesFailed')));
    } finally {
      setSaving(false);
    }
  };

  const togglePermission = (key: string) => {
    if (permissionsReadOnly) return;
    setRolePermissionKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const activeRoles = roles.filter((r) => r.is_active);

  return (
    <Box>
      <RivarPageHeader
        title={t('accessControl.title')}
        subtitle={t('accessControl.subtitle')}
        actions={
          <Button startIcon={<RefreshIcon />} onClick={loadRolesAndPermissions} disabled={loading}>
            {t('common.refresh')}
          </Button>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('accessControl.rolesTab')} />
        <Tab label={t('accessControl.userRolesTab')} />
      </Tabs>

      {tab === 0 && (
        <Box>
          <Box display="flex" justifyContent="flex-end" mb={2}>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
              {t('accessControl.createRole')}
            </Button>
          </Box>

          {loading ? (
            <Box display="flex" justifyContent="center" py={6}>
              <CircularProgress />
            </Box>
          ) : roles.length === 0 ? (
            <Alert severity="info">{t('accessControl.noRoles')}</Alert>
          ) : (
            <Box display="grid" gridTemplateColumns={{ xs: '1fr', lg: '1fr 1.2fr' }} gap={2}>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('accessControl.roleCode')}</TableCell>
                      <TableCell>{t('accessControl.roleName')}</TableCell>
                      <TableCell>{t('accessControl.roleType')}</TableCell>
                      <TableCell>{t('accessControl.status')}</TableCell>
                      <TableCell align="right">{t('accessControl.permissionCount')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {roles.map((role) => (
                      <TableRow
                        key={role.id}
                        hover
                        selected={role.id === selectedRoleId}
                        onClick={() => setSelectedRoleId(role.id)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>{role.code}</TableCell>
                        <TableCell>{role.display_name}</TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={
                              role.is_system
                                ? t('accessControl.systemRole')
                                : t('accessControl.customRole')
                            }
                            color={role.is_system ? 'default' : 'primary'}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={role.is_active ? t('accessControl.active') : t('accessControl.inactive')}
                            color={role.is_active ? 'success' : 'default'}
                          />
                        </TableCell>
                        <TableCell align="right">{permissionCounts[role.id] ?? '—'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Paper sx={{ p: 2 }}>
                {!selectedRole ? (
                  <Typography color="text.secondary">{t('accessControl.selectRole')}</Typography>
                ) : detailLoading ? (
                  <Box display="flex" justifyContent="center" py={4}>
                    <CircularProgress />
                  </Box>
                ) : (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      {selectedRole.display_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {selectedRole.code}
                    </Typography>

                    <TextField
                      fullWidth
                      margin="normal"
                      label={t('accessControl.roleName')}
                      value={roleForm.display_name || ''}
                      onChange={(e) => setRoleForm((f) => ({ ...f, display_name: e.target.value }))}
                      disabled={selectedRole.code === 'system_admin'}
                    />
                    <TextField
                      fullWidth
                      margin="normal"
                      label={t('accessControl.description')}
                      value={roleForm.description || ''}
                      onChange={(e) => setRoleForm((f) => ({ ...f, description: e.target.value }))}
                      multiline
                      minRows={2}
                      disabled={selectedRole.code === 'system_admin'}
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={Boolean(roleForm.is_active)}
                          onChange={(e) =>
                            setRoleForm((f) => ({ ...f, is_active: e.target.checked }))
                          }
                          disabled={selectedRole.is_system}
                        />
                      }
                      label={t('accessControl.active')}
                    />

                    <Box display="flex" gap={1} flexWrap="wrap" mt={1} mb={2}>
                      <Button
                        variant="contained"
                        startIcon={<SaveIcon />}
                        onClick={handleSaveRoleMetadata}
                        disabled={saving || selectedRole.code === 'system_admin'}
                      >
                        {t('accessControl.saveRole')}
                      </Button>
                      {!selectedRole.is_system && selectedRole.is_active && (
                        <Button
                          color="warning"
                          onClick={() => setDeactivateTarget(selectedRole)}
                          disabled={saving}
                        >
                          {t('accessControl.deactivateRole')}
                        </Button>
                      )}
                    </Box>

                    {selectedRole.is_system && (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        {selectedRole.code === 'system_admin'
                          ? t('accessControl.systemAdminLocked')
                          : t('accessControl.systemRoleHint')}
                      </Alert>
                    )}

                    <Typography variant="subtitle1" gutterBottom>
                      {t('accessControl.permissionMatrix')}
                    </Typography>

                    {Object.entries(permissionsByFeature).map(([featureKey, featurePerms]) => (
                      <Box key={featureKey} sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                          {t('accessControl.feature')}: {featureKey}
                        </Typography>
                        <Box display="flex" flexWrap="wrap" gap={1}>
                          {featurePerms
                            .sort((a, b) => a.sort_order - b.sort_order)
                            .map((perm) => (
                              <FormControlLabel
                                key={perm.permission_key}
                                control={
                                  <Checkbox
                                    size="small"
                                    checked={rolePermissionKeys.has(perm.permission_key)}
                                    onChange={() => togglePermission(perm.permission_key)}
                                    disabled={permissionsReadOnly}
                                  />
                                }
                                label={`${t('accessControl.action')}: ${perm.action}`}
                              />
                            ))}
                        </Box>
                      </Box>
                    ))}

                    <Button
                      variant="outlined"
                      startIcon={<SaveIcon />}
                      onClick={handleSavePermissions}
                      disabled={saving || permissionsReadOnly}
                    >
                      {t('accessControl.savePermissions')}
                    </Button>
                  </Box>
                )}
              </Paper>
            </Box>
          )}
        </Box>
      )}

      {tab === 1 && (
        <Paper sx={{ p: 2, maxWidth: 720 }}>
          <Typography variant="h6" gutterBottom>
            {t('accessControl.assignRolesToUser')}
          </Typography>
          <FormControl fullWidth margin="normal">
            <InputLabel>{t('accessControl.selectUser')}</InputLabel>
            <Select
              value={selectedUserId}
              label={t('accessControl.selectUser')}
              onChange={(e) => setSelectedUserId(e.target.value as number | '')}
            >
              <MenuItem value="">
                <em>{t('accessControl.chooseUser')}</em>
              </MenuItem>
              {users.map((u) => (
                <MenuItem key={u.id} value={u.id}>
                  {u.username} ({u.role})
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {selectedUserId !== '' && (
            <>
              <FormControl fullWidth margin="normal">
                <InputLabel>{t('accessControl.roles')}</InputLabel>
                <Select
                  multiple
                  value={userRoleIds}
                  label={t('accessControl.roles')}
                  onChange={(e) => setUserRoleIds(e.target.value as number[])}
                  renderValue={(selected) =>
                    selected
                      .map((id) => activeRoles.find((r) => r.id === id)?.display_name || String(id))
                      .join(', ')
                  }
                >
                  {activeRoles.map((role) => (
                    <MenuItem key={role.id} value={role.id}>
                      {role.display_name} ({role.code})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSaveUserRoles}
                disabled={saving}
              >
                {t('accessControl.saveUserRoles')}
              </Button>
            </>
          )}
        </Paper>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('accessControl.createRole')}</DialogTitle>
        <DialogContent>
          {createError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {createError}
            </Alert>
          )}
          <TextField
            fullWidth
            margin="normal"
            label={t('accessControl.roleCode')}
            value={createForm.code}
            onChange={(e) => setCreateForm((f) => ({ ...f, code: e.target.value }))}
            helperText={t('accessControl.roleCodeHint')}
          />
          <TextField
            fullWidth
            margin="normal"
            label={t('accessControl.roleName')}
            value={createForm.display_name}
            onChange={(e) => setCreateForm((f) => ({ ...f, display_name: e.target.value }))}
          />
          <TextField
            fullWidth
            margin="normal"
            label={t('accessControl.description')}
            value={createForm.description || ''}
            onChange={(e) => setCreateForm((f) => ({ ...f, description: e.target.value }))}
            multiline
            minRows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleCreateRole}>
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(deactivateTarget)} onClose={() => setDeactivateTarget(null)}>
        <DialogTitle>{t('accessControl.deactivateRole')}</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {t('accessControl.deactivateRoleConfirm', { name: deactivateTarget?.display_name })}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeactivateTarget(null)}>{t('common.cancel')}</Button>
          <Button color="warning" onClick={handleDeactivateRole} disabled={saving}>
            {t('accessControl.deactivateRole')}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        message={snackbar.message}
      />
    </Box>
  );
};
