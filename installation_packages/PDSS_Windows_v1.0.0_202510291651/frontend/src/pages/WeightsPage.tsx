import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Slider,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { weightsAPI, projectsAPI, procurementAPI } from '../services/api.ts';
import { DecisionFactorWeight } from '../types/index.ts';
import { useTranslation } from 'react-i18next';

export const WeightsPage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [weights, setWeights] = useState<DecisionFactorWeight[]>([]);
  const [availableFactors, setAvailableFactors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingWeight, setEditingWeight] = useState<DecisionFactorWeight | null>(null);
  const [formData, setFormData] = useState({
    factor_name: '',
    weight: 5,
    description: '',
  });

  useEffect(() => {
    fetchWeights();
    discoverAvailableFactors();
  }, []);

  const discoverAvailableFactors = async () => {
    try {
      // Get all project items and procurement options to discover available factors
      const [projectsResponse, procurementResponse] = await Promise.all([
        projectsAPI.list(),
        procurementAPI.listOptions()
      ]);

      const factors = new Set<string>();
      
      // Add factors from project items
      projectsResponse.data.forEach((project: any) => {
        if (project.project_items) {
          project.project_items.forEach((item: any) => {
            // Add item-specific factors
            if (item.item_code) factors.add(`item_${item.item_code}`);
            if (item.category) factors.add(`category_${item.category}`);
            if (item.unit) factors.add(`unit_${item.unit}`);
          });
        }
      });

      // Add factors from procurement options
      procurementResponse.data.forEach((option: any) => {
        if (option.supplier_name) factors.add(`supplier_${option.supplier_name}`);
        if (option.cost_currency) factors.add(`currency_${option.cost_currency}`);
        if (option.payment_terms) {
          const terms = typeof option.payment_terms === 'string' 
            ? JSON.parse(option.payment_terms) 
            : option.payment_terms;
          if (terms.type) factors.add(`payment_${terms.type}`);
        }
        if (option.expected_delivery_date) factors.add('delivery_timing');
        if (option.discount_bundle_percent) factors.add('bundle_discount');
        if (option.shipping_cost && option.shipping_cost > 0) factors.add('shipping_cost');
      });

      // Add common optimization factors
      factors.add('cost_minimization');
      factors.add('delivery_speed');
      factors.add('supplier_reliability');
      factors.add('payment_terms_flexibility');
      factors.add('currency_risk');
      factors.add('budget_utilization');

      setAvailableFactors(Array.from(factors).sort());
    } catch (err) {
      console.error('Failed to discover available factors:', err);
      // Fallback to common factors
      setAvailableFactors([
        'cost_minimization',
        'delivery_speed', 
        'supplier_reliability',
        'payment_terms_flexibility',
        'currency_risk',
        'budget_utilization'
      ]);
    }
  };

  const fetchWeights = async () => {
    try {
      setLoading(true);
      const response = await weightsAPI.list();
      setWeights(response.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load decision factor weights');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingWeight(null);
    setFormData({
      factor_name: '',
      weight: 1, // Default weight of 1 as requested
      description: '',
    });
    setDialogOpen(true);
  };

  const handleOpenEdit = (weight: DecisionFactorWeight) => {
    setEditingWeight(weight);
    setFormData({
      factor_name: weight.factor_name,
      weight: weight.weight,
      description: weight.description || '',
    });
    setDialogOpen(true);
  };

  const handleClose = () => {
    setDialogOpen(false);
    setEditingWeight(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingWeight) {
        await weightsAPI.update(editingWeight.id, formData);
      } else {
        await weightsAPI.create(formData);
      }
      
      setDialogOpen(false);
      setError('');
      fetchWeights();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('weights.failedToSaveWeight'));
    }
  };

  const handleDelete = async (weightId: number) => {
    if (!window.confirm(t('weights.confirmDeleteWeight'))) return;
    
    try {
      await weightsAPI.delete(weightId);
      setError('');
      fetchWeights();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('weights.failedToDeleteWeight'));
    }
  };

  const getWeightColor = (weight: number) => {
    if (weight >= 8) return 'success';
    if (weight >= 6) return 'primary';
    if (weight >= 4) return 'warning';
    return 'default';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  // Check if user is admin
  if (user?.role !== 'admin') {
    return (
      <Box>
        <Alert severity="error">
          {t('weights.accessDenied')}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">{t('weights.title')}</Typography>
          <Typography variant="body2" color="text.secondary" mt={1}>
            {t('weights.configureOptimizationFactors')}
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenCreate}
        >
{t('weights.addWeight')}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Available Factors Info */}
      <Alert severity="info" sx={{ mb: 2 }}>
        <Typography variant="body2">
          <strong>{t('weights.availableFactors')}</strong> {availableFactors.length} {t('weights.factorsDiscovered')}
          {availableFactors.filter(factor => !weights.some(w => w.factor_name === factor)).length > 0 && (
            <span> {availableFactors.filter(factor => !weights.some(w => w.factor_name === factor)).length} {t('weights.factorsNotConfigured')}</span>
          )}
        </Typography>
      </Alert>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('weights.factorName')}</TableCell>
              <TableCell align="center">{t('weights.weight')}</TableCell>
              <TableCell>{t('weights.description')}</TableCell>
              <TableCell align="center">{t('weights.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {weights.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography variant="body2" color="text.secondary" py={3}>
                    {t('weights.noWeightsConfigured')}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              weights.map((weight) => (
                <TableRow key={weight.id}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {weight.factor_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={weight.weight}
                      color={getWeightColor(weight.weight)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {weight.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => handleOpenEdit(weight)}
                      title="Edit Weight"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(weight.id)}
                      title="Delete Weight"
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingWeight ? 'Edit Decision Factor Weight' : 'Add Decision Factor Weight'}
        </DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal" required>
            <InputLabel>{t('weights.factorName')}</InputLabel>
            <Select
              value={formData.factor_name}
              onChange={(e) => setFormData({ ...formData, factor_name: e.target.value })}
              label={t('weights.factorName')}
              disabled={!!editingWeight}
            >
              {availableFactors
                .filter(factor => !weights.some(w => w.factor_name === factor))
                .map((factor) => (
                  <MenuItem key={factor} value={factor}>
                    {factor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </MenuItem>
                ))}
            </Select>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
              {t('weights.weightHelp')}
            </Typography>
          </FormControl>
          
          <Box sx={{ mt: 3, mb: 2 }}>
            <Typography gutterBottom>
              Weight: {formData.weight}
            </Typography>
            <Slider
              value={formData.weight}
              onChange={(e, value) => setFormData({ ...formData, weight: value as number })}
              min={1}
              max={10}
              marks={[
                { value: 1, label: '1' },
                { value: 5, label: '5' },
                { value: 10, label: '10' },
              ]}
              valueLabelDisplay="on"
              color="primary"
            />
            <Typography variant="caption" color="text.secondary">
              {t('weights.higherValuesImportance')}
            </Typography>
          </Box>

          <TextField
            fullWidth
            label={t('weights.description')}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            margin="normal"
            multiline
            rows={3}
            placeholder={t('weights.describeFactor')}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>{t('weights.cancel')}</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={!formData.factor_name || formData.weight < 1 || formData.weight > 10}
          >
            {editingWeight ? t('weights.update') : t('weights.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

