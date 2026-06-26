import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { usersAPI, accessControlAPI } from '../services/api.ts';
import { User, Role } from '../types/index.ts';
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';
import { RivarPageHeader } from '../components/ui/RivarPageHeader.tsx';
import {
  canCreateUsers,
  canDeleteUsers,
  canEditUsers,
  canViewUsersSection,
} from '../utils/permissions.ts';
import { deriveLegacyRoleFromRoleCodes } from '../utils/legacyRoleDerivation.ts';

interface UsersPageProps {
  embedded?: boolean;
}

export const UsersPage: React.FC<UsersPageProps> = ({ embedded = false }) => {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  
  // Locale-aware date formatter
  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDate = useMemo(() => (dateString: string) => {
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd') : gregorianFormat(d, 'yyyy-MM-dd');
    } catch {
      return new Date(dateString).toLocaleDateString();
    }
  }, [isFa]);
  
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    is_active: true,
  });
  const [rbacRoles, setRbacRoles] = useState<Role[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<number[]>([]);
  const [userRoleLabels, setUserRoleLabels] = useState<Record<number, string>>({});
  const [rolesLoading, setRolesLoading] = useState(false);
  const [roleAssignWarning, setRoleAssignWarning] = useState('');

  const canView = canViewUsersSection(user);
  const canCreate = canCreateUsers(user);
  const canEdit = canEditUsers(user);
  const canDelete = canDeleteUsers(user);

  const loadRbacRoles = async () => {
    setRolesLoading(true);
    try {
      const res = await accessControlAPI.listRoles();
      setRbacRoles((res.data as Role[]).filter((r) => r.is_active));
    } catch {
      setRbacRoles([]);
    } finally {
      setRolesLoading(false);
    }
  };

  const loadUserRbacRoles = async (userId: number) => {
    try {
      const res = await accessControlAPI.getUserRoles(userId);
      setSelectedRoleIds(res.data.role_ids || []);
    } catch {
      setSelectedRoleIds([]);
    }
  };

  const refreshUserRoleLabels = async (userList: User[], roles: Role[]) => {
    const roleMap = new Map(roles.map((r) => [r.id, r.display_name]));
    const entries = await Promise.all(
      userList.map(async (userItem) => {
        try {
          const res = await accessControlAPI.getUserRoles(userItem.id);
          const label = (res.data.role_ids || [])
            .map((id: number) => roleMap.get(id))
            .filter(Boolean)
            .join(', ');
          return [userItem.id, label || '—'] as const;
        } catch {
          return [userItem.id, '—'] as const;
        }
      })
    );
    setUserRoleLabels(Object.fromEntries(entries));
  };

  useEffect(() => {
    const init = async () => {
      setRolesLoading(true);
      try {
        const res = await accessControlAPI.listRoles();
        const activeRoles = (res.data as Role[]).filter((r) => r.is_active);
        setRbacRoles(activeRoles);
        await fetchUsers(activeRoles);
      } catch {
        setRbacRoles([]);
        await fetchUsers([]);
      } finally {
        setRolesLoading(false);
      }
    };
    void init();
  }, []);

  const fetchUsers = async (rolesForLabels: Role[] = rbacRoles) => {
    try {
      const response = await usersAPI.list();
      setUsers(response.data);
      if (rolesForLabels.length) {
        await refreshUserRoleLabels(response.data, rolesForLabels);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    setRoleAssignWarning('');
    if (!selectedRoleIds.length) {
      setError(t('users.rolesRequired'));
      return;
    }
    try {
      const selectedCodes = selectedRoleIds
        .map((id) => rbacRoles.find((r) => r.id === id)?.code)
        .filter((code): code is string => Boolean(code));
      const legacyRole = deriveLegacyRoleFromRoleCodes(selectedCodes);
      const res = await usersAPI.create({ ...formData, role: legacyRole });
      const created = res.data as User;
      try {
        await accessControlAPI.updateUserRoles(created.id, { role_ids: selectedRoleIds });
      } catch (roleErr: any) {
        const detail = roleErr.response?.data?.detail;
        setRoleAssignWarning(
          typeof detail === 'string'
            ? t('users.rolesAssignFailed', { detail })
            : t('users.rolesAssignFailedGeneric')
        );
        fetchUsers();
        return;
      }
      setCreateDialogOpen(false);
      resetForm();
      fetchUsers();
    } catch (err: any) {
      // Handle validation errors (Pydantic returns array of error objects)
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          const errorMessages = detail.map((e: any) => 
            `${e.loc?.join(' -> ') || 'Field'}: ${e.msg}`
          ).join('; ');
          setError(errorMessages);
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError('Failed to create user - invalid data');
        }
      } else {
        setError('Failed to create user');
      }
    }
  };

  const handleEditUser = async () => {
    if (!selectedUser) return;
    
    try {
      const updateData: Record<string, unknown> = { ...formData };
      if (!updateData.password || String(updateData.password).trim() === '') {
        delete updateData.password;
      }
      const selectedCodes = selectedRoleIds
        .map((id) => rbacRoles.find((r) => r.id === id)?.code)
        .filter((code): code is string => Boolean(code));
      updateData.role = deriveLegacyRoleFromRoleCodes(selectedCodes);
      
      await usersAPI.update(selectedUser.id, updateData);
      if (canEdit) {
        try {
          await accessControlAPI.updateUserRoles(selectedUser.id, { role_ids: selectedRoleIds });
        } catch (roleErr: any) {
          const detail = roleErr.response?.data?.detail;
          setError(
            typeof detail === 'string'
              ? detail
              : t('accessControl.saveUserRolesFailed')
          );
          return;
        }
      }
      setEditDialogOpen(false);
      setSelectedUser(null);
      resetForm();
      fetchUsers();
    } catch (err: any) {
      // Handle validation errors (Pydantic returns array of error objects)
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          const errorMessages = detail.map((e: any) => 
            `${e.loc?.join(' -> ') || 'Field'}: ${e.msg}`
          ).join('; ');
          setError(errorMessages);
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError('Failed to update user - invalid data');
        }
      } else {
        setError('Failed to update user');
      }
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await usersAPI.delete(userId);
      fetchUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  const resetForm = () => {
    setFormData({
      username: '',
      password: '',
      is_active: true,
    });
    setSelectedRoleIds([]);
    setRoleAssignWarning('');
  };

  const openCreateDialog = () => {
    resetForm();
    void loadRbacRoles();
    setCreateDialogOpen(true);
  };

  const openEditDialog = (userItem: User) => {
    setSelectedUser(userItem);
    setFormData({
      username: userItem.username,
      password: '',
      is_active: userItem.is_active,
    });
    void loadRbacRoles();
    void loadUserRbacRoles(userItem.id);
    setEditDialogOpen(true);
  };

  const formatDate = (dateString: string) => {
    return formatDisplayDate(dateString);
  };

  if (!canView) {
    return (
      <Alert severity="error">{t('accessControl.featureAccessDenied')}</Alert>
    );
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {!embedded && (
        <RivarPageHeader
          title={t('navigation.users')}
          actions={
            <>
              <Button variant="outlined" size="small" startIcon={<RefreshIcon sx={{ fontSize: 15 }} />} onClick={fetchUsers}>{t('common.refresh')}</Button>
              {canCreate && (
                <Button variant="contained" size="small" startIcon={<AddIcon sx={{ fontSize: 15 }} />} onClick={openCreateDialog}>{t('users.addUser')}</Button>
              )}
            </>
          }
        />
      )}
      {embedded && (
        <Box display="flex" justifyContent="flex-end" gap={1} mb={2}>
          <Button variant="outlined" size="small" startIcon={<RefreshIcon sx={{ fontSize: 15 }} />} onClick={fetchUsers}>{t('common.refresh')}</Button>
          {canCreate && (
            <Button variant="contained" size="small" startIcon={<AddIcon sx={{ fontSize: 15 }} />} onClick={openCreateDialog}>{t('users.addUser')}</Button>
          )}
        </Box>
      )}

      {roleAssignWarning && (
        <Alert severity="warning" sx={{ mb: 2 }} onClose={() => setRoleAssignWarning('')}>
          {roleAssignWarning}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('users.username')}</TableCell>
              <TableCell>{t('users.roles')}</TableCell>
              <TableCell align="center">{t('users.active')}</TableCell>
              <TableCell>{t('users.created')}</TableCell>
              <TableCell align="center">{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((userItem) => (
              <TableRow key={userItem.id}>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {userItem.username}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {userRoleLabels[userItem.id] || '—'}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Chip 
                    label={userItem.is_active ? t('users.active') : t('users.inactive')}
                    color={userItem.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {formatDate(userItem.created_at)}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  {canEdit && (
                    <IconButton
                      size="small"
                      onClick={() => openEditDialog(userItem)}
                      title={t('common.edit')}
                    >
                      <EditIcon />
                    </IconButton>
                  )}
                  {canDelete && (
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteUser(userItem.id)}
                      title={t('common.delete')}
                      color="error"
                      disabled={userItem.id === user?.id}
                    >
                      <DeleteIcon />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create User Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('users.createUser')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('users.username')}
            fullWidth
            variant="outlined"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('users.password')}
            type="password"
            fullWidth
            variant="outlined"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>{t('users.roles')}</InputLabel>
            <Select
              multiple
              value={selectedRoleIds}
              label={t('users.roles')}
              onChange={(e) => setSelectedRoleIds(e.target.value as number[])}
              disabled={rolesLoading}
              renderValue={(selected) =>
                selected
                  .map((id) => rbacRoles.find((r) => r.id === id)?.display_name || String(id))
                  .join(', ')
              }
            >
              {rbacRoles.map((role) => (
                <MenuItem key={role.id} value={role.id}>
                  {role.display_name}
                  {role.is_system ? '' : ` (${role.code})`}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              />
            }
            label={t('users.active')}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleCreateUser} variant="contained">
            {t('users.createUser')}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('users.editUser')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('users.username')}
            fullWidth
            variant="outlined"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            sx={{ mb: 2 }}
            disabled={!canEdit}
          />
          <TextField
            margin="dense"
            label={t('users.passwordLeaveBlank')}
            type="password"
            fullWidth
            variant="outlined"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            sx={{ mb: 2 }}
            disabled={!canEdit}
          />
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>{t('users.roles')}</InputLabel>
            <Select
              multiple
              value={selectedRoleIds}
              label={t('users.roles')}
              onChange={(e) => setSelectedRoleIds(e.target.value as number[])}
              disabled={rolesLoading || !canEdit}
              renderValue={(selected) =>
                selected
                  .map((id) => rbacRoles.find((r) => r.id === id)?.display_name || String(id))
                  .join(', ')
              }
            >
              {rbacRoles.map((role) => (
                <MenuItem key={role.id} value={role.id}>
                  {role.display_name}
                  {role.is_system ? '' : ` (${role.code})`}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              />
            }
            label={t('users.active')}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>{t('common.cancel')}</Button>
          {canEdit && (
            <Button onClick={handleEditUser} variant="contained">
              {t('users.updateUser')}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};
