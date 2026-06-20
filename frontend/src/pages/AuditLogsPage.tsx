import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Grid,
  Chip,
  Tooltip,
} from '@mui/material';
import { auditLogsAPI } from '../services/api.ts';
import { useAuth } from '../contexts/AuthContext.tsx';
import { useTranslation } from 'react-i18next';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';
import { RivarPageHeader } from '../components/ui/RivarPageHeader.tsx';
import { rivarTokens } from '../theme/rivarTheme.ts';

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
  return <Chip size="small" color={color as any} label={action} sx={{ fontSize: '0.6875rem' }} />;
};

const DetailsCell: React.FC<{ details: any }> = ({ details }) => {
  if (!details) return <Typography variant="caption" color="text.secondary">—</Typography>;
  const text = typeof details === 'string' ? details : JSON.stringify(details);
  const preview = text.length > 60 ? text.substring(0, 60) + '…' : text;
  return (
    <Tooltip title={<pre style={{ maxWidth: 400, whiteSpace: 'pre-wrap', fontSize: 11 }}>{text}</pre>} arrow>
      <Typography
        variant="caption"
        sx={{
          fontFamily: 'ui-monospace, monospace',
          color: rivarTokens.ink500,
          display: 'block',
          maxWidth: 200,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          cursor: 'pointer',
        }}
      >
        {preview}
      </Typography>
    </Tooltip>
  );
};

const AuditLogsPage: React.FC = () => {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();

  const isFa = i18n.language?.startsWith('fa');

  const formatDisplayDateTime = useMemo(() => (dateString: string | null) => {
    if (!dateString) return '—';
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
  const [filters, setFilters] = useState<{
    user_id?: string;
    action?: string;
    entity_type?: string;
    entity_id?: string;
  }>({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params: any = { page: page + 1, size };
        if (filters.user_id) params.user_id = Number(filters.user_id);
        if (filters.action) params.action = filters.action;
        if (filters.entity_type) params.entity_type = filters.entity_type;
        if (filters.entity_id) params.entity_id = Number(filters.entity_id);
        const resp = await auditLogsAPI.list(params);
        setRows(resp.data.items || []);
        setTotal(resp.data.total || 0);
      } catch {
        setRows([]);
        setTotal(0);
      }
    };
    fetchData();
  }, [page, size, filters]);

  if (!user || user.role !== 'admin') {
    return (
      <Box>
        <Typography variant="h6">{t('common.accessDenied', 'Access denied')}</Typography>
        <Typography variant="body2" color="text.secondary">
          {t('common.adminOnly', 'Only administrators can view audit logs.')}
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <RivarPageHeader title={t('auditLogsPage.title')} />

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label={t('auditLogsPage.userId')}
              size="small"
              value={filters.user_id || ''}
              onChange={(e) => { setPage(0); setFilters(f => ({ ...f, user_id: e.target.value })); }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label={t('auditLogsPage.action')}
              size="small"
              value={filters.action || ''}
              onChange={(e) => { setPage(0); setFilters(f => ({ ...f, action: e.target.value })); }}
              placeholder={t('auditLogsPage.placeholder.action')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label={t('auditLogsPage.entityType')}
              size="small"
              value={filters.entity_type || ''}
              onChange={(e) => { setPage(0); setFilters(f => ({ ...f, entity_type: e.target.value })); }}
              placeholder={t('auditLogsPage.placeholder.entityType')}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label={t('auditLogsPage.entityId')}
              size="small"
              value={filters.entity_id || ''}
              onChange={(e) => { setPage(0); setFilters(f => ({ ...f, entity_id: e.target.value })); }}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Table + Pagination */}
      <Box
        sx={{
          background: rivarTokens.paper,
          border: `1px solid ${rivarTokens.line}`,
          borderRadius: rivarTokens.radiusLg,
          boxShadow: rivarTokens.shadowCard,
          overflow: 'hidden',
        }}
      >
        <TableContainer sx={{ border: 'none', borderRadius: 0, overflowX: 'auto' }}>
          <Table size="small" sx={{ minWidth: 750 }}>
            <TableHead>
              <TableRow>
                <TableCell>{t('auditLogsPage.time')}</TableCell>
                <TableCell>{t('auditLogsPage.userId')}</TableCell>
                <TableCell>{t('auditLogsPage.action')}</TableCell>
                <TableCell>{t('auditLogsPage.entity')}</TableCell>
                <TableCell>{t('auditLogsPage.details')}</TableCell>
                <TableCell>{t('auditLogsPage.ip')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map(r => (
                <TableRow key={r.id} hover>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatDisplayDateTime(r.created_at || null)}</TableCell>
                  <TableCell>{r.user_id ?? '—'}</TableCell>
                  <TableCell><ActionChip action={r.action} /></TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>
                    {r.entity_type || '—'}{r.entity_id ? `#${r.entity_id}` : ''}
                  </TableCell>
                  <TableCell><DetailsCell details={r.details} /></TableCell>
                  <TableCell sx={{ fontSize: '0.75rem', color: rivarTokens.ink300 }}>
                    {r.ip_address || '—'}
                  </TableCell>
                </TableRow>
              ))}
              {rows.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4, color: rivarTokens.ink300 }}>
                    {t('auditLogsPage.noLogs')}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination — forced LTR to prevent RTL number-reversal */}
        <Box
          sx={{
            borderTop: `1px solid ${rivarTokens.line}`,
            direction: 'ltr',
            display: 'flex',
            justifyContent: isFa ? 'flex-start' : 'flex-end',
          }}
        >
          <TablePagination
            component="div"
            rowsPerPageOptions={[10, 25, 50, 100]}
            count={total}
            rowsPerPage={size}
            page={page}
            onPageChange={(_, p) => setPage(p)}
            onRowsPerPageChange={(e) => { setSize(parseInt(e.target.value, 10)); setPage(0); }}
            labelRowsPerPage={t('dashboard.rowsPerPage')}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default AuditLogsPage;
