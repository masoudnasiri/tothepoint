/**
 * CoverageSummaryModal - Displays coverage analysis for project items and packages
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Grid,
  Tooltip,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { packagesAPI } from '../../services/api.ts';
import { calculateCoverageSummary, SubItemRequirement } from '../../utils/coverageCalculator.ts';

interface CoverageSummaryModalProps {
  open: boolean;
  onClose: () => void;
  projectId: number;
  projectItemId?: number;
  onCreateForRemaining?: (remainingDemand: {
    project_item_id: number;
    main_item_remaining: number;
    subitem_remaining: Array<{ sub_item_id: number; remaining_quantity: number }>;
  }) => void;
}

interface CoverageData {
  project_item_id: number;
  item_code: string;
  item_name?: string;
  required_quantity: number;
  covered_quantity: number;
  remaining_quantity: number;
  coverage_percentage: number;
  subitems: Array<{
    sub_item_id: number;
    name?: string;
    part_number?: string;
    required_quantity: number;
    covered_quantity: number;
    remaining_quantity: number;
    coverage_percentage: number;
  }>;
}

export const CoverageSummaryModal: React.FC<CoverageSummaryModalProps> = ({
  open,
  onClose,
  projectId,
  projectItemId,
  onCreateForRemaining,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [coverageData, setCoverageData] = useState<CoverageData[]>([]);
  const [summary, setSummary] = useState<{
    total_items: number;
    fully_covered: number;
    partially_covered: number;
    uncovered: number;
    overall_coverage: number;
  } | null>(null);

  useEffect(() => {
    if (open) {
      fetchCoverageSummary();
    }
  }, [open, projectId, projectItemId]);

  const fetchCoverageSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      let data: CoverageData[] = [];

      if (projectItemId) {
        // Item-level analysis: query only this item's package coverage.
        const itemResponse = await packagesAPI.getCoverageSummary(projectItemId);
        data = [itemResponse.data as any];
      } else {
        // Project-level analysis (full view from header button).
        const response = await packagesAPI.getProjectCoverageSummary(projectId);
        const responseData = response.data as any;
        data = Array.isArray(responseData?.items) ? responseData.items : [];
      }

      setCoverageData(data);

      // Calculate summary from coverage data structure
      // Backend returns: { project_item_id, main_item: {required, covered, remaining}, subitems: {...}, is_fully_covered, packages: [...] }
      const totalItems = data.length;
      const fullyCovered = data.filter((item: any) => item.is_fully_covered === true).length;
      const partiallyCovered = data.filter((item: any) => {
        const mainCovered = item.main_item?.covered || 0;
        const mainRequired = item.main_item?.required || 0;
        const hasPartialCoverage = mainCovered > 0 && mainCovered < mainRequired;
        return hasPartialCoverage || !item.is_fully_covered;
      }).length;
      const uncovered = data.filter((item: any) => {
        const mainCovered = item.main_item?.covered || 0;
        return mainCovered === 0;
      }).length;
      
      // Calculate overall coverage percentage
      let totalRequired = 0;
      let totalCovered = 0;
      data.forEach((item: any) => {
        const mainRequired = item.main_item?.required || 0;
        const mainCovered = item.main_item?.covered || 0;
        totalRequired += mainRequired;
        totalCovered += mainCovered;
      });
      const overallCoverage = totalRequired > 0 ? (totalCovered / totalRequired) * 100 : 0;

      setSummary({
        total_items: totalItems,
        fully_covered: fullyCovered,
        partially_covered: partiallyCovered,
        uncovered: uncovered,
        overall_coverage: overallCoverage,
      });
    } catch (err: any) {
      console.error('Failed to fetch coverage summary:', err);
      setError(err?.response?.data?.detail || t('procurement.failedToLoadCoverage') || 'Failed to load coverage summary');
    } finally {
      setLoading(false);
    }
  };

  const getCoverageColor = (percentage: number) => {
    if (percentage > 100) return 'warning';
    if (percentage === 100) return 'success';
    if (percentage > 0) return 'warning';
    return 'error';
  };

  const getCoverageLabel = (percentage: number) => {
    if (percentage > 100) return t('procurement.overCovered') || 'Over-covered';
    if (percentage === 100) return t('procurement.fullyCovered') || 'Fully Covered';
    if (percentage > 0) return t('procurement.partiallyCovered') || 'Partially Covered';
    return t('procurement.uncovered') || 'Uncovered';
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <AnalyticsIcon color="primary" />
          <Typography variant="h6">
            {t('procurement.coverageAnalysis') || 'Coverage Analysis'}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : (
          <Box>
            {/* Summary Cards */}
            {summary && (
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {summary.total_items}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('procurement.totalItems') || 'Total Items'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.lighter' }}>
                    <Typography variant="h4" color="success.main">
                      {summary.fully_covered}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('procurement.fullyCovered') || 'Fully Covered'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.lighter' }}>
                    <Typography variant="h4" color="warning.main">
                      {summary.partially_covered}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('procurement.partiallyCovered') || 'Partially Covered'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {Math.round(summary.overall_coverage)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('procurement.overallCoverage') || 'Overall Coverage'}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, summary.overall_coverage)}
                      sx={{ mt: 1 }}
                      color={getCoverageColor(summary.overall_coverage)}
                    />
                  </Paper>
                </Grid>
              </Grid>
            )}

            {/* Coverage Table */}
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('procurement.itemCode') || 'Item Code'}</TableCell>
                    <TableCell>{t('procurement.itemName') || 'Item Name'}</TableCell>
                    <TableCell align="right">{t('procurement.required') || 'Required'}</TableCell>
                    <TableCell align="right">{t('procurement.covered') || 'Covered'}</TableCell>
                    <TableCell align="right">{t('procurement.remaining') || 'Remaining'}</TableCell>
                    <TableCell align="center">{t('procurement.coverage') || 'Coverage'}</TableCell>
                    <TableCell align="center">{t('common.actions') || 'Actions'}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {coverageData.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        <Typography variant="body2" color="text.secondary">
                          {t('procurement.noCoverageData') || 'No coverage data available'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    coverageData.map((item: any) => {
                      // Calculate coverage percentage from main_item data
                      const mainItem = item.main_item || {};
                      const required = mainItem.required || 0;
                      const covered = mainItem.covered || 0;
                      const remaining = mainItem.remaining || 0;
                      const coveragePercentage = required > 0 ? Math.round((covered / required) * 100) : 0;
                      
                      // Convert subitems object to array for rendering
                      const subitemsArray = item.subitems ? Object.entries(item.subitems).map(([subItemId, subItemData]: [string, any]) => ({
                        sub_item_id: parseInt(subItemId),
                        required_quantity: subItemData.required || 0,
                        covered_quantity: subItemData.covered || 0,
                        remaining_quantity: subItemData.remaining || 0,
                        coverage_percentage: subItemData.required > 0 
                          ? Math.round((subItemData.covered / subItemData.required) * 100) 
                          : 0,
                      })) : [];
                      
                      return (
                      <TableRow key={item.project_item_id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {item.item_code || `Item ${item.project_item_id}`}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {item.item_name || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">{required}</TableCell>
                        <TableCell align="right">{covered}</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={remaining}
                            size="small"
                            color={remaining > 0 ? 'warning' : 'success'}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Tooltip title={getCoverageLabel(coveragePercentage)}>
                            <Box>
                              <Chip
                                label={`${coveragePercentage}%`}
                                size="small"
                                color={getCoverageColor(coveragePercentage)}
                              />
                              <LinearProgress
                                variant="determinate"
                                value={Math.min(100, coveragePercentage)}
                                sx={{ mt: 0.5 }}
                                color={getCoverageColor(coveragePercentage)}
                              />
                            </Box>
                          </Tooltip>
                        </TableCell>
                        <TableCell align="center">
                          {remaining > 0 && onCreateForRemaining && (
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => {
                                if (onCreateForRemaining) {
                                  onCreateForRemaining({
                                    project_item_id: item.project_item_id,
                                    main_item_remaining: remaining,
                                    subitem_remaining: subitemsArray
                                      .filter((si) => si.remaining_quantity > 0)
                                      .map((si) => ({
                                        sub_item_id: si.sub_item_id,
                                        remaining_quantity: si.remaining_quantity,
                                      })),
                                  });
                                }
                                onClose();
                              }}
                            >
                              {t('procurement.createForRemaining') || 'Create for Remaining'}
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                    })
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Subitem Details (expandable) */}
            {coverageData.map((item: any) => {
              // Convert subitems object to array
              const subitemsArray = item.subitems ? Object.entries(item.subitems).map(([subItemId, subItemData]: [string, any]) => ({
                sub_item_id: parseInt(subItemId),
                required_quantity: subItemData.required || 0,
                covered_quantity: subItemData.covered || 0,
                remaining_quantity: subItemData.remaining || 0,
                coverage_percentage: subItemData.required > 0 
                  ? Math.round((subItemData.covered / subItemData.required) * 100) 
                  : 0,
              })) : [];
              
              if (subitemsArray.length === 0) return null;
              return (
                <Paper key={`subitems-${item.project_item_id}`} sx={{ p: 2, mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {item.item_code || `Item ${item.project_item_id}`} - {t('procurement.subItems') || 'Sub-Items'}
                  </Typography>
                  <Grid container spacing={1}>
                    {subitemsArray.map((subitem: any) => (
                      <Grid item xs={12} sm={6} md={4} key={subitem.sub_item_id}>
                        <Paper
                          sx={{
                            p: 1,
                            bgcolor: subitem.remaining_quantity > 0 ? 'warning.lighter' : 'success.lighter',
                          }}
                        >
                          <Typography variant="caption" fontWeight="medium">
                            {subitem.name || `Sub-item ${subitem.sub_item_id}`}
                          </Typography>
                          {subitem.part_number && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              {subitem.part_number}
                            </Typography>
                          )}
                          <Box sx={{ mt: 0.5 }}>
                            <Chip
                              label={`${subitem.covered_quantity}/${subitem.required_quantity}`}
                              size="small"
                              color={getCoverageColor(subitem.coverage_percentage) as any}
                            />
                            {subitem.remaining_quantity > 0 && (
                              <Chip
                                label={`${subitem.remaining_quantity} ${t('procurement.remaining') || 'remaining'}`}
                                size="small"
                                color="warning"
                                sx={{ ml: 0.5 }}
                              />
                            )}
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </Paper>
              );
            })}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>{t('common.close') || 'Close'}</Button>
        <Button onClick={fetchCoverageSummary} variant="outlined">
          {t('common.refresh') || 'Refresh'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

