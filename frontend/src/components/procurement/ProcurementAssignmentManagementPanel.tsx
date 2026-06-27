import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Select,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Assignment as AssignmentIcon,
  RemoveCircleOutline as RemoveIcon,
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
  canCreateProcurementAssignments,
  canEditProcurementAssignments,
  canViewProcurementAssignments,
} from '../../utils/permissions.ts';
import { formatApiError } from '../../utils/errorUtils.ts';
import { ProcurementAssigneePicker } from './ProcurementAssigneePicker.tsx';
import { filterProcurementCapableUsers } from '../../utils/procurementAssigneeUtils.ts';
import {
  cancelAssignmentsInBulk,
  getAssignableProjectItemIds,
  isSelectableForRemoval,
  type WorkbenchViewMode,
} from '../../utils/procurementAssignmentWorkbenchUtils.ts';
import { ProcurementAssignmentProjectView } from './ProcurementAssignmentProjectView.tsx';
import { ProcurementAssignmentItemView } from './ProcurementAssignmentItemView.tsx';

type StatusFilter = 'active' | 'all' | ProcurementAssignmentStatus;
type CreateScope = 'project' | 'project_item';

interface ProcurementAssignmentManagementPanelProps {
  initialProjectId?: number | null;
}

export const ProcurementAssignmentManagementPanel: React.FC<
  ProcurementAssignmentManagementPanelProps
> = ({ initialProjectId = null }) => {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<ProcurementAssignment[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [itemsByProjectId, setItemsByProjectId] = useState<Record<number, ProjectItem[]>>({});
  const [usersById, setUsersById] = useState<Record<number, User>>({});
  const [loading, setLoading] = useState(true);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [viewMode, setViewMode] = useState<WorkbenchViewMode>('project');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('active');
  const [projectFilter, setProjectFilter] = useState<number | ''>(initialProjectId ?? '');
  const [assigneeFilter, setAssigneeFilter] = useState<number | ''>('');
  const [scopeFilter, setScopeFilter] = useState<ProcurementAssignmentScope | ''>('');
  const [itemSearch, setItemSearch] = useState('');
  const [expandedProjectId, setExpandedProjectId] = useState<number | null>(initialProjectId);
  const [selectedAssignmentIds, setSelectedAssignmentIds] = useState<number[]>([]);
  const [selectedItemIdsForAssign, setSelectedItemIdsForAssign] = useState<number[]>([]);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [removeTargetIds, setRemoveTargetIds] = useState<number[]>([]);
  const [createProjectId, setCreateProjectId] = useState<number | ''>(initialProjectId ?? '');
  const [createScope, setCreateScope] = useState<CreateScope>('project_item');
  const [createItemIds, setCreateItemIds] = useState<number[]>([]);
  const [assigneeIds, setAssigneeIds] = useState<number[]>([]);
  const [note, setNote] = useState('');
  const [removeReason, setRemoveReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [bulkRemoveSummary, setBulkRemoveSummary] = useState('');

  const projectsById = useMemo(() => {
    const map: Record<number, Project> = {};
    projects.forEach((p) => {
      map[p.id] = p;
    });
    return map;
  }, [projects]);

  const itemLabelById = useMemo(() => {
    const map: Record<number, string> = {};
    Object.values(itemsByProjectId).forEach((items) => {
      items.forEach((item) => {
        map[item.id] = `${item.item_code} — ${item.item_name}`;
      });
    });
    return map;
  }, [itemsByProjectId]);

  const assignmentById = useMemo(() => {
    const map: Record<number, ProcurementAssignment> = {};
    assignments.forEach((assignment) => {
      map[assignment.id] = assignment;
    });
    return map;
  }, [assignments]);

  const assigneeOptions = useMemo(
    () => filterProcurementCapableUsers(Object.values(usersById)),
    [usersById]
  );

  const createDialogItems = useMemo(() => {
    if (createProjectId === '') return [];
    return itemsByProjectId[createProjectId] || [];
  }, [createProjectId, itemsByProjectId]);

  const removableSelectedIds = useMemo(
    () => {
      return selectedAssignmentIds.filter((assignmentId) => {
        const assignment = assignmentById[assignmentId];
        return assignment ? isSelectableForRemoval(assignment) : false;
      });
    },
    [assignmentById, selectedAssignmentIds]
  );

  const selectedAssignableCount = selectedItemIdsForAssign.length;
  const selectedRemovableCount = removableSelectedIds.length;

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
      /* optional */
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
      /* optional */
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
      setItemsByProjectId((prev) => {
        if (prev[projectId]?.length) return prev;
        return {
          ...prev,
          [projectId]: Array.isArray(rows) ? rows : [],
        };
      });
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
    if (initialProjectId != null) {
      setProjectFilter(initialProjectId);
      setCreateProjectId(initialProjectId);
      setExpandedProjectId(initialProjectId);
      loadProjectItems(initialProjectId);
    }
  }, [initialProjectId, loadProjectItems]);

  useEffect(() => {
    if (expandedProjectId != null) {
      loadProjectItems(expandedProjectId);
    }
  }, [expandedProjectId, loadProjectItems]);

  useEffect(() => {
    if (createDialogOpen && createProjectId !== '') {
      loadProjectItems(createProjectId);
    }
  }, [createDialogOpen, createProjectId, loadProjectItems]);

  useEffect(() => {
    if (viewMode !== 'item') return;
    const projectIds = Array.from(new Set(assignments.map((a) => a.project_id)));
    projectIds.forEach((projectId) => {
      loadProjectItems(projectId);
    });
  }, [assignments, loadProjectItems, viewMode]);

  useEffect(() => {
    if (expandedProjectId == null || selectedItemIdsForAssign.length === 0) return;
    const projectItems = itemsByProjectId[expandedProjectId] || [];
    const assignableIds = new Set(
      getAssignableProjectItemIds(
        expandedProjectId,
        projectItems.map((item) => item.id),
        assignments
      )
    );
    setSelectedItemIdsForAssign((prev) => prev.filter((id) => assignableIds.has(id)));
  }, [assignments, expandedProjectId, itemsByProjectId, selectedItemIdsForAssign.length]);

  if (!canViewProcurementAssignments(user)) {
    return <Alert severity="warning">{t('procurementAssignments.accessDenied')}</Alert>;
  }

  const canCreate = canCreateProcurementAssignments(user);
  const canCancel = canCancelProcurementAssignments(user);

  const mapDuplicateError = (err: unknown, fallback: string) => {
    const msg = formatApiError(err, fallback);
    return err &&
      typeof err === 'object' &&
      (err as { response?: { status?: number } }).response?.status === 409
      ? t('procurementAssignments.duplicateAssignment')
      : msg;
  };

  const clearSelection = () => {
    setSelectedAssignmentIds([]);
    setSelectedItemIdsForAssign([]);
  };

  const openRemoveDialog = (ids: number[]) => {
    const removableIds = Array.from(
      new Set(
        ids.filter((assignmentId) => {
          const assignment = assignmentById[assignmentId];
          return assignment ? isSelectableForRemoval(assignment) : false;
        })
      )
    );
    if (removableIds.length === 0) {
      setError(t('procurementAssignments.noActiveAssignmentsSelected'));
      return;
    }
    setRemoveTargetIds(removableIds);
    setRemoveReason('');
    setBulkRemoveSummary('');
    setRemoveDialogOpen(true);
  };

  const handleCreate = async () => {
    if (assigneeIds.length === 0 || createProjectId === '') return;
    if (createScope === 'project_item' && createItemIds.length === 0) return;

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
          project_item_ids: createItemIds,
          note: note || undefined,
        });
      }
      setCreateDialogOpen(false);
      setAssigneeIds([]);
      setCreateItemIds([]);
      setNote('');
      setSuccess(t('procurementAssignments.createSuccess'));
      clearSelection();
      await loadAssignments();
    } catch (err: unknown) {
      setError(mapDuplicateError(err, t('procurementAssignments.createFailed')));
    } finally {
      setSubmitting(false);
    }
  };

  const handleBulkRemove = async () => {
    if (removeTargetIds.length === 0 || !removeReason.trim()) return;
    setSubmitting(true);
    setError('');
    try {
      const result = await cancelAssignmentsInBulk(
        removeTargetIds,
        removeReason.trim(),
        (id, payload) => procurementAssignmentsAPI.cancel(id, payload)
      );
      setBulkRemoveSummary(
        t('procurementAssignments.bulkRemoveSummary', {
          success: result.successCount,
          failed: result.failureCount,
        }) +
          (result.failedIds.length > 0
            ? ` ${t('procurementAssignments.bulkRemoveFailedIds', {
                ids: result.failedIds.join(', '),
              })}`
            : '')
      );
      if (result.failureCount === 0) {
        setRemoveDialogOpen(false);
        setSuccess(
          t('procurementAssignments.bulkRemoveSummary', {
            success: result.successCount,
            failed: result.failureCount,
          })
        );
        clearSelection();
        await loadAssignments();
      } else if (result.successCount > 0) {
        clearSelection();
        await loadAssignments();
      }
    } catch (err: unknown) {
      setError(formatApiError(err, t('procurementAssignments.actionFailed')));
    } finally {
      setSubmitting(false);
    }
  };

  const handleAssignAllItems = (projectId: number) => {
    const items = itemsByProjectId[projectId] || [];
    const assignableItemIds = getAssignableProjectItemIds(
      projectId,
      items.map((item) => item.id),
      assignments
    );
    if (assignableItemIds.length === 0) {
      setError(t('procurementAssignments.noAssignableItemsSelected'));
      return;
    }
    setCreateProjectId(projectId);
    setCreateScope('project_item');
    setCreateItemIds(assignableItemIds);
    setAssigneeIds([]);
    setNote('');
    setCreateDialogOpen(true);
  };

  const handleAssignSelectedItems = (projectId: number) => {
    const assignableItemIds = getAssignableProjectItemIds(
      projectId,
      selectedItemIdsForAssign,
      assignments
    );
    if (assignableItemIds.length === 0) {
      setError(t('procurementAssignments.noAssignableItemsSelected'));
      return;
    }
    setCreateProjectId(projectId);
    setCreateScope('project_item');
    setCreateItemIds(assignableItemIds);
    setAssigneeIds([]);
    setNote('');
    setCreateDialogOpen(true);
  };

  const toggleProject = (projectId: number) => {
    setExpandedProjectId((prev) => (prev === projectId ? null : projectId));
    setSelectedItemIdsForAssign([]);
  };

  const toggleAssignmentSelection = (assignmentId: number) => {
    const assignment = assignmentById[assignmentId];
    if (!assignment || !isSelectableForRemoval(assignment)) return;
    setSelectedAssignmentIds((prev) =>
      prev.includes(assignmentId)
        ? prev.filter((id) => id !== assignmentId)
        : [...prev, assignmentId]
    );
  };

  const toggleItemForAssign = (itemId: number) => {
    setSelectedItemIdsForAssign((prev) =>
      prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]
    );
  };

  const selectAllVisibleAssignments = (assignmentIds: number[]) => {
    setSelectedAssignmentIds(assignmentIds);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap" gap={1}>
        <Typography variant="h6" display="flex" alignItems="center" gap={1}>
          <AssignmentIcon fontSize="small" />
          {t('procurementAssignments.workbenchTitle')}
        </Typography>
        {canCreate && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateDialogOpen(true)}>
            {t('procurementAssignments.assignProcurementUser')}
          </Button>
        )}
      </Box>

      <Alert severity="info" sx={{ mb: 2 }}>
        {t('procurementAssignments.finalizationHint')}
      </Alert>

      <ToggleButtonGroup
        exclusive
        size="small"
        value={viewMode}
        onChange={(_, value: WorkbenchViewMode | null) => value && setViewMode(value)}
        sx={{ mb: 2 }}
      >
        <ToggleButton value="project">{t('procurementAssignments.viewByProject')}</ToggleButton>
        <ToggleButton value="item">{t('procurementAssignments.viewByItem')}</ToggleButton>
      </ToggleButtonGroup>

      <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>{t('procurementAssignments.selectProject')}</InputLabel>
          <Select
            value={projectFilter}
            label={t('procurementAssignments.selectProject')}
            onChange={(e) => {
              setProjectFilter(e.target.value === '' ? '' : Number(e.target.value));
              clearSelection();
            }}
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
            onChange={(e) => {
              setStatusFilter(e.target.value as StatusFilter);
              clearSelection();
            }}
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
            onChange={(e) => {
              setAssigneeFilter(e.target.value === '' ? '' : Number(e.target.value));
              clearSelection();
            }}
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
            onChange={(e) => {
              setScopeFilter(
                e.target.value === '' ? '' : (e.target.value as ProcurementAssignmentScope)
              );
              clearSelection();
            }}
          >
            <MenuItem value="">{t('procurementAssignments.allScopes')}</MenuItem>
            <MenuItem value="project">{t('procurementAssignments.projectLevelResponsibility')}</MenuItem>
            <MenuItem value="project_item">{t('procurementAssignments.itemAssignment')}</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {(selectedAssignableCount > 0 || (canCancel && selectedRemovableCount > 0)) && (
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          {selectedAssignableCount > 0 && (
            <Typography variant="body2">
              {t('procurementAssignments.selectedAssignableItemsCount', {
                count: selectedAssignableCount,
              })}
            </Typography>
          )}
          {canCancel && selectedRemovableCount > 0 && (
            <>
              <Typography variant="body2">
                {t('procurementAssignments.selectedRemovableAssignmentsCount', {
                  count: selectedRemovableCount,
                })}
              </Typography>
              <Button
                size="small"
                color="warning"
                variant="outlined"
                startIcon={<RemoveIcon />}
                onClick={() => openRemoveDialog(removableSelectedIds)}
              >
                {t('procurementAssignments.removeSelectedAssignments')}
              </Button>
            </>
          )}
        </Box>
      )}

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
          <Typography>{t('procurement.loading')}</Typography>
        </Box>
      ) : viewMode === 'project' ? (
        <ProcurementAssignmentProjectView
          assignments={assignments}
          projectsById={projectsById}
          usersById={usersById}
          expandedProjectId={expandedProjectId}
          onToggleProject={toggleProject}
          projectItems={expandedProjectId != null ? itemsByProjectId[expandedProjectId] || [] : []}
          itemsLoading={itemsLoading}
          selectedAssignmentIds={selectedAssignmentIds}
          onToggleAssignmentSelection={toggleAssignmentSelection}
          onSelectAllVisibleAssignments={selectAllVisibleAssignments}
          selectedItemIdsForAssign={selectedItemIdsForAssign}
          onToggleItemForAssign={toggleItemForAssign}
          canCreate={canCreate}
          canCancel={canCancel}
          onAssignAllItems={handleAssignAllItems}
          onAssignSelectedItems={handleAssignSelectedItems}
          onRemoveAssignment={(assignment) => openRemoveDialog([assignment.id])}
          formatDate={formatDate}
        />
      ) : (
        <ProcurementAssignmentItemView
          assignments={assignments}
          projectsById={projectsById}
          itemLabelById={itemLabelById}
          usersById={usersById}
          itemSearch={itemSearch}
          onItemSearchChange={setItemSearch}
          selectedAssignmentIds={selectedAssignmentIds}
          onToggleAssignmentSelection={toggleAssignmentSelection}
          onSelectAllVisibleAssignments={selectAllVisibleAssignments}
          canCancel={canCancel}
          onRemoveAssignment={(assignment) => openRemoveDialog([assignment.id])}
          formatDate={formatDate}
        />
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
                  setCreateItemIds([]);
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
                  setCreateItemIds([]);
                }}
              >
                <MenuItem value="project">{t('procurementAssignments.projectLevelResponsibility')}</MenuItem>
                <MenuItem value="project_item">{t('procurementAssignments.itemAssignment')}</MenuItem>
              </Select>
            </FormControl>
            {createScope === 'project_item' && (
              <FormControl fullWidth disabled={createProjectId === '' || itemsLoading}>
                <InputLabel>{t('procurementAssignments.selectProjectItems')}</InputLabel>
                <Select
                  multiple
                  value={createItemIds}
                  onChange={(e) => {
                    const value = e.target.value;
                    setCreateItemIds(typeof value === 'string' ? value.split(',').map(Number) : value);
                  }}
                  input={<OutlinedInput label={t('procurementAssignments.selectProjectItems')} />}
                  renderValue={(selected) =>
                    selected.map((id) => itemLabelById[id] || `#${id}`).join(', ')
                  }
                >
                  {createDialogItems.map((item) => (
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
              (createScope === 'project_item' && createItemIds.length === 0)
            }
            onClick={handleCreate}
          >
            {t('procurementAssignments.assignProcurementUser')}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={removeDialogOpen} onClose={() => setRemoveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {removeTargetIds.length > 1
            ? t('procurementAssignments.removeSelectedAssignments')
            : t('procurementAssignments.removeAssignment')}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {t('procurementAssignments.removeSelectedConfirmCount', {
              count: removeTargetIds.length,
            })}
          </Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            {t('procurementAssignments.removeAssignmentHint')}
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            label={t('procurementAssignments.removalReason')}
            value={removeReason}
            onChange={(e) => setRemoveReason(e.target.value)}
            fullWidth
            multiline
            minRows={2}
            required
          />
          {bulkRemoveSummary && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              {bulkRemoveSummary}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRemoveDialogOpen(false)}>{t('procurement.cancel')}</Button>
          <Button
            color="warning"
            variant="contained"
            onClick={handleBulkRemove}
            disabled={submitting || !removeReason.trim()}
          >
            {removeTargetIds.length > 1
              ? t('procurementAssignments.removeSelectedAssignments')
              : t('procurementAssignments.removeAssignment')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
