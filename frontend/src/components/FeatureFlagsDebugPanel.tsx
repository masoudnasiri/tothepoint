import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Switch,
  FormControlLabel,
  Button,
  Collapse,
  IconButton,
  Chip,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useFeatureFlags, setFeatureFlagsOverride, getFeatureFlagsOverride } from '../hooks/useFeatureFlags.tsx';
import { useTranslation } from 'react-i18next';

/**
 * QA Debug Panel for Feature Flags (Non-Production Only)
 * 
 * This component provides a UI to override feature flags for testing purposes.
 * It only renders when NODE_ENV !== 'production'.
 */
export const FeatureFlagsDebugPanel: React.FC = () => {
  const { flags, refresh, hasOverrides } = useFeatureFlags();
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [overrides, setOverrides] = useState<Partial<NonNullable<typeof flags>>>({});
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  useEffect(() => {
    // Load existing overrides
    const existing = getFeatureFlagsOverride();
    if (existing) {
      setOverrides(existing);
    }
  }, []);

  // Only render in non-production (after hooks)
  // webpack replaces process.env.NODE_ENV at build time, so we can safely check it
  // @ts-ignore - process.env is replaced by webpack at build time
  const isProduction = process.env.NODE_ENV === 'production';
  
  if (isProduction) {
    return null;
  }

  if (!flags) {
    return null;
  }

  const handleToggle = (flagName: keyof NonNullable<typeof flags>, value: boolean) => {
    const newOverrides = { ...overrides, [flagName]: value };
    setOverrides(newOverrides);
    setFeatureFlagsOverride(newOverrides);
    setSnackbarMessage(`Feature flag "${flagName}" overridden to ${value ? 'enabled' : 'disabled'}`);
    setSnackbarOpen(true);
  };

  const handleReset = () => {
    setOverrides({});
    setFeatureFlagsOverride(null);
    refresh();
    setSnackbarMessage('Feature flags reset to backend values');
    setSnackbarOpen(true);
  };

  const localHasOverrides = Object.keys(overrides).length > 0;

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 16,
        right: 16,
        zIndex: 9999,
        maxWidth: 400,
      }}
    >
      <Paper
        elevation={8}
        sx={{
          p: 2,
          bgcolor: 'warning.lighter',
          border: '2px solid',
          borderColor: 'warning.main',
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
          <Box display="flex" alignItems="center" gap={1}>
            <SettingsIcon color="warning" />
            <Typography variant="subtitle2" fontWeight="bold" color="warning.dark">
              QA Feature Flags
            </Typography>
            {localHasOverrides && (
              <Chip label="Overridden" size="small" color="warning" />
            )}
          </Box>
          <IconButton size="small" onClick={() => setOpen(!open)}>
            {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Collapse in={open}>
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom display="block">
              Override feature flags for testing (non-production only)
            </Typography>

            <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={overrides.enable_package_procurement ?? flags.enable_package_procurement ?? false}
                    onChange={(e) => handleToggle('enable_package_procurement', e.target.checked)}
                    size="small"
                  />
                }
                label={
                  <Typography variant="caption">
                    Enable Package Procurement
                  </Typography>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={overrides.legacy_project_item_fallback ?? flags.legacy_project_item_fallback ?? true}
                    onChange={(e) => handleToggle('legacy_project_item_fallback', e.target.checked)}
                    size="small"
                  />
                }
                label={
                  <Typography variant="caption">
                    Legacy Project Item Fallback
                  </Typography>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={overrides.supplier_normalization_enforced ?? flags.supplier_normalization_enforced ?? false}
                    onChange={(e) => handleToggle('supplier_normalization_enforced', e.target.checked)}
                    size="small"
                  />
                }
                label={
                  <Typography variant="caption">
                    Supplier Normalization Enforced
                  </Typography>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={overrides.enable_package_based_optimization ?? flags.enable_package_based_optimization ?? false}
                    onChange={(e) => handleToggle('enable_package_based_optimization', e.target.checked)}
                    size="small"
                  />
                }
                label={
                  <Typography variant="caption">
                    Package-Based Optimization
                  </Typography>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={overrides.require_package_id_for_new_options ?? flags.require_package_id_for_new_options ?? false}
                    onChange={(e) => handleToggle('require_package_id_for_new_options', e.target.checked)}
                    size="small"
                  />
                }
                label={
                  <Typography variant="caption">
                    Require Package ID for New Options
                  </Typography>
                }
              />
            </Box>

            {localHasOverrides && (
              <Button
                fullWidth
                variant="outlined"
                size="small"
                onClick={handleReset}
                sx={{ mt: 2 }}
              >
                Reset to Backend Values
              </Button>
            )}

            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              Changes take effect after page reload
            </Typography>
          </Box>
        </Collapse>
      </Paper>

      {/* Snackbar for override notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity="info"
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>

      {/* Banner notification when overrides are active */}
      {hasOverrides && (
        <Snackbar
          open={true}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ mt: 8 }}
        >
          <Alert severity="warning" variant="filled" onClose={() => {}}>
            QA overrides active - flags differ from backend
          </Alert>
        </Snackbar>
      )}
    </Box>
  );
};

