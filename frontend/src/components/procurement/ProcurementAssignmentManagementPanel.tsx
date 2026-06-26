import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Assignment as AssignmentIcon,
  Cancel as CancelIcon,
  CheckCircle as CompleteIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import {
  itemsAPI,
  procurementAssignmentsAPI,
  projectsAPI,
  usersAPI,
} from '../../services/api.ts';
import type { Project, ProjectItem, User } from '../../types/index.ts';
import type {
  ProcurementAssignment,
  ProcurementAssignmentScope,
  ProcurementAssignmentStatus,
} from '../../types/procurementAssignments.ts';
import { useAuth } from '../../contexts/AuthContext.tsx';
import {
  canCancelProcurementAssignments,
  canCompleteProcurementAssignments,
  canCreateProcurementAssignments,
  canEditProcurementAssignments,
  canViewProcurementAssignments,
} from '../../utils/permissions.ts';
import { formatApiError } from '../../utils/errorUtils.ts';
import { ProcurementAssigneePicker } from './ProcurementAssigneePicker.tsx';
import { filterProcurementCapableUsers } from '../../utils/procurementAssigneeUtils.ts';

type StatusFilter = 'active' | 'all' | ProcurementAssignmentStatus;
type CreateScope = 'project' | 'project_item';

interface ProcurementAssignmentManagementPanelProps {
  initialProjectId?: number | null;
}

function statusLabelKey(status: ProcurementAssignmentStatus): string {
  const map: Record<ProcurementAssignmentStatus, string> = {
    active: 'procurementAssignments.statusActive',
    completed: 'procurementAssignments.statusCompleted',
    cancelled: 'procurementAssignments.statusCancelled',
  };
  return map[status];
}

function statusChipColor(status: ProcurementAssignmentStatus): 'success' | 'default' | 'warning' {
  if (status === 'active') return 'success';
  if (status === 'completed') return 'default';
  return 'warning';
}

export const ProcurementAssignmentManagementPanel: React.FC<
  ProcurementAssignmentManagementPanelProps
> = ({ initialProjectId = null }) => {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<ProcurementAssignment[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectItems, setProjectItems] = useState<ProjectItem[]>([]);
  const [usersById, setUsersById] = useState<Record<number, User>>({});
  const [loading, setLoading] = useState(true);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('active');
  const [projectFilter, setProjectFilter] = useState<number | ''>(initialProjectId ?? '');
  const [assigneeFilter, setAssigneeFilter] = useState<number | ''>('');
  const [scopeFilter, setScopeFilter] = useState<ProcurementAssignmentScope | ''>('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [completeDialogOpen, setCompleteDialogOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<ProcurementAssignment | null>(null);
  const [createProjectId, setCreateProjectId] = useState<number | ''>(initialProjectId ?? '');
  const [createScope, setCreateScope] = useState<CreateScope>('project');
  const [selectedItemIds, setSelectedItemIds] = useState<number[]>([]);
  const [assigneeIds, setAssigneeIds] = useState<number[]>([]);
  const [note, setNote] = useState('');
  const [cancelReason, setCancelReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const projectsById = useMemo(() => {
    const map: Record<number, Project> = {};
    projects.forEach((p) => {
      map[p.id] = p;
    });
    return map;
  }, [projects]);

  const itemLabelById = useMemo(() => {
    const map: Record<number, string> = {};
    projectItems.forEach((item) => {
      map[item.id] = `${item.item_code} — ${item.item_name}`;
    });
    return map;
  }, [projectItems]);

  const assigneeOptions = useMemo(
    () => filterProcurementCapableUsers(Object.values(usersById)),
    [usersById]
  );

  const formatDate = (value?: string | null) => {
    if (!value) return '—';
    try {
      const d = new Date(value);
      return i18n.language?.startsWith('fa')
        ? d.toLocaleDateString('fa-IR')
        : d.toLocaleDateString();
    } catch {
      return value;
    }
  };

  const loadProjects = useCallback(async () => {
    try {
      const response = await projectsAPI.list({ limit: 500 });
      setProjects(response.data || []);
    } catch {
      /* optional labels */
    }
  }, []);

  const loadUsers = useCallback(async () => {
    try {
      const response = await usersAPI.list({ limit: 500 });
      const map: Record<number, User> = {};
      (response.data || []).forEach((u: User) => {
        map[u.id] = u;
      });
      setUsersById(map);
    } catch {
      /* best-effort labels */
    }
  }, []);

  const loadAssignments = useCallback(async () => {
    if (!canViewProcurementAssignments(user)) return;
    try {
      setLoading(true);
      const params: {
        status?: string;
        project_id?: number;
        assignee_user_id?: number;
        assignment_scope?: ProcurementAssignmentScope;
      } = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (projectFilter !== '') params.project_id = projectFilter;
      if (assigneeFilter !== '') params.assignee_user_id = assigneeFilter;
      if (scopeFilter !== '') params.assignment_scope = scopeFilter;
      const response = await procurementAssignmentsAPI.list(params);
      setAssignments(response.data || []);
      setError('');
    } catch (err: unknown) {
      setError(formatApiError(err, t('procurementAssignments.failedToLoad')));
    } finally {
      setLoading(false);
    }
  }, [assigneeFilter, projectFilter, scopeFilter, statusFilter, t, user]);

  const loadProjectItems = useCallback(async (projectId: number) => {
    try {
      setItemsLoading(true);
      const response = await itemsAPI.listByProject(projectId, { limit: 500 });
      const rows = response.data?.items || response.data || [];
      setProjectItems(Array.isArray(rows) ? rows : []);
    } catch (err: unknown) {
      setError(formatApiError(err, t('procurementAssignments.failedToLoadProjectItems')));
    } finally {
      setItemsLoading(false);
    }
  }, [t]);

  useEffect(() => {
    loadProjects();
    loadUsers();
  }, [loadProjects, loadUsers]);

  useEffect(() => {
    loadAssignments();
  }, [loadAssignments]);

  useEffect(() => {
    if (projectFilter !== '') {
      loadProjectItems(projectFilter);
    }
  }, [projectFilter, loadProjectItems]);

  useEffect(() => {
    if (initialProjectId != null) {
      setProjectFilter(initialProjectId);
      setCreateProjectId(initialProjectId);
    }
  }, [initialProjectId]);

  useEffect(() => {
    if (createDialogOpen && createProjectId !== '' && createScope === 'project_item') {
      loadProjectItems(createProjectId);
    }
  }, [createDialogOpen, createProjectId, createScope, loadProjectItems]);

  if (!canViewProcurementAssignments(user)) {
    return <Alert severity="warning">{t('procurementAssignments.accessDenied')}</Alert>;
  }

  const userLabel = (id: number) => usersById[id]?.username || `#${id}`;
  const projectLabel = (id: number) => {
    const project = projectsById[id];
    return project ? `${project.project_code} — ${project.name}` : `#${id}`;
  };

  const mapDuplicateError = (err: unknown, fallback: string) => {
    const msg = formatApiError(err, fallback);
    return err &&
      typeof err === 'object' &&
      (err as { response?: { status?: number } }).response?.status === 409
      ? t('procurementAssignments.duplicateAssignment')
      : msg;
  };

  const handleCreate = async () => {
    if (assigneeIds.length === 0 || createProjectId === '') return;
    if (createScope === 'project_item' && selectedItemIds.length === 0) return;

    setSubmitting(true);
    setError('');
    try {
      if (createScope === 'project') {
        for (const assigneeId of assigneeIds) {
          await procurementAssignmentsAPI.create({
            project_id: createProjectId,
            assignee_user_id: assigneeId,
            note: note || undefined,
          });
        }
      } else {
        await procurementAssignmentsAPI.bulkCreate({
          project_id: createProjectId,
          assignee_user_ids: assigneeIds,
          project_item_ids: selectedItemIds,
          note: note || undefined,
        });
      }
      setCreateDialogOpen(false);
      setAssigneeIds([]);
      setSelectedItemIds([]);
      setNote('');
      setSuccess(t('procurementAssignments.createSuccess'));
      await loadAssignments();
    } catch (err: unknown) {
      setError(mapDuplicateError(err, t('procurementAssignments.createFailed')));
    } finally {
      setSubmitting(false);
    }
  };

  const handleComplete = async () => {
    if (!selectedAssignment) return;
    setSubmitting(true);
    try {
      await procurementAssignmentsAPI.complete(selectedAssignment.id);
      setCompleteDialogOpen(false);
      setSelectedAssignment(null);
      setSuccess(t('procurementAssignments.completeSuccess'));
      await loadAssignments();
    } catch (err: unknown) {
      setError(formatApiError(err, t('procurementAssignments.actionFailed')));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async () => {
    if (!selectedAssignment || !cancelReason.trim()) return;
    setSubmitting(true);
    try {
      await procurementAssignmentsAPI.cancel(selectedAssignment.id, {
        cancelled_reason: cancelReason.trim(),
      });
      setCancelDialogOpen(false);
      setSelectedAssignment(null);
      setCancelReason('');
      setSuccess(t('procurementAssignments.cancelSuccess'));
      await loadAssignments();
    } catch (err: unknown) {
      setError(formatApiError(err, t('procurementAssignments.actionFailed')));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap" gap={1}>
        <Typography variant="h6" display="flex" alignItems="center" gap={1}>
          <AssignmentIcon fontSize="small" />
          {t('procurementAssignments.managementTitle')}
        </Typography>
        {canCreateProcurementAssignments(user) && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateDialogOpen(true)}>
            {t('procurementAssignments.assignProcurementUser')}
          </Button>
        )}
      </Box>

      <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>{t('procurementAssignments.selectProject')}</InputLabel>
          <Select
            value={projectFilter}
            label={t('procurementAssignments.selectProject')}
            onChange={(e) => setProjectFilter(e.target.value === '' ? '' : Number(e.target.value))}
          >
            <MenuItem value="">{t('procurementAssignments.allProjects')}</MenuItem>
            {projects.map((project) => (
              <MenuItem key={project.id} value={project.id}>
                {project.project_code} — {project.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>{t('procurementAssignments.statusFilter')}</InputLabel>
          <Select
            value={statusFilter}
            label={t('procurementAssignments.statusFilter')}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          >
            <MenuItem value="active">{t('procurementAssignments.statusActive')}</MenuItem>
            <MenuItem value="completed">{t('procurementAssignments.statusCompleted')}</MenuItem>
            <MenuItem value="cancelled">{t('procurementAssignments.statusCancelled')}</MenuItem>
            <MenuItem value="all">{t('procurementAssignments.assignmentHistory')}</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>{t('procurementAssignments.assignedUser')}</InputLabel>
          <Select
            value={assigneeFilter}
            label={t('procurementAssignments.assignedUser')}
            onChange={(e) => setAssigneeFilter(e.target.value === '' ? '' : Number(e.target.value))}
          >
            <MenuItem value="">{t('procurementAssignments.allAssignees')}</MenuItem>
            {assigneeOptions.map((assignee) => (
              <MenuItem key={assignee.id} value={assignee.id}>
                {assignee.username}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>{t('procurementAssignments.assignmentScope')}</InputLabel>
          <Select
            value={scopeFilter}
            label={t('procurementAssignments.assignmentScope')}
            onChange={(e) =>
              setScopeFilter(e.target.value === '' ? '' : (e.target.value as ProcurementAssignmentScope))
            }
          >
            <MenuItem value="">{t('procurementAssignments.allScopes')}</MenuItem>
            <MenuItem value="project">{t('procurementAssignments.projectAssignment')}</MenuItem>
            <MenuItem value="project_item">{t('procurementAssignments.itemAssignment')}</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress size={32} />
        </Box>
      ) : assignments.length === 0 ? (
        <Alert severity="info">{t('procurementAssignments.noAssignments')}</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('procurementAssignments.project')}</TableCell>
                <TableCell>{t('procurementAssignments.scope')}</TableCell>
                <TableCell>{t('procurementAssignments.item')}</TableCell>
                <TableCell>{t('procurementAssignments.assignedUser')}</TableCell>
                <TableCell>{t('procurementAssignments.assignedBy')}</TableCell>
                <TableCell>{t('procurementAssignments.assignmentStatus')}</TableCell>
                <TableCell>{t('procurementAssignments.createdAt')}</TableCell>
                <TableCell>{t('procurementAssignments.assignmentNote')}</TableCell>
                {(canCompleteProcurementAssignments(user) || canCancelProcurementAssignments(user)) && (
                  <TableCell align="right">{t('procurement.actions')}</TableCell>
                )}
              </TableRow>
            </TableHead>
            <TableBody>
              {assignments.map((row) => (
                <TableRow key={row.id}>
                  <TableCell>{projectLabel(row.project_id)}</TableCell>
                  <TableCell>
                    {row.assignment_scope === 'project'
                      ? t('procurementAssignments.projectAssignment')
                      : t('procurementAssignments.itemAssignment')}
                  </TableCell>
                  <TableCell>
                    {row.project_item_id
                      ? itemLabelById[row.project_item_id] || `#${row.project_item_id}`
                      : '—'}
                  </TableCell>
                  <TableCell>{userLabel(row.assignee_user_id)}</TableCell>
                  <TableCell>{userLabel(row.assigned_by_user_id)}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={t(statusLabelKey(row.status))}
                      color={statusChipColor(row.status)}
                    />
                  </TableCell>
                  <TableCell>{formatDate(row.created_at)}</TableCell>
                  <TableCell>{row.note || '—'}</TableCell>
                  {(canCompleteProcurementAssignments(user) || canCancelProcurementAssignments(user)) && (
                    <TableCell align="right">
                      {row.status === 'active' && (
                        <Box display="flex" gap={0.5} justifyContent="flex-end">
                          {canCompleteProcurementAssignments(user) && (
                            <Button
                              size="small"
                              startIcon={<CompleteIcon />}
                              onClick={() => {
                                setSelectedAssignment(row);
                                setCompleteDialogOpen(true);
                              }}
                            >
                              {t('procurementAssignments.complete')}
                            </Button>
                          )}
                          {canCancelProcurementAssignments(user) && (
                            <Button
                              size="small"
                              color="warning"
                              startIcon={<CancelIcon />}
                              onClick={() => {
                                setSelectedAssignment(row);
                                setCancelDialogOpen(true);
                              }}
                            >
                              {t('procurementAssignments.cancel')}
                            </Button>
                          )}
                        </Box>
                      )}
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('procurementAssignments.assignProcurementUser')}</DialogTitle>
        <DialogContent>
          <Box pt={1} display="flex" flexDirection="column" gap={2}>
            <FormControl fullWidth>
              <InputLabel>{t('procurementAssignments.selectProject')}</InputLabel>
              <Select
                value={createProjectId}
                label={t('procurementAssignments.selectProject')}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setCreateProjectId(next);
                  setSelectedItemIds([]);
                }}
              >
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.project_code} — {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>{t('procurementAssignments.assignmentScope')}</InputLabel>
              <Select
                value={createScope}
                label={t('procurementAssignments.assignmentScope')}
                onChange={(e) => {
                  setCreateScope(e.target.value as CreateScope);
                  setSelectedItemIds([]);
                }}
              >
                <MenuItem value="project">{t('procurementAssignments.projectAssignment')}</MenuItem>
                <MenuItem value="project_item">{t('procurementAssignments.itemAssignment')}</MenuItem>
              </Select>
            </FormControl>
            {createScope === 'project_item' && (
              <FormControl fullWidth disabled={createProjectId === '' || itemsLoading}>
                <InputLabel>{t('procurementAssignments.selectProjectItems')}</InputLabel>
                <Select
                  multiple
                  value={selectedItemIds}
                  onChange={(e) => {
                    const value = e.target.value;
                    setSelectedItemIds(typeof value === 'string' ? value.split(',').map(Number) : value);
                  }}
                  input={<OutlinedInput label={t('procurementAssignments.selectProjectItems')} />}
                  renderValue={(selected) =>
                    selected
                      .map((id) => itemLabelById[id] || `#${id}`)
                      .join(', ')
                  }
                >
                  {projectItems.map((item) => (
                    <MenuItem key={item.id} value={item.id}>
                      <ListItemText primary={`${item.item_code} — ${item.item_name}`} />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            <ProcurementAssigneePicker
              value={assigneeIds}
              onChange={setAssigneeIds}
              label={t('procurementAssignments.selectProcurementUsers')}
            />
            {canEditProcurementAssignments(user) && (
              <TextField
                label={t('procurementAssignments.assignmentNote')}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                multiline
                minRows={2}
                fullWidth
              />
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>{t('procurement.cancel')}</Button>
          <Button
            variant="contained"
            disabled={
              submitting ||
              assigneeIds.length === 0 ||
              createProjectId === '' ||
              (createScope === 'project_item' && selectedItemIds.length === 0)
            }
            onClick={handleCreate}
          >
            {t('procurementAssignments.assignProcurementUser')}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={completeDialogOpen} onClose={() => setCompleteDialogOpen(false)}>
        <DialogTitle>{t('procurementAssignments.completeAssignment')}</DialogTitle>
        <DialogContent>
          <Typography>{t('procurementAssignments.confirmComplete')}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompleteDialogOpen(false)}>{t('procurement.cancel')}</Button>
          <Button variant="contained" onClick={handleComplete} disabled={submitting}>
            {t('procurement.confirm')}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={cancelDialogOpen} onClose={() => setCancelDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('procurementAssignments.cancelAssignment')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('procurementAssignments.cancelReason')}
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            fullWidth
            multiline
            minRows={2}
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialogOpen(false)}>{t('procurement.cancel')}</Button>
          <Button
            color="warning"
            variant="contained"
            onClick={handleCancel}
            disabled={submitting || !cancelReason.trim()}
          >
            {t('procurementAssignments.cancelAssignment')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
