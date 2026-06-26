import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Tab,
  Tabs,
  Typography,
} from '@mui/material';
import { Refresh as RefreshIcon, Save as SaveIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { accessControlAPI, usersAPI } from '../services/api.ts';
import { useAuth } from '../contexts/AuthContext.tsx';
import type { Role, User } from '../types/index.ts';
import { RivarPageHeader } from '../components/ui/RivarPageHeader.tsx';
import { RoleManagementPanel } from '../components/accessControl/RoleManagementPanel.tsx';
import { canEditUserRoleAssignment } from '../utils/permissions.ts';

interface AccessControlPageProps {
  embedded?: boolean;
  mode?: 'full' | 'roles' | 'userRoles';
}

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

export const AccessControlPage: React.FC<AccessControlPageProps> = ({
  embedded = false,
  mode = 'full',
}) => {
  const { t } = useTranslation();
  const { user: currentUser } = useAuth();
  const initialTab = mode === 'userRoles' ? 1 : 0;
  const [tab, setTab] = useState(initialTab);
  const [roles, setRoles] = useState<Role[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | ''>('');
  const [userRoleIds, setUserRoleIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const showRolesPanel = mode === 'full' || mode === 'roles';
  const showUserRolesPanel = mode === 'full' || mode === 'userRoles';
  const userRolesReadOnly = !canEditUserRoleAssignment(currentUser);
  const activeRoles = roles.filter((r) => r.is_active);

  const onNotify = useCallback((message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  }, []);

  const loadRoles = useCallback(async () => {
    try {
      const rolesRes = await accessControlAPI.listRoles();
      setRoles(rolesRes.data as Role[]);
    } catch (err) {
      setError(getApiErrorDetail(err, t('accessControl.loadFailed')));
    }
  }, [t]);

  const loadUsers = useCallback(async () => {
    try {
      const res = await usersAPI.list();
      setUsers(res.data as User[]);
    } catch (err) {
      onNotify(getApiErrorDetail(err, t('accessControl.loadUsersFailed')), 'error');
    }
  }, [onNotify, t]);

  const loadUserRoles = useCallback(async (userId: number) => {
    try {
      const res = await accessControlAPI.getUserRoles(userId);
      setUserRoleIds(res.data.role_ids || []);
    } catch (err) {
      onNotify(getApiErrorDetail(err, t('accessControl.loadUserRolesFailed')), 'error');
    }
  }, [onNotify, t]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([loadRoles(), loadUsers()]);
      setLoading(false);
    };
    void init();
  }, [loadRoles, loadUsers]);

  useEffect(() => {
    if (selectedUserId !== '') {
      void loadUserRoles(selectedUserId);
    } else {
      setUserRoleIds([]);
    }
  }, [selectedUserId, loadUserRoles]);

  const handleSaveUserRoles = async () => {
    if (selectedUserId === '') return;
    setSaving(true);
    try {
      await accessControlAPI.updateUserRoles(selectedUserId, { role_ids: userRoleIds });
      onNotify(t('accessControl.userRolesSaved'), 'success');
    } catch (err) {
      onNotify(getApiErrorDetail(err, t('accessControl.saveUserRolesFailed')), 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box>
      {!embedded && (
        <RivarPageHeader
          title={t('accessControl.title')}
          subtitle={t('accessControl.subtitle')}
        />
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {mode === 'full' && (
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
          <Tab label={t('accessControl.rolesTab')} />
          <Tab label={t('accessControl.userRolesTab')} />
        </Tabs>
      )}

      {(mode === 'full' ? tab === 0 : showRolesPanel) && (
        <RoleManagementPanel onNotify={onNotify} />
      )}

      {(mode === 'full' ? tab === 1 : showUserRolesPanel) && (
        <Paper sx={{ p: 2, maxWidth: 720 }}>
          <Box display="flex" justifyContent="flex-end" mb={2}>
            <Button startIcon={<RefreshIcon />} onClick={loadUsers} disabled={loading}>
              {t('common.refresh')}
            </Button>
          </Box>
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
                  {u.username}
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
                  disabled={userRolesReadOnly}
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
                disabled={saving || userRolesReadOnly}
              >
                {t('accessControl.saveUserRoles')}
              </Button>
            </>
          )}
        </Paper>
      )}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        message={snackbar.message}
      />
    </Box>
  );
};
