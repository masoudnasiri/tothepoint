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
} from '@mui/icons-material';
import { DeliveryOptionsManager } from '../components/DeliveryOptionsManager.tsx';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { useParams, useNavigate } from 'react-router-dom';
import { itemsAPI, itemsMasterAPI, excelAPI } from '../services/api.ts';
import { formatApiError } from '../utils/errorUtils.ts';
import { ProjectItem, ProjectItemCreate, ItemMaster } from '../types/index.ts';

export const ProjectItemsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [items, setItems] = useState<ProjectItem[]>([]);
  const [masterItems, setMasterItems] = useState<ItemMaster[]>([]);
  const [selectedMasterItem, setSelectedMasterItem] = useState<ItemMaster | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deliveryOptionsDialogOpen, setDeliveryOptionsDialogOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<ProjectItem | null>(null);
  
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
  }, [projectId]);

  const fetchItems = async () => {
    if (!projectId) return;
    
    try {
      const response = await itemsAPI.listByProject(parseInt(projectId));
      setItems(response.data);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to load project items'));
    } finally {
      setLoading(false);
    }
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
                    onClick={() => {
                      setSelectedItem(item);
                      setFormData({
                        project_id: item.project_id,
                        item_code: item.item_code,
                        item_name: item.item_name || '',
                        quantity: item.quantity,
                        delivery_options: item.delivery_options || [],
                        external_purchase: item.external_purchase,
                        description: item.description || '',
                      });
                      setEditDialogOpen(true);
                    }}
                    title="Edit Item"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteItem(item.id)}
                    title="Delete Item"
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => openDeliveryOptionsDialog(item)}
                    title="Manage Delivery & Invoice Options"
                    color="info"
                  >
                    <DeliveryIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

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
    </Box>
  );
};
