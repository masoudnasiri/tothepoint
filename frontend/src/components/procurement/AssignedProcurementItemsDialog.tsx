import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { procurementAssignmentsAPI } from '../../services/api.ts';
import type { ProcurementAssignedItemSummary } from '../../types/procurementAssignedItems.ts';
import { formatApiError } from '../../utils/errorUtils.ts';

interface AssignedProcurementItemsDialogProps {
  open: boolean;
  onClose: () => void;
  projectId?: number | null;
  projectLabel?: string;
}

export const AssignedProcurementItemsDialog: React.FC<AssignedProcurementItemsDialogProps> = ({
  open,
  onClose,
  projectId = null,
  projectLabel,
}) => {
  const { t } = useTranslation();
  const [items, setItems] = useState<ProcurementAssignedItemSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!open) return;
    try {
      setLoading(true);
      const response =
        projectId != null
          ? await procurementAssignmentsAPI.listProjectAssignedItems(projectId, { status: 'active' })
          : await procurementAssignmentsAPI.listMyAssignedItems({ status: 'active' });
      setItems(response.data || []);
      setError('');
    } catch (err: unknown) {
      setError(formatApiError(err, t('procurementAssignments.failedToLoadAssignedItems')));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [open, projectId, t]);

  useEffect(() => {
    load();
  }, [load]);

  const visibleItems = useMemo(() => {
    if (projectId == null) return items;
    return items.filter((row) => row.project_id === projectId);
  }, [items, projectId]);

  const headerLabel =
    projectLabel ||
    (visibleItems.length > 0
      ? `${visibleItems[0].project_code} — ${visibleItems[0].project_name}`
      : t('procurementAssignments.viewAssignedItems'));

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
        <Box>
          <Typography variant="h6">{t('procurementAssignments.viewAssignedItems')}</Typography>
          <Typography variant="body2" color="text.secondary">
            {headerLabel}
          </Typography>
        </Box>
        <IconButton aria-label={t('common.close')} onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Alert severity="info" sx={{ mb: 2 }}>
          {t('procurementAssignments.assignedItemsReadOnlyHint')}
        </Alert>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box display="flex" justifyContent="center" py={3}>
            <CircularProgress size={28} />
          </Box>
        ) : visibleItems.length === 0 ? (
          <Typography color="text.secondary">{t('procurementAssignments.noAssignedItemsInView')}</Typography>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('procurementAssignments.item')}</TableCell>
                  <TableCell>{t('procurementAssignments.quantity')}</TableCell>
                  <TableCell>{t('procurementAssignments.deliveryDates')}</TableCell>
                  <TableCell>{t('procurementAssignments.assignmentStatus')}</TableCell>
                  <TableCell>{t('procurementAssignments.assignedProcurementUsers')}</TableCell>
                  <TableCell>{t('procurementAssignments.assignmentScope')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {visibleItems.map((row) => (
                  <TableRow key={row.project_item_id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {row.item_code}
                      </Typography>
                      {row.item_name && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {row.item_name}
                        </Typography>
                      )}
                      {row.description && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {row.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>{row.quantity}</TableCell>
                    <TableCell>
                      {(row.delivery_options || []).length > 0
                        ? row.delivery_options.join(', ')
                        : '—'}
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={row.is_finalized ? t('procurementAssignments.itemFinalized') : row.item_status || '—'}
                        color={row.is_finalized ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      {row.assignments.map((a) => (
                        <Chip
                          key={a.assignment_id}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                          label={a.assignee_username || `#${a.assignee_user_id}`}
                        />
                      ))}
                    </TableCell>
                    <TableCell>
                      {row.covered_by_project_assignment
                        ? t('procurementAssignments.projectLevelAssignment')
                        : t('procurementAssignments.itemLevelAssignment')}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DialogContent>
    </Dialog>
  );
};
