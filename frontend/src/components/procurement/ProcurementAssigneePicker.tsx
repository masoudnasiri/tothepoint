import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Checkbox,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Select,
  SelectChangeEvent,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { usersAPI } from '../../services/api.ts';
import type { User } from '../../types/index.ts';
import { filterProcurementCapableUsers, formatUserLabel } from '../../utils/procurementAssigneeUtils.ts';
import { formatApiError } from '../../utils/errorUtils.ts';

interface ProcurementAssigneePickerProps {
  value: number[];
  onChange: (userIds: number[]) => void;
  disabled?: boolean;
  label?: string;
}

export const ProcurementAssigneePicker: React.FC<ProcurementAssigneePickerProps> = ({
  value,
  onChange,
  disabled = false,
  label,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [candidates, setCandidates] = useState<User[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const response = await usersAPI.list({ limit: 500 });
        if (!cancelled) {
          setCandidates(filterProcurementCapableUsers(response.data || []));
          setError('');
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(formatApiError(err, t('procurementAssignments.failedToLoadAssignees')));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [t]);

  const handleChange = (event: SelectChangeEvent<number[]>) => {
    const raw = event.target.value;
    onChange(typeof raw === 'string' ? raw.split(',').map(Number) : raw);
  };

  if (loading) {
    return (
      <Box display="flex" alignItems="center" gap={1} py={1}>
        <CircularProgress size={20} />
      </Box>
    );
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 1 }}>
          {error}
        </Alert>
      )}
      {candidates.length === 0 ? (
        <Alert severity="warning">{t('procurementAssignments.noProcurementUsers')}</Alert>
      ) : (
        <FormControl fullWidth disabled={disabled}>
          <InputLabel>{label || t('procurementAssignments.assignProcurementUser')}</InputLabel>
          <Select
            multiple
            value={value}
            onChange={handleChange}
            input={<OutlinedInput label={label || t('procurementAssignments.assignProcurementUser')} />}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((id) => {
                  const user = candidates.find((u) => u.id === id);
                  return <Chip key={id} size="small" label={user ? formatUserLabel(user) : id} />;
                })}
              </Box>
            )}
          >
            {candidates.map((user) => (
              <MenuItem key={user.id} value={user.id}>
                <Checkbox checked={value.includes(user.id)} />
                <ListItemText primary={formatUserLabel(user)} />
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}
    </Box>
  );
};
