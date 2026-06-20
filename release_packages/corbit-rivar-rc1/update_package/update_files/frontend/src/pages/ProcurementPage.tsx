import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
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
  Pagination,
  Grid,
  InputAdornment,
} from '@mui/material';
import { formatApiError } from '../utils/errorUtils.ts';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Visibility as VisibilityIcon,
  Analytics as AnalyticsIcon,
  ExpandMore as ExpandMoreIcon,
  Inventory as InventoryIcon,
  ShoppingCart as ShoppingCartIcon,
  LocalShipping as LocalShippingIcon,
  Business as BusinessIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext.tsx';
import { useFeatureFlags } from '../hooks/useFeatureFlags.tsx';
import { deliveryOptionsAPI, itemsAPI, projectsAPI, packagesAPI, procurementAPI } from '../services/api.ts';
import { PackageWizard } from '../components/PackageWizard/PackageWizard.tsx';
import { PackageList } from '../components/packages/PackageList.tsx';
import { CoverageSummaryModal } from '../components/packages/CoverageSummaryModal.tsx';
import { SubItemRequirement } from '../utils/coverageCalculator.ts';
import { useTranslation } from 'react-i18next';
import { useMemo } from 'react';
import { format as jalaliFormat, parseISO as jalaliParseISO } from 'date-fns-jalali';
import { format as gregorianFormat, parseISO as gregorianParseISO } from 'date-fns';
import { RivarPageHeader } from '../components/ui/RivarPageHeader.tsx';
import { RivarMetricCard } from '../components/ui/RivarMetricCard.tsx';
import { RivarPanel } from '../components/ui/RivarPanel.tsx';
import { RivarToolbar } from '../components/ui/RivarToolbar.tsx';
import { RivarEmptyState } from '../components/ui/RivarEmptyState.tsx';
import { RivarStatusPill } from '../components/ui/RivarStatusPill.tsx';
import { rivarTokens } from '../theme/rivarTheme.ts';

interface DeliveryOption {
  id: number;
  delivery_date: string;
  delivery_slot: number | null;
  invoice_amount_per_unit: number;
  notes?: string | null;
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

  const isFa = i18n.language?.startsWith('fa');
  const formatDisplayDate = useMemo(() => (dateString: string | null) => {
    if (!dateString) return '-';
    try {
      const d = isFa ? jalaliParseISO(dateString) : gregorianParseISO(dateString);
      return isFa ? jalaliFormat(d, 'yyyy/MM/dd') : gregorianFormat(d, 'yyyy-MM-dd');
    } catch { return new Date(dateString).toLocaleDateString(); }
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
  const { flags, isPackageMode } = useFeatureFlags();

  const [packageWizardOpen, setPackageWizardOpen] = useState(false);
  const [wizardProjectItemId, setWizardProjectItemId] = useState<number | null>(null);
  const [wizardItemCode, setWizardItemCode] = useState<string>('');
  const [wizardItemName, setWizardItemName] = useState<string>('');
  const [wizardMainItemQuantity, setWizardMainItemQuantity] = useState<number>(0);
  const [wizardSubItemRequirements, setWizardSubItemRequirements] = useState<SubItemRequirement[]>([]);
  const [wizardExistingPackages, setWizardExistingPackages] = useState<any[]>([]);
  const [packageRefreshTrigger, setPackageRefreshTrigger] = useState(0);
  const [editingPackageId, setEditingPackageId] = useState<number | null>(null);
  const [wizardInitialData, setWizardInitialData] = useState<any>(null);

  const [coverageModalOpen, setCoverageModalOpen] = useState(false);
  const [selectedProjectIdForCoverage, setSelectedProjectIdForCoverage] = useState<number | null>(null);
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>(false);
  const [page, setPage] = useState(0);
  const ITEMS_PER_PAGE = 50;
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
  const [summaryStats, setSummaryStats] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await projectsAPI.list();
        const map: Record<number, string> = {};
        (res.data || []).forEach((p: any) => { map[p.id] = p.name || p.project_code; });
        setProjectsMap(map);
      } catch { /* ignore */ }
    })();
  }, []);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const itemsResponse = await itemsAPI.listFinalized({ skip: 0, limit: 10000 });
      const mapped = itemsResponse.data.map((item: any) => ({
        item_code: item.item_code, item_name: item.item_name, description: item.description || '',
        project_id: item.project_id, project_item_id: item.id, quantity: item.quantity,
        status: item.status, external_purchase: item.external_purchase, file_path: item.file_path,
        file_name: item.file_name, decision_date: item.decision_date, procurement_date: item.procurement_date,
        payment_date: item.payment_date, invoice_submission_date: item.invoice_submission_date,
        expected_cash_in_date: item.expected_cash_in_date, actual_cash_in_date: item.actual_cash_in_date,
        is_finalized: item.is_finalized, finalized_by: item.finalized_by, finalized_at: item.finalized_at,
        created_at: item.created_at, updated_at: item.updated_at,
      }));
      setItemsWithDetails(mapped);
      calculateSummaryStats(mapped);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to load procurement data'));
    } finally {
      setLoading(false);
    }
  };

  const calculateSummaryStats = async (items?: ItemWithDetails[]) => {
    try {
      const toProcess = items || itemsWithDetails;
      let totalPackages = 0, activePackages = 0, itemsWithPackages = 0;
      const uniqueSuppliers = new Set<string>();
      for (const item of toProcess) {
        try {
          const r = await packagesAPI.listByProjectItem(item.project_item_id, true);
          const pkgs = Array.isArray(r.data) ? r.data : [];
          totalPackages += pkgs.length;
          activePackages += pkgs.filter((p: any) => p.is_active).length;
          pkgs.forEach((p: any) => { if (p.supplier?.company_name) uniqueSuppliers.add(p.supplier.company_name); });
          if (pkgs.length > 0) itemsWithPackages++;
        } catch { /* skip */ }
      }
      setSummaryStats({ totalItems: toProcess.length, totalPackages, activePackages, itemsWithPackages, uniqueSuppliers: uniqueSuppliers.size, suppliers: Array.from(uniqueSuppliers) });
    } catch { /* skip */ }
  };

  useEffect(() => {
    if (itemsWithDetails.length > 0) calculateSummaryStats(itemsWithDetails);
  }, [itemsWithDetails]);

  const getFilteredItems = useMemo(() => {
    let filtered = itemsWithDetails;
    if (searchTerm) {
      const s = searchTerm.toLowerCase();
      filtered = filtered.filter(i => i.item_code.toLowerCase().includes(s) || i.item_name?.toLowerCase().includes(s) || i.description?.toLowerCase().includes(s));
    }
    if (selectedProjects.length > 0) filtered = filtered.filter(i => selectedProjects.includes(i.project_id));
    return filtered;
  }, [itemsWithDetails, searchTerm, selectedProjects]);

  const handleAccordionChange = (key: string) => (_: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedAccordion(isExpanded ? key : false);
  };

  const openItemDetails = async (itemDetails: ItemWithDetails) => {
    setSelectedItemDetails(itemDetails);
    try { const r = await projectsAPI.get(itemDetails.project_id); setProjectInfo(r.data); } catch { }
    try { const r = await deliveryOptionsAPI.listByItem(itemDetails.project_item_id); setItemDeliveryOptions(r.data); } catch { setItemDeliveryOptions([]); }
    try { const r = await itemsAPI.get(itemDetails.project_item_id); setItemSubItems(r.data?.sub_items || []); } catch { setItemSubItems([]); }
    setViewItemDialogOpen(true);
  };

  const openPackageWizard = async (itemDetails: ItemWithDetails) => {
    try {
      const subItemsResponse = await itemsAPI.listProjectItemSubItems(itemDetails.project_item_id);
      const subItemRequirements: SubItemRequirement[] = subItemsResponse.data.map((sub: any) => ({
        sub_item_id: sub.sub_item?.id || sub.id,
        item_subitem_id: sub.id,
        name: sub.sub_item?.name || `Sub-item ${sub.sub_item?.id || sub.id}`,
        part_number: sub.sub_item?.part_number,
        required_quantity: sub.quantity || 0,
      }));
      const existingPkgRes = await packagesAPI.listByProjectItem(itemDetails.project_item_id, true);
      setWizardProjectItemId(itemDetails.project_item_id);
      setWizardItemCode(itemDetails.item_code);
      setWizardItemName(itemDetails.item_name);
      setWizardMainItemQuantity(itemDetails.quantity || 0);
      setWizardSubItemRequirements(subItemRequirements);
      setWizardExistingPackages(existingPkgRes.data || []);
      setPackageWizardOpen(true);
    } catch (err: any) {
      setError(formatApiError(err, t('procurement.failedToOpenWizard') || 'Failed to open package wizard'));
    }
  };

  const openEditPackage = async (packageId: number, itemDetails: ItemWithDetails) => {
    try {
      const packageResponse = await packagesAPI.get(packageId);
      const packageData = packageResponse.data;
      const subitems = packageData?.subitems || [];
      const optionsResponse = await procurementAPI.listByProjectItem(itemDetails.project_item_id);
      const packageOption = optionsResponse.data.find((opt: any) => opt.package_id === packageId);
      const subItemsResponse = await itemsAPI.listProjectItemSubItems(itemDetails.project_item_id);
      const subItemRequirements: SubItemRequirement[] = subItemsResponse.data.map((sub: any) => ({
        sub_item_id: sub.sub_item?.id || sub.id, item_subitem_id: sub.id,
        name: sub.sub_item?.name || `Sub-item ${sub.sub_item?.id || sub.id}`,
        part_number: sub.sub_item?.part_number, required_quantity: sub.quantity || 0,
      }));
      const existingPkgRes = await packagesAPI.listByProjectItem(itemDetails.project_item_id, true);
      const subitemQuantities: Record<number, number> = {};
      subitems.forEach((si: any) => {
        const req = subItemRequirements.find(r => r.item_subitem_id === si.project_item_subitem_id);
        if (req) subitemQuantities[req.sub_item_id] = si.quantity_covered || 0;
      });
      setWizardProjectItemId(itemDetails.project_item_id);
      setWizardItemCode(itemDetails.item_code);
      setWizardItemName(itemDetails.item_name);
      setWizardMainItemQuantity(itemDetails.quantity || 0);
      setWizardSubItemRequirements(subItemRequirements);
      setWizardExistingPackages(existingPkgRes.data || []);
      setWizardInitialData({
        package_name: packageData.package_name || '', supplier_id: packageData.supplier_id || null,
        package_type: packageData.package_type || 'CUSTOM', description: packageData.description || '',
        main_item_quantity: packageData.main_item_quantity || 0, subitem_quantities: subitemQuantities,
        base_cost: packageOption?.base_cost || packageOption?.cost_amount || 0,
        currency_id: packageOption?.currency_id || null, shipping_cost: packageOption?.shipping_cost || 0,
        delivery_option_id: packageOption?.delivery_option_id || null, lomc_lead_time: packageOption?.lomc_lead_time || 0,
        purchase_date: packageOption?.purchase_date || new Date().toISOString().split('T')[0],
        expected_delivery_date: packageOption?.expected_delivery_date || '',
        payment_terms: packageOption?.payment_terms || { type: 'cash', discount_percent: 0 },
        discount_bundle_threshold: packageOption?.discount_bundle_threshold,
        discount_bundle_percent: packageOption?.discount_bundle_percent,
      });
      setEditingPackageId(packageId);
      setPackageWizardOpen(true);
    } catch (err: any) {
      setError(formatApiError(err, t('procurement.failedToLoadPackage') || 'Failed to load package'));
    }
  };

  const closePackageWizard = () => {
    setPackageWizardOpen(false); setWizardProjectItemId(null); setWizardItemCode('');
    setWizardItemName(''); setWizardMainItemQuantity(0); setWizardSubItemRequirements([]);
    setWizardExistingPackages([]); setEditingPackageId(null); setWizardInitialData(null);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={32} />
      </Box>
    );
  }

  const canProcure = user?.role === 'procurement' || user?.role === 'admin';

  return (
    <Box>
      <RivarPageHeader
        title={t('procurement.title')}
        subtitle={t('procurement.subtitle') || 'Manage procurement packages for finalized project items'}
        actions={canProcure ? (
          <>
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon sx={{ fontSize: 15 }} />}
              onClick={() => { setLoading(true); fetchData(); }}
            >
              {t('procurement.refresh')}
            </Button>
            <Button
              variant="outlined"
              size="small"
              startIcon={<AnalyticsIcon sx={{ fontSize: 15 }} />}
              onClick={() => {
                if (selectedProjects.length === 1) {
                  setSelectedProjectIdForCoverage(selectedProjects[0]);
                } else if (itemsWithDetails.length > 0) {
                  setSelectedProjectIdForCoverage(itemsWithDetails[0].project_id);
                } else {
                  setError(t('procurement.selectProjectForAnalysis') || 'Please select a project first.');
                  return;
                }
                setCoverageModalOpen(true);
              }}
            >
              {t('procurement.analyzeCoverage') || 'Analyze Coverage'}
            </Button>
          </>
        ) : undefined}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Summary metrics */}
      {summaryStats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={4} md={2.4}>
            <RivarMetricCard label={t('procurement.totalItems')} value={summaryStats.totalItems} icon={<InventoryIcon />} variant="default" />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <RivarMetricCard label={t('procurement.totalPackages') || 'Total Packages'} value={summaryStats.totalPackages || 0} icon={<ShoppingCartIcon />} variant="accent" />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <RivarMetricCard label={t('procurement.activePackages') || 'Active Packages'} value={summaryStats.activePackages || 0} icon={<AssignmentIcon />} variant="good" />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <RivarMetricCard label={t('procurement.itemsWithPackages') || 'Items w/ Packages'} value={summaryStats.itemsWithPackages || 0} icon={<LocalShippingIcon />} variant="warn" />
          </Grid>
          <Grid item xs={6} sm={4} md={2.4}>
            <RivarMetricCard label={t('procurement.suppliers')} value={summaryStats.uniqueSuppliers || 0} icon={<BusinessIcon />} variant="default" />
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <RivarPanel sx={{ mb: 3 }}>
        <RivarToolbar
          left={
            <TextField
              placeholder={t('procurement.searchPlaceholder') || 'Search by code, name, description…'}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="small"
              sx={{ minWidth: 260 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ fontSize: 16, color: rivarTokens.ink300 }} />
                  </InputAdornment>
                ),
              }}
            />
          }
          right={
            <>
              <FormControl size="small" sx={{ minWidth: 160 }}>
                <InputLabel>{t('procurement.projects')}</InputLabel>
                <Select
                  multiple
                  label={t('procurement.projects')}
                  value={selectedProjects}
                  onChange={(e) => setSelectedProjects(e.target.value as number[])}
                  renderValue={(s) => `${s.length} ${t('procurement.selected')}`}
                >
                  {[...new Map(itemsWithDetails.map(i => [i.project_id, i])).values()].map(item => (
                    <MenuItem key={item.project_id} value={item.project_id}>
                      {projectsMap[item.project_id] || `Project ${item.project_id}`}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {(searchTerm || selectedProjects.length > 0) && (
                <Button size="small" variant="outlined" onClick={() => { setSearchTerm(''); setSelectedProjects([]); }}>
                  Clear
                </Button>
              )}
            </>
          }
        />
        {(searchTerm || selectedProjects.length > 0) && (
          <Typography variant="caption" sx={{ color: rivarTokens.ink500 }}>
            {getFilteredItems.length} {t('procurement.itemsMatchFilters') || 'items match filters'}
          </Typography>
        )}
      </RivarPanel>

      {/* Items list */}
      {itemsWithDetails.length === 0 ? (
        <RivarPanel>
          <RivarEmptyState
            icon={<InventoryIcon />}
            title={t('procurement.noItemsAvailable') || 'No Project Items Available'}
            description={t('procurement.noItemsMessage') || 'Items will appear here once finalized by the PMO.'}
          />
        </RivarPanel>
      ) : (
        <>
          <Box sx={{ mb: 2 }}>
            {getFilteredItems
              .slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)
              .map((item) => {
                const accordionKey = `${item.item_code}-${item.project_item_id}`;
                return (
                  <Accordion
                    key={accordionKey}
                    expanded={expandedAccordion === accordionKey}
                    onChange={handleAccordionChange(accordionKey)}
                    sx={{ mb: 1 }}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ fontSize: 18 }} />}>
                      <Box
                        sx={{
                          width: '100%',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          pr: 1,
                          gap: 2,
                        }}
                      >
                        <Box sx={{ minWidth: 0 }}>
                          <Typography
                            sx={{
                              fontWeight: 600,
                              fontSize: '0.875rem',
                              color: rivarTokens.ink,
                            }}
                          >
                            {item.item_code}
                          </Typography>
                          <Typography
                            variant="caption"
                            sx={{ color: rivarTokens.ink500, display: 'block', mt: 0.25 }}
                          >
                            {item.item_name}
                            {projectsMap[item.project_id] && ` — ${projectsMap[item.project_id]}`}
                            {item.description && ` · ${item.description.substring(0, 80)}${item.description.length > 80 ? '…' : ''}`}
                          </Typography>
                        </Box>
                        <Box display="flex" alignItems="center" gap={1} flexShrink={0}>
                          {item.quantity !== undefined && (
                            <RivarStatusPill
                              label={`Qty: ${item.quantity}`}
                              variant="neutral"
                            />
                          )}
                          <IconButton
                            size="small"
                            onClick={async (e) => { e.stopPropagation(); await openItemDetails(item); }}
                            sx={{ color: rivarTokens.accent }}
                          >
                            <VisibilityIcon sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Box>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails sx={{ pt: 0 }}>
                      <PackageList
                        projectItemId={item.project_item_id}
                        itemCode={item.item_code}
                        itemName={item.item_name}
                        onEdit={(packageId) => openEditPackage(packageId, item)}
                        onDelete={async (packageId) => {
                          if (window.confirm(t('procurement.confirmDeletePackage') || 'Delete this package?')) {
                            try {
                              await packagesAPI.delete(packageId);
                              setPackageRefreshTrigger(p => p + 1);
                              fetchData();
                            } catch (err: any) {
                              setError(formatApiError(err, t('procurement.failedToDeletePackage') || 'Failed to delete'));
                            }
                          }
                        }}
                        onAnalyze={(_packageId) => {
                          setSelectedProjectIdForCoverage(item.project_id);
                          setCoverageModalOpen(true);
                        }}
                        onSendToOptimizer={(packageId) => {
                          console.log('Send package to optimizer:', packageId);
                        }}
                        refreshTrigger={packageRefreshTrigger}
                      />
                      {canProcure && (
                        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-start' }}>
                          <Button
                            variant="contained"
                            size="small"
                            startIcon={<AddIcon sx={{ fontSize: 15 }} />}
                            onClick={() => openPackageWizard(item)}
                          >
                            {t('procurement.createPackage') || 'Create Package'}
                          </Button>
                        </Box>
                      )}
                    </AccordionDetails>
                  </Accordion>
                );
              })}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
            <Pagination
              count={Math.ceil(getFilteredItems.length / ITEMS_PER_PAGE)}
              page={page + 1}
              onChange={(_, p) => setPage(p - 1)}
              color="primary"
              size="small"
              showFirstButton
              showLastButton
            />
            <Typography variant="caption" sx={{ color: rivarTokens.ink500 }}>
              {page * ITEMS_PER_PAGE + 1}–{Math.min((page + 1) * ITEMS_PER_PAGE, getFilteredItems.length)} / {getFilteredItems.length}
            </Typography>
          </Box>
        </>
      )}

      {/* Coverage Summary Modal */}
      {coverageModalOpen && selectedProjectIdForCoverage && (
        <CoverageSummaryModal
          open={coverageModalOpen}
          onClose={() => { setCoverageModalOpen(false); setSelectedProjectIdForCoverage(null); }}
          projectId={selectedProjectIdForCoverage}
          onCreateForRemaining={(remainingDemand) => {
            const itemDetails = itemsWithDetails.find(i => i.project_item_id === remainingDemand.project_item_id);
            if (itemDetails) {
              setWizardProjectItemId(itemDetails.project_item_id);
              setWizardItemCode(itemDetails.item_code);
              setWizardItemName(itemDetails.item_name);
              setWizardMainItemQuantity(remainingDemand.main_item_remaining);
              setWizardSubItemRequirements(
                remainingDemand.subitem_remaining.map((si: any) => ({
                  sub_item_id: si.sub_item_id, item_subitem_id: si.item_subitem_id, required_quantity: si.remaining_quantity,
                }))
              );
              setWizardExistingPackages([]);
              setPackageWizardOpen(true);
              setCoverageModalOpen(false);
            }
          }}
        />
      )}

      {/* Package Wizard */}
      {packageWizardOpen && wizardProjectItemId && (
        <PackageWizard
          open={packageWizardOpen}
          onClose={closePackageWizard}
          projectItemId={wizardProjectItemId}
          itemCode={wizardItemCode}
          itemName={wizardItemName}
          mainItemRequiredQuantity={wizardMainItemQuantity}
          subItemRequirements={wizardSubItemRequirements}
          existingPackages={wizardExistingPackages}
          editingPackageId={editingPackageId}
          initialData={wizardInitialData}
          onPackageCreated={async () => {
            setPackageRefreshTrigger(p => p + 1);
            fetchData();
            setEditingPackageId(null);
            setWizardInitialData(null);
          }}
        />
      )}

      {/* View Item Detail Dialog */}
      <Dialog open={viewItemDialogOpen} onClose={() => setViewItemDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogContent sx={{ p: 0 }}>
          {selectedItemDetails && (
            <Box sx={{ p: 3 }}>
              {/* Header */}
              <Box display="flex" alignItems="center" gap={1.5} mb={3}>
                <Box
                  sx={{
                    width: 40, height: 40, borderRadius: '10px',
                    background: rivarTokens.accentTint, display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                  }}
                >
                  <InventoryIcon sx={{ color: rivarTokens.accent600, fontSize: 20 }} />
                </Box>
                <Box>
                  <Typography sx={{ fontWeight: 700, fontSize: '1rem', color: rivarTokens.accent600 }}>
                    {selectedItemDetails.item_code}
                  </Typography>
                  <Typography variant="caption" sx={{ color: rivarTokens.ink500 }}>
                    {selectedItemDetails.item_name || t('procurement.notSpecified')}
                  </Typography>
                </Box>
              </Box>

              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6}>
                  <Box sx={{ background: rivarTokens.surface, borderRadius: rivarTokens.radiusMd, p: 1.5 }}>
                    <Typography variant="caption" sx={{ color: rivarTokens.ink500 }}>{t('procurement.quantity')}</Typography>
                    <Typography sx={{ fontWeight: 700, fontSize: '1.25rem', fontFamily: 'ui-monospace, monospace' }}>
                      {selectedItemDetails.quantity || 0}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ background: rivarTokens.surface, borderRadius: rivarTokens.radiusMd, p: 1.5 }}>
                    <Typography variant="caption" sx={{ color: rivarTokens.ink500 }}>{t('procurement.projectName')}</Typography>
                    <Typography sx={{ fontWeight: 600, fontSize: '0.875rem' }}>
                      {projectInfo?.name || t('procurement.loading')}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              {selectedItemDetails.description && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="caption" sx={{ color: rivarTokens.ink500, display: 'block', mb: 0.5 }}>{t('procurement.description')}</Typography>
                  <Typography variant="body2">{selectedItemDetails.description}</Typography>
                </Box>
              )}

              {/* Sub-items */}
              {itemSubItems && itemSubItems.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>{t('procurement.subItems') || 'Sub-Items'}</Typography>
                  {itemSubItems.map((si) => (
                    <Box
                      key={si.sub_item_id}
                      sx={{ p: 1.5, mb: 1, border: `1px solid ${rivarTokens.line}`, borderRadius: rivarTokens.radiusSm }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>{si.name || '-'}</Typography>
                      <Typography variant="caption" sx={{ color: rivarTokens.ink300 }}>{si.part_number || '-'}</Typography>
                      <Typography variant="caption" sx={{ display: 'block' }}>{t('procurement.quantity')}: {si.quantity}</Typography>
                    </Box>
                  ))}
                </Box>
              )}

              {/* Delivery options */}
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 1.5 }}>{t('procurement.deliveryInvoiceOptions')}</Typography>
              {itemDeliveryOptions.length > 0 ? (
                itemDeliveryOptions.map((option, idx) => (
                  <Box
                    key={option.id}
                    sx={{ p: 2, mb: 1.5, background: rivarTokens.surface, borderRadius: rivarTokens.radiusMd, border: `1px solid ${rivarTokens.line}` }}
                  >
                    <Typography variant="caption" sx={{ fontWeight: 600, color: rivarTokens.ink }}>
                      {t('procurement.option')} {idx + 1} — {t('procurement.slot')} {option.delivery_slot ?? 'N/A'}
                    </Typography>
                    <Grid container spacing={2} sx={{ mt: 0.5 }}>
                      <Grid item xs={6}>
                        <Typography variant="caption" sx={{ color: rivarTokens.ink500 }}>{t('procurement.deliveryDate')}</Typography>
                        <Typography variant="body2">{option.delivery_date ? formatDisplayDate(option.delivery_date) : '-'}</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" sx={{ color: rivarTokens.ink500 }}>{t('procurement.item')}</Typography>
                        <Typography variant="body2">{selectedItemDetails.item_name || '-'}</Typography>
                      </Grid>
                      {option.notes && (
                        <Grid item xs={12}>
                          <Typography variant="caption" sx={{ color: rivarTokens.ink500 }}>{t('procurement.optionalNotes')}</Typography>
                          <Typography variant="body2">{option.notes}</Typography>
                        </Grid>
                      )}
                    </Grid>
                  </Box>
                ))
              ) : (
                <Box sx={{ p: 2, background: rivarTokens.surface, borderRadius: rivarTokens.radiusMd, textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ color: rivarTokens.ink500 }}>{t('procurement.noDeliveryOptions')}</Typography>
                </Box>
              )}

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button variant="outlined" size="small" onClick={() => setViewItemDialogOpen(false)}>
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
