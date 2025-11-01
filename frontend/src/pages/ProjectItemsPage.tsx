import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
import { ProjectItem, ProjectItemCreate, ItemMaster, ItemSubItem } from '../types/index.ts';
import { useAuth } from '../contexts/AuthContext.tsx';

export const ProjectItemsPage: React.FC = () => {
  const { t } = useTranslation();
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [items, setItems] = useState<ProjectItem[]>([]);
  const [masterItems, setMasterItems] = useState<ItemMaster[]>([]);
  const [selectedMasterItem, setSelectedMasterItem] = useState<ItemMaster | null>(null);
  const [masterSubItems, setMasterSubItems] = useState<ItemSubItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
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
      setError(formatApiError(err, t('projectItems.failedToLoadProjectItems')));
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
      setError(formatApiError(err, t('projectItems.failedToLoadItemsCatalog')));
    }
  };

  const handleCreateItem = async () => {
    try {
      // Ensure we send all sub-items (default 0 if not edited)
      const subItemsMap = new Map((formData.sub_items || []).map(s => [s.sub_item_id, s.quantity]));
      const completeSubItems = masterSubItems.map(si => ({ sub_item_id: si.id, quantity: subItemsMap.get(si.id) ?? 0 }));
      const payload = { ...formData, sub_items: completeSubItems } as any;
      await itemsAPI.create(payload);
      setCreateDialogOpen(false);
      resetForm();
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, t('projectItems.failedToCreateItem')));
    }
  };

  const handleEditItem = async () => {
    if (!selectedItem) return;
    
    try {
      const subItemsMap = new Map((formData.sub_items || []).map(s => [s.sub_item_id, s.quantity]));
      const completeSubItems = masterSubItems.map(si => ({ sub_item_id: si.id, quantity: subItemsMap.get(si.id) ?? 0 }));
      const payload = { ...formData, sub_items: completeSubItems } as any;
      await itemsAPI.update(selectedItem.id, payload);
      setEditDialogOpen(false);
      setSelectedItem(null);
      resetForm();
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, t('projectItems.failedToUpdateItem')));
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    if (!window.confirm(t('projectItems.areYouSureDelete'))) return;
    
    try {
      await itemsAPI.delete(itemId);
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, t('projectItems.failedToDeleteItem')));
    }
  };

  const handleFinalizeItem = async (itemId: number) => {
    if (!window.confirm(t('projectItems.areYouSureFinalize'))) return;
    
    try {
      await itemsAPI.finalize(itemId, { is_finalized: true });
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, t('projectItems.failedToFinalizeItem')));
    }
  };

  const handleUnfinalizeItem = async (itemId: number) => {
    if (!window.confirm(t('projectItems.areYouSureUnfinalize'))) return;
    
    try {
      await itemsAPI.unfinalize(itemId);
      fetchItems();
    } catch (err: any) {
      setError(formatApiError(err, t('projectItems.failedToUnfinalizeItem')));
    }
  };

  const handleFinalizeAllItems = async () => {
    if (!projectId) return;
    
    if (!window.confirm(t('projectItems.areYouSureFinalizeAll'))) return;
    
    try {
      const response = await itemsAPI.finalizeAll(parseInt(projectId));
      fetchItems();
      setSuccess(`Successfully finalized ${response.data.finalized_count} items`);
    } catch (err: any) {
      setError(formatApiError(err, t('projectItems.failedToFinalizeAllItems')));
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
      // Load sub-items for this master item
      itemsMasterAPI.listSubItems(masterItem.id).then(res => setMasterSubItems(res.data || [])).catch(() => setMasterSubItems([]));
      setFormData({
        ...formData,
        master_item_id: masterItem.id,
        item_code: masterItem.item_code,
        item_name: masterItem.item_name,
        // Initialize sub_items quantities to zero for all available sub-items
        sub_items: [],
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
      alert(t('projectItems.atLeastOneDeliveryDateRequired'));
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
      setError(t('projectItems.failedToExportItems'));
    }
  };

  const handleImportItems = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await excelAPI.importItems(file);
      fetchItems();
      alert(t('projectItems.itemsImportedSuccessfully'));
    } catch (err: any) {
      setError(formatApiError(err, t('projectItems.failedToImportItems')));
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
      setError(t('projectItems.failedToDownloadTemplate'));
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
        <InputLabel>{t('projectItems.selectItemFromCatalog')}</InputLabel>
        <Select
          value={formData.master_item_id || ''}
          label={t('projectItems.selectItemFromCatalog')}
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
            📦 {t('projectItems.selectedItem')}
          </Typography>
          <Typography variant="body2" sx={{ mb: 0.5 }}>
            <strong>{t('projectItems.code')}:</strong> {selectedMasterItem.item_code}
          </Typography>
          <Typography variant="body2" sx={{ mb: 0.5 }}>
            <strong>{t('projectItems.company')}:</strong> {selectedMasterItem.company}
          </Typography>
          <Typography variant="body2" sx={{ mb: 0.5 }}>
            <strong>{t('projectItems.name')}:</strong> {selectedMasterItem.item_name}
          </Typography>
          {selectedMasterItem.model && (
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              <strong>{t('projectItems.model')}:</strong> {selectedMasterItem.model}
            </Typography>
          )}
          {selectedMasterItem.category && (
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              <strong>{t('projectItems.category')}:</strong> {selectedMasterItem.category}
            </Typography>
          )}
          <Typography variant="body2">
            <strong>{t('projectItems.unit')}:</strong> {selectedMasterItem.unit}
          </Typography>
          {(selectedMasterItem as any).part_number && (
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              <strong>{t('projectItems.partNumber') || 'Part Number'}:</strong> {(selectedMasterItem as any).part_number}
            </Typography>
          )}
        </Paper>
      )}

      <TextField
        margin="dense"
        label={t('projectItems.quantity')}
        type="number"
        fullWidth
        variant="outlined"
        value={formData.quantity}
        onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
        sx={{ mb: 2 }}
      />

      {/* Sub-Items Quantities (if any) */}
      {selectedMasterItem && masterSubItems.length > 0 && (
        <Box sx={{ mb: 2, p: 2, border: '1px dashed', borderColor: 'divider', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            {t('projectItems.subItemsBreakdown') || 'Sub-Items Breakdown'}
          </Typography>
          {masterSubItems.map((si) => {
            const existing = (formData.sub_items || []).find(s => s.sub_item_id === si.id);
            const qty = existing ? existing.quantity : 0;
            return (
              <Box key={si.id} sx={{ display: 'grid', gridTemplateColumns: '1fr 160px', gap: 1, alignItems: 'center', mb: 1 }}>
                <Box>
                  <Typography variant="body2" fontWeight="medium">{si.name}</Typography>
                  <Typography variant="caption" color="text.secondary">{si.part_number || '-'}</Typography>
                </Box>
                <TextField
                  size="small"
                  type="number"
                  label={t('projectItems.quantity')}
                  value={qty}
                  onChange={(e) => {
                    const newQty = Math.max(0, parseInt(e.target.value || '0'));
                    const list = [...(formData.sub_items || [])];
                    const idx = list.findIndex(x => x.sub_item_id === si.id);
                    if (idx >= 0) {
                      list[idx] = { sub_item_id: si.id, quantity: newQty };
                    } else {
                      list.push({ sub_item_id: si.id, quantity: newQty });
                    }
                    setFormData({ ...formData, sub_items: list });
                  }}
                  inputProps={{ min: 0 }}
                />
              </Box>
            );
          })}
        </Box>
      )}
      
      {/* Delivery Options Manager */}
      <Box sx={{ mb: 2, p: 2, border: '1px solid #ddd', borderRadius: 1 }}>
        <Typography variant="subtitle2" gutterBottom>
          {t('projectItems.deliveryDateOptions')}
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
                secondary={index === 0 ? t('projectItems.primaryOption') : `${t('projectItems.option')} ${index + 1}`}
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  size="small"
                  onClick={() => removeDeliveryDate(dateStr)}
                  disabled={formData.delivery_options.length === 1}
                  title={formData.delivery_options.length === 1 ? t('projectItems.cannotRemoveLastDate') : t('projectItems.removeDate')}
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
              label={t('projectItems.addDeliveryDate')}
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
        label={t('projectItems.projectSpecificDescription')}
        fullWidth
        multiline
        rows={4}
        variant="outlined"
        value={formData.description || ''}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        placeholder={t('projectItems.descriptionPlaceholder')}
        helperText={t('projectItems.descriptionHelperText')}
        sx={{ mb: 2 }}
      />

      <FormControlLabel
        control={
          <Checkbox
            checked={formData.external_purchase}
            onChange={(e) => setFormData({ ...formData, external_purchase: e.target.checked })}
          />
        }
        label={t('projectItems.externalPurchase')}
      />
    </>
  );

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate('/projects')} sx={{ mr: 1 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4">{t('projectItems.projectItems')}</Typography>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="subtitle1" color="text.secondary">
          {t('projectItems.projectId')}: {projectId}
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadTemplate}
            sx={{ mr: 1 }}
          >
            {t('projectItems.downloadTemplate')}
          </Button>
          <Button
            variant="outlined"
            component="label"
            startIcon={<UploadIcon />}
            sx={{ mr: 1 }}
          >
            {t('projectItems.importItems')}
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
            {t('projectItems.exportItems')}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              resetForm();
              setCreateDialogOpen(true);
            }}
          >
            {t('projectItems.addItem')}
          </Button>
          <Button
            variant="contained"
            color="success"
            startIcon={<FinalizeIcon />}
            onClick={handleFinalizeAllItems}
            sx={{ ml: 1 }}
          >
            {t('projectItems.finalizeAllItems')}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Search and Filter Bar */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
          <TextField
            label={t('projectItems.search')}
            placeholder={t('projectItems.searchPlaceholder')}
            value={searchTerm}
            onChange={handleSearchChange}
            size="small"
            sx={{ minWidth: 300, flexGrow: 1 }}
          />
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>{t('projectItems.status')}</InputLabel>
            <Select
              value={statusFilter}
              label={t('projectItems.status')}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="">{t('projectItems.all')}</MenuItem>
              <MenuItem value="PENDING">{t('projectItems.pending')}</MenuItem>
              <MenuItem value="SUGGESTED">{t('projectItems.suggested')}</MenuItem>
              <MenuItem value="DECIDED">{t('projectItems.decided')}</MenuItem>
              <MenuItem value="PROCURED">{t('projectItems.procured')}</MenuItem>
              <MenuItem value="FULFILLED">{t('projectItems.fulfilled')}</MenuItem>
              <MenuItem value="PAID">{t('projectItems.paid')}</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>{t('projectItems.finalized')}</InputLabel>
            <Select
              value={finalizedFilter}
              label={t('projectItems.finalized')}
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
              label={t('projectItems.externalPurchase')}
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
            {t('projectItems.clearFilters')}
          </Button>

          <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
            {t('projectItems.total')}: {totalCount} {totalCount !== 1 ? t('projectItems.items') : t('projectItems.item')}
          </Typography>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('projectItems.itemCode')}</TableCell>
              <TableCell>{t('projectItems.itemName')}</TableCell>
              <TableCell align="right">{t('projectItems.quantity')}</TableCell>
              <TableCell align="center">{t('projectItems.deliveryOptions')}</TableCell>
              <TableCell align="center">{t('projectItems.status')}</TableCell>
              <TableCell align="center">{t('projectItems.externalPurchase')}</TableCell>
              <TableCell align="center">{t('projectItems.actions')}</TableCell>
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
                        label={t('projectItems.finalized')}
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
                    label={item.external_purchase ? t('projectItems.yes') : t('projectItems.no')}
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
                    title={t('projectItems.viewItemDetails')}
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
                        master_item_id: (item as any).master_item_id,
                        item_code: item.item_code,
                        item_name: item.item_name || '',
                        quantity: item.quantity,
                        delivery_options: item.delivery_options || [],
                        external_purchase: item.external_purchase,
                        description: item.description || '',
                        // Prefill existing sub-item quantities if present
                        sub_items: ((item as any).sub_items || []).map((si: any) => ({
                          sub_item_id: si.sub_item_id,
                          quantity: si.quantity ?? 0,
                        })),
                      });
                      
                      // Load the master item for display
                      if ((item as any).master_item_id) {
                        const mid = (item as any).master_item_id as number;
                        itemsMasterAPI.get(mid).then(response => {
                          setSelectedMasterItem(response.data);
                        }).catch(err => console.error('Failed to load master item'));
                        // Also load the sub-items for this master to render the breakdown
                        itemsMasterAPI.listSubItems(mid).then(res => setMasterSubItems(res.data || []))
                          .catch(() => setMasterSubItems([]));
                      }
                      
                      setEditDialogOpen(true);
                    }}
                    title={
                      item.has_finalized_decision
                        ? t('projectItems.cannotEditProcurement')
                        : t('projectItems.editItem')
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
                        ? t('projectItems.cannotDeleteProcurement')
                        : t('projectItems.deleteItem')
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
                          title={t('projectItems.finalizeItem')}
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
                              ? t('projectItems.cannotUnfinalizeProcurement')
                              : t('projectItems.unfinalizeItem')
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
            {t('projectItems.showing')} {items.length === 0 ? 0 : page * rowsPerPage + 1} - {Math.min((page + 1) * rowsPerPage, totalCount)} {t('projectItems.of')} {totalCount}
          </Typography>
          <Box display="flex" gap={1} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>{t('projectItems.perPage')}</InputLabel>
              <Select
                value={rowsPerPage}
                label={t('projectItems.perPage')}
                onChange={(e) => handleChangeRowsPerPage(e as any)}
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
              {t('projectItems.previous')}
            </Button>
            <Typography variant="body2" sx={{ px: 2 }}>
              {t('projectItems.page')} {page + 1} {t('projectItems.of')} {Math.max(1, Math.ceil(totalCount / rowsPerPage))}
            </Typography>
            <Button
              size="small"
              disabled={(page + 1) * rowsPerPage >= totalCount}
              onClick={() => setPage(page + 1)}
            >
              {t('projectItems.next')}
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
        <DialogTitle>{t('projectItems.addNewItem')}</DialogTitle>
        <DialogContent>
          {renderFormFields()}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>{t('projectItems.cancel')}</Button>
          <Button 
            onClick={handleCreateItem} 
            variant="contained"
            disabled={!formData.item_code || !formData.delivery_options || formData.delivery_options.length === 0}
          >
            {t('projectItems.addItem')}
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
        <DialogTitle>{t('projectItems.editItem')}</DialogTitle>
        <DialogContent>
          {renderFormFields()}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setEditDialogOpen(false);
            resetForm();
            setSelectedItem(null);
          }}>{t('projectItems.cancel')}</Button>
          <Button 
            onClick={handleEditItem} 
            variant="contained"
            disabled={!formData.item_code || !formData.delivery_options || formData.delivery_options.length === 0}
          >
            {t('projectItems.updateItem')}
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
          {t('projectItems.deliveryInvoiceConfiguration')}
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
        <DialogTitle>{t('projectItems.itemDetails')}</DialogTitle>
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
                    {t('projectItems.quantity')}
                  </Typography>
                  <Typography variant="h6">{selectedItem.quantity}</Typography>
                </Paper>

                {/* Sub-Items Breakdown (read-only) */}
                <Paper elevation={1} sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    {t('projectItems.subItemsBreakdown')}
                  </Typography>
                  {(selectedItem as any).sub_items && (selectedItem as any).sub_items.length > 0 ? (
                    <Box sx={{ display: 'grid', gap: 1, mt: 1 }}>
                      {(selectedItem as any).sub_items.map((si: any) => (
                        <Paper key={si.sub_item_id} elevation={0} sx={{ p: 1.5, bgcolor: 'grey.50', border: '1px solid', borderColor: 'grey.200' }}>
                          <Typography variant="body2" fontWeight="medium">{si.name || '-'}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {t('projectItems.partNumber')}: {si.part_number || '-'}
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            {t('projectItems.quantity')}: {si.quantity ?? 0}
                          </Typography>
                        </Paper>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      {t('itemsMaster.noSubItems')}
                    </Typography>
                  )}
                </Paper>

                {selectedItem.description && (
                  <Paper elevation={1} sx={{ p: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                      {t('projectItems.description')}
                    </Typography>
                    <Typography variant="body1">{selectedItem.description}</Typography>
                  </Paper>
                )}

                <Paper elevation={1} sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    {t('projectItems.deliveryInvoiceOptions')}
                  </Typography>
                  {viewItemDeliveryOptions && viewItemDeliveryOptions.length > 0 ? (
                    <Box sx={{ mt: 2 }}>
                      {viewItemDeliveryOptions.map((option, index) => (
                        <Paper key={option.id} elevation={2} sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                          <Typography variant="body2" fontWeight="medium" gutterBottom>
                            {t('projectItems.option')} {index + 1} - {t('projectItems.slot')} {option.slot_number}
                          </Typography>
                          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mt: 1 }}>
                            <Box>
                              <Typography variant="caption" color="textSecondary">{t('projectItems.deliveryDate')}:</Typography>
                              <Typography variant="body2">{option.delivery_date}</Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="textSecondary">{t('projectItems.invoiceAmountPerUnit')}:</Typography>
                              <Typography variant="body2">${option.invoice_amount_per_unit}</Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="textSecondary">{t('projectItems.invoiceTiming')}:</Typography>
                              <Typography variant="body2">
                                {option.invoice_timing_type === 'ABSOLUTE' 
                                  ? `${t('projectItems.absolute')}: ${option.invoice_issue_date}`
                                  : `${t('projectItems.relative')}: ${option.invoice_days_after_delivery} ${t('projectItems.daysAfterDelivery')}`
                                }
                              </Typography>
                            </Box>
                            <Box>
                              <Typography variant="caption" color="textSecondary">{t('projectItems.totalInvoice')}:</Typography>
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
                      {t('projectItems.noDeliveryInvoiceOptions')}
                    </Typography>
                  )}
                </Paper>

                <Paper elevation={1} sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    {t('projectItems.externalPurchase')}
                  </Typography>
                  <Chip 
                    label={selectedItem.external_purchase ? t('projectItems.yes') : t('projectItems.no')} 
                    color={selectedItem.external_purchase ? 'warning' : 'default'}
                  />
                </Paper>

                {selectedItem.file_name && (
                  <Paper elevation={1} sx={{ p: 2 }}>
                    <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                      {t('projectItems.attachedFile')}
                    </Typography>
                    <Typography variant="body2">📎 {selectedItem.file_name}</Typography>
                  </Paper>
                )}

                <Paper elevation={1} sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="caption" color="textSecondary">
                    {t('projectItems.created')}: {new Date(selectedItem.created_at).toLocaleString()}
                  </Typography>
                  {selectedItem.updated_at && (
                    <>
                      <br />
                      <Typography variant="caption" color="textSecondary">
                        {t('projectItems.updated')}: {new Date(selectedItem.updated_at).toLocaleString()}
                      </Typography>
                    </>
                  )}
                </Paper>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>{t('projectItems.close')}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
