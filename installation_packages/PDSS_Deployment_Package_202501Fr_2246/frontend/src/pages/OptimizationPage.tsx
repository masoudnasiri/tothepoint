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
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Grid,
  LinearProgress,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  AttachMoney as AttachMoneyIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { financeAPI, decisionsAPI, procurementAPI } from '../services/api.ts';
import { OptimizationResult, OptimizationRunResponse, ProcurementOption } from '../types/index.ts';
import { formatApiError } from '../utils/errorUtils.ts';

export const OptimizationPage: React.FC = () => {
  const { user } = useAuth();
  const [results, setResults] = useState<OptimizationResult[]>([]);
  const [editedResults, setEditedResults] = useState<Record<number, OptimizationResult>>({});
  const [removedResultIds, setRemovedResultIds] = useState<Set<number>>(new Set());
  const [addedResults, setAddedResults] = useState<OptimizationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [runDialogOpen, setRunDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedResult, setSelectedResult] = useState<OptimizationResult | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [procurementOptions, setProcurementOptions] = useState<ProcurementOption[]>([]);
  
  const [optimizationConfig, setOptimizationConfig] = useState({
    max_time_slots: 12,
    time_limit_seconds: 300,
  });
  const [lastRun, setLastRun] = useState<OptimizationRunResponse | null>(null);

  useEffect(() => {
    fetchResults();
    fetchLatestRun();
    fetchProcurementOptions();
  }, []);

  const fetchResults = async () => {
    try {
      const response = await financeAPI.listResults();
      setResults(response.data);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to load optimization results'));
    } finally {
      setLoading(false);
    }
  };

  const fetchLatestRun = async () => {
    try {
      const response = await financeAPI.getLatestRun();
      if (response.data && typeof response.data === 'object') {
        if (Object.keys(response.data).length === 1 && 'run_id' in response.data) {
          return;
        }
        setLastRun(response.data);
      }
    } catch (err: any) {
      // No previous runs
    }
  };

  const fetchProcurementOptions = async () => {
    try {
      const response = await procurementAPI.listOptions();
      setProcurementOptions(response.data);
    } catch (err: any) {
      console.error('Failed to load procurement options');
    }
  };

  const handleRunOptimization = async () => {
    setOptimizing(true);
    setError('');

    try {
      const response = await financeAPI.runOptimization(optimizationConfig);
      setLastRun(response.data);
      setRunDialogOpen(false);
      fetchResults();
      
      if (response.data.status === 'OPTIMAL' || response.data.status === 'FEASIBLE') {
        alert(`Optimization completed successfully!\nTotal Cost: $${response.data.total_cost.toLocaleString()}\nItems Optimized: ${response.data.items_optimized}`);
      } else {
        alert(`Optimization failed: ${response.data.message}`);
      }
    } catch (err: any) {
      setError(formatApiError(err, 'Optimization failed'));
    } finally {
      setOptimizing(false);
    }
  };

  const handleOpenEdit = (result: OptimizationResult) => {
    setSelectedResult(result);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = () => {
    if (selectedResult) {
      // Save the edited result to local state
      setEditedResults({
        ...editedResults,
        [selectedResult.id]: selectedResult
      });
      setEditDialogOpen(false);
      setSelectedResult(null);
    }
  };

  const handleRemoveItem = (resultId: number) => {
    if (window.confirm('Are you sure you want to remove this item from the plan?')) {
      setRemovedResultIds(new Set([...removedResultIds, resultId]));
    }
  };

  const handleOpenAddItem = (runId: string) => {
    setSelectedRunId(runId);
    setSelectedDecision(null);
    setAddDialogOpen(true);
  };

  const handleAddItem = () => {
    if (!selectedRunId) return;

    // Create a new result with a temporary negative ID
    const newResult: OptimizationResult = {
      id: -(addedResults.length + 1), // Temporary negative ID
      run_id: selectedRunId,
      run_timestamp: new Date().toISOString(),
      project_id: 1, // Default, should be selected by user
      item_code: '',
      procurement_option_id: procurementOptions.length > 0 ? procurementOptions[0].id : 0,
      purchase_time: 1,
      delivery_time: 1,
      quantity: 1,
      final_cost: 0,
    };

    setSelectedResult(newResult);
    setAddDialogOpen(false);
    setEditDialogOpen(true);
  };

  const handleSaveAddedItem = () => {
    if (selectedResult && selectedResult.id < 0) {
      // This is a new item
      setAddedResults([...addedResults, selectedResult]);
      setEditDialogOpen(false);
      setSelectedResult(null);
    } else {
      handleSaveEdit();
    }
  };

  const handleDeleteOptimization = async () => {
    if (!selectedRunId) return;
    
    try {
      setSaving(true);
      setError('');
      
      await financeAPI.deleteOptimizationResults(selectedRunId);
      
      setDeleteDialogOpen(false);
      setSelectedRunId(null);
      setSuccess('Optimization results deleted successfully. Related finalized decisions have been reverted.');
      
      // Refresh the results
      await fetchResults();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to delete optimization results'));
    } finally {
      setSaving(false);
    }
  };

  const handleSavePlan = async (runId: string, runResults: OptimizationResult[]) => {
    setSaving(true);
    setError('');

    try {
      // Collect item IDs and option IDs from results (including edited ones)
      const itemIds: number[] = [];
      const optionIds: number[] = [];
      
      runResults.forEach(result => {
        // Use edited result if it exists, otherwise use original
        const finalResult = editedResults[result.id] || result;
        
        // We need to map from OptimizationResult to project_item_id
        // For now, we'll save the procurement_option_id
        itemIds.push(result.id);  // This should be project_item_id from database
        optionIds.push(finalResult.procurement_option_id);
      });

      await decisionsAPI.saveBatch(runId, itemIds, optionIds);
      
      alert(`Plan saved successfully! ${runResults.length} decisions recorded.`);
      setEditedResults({});  // Clear edited results
      
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to save plan'));
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPTIMAL':
        return 'success';
      case 'FEASIBLE':
        return 'warning';
      case 'INFEASIBLE':
        return 'error';
      default:
        return 'default';
    }
  };

  // Group results by run
  const groupedResults = results.reduce((acc, result) => {
    // Skip removed items
    if (removedResultIds.has(result.id)) {
      return acc;
    }

    const runId = result.run_id;
    if (!acc[runId]) {
      acc[runId] = {
        run_id: runId,
        run_timestamp: result.run_timestamp,
        results: [],
        total_cost: 0,
      };
    }
    // Use edited result if available
    const finalResult = editedResults[result.id] || result;
    acc[runId].results.push(finalResult);
    acc[runId].total_cost += parseFloat(String(finalResult.final_cost)) || 0;
    return acc;
  }, {} as Record<string, any>);

  // Add manually added items to their respective runs
  addedResults.forEach(result => {
    const runId = result.run_id;
    if (groupedResults[runId]) {
      groupedResults[runId].results.push(result);
      groupedResults[runId].total_cost += parseFloat(String(result.final_cost)) || 0;
    }
  });

  const runIds = Object.keys(groupedResults).sort((a, b) => 
    new Date(groupedResults[b].run_timestamp).getTime() - new Date(groupedResults[a].run_timestamp).getTime()
  );

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
        <Typography variant="h4">Optimization Results</Typography>
        <Box display="flex" gap={2}>
          {(user?.role === 'finance' || user?.role === 'admin') && results.length > 0 && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => {
                setSelectedRunId(results[0]?.run_id || null);
                setDeleteDialogOpen(true);
              }}
              disabled={saving}
            >
              Delete Results
            </Button>
          )}
          {(user?.role === 'finance' || user?.role === 'admin') && (
            <Button
              variant="contained"
              startIcon={<PlayArrowIcon />}
              onClick={() => setRunDialogOpen(true)}
              disabled={optimizing}
            >
              {optimizing ? 'Running...' : 'Run Optimization'}
            </Button>
          )}
        </Box>
      </Box>

      {optimizing && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <CircularProgress size={20} sx={{ mr: 2 }} />
              <Typography variant="h6">Running Optimization...</Typography>
            </Box>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              This may take several minutes. The engine is analyzing all active projects with priority weighting.
            </Typography>
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {lastRun && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Latest Optimization Run
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Box display="flex" alignItems="center">
                  <TrendingUpIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Status
                    </Typography>
                    <Chip 
                      label={lastRun.status} 
                      color={getStatusColor(lastRun.status) as any}
                      size="small"
                    />
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box display="flex" alignItems="center">
                  <AttachMoneyIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Total Cost
                    </Typography>
                    <Typography variant="h6">
                      {formatCurrency(parseFloat(String(lastRun.total_cost)) || 0)}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box display="flex" alignItems="center">
                  <ScheduleIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Items Optimized
                    </Typography>
                    <Typography variant="h6">
                      {lastRun.items_optimized}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Execution Time
                  </Typography>
                  <Typography variant="h6">
                    {lastRun.execution_time_seconds ? lastRun.execution_time_seconds.toFixed(1) : '0.0'}s
                  </Typography>
                </Box>
              </Grid>
            </Grid>
            {lastRun.message && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                {lastRun.message}
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {runIds.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="h6" color="text.secondary" align="center">
              No optimization results available
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Run an optimization to see results here
            </Typography>
          </CardContent>
        </Card>
      ) : (
        runIds.map((runId) => {
          const run = groupedResults[runId];
          const hasEdits = run.results.some((r: OptimizationResult) => editedResults[r.id]);
          
          return (
            <Card key={runId} sx={{ mb: 3 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Box>
                    <Typography variant="h6">
                      Run {runId.slice(0, 8)}...
                    </Typography>
                    {hasEdits && (
                      <Chip 
                        label="Has manual edits" 
                        size="small" 
                        color="warning"
                        sx={{ mt: 0.5 }}
                      />
                    )}
                  </Box>
                  <Box display="flex" gap={1}>
                    <Chip 
                      label={formatCurrency(parseFloat(String(run.total_cost)) || 0)}
                      color="primary"
                      variant="outlined"
                    />
                    <Chip 
                      label={`${run.results.length} items`}
                      color="secondary"
                      variant="outlined"
                    />
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {formatDate(run.run_timestamp)}
                </Typography>

                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<AddIcon />}
                    onClick={() => handleOpenAddItem(runId)}
                  >
                    Add Item to Plan
                  </Button>
                </Box>

                <TableContainer component={Paper} sx={{ mt: 2 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Project</TableCell>
                        <TableCell>Item Code</TableCell>
                        <TableCell>Supplier/Option</TableCell>
                        <TableCell>Purchase Time</TableCell>
                        <TableCell>Delivery Time</TableCell>
                        <TableCell align="right">Quantity</TableCell>
                        <TableCell align="right">Cost</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {run.results.map((result: OptimizationResult) => {
                        const isEdited = !!editedResults[result.id];
                        const isAdded = result.id < 0;
                        return (
                          <TableRow 
                            key={result.id}
                            sx={{ 
                              bgcolor: isAdded ? 'success.light' : (isEdited ? 'action.hover' : 'inherit'),
                              opacity: isAdded ? 0.9 : 1
                            }}
                          >
                            <TableCell>
                              {result.project_id ? `Project ${result.project_id}` : '-'}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontWeight="medium">
                                {result.item_code || '(New Item)'}
                              </Typography>
                              {isAdded && (
                                <Chip label="NEW" size="small" color="success" sx={{ ml: 1 }} />
                              )}
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={`Option #${result.procurement_option_id}`} 
                                size="small"
                                variant={isEdited ? "filled" : "outlined"}
                                color={isEdited ? "warning" : "default"}
                              />
                            </TableCell>
                            <TableCell>
                              <Chip label={`Period ${result.purchase_time}`} size="small" />
                            </TableCell>
                            <TableCell>
                              <Chip label={`Period ${result.delivery_time}`} size="small" color="primary" />
                            </TableCell>
                            <TableCell align="right">{result.quantity}</TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" fontWeight="medium">
                                {formatCurrency(parseFloat(String(result.final_cost)) || 0)}
                              </Typography>
                            </TableCell>
                            <TableCell align="center">
                              <IconButton
                                size="small"
                                onClick={() => handleOpenEdit(result)}
                                title="Edit Decision"
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleRemoveItem(result.id)}
                                title="Remove from Plan"
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Save Plan Button */}
                {(user?.role === 'finance' || user?.role === 'admin' || user?.role === 'pm') && (
                  <Box display="flex" justifyContent="flex-end" mt={2}>
                    <Button
                      variant="contained"
                      color="success"
                      startIcon={<SaveIcon />}
                      onClick={() => handleSavePlan(runId, run.results)}
                      disabled={saving}
                    >
                      {saving ? 'Saving...' : 'Save Plan as Final Decision'}
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>
          );
        })
      )}

      {/* Run Optimization Dialog */}
      <Dialog open={runDialogOpen} onClose={() => setRunDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Portfolio Optimization</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Configure the optimization parameters. The engine will analyze all active projects using priority weights.
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            label="Maximum Time Slots"
            type="number"
            fullWidth
            variant="outlined"
            value={optimizationConfig.max_time_slots}
            onChange={(e) => setOptimizationConfig({
              ...optimizationConfig,
              max_time_slots: parseInt(e.target.value) || 12
            })}
            sx={{ mb: 2 }}
            helperText="Maximum number of time periods to consider"
          />
          <TextField
            margin="dense"
            label="Time Limit (seconds)"
            type="number"
            fullWidth
            variant="outlined"
            value={optimizationConfig.time_limit_seconds}
            onChange={(e) => setOptimizationConfig({
              ...optimizationConfig,
              time_limit_seconds: parseInt(e.target.value) || 300
            })}
            helperText="Maximum time to spend on optimization"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRunDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRunOptimization} variant="contained" disabled={optimizing}>
            {optimizing ? 'Running...' : 'Run Optimization'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Item Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Item to Optimization Plan</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2, mt: 1 }}>
            Add a new item to this optimization plan. You'll be able to configure all details in the next step.
          </Alert>
          <Typography variant="body2" color="text.secondary" paragraph>
            Click "Continue" to proceed with adding a new item to the plan.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddItem} variant="contained" color="primary">
            Continue
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Decision Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedResult && selectedResult.id < 0 ? 'Add New Item' : 'Edit Procurement Decision'}
        </DialogTitle>
        <DialogContent>
          {selectedResult && (
            <>
              <Typography variant="body2" color="text.secondary" paragraph>
                {selectedResult.id < 0 
                  ? 'Configure the details for the new item to add to the plan.'
                  : 'Manually adjust the procurement decision for this item.'}
              </Typography>
              
              <TextField
                margin="dense"
                label="Item Code"
                fullWidth
                variant="outlined"
                value={selectedResult.item_code}
                onChange={(e) => setSelectedResult({
                  ...selectedResult!,
                  item_code: e.target.value
                })}
                disabled={selectedResult.id >= 0}
                sx={{ mb: 2 }}
                helperText={selectedResult.id < 0 ? "Enter the item code" : ""}
              />
              
              <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
                <InputLabel>Procurement Option</InputLabel>
                <Select
                  value={selectedResult.procurement_option_id}
                  label="Procurement Option"
                  onChange={(e) => {
                    if (selectedResult) {
                      const option = procurementOptions.find(o => o.id === Number(e.target.value));
                      setSelectedResult({
                        ...selectedResult,
                        procurement_option_id: Number(e.target.value),
                        item_code: option ? option.item_code : selectedResult.item_code,
                        final_cost: option ? option.base_cost * selectedResult.quantity : selectedResult.final_cost
                      });
                    }
                  }}
                >
                  {procurementOptions
                    .filter(opt => selectedResult.id < 0 || opt.item_code === selectedResult.item_code)
                    .map(option => (
                      <MenuItem key={option.id} value={option.id}>
                        {option.item_code} - {option.supplier_name} - {formatCurrency(option.base_cost)} (Lead: {option.lomc_lead_time})
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>

              <TextField
                margin="dense"
                label="Quantity"
                type="number"
                fullWidth
                variant="outlined"
                value={selectedResult.quantity}
                onChange={(e) => {
                  const qty = parseInt(e.target.value) || 1;
                  const option = procurementOptions.find(o => o.id === selectedResult.procurement_option_id);
                  setSelectedResult({
                    ...selectedResult!,
                    quantity: qty,
                    final_cost: option ? option.base_cost * qty : selectedResult.final_cost
                  });
                }}
                sx={{ mb: 2 }}
              />

              <TextField
                margin="dense"
                label="Purchase Time"
                type="number"
                fullWidth
                variant="outlined"
                value={selectedResult.purchase_time}
                onChange={(e) => setSelectedResult({
                  ...selectedResult!,
                  purchase_time: parseInt(e.target.value) || 1
                })}
                sx={{ mb: 2 }}
                helperText="Time period when purchase order is placed"
              />

              <TextField
                margin="dense"
                label="Delivery Time"
                type="number"
                fullWidth
                variant="outlined"
                value={selectedResult.delivery_time}
                onChange={(e) => setSelectedResult({
                  ...selectedResult!,
                  delivery_time: parseInt(e.target.value) || 1
                })}
                helperText="Time period when item is delivered"
              />

              <Alert severity="success" sx={{ mt: 2 }}>
                <Typography variant="body2" fontWeight="medium">
                  Estimated Cost: {formatCurrency(parseFloat(String(selectedResult.final_cost)) || 0)}
                </Typography>
              </Alert>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSaveAddedItem} 
            variant="contained" 
            color={selectedResult && selectedResult.id < 0 ? "success" : "warning"}
          >
            {selectedResult && selectedResult.id < 0 ? 'Add Item' : 'Save Edit'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Optimization Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Optimization Results</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Are you sure you want to delete the optimization results?
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            This action will:
          </Typography>
          <ul>
            <li>Delete all optimization results</li>
            <li>Revert any finalized decisions back to PROPOSED status</li>
            <li>Cancel associated cash flow events</li>
          </ul>
          <Typography variant="body2" color="error">
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleDeleteOptimization} 
            variant="contained" 
            color="error"
            disabled={saving}
          >
            {saving ? 'Deleting...' : 'Delete Results'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

