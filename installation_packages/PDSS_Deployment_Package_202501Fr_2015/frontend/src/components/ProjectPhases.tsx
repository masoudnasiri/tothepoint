import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Edit, Delete, Add } from '@mui/icons-material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { phasesAPI } from '../services/api.ts';
import { ProjectPhase } from '../types/index.ts';

interface ProjectPhasesProps {
  projectId: number;
}

export const ProjectPhases: React.FC<ProjectPhasesProps> = ({ projectId }) => {
  const [phases, setPhases] = useState<ProjectPhase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [editingPhase, setEditingPhase] = useState<ProjectPhase | null>(null);
  const [formData, setFormData] = useState({
    phase_name: '',
    start_date: new Date(),
    end_date: new Date(),
  });

  useEffect(() => {
    loadPhases();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const loadPhases = async () => {
    try {
      setLoading(true);
      const response = await phasesAPI.listByProject(projectId);
      setPhases(response.data);
      setError('');
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load phases');
      console.error('Failed to load phases:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingPhase(null);
    setFormData({
      phase_name: '',
      start_date: new Date(),
      end_date: new Date(),
    });
    setOpen(true);
  };

  const handleOpenEdit = (phase: ProjectPhase) => {
    setEditingPhase(phase);
    setFormData({
      phase_name: phase.phase_name,
      start_date: new Date(phase.start_date),
      end_date: new Date(phase.end_date),
    });
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setEditingPhase(null);
  };

  const handleSubmit = async () => {
    try {
      const submitData = {
        phase_name: formData.phase_name,
        start_date: formData.start_date.toISOString().split('T')[0],
        end_date: formData.end_date.toISOString().split('T')[0],
        project_id: projectId,
      };

      if (editingPhase) {
        await phasesAPI.update(editingPhase.id, submitData);
      } else {
        await phasesAPI.create(projectId, submitData);
      }
      
      setOpen(false);
      setError('');
      loadPhases();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to save phase');
      console.error('Failed to save phase:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this phase?')) return;
    
    try {
      await phasesAPI.delete(id);
      setError('');
      loadPhases();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to delete phase');
      console.error('Failed to delete phase:', error);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Project Phases</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleOpenCreate}
          size="small"
        >
          Add Phase
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Phase Name</TableCell>
              <TableCell align="center">Start Date</TableCell>
              <TableCell align="center">End Date</TableCell>
              <TableCell align="center">Duration (days)</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {phases.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography variant="body2" color="text.secondary" py={2}>
                    No phases defined. Click "Add Phase" to create one.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              phases.map((phase) => {
                const startDate = new Date(phase.start_date);
                const endDate = new Date(phase.end_date);
                const duration = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
                
                return (
                  <TableRow key={phase.id}>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {phase.phase_name}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      {startDate.toLocaleDateString()}
                    </TableCell>
                    <TableCell align="center">
                      {endDate.toLocaleDateString()}
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body2" color="text.secondary">
                        {duration} days
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenEdit(phase)}
                        title="Edit Phase"
                      >
                        <Edit fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(phase.id)}
                        title="Delete Phase"
                        color="error"
                      >
                        <Delete fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>{editingPhase ? 'Edit Phase' : 'Add New Phase'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Phase Name"
            value={formData.phase_name}
            onChange={(e) => setFormData({ ...formData, phase_name: e.target.value })}
            margin="normal"
            placeholder="e.g., Q1-2025 Planning"
            required
          />
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Box sx={{ mt: 2 }}>
              <DatePicker
                label="Start Date"
                value={formData.start_date}
                onChange={(date) => setFormData({ ...formData, start_date: date || new Date() })}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    margin: 'normal',
                    required: true,
                  }
                }}
              />
            </Box>
            <Box sx={{ mt: 2 }}>
              <DatePicker
                label="End Date"
                value={formData.end_date}
                onChange={(date) => setFormData({ ...formData, end_date: date || new Date() })}
                minDate={formData.start_date}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    margin: 'normal',
                    required: true,
                  }
                }}
              />
            </Box>
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={!formData.phase_name || !formData.start_date || !formData.end_date}
          >
            {editingPhase ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

