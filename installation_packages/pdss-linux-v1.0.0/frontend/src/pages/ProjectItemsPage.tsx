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
  FormControlLabel,
  FormControl,
  InputLabel,
  Select,
  Checkbox,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Close as CloseIcon,
  LocalShipping as DeliveryIcon,
  Visibility as VisibilityIcon,
  CheckCircle as FinalizeIcon,
  Unpublished as UnfinalizeIcon,
  Lock as LockedIcon,
} from '@mui/icons-material';
import { DeliveryOptionsManager } from '../components/DeliveryOptionsManager.tsx';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { useParams, useNavigate } from 'react-router-dom';
import { itemsAPI, itemsMasterAPI, excelAPI, deliveryOptionsAPI } from '../services/api.ts';
import { formatApiError } from '../utils/errorUtils.ts';
import { ProjectItem, ProjectItemCreate, ItemMaster } from '../types/index.ts';
import { useAuth } from '../contexts/AuthContext.tsx';

export const ProjectItemsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [items, setItems] = useState<ProjectItem[]>([]);
  const [masterItems, setMasterItems] = useState<ItemMaster[]>([]);
  const [selectedMasterItem, setSelectedMasterItem] = useState<ItemMaster | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deliveryOptionsDialogOpen, setDeliveryOptionsDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ProjectItem | null>(null);
  const [viewItemDeliveryOptions, setViewItemDeliveryOptions] = useState<any[]>([]);
  
  // Pagination and filter state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [finalizedFilter, setFinalizedFilter] = useState<string>('');
  const [externalPurchaseFilter, setExternalPurchaseFilter] = useState<string>('');
  
  // Form data with delivery_options array
  const [formData, setFormData] = useState<ProjectItemCreate>({
    project_id: parseInt(projectId || '0'),
    master_item_id: undefined,
    item_code: '',
    item_name: '',
    quantity: 1,
    delivery_options: [new Date().toISOString().split('T')[0]],
    external_purchase: false,
    description: '',
  });

  // Separate state for date picker input
  const [newDeliveryDate, setNewDeliveryDate] = useState<Date>(new Date());

  useEffect(() => {
    if (projectId) {
      fetchItems();
      fetchMasterItems();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, page, rowsPerPage, searchTerm, statusFilter, finalizedFilter, externalPurchaseFilter]);

  const fetchItems = async () => {
    if (!projectId) return;
    
    setLoading(true);
    try {
      const params: any = {
        skip: page * rowsPerPage,
        limit: rowsPerPage,
      };
      
      if (searchTerm) params.search = searchTerm;
      if (statusFilter) params.status = statusFilter;
      if (finalizedFilter !== '') params.is_finalized = finalizedFilter === 'true';
      if (externalPurchaseFilter !== '') params.external_purchase = externalPurchaseFilter === 'true';
      
      const response = await itemsAPI.listByProject(parseInt(projectId), params);
      setItems(response.data.items || response.data);
      setTotalCount(response.data.total || response.data.length);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to load project items'));
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    setPage(0); // Reset to first page on search
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setStatusFilter('');
    setFinalizedFilter('');
    setExternalPurchaseFilter('');
    setPage(0);
  };

  const fetchMasterItems = async () => {
    try {
      const response = await itemsMasterAPI.list({ active_only: true });
      setMasterItems(response.data);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to load items catalog'));
    }
  };

  const handleCreateItem = async () => {
    try {
      await itemsAPI.create(formData);
      setCreateDialogOpen(false);
      resetForm();
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to create item'));
    }
  };

  const handleEditItem = async () => {
    if (!selectedItem) return;
    
    try {
      await itemsAPI.update(selectedItem.id, formData);
      setEditDialogOpen(false);
      setSelectedItem(null);
      resetForm();
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to update item'));
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    if (!window.confirm('Are you sure you want to delete this item?')) return;
    
    try {
      await itemsAPI.delete(itemId);
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to delete item'));
    }
  };

  const handleFinalizeItem = async (itemId: number) => {
    if (!window.confirm('Are you sure you want to finalize this item? It will be visible in procurement.')) return;
    
    try {
      await itemsAPI.finalize(itemId, { is_finalized: true });
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to finalize item'));
    }
  };

  const handleUnfinalizeItem = async (itemId: number) => {
    if (!window.confirm('Are you sure you want to unfinalize this item? It will be removed from procurement view.')) return;
    
    try {
      await itemsAPI.unfinalize(itemId);
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to unfinalize item'));
    }
  };

  const openDeliveryOptionsDialog = (item: ProjectItem) => {
    setSelectedItem(item);
    setDeliveryOptionsDialogOpen(true);
  };

  const handleMasterItemSelect = (masterItemId: number) => {
    const masterItem = masterItems.find(m => m.id === masterItemId);
    if (masterItem) {
      setSelectedMasterItem(masterItem);
      setFormData({
        ...formData,
        master_item_id: masterItem.id,
        item_code: masterItem.item_code,
        item_name: masterItem.item_name,
      });
    }
  };

  const resetForm = () => {
    setFormData({
      project_id: parseInt(projectId || '0'),
      master_item_id: undefined,
      item_code: '',
      item_name: '',
      quantity: 1,
      delivery_options: [new Date().toISOString().split('T')[0]],
      external_purchase: false,
      description: '',
    });
    setSelectedMasterItem(null);
    setNewDeliveryDate(new Date());
  };

  // Delivery options management functions
  const addDeliveryDate = () => {
    const dateStr = newDeliveryDate.toISOString().split('T')[0];
    if (!formData.delivery_options.includes(dateStr)) {
      setFormData({
        ...formData,
        delivery_options: [...formData.delivery_options, dateStr].sort(),
      });
    }
    setNewDeliveryDate(new Date());
  };

  const removeDeliveryDate = (dateToRemove: string) => {
    if (formData.delivery_options.length > 1) {
      setFormData({
        ...formData,
        delivery_options: formData.delivery_options.filter(d => d !== dateToRemove),
      });
    } else {
      alert('At least one delivery date must be provided');
    }
  };

  const handleExportItems = async () => {
    try {
      const response = await excelAPI.exportItems(parseInt(projectId || '0'));
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `project_${projectId}_items.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to export items');
    }
  };

  const handleImportItems = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await excelAPI.importItems(file);
      fetchItems();
      alert('Items imported successfully');
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to import items'));
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await excelAPI.downloadItemsTemplate();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'project_items_template.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download template');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  // Render form fields function for both create and edit dialogs
  const renderFormFields = () => (
    <>
      {/* Select from Items Master */}
      <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
        <InputLabel>Select Item from Catalog *</InputLabel>
        <Select
          value={formData.master_item_id || ''}
          label="Select Item from Catalog *"
          onChange={(e) => handleMasterItemSelect(e.target.value as number)}
        >
          {masterItems.length === 0 ? (
            <MenuItem disabled>No items in catalog. Create items in Items Master page first.</MenuItem>
          ) : (
            masterItems.map((item) => (
              <MenuItem key={item.id} value={item.id}>
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    {item.item_code}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {item.company} - {item.item_name} {item.model && `(${item.model})`}
                  </Typography>
                </Box>
              </MenuItem>
            ))
          )}
        </Select>
      </FormControl>

      {/* Display selected master item details */}
      {selectedMasterItem && (
        <Paper elevation={0} sx={{ p: 2, mb: 2, bgcolor: 'success.lighter', border: '2px solid', borderColor: 'success.main' }}>
          <Typography variant="subtitle2" color="success.dark" gutterBottom>
            📦 Selected Item
          </Typography>
          <Typography variant="body2" sx={{ mb: 0.5 }}>
            <strong>Code:</strong> {selectedMasterItem.item_code}
          </Typography>
          <Typography variant="body2" sx={{ mb: 0.5 }}>
            <strong>Company:</strong> {selectedMasterItem.company}
          </Typography>
          <Typography variant="body2" sx={{ mb: 0.5 }}>
            <strong>Name:</strong> {selectedMasterItem.item_name}
          </Typography>
          {selectedMasterItem.model && (
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              <strong>Model:</strong> {selectedMasterItem.model}
            </Typography>
          )}
          {selectedMasterItem.category && (
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              <strong>Category:</strong> {selectedMasterItem.category}
            </Typography>
          )}
          <Typography variant="body2">
            <strong>Unit:</strong> {selectedMasterItem.unit}
          </Typography>
        </Paper>
      )}

      <TextField
        margin="dense"
        label="Quantity"
        type="number"
        fullWidth
        variant="outlined"
        value={formData.quantity}
        onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
        sx={{ mb: 2 }}
      />
      
      {/* Delivery Options Manager */}
      <Box sx={{ mb: 2, p: 2, border: '1px solid #ddd', borderRadius: 1 }}>
        <Typography variant="subtitle2" gutterBottom>
          Delivery Date Options (at least 1 required)
        </Typography>
        
        {/* List of current delivery dates */}
        <List dense>
          {formData.delivery_options.map((dateStr, index) => (
            <ListItem key={index} sx={{ bgcolor: 'background.paper', mb: 0.5, borderRadius: 1 }}>
              <ListItemText
                primary={new Date(dateStr).toLocaleDateString('en-US', {
                  weekday: 'short',
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })}
                secondary={index === 0 ? 'Primary option' : `Option ${index + 1}`}
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  size="small"
                  onClick={() => removeDeliveryDate(dateStr)}
                  disabled={formData.delivery_options.length === 1}
                  title={formData.delivery_options.length === 1 ? 'Cannot remove last date' : 'Remove date'}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>

        {/* Add new delivery date */}
        <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Add Delivery Date"
              value={newDeliveryDate}
              onChange={(date) => date && setNewDeliveryDate(date)}
              slotProps={{
                textField: {
                  size: 'small',
                  sx: { flexGrow: 1 }
                }
              }}
            />
          </LocalizationProvider>
          <Button
            variant="outlined"
            onClick={addDeliveryDate}
            startIcon={<AddIcon />}
          >
            Add
          </Button>
        </Box>
      </Box>

      {/* Project-Specific Description */}
      <TextField
        margin="dense"
        label="Project-Specific Description (Optional)"
        fullWidth
        multiline
        rows={4}
        variant="outlined"
        value={formData.description || ''}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        placeholder="Enter project-specific context: usage location, special requirements, installation notes..."
        helperText="Use this for project-specific details. Master item specs are defined in Items Master catalog."
        sx={{ mb: 2 }}
      />

      <FormControlLabel
        control={
          <Checkbox
            checked={formData.external_purchase}
            onChange={(e) => setFormData({ ...formData, external_purchase: e.target.checked })}
          />
        }
        label="External Purchase"
      />
    </>
  );

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/projects')} sx={{ mr: 1 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">Project Items</Typography>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="subtitle1" color="text.secondary">
          Project ID: {projectId}
        </Typography>
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
            Import Items
            <input
              type="file"
              hidden
              accept=".xlsx,.xls"
              onChange={handleImportItems}
            />
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExportItems}
            sx={{ mr: 1 }}
          >
            Export Items
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              resetForm();
              setCreateDialogOpen(true);
            }}
          >
            Add Item
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Search and Filter Bar */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
          <TextField
            label="Search"
            placeholder="Search by code, name, or description..."
            value={searchTerm}
            onChange={handleSearchChange}
            size="small"
            sx={{ minWidth: 300, flexGrow: 1 }}
          />
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="PENDING">PENDING</MenuItem>
              <MenuItem value="SUGGESTED">SUGGESTED</MenuItem>
              <MenuItem value="DECIDED">DECIDED</MenuItem>
              <MenuItem value="PROCURED">PROCURED</MenuItem>
              <MenuItem value="FULFILLED">FULFILLED</MenuItem>
              <MenuItem value="PAID">PAID</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Finalized</InputLabel>
            <Select
              value={finalizedFilter}
              label="Finalized"
              onChange={(e) => {
                setFinalizedFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>External Purchase</InputLabel>
            <Select
              value={externalPurchaseFilter}
              label="External Purchase"
              onChange={(e) => {
                setExternalPurchaseFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            onClick={handleClearFilters}
            size="small"
          >
            Clear Filters
          </Button>

          <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
            Total: {totalCount} item{totalCount !== 1 ? 's' : ''}
          </Typography>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Item Code</TableCell>
              <TableCell>Item Name</TableCell>
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="center">Delivery Options</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">External Purchase</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {item.item_code}
                  </Typography>
                </TableCell>
                <TableCell>{item.item_name}</TableCell>
                <TableCell align="right">{item.quantity}</TableCell>
                <TableCell align="center">
                  <Box>
                    {item.delivery_options && item.delivery_options.length > 0 ? (
                      <>
                        <Typography variant="body2">
                          {new Date(item.delivery_options[0]).toLocaleDateString()}
                        </Typography>
                        {item.delivery_options.length > 1 && (
                          <Chip
                            label={`+${item.delivery_options.length - 1} more`}
                            size="small"
                            color="info"
                            variant="outlined"
                            sx={{ mt: 0.5 }}
                          />
                        )}
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary">-</Typography>
                    )}
                  </Box>
                </TableCell>
                <TableCell align="center">
                  <Box display="flex" flexDirection="column" gap={0.5} alignItems="center">
                    <Chip 
                      label={item.status} 
                      size="small"
                      color={
                        item.status === 'PENDING' ? 'default' :
                        item.status === 'SUGGESTED' ? 'info' :
                        item.status === 'DECIDED' ? 'primary' :
                        item.status === 'PROCURED' ? 'secondary' :
                        item.status === 'FULFILLED' ? 'warning' :
                        item.status === 'PAID' ? 'success' : 'default'
                      }
                    />
                    {item.is_finalized && (
                      <Chip
                        label="FINALIZED"
                        size="small"
                        color="success"
                        variant="filled"
                        icon={<FinalizeIcon />}
                      />
                    )}
                  </Box>
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={item.external_purchase ? 'Yes' : 'No'}
                    size="small"
                    color={item.external_purchase ? 'warning' : 'default'}
                  />
                </TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small"
                    onClick={async () => {
                      setSelectedItem(item);
                      // Fetch delivery options for this item
                      try {
                        const response = await deliveryOptionsAPI.listByItem(item.id);
                        setViewItemDeliveryOptions(response.data);
                      } catch (err) {
                        console.error('Failed to load delivery options', err);
                        setViewItemDeliveryOptions([]);
                      }
                      setViewDialogOpen(true);
                    }}
                    title="View Item Details"
                    color="primary"
                  >
                    <VisibilityIcon />
                  </IconButton>
                  {/* Edit button - disabled if procurement has finalized decision */}
                  <IconButton
                    size="small"
                    onClick={() => {
                      setSelectedItem(item);
                      setFormData({
                        project_id: item.project_id,
                        master_item_id: item.master_item_id,
                        item_code: item.item_code,
                        item_name: item.item_name || '',
                        quantity: item.quantity,
                        delivery_options: item.delivery_options || [],
                        external_purchase: item.external_purchase,
                        description: item.description || '',
                      });
                      
                      // Load the master item for display
                      if (item.master_item_id) {
                        itemsMasterAPI.get(item.master_item_id).then(response => {
                          setSelectedMasterItem(response.data);
                        }).catch(err => console.error('Failed to load master item'));
                      }
                      
                      setEditDialogOpen(true);
                    }}
                    title={
                      item.has_finalized_decision
                        ? "Cannot edit: Procurement has finalized decision"
                        : "Edit Item"
                    }
                    disabled={item.has_finalized_decision}
                  >
                    <EditIcon />
                  </IconButton>
                  
                  {/* Delete button - disabled if procurement has finalized decision */}
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteItem(item.id)}
                    title={
                      item.has_finalized_decision
                        ? "Cannot delete: Procurement has finalized decision"
                        : "Delete Item"
                    }
                    color="error"
                    disabled={item.has_finalized_decision}
                  >
                    <DeleteIcon />
                  </IconButton>
                  
                  {/* Delivery Options */}
                  <IconButton
                    size="small"
                    onClick={() => openDeliveryOptionsDialog(item)}
                    title="Manage Delivery & Invoice Options"
                    color="info"
                  >
                    <DeliveryIcon />
                  </IconButton>
                  
                  {/* Finalize/Unfinalize toggle - for PMO/Admin only */}
                  {(user?.role === 'pmo' || user?.role === 'admin') && (
                    <>
                      {!item.is_finalized ? (
                        <IconButton
                          size="small"
                          onClick={() => handleFinalizeItem(item.id)}
                          title="Finalize Item (makes visible in procurement)"
                          color="success"
                        >
                          <FinalizeIcon />
                        </IconButton>
                      ) : (
                        <IconButton
                          size="small"
                          onClick={() => handleUnfinalizeItem(item.id)}
                          title={
                            item.has_finalized_decision
                              ? "Cannot unfinalize: Procurement has finalized decision"
                              : "Unfinalize Item (remove from procurement)"
                          }
                          color="warning"
                          disabled={item.has_finalized_decision}
                        >
                          {item.has_finalized_decision ? <LockedIcon /> : <UnfinalizeIcon />}
                        </IconButton>
                      )}
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <Paper sx={{ mt: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" p={2}>
          <Typography variant="body2" color="text.secondary">
            Showing {items.length === 0 ? 0 : page * rowsPerPage + 1} - {Math.min((page + 1) * rowsPerPage, totalCount)} of {totalCount}
          </Typography>
          <Box display="flex" gap={1} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>Per Page</InputLabel>
              <Select
                value={rowsPerPage}
                label="Per Page"
                onChange={handleChangeRowsPerPage}
              >
                <MenuItem value={10}>10</MenuItem>
                <MenuItem value={25}>25</MenuItem>
                <MenuItem value={50}>50</MenuItem>
                <MenuItem value={100}>100</MenuItem>
              </Select>
            </FormControl>
            <Button
              size="small"
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </Button>
            <Typography variant="body2" sx={{ px: 2 }}>
              Page {page + 1} of {Math.max(1, Math.ceil(totalCount / rowsPerPage))}
            </Typography>
            <Button
              size="small"
              disabled={(page + 1) * rowsPerPage >= totalCount}
              onClick={() => setPage(page + 1)}
            >
              Next
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Create Item Dialog */}
      <Dialog 
        open={createDialogOpen} 
        onClose={() => {
          setCreateDialogOpen(false);
          resetForm();
          setSelectedItem(null);
        }} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Add New Item</DialogTitle>
        <DialogContent>
          {renderFormFields()}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateItem} 
            variant="contained"
            disabled={!formData.item_code || !formData.delivery_options || formData.delivery_options.length === 0}
          >
            Add Item
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Item Dialog */}
      <Dialog 
        open={editDialogOpen} 
        onClose={() => {
          setEditDialogOpen(false);
        }} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>Edit Item</DialogTitle>
        <DialogContent>
          {renderFormFields()}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setEditDialogOpen(false);
            resetForm();
            setSelectedItem(null);
          }}>Cancel</Button>
          <Button 
            onClick={handleEditItem} 
            variant="contained"
            disabled={!formData.item_code || !formData.delivery_options || formData.delivery_options.length === 0}
          >
            Update Item
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delivery & Invoice Options Dialog */}
      <Dialog 
        open={deliveryOptionsDialogOpen} 
        onClose={() => setDeliveryOptionsDialogOpen(false)} 
        maxWidth="lg" 
        fullWidth
      >
        <DialogTitle>
          Delivery & Invoice Configuration
        </DialogTitle>
        <DialogContent>
          {selectedItem && (
            <DeliveryOptionsManager 
              projectItemId={selectedItem.id} 
              itemCode={selectedItem.item_code}
              availableDeliveryDates={selectedItem.delivery_options || []}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeliveryOptionsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* View Item Dialog */}
      <Dialog 
        open={viewDialogOpen} 
        onClose={() => {
          setViewDialogOpen(false);
          setSelectedItem(null);
        }} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>Item Details</DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Box sx={{ pt: 2 }}>
              <Paper elevation={0} sx={{ p: 3, mb: 2, bgcolor: 'primary.lighter' }}>
                <Typography variant="h6" gutterBottom color="primary.dark">
                  📦 {selectedItem.item_code}
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  {selectedItem.item_name}
                </Typography>
              </Paper>

              <Box sx={{ display: 'grid', gap: 2 }}>
                <Paper elevation={1} sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Quantity
                  </Typography>
                  <Typography variant="h6">{selectedItem.quantity}</Typography>
                </Paper>

                {selectedItem.description && (
                  <Paper elevation={1} sx={{ p: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                      Description
                    </Typography>
                    <Typography variant="body1">{selectedItem.description}</Typography>
                  </Paper>
                )}

                <Paper elevation={1} sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Delivery & Invoice Options
                  </Typography>
                  {viewItemDeliveryOptions && viewItemDeliveryOptions.length > 0 ? (
                    <Box sx={{ mt: 2 }}>
                      {viewItemDeliveryOptions.map((option, index) => (
                        <Paper key={option.id} elevation={2} sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                          <Typography variant="body2" fontWeight="medium" gutterBottom>
                            Option {index + 1} - Slot {option.slot_number}
                          </Typography>
                          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mt: 1 }}>
                            <Box>
                              <Typography variant="caption" color="textSecondary">Delivery Date:</Typography>
                              <Typography variant="body2">{option.delivery_date}</Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="textSecondary">Invoice Amount/Unit:</Typography>
                              <Typography variant="body2">${option.invoice_amount_per_unit}</Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="textSecondary">Invoice Timing:</Typography>
                              <Typography variant="body2">
                                {option.invoice_timing_type === 'ABSOLUTE' 
                                  ? `Absolute: ${option.invoice_issue_date}`
                                  : `Relative: ${option.invoice_days_after_delivery} days after delivery`
                                }
                              </Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="textSecondary">Total Invoice:</Typography>
                              <Typography variant="body2" fontWeight="medium">
                                ${(option.invoice_amount_per_unit * selectedItem.quantity).toFixed(2)}
                              </Typography>
                            </Box>
                          </Box>
                        </Paper>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      No delivery & invoice options configured
                    </Typography>
                  )}
                </Paper>

                <Paper elevation={1} sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    External Purchase
                  </Typography>
                  <Chip 
                    label={selectedItem.external_purchase ? 'Yes' : 'No'} 
                    color={selectedItem.external_purchase ? 'warning' : 'default'}
                  />
                </Paper>

                {selectedItem.file_name && (
                  <Paper elevation={1} sx={{ p: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                      Attached File
                    </Typography>
                    <Typography variant="body2">📎 {selectedItem.file_name}</Typography>
                  </Paper>
                )}

                <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="caption" color="textSecondary">
                    Created: {new Date(selectedItem.created_at).toLocaleString()}
                  </Typography>
                  {selectedItem.updated_at && (
                    <>
                      <br />
                      <Typography variant="caption" color="textSecondary">
                        Updated: {new Date(selectedItem.updated_at).toLocaleString()}
                      </Typography>
                    </>
                  )}
                </Paper>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
