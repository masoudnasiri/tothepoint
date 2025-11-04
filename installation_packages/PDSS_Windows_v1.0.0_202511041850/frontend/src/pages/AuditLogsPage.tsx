import React, { useEffect, useMemo, useState } from 'react';
import { Box, Paper, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TablePagination, TextField, Grid, Chip } from '@mui/material';
import { auditLogsAPI } from '../services/api.ts';
import { useAuth } from '../contexts/AuthContext.tsx';
import { useTranslation } from 'react-i18next';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';

type AuditItem = {
  id: number;
  user_id: number | null;
  action: string;
  entity_type?: string | null;
  entity_id?: number | null;
  details?: any;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at?: string | null;
};

const ActionChip: React.FC<{ action: string }> = ({ action }) => {
  const color = useMemo(() => {
    if (action.includes('LOGIN')) return 'success';
    if (action.includes('DELETE')) return 'error';
    if (action.includes('UPDATE')) return 'warning';
    return 'default';
  }, [action]);
  return <Chip size="small" color={color as any} label={action} />;
};

export const AuditLogsPage: React.FC = () => {
  const { user } = useAuth();
  const { i18n } = useTranslation();
  
  // Locale-aware date formatter
  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDateTime = useMemo(() => (dateString: string | null) => {
    if (!dateString) return '-';
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd HH:mm') : gregorianFormat(d, 'yyyy-MM-dd HH:mm');
    } catch {
      return new Date(dateString).toLocaleString();
    }
  }, [isFa]);
  
  const [rows, setRows] = useState<AuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(25);
  const [filters, setFilters] = useState<{ user_id?: string; action?: string; entity_type?: string; entity_id?: string }>({});

  useEffect(() => {
    const fetchData = async () => {
      const params: any = { page: page + 1, size };
      if (filters.user_id) params.user_id = Number(filters.user_id);
      if (filters.action) params.action = filters.action;
      if (filters.entity_type) params.entity_type = filters.entity_type;
      if (filters.entity_id) params.entity_id = Number(filters.entity_id);
      const resp = await auditLogsAPI.list(params);
      setRows(resp.data.items || []);
      setTotal(resp.data.total || 0);
    };
    fetchData();
  }, [page, size, filters]);

  // Gate: admin only
  if (!user || user.role !== 'admin') {
    return (
      <Box p={3}>
        <Typography variant="h6">Access denied</Typography>
        <Typography variant="body2">Only administrators can view audit logs.</Typography>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Typography variant="h5" gutterBottom>Audit Logs</Typography>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <TextField fullWidth label="User ID" size="small" value={filters.user_id || ''} onChange={(e) => setFilters(f => ({ ...f, user_id: e.target.value }))} />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField fullWidth label="Action" size="small" value={filters.action || ''} onChange={(e) => setFilters(f => ({ ...f, action: e.target.value }))} placeholder="LOGIN, PROJECT_CREATE..." />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField fullWidth label="Entity Type" size="small" value={filters.entity_type || ''} onChange={(e) => setFilters(f => ({ ...f, entity_type: e.target.value }))} placeholder="project, project_item..." />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField fullWidth label="Entity ID" size="small" value={filters.entity_id || ''} onChange={(e) => setFilters(f => ({ ...f, entity_id: e.target.value }))} />
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>User ID</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Entity</TableCell>
              <TableCell>Details</TableCell>
              <TableCell>IP</TableCell>
              <TableCell>User-Agent</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map(r => (
              <TableRow key={r.id} hover>
                <TableCell>{formatDisplayDateTime(r.created_at || null)}</TableCell>
                <TableCell>{r.user_id ?? '-'}</TableCell>
                <TableCell><ActionChip action={r.action} /></TableCell>
                <TableCell>{r.entity_type || '-'}{r.entity_id ? `#${r.entity_id}` : ''}</TableCell>
                <TableCell>
                  <code style={{ fontSize: 12 }}>{r.details ? JSON.stringify(r.details) : '-'}</code>
                </TableCell>
                <TableCell>{r.ip_address || '-'}</TableCell>
                <TableCell>
                  <Typography variant="caption" color="text.secondary" sx={{ maxWidth: 240, display: 'inline-block' }}>
                    {r.user_agent || '-'}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
            {rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center">No logs</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          rowsPerPageOptions={[10, 25, 50, 100]}
          count={total}
          rowsPerPage={size}
          page={page}
          onPageChange={(_, p) => setPage(p)}
          onRowsPerPageChange={(e) => { setSize(parseInt(e.target.value, 10)); setPage(0); }}
        />
      </TableContainer>
    </Box>
  );
};

export default AuditLogsPage;


