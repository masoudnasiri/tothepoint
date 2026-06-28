import React from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
} from '@mui/material';
import { RemoveCircleOutline as RemoveIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import type { Project, User } from '../../types/index.ts';
import type { ProcurementAssignment } from '../../types/procurementAssignments.ts';
import { isSelectableForRemoval } from '../../utils/procurementAssignmentWorkbenchUtils.ts';

interface ProcurementAssignmentItemViewProps {
  assignments: ProcurementAssignment[];
  projectsById: Record<number, Project>;
  itemLabelById: Record<number, string>;
  usersById: Record<number, User>;
  itemSearch: string;
  onItemSearchChange: (value: string) => void;
  selectedAssignmentIds: number[];
  onToggleAssignmentSelection: (assignmentId: number) => void;
  onSelectAllVisibleAssignments: (assignmentIds: number[]) => void;
  canCancel: boolean;
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

export const ProcurementAssignmentItemView: React.FC<ProcurementAssignmentItemViewProps> = ({
  assignments,
  projectsById,
  itemLabelById,
  usersById,
  itemSearch,
  onItemSearchChange,
  selectedAssignmentIds,
  onToggleAssignmentSelection,
  onSelectAllVisibleAssignments,
  canCancel,
  onRemoveAssignment,
  formatDate,
}) => {
  const { t, i18n } = useTranslation();
  const isFa = i18n.language?.startsWith('fa');
  const userLabel = (id: number) => usersById[id]?.username || `#${id}`;
  const projectLabel = (id: number) => {
    const project = projectsById[id];
    return project ? `${project.project_code} — ${project.name}` : `#${id}`;
  };

  const normalizedSearch = itemSearch.trim().toLowerCase();
  const filtered = assignments.filter((row) => {
    if (!normalizedSearch) return true;
    const itemText =
      row.project_item_id != null
        ? (itemLabelById[row.project_item_id] || `#${row.project_item_id}`).toLowerCase()
        : '';
    const projectText = projectLabel(row.project_id).toLowerCase();
    return itemText.includes(normalizedSearch) || projectText.includes(normalizedSearch);
  });

  const selectableIds = filtered.filter(isSelectableForRemoval).map((a) => a.id);

  if (filtered.length === 0) {
    return <Alert severity="info">{t('procurementAssignments.noAssignments')}</Alert>;
  }

  return (
    <Box>
      <TextField
        size="small"
        fullWidth
        sx={{ mb: 2 }}
        label={t('procurementAssignments.searchItemsOrProjects')}
        value={itemSearch}
        onChange={(e) => onItemSearchChange(e.target.value)}
        inputProps={{ style: { textAlign: isFa ? 'right' : 'left' } }}
      />

      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
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
              <TableCell sx={{ whiteSpace: 'nowrap', textAlign: isFa ? 'right' : 'left' }}>{t('procurementAssignments.project')}</TableCell>
              <TableCell sx={{ minWidth: 220, textAlign: isFa ? 'right' : 'left' }}>{t('procurementAssignments.item')}</TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap', textAlign: isFa ? 'right' : 'left' }}>{t('procurementAssignments.scope')}</TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap', textAlign: isFa ? 'right' : 'left' }}>{t('procurementAssignments.assignedUser')}</TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap', textAlign: isFa ? 'right' : 'left' }}>{t('procurementAssignments.assignmentStatus')}</TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap', textAlign: isFa ? 'right' : 'left' }}>{t('procurementAssignments.createdAt')}</TableCell>
              {canCancel && <TableCell align={isFa ? 'left' : 'right'}>{t('procurement.actions')}</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((row) => (
              <TableRow key={row.id}>
                {canCancel && (
                  <TableCell padding="checkbox">
                    {isSelectableForRemoval(row) && (
                      <Tooltip title={t('procurementAssignments.removeAssignment')}>
                        <Checkbox
                          checked={selectedAssignmentIds.includes(row.id)}
                          inputProps={{
                            'aria-label': t('procurementAssignments.removeAssignment'),
                          }}
                          onChange={() => onToggleAssignmentSelection(row.id)}
                        />
                      </Tooltip>
                    )}
                  </TableCell>
                )}
                <TableCell sx={{ fontSize: 13, textAlign: isFa ? 'right' : 'left' }}>{projectLabel(row.project_id)}</TableCell>
                <TableCell sx={{ fontSize: 13, textAlign: isFa ? 'right' : 'left' }}>
                  {row.project_item_id
                    ? itemLabelById[row.project_item_id] || `#${row.project_item_id}`
                    : '—'}
                </TableCell>
                <TableCell sx={{ textAlign: isFa ? 'right' : 'left' }}>
                  {row.assignment_scope === 'project'
                    ? t('procurementAssignments.projectLevelResponsibility')
                    : t('procurementAssignments.itemAssignment')}
                </TableCell>
                <TableCell sx={{ textAlign: isFa ? 'right' : 'left' }}>{userLabel(row.assignee_user_id)}</TableCell>
                <TableCell sx={{ textAlign: isFa ? 'right' : 'left' }}>
                  <Chip
                    size="small"
                    label={t(statusLabelKey(row.status))}
                    color={row.status === 'active' ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell sx={{ textAlign: isFa ? 'right' : 'left' }}>{formatDate(row.created_at)}</TableCell>
                {canCancel && (
                  <TableCell align={isFa ? 'left' : 'right'}>
                    {isSelectableForRemoval(row) && (
                      <Button
                        size="small"
                        color="warning"
                        variant="text"
                        startIcon={<RemoveIcon />}
                        onClick={() => onRemoveAssignment(row)}
                      >
                        {t('procurementAssignments.removeAssignment')}
                      </Button>
                    )}
                    {!isSelectableForRemoval(row) && '—'}
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};
