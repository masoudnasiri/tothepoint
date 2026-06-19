import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Paper,
  Grid,
  Slider,
  Chip,
  LinearProgress,
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Analytics as AnalyticsIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { SubItemRequirement, calculateRemainingDemand } from '../../utils/coverageCalculator.ts';
import { CoverageSummary } from '../../utils/coverageCalculator.ts';
import { packagesAPI } from '../../services/api.ts';

interface PackageWizardStep2Props {
  data: {
    main_item_quantity: number;
    subitem_quantities: Record<number, number>;
  };
  mainItemRequiredQuantity: number;
  subItemRequirements: SubItemRequirement[];
  coverageSummary: CoverageSummary | null;
  existingPackages?: any[];
  projectItemId?: number;
  onChange: (updates: Partial<PackageWizardStep2Props['data']>) => void;
  onCreateForRemainingDemand?: (remainingDemand: any) => void;
}

export const PackageWizardStep2: React.FC<PackageWizardStep2Props> = ({
  data,
  mainItemRequiredQuantity,
  subItemRequirements,
  coverageSummary,
  existingPackages = [],
  projectItemId,
  onChange,
  onCreateForRemainingDemand,
}) => {
  const { t } = useTranslation();
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisDialogOpen, setAnalysisDialogOpen] = useState(false);
  const [remainingDemand, setRemainingDemand] = useState<any>(null);

  const handleMainItemQuantityChange = (value: number) => {
    onChange({ main_item_quantity: Math.max(0, Math.min(value, mainItemRequiredQuantity)) });
  };

  const handleSubitemQuantityChange = (subItemId: number, value: number) => {
    const requirement = subItemRequirements.find((req) => req.sub_item_id === subItemId);
    const maxQuantity = requirement?.required_quantity || 0;
    const newQuantities = {
      ...data.subitem_quantities,
      [subItemId]: Math.max(0, Math.min(value, maxQuantity)),
    };
    onChange({ subitem_quantities: newQuantities });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Typography variant="h6" gutterBottom>
        {t('procurement.quantityComposition') || 'Quantity Composition'}
      </Typography>

      {/* Main Item Quantity */}
      <Paper elevation={1} sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          {t('procurement.mainItem') || 'Main Item Quantity'}
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={8}>
              <Slider
                value={data.main_item_quantity}
                onChange={(_, value) => handleMainItemQuantityChange(value as number)}
                min={0}
                max={mainItemRequiredQuantity}
                step={1}
                marks={[
                  { value: 0, label: '0' },
                  { value: mainItemRequiredQuantity, label: `${mainItemRequiredQuantity}` },
                ]}
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label={t('procurement.quantity') || 'Quantity'}
                value={data.main_item_quantity}
                onChange={(e) => handleMainItemQuantityChange(parseInt(e.target.value) || 0)}
                inputProps={{ min: 0, max: mainItemRequiredQuantity }}
                helperText={`${t('procurement.required') || 'Required'}: ${mainItemRequiredQuantity}`}
              />
            </Grid>
          </Grid>
          <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            <LinearProgress
              variant="determinate"
              value={(data.main_item_quantity / mainItemRequiredQuantity) * 100}
              sx={{ flexGrow: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              {Math.round((data.main_item_quantity / mainItemRequiredQuantity) * 100)}%
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Subitem Quantities */}
      {subItemRequirements.length > 0 && (
        <Paper elevation={1} sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            {t('procurement.subItems') || 'Sub-Item Quantities'}
          </Typography>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            {subItemRequirements.map((req, index) => {
              const currentQuantity = data.subitem_quantities[req.sub_item_id] || 0;
              const coveragePct = req.required_quantity > 0
                ? (currentQuantity / req.required_quantity) * 100
                : 0;

              return (
                <Box key={req.item_subitem_id || req.sub_item_id || `subitem-${index}`}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {req.name || `Sub-item ${req.sub_item_id}`}
                      </Typography>
                      {req.part_number && (
                        <Typography variant="caption" color="text.secondary">
                          {t('procurement.partNumber') || 'Part'}: {req.part_number}
                        </Typography>
                      )}
                    </Box>
                    <Chip
                      label={`${currentQuantity} / ${req.required_quantity}`}
                      size="small"
                      color={coveragePct === 100 ? 'success' : coveragePct > 0 ? 'warning' : 'default'}
                    />
                  </Box>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={8}>
                      <Slider
                        value={currentQuantity}
                        onChange={(_, value) => handleSubitemQuantityChange(req.sub_item_id, value as number)}
                        min={0}
                        max={req.required_quantity}
                        step={1}
                        marks={[
                          { value: 0, label: '0' },
                          { value: req.required_quantity, label: `${req.required_quantity}` },
                        ]}
                        valueLabelDisplay="auto"
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="number"
                        size="small"
                        value={currentQuantity}
                        onChange={(e) => handleSubitemQuantityChange(req.sub_item_id, parseInt(e.target.value) || 0)}
                        inputProps={{ min: 0, max: req.required_quantity }}
                      />
                    </Grid>
                  </Grid>
                  <LinearProgress
                    variant="determinate"
                    value={coveragePct}
                    sx={{ mt: 1 }}
                    color={coveragePct === 100 ? 'success' : 'primary'}
                  />
                </Box>
              );
            })}
          </Box>
        </Paper>
      )}

      {/* Coverage Summary */}
      {coverageSummary && (
        <Paper elevation={2} sx={{ p: 2, bgcolor: 'primary.lighter' }}>
          <Typography variant="subtitle2" gutterBottom fontWeight="bold">
            {t('procurement.coverageSummary') || 'Coverage Summary'}
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2">
                {t('procurement.overallCoverage') || 'Overall Coverage'}
              </Typography>
              <Chip
                label={`${Math.round(coverageSummary.overall_coverage_percentage)}%`}
                color={coverageSummary.is_fully_covered ? 'success' : 'primary'}
                size="small"
              />
            </Box>
            <LinearProgress
              variant="determinate"
              value={coverageSummary.overall_coverage_percentage}
              sx={{ mb: 2 }}
              color={coverageSummary.is_fully_covered ? 'success' : 'primary'}
            />
            <Grid container spacing={1}>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">
                  {t('procurement.mainItem') || 'Main Item'}
                </Typography>
                <Typography variant="body2">
                  {coverageSummary.main_item.covered} / {coverageSummary.main_item.required}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">
                  {t('procurement.subItems') || 'Sub-Items'}
                </Typography>
                <Typography variant="body2">
                  {coverageSummary.subitems.reduce((sum, si) => sum + si.covered, 0)} /{' '}
                  {coverageSummary.subitems.reduce((sum, si) => sum + si.required, 0)}
                </Typography>
              </Grid>
            </Grid>
            {coverageSummary.is_fully_covered && (
              <Alert severity="success" sx={{ mt: 2 }}>
                {t('procurement.fullyCovered') || 'This package provides full coverage!'}
              </Alert>
            )}
            {!coverageSummary.is_fully_covered && (
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={analyzing ? <CircularProgress size={16} /> : <AnalyticsIcon />}
                  onClick={async () => {
                    setAnalyzing(true);
                    try {
                      // Calculate remaining demand with current package
                      const mockPackageCoverage = {
                        package_id: 0,
                        package_name: 'Current Package',
                        package_type: 'FULL' as const,
                        main_item_quantity: data.main_item_quantity,
                        subitem_coverages: subItemRequirements.map((req) => ({
                          sub_item_id: req.sub_item_id,
                          covered_quantity: data.subitem_quantities[req.sub_item_id] || 0,
                          required_quantity: req.required_quantity,
                        })),
                      };

                      const existingCoverages = existingPackages.map((pkg) => ({
                        package_id: pkg.id,
                        package_name: pkg.package_name || '',
                        package_type: pkg.package_type as 'FULL' | 'PARTIAL' | 'CUSTOM',
                        main_item_quantity: 0,
                        subitem_coverages: [],
                      }));

                      const remaining = calculateRemainingDemand(
                        mainItemRequiredQuantity,
                        subItemRequirements,
                        [...existingCoverages, mockPackageCoverage]
                      );
                      setRemainingDemand(remaining);
                      setAnalysisDialogOpen(true);
                    } catch (err) {
                      console.error('Failed to analyze coverage', err);
                    } finally {
                      setAnalyzing(false);
                    }
                  }}
                  disabled={analyzing}
                  fullWidth
                >
                  {analyzing
                    ? t('procurement.analyzingCoverage') || 'Analyzing Coverage...'
                    : t('procurement.analyzeCoverage') || 'Analyze Coverage & Remaining Demand'}
                </Button>
              </Box>
            )}
          </Box>
        </Paper>
      )}

      {/* Analysis Dialog */}
      <Dialog open={analysisDialogOpen} onClose={() => setAnalysisDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {t('procurement.coverageAnalysis') || 'Coverage Analysis'}
        </DialogTitle>
        <DialogContent>
          {remainingDemand && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                {t('procurement.remainingDemand') || 'Remaining Demand'}
              </Typography>
              <Paper sx={{ p: 2, mt: 1, bgcolor: 'warning.lighter' }}>
                <Typography variant="body2" gutterBottom>
                  <strong>{t('procurement.mainItem') || 'Main Item'}:</strong>{' '}
                  {remainingDemand.main_item_remaining > 0 ? (
                    <Chip
                      label={`${remainingDemand.main_item_remaining} ${t('procurement.remaining') || 'remaining'}`}
                      color="warning"
                      size="small"
                    />
                  ) : (
                    <Chip label={t('procurement.fullyCovered') || 'Fully Covered'} color="success" size="small" />
                  )}
                </Typography>
                {remainingDemand.subitem_remaining.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      <strong>{t('procurement.subItems') || 'Sub-Items'}:</strong>
                    </Typography>
                    {remainingDemand.subitem_remaining.map((item: any) => {
                      const req = subItemRequirements.find((r) => r.sub_item_id === item.sub_item_id);
                      return (
                        <Box key={item.sub_item_id} sx={{ mt: 1 }}>
                          <Chip
                            label={`${req?.name || `Sub-item ${item.sub_item_id}`}: ${item.remaining_quantity} ${t('procurement.remaining') || 'remaining'}`}
                            color="warning"
                            size="small"
                          />
                        </Box>
                      );
                    })}
                  </Box>
                )}
                {remainingDemand.main_item_remaining === 0 &&
                  remainingDemand.subitem_remaining.length === 0 && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                      {t('procurement.allItemsFullyCovered') || 'All items are fully covered!'}
                    </Alert>
                  )}
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalysisDialogOpen(false)}>
            {t('common.close') || 'Close'}
          </Button>
          {remainingDemand && (remainingDemand.main_item_remaining > 0 || remainingDemand.subitem_remaining.length > 0) && (
            <Button
              variant="contained"
              color="primary"
              onClick={() => {
                setAnalysisDialogOpen(false);
                // Trigger package creation with remaining demand pre-filled
                // This will be handled by the parent component
                if (onCreateForRemainingDemand) {
                  onCreateForRemainingDemand(remainingDemand);
                }
              }}
            >
              {t('procurement.createPackageForRemaining') || 'Create Package for Remaining Demand'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

