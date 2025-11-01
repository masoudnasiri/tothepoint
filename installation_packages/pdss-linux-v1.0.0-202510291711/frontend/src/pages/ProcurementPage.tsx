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
  Autocomplete,
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
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import api, { procurementAPI, excelAPI, deliveryOptionsAPI, itemsAPI, suppliersAPI, projectsAPI } from '../services/api.ts';
import { ProcurementOption, ProcurementOptionCreate } from '../types/index.ts';
import { CurrencySelector } from '../components/CurrencySelector.tsx';
import { useTranslation } from 'react-i18next';

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
  quantity?: number;
  status?: string;
  external_purchase?: boolean;
  file_path?: string;
  file_name?: string;
  decision_date?: string;
  procurement_date?: string;
  payment_date?: string;
  invoice_submission_date?: string;
  expected_cash_in_date?: string;
  actual_cash_in_date?: string;
  is_finalized?: boolean;
  finalized_by?: number;
  finalized_at?: string;
  created_at?: string;
  updated_at?: string;
}

interface Supplier {
  id: number;
  supplier_id: string;
  company_name: string;
}

export const ProcurementPage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [itemCodes, setItemCodes] = useState<string[]>([]);
  const [itemsWithDetails, setItemsWithDetails] = useState<ItemWithDetails[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedItemDetails, setSelectedItemDetails] = useState<ItemWithDetails | null>(null);
  const [procurementOptions, setProcurementOptions] = useState<ProcurementOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [viewItemDialogOpen, setViewItemDialogOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<ProcurementOption | null>(null);
  const [projectInfo, setProjectInfo] = useState<any>(null);
  const [itemDeliveryOptions, setItemDeliveryOptions] = useState<DeliveryOption[]>([]);
  const [selectedItemCode, setSelectedItemCode] = useState<string>('');
  const [availableDeliveryOptions, setAvailableDeliveryOptions] = useState<DeliveryOption[]>([]);
  const [selectedDeliveryDate, setSelectedDeliveryDate] = useState<string>('');
  const [selectedDeliveryOptionId, setSelectedDeliveryOptionId] = useState<number | null>(null);
  const [formData, setFormData] = useState<any>({
    item_code: '',
    supplier_name: '',
    supplier_id: null,
    base_cost: 0,
    currency_id: '',
    shipping_cost: 0,
    delivery_option_id: null,
    lomc_lead_time: 0,
    purchase_date: '',
    expected_delivery_date: '',
    project_item_id: null, // Add project_item_id field
    discount_bundle_threshold: undefined,
    discount_bundle_percent: undefined,
    payment_terms: { type: 'cash', discount_percent: 0 },
    is_finalized: false,
  });
  const [bulkUpdating, setBulkUpdating] = useState<string | null>(null);
  const [loadedItemOptions, setLoadedItemOptions] = useState<Record<string, ProcurementOption[]>>({});
  const [loadingItemOptions, setLoadingItemOptions] = useState<Record<string, boolean>>({});

  // Helper function to format number with thousand separators
  const formatNumberWithCommas = (value: string | number): string => {
    if (!value) return '';
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(numValue)) return '';
    return numValue.toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });
  };

  // Helper function to parse formatted number back to raw value
  const parseFormattedNumber = (formattedValue: string): string => {
    return formattedValue.replace(/,/g, '');
  };

  // Helper function to add commas while typing
  const addCommasWhileTyping = (value: string): string => {
    // Remove all non-digit characters except decimal point
    const cleanValue = value.replace(/[^\d.]/g, '');
    
    // Split by decimal point
    const parts = cleanValue.split('.');
    const integerPart = parts[0];
    const decimalPart = parts[1];
    
    // Add commas to integer part
    const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    
    // Combine with decimal part if exists
    return decimalPart ? `${formattedInteger}.${decimalPart}` : formattedInteger;
  };
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
      // Fetch only finalized items (PMO finalized items) - request all items
      const itemsResponse = await itemsAPI.listFinalized({ skip: 0, limit: 10000 });
      
      // Convert finalized items to the format expected by the procurement page
      const itemsWithDetails = itemsResponse.data.map((item: any) => ({
        item_code: item.item_code,
        item_name: item.item_name,
        description: item.description || '',
        project_id: item.project_id,
        project_item_id: item.id,
        quantity: item.quantity,
        status: item.status,
        external_purchase: item.external_purchase,
        file_path: item.file_path,
        file_name: item.file_name,
        decision_date: item.decision_date,
        procurement_date: item.procurement_date,
        payment_date: item.payment_date,
        invoice_submission_date: item.invoice_submission_date,
        expected_cash_in_date: item.expected_cash_in_date,
        actual_cash_in_date: item.actual_cash_in_date,
        is_finalized: item.is_finalized,
        finalized_by: item.finalized_by,
        finalized_at: item.finalized_at,
        created_at: item.created_at,
        updated_at: item.updated_at,
      }));
      
      setItemsWithDetails(itemsWithDetails);
      setItemCodes(itemsWithDetails.map((item: ItemWithDetails) => item.item_code));
      // Don't load all options at once - will fetch per item when needed
      setProcurementOptions([]);
      
      // Load suppliers for dropdown
      const suppliersResponse = await procurementAPI.getSuppliers();
      setSuppliers(suppliersResponse.data);
      
      // Calculate summary statistics with the newly loaded items
      calculateSummaryStats(itemsWithDetails);
    } catch (err: any) {
      console.error('Error loading finalized items:', err);
      // Handle validation errors
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Pydantic validation errors
          const errorMessages = err.response.data.detail.map((e: any) => e.msg).join(', ');
          setError(`Validation error: ${errorMessages}`);
        } else if (typeof err.response.data.detail === 'string') {
          setError(err.response.data.detail);
        } else {
          setError('Failed to load finalized items');
        }
      } else {
        setError('Failed to load procurement data');
      }
    } finally {
      setLoading(false);
    }
  };

  const calculateSummaryStats = async (items?: ItemWithDetails[]) => {
    try {
      // Use provided items or fall back to state
      const itemsToProcess = items || itemsWithDetails;
      
      // Since we're only showing finalized items, calculate stats based on those items
      const totalItems = itemsToProcess.length;
      
      // Get procurement options for the finalized items only
      let totalOptions = 0;
      let finalizedOptions = 0;
      let uniqueSuppliers: string[] = [];
      let uniqueCurrencies: string[] = [];
      let totalCost = 0;
      
      // For each finalized item, get its procurement options
      for (const item of itemsToProcess) {
        try {
          const optionsResponse = await procurementAPI.listByProjectItem(item.project_item_id);
          const options = optionsResponse.data;
          
          totalOptions += options.length;
          finalizedOptions += options.filter((opt: any) => opt.is_finalized).length;
          
          // Collect suppliers and currencies
          options.forEach((opt: any) => {
            if (opt.supplier_name) uniqueSuppliers.push(opt.supplier_name);
            if (opt.currency_code) uniqueCurrencies.push(opt.currency_code);
            if (opt.base_cost) totalCost += opt.base_cost;
          });
        } catch (err) {
          console.warn(`Failed to load options for item ${item.item_code}:`, err);
        }
      }
      
      // Remove duplicates
      uniqueSuppliers = [...new Set(uniqueSuppliers)];
      uniqueCurrencies = [...new Set(uniqueCurrencies)];
      
      setSummaryStats({
        totalItems,
        totalOptions,
        finalizedOptions,
        notFinalizedOptions: totalOptions - finalizedOptions,
        uniqueSuppliers: uniqueSuppliers.length,
        uniqueCurrencies: uniqueCurrencies.length,
        totalCost,
        finalizedCost: totalCost, // All options are for finalized items
        suppliers: uniqueSuppliers,
        currencies: uniqueCurrencies
      });
    } catch (err) {
      console.error('Failed to calculate summary stats:', err);
    }
  };

  const fetchOptionsByProjectItem = async (projectItemId: number) => {
    try {
      const response = await procurementAPI.listByProjectItem(projectItemId);
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load options');
      return [];
    }
  };

  const handleAccordionChange = (itemKey: string) => async (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedAccordion(isExpanded ? itemKey : false);
    
    // Extract itemCode and projectItemId from the key (format: "itemCode-projectItemId")
    // Split by last dash to get itemCode (itemCode may contain dashes like DELL-LAT1)
    const lastDashIndex = itemKey.lastIndexOf('-');
    const itemCode = lastDashIndex !== -1 ? itemKey.substring(0, lastDashIndex) : itemKey;
    const projectItemId = lastDashIndex !== -1 ? parseInt(itemKey.substring(lastDashIndex + 1)) : null;
    
    // If expanding and options not loaded yet, fetch them
    if (isExpanded && projectItemId && !loadedItemOptions[itemKey]) {
      try {
        // Set loading state
        setLoadingItemOptions(prev => ({ ...prev, [itemKey]: true }));
        
        const options = await fetchOptionsByProjectItem(projectItemId);
        setLoadedItemOptions(prev => ({
          ...prev,
          [itemKey]: options
        }));
        
        // Clear loading state
        setLoadingItemOptions(prev => ({ ...prev, [itemKey]: false }));
      } catch (err) {
        console.error('Failed to load options for', itemCode, err);
        // Clear loading state on error
        setLoadingItemOptions(prev => ({ ...prev, [itemKey]: false }));
        // Set empty array to prevent repeated loading attempts
        setLoadedItemOptions(prev => ({
          ...prev,
          [itemKey]: []
        }));
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

  const getFilteredOptions = (itemCode: string, projectItemId: number) => {
    const itemKey = `${itemCode}-${projectItemId}`;
    const options = loadedItemOptions[itemKey] || [];
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

  const fetchDeliveryOptions = async (projectItemId: number) => {
    try {
      const response = await deliveryOptionsAPI.listByItem(projectItemId);
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
      // Pass the project_item_id to get project-item-specific delivery options
      await fetchDeliveryOptions(itemDetails.project_item_id);
    } else {
      setAvailableDeliveryOptions([]);
      setSelectedDeliveryDate('');
      setSelectedItemDetails(null);
    }
  };

  // Calculate lead time from delivery date
  const calculateLeadTime = (deliveryDate: string): number => {
    if (!deliveryDate) return 0;
    const today = new Date();
    const delivery = new Date(deliveryDate);
    const diffTime = delivery.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(0, diffDays); // Return 0 if delivery date is in the past
  };

  const handleCreateOption = async () => {
    // Validate currency_id is selected
    if (!formData.currency_id || formData.currency_id === '' || formData.currency_id === 0) {
      setError('Please select a currency');
      return;
    }
    
    try {
      const createdOption = await procurementAPI.create(formData);
      const itemCode = formData.item_code;
      
      setCreateDialogOpen(false);
      resetForm();
      
      // Refresh the options for this specific item
      if (selectedItemDetails) {
        const updatedOptionsResponse = await procurementAPI.listByProjectItem(selectedItemDetails.project_item_id);
        if (updatedOptionsResponse.data) {
          const key = `${itemCode}-${selectedItemDetails.project_item_id}`;
          setLoadedItemOptions(prevOptions => ({
            ...prevOptions,
            [key]: updatedOptionsResponse.data,
          }));
        }
      }
      
      // Also refresh the items list
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
      const itemCode = formData.item_code;
      
      setEditDialogOpen(false);
      setSelectedOption(null);
      resetForm();
      
      // Refresh the options for this specific item
      if (selectedItemDetails) {
        const updatedOptionsResponse = await procurementAPI.listByProjectItem(selectedItemDetails.project_item_id);
        if (updatedOptionsResponse.data) {
          const key = `${itemCode}-${selectedItemDetails.project_item_id}`;
          setLoadedItemOptions(prevOptions => ({
            ...prevOptions,
            [key]: updatedOptionsResponse.data,
          }));
        }
      }
      
      // Also refresh the items list
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

  const handleDeleteOption = async (optionId: number, itemCode: string, projectItemId: number) => {
    if (!window.confirm('Are you sure you want to delete this procurement option?')) return;
    
    try {
      await procurementAPI.delete(optionId);
      
      // Refresh the options for this specific item
      const updatedOptionsResponse = await procurementAPI.listByProjectItem(projectItemId);
      if (updatedOptionsResponse.data) {
        const key = `${itemCode}-${projectItemId}`;
        setLoadedItemOptions(prevOptions => ({
          ...prevOptions,
          [key]: updatedOptionsResponse.data,
        }));
      }
      
      // Also refresh the items list
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete procurement option');
    }
  };

  const handleFinalizeAllItemsOnPage = async () => {
    if (bulkUpdating) {
      return; // Prevent if already updating
    }
    
    const currentPageItems = itemsWithDetails.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE);
    
    if (!window.confirm(`Are you sure you want to finalize ALL options for all ${currentPageItems.length} items on this page?\n\nThis will mark all procurement options as ready for optimization.`)) {
      return;
    }
    
    setBulkUpdating('PAGE_BULK_UPDATE');
    setError('');
    
    let totalSuccess = 0;
    let totalFailed = 0;
    let itemsProcessed = 0;
    
    try {
      for (const item of currentPageItems) {
        itemsProcessed++;
        
        try {
          // Load options if not already loaded
          const itemKey = `${item.item_code}-${item.project_item_id}`;
          let itemOptions = loadedItemOptions[itemKey] || [];
          
          if (itemOptions.length === 0) {
            itemOptions = await fetchOptionsByProjectItem(item.project_item_id);
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
          const updatedOptions = await fetchOptionsByProjectItem(item.project_item_id);
          setLoadedItemOptions(prev => ({
            ...prev,
            [itemKey]: updatedOptions
          }));
          
        } catch (err) {
          console.error(`Failed to process item ${item.item_code}:`, err);
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

  const handleBulkFinalizeToggle = async (itemCode: string, shouldFinalize: boolean, projectItemId: number) => {
    const itemKey = `${itemCode}-${projectItemId}`;
    if (bulkUpdating === itemKey) {
      return; // Prevent double-click
    }
    
    setBulkUpdating(itemKey);
    setError('');
    
    try {
      // Auto-load options if not already loaded
      let itemOptions = loadedItemOptions[itemKey] || [];
      
      if (itemOptions.length === 0) {
        // Load options first
        itemOptions = await fetchOptionsByProjectItem(projectItemId);
        setLoadedItemOptions(prev => ({
          ...prev,
          [itemKey]: itemOptions
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
      const updatedOptions = await fetchOptionsByProjectItem(projectItemId);
      setLoadedItemOptions(prev => ({
        ...prev,
        [itemKey]: updatedOptions
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
      supplier_id: null,
      base_cost: 0,
      currency_id: '',
      shipping_cost: 0,
      delivery_option_id: null,
      lomc_lead_time: 0,
      purchase_date: '',
      expected_delivery_date: '',
      project_item_id: null, // Add project_item_id field
      discount_bundle_threshold: undefined,
      discount_bundle_percent: undefined,
      payment_terms: { type: 'cash', discount_percent: 0 },
      is_finalized: false,
    });
    setAvailableDeliveryOptions([]);
    setSelectedDeliveryDate('');
    setSelectedDeliveryOptionId(null);
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
    if (!terms) return 'N/A';
    
    if (terms.type === 'cash') {
      return `Cash${terms.discount_percent ? ` (${terms.discount_percent}% discount)` : ''}`;
    } else if (terms.type === 'installments') {
      if (terms.schedule && Array.isArray(terms.schedule)) {
        const schedule = terms.schedule.map((s: any) => `${s.percent}%`).join(', ');
        return `Installments (${schedule})`;
      }
      return 'Installments';
    }
    
    return 'Unknown';
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
        <Typography variant="h4">{t('procurement.title')}</Typography>
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
              title={t('procurement.refreshToSeeItems')}
            >
              {t('procurement.refresh')}
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadTemplate}
              sx={{ mr: 1 }}
            >
              {t('procurement.downloadTemplate')}
            </Button>
            <Button
              variant="outlined"
              component="label"
              startIcon={<UploadIcon />}
              sx={{ mr: 1 }}
            >
              {t('procurement.importOptions')}
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
              {t('procurement.exportOptions')}
            </Button>
            <Button
              variant="contained"
              color="success"
              startIcon={<DoneAllIcon />}
              onClick={handleFinalizeAllItemsOnPage}
              disabled={bulkUpdating !== null || itemCodes.length === 0}
              sx={{ mr: 1 }}
            >
              {bulkUpdating === 'PAGE_BULK_UPDATE' ? t('procurement.finalizing') : t('procurement.finalizeAllItemsOnPage')}
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
            📊 {t('procurement.procurementSummary')}
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.totalItems}
                </Typography>
                <Typography variant="body2">{t('procurement.totalItems')}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.finalizedOptions}
                </Typography>
                <Typography variant="body2">{t('procurement.finalizedOptions')}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.notFinalizedOptions}
                </Typography>
                <Typography variant="body2">{t('procurement.notFinalized')}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.uniqueSuppliers}
                </Typography>
                <Typography variant="body2">{t('procurement.suppliers')}</Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Filters and Search */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🔍 {t('procurement.filtersAndSearch')}
        </Typography>
        <Grid container spacing={2}>
          {/* Search */}
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label={t('procurement.searchItems')}
              placeholder={t('procurement.searchPlaceholder')}
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
              <InputLabel>{t('procurement.projects')}</InputLabel>
              <Select
                multiple
                value={selectedProjects}
                onChange={(e) => setSelectedProjects(e.target.value as number[])}
                renderValue={(selected) => `${selected.length} ${t('procurement.selected')}`}
              >
                {itemsWithDetails.map((item) => (
                  <MenuItem key={item.project_id} value={item.project_id}>
                    {t('procurement.project')} {item.project_id}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Supplier Filter */}
          <Grid item xs={12} md={2}>
            <FormControl fullWidth>
              <InputLabel>{t('procurement.suppliers')}</InputLabel>
              <Select
                multiple
                value={selectedSuppliers}
                onChange={(e) => setSelectedSuppliers(e.target.value as string[])}
                renderValue={(selected) => `${selected.length} ${t('procurement.selected')}`}
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
              <InputLabel>{t('procurement.currencies')}</InputLabel>
              <Select
                multiple
                value={selectedCurrencies}
                onChange={(e) => setSelectedCurrencies(e.target.value as string[])}
                renderValue={(selected) => `${selected.length} ${t('procurement.selected')}`}
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
              <InputLabel>{t('procurement.status')}</InputLabel>
              <Select
                value={finalizedFilter}
                onChange={(e) => setFinalizedFilter(e.target.value)}
              >
                <MenuItem value="all">{t('procurement.allOptions')}</MenuItem>
                <MenuItem value="finalized">{t('procurement.finalizedOnly')}</MenuItem>
                <MenuItem value="not_finalized">{t('procurement.notFinalized')}</MenuItem>
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
              label={`${getFilteredItems().length} ${t('procurement.itemsMatchFilters')}`}
              color="primary"
              variant="outlined"
            />
          )}
        </Box>
      </Paper>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          ℹ️ <strong>{t('procurement.itemLifecycle')}</strong>
        </Typography>
      </Alert>

      {itemCodes.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('procurement.noItemsAvailable')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('procurement.allItemsFinalized')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t('procurement.itemsWillAppearWhen')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('procurement.pmCreatesNewItems')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('procurement.financeRevertsDecisions')}
          </Typography>
        </Paper>
      ) : (
        <>
        {getFilteredItems()
          .slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)
          .map((item) => {
        const itemCode = item.item_code;
        const itemDetails = item;
        const itemOptions = getFilteredOptions(itemCode, itemDetails.project_item_id);
        
        
        return (
          <Accordion 
            key={`${itemCode}-${itemDetails.project_item_id}`} 
            sx={{ mb: 2 }}
            expanded={expandedAccordion === `${itemCode}-${itemDetails.project_item_id}`}
            onChange={handleAccordionChange(`${itemCode}-${itemDetails.project_item_id}`)}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', pr: 2 }}>
                <Box>
                  <Typography variant="h6">
                    {itemCode} {loadedItemOptions[`${itemCode}-${itemDetails.project_item_id}`] ? `(${itemOptions.length} options)` : '(click to load options)'}
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
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <IconButton
                    size="small"
                    onClick={async (e) => {
                      e.stopPropagation();
                      setSelectedItemDetails(itemDetails);
                      
                      // Fetch project information
                      try {
                        const projectResponse = await projectsAPI.get(itemDetails.project_id);
                        setProjectInfo(projectResponse.data);
                      } catch (err) {
                        console.error('Failed to fetch project info:', err);
                      }
                      
                      // Fetch delivery options for this specific project item
                      try {
                        const deliveryResponse = await deliveryOptionsAPI.listByItem(itemDetails.project_item_id);
                        setItemDeliveryOptions(deliveryResponse.data);
                      } catch (err) {
                        console.error('Failed to fetch delivery options:', err);
                        setItemDeliveryOptions([]);
                      }
                      
                      setViewItemDialogOpen(true);
                    }}
                    title={t('procurement.viewItemDetails')}
                    color="primary"
                  >
                    <VisibilityIcon />
                  </IconButton>
                </Box>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('procurement.supplier')}</TableCell>
                    <TableCell align="right">{t('procurement.baseCost')}</TableCell>
                    <TableCell align="center">{t('procurement.purchaseDate')}</TableCell>
                    <TableCell align="center">{t('procurement.deliveryDate')}</TableCell>
                    <TableCell align="center">{t('procurement.bundleDiscount')}</TableCell>
                    <TableCell>{t('procurement.paymentTerms')}</TableCell>
                    <TableCell align="center">{t('procurement.status')}</TableCell>
                    <TableCell align="center">{t('procurement.actions')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loadingItemOptions[`${itemCode}-${itemDetails.project_item_id}`] ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        <CircularProgress size={24} /> {t('procurement.loadingOptions')}
                      </TableCell>
                    </TableRow>
                  ) : itemOptions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} align="center">
                        <Typography variant="body2" color="text.secondary">
                          {t('procurement.noProcurementOptionsYet')}
                        </Typography>
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
                          {option.purchase_date ? (
                            <Chip 
                              label={new Date(option.purchase_date).toLocaleDateString()} 
                              size="small" 
                              color="secondary"
                            />
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell align="center">
                          {option.expected_delivery_date ? (
                            <Chip 
                              label={new Date(option.expected_delivery_date).toLocaleDateString()} 
                              size="small" 
                              color="primary"
                            />
                          ) : (
                            <Chip label={`${option.lomc_lead_time} ${t('procurement.periods')}`} size="small" />
                          )}
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
                              label={t('procurement.finalized')} 
                              color="success" 
                              size="small"
                            />
                          ) : (
                            <Chip 
                              label={t('procurement.draft')} 
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
                                onClick={async () => {
                                  setSelectedOption(option);
                                  setFormData({
                                    item_code: option.item_code,
                                    supplier_name: option.supplier_name,
                                    supplier_id: (option as any).supplier_id || null,
                                    base_cost: option.base_cost,
                                    currency_id: option.currency_id || 0,
                                    shipping_cost: (option as any).shipping_cost || 0,
                                    delivery_option_id: (option as any).delivery_option_id || null,
                                    lomc_lead_time: option.lomc_lead_time,
                                    purchase_date: (option as any).purchase_date || '',
                                    expected_delivery_date: (option as any).expected_delivery_date || '',
                                    project_item_id: (option as any).project_item_id || null, // Add project_item_id
                                    discount_bundle_threshold: option.discount_bundle_threshold,
                                    discount_bundle_percent: option.discount_bundle_percent,
                                    payment_terms: option.payment_terms,
                                    is_finalized: option.is_finalized || false,
                                  });
                                  // Set item details for display
                                  const itemDetails = itemsWithDetails.find(item => item.item_code === option.item_code);
                                  setSelectedItemDetails(itemDetails || null);
                                  // Fetch delivery options for this specific project item
                                  if (option.item_code && itemDetails) {
                                    try {
                                      const deliveryResponse = await deliveryOptionsAPI.listByItem(itemDetails.project_item_id);
                                      const deliveryOptions = deliveryResponse.data;
                                      setAvailableDeliveryOptions(deliveryOptions);
                                      
                                      // Check if the current delivery_option_id is valid in the new options
                                      const currentDeliveryOptionId = option.delivery_option_id;
                                      const isValidDeliveryOption = deliveryOptions.some(opt => opt.id === currentDeliveryOptionId);
                                      if (!isValidDeliveryOption && deliveryOptions.length > 0) {
                                        // Reset to the first available option if current one is not valid
                                        setFormData(prev => ({
                                          ...prev,
                                          delivery_option_id: deliveryOptions[0].id,
                                          expected_delivery_date: deliveryOptions[0].delivery_date
                                        }));
                                      }
                                    } catch (err) {
                                      setAvailableDeliveryOptions([]);
                                    }
                                  }
                                  setEditDialogOpen(true);
                                }}
                                title={t('procurement.editOption')}
                              >
                                <EditIcon />
                              </IconButton>
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteOption(option.id, itemCode, itemDetails.project_item_id)}
                                title={t('procurement.deleteOption')}
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
                      supplier_id: null,
                      base_cost: 0,
                      currency_id: '',
                      shipping_cost: 0,
                      lomc_lead_time: 0,
                      project_item_id: itemDetails.project_item_id, // Set project_item_id
                      discount_bundle_threshold: undefined,
                      discount_bundle_percent: undefined,
                      payment_terms: { type: 'cash', discount_percent: 0 },
                      is_finalized: false,
                    });
                    setSelectedItemDetails(itemDetails || null);
                    // Pass project_item_id to get project-item-specific delivery options
                    if (itemDetails) {
                      fetchDeliveryOptions(itemDetails.project_item_id);
                    } else {
                      setAvailableDeliveryOptions([]);
                    }
                    setCreateDialogOpen(true);
                  }}
                >
                  {t('procurement.addOptionFor')} {itemCode}
                </Button>
                
                {/* Bulk Finalize/Unfinalize Button */}
                {itemOptions.length > 0 && (() => {
                  const allFinalized = itemOptions.every((opt) => opt.is_finalized);
                  const isUpdating = bulkUpdating === `${itemCode}-${itemDetails.project_item_id}`;
                  return (
                    <Button
                      variant={allFinalized ? "outlined" : "contained"}
                      color={allFinalized ? "warning" : "success"}
                      startIcon={allFinalized ? <RemoveDoneIcon /> : <DoneAllIcon />}
                      onClick={() => handleBulkFinalizeToggle(itemCode, !allFinalized, itemDetails.project_item_id)}
                      disabled={isUpdating}
                    >
                      {isUpdating ? t('procurement.updating') : (allFinalized ? t('procurement.unfinalizeAll') : t('procurement.finalizeAll'))}
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
          {t('procurement.showing')} {page * ITEMS_PER_PAGE + 1}-{Math.min((page + 1) * ITEMS_PER_PAGE, getFilteredItems().length)} {t('procurement.of')} {getFilteredItems().length} {t('procurement.items')}
        </Typography>
      </Box>
      </>
      )}

      {/* Create Option Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('procurement.addNewProcurementOption')}</DialogTitle>
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

          <Autocomplete
            fullWidth
            options={suppliers}
            getOptionLabel={(option) => `${option.company_name} (${option.supplier_id})`}
            value={suppliers.find(s => s.id === formData.supplier_id) || null}
            onChange={(event, newValue) => {
              setFormData({ 
                ...formData, 
                supplier_id: newValue ? newValue.id : null,
                supplier_name: newValue ? newValue.company_name : ''
              });
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label={t('procurement.supplierName')}
                placeholder={t('procurement.selectSupplier')}
                margin="dense"
                sx={{ mb: 2 }}
              />
            )}
            renderOption={(props, option) => (
              <li {...props}>
                {option.company_name} ({option.supplier_id})
              </li>
            )}
            isOptionEqualToValue={(option, value) => option.id === value?.id}
            noOptionsText={t('procurement.noSuppliersFound')}
          />
          <TextField
            margin="dense"
            label={t('procurement.baseCost')}
            type="text"
            fullWidth
            variant="outlined"
            value={formData.base_cost ? addCommasWhileTyping(formData.base_cost.toString()) : ''}
            onChange={(e) => {
              const rawValue = parseFormattedNumber(e.target.value);
              const numericValue = parseFloat(rawValue) || 0;
              setFormData({ ...formData, base_cost: numericValue });
            }}
            inputProps={{ 
              step: 0.01, 
              min: 0,
              placeholder: '0.00'
            }}
            helperText={t('procurement.baseCostHelper')}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('procurement.shippingCost')}
            type="text"
            fullWidth
            variant="outlined"
            value={formData.shipping_cost ? addCommasWhileTyping(formData.shipping_cost.toString()) : ''}
            onChange={(e) => {
              const rawValue = parseFormattedNumber(e.target.value);
              const numericValue = parseFloat(rawValue) || 0;
              setFormData({ ...formData, shipping_cost: numericValue });
            }}
            inputProps={{ 
              step: 0.01, 
              min: 0,
              placeholder: '0.00'
            }}
            helperText={t('procurement.shippingCostHelper')}
            sx={{ mb: 2 }}
          />
          <CurrencySelector
            value={formData.currency_id}
            onChange={(currencyId) => setFormData({ ...formData, currency_id: currencyId as number })}
            label={t('procurement.currency')}
            required
            showRate
            sx={{ mb: 2 }}
          />
          {/* Delivery Option Selection */}
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>{t('procurement.deliveryOption')}</InputLabel>
            <Select
              value={formData.delivery_option_id || ''}
              onChange={(e) => {
                const deliveryOptionId = e.target.value;
                const selectedOption = availableDeliveryOptions.find(opt => opt.id === deliveryOptionId);
                const leadTime = selectedOption ? calculateLeadTime(selectedOption.delivery_date) : 0;
                setFormData({ 
                  ...formData, 
                  delivery_option_id: deliveryOptionId,
                  expected_delivery_date: selectedOption?.delivery_date || '',
                  lomc_lead_time: leadTime // Calculate actual lead time from delivery date
                });
                setSelectedDeliveryOptionId(deliveryOptionId);
              }}
              disabled={availableDeliveryOptions.length === 0}
            >
              {availableDeliveryOptions.length === 0 ? (
                <MenuItem disabled>{t('procurement.noDeliveryOptionsAvailable')}</MenuItem>
              ) : (
                availableDeliveryOptions.map((option) => (
                  <MenuItem key={option.id} value={option.id}>
                    {option.delivery_date} - Slot {option.delivery_slot}
                  </MenuItem>
                ))
              )}
            </Select>
            {availableDeliveryOptions.length === 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                No delivery options found for this item. Please add delivery options in the project first.
              </Typography>
            )}
          </FormControl>

          {/* Purchase Date */}
          <TextField
            margin="dense"
            label={t('procurement.purchaseDate')}
            type="date"
            fullWidth
            variant="outlined"
            value={formData.purchase_date}
            onChange={(e) => setFormData({ 
              ...formData, 
              purchase_date: e.target.value 
            })}
            helperText={t('procurement.purchaseDateHelper')}
            sx={{ mb: 2 }}
          />

          {/* Expected Delivery Date (auto-filled) */}
          <TextField
            margin="dense"
            label={t('procurement.expectedDeliveryDate')}
            type="date"
            fullWidth
            variant="outlined"
            value={formData.expected_delivery_date}
            disabled
            helperText="Auto-filled from selected delivery option"
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('procurement.bundleDiscountThreshold')}
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
            label={t('procurement.bundleDiscountPercentage')}
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
            <InputLabel>{t('procurement.paymentType')}</InputLabel>
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
              <MenuItem value="cash">{t('procurement.cash')}</MenuItem>
              <MenuItem value="installments">{t('procurement.installments')}</MenuItem>
            </Select>
          </FormControl>
          {formData.payment_terms.type === 'cash' && (
            <TextField
              margin="dense"
              label={t('procurement.cashDiscountPercentage')}
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
                {t('procurement.installmentSchedule')}
              </Typography>
              {formData.payment_terms.schedule.map((installment, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                  <TextField
                    label={t('procurement.daysAfterPurchase')}
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
                    label={t('procurement.percentage')}
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
                  ✅ {t('procurement.markAsFinalized')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('procurement.onlyFinalizedOptions')}
                </Typography>
              </Box>
            }
            sx={{ mt: 2, mb: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>{t('procurement.cancel')}</Button>
          <Button onClick={handleCreateOption} variant="contained">
            {t('procurement.addOption')}
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
                // Fetch delivery options for the selected project item
                if (newItemCode && itemDetails) {
                  fetchDeliveryOptions(itemDetails.project_item_id);
                } else {
                  setAvailableDeliveryOptions([]);
                }
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

          <Autocomplete
            fullWidth
            options={suppliers}
            getOptionLabel={(option) => `${option.company_name} (${option.supplier_id})`}
            value={suppliers.find(s => s.id === formData.supplier_id) || null}
            onChange={(event, newValue) => {
              setFormData({ 
                ...formData, 
                supplier_id: newValue ? newValue.id : null,
                supplier_name: newValue ? newValue.company_name : ''
              });
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label={t('procurement.supplierName')}
                placeholder={t('procurement.selectSupplier')}
                margin="dense"
                sx={{ mb: 2 }}
              />
            )}
            renderOption={(props, option) => (
              <li {...props}>
                {option.company_name} ({option.supplier_id})
              </li>
            )}
            isOptionEqualToValue={(option, value) => option.id === value?.id}
            noOptionsText={t('procurement.noSuppliersFound')}
          />
          <TextField
            margin="dense"
            label={t('procurement.baseCost')}
            type="text"
            fullWidth
            variant="outlined"
            value={formData.base_cost ? addCommasWhileTyping(formData.base_cost.toString()) : ''}
            onChange={(e) => {
              const rawValue = parseFormattedNumber(e.target.value);
              const numericValue = parseFloat(rawValue) || 0;
              setFormData({ ...formData, base_cost: numericValue });
            }}
            inputProps={{ 
              step: 0.01, 
              min: 0,
              placeholder: '0.00'
            }}
            helperText={t('procurement.baseCostHelper')}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('procurement.shippingCost')}
            type="text"
            fullWidth
            variant="outlined"
            value={formData.shipping_cost ? addCommasWhileTyping(formData.shipping_cost.toString()) : ''}
            onChange={(e) => {
              const rawValue = parseFormattedNumber(e.target.value);
              const numericValue = parseFloat(rawValue) || 0;
              setFormData({ ...formData, shipping_cost: numericValue });
            }}
            inputProps={{ 
              step: 0.01, 
              min: 0,
              placeholder: '0.00'
            }}
            helperText={t('procurement.shippingCostHelper')}
            sx={{ mb: 2 }}
          />
          <CurrencySelector
            value={formData.currency_id}
            onChange={(currencyId) => setFormData({ ...formData, currency_id: currencyId as number })}
            label={t('procurement.currency')}
            required
            showRate
            sx={{ mb: 2 }}
          />
          {/* Delivery Option Selection */}
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>{t('procurement.deliveryOption')}</InputLabel>
            <Select
              value={formData.delivery_option_id || ''}
              onChange={(e) => {
                const deliveryOptionId = e.target.value;
                const selectedOption = availableDeliveryOptions.find(opt => opt.id === deliveryOptionId);
                const leadTime = selectedOption ? calculateLeadTime(selectedOption.delivery_date) : 0;
                setFormData({ 
                  ...formData, 
                  delivery_option_id: deliveryOptionId,
                  expected_delivery_date: selectedOption?.delivery_date || '',
                  lomc_lead_time: leadTime // Calculate actual lead time from delivery date
                });
                setSelectedDeliveryOptionId(deliveryOptionId);
              }}
              disabled={availableDeliveryOptions.length === 0}
            >
              {availableDeliveryOptions.length === 0 ? (
                <MenuItem disabled>{t('procurement.noDeliveryOptionsAvailable')}</MenuItem>
              ) : (
                availableDeliveryOptions.map((option) => (
                  <MenuItem key={option.id} value={option.id}>
                    {option.delivery_date} - Slot {option.delivery_slot}
                  </MenuItem>
                ))
              )}
            </Select>
            {availableDeliveryOptions.length === 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                No delivery options found for this item. Please add delivery options in the project first.
              </Typography>
            )}
          </FormControl>

          {/* Purchase Date */}
          <TextField
            margin="dense"
            label={t('procurement.purchaseDate')}
            type="date"
            fullWidth
            variant="outlined"
            value={formData.purchase_date}
            onChange={(e) => setFormData({ 
              ...formData, 
              purchase_date: e.target.value 
            })}
            helperText={t('procurement.purchaseDateHelper')}
            sx={{ mb: 2 }}
          />

          {/* Expected Delivery Date (auto-filled) */}
          <TextField
            margin="dense"
            label={t('procurement.expectedDeliveryDate')}
            type="date"
            fullWidth
            variant="outlined"
            value={formData.expected_delivery_date}
            disabled
            helperText="Auto-filled from selected delivery option"
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label={t('procurement.bundleDiscountThreshold')}
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
            label={t('procurement.bundleDiscountPercentage')}
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
            <InputLabel>{t('procurement.paymentType')}</InputLabel>
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
              <MenuItem value="cash">{t('procurement.cash')}</MenuItem>
              <MenuItem value="installments">{t('procurement.installments')}</MenuItem>
            </Select>
          </FormControl>
          {formData.payment_terms.type === 'cash' && (
            <TextField
              margin="dense"
              label={t('procurement.cashDiscountPercentage')}
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
                {t('procurement.installmentSchedule')}
              </Typography>
              {formData.payment_terms.schedule.map((installment, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                  <TextField
                    label={t('procurement.daysAfterPurchase')}
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
                    label={t('procurement.percentage')}
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
                  ✅ {t('procurement.markAsFinalized')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('procurement.onlyFinalizedOptions')}
                </Typography>
              </Box>
            }
            sx={{ mt: 2, mb: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>{t('procurement.cancel')}</Button>
          <Button onClick={handleEditOption} variant="contained">
            {t('procurement.updateOption')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Item Detail Dialog */}
      <Dialog open={viewItemDialogOpen} onClose={() => setViewItemDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogContent sx={{ p: 0 }}>
          {selectedItemDetails && (
            <Box sx={{ p: 3 }}>
              {/* Item Details Section */}
              <Box sx={{ mb: 4 }}>
                <Typography variant="h4" sx={{ mb: 2, fontWeight: 600, color: '#333' }}>
                  {t('procurement.itemDetails')}
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Box sx={{ 
                    width: 40, 
                    height: 40, 
                    backgroundColor: '#8B4513', 
                    borderRadius: 1, 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    mr: 2
                  }}>
                    <Typography sx={{ color: 'white', fontSize: '20px' }}>📦</Typography>
                  </Box>
                  <Box>
                    <Typography variant="h5" sx={{ color: '#1976d2', fontWeight: 600 }}>
                      {selectedItemDetails.item_code}
                    </Typography>
                    <Typography variant="body1" sx={{ color: '#666' }}>
                      {selectedItemDetails.item_name || t('procurement.notSpecified')}
                    </Typography>
                  </Box>
                </Box>

                {/* Quantity Card */}
                <Paper sx={{ p: 2, backgroundColor: '#f5f5f5', borderRadius: 2 }}>
                  <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                    {t('procurement.quantity')}
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#333' }}>
                    {selectedItemDetails.quantity || 0}
                  </Typography>
                </Paper>

                {/* Project Information */}
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                    {t('procurement.projectName')}
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500, color: '#333' }}>
                    {projectInfo?.name || t('procurement.loading')}
                  </Typography>
                </Box>

                {/* Description */}
                {selectedItemDetails.description && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                      {t('procurement.description')}
                    </Typography>
                    <Typography variant="body1" sx={{ color: '#333' }}>
                      {selectedItemDetails.description}
                    </Typography>
                  </Box>
                )}
              </Box>

              {/* Delivery & Invoice Options Section */}
              <Box>
                <Typography variant="h4" sx={{ mb: 2, fontWeight: 600, color: '#333' }}>
                  {t('procurement.deliveryInvoiceOptions')}
                </Typography>
                
                {itemDeliveryOptions.length > 0 ? (
                  itemDeliveryOptions.map((option, index) => (
                    <Paper key={option.id} sx={{ p: 2, backgroundColor: '#f5f5f5', borderRadius: 2, mb: 2 }}>
                      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: '#333' }}>
                        {t('procurement.option')} {index + 1} - {t('procurement.slot')} {option.delivery_slot || 'N/A'}
                      </Typography>
                      
                      <Grid container spacing={3}>
                        <Grid item xs={6}>
                          <Box>
                            <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                              {t('procurement.deliveryDate')}:
                            </Typography>
                            <Typography variant="body1" sx={{ fontWeight: 500, color: '#333' }}>
                              {option.delivery_date ? new Date(option.delivery_date).toLocaleDateString() : t('procurement.notSpecified')}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box>
                            <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                              {t('procurement.item')}:
                            </Typography>
                            <Typography variant="body1" sx={{ fontWeight: 500, color: '#333' }}>
                              {selectedItemDetails.item_name || t('procurement.notSpecified')}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12}>
                          <Box>
                            <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                              {t('procurement.description')}:
                            </Typography>
                            <Typography variant="body1" sx={{ color: '#333' }}>
                              {selectedItemDetails.description || t('procurement.notSpecified')}
                            </Typography>
                          </Box>
                        </Grid>
                        {option.notes && (
                          <Grid item xs={12}>
                            <Box>
                              <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                                {t('procurement.optionalNotes')}:
                              </Typography>
                              <Typography variant="body1" sx={{ color: '#333' }}>
                                {option.notes}
                              </Typography>
                            </Box>
                          </Grid>
                        )}
                      </Grid>
                    </Paper>
                  ))
                ) : (
                  <Paper sx={{ p: 3, backgroundColor: '#f5f5f5', borderRadius: 2, textAlign: 'center' }}>
                    <Typography variant="body1" sx={{ color: '#666' }}>
                      {t('procurement.noDeliveryOptions')}
                    </Typography>
                  </Paper>
                )}
              </Box>

              {/* Close Button */}
              <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
                <Button 
                  onClick={() => setViewItemDialogOpen(false)} 
                  variant="contained"
                  sx={{ 
                    backgroundColor: '#1976d2',
                    '&:hover': { backgroundColor: '#1565c0' }
                  }}
                >
                  {t('procurement.close')}
                </Button>
              </Box>
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};
