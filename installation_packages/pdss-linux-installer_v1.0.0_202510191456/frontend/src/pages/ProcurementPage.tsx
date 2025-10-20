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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Checkbox,
  FormControlLabel,
  Pagination,
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  DoneAll as DoneAllIcon,
  RemoveDone as RemoveDoneIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import api, { procurementAPI, excelAPI, deliveryOptionsAPI } from '../services/api.ts';
import { ProcurementOption, ProcurementOptionCreate } from '../types/index.ts';
import { CurrencySelector } from '../components/CurrencySelector.tsx';

interface DeliveryOption {
  id: number;
  delivery_date: string;
  delivery_slot: number | null;
  invoice_amount_per_unit: number;
}

interface ItemWithDetails {
  item_code: string;
  item_name: string;
  description: string;
  project_id: number;
  project_item_id: number;
}

export const ProcurementPage: React.FC = () => {
  const { user } = useAuth();
  const [itemCodes, setItemCodes] = useState<string[]>([]);
  const [itemsWithDetails, setItemsWithDetails] = useState<ItemWithDetails[]>([]);
  const [selectedItemDetails, setSelectedItemDetails] = useState<ItemWithDetails | null>(null);
  const [procurementOptions, setProcurementOptions] = useState<ProcurementOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<ProcurementOption | null>(null);
  const [selectedItemCode, setSelectedItemCode] = useState<string>('');
  const [availableDeliveryOptions, setAvailableDeliveryOptions] = useState<DeliveryOption[]>([]);
  const [selectedDeliveryDate, setSelectedDeliveryDate] = useState<string>('');
  const [formData, setFormData] = useState<any>({
    item_code: '',
    supplier_name: '',
    base_cost: 0,
    currency_id: '',
    shipping_cost: 0,
    lomc_lead_time: 0,
    discount_bundle_threshold: undefined,
    discount_bundle_percent: undefined,
    payment_terms: { type: 'cash', discount_percent: 0 },
    is_finalized: false,
  });
  const [bulkUpdating, setBulkUpdating] = useState<string | null>(null);
  const [loadedItemOptions, setLoadedItemOptions] = useState<Record<string, ProcurementOption[]>>({});
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>(false);
  const [page, setPage] = useState(0);
  const ITEMS_PER_PAGE = 50;
  
  // New state for filters and search
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
  const [selectedSuppliers, setSelectedSuppliers] = useState<string[]>([]);
  const [selectedCurrencies, setSelectedCurrencies] = useState<string[]>([]);
  const [finalizedFilter, setFinalizedFilter] = useState<string>('all'); // 'all', 'finalized', 'not_finalized'
  const [summaryStats, setSummaryStats] = useState<any>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // Only fetch items, not all options (too many options to load at once)
      const itemsResponse = await procurementAPI.getItemsWithDetails();
      
      setItemsWithDetails(itemsResponse.data);
      setItemCodes(itemsResponse.data.map((item: ItemWithDetails) => item.item_code));
      // Don't load all options at once - will fetch per item when needed
      setProcurementOptions([]);
      
      // Calculate summary statistics
      calculateSummaryStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load procurement data');
    } finally {
      setLoading(false);
    }
  };

  const calculateSummaryStats = async () => {
    try {
      // Get all procurement options for summary
      const allOptionsResponse = await procurementAPI.list();
      const allOptions = allOptionsResponse.data;
      
      // Calculate statistics
      const totalItems = itemsWithDetails.length;
      const totalOptions = allOptions.length;
      const finalizedOptions = allOptions.filter((opt: any) => opt.is_finalized).length;
      const notFinalizedOptions = totalOptions - finalizedOptions;
      
      // Get unique suppliers and currencies
      const uniqueSuppliers = [...new Set(allOptions.map((opt: any) => opt.supplier_name))];
      const uniqueCurrencies = [...new Set(allOptions.map((opt: any) => opt.currency_code))];
      
      // Calculate cost statistics
      const totalCost = allOptions.reduce((sum: number, opt: any) => sum + (opt.base_cost || 0), 0);
      const finalizedCost = allOptions
        .filter((opt: any) => opt.is_finalized)
        .reduce((sum: number, opt: any) => sum + (opt.base_cost || 0), 0);
      
      setSummaryStats({
        totalItems,
        totalOptions,
        finalizedOptions,
        notFinalizedOptions,
        uniqueSuppliers: uniqueSuppliers.length,
        uniqueCurrencies: uniqueCurrencies.length,
        totalCost,
        finalizedCost,
        suppliers: uniqueSuppliers,
        currencies: uniqueCurrencies
      });
    } catch (err) {
      console.error('Failed to calculate summary stats:', err);
    }
  };

  const fetchOptionsByItemCode = async (itemCode: string) => {
    try {
      const response = await procurementAPI.listByItemCode(itemCode);
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load options');
      return [];
    }
  };

  const handleAccordionChange = (itemCode: string) => async (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedAccordion(isExpanded ? itemCode : false);
    
    // If expanding and options not loaded yet, fetch them
    if (isExpanded && !loadedItemOptions[itemCode]) {
      try {
        const options = await fetchOptionsByItemCode(itemCode);
        setLoadedItemOptions(prev => ({
          ...prev,
          [itemCode]: options
        }));
      } catch (err) {
        console.error('Failed to load options for', itemCode, err);
      }
    }
  };

  // Filter and search logic
  const getFilteredItems = () => {
    let filtered = itemsWithDetails;

    // Search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(item => 
        item.item_code.toLowerCase().includes(searchLower) ||
        item.item_name?.toLowerCase().includes(searchLower) ||
        item.description?.toLowerCase().includes(searchLower)
      );
    }

    // Project filter
    if (selectedProjects.length > 0) {
      filtered = filtered.filter(item => selectedProjects.includes(item.project_id));
    }

    return filtered;
  };

  const getFilteredOptions = (itemCode: string) => {
    const options = loadedItemOptions[itemCode] || [];
    let filtered = options;

    // Supplier filter
    if (selectedSuppliers.length > 0) {
      filtered = filtered.filter(opt => selectedSuppliers.includes(opt.supplier_name));
    }

    // Currency filter
    if (selectedCurrencies.length > 0) {
      filtered = filtered.filter(opt => selectedCurrencies.includes(opt.currency_code));
    }

    // Finalized filter
    if (finalizedFilter === 'finalized') {
      filtered = filtered.filter(opt => opt.is_finalized);
    } else if (finalizedFilter === 'not_finalized') {
      filtered = filtered.filter(opt => !opt.is_finalized);
    }

    return filtered;
  };

  const fetchDeliveryOptions = async (itemCode: string, projectId?: number) => {
    try {
      // If project_id is available, pass it to get project-specific delivery options
      const url = projectId 
        ? `/delivery-options/by-item-code/${itemCode}?project_id=${projectId}`
        : `/delivery-options/by-item-code/${itemCode}`;
      const response = await api.get(url);
      setAvailableDeliveryOptions(response.data);
      setSelectedDeliveryDate(''); // Reset selection
    } catch (err: any) {
      setAvailableDeliveryOptions([]);
      // Don't show error for missing delivery options, just warn user in UI
    }
  };

  const handleItemCodeChange = async (itemCode: string) => {
    setFormData({ ...formData, item_code: itemCode });
    
    // Find and set item details
    const itemDetails = itemsWithDetails.find(item => item.item_code === itemCode);
    setSelectedItemDetails(itemDetails || null);
    
    if (itemCode && itemDetails) {
      // Pass the project_id to get project-specific delivery options
      await fetchDeliveryOptions(itemCode, itemDetails.project_id);
    } else {
      setAvailableDeliveryOptions([]);
      setSelectedDeliveryDate('');
      setSelectedItemDetails(null);
    }
  };

  const handleCreateOption = async () => {
    // Validate currency_id is selected
    if (!formData.currency_id || formData.currency_id === '' || formData.currency_id === 0) {
      setError('Please select a currency');
      return;
    }
    
    try {
      await procurementAPI.create(formData);
      setCreateDialogOpen(false);
      resetForm();
      fetchData();
    } catch (err: any) {
      // Handle validation errors (422) which return array of error objects
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          const errorMessages = detail.map((e: any) => 
            `${e.loc.join(' -> ')}: ${e.msg}`
          ).join('; ');
          setError(errorMessages);
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError('Failed to create procurement option');
        }
      } else {
        setError('Failed to create procurement option');
      }
    }
  };

  const handleEditOption = async () => {
    if (!selectedOption) return;
    
    try {
      await procurementAPI.update(selectedOption.id, formData);
      setEditDialogOpen(false);
      setSelectedOption(null);
      resetForm();
      fetchData();
    } catch (err: any) {
      // Handle validation errors
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          const errorMessages = detail.map((e: any) => 
            `${e.loc.join(' -> ')}: ${e.msg}`
          ).join('; ');
          setError(errorMessages);
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError('Failed to update procurement option');
        }
      } else {
        setError('Failed to update procurement option');
      }
    }
  };

  const handleDeleteOption = async (optionId: number) => {
    if (!window.confirm('Are you sure you want to delete this procurement option?')) return;
    
    try {
      await procurementAPI.delete(optionId);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete procurement option');
    }
  };

  const handleFinalizeAllItemsOnPage = async () => {
    if (bulkUpdating) {
      return; // Prevent if already updating
    }
    
    const currentPageItems = itemCodes.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE);
    
    if (!window.confirm(`Are you sure you want to finalize ALL options for all ${currentPageItems.length} items on this page?\n\nThis will mark all procurement options as ready for optimization.`)) {
      return;
    }
    
    setBulkUpdating('PAGE_BULK_UPDATE');
    setError('');
    
    let totalSuccess = 0;
    let totalFailed = 0;
    let itemsProcessed = 0;
    
    try {
      for (const itemCode of currentPageItems) {
        itemsProcessed++;
        
        try {
          // Load options if not already loaded
          let itemOptions = loadedItemOptions[itemCode] || [];
          
          if (itemOptions.length === 0) {
            itemOptions = await fetchOptionsByItemCode(itemCode);
          }
          
          // Finalize all options for this item
          for (const option of itemOptions) {
            try {
              await procurementAPI.update(option.id, { is_finalized: true });
              totalSuccess++;
            } catch {
              totalFailed++;
            }
          }
          
          // Reload and cache the updated options
          const updatedOptions = await fetchOptionsByItemCode(itemCode);
          setLoadedItemOptions(prev => ({
            ...prev,
            [itemCode]: updatedOptions
          }));
          
        } catch (err) {
          console.error(`Failed to process item ${itemCode}:`, err);
        }
      }
      
      if (totalFailed > 0) {
        setError(`Processed ${itemsProcessed} items: ${totalSuccess} options finalized, ${totalFailed} failed.`);
      } else {
        setError(''); // Clear any previous errors
        alert(`✅ Success! Finalized ${totalSuccess} options across ${itemsProcessed} items.`);
      }
      
    } catch (err: any) {
      setError('Failed to finalize items on page');
    } finally {
      setBulkUpdating(null);
    }
  };

  const handleBulkFinalizeToggle = async (itemCode: string, shouldFinalize: boolean) => {
    if (bulkUpdating === itemCode) {
      return; // Prevent double-click
    }
    
    setBulkUpdating(itemCode);
    setError('');
    
    try {
      // Auto-load options if not already loaded
      let itemOptions = loadedItemOptions[itemCode] || [];
      
      if (itemOptions.length === 0) {
        // Load options first
        itemOptions = await fetchOptionsByItemCode(itemCode);
        setLoadedItemOptions(prev => ({
          ...prev,
          [itemCode]: itemOptions
        }));
      }
      
      if (itemOptions.length === 0) {
        setError(`No options found for ${itemCode}`);
        setBulkUpdating(null);
        return;
      }
      
      const action = shouldFinalize ? 'finalize' : 'unfinalize';
      if (!window.confirm(`Are you sure you want to ${action} all ${itemOptions.length} options for ${itemCode}?`)) {
        setBulkUpdating(null);
        return;
      }
      
      // Update options one by one to better handle errors
      let successCount = 0;
      let failedCount = 0;
      
      for (const option of itemOptions) {
        try {
          await procurementAPI.update(option.id, { is_finalized: shouldFinalize });
          successCount++;
        } catch (optErr: any) {
          failedCount++;
        }
      }
      
      // Reload options for this specific item
      const updatedOptions = await fetchOptionsByItemCode(itemCode);
      setLoadedItemOptions(prev => ({
        ...prev,
        [itemCode]: updatedOptions
      }));
      
      if (failedCount > 0) {
        setError(`Updated ${successCount} options, but ${failedCount} failed.`);
      }
    } catch (err: any) {
      
      // Handle validation errors
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        const errorMessages = detail.map((error: any) => 
          typeof error === 'string' ? error : `${error.loc?.join('.')}: ${error.msg}`
        ).join('; ');
        setError(errorMessages);
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError(`Failed to ${action} options`);
      }
    } finally {
      setBulkUpdating(null);
    }
  };

  const resetForm = () => {
    setFormData({
      item_code: selectedItemCode,
      supplier_name: '',
      base_cost: 0,
      lomc_lead_time: 0,
      discount_bundle_threshold: undefined,
      discount_bundle_percent: undefined,
      payment_terms: { type: 'cash', discount_percent: 0 },
      is_finalized: false,
    });
    setAvailableDeliveryOptions([]);
    setSelectedDeliveryDate('');
    setSelectedItemDetails(null);
  };

  const handleExportOptions = async () => {
    try {
      const response = await excelAPI.exportProcurement();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'procurement_options.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to export options');
    }
  };

  const handleImportOptions = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await excelAPI.importProcurement(file);
      fetchData();
      alert('Procurement options imported successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import options');
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await excelAPI.downloadProcurementTemplate();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'procurement_options_template.xlsx';
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

  const formatPaymentTerms = (terms: any) => {
    if (terms.type === 'cash') {
      return `Cash${terms.discount_percent ? ` (${terms.discount_percent}% discount)` : ''}`;
    } else {
      const schedule = terms.schedule.map((s: any) => `${s.percent}%`).join(', ');
      return `Installments (${schedule})`;
    }
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
        <Typography variant="h4">Procurement Options</Typography>
        {(user?.role === 'procurement' || user?.role === 'admin') && (
          <Box>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => {
                setLoading(true);
                fetchData();
              }}
              sx={{ mr: 1 }}
              title="Refresh to see items after decisions are reverted"
            >
              Refresh
            </Button>
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
              Import Options
              <input
                type="file"
                hidden
                accept=".xlsx,.xls"
                onChange={handleImportOptions}
              />
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExportOptions}
              sx={{ mr: 1 }}
            >
              Export Options
            </Button>
            <Button
              variant="contained"
              color="success"
              startIcon={<DoneAllIcon />}
              onClick={handleFinalizeAllItemsOnPage}
              disabled={bulkUpdating !== null || itemCodes.length === 0}
              sx={{ mr: 1 }}
            >
              {bulkUpdating === 'PAGE_BULK_UPDATE' ? 'Finalizing...' : 'Finalize All Items on Page'}
            </Button>
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      {summaryStats && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            📊 Procurement Summary
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.totalItems}
                </Typography>
                <Typography variant="body2">Total Items</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.finalizedOptions}
                </Typography>
                <Typography variant="body2">Finalized Options</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.notFinalizedOptions}
                </Typography>
                <Typography variant="body2">Not Finalized</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.uniqueSuppliers}
                </Typography>
                <Typography variant="body2">Suppliers</Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Filters and Search */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🔍 Filters & Search
        </Typography>
        <Grid container spacing={2}>
          {/* Search */}
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Search Items"
              placeholder="Search by item code, name, or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>

          {/* Project Filter */}
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Projects</InputLabel>
              <Select
                multiple
                value={selectedProjects}
                onChange={(e) => setSelectedProjects(e.target.value as number[])}
                renderValue={(selected) => `${selected.length} selected`}
              >
                {itemsWithDetails.map((item) => (
                  <MenuItem key={item.project_id} value={item.project_id}>
                    Project {item.project_id}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Supplier Filter */}
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Suppliers</InputLabel>
              <Select
                multiple
                value={selectedSuppliers}
                onChange={(e) => setSelectedSuppliers(e.target.value as string[])}
                renderValue={(selected) => `${selected.length} selected`}
              >
                {summaryStats?.suppliers.map((supplier: string) => (
                  <MenuItem key={supplier} value={supplier}>
                    {supplier}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Currency Filter */}
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Currencies</InputLabel>
              <Select
                multiple
                value={selectedCurrencies}
                onChange={(e) => setSelectedCurrencies(e.target.value as string[])}
                renderValue={(selected) => `${selected.length} selected`}
              >
                {summaryStats?.currencies.map((currency: string) => (
                  <MenuItem key={currency} value={currency}>
                    {currency}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Finalized Filter */}
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={finalizedFilter}
                onChange={(e) => setFinalizedFilter(e.target.value)}
              >
                <MenuItem value="all">All Options</MenuItem>
                <MenuItem value="finalized">Finalized Only</MenuItem>
                <MenuItem value="not_finalized">Not Finalized</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Clear Filters */}
        <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            size="small"
            onClick={() => {
              setSearchTerm('');
              setSelectedProjects([]);
              setSelectedSuppliers([]);
              setSelectedCurrencies([]);
              setFinalizedFilter('all');
            }}
          >
            Clear All Filters
          </Button>
          {(searchTerm || selectedProjects.length > 0 || selectedSuppliers.length > 0 || selectedCurrencies.length > 0 || finalizedFilter !== 'all') && (
            <Chip
              label={`${getFilteredItems().length} items match filters`}
              color="primary"
              variant="outlined"
            />
          )}
        </Box>
      </Paper>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          ℹ️ <strong>Item Lifecycle:</strong> Items with finalized (LOCKED) decisions are automatically removed from this list. 
          They will reappear if the decision is reverted by Finance team.
        </Typography>
      </Alert>

      {itemCodes.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Items Available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            All items have finalized decisions or no project items exist yet.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Items will appear here when:
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • PM creates new project items
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Finance reverts locked decisions
          </Typography>
        </Paper>
      ) : (
        <>
        {getFilteredItems()
          .slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)
          .map((item) => {
        const itemCode = item.item_code;
        const itemDetails = item;
        const itemOptions = getFilteredOptions(itemCode);
        
        
        return (
          <Accordion 
            key={itemCode} 
            sx={{ mb: 2 }}
            expanded={expandedAccordion === itemCode}
            onChange={handleAccordionChange(itemCode)}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', pr: 2 }}>
                <Box>
                  <Typography variant="h6">
                    {itemCode} {loadedItemOptions[itemCode] ? `(${itemOptions.length} options)` : '(click to load options)'}
                  </Typography>
                  {itemDetails && (itemDetails.item_name || itemDetails.description) && (
                    <Typography variant="caption" color="text.secondary">
                      {itemDetails.item_name}
                      {itemDetails.item_name && itemDetails.description && ' - '}
                      {itemDetails.description && itemDetails.description.substring(0, 80)}
                      {itemDetails.description && itemDetails.description.length > 80 && '...'}
                    </Typography>
                  )}
                </Box>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Supplier</TableCell>
                    <TableCell align="right">Base Cost</TableCell>
                    <TableCell align="center">Lead Time</TableCell>
                    <TableCell align="center">Bundle Discount</TableCell>
                    <TableCell>Payment Terms</TableCell>
                    <TableCell align="center">Status</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {itemOptions.length === 0 && expandedAccordion === itemCode ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        <CircularProgress size={24} /> Loading options...
                      </TableCell>
                    </TableRow>
                  ) : (
                    itemOptions.map((option) => (
                      <TableRow key={option.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {option.supplier_name}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatCurrency(option.base_cost)}
                        </TableCell>
                        <TableCell align="center">
                          <Chip label={`${option.lomc_lead_time} periods`} size="small" />
                        </TableCell>
                        <TableCell align="center">
                          {option.discount_bundle_threshold && option.discount_bundle_percent ? (
                            <Chip 
                              label={`${option.discount_bundle_percent}% @ ${option.discount_bundle_threshold}+`}
                              size="small"
                              color="success"
                            />
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatPaymentTerms(option.payment_terms)}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          {option.is_finalized ? (
                            <Chip 
                              icon={<CheckCircleIcon />}
                              label="Finalized" 
                              color="success" 
                              size="small"
                            />
                          ) : (
                            <Chip 
                              label="Draft" 
                              color="default" 
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </TableCell>
                        <TableCell align="center">
                          {(user?.role === 'procurement' || user?.role === 'admin') && (
                            <>
                              <IconButton
                                size="small"
                                onClick={() => {
                                  setSelectedOption(option);
                                  setFormData({
                                    item_code: option.item_code,
                                    supplier_name: option.supplier_name,
                                    base_cost: option.base_cost,
                                    currency_id: option.currency_id || 0,
                                    shipping_cost: (option as any).shipping_cost || 0,
                                    lomc_lead_time: option.lomc_lead_time,
                                    discount_bundle_threshold: option.discount_bundle_threshold,
                                    discount_bundle_percent: option.discount_bundle_percent,
                                    payment_terms: option.payment_terms,
                                    is_finalized: option.is_finalized || false,
                                  });
                                  // Set item details for display
                                  const itemDetails = itemsWithDetails.find(item => item.item_code === option.item_code);
                                  setSelectedItemDetails(itemDetails || null);
                                  setEditDialogOpen(true);
                                }}
                                title="Edit Option"
                              >
                                <EditIcon />
                              </IconButton>
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteOption(option.id)}
                                title="Delete Option"
                                color="error"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            
            {/* Add Option Button and Bulk Finalize for this item */}
            {(user?.role === 'procurement' || user?.role === 'admin') && (
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => {
                    // Pre-fill item code and fetch details
                    setFormData({
                      item_code: itemCode,
                      supplier_name: '',
                      base_cost: 0,
                      currency_id: '',
                      shipping_cost: 0,
                      lomc_lead_time: 0,
                      discount_bundle_threshold: undefined,
                      discount_bundle_percent: undefined,
                      payment_terms: { type: 'cash', discount_percent: 0 },
                      is_finalized: false,
                    });
                    setSelectedItemDetails(itemDetails || null);
                    // Pass project_id to get project-specific delivery options
                    if (itemDetails) {
                      fetchDeliveryOptions(itemCode, itemDetails.project_id);
                    } else {
                      fetchDeliveryOptions(itemCode);
                    }
                    setCreateDialogOpen(true);
                  }}
                >
                  Add Option for {itemCode}
                </Button>
                
                {/* Bulk Finalize/Unfinalize Button */}
                {itemOptions.length > 0 && (() => {
                  const allFinalized = itemOptions.every((opt) => opt.is_finalized);
                  const isUpdating = bulkUpdating === itemCode;
                  return (
                    <Button
                      variant={allFinalized ? "outlined" : "contained"}
                      color={allFinalized ? "warning" : "success"}
                      startIcon={allFinalized ? <RemoveDoneIcon /> : <DoneAllIcon />}
                      onClick={() => handleBulkFinalizeToggle(itemCode, !allFinalized)}
                      disabled={isUpdating}
                    >
                      {isUpdating ? 'Updating...' : (allFinalized ? 'Unfinalize All' : 'Finalize All')}
                    </Button>
                  );
                })()}
              </Box>
            )}
          </AccordionDetails>
        </Accordion>
        );
      })}
      
      {/* Pagination */}
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Pagination
          count={Math.ceil(getFilteredItems().length / ITEMS_PER_PAGE)}
          page={page + 1}
          onChange={(e, newPage) => setPage(newPage - 1)}
          color="primary"
          size="large"
          showFirstButton
          showLastButton
        />
        <Typography variant="body2" sx={{ ml: 2, alignSelf: 'center', color: 'text.secondary' }}>
          Showing {page * ITEMS_PER_PAGE + 1}-{Math.min((page + 1) * ITEMS_PER_PAGE, getFilteredItems().length)} of {getFilteredItems().length} items
        </Typography>
      </Box>
      </>
      )}

      {/* Create Option Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Procurement Option</DialogTitle>
        <DialogContent>
          {/* Item Information - Pre-filled */}
          <Paper elevation={0} sx={{ p: 2, mb: 2, bgcolor: 'primary.lighter', border: '2px solid', borderColor: 'primary.main' }}>
            <Typography variant="subtitle1" color="primary.dark" gutterBottom sx={{ fontWeight: 'bold' }}>
              📦 {formData.item_code}
            </Typography>
            {selectedItemDetails && selectedItemDetails.item_name && (
              <Typography variant="body2" sx={{ mb: 0.5 }}>
                <strong>Name:</strong> {selectedItemDetails.item_name}
              </Typography>
            )}
            {selectedItemDetails && selectedItemDetails.description && (
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                <strong>Description:</strong> {selectedItemDetails.description}
              </Typography>
            )}
          </Paper>

          <TextField
            margin="dense"
            label="Supplier Name"
            fullWidth
            variant="outlined"
            value={formData.supplier_name}
            onChange={(e) => setFormData({ ...formData, supplier_name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Base Cost"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.base_cost}
            onChange={(e) => setFormData({ ...formData, base_cost: parseFloat(e.target.value) || 0 })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Shipping Cost (Optional)"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.shipping_cost}
            onChange={(e) => setFormData({ ...formData, shipping_cost: parseFloat(e.target.value) || 0 })}
            helperText="Shipping cost in the same currency as base cost"
            sx={{ mb: 2 }}
          />
          <CurrencySelector
            value={formData.currency_id}
            onChange={(currencyId) => setFormData({ ...formData, currency_id: currencyId as number })}
            label="Currency"
            required
            showRate
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Delivery Date (from PM's Project Items)</InputLabel>
            <Select
              value={selectedDeliveryDate}
              onChange={(e) => {
                setSelectedDeliveryDate(e.target.value);
                const selected = availableDeliveryOptions.find(opt => opt.delivery_date === e.target.value);
                setFormData({ 
                  ...formData, 
                  lomc_lead_time: selected?.delivery_slot || 0 
                });
              }}
              disabled={!formData.item_code || availableDeliveryOptions.length === 0}
            >
              {availableDeliveryOptions.length === 0 && formData.item_code ? (
                <MenuItem value="" disabled>
                  No delivery dates set for this item
                </MenuItem>
              ) : (
                availableDeliveryOptions.map((opt) => (
                  <MenuItem key={opt.id} value={opt.delivery_date}>
                    {new Date(opt.delivery_date).toLocaleDateString()} {opt.delivery_slot ? `(Slot ${opt.delivery_slot})` : ''}
                  </MenuItem>
                ))
              )}
            </Select>
            {formData.item_code && availableDeliveryOptions.length === 0 && (
              <Alert severity="warning" sx={{ mt: 1 }}>
                No delivery dates found for this item. Please ask PM to set delivery options first.
              </Alert>
            )}
          </FormControl>
          <TextField
            margin="dense"
            label="Bundle Discount Threshold"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.discount_bundle_threshold || ''}
            onChange={(e) => setFormData({ 
              ...formData, 
              discount_bundle_threshold: e.target.value ? parseInt(e.target.value) : undefined 
            })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Bundle Discount Percentage"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.discount_bundle_percent || ''}
            onChange={(e) => setFormData({ 
              ...formData, 
              discount_bundle_percent: e.target.value ? parseFloat(e.target.value) : undefined 
            })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Payment Type</InputLabel>
            <Select
              value={formData.payment_terms.type}
              onChange={(e) => {
                const type = e.target.value as 'cash' | 'installments';
                setFormData({
                  ...formData,
                  payment_terms: type === 'cash' 
                    ? { type: 'cash', discount_percent: 0 }
                    : { type: 'installments', schedule: [{ due_offset: 0, percent: 100 }] }
                });
              }}
            >
              <MenuItem value="cash">Cash</MenuItem>
              <MenuItem value="installments">Installments</MenuItem>
            </Select>
          </FormControl>
          {formData.payment_terms.type === 'cash' && (
            <TextField
              margin="dense"
              label="Cash Discount Percentage"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.payment_terms.discount_percent || 0}
              onChange={(e) => setFormData({
                ...formData,
                payment_terms: {
                  ...formData.payment_terms,
                  discount_percent: parseFloat(e.target.value) || 0
                }
              })}
              sx={{ mb: 2 }}
            />
          )}
          {formData.payment_terms.type === 'installments' && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Installment Schedule (must total 100%)
              </Typography>
              {formData.payment_terms.schedule.map((installment, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                  <TextField
                    label="Days After Purchase"
                    type="number"
                    size="small"
                    value={installment.due_offset}
                    onChange={(e) => {
                      const newSchedule = [...formData.payment_terms.schedule];
                      newSchedule[index].due_offset = parseInt(e.target.value) || 0;
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule
                        }
                      });
                    }}
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    label="Percentage"
                    type="number"
                    size="small"
                    value={installment.percent}
                    onChange={(e) => {
                      const newSchedule = [...formData.payment_terms.schedule];
                      newSchedule[index].percent = parseFloat(e.target.value) || 0;
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule
                        }
                      });
                    }}
                    sx={{ flex: 1 }}
                    InputProps={{ endAdornment: '%' }}
                  />
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => {
                      const newSchedule = formData.payment_terms.schedule.filter((_, i) => i !== index);
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule.length > 0 ? newSchedule : [{ due_offset: 0, percent: 100 }]
                        }
                      });
                    }}
                    disabled={formData.payment_terms.schedule.length === 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              ))}
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => {
                  const newSchedule = [
                    ...formData.payment_terms.schedule,
                    { due_offset: 30, percent: 0 }
                  ];
                  setFormData({
                    ...formData,
                    payment_terms: {
                      ...formData.payment_terms,
                      schedule: newSchedule
                    }
                  });
                }}
                sx={{ mt: 1 }}
              >
                Add Installment
              </Button>
              <Typography variant="caption" color={
                formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0) === 100 
                  ? 'success.main' 
                  : 'error.main'
              } sx={{ display: 'block', mt: 1 }}>
                Total: {formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0)}%
                {formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0) !== 100 && ' (Must equal 100%)'}
              </Typography>
            </Box>
          )}

          {/* Finalized Checkbox */}
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.is_finalized || false}
                onChange={(e) => setFormData({ ...formData, is_finalized: e.target.checked })}
                color="success"
              />
            }
            label={
              <Box>
                <Typography variant="body2" fontWeight="medium">
                  ✅ Mark as Finalized
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Only finalized options will be used in procurement optimization
                </Typography>
              </Box>
            }
            sx={{ mt: 2, mb: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateOption} variant="contained">
            Add Option
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Option Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Procurement Option</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Item Code</InputLabel>
            <Select
              value={formData.item_code}
              onChange={(e) => {
                const newItemCode = e.target.value;
                setFormData({ ...formData, item_code: newItemCode });
                const itemDetails = itemsWithDetails.find(item => item.item_code === newItemCode);
                setSelectedItemDetails(itemDetails || null);
              }}
            >
              {itemCodes.map((code) => (
                <MenuItem key={code} value={code}>
                  {code}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Item Details Display */}
          {selectedItemDetails && (
            <Paper elevation={0} sx={{ p: 2, mb: 2, bgcolor: 'info.lighter', border: '1px solid', borderColor: 'info.light' }}>
              <Typography variant="subtitle2" color="info.dark" gutterBottom>
                📦 Item Information
              </Typography>
              {selectedItemDetails.item_name && (
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Name:</strong> {selectedItemDetails.item_name}
                </Typography>
              )}
              {selectedItemDetails.description && (
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  <strong>Description:</strong> {selectedItemDetails.description}
                </Typography>
              )}
              {!selectedItemDetails.item_name && !selectedItemDetails.description && (
                <Typography variant="body2" color="text.secondary">
                  No additional details available for this item.
                </Typography>
              )}
            </Paper>
          )}

          <TextField
            margin="dense"
            label="Supplier Name"
            fullWidth
            variant="outlined"
            value={formData.supplier_name}
            onChange={(e) => setFormData({ ...formData, supplier_name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Base Cost"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.base_cost}
            onChange={(e) => setFormData({ ...formData, base_cost: parseFloat(e.target.value) || 0 })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Shipping Cost (Optional)"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.shipping_cost}
            onChange={(e) => setFormData({ ...formData, shipping_cost: parseFloat(e.target.value) || 0 })}
            helperText="Shipping cost in the same currency as base cost"
            sx={{ mb: 2 }}
          />
          <CurrencySelector
            value={formData.currency_id}
            onChange={(currencyId) => setFormData({ ...formData, currency_id: currencyId as number })}
            label="Currency"
            required
            showRate
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Lead Time (periods)"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.lomc_lead_time}
            onChange={(e) => setFormData({ ...formData, lomc_lead_time: parseInt(e.target.value) || 0 })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Bundle Discount Threshold"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.discount_bundle_threshold || ''}
            onChange={(e) => setFormData({ 
              ...formData, 
              discount_bundle_threshold: e.target.value ? parseInt(e.target.value) : undefined 
            })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Bundle Discount Percentage"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.discount_bundle_percent || ''}
            onChange={(e) => setFormData({ 
              ...formData, 
              discount_bundle_percent: e.target.value ? parseFloat(e.target.value) : undefined 
            })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Payment Type</InputLabel>
            <Select
              value={formData.payment_terms.type}
              onChange={(e) => {
                const type = e.target.value as 'cash' | 'installments';
                setFormData({
                  ...formData,
                  payment_terms: type === 'cash' 
                    ? { type: 'cash', discount_percent: 0 }
                    : { type: 'installments', schedule: [{ due_offset: 0, percent: 100 }] }
                });
              }}
            >
              <MenuItem value="cash">Cash</MenuItem>
              <MenuItem value="installments">Installments</MenuItem>
            </Select>
          </FormControl>
          {formData.payment_terms.type === 'cash' && (
            <TextField
              margin="dense"
              label="Cash Discount Percentage"
              type="number"
              fullWidth
              variant="outlined"
              value={formData.payment_terms.discount_percent || 0}
              onChange={(e) => setFormData({
                ...formData,
                payment_terms: {
                  ...formData.payment_terms,
                  discount_percent: parseFloat(e.target.value) || 0
                }
              })}
              sx={{ mb: 2 }}
            />
          )}
          {formData.payment_terms.type === 'installments' && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Installment Schedule (must total 100%)
              </Typography>
              {formData.payment_terms.schedule.map((installment, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                  <TextField
                    label="Days After Purchase"
                    type="number"
                    size="small"
                    value={installment.due_offset}
                    onChange={(e) => {
                      const newSchedule = [...formData.payment_terms.schedule];
                      newSchedule[index].due_offset = parseInt(e.target.value) || 0;
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule
                        }
                      });
                    }}
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    label="Percentage"
                    type="number"
                    size="small"
                    value={installment.percent}
                    onChange={(e) => {
                      const newSchedule = [...formData.payment_terms.schedule];
                      newSchedule[index].percent = parseFloat(e.target.value) || 0;
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule
                        }
                      });
                    }}
                    sx={{ flex: 1 }}
                    InputProps={{ endAdornment: '%' }}
                  />
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => {
                      const newSchedule = formData.payment_terms.schedule.filter((_, i) => i !== index);
                      setFormData({
                        ...formData,
                        payment_terms: {
                          ...formData.payment_terms,
                          schedule: newSchedule.length > 0 ? newSchedule : [{ due_offset: 0, percent: 100 }]
                        }
                      });
                    }}
                    disabled={formData.payment_terms.schedule.length === 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              ))}
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => {
                  const newSchedule = [
                    ...formData.payment_terms.schedule,
                    { due_offset: 30, percent: 0 }
                  ];
                  setFormData({
                    ...formData,
                    payment_terms: {
                      ...formData.payment_terms,
                      schedule: newSchedule
                    }
                  });
                }}
                sx={{ mt: 1 }}
              >
                Add Installment
              </Button>
              <Typography variant="caption" color={
                formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0) === 100 
                  ? 'success.main' 
                  : 'error.main'
              } sx={{ display: 'block', mt: 1 }}>
                Total: {formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0)}%
                {formData.payment_terms.schedule.reduce((sum, inst) => sum + inst.percent, 0) !== 100 && ' (Must equal 100%)'}
              </Typography>
            </Box>
          )}

          {/* Finalized Checkbox */}
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.is_finalized || false}
                onChange={(e) => setFormData({ ...formData, is_finalized: e.target.checked })}
                color="success"
              />
            }
            label={
              <Box>
                <Typography variant="body2" fontWeight="medium">
                  ✅ Mark as Finalized
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Only finalized options will be used in procurement optimization
                </Typography>
              </Box>
            }
            sx={{ mt: 2, mb: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleEditOption} variant="contained">
            Update Option
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
