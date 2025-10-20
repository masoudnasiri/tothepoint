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
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { weightsAPI } from '../services/api.ts';
import { DecisionFactorWeight } from '../types/index.ts';

export const WeightsPage: React.FC = () => {
  const { user } = useAuth();
  const [weights, setWeights] = useState<DecisionFactorWeight[]>([]);
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
  }, []);

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
      weight: 5,
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
      setError(err.response?.data?.detail || 'Failed to save weight');
    }
  };

  const handleDelete = async (weightId: number) => {
    if (!window.confirm('Are you sure you want to delete this decision factor weight?')) return;
    
    try {
      await weightsAPI.delete(weightId);
      setError('');
      fetchWeights();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete weight');
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
          Access Denied: Only administrators can manage decision factor weights.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">Decision Factor Weights</Typography>
          <Typography variant="body2" color="text.secondary" mt={1}>
            Configure optimization factor priorities for the decision support system
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenCreate}
        >
          Add Weight
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Factor Name</TableCell>
              <TableCell align="center">Weight</TableCell>
              <TableCell>Description</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {weights.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography variant="body2" color="text.secondary" py={3}>
                    No decision factor weights configured. Click "Add Weight" to create one.
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
          <TextField
            autoFocus
            fullWidth
            label="Factor Name"
            value={formData.factor_name}
            onChange={(e) => setFormData({ ...formData, factor_name: e.target.value })}
            margin="normal"
            placeholder="e.g., cost_minimization"
            helperText="Use lowercase with underscores (e.g., supplier_rating)"
            required
            disabled={!!editingWeight}
          />
          
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
              Higher values indicate greater importance in optimization
            </Typography>
          </Box>

          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            margin="normal"
            multiline
            rows={3}
            placeholder="Describe what this factor represents..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={!formData.factor_name || formData.weight < 1 || formData.weight > 10}
          >
            {editingWeight ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

