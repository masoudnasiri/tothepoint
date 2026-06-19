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
  Analytics as AnalyticsIcon,
  Send as SendIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { packagesAPI, procurementAPI } from '../../services/api.ts';
import { ProcurementPackage } from '../../types/packages.ts';

interface PackageListProps {
  projectItemId: number;
  itemCode: string;
  itemName?: string;
  onEdit?: (packageId: number) => void;
  onDelete?: (packageId: number) => void;
  onAnalyze?: (packageId: number) => void;
  onSendToOptimizer?: (packageId: number) => void;
  refreshTrigger?: number;
}

interface PackageWithDetails extends ProcurementPackage {
  coverage_percentage?: number;
  main_item_quantity?: number;
  subitem_count?: number;
  procurement_option_count?: number;
  supplier_name?: string;
}

export const PackageList: React.FC<PackageListProps> = ({
  projectItemId,
  itemCode,
  itemName,
  onEdit,
  onDelete,
  onAnalyze,
  onSendToOptimizer,
  refreshTrigger,
}) => {
  const { t } = useTranslation();
  const [packages, setPackages] = useState<PackageWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPackages();
  }, [projectItemId, refreshTrigger]);

  const fetchPackages = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await packagesAPI.listByProjectItem(projectItemId, true);
      const packagesData = response.data as ProcurementPackage[];

      // Fetch additional details for each package
      const packagesWithDetails = await Promise.all(
        packagesData.map(async (pkg) => {
          try {
            // Get package details including subitems
            const pkgDetails = await packagesAPI.get(pkg.id);
            // Handle both direct array and nested structure
            const subitems = Array.isArray(pkgDetails.data?.subitems) 
              ? pkgDetails.data.subitems 
              : (pkgDetails.data?.data?.subitems || []);
            
            // Debug logging
            if (subitems.length === 0) {
              console.log(`Package ${pkg.id} subitems:`, pkgDetails.data?.subitems, 'Full response:', pkgDetails.data);
            }
            
            // Get procurement options for this package
            const optionsResponse = await procurementAPI.listByProjectItem(projectItemId);
            const packageOptions = optionsResponse.data.filter(
              (opt: any) => opt.package_id === pkg.id
            );
            
            // Debug logging for procurement options
            if (packageOptions.length === 0) {
              console.log(`Package ${pkg.id} procurement options:`, optionsResponse.data?.filter((opt: any) => opt.package_id === pkg.id));
            }

            // Calculate coverage if available
            const coverageSummary = await packagesAPI.getCoverageSummary(projectItemId).catch(() => null);
            const itemCoverage = coverageSummary?.data?.items?.find(
              (item: any) => item.project_item_id === projectItemId
            );

            // Get supplier name from package data (supplier relationship should be loaded)
            // The list endpoint now includes supplier in the response
            const supplierName = 
              (pkg as any).supplier?.company_name || 
              pkgDetails.data?.supplier?.company_name || 
              null;

            return {
              ...pkg,
              subitem_count: subitems.length,
              procurement_option_count: packageOptions.length,
              coverage_percentage: itemCoverage?.coverage_percentage || 0,
              main_item_quantity: subitems.reduce((sum: number, si: any) => sum + (si.quantity_covered || 0), 0),
              supplier_name: supplierName,
            };
          } catch (err) {
            console.error(`Failed to fetch details for package ${pkg.id}:`, err);
            // Even if details fail, try to get supplier from the list response
            const supplierName = (pkg as any).supplier?.company_name || null;
            return {
              ...pkg,
              subitem_count: 0,
              procurement_option_count: 0,
              coverage_percentage: 0,
              supplier_name: supplierName,
            };
          }
        })
      );

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
      case 'FULL':
        return 'primary';
      case 'PARTIAL':
        return 'secondary';
      case 'CUSTOM':
        return 'default';
      default:
        return 'default';
    }
  };

  const getCoverageColor = (percentage: number) => {
    if (percentage === 100) return 'success';
    if (percentage > 0) return 'warning';
    return 'error';
  };

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
                  {pkg.package_name || `${itemCode} - ${t(`procurement.packageType${pkg.package_type}`)}`}
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
                  label={t(`procurement.packageType${pkg.package_type}`) || pkg.package_type}
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
                <Tooltip title={`${Math.round(pkg.coverage_percentage || 0)}% coverage`}>
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
                <Chip
                  label={pkg.is_active ? (t('procurement.active') || 'Active') : (t('procurement.inactive') || 'Inactive')}
                  size="small"
                  color={pkg.is_active ? 'success' : 'default'}
                />
              </TableCell>
              <TableCell align="center">
                <Box display="flex" gap={0.5} justifyContent="center">
                  {onAnalyze && (
                    <Tooltip title={t('procurement.analyzeCoverage') || 'Analyze Coverage'}>
                      <IconButton size="small" onClick={() => onAnalyze(pkg.id)}>
                        <AnalyticsIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  {onSendToOptimizer && (
                    <Tooltip title={t('procurement.sendToOptimizer') || 'Send to Optimizer'}>
                      <IconButton size="small" color="primary" onClick={() => onSendToOptimizer(pkg.id)}>
                        <SendIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  {onEdit && (
                    <Tooltip title={t('common.edit') || 'Edit'}>
                      <IconButton size="small" onClick={() => onEdit(pkg.id)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  {onDelete && (
                    <Tooltip title={t('common.delete') || 'Delete'}>
                      <IconButton size="small" color="error" onClick={() => onDelete(pkg.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
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

