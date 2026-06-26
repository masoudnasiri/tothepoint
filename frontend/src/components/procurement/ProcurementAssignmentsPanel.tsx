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
  MenuItem,
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
import { procurementAssignmentsAPI, usersAPI } from '../../services/api.ts';
import type { ProjectItem, User } from '../../types/index.ts';
import type {
  ProcurementAssignment,
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

type StatusFilter = 'active' | 'all' | ProcurementAssignmentStatus;

interface ProcurementAssignmentsPanelProps {
  projectId: number;
  projectItems?: ProjectItem[];
  bulkItemIds?: number[];
  onBulkDialogConsumed?: () => void;
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

export const ProcurementAssignmentsPanel: React.FC<ProcurementAssignmentsPanelProps> = ({
  projectId,
  projectItems = [],
  bulkItemIds = [],
  onBulkDialogConsumed,
}) => {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<ProcurementAssignment[]>([]);
  const [usersById, setUsersById] = useState<Record<number, User>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('active');
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [completeDialogOpen, setCompleteDialogOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<ProcurementAssignment | null>(null);
  const [assigneeIds, setAssigneeIds] = useState<number[]>([]);
  const [note, setNote] = useState('');
  const [cancelReason, setCancelReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const itemLabelById = useMemo(() => {
    const map: Record<number, string> = {};
    projectItems.forEach((item) => {
      map[item.id] = `${item.item_code} — ${item.item_name}`;
    });
    return map;
  }, [projectItems]);

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
      const params: { status?: string } = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      const response = await procurementAssignmentsAPI.listByProject(projectId, params);
      setAssignments(response.data || []);
      setError('');
    } catch (err: unknown) {
      setError(formatApiError(err, t('procurementAssignments.failedToLoad')));
    } finally {
      setLoading(false);
    }
  }, [projectId, statusFilter, t, user]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  useEffect(() => {
    loadAssignments();
  }, [loadAssignments]);

  useEffect(() => {
    if (bulkItemIds.length > 0 && canCreateProcurementAssignments(user)) {
      setBulkDialogOpen(true);
    }
  }, [bulkItemIds, user]);

  if (!canViewProcurementAssignments(user)) {
    return <Alert severity="warning">{t('procurementAssignments.accessDenied')}</Alert>;
  }

  const userLabel = (id: number) => usersById[id]?.username || `#${id}`;

  const handleCreateProjectLevel = async () => {
    if (assigneeIds.length === 0) return;
    setSubmitting(true);
    setError('');
    try {
      for (const assigneeId of assigneeIds) {
        await procurementAssignmentsAPI.create({
          project_id: projectId,
          assignee_user_id: assigneeId,
          note: note || undefined,
        });
      }
      setProjectDialogOpen(false);
      setAssigneeIds([]);
      setNote('');
      setSuccess(t('procurementAssignments.createSuccess'));
      await loadAssignments();
    } catch (err: unknown) {
      const msg = formatApiError(err, t('procurementAssignments.createFailed'));
      setError(
        err && typeof err === 'object' && (err as { response?: { status?: number } }).response?.status === 409
          ? t('procurementAssignments.duplicateAssignment')
          : msg
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleBulkCreate = async () => {
    if (assigneeIds.length === 0 || bulkItemIds.length === 0) return;
    setSubmitting(true);
    setError('');
    try {
      await procurementAssignmentsAPI.bulkCreate({
        project_id: projectId,
        assignee_user_ids: assigneeIds,
        project_item_ids: bulkItemIds,
        note: note || undefined,
      });
      setBulkDialogOpen(false);
      setAssigneeIds([]);
      setNote('');
      onBulkDialogConsumed?.();
      setSuccess(t('procurementAssignments.bulkCreateSuccess'));
      await loadAssignments();
    } catch (err: unknown) {
      const msg = formatApiError(err, t('procurementAssignments.createFailed'));
      setError(
        err && typeof err === 'object' && (err as { response?: { status?: number } }).response?.status === 409
          ? t('procurementAssignments.duplicateAssignment')
          : msg
      );
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
          {t('procurementAssignments.title')}
        </Typography>
        <Box display="flex" gap={1} flexWrap="wrap">
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
          {canCreateProcurementAssignments(user) && (
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setProjectDialogOpen(true)}>
              {t('procurementAssignments.projectLevelAssignment')}
            </Button>
          )}
        </Box>
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
        <Alert severity="info">{t('procurementAssignments.noAssignedProcurementUsers')}</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
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
                  <TableCell>
                    {row.assignment_scope === 'project'
                      ? t('procurementAssignments.projectLevelAssignment')
                      : t('procurementAssignments.itemLevelAssignment')}
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
                              {t('procurementAssignments.completeAssignment')}
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
                              {t('procurementAssignments.cancelAssignment')}
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

      <Dialog open={projectDialogOpen} onClose={() => setProjectDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('procurementAssignments.projectLevelAssignment')}</DialogTitle>
        <DialogContent>
          <Box pt={1} display="flex" flexDirection="column" gap={2}>
            <ProcurementAssigneePicker value={assigneeIds} onChange={setAssigneeIds} />
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
          <Button onClick={() => setProjectDialogOpen(false)}>{t('procurement.cancel')}</Button>
          <Button
            variant="contained"
            disabled={submitting || assigneeIds.length === 0}
            onClick={handleCreateProjectLevel}
          >
            {t('procurementAssignments.assignProcurementUser')}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={bulkDialogOpen} onClose={() => setBulkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('procurementAssignments.assignSelectedItems')}</DialogTitle>
        <DialogContent>
          <Box pt={1} display="flex" flexDirection="column" gap={2}>
            <Typography variant="body2" color="text.secondary">
              {t('procurementAssignments.selectedItemsCount', { count: bulkItemIds.length })}
            </Typography>
            <ProcurementAssigneePicker value={assigneeIds} onChange={setAssigneeIds} />
            <TextField
              label={t('procurementAssignments.assignmentNote')}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              multiline
              minRows={2}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDialogOpen(false)}>{t('procurement.cancel')}</Button>
          <Button
            variant="contained"
            disabled={submitting || assigneeIds.length === 0 || bulkItemIds.length === 0}
            onClick={handleBulkCreate}
          >
            {t('procurementAssignments.assignSelectedItems')}
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
