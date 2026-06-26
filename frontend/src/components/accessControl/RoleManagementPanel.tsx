import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
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
  Drawer,
  FormControlLabel,
  IconButton,
  InputAdornment,
  Paper,
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
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
  ContentCopy as CopyIcon,
  DeleteOutline as DeleteIcon,
  Edit as EditIcon,
  ExpandMore as ExpandMoreIcon,
  Lock as LockIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { accessControlAPI } from '../../services/api.ts';
import type { Permission, Role, RoleAssignedUser, RoleCreate, RoleUpdate } from '../../types/index.ts';
import {
  PERMISSION_GROUP_ORDER,
  actionLabelKey,
  featureLabelKey,
  isPilotEnforcedPermission,
  resolvePermissionGroup,
} from '../../utils/permissionLabels.ts';

const ROLE_CODE_PATTERN = /^[a-z][a-z0-9_]*$/;
const DRAWER_WIDTH = { xs: '100%', sm: 560, md: 720, lg: 900 };

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

function setsEqual(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false;
  for (const item of a) {
    if (!b.has(item)) return false;
  }
  return true;
}

interface RoleManagementPanelProps {
  onNotify: (message: string, severity: 'success' | 'error') => void;
}

export const RoleManagementPanel: React.FC<RoleManagementPanelProps> = ({ onNotify }) => {
  const { t } = useTranslation();
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [permissionCounts, setPermissionCounts] = useState<Record<number, number>>({});
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorTab, setEditorTab] = useState(0);
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null);
  const [roleForm, setRoleForm] = useState<RoleUpdate>({});
  const [savedRoleForm, setSavedRoleForm] = useState<RoleUpdate>({});
  const [rolePermissionKeys, setRolePermissionKeys] = useState<Set<string>>(new Set());
  const [savedPermissionKeys, setSavedPermissionKeys] = useState<Set<string>>(new Set());
  const [assignedUsers, setAssignedUsers] = useState<RoleAssignedUser[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState<RoleCreate>({ code: '', display_name: '', description: '' });
  const [createError, setCreateError] = useState('');
  const [deactivateTarget, setDeactivateTarget] = useState<Role | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    master_data: true,
  });

  const selectedRole = useMemo(
    () => roles.find((r) => r.id === selectedRoleId) || null,
    [roles, selectedRoleId]
  );

  const filteredRoles = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return roles;
    return roles.filter(
      (r) =>
        r.code.toLowerCase().includes(q) ||
        r.display_name.toLowerCase().includes(q)
    );
  }, [roles, search]);

  const matrixByGroup = useMemo(() => {
    const grouped: Record<string, Record<string, Permission[]>> = {};
    for (const perm of permissions) {
      const group = resolvePermissionGroup(perm.feature_key);
      if (!grouped[group]) grouped[group] = {};
      if (!grouped[group][perm.feature_key]) grouped[group][perm.feature_key] = [];
      grouped[group][perm.feature_key].push(perm);
    }
    for (const group of Object.keys(grouped)) {
      for (const feature of Object.keys(grouped[group])) {
        grouped[group][feature].sort((a, b) => a.sort_order - b.sort_order);
      }
    }
    return grouped;
  }, [permissions]);

  const allActions = useMemo(() => {
    const actions = new Set<string>();
    permissions.forEach((p) => actions.add(p.action));
    const order = ['view', 'create', 'edit', 'delete', 'manage', 'assign', 'export'];
    return Array.from(actions).sort((a, b) => {
      const ai = order.indexOf(a);
      const bi = order.indexOf(b);
      if (ai === -1 && bi === -1) return a.localeCompare(b);
      if (ai === -1) return 1;
      if (bi === -1) return -1;
      return ai - bi;
    });
  }, [permissions]);

  const permissionsReadOnly = Boolean(
    selectedRole && (selectedRole.code === 'system_admin' || !selectedRole.is_active)
  );

  const isDirty = useMemo(() => {
    if (!selectedRole) return false;
    const formChanged =
      (roleForm.display_name || '') !== (savedRoleForm.display_name || '') ||
      (roleForm.description || '') !== (savedRoleForm.description || '') ||
      Boolean(roleForm.is_active) !== Boolean(savedRoleForm.is_active);
    return formChanged || !setsEqual(rolePermissionKeys, savedPermissionKeys);
  }, [selectedRole, roleForm, savedRoleForm, rolePermissionKeys, savedPermissionKeys]);

  const labelForFeature = (featureKey: string) => {
    const key = featureLabelKey(featureKey);
    const translated = t(key);
    return translated === key ? featureKey : translated;
  };

  const labelForAction = (action: string) => {
    const key = actionLabelKey(action);
    const translated = t(key);
    return translated === key ? action : translated;
  };

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
      const counts: Record<number, number> = {};
      for (const role of roleList) {
        counts[role.id] = role.permission_count ?? 0;
      }
      setPermissionCounts(counts);
    } catch (err) {
      setError(getApiErrorDetail(err, t('accessControl.loadFailed')));
    } finally {
      setLoading(false);
    }
    // Mount/refresh loader; translation fn is not a stable dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadRoleDetail = useCallback(
    async (roleId: number) => {
      setDetailLoading(true);
      try {
        const [roleRes, permRes, usersRes] = await Promise.all([
          accessControlAPI.getRole(roleId),
          accessControlAPI.getRolePermissions(roleId),
          accessControlAPI.getRoleAssignedUsers(roleId),
        ]);
        const role = roleRes.data as Role;
        const keys = (permRes.data?.permission_keys || []) as string[];
        const form: RoleUpdate = {
          display_name: role.display_name,
          description: role.description || '',
          is_active: role.is_active,
        };
        setRoleForm(form);
        setSavedRoleForm(form);
        const keySet = new Set(keys);
        setRolePermissionKeys(keySet);
        setSavedPermissionKeys(new Set(keys));
        setPermissionCounts((prev) => ({ ...prev, [roleId]: keys.length }));
        setAssignedUsers(usersRes.data as RoleAssignedUser[]);
      } catch (err) {
        onNotify(getApiErrorDetail(err, t('accessControl.loadRoleFailed')), 'error');
      } finally {
        setDetailLoading(false);
      }
    },
    [onNotify]
  );

  useEffect(() => {
    void loadRolesAndPermissions();
  }, [loadRolesAndPermissions]);

  useEffect(() => {
    if (editorOpen && selectedRoleId) {
      void loadRoleDetail(selectedRoleId);
    }
  }, [editorOpen, selectedRoleId, loadRoleDetail]);

  const openEditor = (roleId: number) => {
    setSelectedRoleId(roleId);
    setEditorTab(0);
    setEditorOpen(true);
  };

  const closeEditor = () => {
    if (isDirty && !window.confirm(t('accessControl.unsavedChangesConfirm'))) {
      return;
    }
    setEditorOpen(false);
    setSelectedRoleId(null);
    setEditorTab(0);
  };

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
      onNotify(t('accessControl.roleCreated'), 'success');
      await loadRolesAndPermissions();
      openEditor(created.id);
    } catch (err) {
      setCreateError(getApiErrorDetail(err, t('accessControl.createRoleFailed')));
    }
  };

  const handleSaveRoleMetadata = async () => {
    if (!selectedRole) return;
    setSaving(true);
    try {
      await accessControlAPI.updateRole(selectedRole.id, {
        display_name: roleForm.display_name,
        description: roleForm.description,
        is_active: roleForm.is_active,
      });
      onNotify(t('accessControl.roleUpdated'), 'success');
      await loadRolesAndPermissions();
      await loadRoleDetail(selectedRole.id);
    } catch (err) {
      onNotify(getApiErrorDetail(err, t('accessControl.updateRoleFailed')), 'error');
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
      onNotify(t('accessControl.permissionsSaved'), 'success');
      await loadRoleDetail(selectedRole.id);
    } catch (err) {
      onNotify(getApiErrorDetail(err, t('accessControl.savePermissionsFailed')), 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivateRole = async () => {
    if (!deactivateTarget) return;
    setSaving(true);
    try {
      await accessControlAPI.deactivateRole(deactivateTarget.id);
      onNotify(t('accessControl.roleDeactivated'), 'success');
      setDeactivateTarget(null);
      if (selectedRoleId === deactivateTarget.id) {
        setEditorOpen(false);
        setSelectedRoleId(null);
      }
      await loadRolesAndPermissions();
    } catch (err) {
      onNotify(getApiErrorDetail(err, t('accessControl.deactivateRoleFailed')), 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDuplicateRole = async (role: Role) => {
    const suffix = `_copy_${Date.now().toString(36).slice(-4)}`;
    const baseCode = role.code.slice(0, Math.max(1, 64 - suffix.length));
    const newCode = `${baseCode}${suffix}`;
    try {
      const createdRes = await accessControlAPI.createRole({
        code: newCode,
        display_name: `${role.display_name} (${t('accessControl.copySuffix')})`,
        description: role.description || null,
      });
      const created = createdRes.data as Role;
      const permRes = await accessControlAPI.getRolePermissions(role.id);
      const keys = (permRes.data?.permission_keys || []) as string[];
      if (keys.length) {
        await accessControlAPI.updateRolePermissions(created.id, { permission_keys: keys });
      }
      onNotify(t('accessControl.roleDuplicated'), 'success');
      await loadRolesAndPermissions();
      openEditor(created.id);
    } catch (err) {
      onNotify(getApiErrorDetail(err, t('accessControl.duplicateRoleFailed')), 'error');
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

  const groupPermissionKeys = (groupKey: string): string[] => {
    const features = matrixByGroup[groupKey];
    if (!features) return [];
    return Object.values(features)
      .flat()
      .map((p) => p.permission_key);
  };

  const selectAllInGroup = (groupKey: string) => {
    if (permissionsReadOnly) return;
    const keys = groupPermissionKeys(groupKey);
    setRolePermissionKeys((prev) => new Set([...prev, ...keys]));
  };

  const clearGroup = (groupKey: string) => {
    if (permissionsReadOnly) return;
    const keys = new Set(groupPermissionKeys(groupKey));
    setRolePermissionKeys((prev) => {
      const next = new Set(prev);
      keys.forEach((k) => next.delete(k));
      return next;
    });
  };

  const viewOnlyInGroup = (groupKey: string) => {
    if (permissionsReadOnly) return;
    const features = matrixByGroup[groupKey];
    if (!features) return;
    const viewKeys = Object.values(features)
      .flat()
      .filter((p) => p.action === 'view')
      .map((p) => p.permission_key);
    clearGroup(groupKey);
    setRolePermissionKeys((prev) => new Set([...prev, ...viewKeys]));
  };

  const renderPermissionMatrix = () => (
    <Box>
      <Alert severity="info" sx={{ mb: 2, py: 0.5 }} icon={false}>
        <Typography variant="caption">{t('accessControl.enforcementPilotNotice')}</Typography>
      </Alert>
      {PERMISSION_GROUP_ORDER.map((groupKey) => {
        const features = matrixByGroup[groupKey];
        if (!features) return null;
        const groupActions = allActions.filter((action) =>
          Object.values(features).some((perms) => perms.some((p) => p.action === action))
        );
        return (
          <Accordion
            key={groupKey}
            expanded={Boolean(expandedGroups[groupKey])}
            onChange={(_, expanded) =>
              setExpandedGroups((prev) => ({ ...prev, [groupKey]: expanded }))
            }
            disableGutters
            sx={{ mb: 1, '&:before': { display: 'none' } }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', width: '100%' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {t(`permissionGroups.${groupKey}`)}
                </Typography>
                <Box sx={{ ml: 'auto', display: 'flex', gap: 0.5 }} onClick={(e) => e.stopPropagation()}>
                  <Button size="small" onClick={() => selectAllInGroup(groupKey)} disabled={permissionsReadOnly}>
                    {t('accessControl.selectAllGroup')}
                  </Button>
                  <Button size="small" onClick={() => viewOnlyInGroup(groupKey)} disabled={permissionsReadOnly}>
                    {t('accessControl.viewOnlyGroup')}
                  </Button>
                  <Button size="small" onClick={() => clearGroup(groupKey)} disabled={permissionsReadOnly}>
                    {t('accessControl.clearGroup')}
                  </Button>
                </Box>
              </Box>
            </AccordionSummary>
            <AccordionDetails sx={{ pt: 0 }}>
              <TableContainer sx={{ maxHeight: 320, overflow: 'auto' }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('accessControl.feature')}</TableCell>
                      {groupActions.map((action) => (
                        <TableCell key={action} align="center" sx={{ whiteSpace: 'nowrap' }}>
                          {labelForAction(action)}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(features).map(([featureKey, featurePerms]) => (
                      <TableRow key={featureKey}>
                        <TableCell sx={{ minWidth: 160 }}>
                          <Typography variant="body2">{labelForFeature(featureKey)}</Typography>
                          {featurePerms.some((p) => isPilotEnforcedPermission(p.permission_key)) && (
                            <Chip
                              size="small"
                              label={t('accessControl.pilotEnforced')}
                              color="warning"
                              variant="outlined"
                              sx={{ mt: 0.5 }}
                            />
                          )}
                          <Typography variant="caption" color="text.secondary" display="block">
                            {featureKey}
                          </Typography>
                        </TableCell>
                        {groupActions.map((action) => {
                          const perm = featurePerms.find((p) => p.action === action);
                          if (!perm) {
                            return <TableCell key={action} align="center">—</TableCell>;
                          }
                          return (
                            <TableCell key={action} align="center">
                              <Checkbox
                                size="small"
                                checked={rolePermissionKeys.has(perm.permission_key)}
                                onChange={() => togglePermission(perm.permission_key)}
                                disabled={permissionsReadOnly}
                                inputProps={{ 'aria-label': perm.permission_key }}
                              />
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        );
      })}
    </Box>
  );

  return (
    <Box>
      <Box display="flex" flexWrap="wrap" gap={1} justifyContent="space-between" alignItems="center" mb={2}>
        <TextField
          size="small"
          placeholder={t('accessControl.searchRoles')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ minWidth: 220, flex: '1 1 220px', maxWidth: 400 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
        <Box display="flex" gap={1}>
          <Button startIcon={<RefreshIcon />} onClick={loadRolesAndPermissions} disabled={loading}>
            {t('common.refresh')}
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            {t('accessControl.createRole')}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress />
        </Box>
      ) : filteredRoles.length === 0 ? (
        <Alert severity="info">{search ? t('accessControl.noRolesMatch') : t('accessControl.noRoles')}</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('accessControl.roleName')}</TableCell>
                <TableCell>{t('accessControl.roleCode')}</TableCell>
                <TableCell>{t('accessControl.roleType')}</TableCell>
                <TableCell>{t('accessControl.status')}</TableCell>
                <TableCell align="right">{t('accessControl.permissionCount')}</TableCell>
                <TableCell align="right">{t('accessControl.assignedUsers')}</TableCell>
                <TableCell align="center">{t('common.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredRoles.map((role) => (
                <TableRow key={role.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={500} noWrap title={role.display_name}>
                      {role.display_name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary" noWrap title={role.code}>
                      {role.code}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      icon={role.is_system ? <LockIcon sx={{ fontSize: 14 }} /> : undefined}
                      label={role.is_system ? t('accessControl.systemRole') : t('accessControl.customRole')}
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
                  <TableCell align="right">{permissionCounts[role.id] ?? role.user_count ?? '—'}</TableCell>
                  <TableCell align="right">{role.user_count ?? 0}</TableCell>
                  <TableCell align="center" sx={{ whiteSpace: 'nowrap' }}>
                    <Tooltip title={t('common.edit')}>
                      <IconButton size="small" onClick={() => openEditor(role.id)} aria-label={t('common.edit')}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('accessControl.duplicateRole')}>
                      <IconButton
                        size="small"
                        onClick={() => void handleDuplicateRole(role)}
                        aria-label={t('accessControl.duplicateRole')}
                      >
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {!role.is_system && role.is_active && role.code !== 'system_admin' && (
                      <Tooltip title={t('accessControl.deactivateRole')}>
                        <IconButton
                          size="small"
                          color="warning"
                          onClick={() => setDeactivateTarget(role)}
                          aria-label={t('accessControl.deactivateRole')}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Drawer
        anchor="right"
        open={editorOpen}
        onClose={closeEditor}
        PaperProps={{
          sx: { width: DRAWER_WIDTH, display: 'flex', flexDirection: 'column' },
        }}
      >
        <Box sx={{ px: 2, pt: 2, pb: 1, display: 'flex', alignItems: 'flex-start', gap: 1 }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="h6" noWrap title={selectedRole?.display_name}>
              {selectedRole?.display_name || t('accessControl.selectRole')}
            </Typography>
            {selectedRole && (
              <Typography variant="body2" color="text.secondary" noWrap title={selectedRole.code}>
                {selectedRole.code}
              </Typography>
            )}
          </Box>
          <IconButton onClick={closeEditor} aria-label={t('common.close')}>
            <CloseIcon />
          </IconButton>
        </Box>

        <Tabs value={editorTab} onChange={(_, v) => setEditorTab(v)} sx={{ px: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Tab label={t('accessControl.roleDetailsTab')} />
          <Tab label={t('accessControl.permissionsTab')} />
          <Tab label={t('accessControl.assignedUsersTab')} />
        </Tabs>

        <Box sx={{ flex: 1, overflow: 'auto', px: 2, py: 2 }}>
          {detailLoading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : !selectedRole ? (
            <Typography color="text.secondary">{t('accessControl.selectRole')}</Typography>
          ) : editorTab === 0 ? (
            <Box>
              {selectedRole.is_system && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  {selectedRole.code === 'system_admin'
                    ? t('accessControl.systemAdminLocked')
                    : t('accessControl.systemRoleHint')}
                </Alert>
              )}
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
                    onChange={(e) => setRoleForm((f) => ({ ...f, is_active: e.target.checked }))}
                    disabled={selectedRole.is_system}
                  />
                }
                label={t('accessControl.active')}
              />
            </Box>
          ) : editorTab === 1 ? (
            renderPermissionMatrix()
          ) : (
            <Box>
              {assignedUsers.length === 0 ? (
                <Typography color="text.secondary">{t('accessControl.noAssignedUsers')}</Typography>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>{t('users.username')}</TableCell>
                        <TableCell>{t('users.active')}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {assignedUsers.map((u) => (
                        <TableRow key={u.id}>
                          <TableCell>{u.username}</TableCell>
                          <TableCell>
                            {u.is_active ? t('users.active') : t('users.inactive')}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2 }}>
                {t('accessControl.assignedUsersReadOnlyHint')}
              </Typography>
            </Box>
          )}
        </Box>

        <Box
          sx={{
            px: 2,
            py: 1.5,
            borderTop: 1,
            borderColor: 'divider',
            display: 'flex',
            gap: 1,
            justifyContent: 'flex-end',
            flexWrap: 'wrap',
            bgcolor: 'background.paper',
          }}
        >
          <Button onClick={closeEditor}>{t('common.cancel')}</Button>
          {editorTab === 0 && (
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSaveRoleMetadata}
              disabled={saving || selectedRole?.code === 'system_admin'}
            >
              {t('accessControl.saveRole')}
            </Button>
          )}
          {editorTab === 1 && (
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSavePermissions}
              disabled={saving || permissionsReadOnly}
            >
              {t('accessControl.savePermissions')}
            </Button>
          )}
        </Box>
      </Drawer>

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
    </Box>
  );
};
