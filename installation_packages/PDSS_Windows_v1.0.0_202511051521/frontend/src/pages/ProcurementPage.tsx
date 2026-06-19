import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  IconButton,
  Dialog,
  DialogContent,
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
  Pagination,
  Grid,
} from '@mui/material';
import { formatApiError } from '../utils/errorUtils.ts';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Visibility as VisibilityIcon,
  Analytics as AnalyticsIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { useFeatureFlags } from '../hooks/useFeatureFlags.tsx';
import { deliveryOptionsAPI, itemsAPI, projectsAPI, packagesAPI } from '../services/api.ts';
import { PackageWizard } from '../components/PackageWizard/PackageWizard.tsx';
import { PackageList } from '../components/packages/PackageList.tsx';
import { CoverageSummaryModal } from '../components/packages/CoverageSummaryModal.tsx';
import { SubItemRequirement } from '../utils/coverageCalculator.ts';
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';

interface DeliveryOption {
  id: number;
  delivery_date: string;
  delivery_slot: number | null;
  invoice_amount_per_unit: number;
  notes?: string | null; // Optional notes field
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
  const { t, i18n } = useTranslation();
  
  // Locale-aware date formatter
  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDate = useMemo(() => (dateString: string | null) => {
    if (!dateString) return '-';
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd') : gregorianFormat(d, 'yyyy-MM-dd');
    } catch {
      return new Date(dateString).toLocaleDateString();
    }
  }, [isFa]);
  
  const [projectsMap, setProjectsMap] = useState<Record<number, string>>({});
  const [itemsWithDetails, setItemsWithDetails] = useState<ItemWithDetails[]>([]);
  const [selectedItemDetails, setSelectedItemDetails] = useState<ItemWithDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewItemDialogOpen, setViewItemDialogOpen] = useState(false);
  const [itemSubItems, setItemSubItems] = useState<Array<{ sub_item_id: number; name?: string; part_number?: string; quantity: number }>>([]);
  const [projectInfo, setProjectInfo] = useState<any>(null);
  const [itemDeliveryOptions, setItemDeliveryOptions] = useState<DeliveryOption[]>([]);
  const { flags, isPackageMode, hasOverrides } = useFeatureFlags();
  
  // Package Wizard state
  const [packageWizardOpen, setPackageWizardOpen] = useState(false);
  const [wizardProjectItemId, setWizardProjectItemId] = useState<number | null>(null);
  const [wizardItemCode, setWizardItemCode] = useState<string>('');
  const [wizardItemName, setWizardItemName] = useState<string>('');
  const [wizardMainItemQuantity, setWizardMainItemQuantity] = useState<number>(0);
  const [wizardSubItemRequirements, setWizardSubItemRequirements] = useState<SubItemRequirement[]>([]);
  const [wizardExistingPackages, setWizardExistingPackages] = useState<any[]>([]);
  const [packageRefreshTrigger, setPackageRefreshTrigger] = useState(0);
  
  // Coverage Summary Modal state
  const [coverageModalOpen, setCoverageModalOpen] = useState(false);
  const [selectedProjectIdForCoverage, setSelectedProjectIdForCoverage] = useState<number | null>(null);
  // Load all active projects to map id -> name for headers
  useEffect(() => {
    (async () => {
      try {
        const res = await projectsAPI.list();
        const map: Record<number, string> = {};
        (res.data || []).forEach((p: any) => { map[p.id] = p.name || p.project_code; });
        setProjectsMap(map);
      } catch (e) {
        // ignore
      }
    })();
  }, []);

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
      
      // Calculate summary statistics based on packages
      calculateSummaryStats(itemsWithDetails);
    } catch (err: any) {
      console.error('Error loading finalized items:', err);
      setError(formatApiError(err, 'Failed to load procurement data'));
    } finally {
      setLoading(false);
    }
  };

  // Calculate summary statistics based on packages
  const calculateSummaryStats = async (items?: ItemWithDetails[]) => {
    try {
      const itemsToProcess = items || itemsWithDetails;
      const totalItems = itemsToProcess.length;
      
      let totalPackages = 0;
      let activePackages = 0;
      let uniqueSuppliers: Set<string> = new Set();
      let itemsWithPackages = 0;
      
      // Fetch packages for each item (lazy-loaded, batch processing)
      for (const item of itemsToProcess) {
        try {
          const packagesResponse = await packagesAPI.listByProjectItem(item.project_item_id, true);
          const packages = Array.isArray(packagesResponse.data) ? packagesResponse.data : [];
          
          totalPackages += packages.length;
          activePackages += packages.filter((pkg: any) => pkg.is_active).length;
          
          // Collect unique suppliers from packages
          packages.forEach((pkg: any) => {
            if (pkg.supplier?.company_name) {
              uniqueSuppliers.add(pkg.supplier.company_name);
            }
          });
          
          if (packages.length > 0) {
            itemsWithPackages++;
          }
        } catch (err) {
          // Silently skip items without packages
          console.debug(`No packages for item ${item.item_code}`);
        }
      }
      
      setSummaryStats({
        totalItems,
        totalPackages,
        activePackages,
        itemsWithPackages,
        uniqueSuppliers: uniqueSuppliers.size,
        suppliers: Array.from(uniqueSuppliers),
      });
    } catch (err) {
      console.error('Failed to calculate summary stats:', err);
    }
  };

  const handleAccordionChange = (itemKey: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedAccordion(isExpanded ? itemKey : false);
  };

  // Filter and search logic (memoized for performance)
  const getFilteredItems = useMemo(() => {
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
  }, [itemsWithDetails, searchTerm, selectedProjects]);

  // Calculate summary stats (trigger when items change)
  useEffect(() => {
    if (itemsWithDetails.length > 0) {
      calculateSummaryStats(itemsWithDetails);
    }
  }, [itemsWithDetails]);


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
              startIcon={<AnalyticsIcon />}
              onClick={() => {
                // Open overall project coverage summary
                if (selectedProjects.length === 1) {
                  setSelectedProjectIdForCoverage(selectedProjects[0]);
                  setCoverageModalOpen(true);
                } else if (itemsWithDetails.length > 0) {
                  // If no project selected, show for the first item as a fallback
                  setSelectedProjectIdForCoverage(itemsWithDetails[0].project_id);
                  setCoverageModalOpen(true);
                } else {
                  setError(t('procurement.selectProjectForAnalysis') || 'Please select a project or ensure items are available for coverage analysis.');
                }
              }}
              sx={{ mr: 1 }}
            >
              {t('procurement.analyzeCoverage') || 'Analyze Coverage'}
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
                  {summaryStats.totalPackages || 0}
                </Typography>
                <Typography variant="body2">{t('procurement.totalPackages') || 'Total Packages'}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.activePackages || 0}
                </Typography>
                <Typography variant="body2">{t('procurement.activePackages') || 'Active Packages'}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.itemsWithPackages || 0}
                </Typography>
                <Typography variant="body2">{t('procurement.itemsWithPackages') || 'Items with Packages'}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'white' }}>
                <Typography variant="h4" fontWeight="bold">
                  {summaryStats.uniqueSuppliers || 0}
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

        </Grid>

        {/* Clear Filters */}
        <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            size="small"
            onClick={() => {
              setSearchTerm('');
              setSelectedProjects([]);
            }}
          >
            Clear All Filters
          </Button>
          {(searchTerm || selectedProjects.length > 0) && (
            <Chip
              label={`${getFilteredItems.length} ${t('procurement.itemsMatchFilters')}`}
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

      {itemsWithDetails.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('procurement.noItemsAvailable') || 'No Project Items Available'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2, mb: 3 }}>
            {t('procurement.noItemsMessage') || 'There are no finalized project items available for procurement. Items will appear here once they are finalized by the Project Management Office.'}
          </Typography>
        </Paper>
      ) : (
        <>
        {getFilteredItems
          .slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)
          .map((item) => {
        const itemCode = item.item_code;
        const itemDetails = item;
        
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
                    {itemCode}
                  </Typography>
                  {itemDetails && (itemDetails.item_name || itemDetails.description) && (
                    <Typography variant="caption" color="text.secondary">
                      {itemDetails.item_name}
                      {projectsMap[itemDetails.project_id] && ` — ${projectsMap[itemDetails.project_id]}`}
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

                      // Fetch sub-items breakdown for this project item
                      try {
                        const itemResponse = await itemsAPI.get(itemDetails.project_item_id);
                        setItemSubItems(itemResponse.data?.sub_items || []);
                      } catch (err) {
                        console.error('Failed to fetch sub-items:', err);
                        setItemSubItems([]);
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
              {/* Package List */}
              <PackageList
                projectItemId={itemDetails.project_item_id}
                itemCode={itemCode}
                itemName={itemDetails.item_name}
                onEdit={(packageId) => {
                  // TODO: Open package wizard in edit mode
                  console.log('Edit package:', packageId);
                }}
                onDelete={async (packageId) => {
                  if (window.confirm(t('procurement.confirmDeletePackage') || 'Are you sure you want to delete this package?')) {
                    try {
                      await packagesAPI.delete(packageId);
                      setPackageRefreshTrigger(prev => prev + 1);
                      fetchData();
                    } catch (err: any) {
                      setError(formatApiError(err, t('procurement.failedToDeletePackage') || 'Failed to delete package'));
                    }
                  }
                }}
                onAnalyze={(packageId) => {
                  setSelectedProjectIdForCoverage(itemDetails.project_id);
                  setCoverageModalOpen(true);
                }}
                onSendToOptimizer={async (packageId) => {
                  try {
                    // TODO: Implement optimizer preview with package
                    console.log('Send package to optimizer:', packageId);
                    // const response = await financeAPI.previewOptimization(itemDetails.project_id, [packageId]);
                  } catch (err: any) {
                    setError(formatApiError(err, t('procurement.failedToPreviewOptimization') || 'Failed to preview optimization'));
                  }
                }}
                refreshTrigger={packageRefreshTrigger}
              />
              
              {/* Create Package Button */}
              {(user?.role === 'procurement' || user?.role === 'admin') && (
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={async () => {
                      // Open package wizard
                      try {
                        const itemResponse = await itemsAPI.get(itemDetails.project_item_id);
                        const subItems = itemResponse.data?.sub_items || [];
                        const subItemRequirements: SubItemRequirement[] = subItems.map((si: any) => ({
                          sub_item_id: si.id,
                          name: si.name,
                          part_number: si.part_number,
                          required_quantity: si.quantity || 0,
                        }));

                        // Load existing packages
                        const packagesResponse = await packagesAPI.listByProjectItem(itemDetails.project_item_id, true);
                        const existingPackages = packagesResponse.data || [];

                        setWizardProjectItemId(itemDetails.project_item_id);
                        setWizardItemCode(itemCode);
                        setWizardItemName(itemDetails.item_name);
                        setWizardMainItemQuantity(itemDetails.quantity || 0);
                        setWizardSubItemRequirements(subItemRequirements);
                        setWizardExistingPackages(existingPackages);
                        setPackageWizardOpen(true);
                      } catch (err: any) {
                        console.error('Failed to open package wizard:', err);
                        setError(formatApiError(err, t('procurement.failedToOpenWizard') || 'Failed to open package wizard'));
                      }
                    }}
                  >
                    {t('procurement.createPackage') || 'Create Package'}
                  </Button>
                </Box>
              )}
            </AccordionDetails>
          </Accordion>
        );
      })}
      
      {/* Coverage Summary Modal */}
      {coverageModalOpen && selectedProjectIdForCoverage && (
        <CoverageSummaryModal
          open={coverageModalOpen}
          onClose={() => {
            setCoverageModalOpen(false);
            setSelectedProjectIdForCoverage(null);
          }}
          projectId={selectedProjectIdForCoverage}
          onCreateForRemaining={(remainingDemand) => {
            // Find the item and open wizard with remaining demand pre-filled
            const itemDetails = itemsWithDetails.find(
              item => item.project_item_id === remainingDemand.project_item_id
            );
            if (itemDetails) {
              // TODO: Pre-fill wizard with remaining demand quantities
              setWizardProjectItemId(itemDetails.project_item_id);
              setWizardItemCode(itemDetails.item_code);
              setWizardItemName(itemDetails.item_name);
              setWizardMainItemQuantity(remainingDemand.main_item_remaining);
              setWizardSubItemRequirements(
                remainingDemand.subitem_remaining.map((si) => ({
                  sub_item_id: si.sub_item_id,
                  required_quantity: si.remaining_quantity,
                }))
              );
              setWizardExistingPackages([]);
              setPackageWizardOpen(true);
              setCoverageModalOpen(false);
            }
          }}
        />
      )}
      
      {/* Pagination */}
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Pagination
          count={Math.ceil(getFilteredItems.length / ITEMS_PER_PAGE)}
          page={page + 1}
          onChange={(e, newPage) => setPage(newPage - 1)}
          color="primary"
          size="large"
          showFirstButton
          showLastButton
        />
        <Typography variant="body2" sx={{ ml: 2, alignSelf: 'center', color: 'text.secondary' }}>
          {t('procurement.showing')} {page * ITEMS_PER_PAGE + 1}-{Math.min((page + 1) * ITEMS_PER_PAGE, getFilteredItems.length)} {t('procurement.of')} {getFilteredItems.length} {t('procurement.items')}
        </Typography>
      </Box>
      </>
      )}

      {/* Package Wizard */}
      {packageWizardOpen && wizardProjectItemId && (
        <PackageWizard
          open={packageWizardOpen}
          onClose={() => {
            setPackageWizardOpen(false);
            setWizardProjectItemId(null);
            setWizardItemCode('');
            setWizardItemName('');
            setWizardMainItemQuantity(0);
            setWizardSubItemRequirements([]);
            setWizardExistingPackages([]);
          }}
          projectItemId={wizardProjectItemId}
          itemCode={wizardItemCode}
          itemName={wizardItemName}
          mainItemRequiredQuantity={wizardMainItemQuantity}
          subItemRequirements={wizardSubItemRequirements}
          existingPackages={wizardExistingPackages}
          onPackageCreated={async (packageId) => {
            // Refresh data after package creation
            setPackageRefreshTrigger(prev => prev + 1);
            fetchData();
          }}
        />
      )}

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

              {/* Sub-Items Breakdown */}
              {itemSubItems && itemSubItems.length > 0 && (
                <Box sx={{ mt: 2, mb: 3 }}>
                  <Typography variant="h5" sx={{ mb: 1, fontWeight: 600, color: '#333' }}>
                    {t('procurement.subItems') || 'Sub-Items'}
                  </Typography>
                  {itemSubItems.map(si => (
                    <Paper key={si.sub_item_id} sx={{ p: 1.5, mb: 1 }}>
                      <Typography variant="body2" fontWeight="medium">{si.name || '-'}</Typography>
                      <Typography variant="caption" color="text.secondary">{si.part_number || '-'}</Typography>
                      <Typography variant="body2">{t('procurement.quantity')}: {si.quantity}</Typography>
                    </Paper>
                  ))}
                </Box>
              )}

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
                              {option.delivery_date ? formatDisplayDate(option.delivery_date) : t('procurement.notSpecified')}
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
