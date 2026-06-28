import React from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Collapse,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIcon,
  RemoveCircleOutline as RemoveIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import type { Project, ProjectItem, User } from '../../types/index.ts';
import type { ProcurementAssignment } from '../../types/procurementAssignments.ts';
import {
  assignmentsForProjectItem,
  getAssignableProjectItemIds,
  isSelectableForRemoval,
  summarizeProjectAssignments,
} from '../../utils/procurementAssignmentWorkbenchUtils.ts';

interface ProcurementAssignmentProjectViewProps {
  assignments: ProcurementAssignment[];
  projectsById: Record<number, Project>;
  usersById: Record<number, User>;
  expandedProjectId: number | null;
  onToggleProject: (projectId: number) => void;
  projectItems: ProjectItem[];
  itemsLoading: boolean;
  selectedAssignmentIds: number[];
  onToggleAssignmentSelection: (assignmentId: number) => void;
  onSelectAllVisibleAssignments: (assignmentIds: number[]) => void;
  selectedItemIdsForAssign: number[];
  onToggleItemForAssign: (itemId: number) => void;
  canCreate: boolean;
  canCancel: boolean;
  onAssignAllItems: (projectId: number) => void;
  onAssignSelectedItems: (projectId: number) => void;
  onRemoveAssignment: (assignment: ProcurementAssignment) => void;
  formatDate: (value?: string | null) => string;
}

function statusLabelKey(status: ProcurementAssignment['status']): string {
  const map = {
    active: 'procurementAssignments.statusActive',
    completed: 'procurementAssignments.statusCompleted',
    cancelled: 'procurementAssignments.statusCancelled',
  } as const;
  return map[status];
}

export const ProcurementAssignmentProjectView: React.FC<ProcurementAssignmentProjectViewProps> = ({
  assignments,
  projectsById,
  usersById,
  expandedProjectId,
  onToggleProject,
  projectItems,
  itemsLoading,
  selectedAssignmentIds,
  onToggleAssignmentSelection,
  onSelectAllVisibleAssignments,
  selectedItemIdsForAssign,
  onToggleItemForAssign,
  canCreate,
  canCancel,
  onAssignAllItems,
  onAssignSelectedItems,
  onRemoveAssignment,
  formatDate,
}) => {
  const { t, i18n } = useTranslation();
  const isFa = i18n.language?.startsWith('fa');
  const projectIds = Array.from(new Set(assignments.map((a) => a.project_id))).sort((a, b) => a - b);
  const finalizedProjectItems = projectItems.filter((item) => Boolean(item.is_finalized));

  if (projectIds.length === 0) {
    return <Alert severity="info">{t('procurementAssignments.noAssignments')}</Alert>;
  }

  const userLabel = (id: number) => usersById[id]?.username || `#${id}`;

  return (
    <Box display="flex" flexDirection="column" gap={1}>
      {projectIds.map((projectId) => {
        const summary = summarizeProjectAssignments(projectId, assignments);
        const project = projectsById[projectId];
        const expanded = expandedProjectId === projectId;
        const selectableIds = [
          ...summary.projectLevelAssignments.filter(isSelectableForRemoval).map((a) => a.id),
          ...summary.itemLevelAssignments.filter(isSelectableForRemoval).map((a) => a.id),
        ];

        return (
          <Paper key={projectId} variant="outlined" sx={{ overflow: 'hidden', borderRadius: 2 }}>
            <Box
              display="flex"
              alignItems="center"
              justifyContent="space-between"
              px={2}
              py={1}
              sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
              onClick={() => onToggleProject(projectId)}
            >
              <Box>
                <Typography variant="subtitle2" fontWeight={700}>
                  {project ? `${project.project_code} — ${project.name}` : `#${projectId}`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('procurementAssignments.assignmentCoverage')}:{' '}
                  {t('procurementAssignments.activeAssignmentCount', { count: summary.activeCount })}
                  {' · '}
                  {t('procurementAssignments.assignedItemsCount', {
                    count: summary.itemAssignmentCount,
                  })}
                  {summary.projectLevelAssignments.some((a) => a.status === 'active') &&
                    ` · ${t('procurementAssignments.projectLevelResponsibility')}`}
                </Typography>
                <Box mt={0.5} display="flex" flexWrap="wrap" gap={0.5} justifyContent={isFa ? 'flex-end' : 'flex-start'}>
                  {summary.assigneeIds.map((id) => (
                    <Chip key={id} size="small" label={userLabel(id)} />
                  ))}
                </Box>
              </Box>
              <IconButton size="small" aria-label="expand">
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>

            <Collapse in={expanded}>
              <Box px={2} pb={2}>
                {summary.projectLevelAssignments.some((a) => a.status === 'active') && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    {t('procurementAssignments.projectLevelPartialRemovalHint')}
                  </Alert>
                )}

                {summary.projectLevelAssignments.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="body2" fontWeight={600} gutterBottom>
                      {t('procurementAssignments.projectLevelResponsibility')}
                    </Typography>
                    {summary.projectLevelAssignments.map((assignment) => (
                      <Box
                        key={assignment.id}
                        display="flex"
                        alignItems="center"
                        gap={1}
                        flexWrap="wrap"
                        mb={0.5}
                      >
                        {canCancel && isSelectableForRemoval(assignment) && (
                          <Checkbox
                            size="small"
                            checked={selectedAssignmentIds.includes(assignment.id)}
                            onChange={() => onToggleAssignmentSelection(assignment.id)}
                          />
                        )}
                        <Chip
                          size="small"
                          label={`${userLabel(assignment.assignee_user_id)} · ${t(statusLabelKey(assignment.status))} · ${formatDate(assignment.created_at)}`}
                          color={assignment.status === 'active' ? 'success' : 'default'}
                        />
                        {canCancel && isSelectableForRemoval(assignment) && (
                          <Button
                            size="small"
                            color="warning"
                            startIcon={<RemoveIcon />}
                            onClick={() => onRemoveAssignment(assignment)}
                          >
                            {t('procurementAssignments.removeAssignment')}
                          </Button>
                        )}
                      </Box>
                    ))}
                  </Box>
                )}

                <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                  {canCreate && (
                    <>
                      <Button size="small" variant="outlined" onClick={() => onAssignAllItems(projectId)}>
                        {t('procurementAssignments.assignAllFinalizedProjectItems')}
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        disabled={selectedItemIdsForAssign.length === 0}
                        onClick={() => onAssignSelectedItems(projectId)}
                      >
                        {t('procurementAssignments.assignSelectedItems')}
                      </Button>
                    </>
                  )}
                </Box>

                {itemsLoading ? (
                  <Box display="flex" justifyContent="center" py={2}>
                    <CircularProgress size={24} />
                  </Box>
                ) : finalizedProjectItems.length === 0 ? (
                  <Alert severity="info">
                    {t('procurementAssignments.noFinalizedItemsForItemAssignment')}
                  </Alert>
                ) : (
                  <TableContainer sx={{ border: 1, borderColor: 'divider', borderRadius: 1.5 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          {canCancel && (
                            <TableCell padding="checkbox">
                              <Tooltip title={t('procurementAssignments.removeSelectedAssignments')}>
                                <Checkbox
                                  indeterminate={
                                    selectableIds.length > 0 &&
                                    selectableIds.some((id) => !selectedAssignmentIds.includes(id)) &&
                                    selectableIds.some((id) => selectedAssignmentIds.includes(id))
                                  }
                                  checked={
                                    selectableIds.length > 0 &&
                                    selectableIds.every((id) => selectedAssignmentIds.includes(id))
                                  }
                                  inputProps={{
                                    'aria-label': t('procurementAssignments.removeSelectedAssignments'),
                                  }}
                                  onChange={(e) => {
                                    onSelectAllVisibleAssignments(e.target.checked ? selectableIds : []);
                                  }}
                                />
                              </Tooltip>
                            </TableCell>
                          )}
                          {canCreate && (
                            <TableCell padding="checkbox" sx={{ whiteSpace: 'nowrap', textAlign: isFa ? 'right' : 'left' }}>
                              {t('procurementAssignments.assign')}
                            </TableCell>
                          )}
                          <TableCell sx={{ whiteSpace: 'nowrap', textAlign: isFa ? 'right' : 'left' }}>
                            {t('procurementAssignments.item')}
                          </TableCell>
                          <TableCell sx={{ minWidth: 220, textAlign: isFa ? 'right' : 'left' }}>
                            {t('procurementAssignments.assignedProcurementUsers')}
                          </TableCell>
                          <TableCell sx={{ whiteSpace: 'nowrap', textAlign: isFa ? 'right' : 'left' }}>
                            {t('procurementAssignments.assignmentStatus')}
                          </TableCell>
                          {canCancel && (
                            <TableCell sx={{ whiteSpace: 'nowrap', textAlign: isFa ? 'right' : 'left' }}>
                              {t('procurement.actions')}
                            </TableCell>
                          )}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {finalizedProjectItems.map((item) => {
                          const itemAssignments = assignmentsForProjectItem(assignments, item.id);
                          const removableAssignments = itemAssignments.filter(isSelectableForRemoval);
                          const assignableForAssignment = getAssignableProjectItemIds(
                            projectId,
                            [item.id],
                            assignments
                          ).includes(item.id);
                          const allSelected =
                            removableAssignments.length > 0 &&
                            removableAssignments.every((a) => selectedAssignmentIds.includes(a.id));

                          return (
                            <TableRow key={item.id}>
                              {canCancel && (
                                <TableCell padding="checkbox">
                                  {removableAssignments.length > 0 && (
                                    <Tooltip title={t('procurementAssignments.removeAssignment')}>
                                      <Checkbox
                                        checked={allSelected}
                                        indeterminate={
                                          removableAssignments.some((a) =>
                                            selectedAssignmentIds.includes(a.id)
                                          ) && !allSelected
                                        }
                                        inputProps={{
                                          'aria-label': t('procurementAssignments.removeAssignment'),
                                        }}
                                        onChange={(e) => {
                                          if (e.target.checked) {
                                            onSelectAllVisibleAssignments([
                                              ...new Set([
                                                ...selectedAssignmentIds,
                                                ...removableAssignments.map((a) => a.id),
                                              ]),
                                            ]);
                                          } else {
                                            onSelectAllVisibleAssignments(
                                              selectedAssignmentIds.filter(
                                                (id) => !removableAssignments.some((a) => a.id === id)
                                              )
                                            );
                                          }
                                        }}
                                      />
                                    </Tooltip>
                                  )}
                                </TableCell>
                              )}
                              {canCreate && (
                                <TableCell padding="checkbox">
                                  <Tooltip title={t('procurementAssignments.assignSelectedItems')}>
                                    <Checkbox
                                      checked={selectedItemIdsForAssign.includes(item.id)}
                                      disabled={!assignableForAssignment}
                                      inputProps={{
                                        'aria-label': t('procurementAssignments.assignSelectedItems'),
                                      }}
                                      onChange={() => onToggleItemForAssign(item.id)}
                                    />
                                  </Tooltip>
                                </TableCell>
                              )}
                              <TableCell sx={{ fontSize: 13, textAlign: isFa ? 'right' : 'left' }}>
                                {`${item.item_code} — ${item.item_name}`}
                              </TableCell>
                              <TableCell sx={{ textAlign: isFa ? 'right' : 'left', verticalAlign: 'top' }}>
                                {itemAssignments.length === 0 ? (
                                  <Typography variant="body2" color="text.secondary">
                                    {t('procurementAssignments.unassignedItem')}
                                  </Typography>
                                ) : (
                                  <Box display="flex" flexDirection="column" gap={0.5}>
                                    {itemAssignments.map((assignment) => (
                                      <Box
                                        key={assignment.id}
                                        display="flex"
                                        alignItems="center"
                                        gap={0.5}
                                        flexWrap="wrap"
                                        justifyContent={isFa ? 'flex-end' : 'flex-start'}
                                      >
                                        <Chip
                                          size="small"
                                          label={userLabel(assignment.assignee_user_id)}
                                          color={assignment.status === 'active' ? 'primary' : 'default'}
                                          sx={{ maxWidth: 220 }}
                                        />
                                      </Box>
                                    ))}
                                  </Box>
                                )}
                              </TableCell>
                              <TableCell sx={{ textAlign: isFa ? 'right' : 'left', verticalAlign: 'top' }}>
                                {itemAssignments.length === 0
                                  ? '—'
                                  : (
                                    <Box display="flex" flexDirection="column" gap={0.5}>
                                      {itemAssignments.map((assignment) => (
                                        <Chip
                                          key={`status-${assignment.id}`}
                                          size="small"
                                          label={t(statusLabelKey(assignment.status))}
                                          color={assignment.status === 'active' ? 'success' : 'default'}
                                          sx={{ alignSelf: isFa ? 'flex-end' : 'flex-start' }}
                                        />
                                      ))}
                                    </Box>
                                  )}
                              </TableCell>
                              {canCancel && (
                                <TableCell sx={{ textAlign: isFa ? 'right' : 'left', verticalAlign: 'top' }}>
                                  {removableAssignments.length === 0 ? (
                                    '—'
                                  ) : (
                                    <Box display="flex" flexDirection="column" gap={0.5}>
                                      {removableAssignments.map((assignment) => (
                                        <Button
                                          key={`remove-${assignment.id}`}
                                          size="small"
                                          color="warning"
                                          variant="text"
                                          onClick={() => onRemoveAssignment(assignment)}
                                          sx={{ alignSelf: isFa ? 'flex-end' : 'flex-start' }}
                                        >
                                          {t('procurementAssignments.removeAssignment')}
                                        </Button>
                                      ))}
                                    </Box>
                                  )}
                                </TableCell>
                              )}
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Box>
            </Collapse>
          </Paper>
        );
      })}
    </Box>
  );
};
