import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Link,
  Paper,
  Typography,
} from '@mui/material';
import { Assignment as AssignmentIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import { procurementAssignmentsAPI, projectsAPI } from '../../services/api.ts';
import type { Project } from '../../types/index.ts';
import type { ProcurementAssignment } from '../../types/procurementAssignments.ts';
import { useAuth } from '../../contexts/AuthContext.tsx';
import { canViewProcurementAssignments, canViewProjectItems } from '../../utils/permissions.ts';
import { formatApiError } from '../../utils/errorUtils.ts';
import type { ProcurementAssignmentStatus } from '../../types/procurementAssignments.ts';
import { AssignedProcurementItemsDialog } from './AssignedProcurementItemsDialog.tsx';

function statusLabelKey(status: ProcurementAssignmentStatus): string {
  const map: Record<ProcurementAssignmentStatus, string> = {
    active: 'procurementAssignments.statusActive',
    completed: 'procurementAssignments.statusCompleted',
    cancelled: 'procurementAssignments.statusCancelled',
  };
  return map[status];
}

export const MyProcurementAssignmentsPanel: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<ProcurementAssignment[]>([]);
  const [projectsById, setProjectsById] = useState<Record<number, Project>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const [assignedItemsProjectId, setAssignedItemsProjectId] = useState<number | null>(null);
  const [assignedItemsProjectLabel, setAssignedItemsProjectLabel] = useState('');

  const load = useCallback(async () => {
    if (!user?.id || !canViewProcurementAssignments(user)) return;
    try {
      setLoading(true);
      const response = await procurementAssignmentsAPI.list({
        assignee_user_id: user.id,
        status: showHistory ? undefined : 'active',
      });
      setAssignments(response.data || []);
      setError('');
    } catch (err: unknown) {
      setError(formatApiError(err, t('procurementAssignments.failedToLoad')));
    } finally {
      setLoading(false);
    }
  }, [showHistory, t, user]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    (async () => {
      try {
        const response = await projectsAPI.list({ limit: 500 });
        const map: Record<number, Project> = {};
        (response.data || []).forEach((p: Project) => {
          map[p.id] = p;
        });
        setProjectsById(map);
      } catch {
        /* labels optional */
      }
    })();
  }, []);

  const grouped = useMemo(() => {
    const byProject: Record<number, { project: ProcurementAssignment[]; items: ProcurementAssignment[] }> = {};
    assignments.forEach((a) => {
      if (!byProject[a.project_id]) {
        byProject[a.project_id] = { project: [], items: [] };
      }
      if (a.assignment_scope === 'project') {
        byProject[a.project_id].project.push(a);
      } else {
        byProject[a.project_id].items.push(a);
      }
    });
    return byProject;
  }, [assignments]);

  if (!canViewProcurementAssignments(user)) {
    return null;
  }

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1} flexWrap="wrap" gap={1}>
        <Typography variant="h6" display="flex" alignItems="center" gap={1}>
          <AssignmentIcon fontSize="small" />
          {t('procurementAssignments.myAssignments')}
        </Typography>
        <Button size="small" variant="outlined" onClick={() => setShowHistory((v) => !v)}>
          {showHistory ? t('procurementAssignments.showActiveOnly') : t('procurementAssignments.assignmentHistory')}
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 2 }}>
        {t('procurementAssignments.scopeDisclaimer')}
      </Alert>
      <Alert severity="info" sx={{ mb: 2 }}>
        {t('procurementAssignments.myAssignmentsWorkflowHint')}
      </Alert>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={2}>
          <CircularProgress size={28} />
        </Box>
      ) : assignments.length === 0 ? (
        <Typography color="text.secondary">{t('procurementAssignments.noMyAssignments')}</Typography>
      ) : (
        Object.entries(grouped).map(([projectIdStr, groups]) => {
          const projectId = Number(projectIdStr);
          const project = projectsById[projectId];
          return (
            <Box key={projectId} mb={2}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                {t('procurementAssignments.assignedProjects')}:{' '}
                {project ? `${project.project_code} — ${project.name}` : `#${projectId}`}
                {' '}
                {canViewProjectItems(user) ? (
                  <Link component={RouterLink} to={`/projects/${projectId}/items`} underline="hover">
                    {t('procurementAssignments.openProjectItems')}
                  </Link>
                ) : (
                  <Link
                    component="button"
                    type="button"
                    underline="hover"
                    onClick={() => {
                      setAssignedItemsProjectId(projectId);
                      setAssignedItemsProjectLabel(
                        project ? `${project.project_code} — ${project.name}` : `#${projectId}`
                      );
                    }}
                  >
                    {t('procurementAssignments.viewAssignedItems')}
                  </Link>
                )}
              </Typography>

              {groups.project.length > 0 && (
                <Box mb={1}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {t('procurementAssignments.projectLevelAssignment')}
                  </Typography>
                  {groups.project.map((a) => (
                    <Chip
                      key={a.id}
                      size="small"
                      sx={{ mr: 0.5, mb: 0.5 }}
                      label={`${t(statusLabelKey(a.status))} · ${a.note || t('procurementAssignments.projectLevelAssignment')}`}
                      color={a.status === 'active' ? 'success' : 'default'}
                    />
                  ))}
                </Box>
              )}

              {groups.items.length > 0 && (
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {t('procurementAssignments.assignedItems')}
                  </Typography>
                  {groups.items.map((a) => (
                    <Chip
                      key={a.id}
                      size="small"
                      sx={{ mr: 0.5, mb: 0.5 }}
                      label={`${t('procurementAssignments.itemLevelAssignment')} #${a.project_item_id} · ${t(statusLabelKey(a.status))}`}
                      color={a.status === 'active' ? 'primary' : 'default'}
                    />
                  ))}
                </Box>
              )}
            </Box>
          );
        })
      )}

      <AssignedProcurementItemsDialog
        open={assignedItemsProjectId != null}
        onClose={() => setAssignedItemsProjectId(null)}
        projectId={assignedItemsProjectId}
        projectLabel={assignedItemsProjectLabel}
      />
    </Paper>
  );
};
