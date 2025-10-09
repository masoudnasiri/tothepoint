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
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useAuth } from '../contexts/AuthContext.tsx';
import { financeAPI, excelAPI } from '../services/api.ts';
import { BudgetData, BudgetDataCreate } from '../types/index.ts';

export const FinancePage: React.FC = () => {
  const { user } = useAuth();
  const [budgetData, setBudgetData] = useState<BudgetData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedBudget, setSelectedBudget] = useState<BudgetData | null>(null);
  const [formData, setFormData] = useState<BudgetDataCreate>({
    budget_date: new Date().toISOString().split('T')[0],
    available_budget: 0,
  });

  useEffect(() => {
    fetchBudgetData();
  }, []);

  const fetchBudgetData = async () => {
    try {
      const response = await financeAPI.listBudget();
      setBudgetData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load budget data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBudget = async () => {
    try {
      await financeAPI.createBudget(formData);
      setCreateDialogOpen(false);
      resetForm();
      fetchBudgetData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create budget data');
    }
  };

  const handleEditBudget = async () => {
    if (!selectedBudget) return;
    
    try {
      await financeAPI.updateBudget(selectedBudget.budget_date, formData);
      setEditDialogOpen(false);
      setSelectedBudget(null);
      resetForm();
      fetchBudgetData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update budget data');
    }
  };

  const handleDeleteBudget = async (budgetDate: string) => {
    if (!window.confirm('Are you sure you want to delete this budget data?')) return;
    
    try {
      await financeAPI.deleteBudget(budgetDate);
      fetchBudgetData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete budget data');
    }
  };

  const resetForm = () => {
    setFormData({
      budget_date: new Date().toISOString().split('T')[0],
      available_budget: 0,
    });
  };

  const handleExportBudget = async () => {
    try {
      const response = await excelAPI.exportBudget();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'budget_data.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to export budget data');
    }
  };

  const handleImportBudget = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await excelAPI.importBudget(file);
      fetchBudgetData();
      alert('Budget data imported successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import budget data');
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await excelAPI.downloadBudgetTemplate();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'budget_template.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download template');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const calculateTotalBudget = () => {
    return budgetData.reduce((sum, budget) => sum + Number(budget.available_budget || 0), 0);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Budget Management</Typography>
        {(user?.role === 'finance' || user?.role === 'admin') && (
          <Box>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadTemplate}
              sx={{ mr: 1 }}
            >
              Download Template
            </Button>
            <Button
              variant="outlined"
              component="label"
              startIcon={<UploadIcon />}
              sx={{ mr: 1 }}
            >
              Import Budget
              <input
                type="file"
                hidden
                accept=".xlsx,.xls"
                onChange={handleImportBudget}
              />
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExportBudget}
              sx={{ mr: 1 }}
            >
              Export Budget
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Add Budget
            </Button>
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Budget Summary
        </Typography>
        <Box display="flex" gap={2}>
          <Chip
            label={`Total Periods: ${budgetData.length}`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`Total Budget: ${formatCurrency(calculateTotalBudget())}`}
            color="success"
            variant="outlined"
          />
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Budget Date</TableCell>
              <TableCell align="right">Available Budget</TableCell>
              <TableCell align="center">Created</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {budgetData.map((budget) => (
              <TableRow key={budget.budget_date}>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {new Date(budget.budget_date).toLocaleDateString()}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body1" fontWeight="medium" color="primary">
                    {formatCurrency(Number(budget.available_budget || 0))}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="body2" color="text.secondary">
                    {new Date(budget.created_at).toLocaleDateString()}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  {(user?.role === 'finance' || user?.role === 'admin') && (
                    <>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedBudget(budget);
                          setFormData({
                            budget_date: budget.budget_date,
                            available_budget: Number(budget.available_budget || 0),
                          });
                          setEditDialogOpen(true);
                        }}
                        title="Edit Budget"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteBudget(budget.budget_date)}
                        title="Delete Budget"
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Budget Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Budget Entry</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Budget Date"
              value={new Date(formData.budget_date)}
              onChange={(newValue) => {
                if (newValue) {
                  setFormData({ ...formData, budget_date: newValue.toISOString().split('T')[0] });
                }
              }}
              slotProps={{ textField: { fullWidth: true, margin: 'dense', sx: { mb: 2 } } }}
            />
          </LocalizationProvider>
          <TextField
            margin="dense"
            label="Available Budget"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.available_budget}
            onChange={(e) => setFormData({ ...formData, available_budget: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: '0.01' }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateBudget} variant="contained">
            Add Budget
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Budget Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Budget Entry</DialogTitle>
        <DialogContent>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Budget Date"
              value={new Date(formData.budget_date)}
              onChange={(newValue) => {
                if (newValue) {
                  setFormData({ ...formData, budget_date: newValue.toISOString().split('T')[0] });
                }
              }}
              disabled
              slotProps={{ textField: { fullWidth: true, margin: 'dense', sx: { mb: 2 } } }}
            />
          </LocalizationProvider>
          <TextField
            margin="dense"
            label="Available Budget"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.available_budget}
            onChange={(e) => setFormData({ ...formData, available_budget: parseFloat(e.target.value) || 0 })}
            inputProps={{ step: '0.01' }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleEditBudget} variant="contained">
            Update Budget
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
