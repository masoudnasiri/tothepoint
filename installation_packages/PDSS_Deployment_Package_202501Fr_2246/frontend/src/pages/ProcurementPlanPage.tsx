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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Grid,
  Divider,
  InputAdornment,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  CheckCircle as ConfirmIcon,
  ThumbUp as AcceptIcon,
  Receipt as InvoiceIcon,
  FileDownload as ExportIcon,
  LocalShipping as ShippingIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { procurementPlanAPI, projectsAPI } from '../services/api.ts';
import {
  ProcurementPlanItem,
  DeliveryStatus,
  ProcurementDeliveryConfirmation,
  PMDeliveryAcceptance,
  ActualInvoiceData,
} from '../types/index.ts';

export const ProcurementPlanPage: React.FC = () => {
  const { user } = useAuth();
  const [items, setItems] = useState<ProcurementPlanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [projectFilter, setProjectFilter] = useState<number | ''>('');
  const [projects, setProjects] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  
  // Dialogs
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [acceptDialogOpen, setAcceptDialogOpen] = useState(false);
  const [invoiceDialogOpen, setInvoiceDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ProcurementPlanItem | null>(null);
  
  // Form data
  const [confirmData, setConfirmData] = useState<ProcurementDeliveryConfirmation>({
    actual_delivery_date: new Date().toISOString().split('T')[0],
    is_correct_item: true,
    serial_number: '',
    delivery_notes: '',
  });
  
  const [acceptData, setAcceptData] = useState<PMDeliveryAcceptance>({
    is_accepted_for_project: true,
    customer_delivery_date: '',
    acceptance_notes: '',
  });
  
  const [invoiceData, setInvoiceData] = useState<ActualInvoiceData>({
    actual_invoice_issue_date: new Date().toISOString().split('T')[0],
    actual_invoice_amount: 0,
    actual_invoice_received_date: '',
    notes: '',
  });

  useEffect(() => {
    fetchItems();
    fetchProjects();
  }, [statusFilter, projectFilter]);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (statusFilter) params.status_filter = statusFilter;
      if (projectFilter) params.project_id = projectFilter;
      
      const response = await procurementPlanAPI.list(params);
      setItems(response.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load procurement plan');
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await projectsAPI.list();
      setProjects(response.data);
    } catch (err) {
      console.error('Failed to load projects:', err);
    }
  };

  const handleViewItem = async (item: ProcurementPlanItem) => {
    try {
      const response = await procurementPlanAPI.get(item.id);
      setSelectedItem(response.data);
      setViewDialogOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load item details');
    }
  };

  const handleConfirmDelivery = async () => {
    if (!selectedItem) return;
    
    try {
      await procurementPlanAPI.confirmDelivery(selectedItem.id, confirmData);
      setSuccess('Delivery confirmed successfully!');
      setConfirmDialogOpen(false);
      fetchItems();
      // Reset form
      setConfirmData({
        actual_delivery_date: new Date().toISOString().split('T')[0],
        is_correct_item: true,
        serial_number: '',
        delivery_notes: '',
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to confirm delivery');
    }
  };

  const handleAcceptDelivery = async () => {
    if (!selectedItem) return;
    
    try {
      await procurementPlanAPI.acceptDelivery(selectedItem.id, acceptData);
      setSuccess('Delivery accepted successfully!');
      setAcceptDialogOpen(false);
      fetchItems();
      // Reset form
      setAcceptData({
        is_accepted_for_project: true,
        customer_delivery_date: '',
        acceptance_notes: '',
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to accept delivery');
    }
  };

  const handleEnterInvoice = async () => {
    if (!selectedItem) return;
    
    // Validation
    if (!invoiceData.actual_invoice_amount || invoiceData.actual_invoice_amount <= 0) {
      setError('Invoice amount must be greater than 0');
      return;
    }
    
    try {
      await procurementPlanAPI.enterInvoice(selectedItem.id, invoiceData);
      setSuccess('Invoice data entered successfully!');
      setInvoiceDialogOpen(false);
      fetchItems();
      // Reset form
      setInvoiceData({
        actual_invoice_issue_date: new Date().toISOString().split('T')[0],
        actual_invoice_amount: 0,
        actual_invoice_received_date: '',
        notes: '',
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to enter invoice data');
    }
  };

  const handleExport = async () => {
    try {
      const response = await procurementPlanAPI.export();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `procurement_plan_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSuccess('Export completed successfully!');
    } catch (err: any) {
      setError('Failed to export procurement plan');
    }
  };

  const getStatusColor = (status: DeliveryStatus): 'default' | 'warning' | 'success' => {
    switch (status) {
      case 'AWAITING_DELIVERY':
        return 'default';
      case 'CONFIRMED_BY_PROCUREMENT':
        return 'warning';
      case 'DELIVERY_COMPLETE':
        return 'success';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: DeliveryStatus): string => {
    switch (status) {
      case 'AWAITING_DELIVERY':
        return 'Awaiting Delivery';
      case 'CONFIRMED_BY_PROCUREMENT':
        return 'Confirmed by Procurement';
      case 'DELIVERY_COMPLETE':
        return 'Delivery Complete';
      default:
        return status;
    }
  };

  const isProcurementTeam = user?.role === 'procurement' || user?.role === 'admin' || user?.role === 'finance';
  const isPM = user?.role === 'pm' || user?.role === 'pmo' || user?.role === 'admin';

  // Filter items based on search term
  const filteredItems = items.filter(item => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    
    // Search in common fields
    if (item.item_code?.toLowerCase().includes(searchLower)) return true;
    if (item.item_name?.toLowerCase().includes(searchLower)) return true;
    if (item.item_description?.toLowerCase().includes(searchLower)) return true;
    if (item.project_name?.toLowerCase().includes(searchLower)) return true;
    if (item.project_code?.toLowerCase().includes(searchLower)) return true;
    if (item.serial_number?.toLowerCase().includes(searchLower)) return true;
    if (item.delivery_status?.toLowerCase().includes(searchLower)) return true;
    
    // Search in procurement-specific fields (if visible)
    if (isProcurementTeam) {
      if (item.supplier_name?.toLowerCase().includes(searchLower)) return true;
      if (item.final_cost?.toString().includes(searchLower)) return true;
      if (item.procurement_delivery_notes?.toLowerCase().includes(searchLower)) return true;
    }
    
    // Search in PM-specific fields (if visible)
    if (isPM) {
      if (item.pm_acceptance_notes?.toLowerCase().includes(searchLower)) return true;
    }
    
    // Search in dates
    if (item.delivery_date?.includes(searchTerm)) return true;
    if (item.actual_delivery_date?.includes(searchTerm)) return true;
    if (item.customer_delivery_date?.includes(searchTerm)) return true;
    
    return false;
  });

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
        <Typography variant="h4" component="h1">
          <ShippingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Procurement Plan & Delivery Tracking
        </Typography>
        <Button
          variant="outlined"
          startIcon={<ExportIcon />}
          onClick={handleExport}
        >
          Export to Excel
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess('')} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Search"
              placeholder="Search by item code, name, project, supplier, etc..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              variant="outlined"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Delivery Status</InputLabel>
              <Select
                value={statusFilter}
                label="Delivery Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="AWAITING_DELIVERY">Awaiting Delivery</MenuItem>
                <MenuItem value="CONFIRMED_BY_PROCUREMENT">Confirmed by Procurement</MenuItem>
                <MenuItem value="DELIVERY_COMPLETE">Delivery Complete</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Project</InputLabel>
              <Select
                value={projectFilter}
                label="Project"
                onChange={(e) => setProjectFilter(e.target.value as number | '')}
              >
                <MenuItem value="">All Projects</MenuItem>
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Total Items</Typography>
            <Typography variant="h4">{filteredItems.length}</Typography>
            {searchTerm && (
              <Typography variant="caption" color="textSecondary">
                (filtered from {items.length})
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Awaiting Delivery</Typography>
            <Typography variant="h4">
              {filteredItems.filter(i => i.delivery_status === 'AWAITING_DELIVERY').length}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6">Completed</Typography>
            <Typography variant="h4">
              {filteredItems.filter(i => i.delivery_status === 'DELIVERY_COMPLETE').length}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Main Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Item Code</TableCell>
              <TableCell>Item Name</TableCell>
              <TableCell>Project</TableCell>
              {isProcurementTeam && <TableCell>Supplier</TableCell>}
              <TableCell align="right">Quantity</TableCell>
              {isProcurementTeam && <TableCell align="right">Cost</TableCell>}
              <TableCell>Planned Delivery</TableCell>
              <TableCell>Actual Delivery</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={isProcurementTeam ? 10 : 8} align="center">
                  <Typography color="textSecondary">
                    {searchTerm || statusFilter || projectFilter
                      ? 'No items match your search criteria.'
                      : 'No items found. Items will appear here after decisions are finalized.'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredItems.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell>{item.item_code}</TableCell>
                  <TableCell>{item.item_name || 'N/A'}</TableCell>
                  <TableCell>{item.project_name || 'N/A'}</TableCell>
                  {isProcurementTeam && <TableCell>{item.supplier_name || 'N/A'}</TableCell>}
                  <TableCell align="right">{item.quantity}</TableCell>
                  {isProcurementTeam && (
                    <TableCell align="right">
                      ${item.final_cost?.toLocaleString() || 'N/A'}
                    </TableCell>
                  )}
                  <TableCell>{item.delivery_date}</TableCell>
                  <TableCell>{item.actual_delivery_date || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={getStatusLabel(item.delivery_status)}
                      color={getStatusColor(item.delivery_status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => handleViewItem(item)}
                      title="View Details"
                    >
                      <ViewIcon />
                    </IconButton>
                    
                    {/* Procurement Team: Confirm Delivery */}
                    {isProcurementTeam && item.delivery_status === 'AWAITING_DELIVERY' && (
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => {
                          setSelectedItem(item);
                          setConfirmDialogOpen(true);
                        }}
                        title="Confirm Delivery"
                      >
                        <ConfirmIcon />
                      </IconButton>
                    )}
                    
                    {/* PM: Accept Delivery */}
                    {isPM && (item.delivery_status === 'CONFIRMED_BY_PROCUREMENT' || item.delivery_status === 'AWAITING_DELIVERY') && !item.is_accepted_by_pm && (
                      <IconButton
                        size="small"
                        color="info"
                        onClick={() => {
                          setSelectedItem(item);
                          setAcceptDialogOpen(true);
                        }}
                        title="Accept Delivery"
                      >
                        <AcceptIcon />
                      </IconButton>
                    )}
                    
                    {/* Procurement Team: Enter Invoice (only when delivery complete) */}
                    {isProcurementTeam && item.delivery_status === 'DELIVERY_COMPLETE' && !item.actual_invoice_issue_date && (
                      <IconButton
                        size="small"
                        color="warning"
                        onClick={() => {
                          setSelectedItem(item);
                          setInvoiceData({
                            ...invoiceData,
                            actual_invoice_amount: item.final_cost || 0,
                          });
                          setInvoiceDialogOpen(true);
                        }}
                        title="Enter Invoice"
                      >
                        <InvoiceIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* View Details Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Item Details</DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">Item Code</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.item_code}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">Item Name</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.item_name || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="textSecondary">Description</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.item_description || 'No description'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">Project</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.project_name || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">Quantity</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.quantity}</Typography>
                </Grid>
                
                {isProcurementTeam && (
                  <>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">Supplier</Typography>
                      <Typography variant="body1" gutterBottom>{selectedItem.supplier_name || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">Final Cost</Typography>
                      <Typography variant="body1" gutterBottom>${selectedItem.final_cost?.toLocaleString() || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">Purchase Date</Typography>
                      <Typography variant="body1" gutterBottom>{selectedItem.purchase_date || 'N/A'}</Typography>
                    </Grid>
                  </>
                )}
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">Planned Delivery</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.delivery_date}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">Actual Delivery</Typography>
                  <Typography variant="body1" gutterBottom>{selectedItem.actual_delivery_date || 'Not yet delivered'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" color="textSecondary">Delivery Status</Typography>
                  <Chip
                    label={getStatusLabel(selectedItem.delivery_status)}
                    color={getStatusColor(selectedItem.delivery_status)}
                    size="small"
                  />
                </Grid>
                
                {selectedItem.serial_number && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">Serial Number</Typography>
                    <Typography variant="body1" gutterBottom>{selectedItem.serial_number}</Typography>
                  </Grid>
                )}
                
                {isProcurementTeam && selectedItem.procurement_delivery_notes && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">Procurement Notes</Typography>
                    <Typography variant="body1" gutterBottom>{selectedItem.procurement_delivery_notes}</Typography>
                  </Grid>
                )}
                
                {isPM && selectedItem.pm_acceptance_notes && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">PM Acceptance Notes</Typography>
                    <Typography variant="body1" gutterBottom>{selectedItem.pm_acceptance_notes}</Typography>
                  </Grid>
                )}
                
                {isProcurementTeam && selectedItem.actual_invoice_issue_date && (
                  <>
                    <Grid item xs={12}><Divider sx={{ my: 1 }} /></Grid>
                    <Grid item xs={12}>
                      <Typography variant="h6" gutterBottom>Invoice Information</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">Invoice Issue Date</Typography>
                      <Typography variant="body1" gutterBottom>{selectedItem.actual_invoice_issue_date}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" color="textSecondary">Invoice Amount</Typography>
                      <Typography variant="body1" gutterBottom>${selectedItem.actual_invoice_amount?.toLocaleString() || 'N/A'}</Typography>
                    </Grid>
                    {selectedItem.actual_invoice_received_date && (
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="textSecondary">Invoice Received Date</Typography>
                        <Typography variant="body1" gutterBottom>{selectedItem.actual_invoice_received_date}</Typography>
                      </Grid>
                    )}
                  </>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Confirm Delivery Dialog (Procurement Team) */}
      <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Confirm Supplier Delivery</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Actual Delivery Date"
              type="date"
              value={confirmData.actual_delivery_date}
              onChange={(e) => setConfirmData({ ...confirmData, actual_delivery_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              sx={{ mb: 2 }}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={confirmData.is_correct_item}
                  onChange={(e) => setConfirmData({ ...confirmData, is_correct_item: e.target.checked })}
                />
              }
              label="Item matches the order specification"
            />
            <TextField
              fullWidth
              label="Serial Number (Optional)"
              value={confirmData.serial_number}
              onChange={(e) => setConfirmData({ ...confirmData, serial_number: e.target.value })}
              sx={{ mb: 2, mt: 2 }}
            />
            <TextField
              fullWidth
              label="Delivery Notes (Optional)"
              multiline
              rows={3}
              value={confirmData.delivery_notes}
              onChange={(e) => setConfirmData({ ...confirmData, delivery_notes: e.target.value })}
              placeholder="e.g., Box was damaged but contents are fine"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="success"
            onClick={handleConfirmDelivery}
            disabled={!confirmData.is_correct_item}
          >
            Confirm Delivery
          </Button>
        </DialogActions>
      </Dialog>

      {/* Accept Delivery Dialog (PM) */}
      <Dialog open={acceptDialogOpen} onClose={() => setAcceptDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Accept Delivery for Project</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={acceptData.is_accepted_for_project}
                  onChange={(e) => setAcceptData({ ...acceptData, is_accepted_for_project: e.target.checked })}
                />
              }
              label="I accept this item for my project"
            />
            <TextField
              fullWidth
              label="Customer Delivery Date (Optional)"
              type="date"
              value={acceptData.customer_delivery_date}
              onChange={(e) => setAcceptData({ ...acceptData, customer_delivery_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              sx={{ mb: 2, mt: 2 }}
              helperText="When the item was (or will be) delivered to the end customer"
            />
            <TextField
              fullWidth
              label="Acceptance Notes (Optional)"
              multiline
              rows={3}
              value={acceptData.acceptance_notes}
              onChange={(e) => setAcceptData({ ...acceptData, acceptance_notes: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAcceptDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="info"
            onClick={handleAcceptDelivery}
            disabled={!acceptData.is_accepted_for_project}
          >
            Accept Delivery
          </Button>
        </DialogActions>
      </Dialog>

      {/* Enter Invoice Dialog (Procurement Team) */}
      <Dialog open={invoiceDialogOpen} onClose={() => setInvoiceDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Enter Invoice Data</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              Invoice can only be entered when delivery is complete (confirmed by both Procurement and PM).
            </Alert>
            <TextField
              fullWidth
              label="Invoice Issue Date"
              type="date"
              value={invoiceData.actual_invoice_issue_date}
              onChange={(e) => setInvoiceData({ ...invoiceData, actual_invoice_issue_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              sx={{ mb: 2 }}
              required
            />
            <TextField
              fullWidth
              label="Invoice Amount"
              type="number"
              value={invoiceData.actual_invoice_amount}
              onChange={(e) => setInvoiceData({ ...invoiceData, actual_invoice_amount: parseFloat(e.target.value) })}
              sx={{ mb: 2 }}
              required
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              fullWidth
              label="Invoice Received Date (Optional)"
              type="date"
              value={invoiceData.actual_invoice_received_date}
              onChange={(e) => setInvoiceData({ ...invoiceData, actual_invoice_received_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
              sx={{ mb: 2 }}
              helperText="When payment was actually received from customer"
            />
            <TextField
              fullWidth
              label="Notes (Optional)"
              multiline
              rows={3}
              value={invoiceData.notes}
              onChange={(e) => setInvoiceData({ ...invoiceData, notes: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInvoiceDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="warning"
            onClick={handleEnterInvoice}
          >
            Enter Invoice
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

