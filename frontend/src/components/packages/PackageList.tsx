/**
 * PackageList - Displays packages in a table format for procurement page
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Tooltip,
  Box,
  Typography,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
} from '@mui/material';
import { formatApiError } from '../../utils/errorUtils.ts';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { packagesAPI, procurementAPI } from '../../services/api.ts';
import { ProcurementPackage } from '../../types/packages.ts';

interface PackageListProps {
  projectItemId: number;
  itemCode: string;
  itemName?: string;
  enabled?: boolean;
  onEdit?: (packageId: number) => void;
  onDelete?: (packageId: number) => void;
  refreshTrigger?: number;
}

interface PackageWithDetails extends ProcurementPackage {
  coverage_percentage?: number;
  main_item_quantity?: number;
  subitem_count?: number;
  procurement_option_count?: number;
  supplier_name?: string;
}

const toCoveragePercent = (
  pkg: ProcurementPackage,
  coverageSummary: any
): number => {
  const mainRequired = Number(coverageSummary?.main_item?.required || 0);
  const subitemsMap = coverageSummary?.subitems || {};
  const totalSubRequired = Object.values(subitemsMap).reduce(
    (sum: number, sub: any) => sum + Number(sub?.required || 0),
    0
  );

  // For FULL package UX/business expectation: if main item demand is fully covered, show 100%.
  if (pkg.package_type === 'FULL') {
    if (mainRequired <= 0) return 100;
    return Number(pkg.main_item_quantity || 0) >= mainRequired ? 100 : Math.min(100, (Number(pkg.main_item_quantity || 0) / mainRequired) * 100);
  }

  const coveredMain = Math.min(Number(pkg.main_item_quantity || 0), Math.max(0, mainRequired));

  const packageSubitems = pkg.subitems || [];
  const coveredSub = packageSubitems.reduce((sum, si) => {
    const req = Number(subitemsMap?.[si.project_item_subitem_id]?.required || 0);
    const covered = Number(si.quantity_covered || 0);
    return sum + Math.min(Math.max(0, covered), Math.max(0, req));
  }, 0);

  // Denominator should be total item demand, not only sub-items present in this package.
  const totalRequired = mainRequired + totalSubRequired;
  if (totalRequired <= 0) return 0;

  return Math.min(100, ((coveredMain + coveredSub) / totalRequired) * 100);
};

export const PackageList: React.FC<PackageListProps> = ({
  projectItemId,
  itemCode,
  itemName,
  enabled = true,
  onEdit,
  onDelete,
  refreshTrigger,
}) => {
  const { t } = useTranslation();
  const [packages, setPackages] = useState<PackageWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) return;
    fetchPackages();
  }, [enabled, projectItemId, refreshTrigger]);

  const fetchPackages = async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    try {
      const packagesResponse = await packagesAPI.listByProjectItem(projectItemId, true);

      const packagesData = packagesResponse.data as ProcurementPackage[];
      if (!packagesData || packagesData.length === 0) {
        setPackages([]);
        setLoading(false);
        return;
      }

      const [optionsResponse, coverageResponse] = await Promise.all([
        procurementAPI.listByProjectItem(projectItemId),
        packagesAPI.getCoverageSummary(projectItemId).catch(() => null),
      ]);

      const optionsData = Array.isArray(optionsResponse.data) ? optionsResponse.data : [];
      const coverageSummary = coverageResponse?.data || null;

      const optionCountByPackageId = optionsData.reduce((acc: Record<number, number>, opt: any) => {
        const pkgId = Number(opt?.package_id);
        if (Number.isFinite(pkgId)) {
          acc[pkgId] = (acc[pkgId] || 0) + 1;
        }
        return acc;
      }, {});

      const packagesWithDetails = packagesData.map((pkg) => {
        const subitems = pkg.subitems || [];
        const supplierName = (pkg as any).supplier?.company_name || null;

        return {
          ...pkg,
          subitem_count: subitems.length,
          procurement_option_count: optionCountByPackageId[pkg.id] || 0,
          coverage_percentage: toCoveragePercent(pkg, coverageSummary),
          supplier_name: supplierName,
        };
      });

      setPackages(packagesWithDetails);
    } catch (err: any) {
      console.error('Failed to fetch packages:', err);
      setError(formatApiError(err, t('procurement.failedToLoadPackages') || 'Failed to load packages'));
    } finally {
      setLoading(false);
    }
  };

  const getPackageTypeColor = (type: string) => {
    switch (type) {
      case 'FULL':   return 'primary';
      case 'PARTIAL': return 'secondary';
      case 'CUSTOM':  return 'default';
      default:        return 'default';
    }
  };

  // Backend returns uppercase (FULL/PARTIAL/CUSTOM), i18n keys use camelCase (Full/Partial/Custom)
  const getPackageTypeLabel = (type: string) => {
    const keyMap: Record<string, string> = {
      FULL:    'procurement.packageTypeFull',
      PARTIAL: 'procurement.packageTypePartial',
      CUSTOM:  'procurement.packageTypeCustom',
    };
    return t(keyMap[type] || 'procurement.packageTypeCustom') || type;
  };

  const getCoverageColor = (percentage: number) => {
    if (percentage > 100) return 'warning';
    if (percentage === 100) return 'success';
    if (percentage > 0) return 'warning';
    return 'error';
  };

  const getStatusChip = (pkg: PackageWithDetails) => {
    const status = pkg.status || (pkg.is_active ? (pkg.is_finalized ? 'FINALIZED' : 'DRAFT') : 'INACTIVE');
    switch (status) {
      case 'SENT_TO_OPTIMIZATION':
        return { label: t('procurement.sentToOptimization') || 'Sent to optimization', color: 'info' as const };
      case 'FINALIZED':
        return { label: t('procurement.finalized') || 'Finalized', color: 'success' as const };
      case 'INACTIVE':
        return { label: t('procurement.inactive') || 'Inactive', color: 'default' as const };
      default:
        return { label: t('procurement.draft') || 'Draft', color: 'warning' as const };
    }
  };

  if (!enabled) {
    return null;
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (packages.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {t('procurement.noPackagesForItem') || 'No packages created for this item yet.'}
        </Typography>
      </Paper>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('procurement.packageName') || 'Package Name'}</TableCell>
            <TableCell align="center">{t('procurement.packageType') || 'Type'}</TableCell>
            <TableCell>{t('procurement.supplier') || 'Supplier'}</TableCell>
            <TableCell align="center">{t('procurement.coverage') || 'Coverage'}</TableCell>
            <TableCell align="center">{t('procurement.subItems') || 'Sub-Items'}</TableCell>
            <TableCell align="center">{t('procurement.options') || 'Options'}</TableCell>
            <TableCell align="center">{t('procurement.status') || 'Status'}</TableCell>
            <TableCell align="center">{t('common.actions') || 'Actions'}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {packages.map((pkg) => (
            <TableRow key={pkg.id}>
              <TableCell>
                <Typography variant="body2" fontWeight="medium">
                  {pkg.package_name || `${itemCode} - ${getPackageTypeLabel(pkg.package_type)}`}
                </Typography>
                {pkg.description && (
                  <Typography variant="caption" color="text.secondary" display="block">
                    {pkg.description.substring(0, 50)}
                    {pkg.description.length > 50 && '...'}
                  </Typography>
                )}
              </TableCell>
              <TableCell align="center">
                <Chip
                  label={getPackageTypeLabel(pkg.package_type)}
                  size="small"
                  color={getPackageTypeColor(pkg.package_type)}
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2">
                  {pkg.supplier_name || t('procurement.notSpecified') || '-'}
                </Typography>
              </TableCell>
              <TableCell align="center">
                <Tooltip title={`${Math.round(pkg.coverage_percentage || 0)}% ${(t('procurement.thisPackageCoverage') || 'This package coverage')}`}>
                  <Box>
                    <Chip
                      label={`${Math.round(pkg.coverage_percentage || 0)}%`}
                      size="small"
                      color={getCoverageColor(pkg.coverage_percentage || 0)}
                    />
                  </Box>
                </Tooltip>
              </TableCell>
              <TableCell align="center">
                <Chip label={pkg.subitem_count || 0} size="small" variant="outlined" />
              </TableCell>
              <TableCell align="center">
                <Chip label={pkg.procurement_option_count || 0} size="small" variant="outlined" />
              </TableCell>
              <TableCell align="center">
                <Chip {...getStatusChip(pkg)} size="small" />
              </TableCell>
              <TableCell align="center">
                <Box display="flex" gap={0.5} justifyContent="center">
                  {onEdit && (
                    <Tooltip title={pkg.is_locked_for_optimization ? (t('procurement.rollbackRequiredBeforeEdit') || 'Rollback required before editing') : (t('common.edit') || 'Edit')}>
                      <span>
                      <IconButton size="small" onClick={() => onEdit(pkg.id)} disabled={pkg.is_locked_for_optimization}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                      </span>
                    </Tooltip>
                  )}
                  {onDelete && (
                    <Tooltip title={pkg.is_locked_for_optimization ? (t('procurement.rollbackRequiredBeforeEdit') || 'Rollback required before editing') : (t('common.delete') || 'Delete')}>
                      <span>
                      <IconButton size="small" color="error" onClick={() => onDelete(pkg.id)} disabled={pkg.is_locked_for_optimization}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                      </span>
                    </Tooltip>
                  )}
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

