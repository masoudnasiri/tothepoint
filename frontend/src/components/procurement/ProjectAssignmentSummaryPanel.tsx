import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Typography,
} from '@mui/material';
import { Assignment as AssignmentIcon } from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { procurementAssignmentsAPI, usersAPI } from '../../services/api.ts';
import type { User } from '../../types/index.ts';
import type { ProcurementAssignment } from '../../types/procurementAssignments.ts';
import { useAuth } from '../../contexts/AuthContext.tsx';
import { canViewProcurementAssignments } from '../../utils/permissions.ts';
import { formatApiError } from '../../utils/errorUtils.ts';

interface ProjectAssignmentSummaryPanelProps {
  projectId: number;
}

export const ProjectAssignmentSummaryPanel: React.FC<ProjectAssignmentSummaryPanelProps> = ({
  projectId,
}) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<ProcurementAssignment[]>([]);
  const [usersById, setUsersById] = useState<Record<number, User>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!canViewProcurementAssignments(user)) return;
    try {
      setLoading(true);
      const [assignmentResponse, usersResponse] = await Promise.all([
        procurementAssignmentsAPI.listByProject(projectId, { status: 'active' }),
        usersAPI.list({ limit: 500 }),
      ]);
      setAssignments(assignmentResponse.data || []);
      const map: Record<number, User> = {};
      (usersResponse.data || []).forEach((u: User) => {
        map[u.id] = u;
      });
      setUsersById(map);
      setError('');
    } catch (err: unknown) {
      setError(formatApiError(err, t('procurementAssignments.failedToLoad')));
    } finally {
      setLoading(false);
    }
  }, [projectId, t, user]);

  useEffect(() => {
    load();
  }, [load]);

  const projectLevel = useMemo(
    () => assignments.filter((a) => a.assignment_scope === 'project'),
    [assignments]
  );
  const itemLevel = useMemo(
    () => assignments.filter((a) => a.assignment_scope === 'project_item'),
    [assignments]
  );

  if (!canViewProcurementAssignments(user)) {
    return null;
  }

  const userLabel = (id: number) => usersById[id]?.username || `#${id}`;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" gap={2} flexWrap="wrap">
        <Box>
          <Typography variant="subtitle1" display="flex" alignItems="center" gap={1} gutterBottom>
            <AssignmentIcon fontSize="small" />
            {t('procurementAssignments.assignedWork')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('procurementAssignments.projectSummaryHint')}
          </Typography>
        </Box>
        <Button
          component={RouterLink}
          to={`/procurement?tab=assignments&projectId=${projectId}`}
          variant="outlined"
          size="small"
        >
          {t('procurementAssignments.manageInProcurement')}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={2}>
          <CircularProgress size={24} />
        </Box>
      ) : assignments.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          {t('procurementAssignments.noAssignedProcurementUsers')}
        </Typography>
      ) : (
        <Box sx={{ mt: 2 }}>
          {projectLevel.length > 0 && (
            <Box mb={1}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('procurementAssignments.projectAssignment')}
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={0.5}>
                {projectLevel.map((a) => (
                  <Chip
                    key={a.id}
                    size="small"
                    label={`${userLabel(a.assignee_user_id)} · ${t('procurementAssignments.statusActive')}`}
                    color="success"
                  />
                ))}
              </Box>
            </Box>
          )}
          {itemLevel.length > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('procurementAssignments.itemAssignment')}
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={0.5}>
                {itemLevel.map((a) => (
                  <Chip
                    key={a.id}
                    size="small"
                    label={`#${a.project_item_id} · ${userLabel(a.assignee_user_id)}`}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          )}
        </Box>
      )}
    </Paper>
  );
};

/** Active assignee usernames keyed by project item id (read-only helper for item rows). */
export function useProjectItemAssignmentMap(projectId: number) {
  const { user } = useAuth();
  const [byItemId, setByItemId] = useState<Record<number, string[]>>({});

  useEffect(() => {
    if (!projectId || !canViewProcurementAssignments(user)) return;
    let cancelled = false;
    (async () => {
      try {
        const [assignmentResponse, usersResponse] = await Promise.all([
          procurementAssignmentsAPI.listByProject(projectId, { status: 'active' }),
          usersAPI.list({ limit: 500 }),
        ]);
        if (cancelled) return;
        const usersById: Record<number, User> = {};
        (usersResponse.data || []).forEach((u: User) => {
          usersById[u.id] = u;
        });
        const map: Record<number, string[]> = {};
        (assignmentResponse.data || []).forEach((a: ProcurementAssignment) => {
          if (a.project_item_id == null) return;
          const label = usersById[a.assignee_user_id]?.username || `#${a.assignee_user_id}`;
          if (!map[a.project_item_id]) map[a.project_item_id] = [];
          map[a.project_item_id].push(label);
        });
        setByItemId(map);
      } catch {
        /* optional row hints */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId, user]);

  return byItemId;
}
