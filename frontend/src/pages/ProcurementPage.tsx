import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
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
  Checkbox,
  FormControlLabel,
  FormGroup,
  Divider,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Pagination,
  Grid,
  InputAdornment,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { formatApiError } from '../utils/errorUtils.ts';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Send as SendIcon,
  Search as SearchIcon,
  Visibility as VisibilityIcon,
  Analytics as AnalyticsIcon,
  ExpandMore as ExpandMoreIcon,
  Inventory as InventoryIcon,
  ShoppingCart as ShoppingCartIcon,
  LocalShipping as LocalShippingIcon,
  Business as BusinessIcon,
  Assignment as AssignmentIcon,
  RestartAlt as RestartAltIcon,
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
import { MyProcurementAssignmentsPanel } from '../components/procurement/MyProcurementAssignmentsPanel.tsx';
import { canViewProcurementAssignments } from '../utils/permissions.ts';
import { RivarMetricCard } from '../components/ui/RivarMetricCard.tsx';
import { RivarPanel } from '../components/ui/RivarPanel.tsx';
import { RivarToolbar } from '../components/ui/RivarToolbar.tsx';
import { RivarEmptyState } from '../components/ui/RivarEmptyState.tsx';
import { RivarStatusPill } from '../components/ui/RivarStatusPill.tsx';
import { LocalizedDateProvider } from '../components/LocalizedDateProvider.tsx';
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
  coverage_state?: string;
  coverage_percentage?: number;
  optimization_state?: 'not_sent_to_optimization' | 'sent_to_optimization' | 'rolled_back_from_optimization';
  is_sent_to_optimization?: boolean;
  active_package_count?: number;
  finalized_package_count?: number;
  can_rollback_optimization_submission?: boolean;
}

interface Supplier {
  id: number;
  supplier_id: string;
  company_name: string;
}

type RollbackDateField = 'submitted_at' | 'delivery_date' | 'purchase_date' | 'project_need_date';

interface BulkRollbackFilters {
  include_full_package_items: boolean;
  include_partial_package_items: boolean;
  include_complete_coverage_items: boolean;
  include_incomplete_coverage_items: boolean;
  include_over_covered_items: boolean;
  include_domestic_suppliers: boolean;
  include_foreign_suppliers: boolean;
  include_single_supplier_items: boolean;
  include_multiple_supplier_items: boolean;
  include_warning_incomplete_submissions: boolean;
  min_total_cost_irr?: number;
  max_total_cost_irr?: number;
  date_from?: string;
  date_to?: string;
  date_field: RollbackDateField;
  project_ids: number[];
  supplier_ids: number[];
}

interface BulkRollbackPreviewItem {
  project_item_id: number;
  item_code: string;
  item_name?: string;
  package_type_bucket: string;
  coverage_state: string;
  supplier_bucket: string;
  supplier_count: number;
  total_cost_irr?: number | null;
  selected_date?: string | null;
  skip_reasons?: Array<{ code?: string; reason?: string; count?: number }>;
}

interface BulkRollbackPreviewResponse {
  matched_items: BulkRollbackPreviewItem[];
  rollbackable_items: BulkRollbackPreviewItem[];
  unsafe_items: BulkRollbackPreviewItem[];
  summary: {
    matched_count: number;
    rollbackable_count: number;
    unsafe_count: number;
    by_package_type: Record<string, number>;
    by_coverage_state: Record<string, number>;
    by_supplier_type: Record<string, number>;
    by_date_range: Record<string, number>;
    by_cost_range: Record<string, number>;
  };
  warnings: string[];
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
  const [selectedProjectItemIdForCoverage, setSelectedProjectItemIdForCoverage] = useState<number | null>(null);
  const [expandedAccordion, setExpandedAccordion] = useState<string | false>(false);
  const [page, setPage] = useState(0);
  const ITEMS_PER_PAGE = 50;
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
  const [summaryStats, setSummaryStats] = useState<any>(null);
  const [optimizationFilter, setOptimizationFilter] = useState<'all' | 'not_sent' | 'sent' | 'rolled_back'>('all');
  const [coverageFilter, setCoverageFilter] = useState<'all' | 'no_package' | 'partial' | 'full' | 'over_covered' | 'missing_components'>('all');
  const [notice, setNotice] = useState('');
  const [bulkRollbackOpen, setBulkRollbackOpen] = useState(false);
  const [bulkRollbackLoading, setBulkRollbackLoading] = useState(false);
  const [bulkRollbackExecuting, setBulkRollbackExecuting] = useState(false);
  const [bulkRollbackNote, setBulkRollbackNote] = useState('');
  const [bulkRollbackFilters, setBulkRollbackFilters] = useState<BulkRollbackFilters>({
    include_full_package_items: true,
    include_partial_package_items: true,
    include_complete_coverage_items: true,
    include_incomplete_coverage_items: true,
    include_over_covered_items: true,
    include_domestic_suppliers: true,
    include_foreign_suppliers: true,
    include_single_supplier_items: true,
    include_multiple_supplier_items: true,
    include_warning_incomplete_submissions: true,
    date_field: 'submitted_at',
    project_ids: [],
    supplier_ids: [],
  });
  const [bulkRollbackPreview, setBulkRollbackPreview] = useState<BulkRollbackPreviewResponse | null>(null);
  const [bulkRollbackSelectedIds, setBulkRollbackSelectedIds] = useState<number[]>([]);

  const hasAnyRollbackChecklistFilterSelected = useMemo(() => (
    bulkRollbackFilters.include_full_package_items ||
    bulkRollbackFilters.include_partial_package_items ||
    bulkRollbackFilters.include_complete_coverage_items ||
    bulkRollbackFilters.include_incomplete_coverage_items ||
    bulkRollbackFilters.include_over_covered_items ||
    bulkRollbackFilters.include_domestic_suppliers ||
    bulkRollbackFilters.include_foreign_suppliers ||
    bulkRollbackFilters.include_single_supplier_items ||
    bulkRollbackFilters.include_multiple_supplier_items ||
    bulkRollbackFilters.include_warning_incomplete_submissions
  ), [bulkRollbackFilters]);

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

  useEffect(() => { fetchData(); }, [optimizationFilter, coverageFilter]);

  const fetchData = async () => {
    try {
      const itemsResponse = await itemsAPI.listFinalized({
        skip: 0,
        limit: 10000,
        optimization_state: optimizationFilter,
        coverage_state: coverageFilter,
      });
      const mapped = itemsResponse.data.map((item: any) => ({
        item_code: item.item_code, item_name: item.item_name, description: item.description || '',
        project_id: item.project_id, project_item_id: item.id, quantity: item.quantity,
        status: item.status, external_purchase: item.external_purchase, file_path: item.file_path,
        file_name: item.file_name, decision_date: item.decision_date, procurement_date: item.procurement_date,
        payment_date: item.payment_date, invoice_submission_date: item.invoice_submission_date,
        expected_cash_in_date: item.expected_cash_in_date, actual_cash_in_date: item.actual_cash_in_date,
        is_finalized: item.is_finalized, finalized_by: item.finalized_by, finalized_at: item.finalized_at,
        created_at: item.created_at, updated_at: item.updated_at,
        coverage_state: item.coverage_state,
        coverage_percentage: item.coverage_percentage,
        optimization_state: item.optimization_state,
        is_sent_to_optimization: item.is_sent_to_optimization,
        active_package_count: item.active_package_count,
        finalized_package_count: item.finalized_package_count,
        can_rollback_optimization_submission: item.can_rollback_optimization_submission,
      }));
      setItemsWithDetails(mapped);
      calculateSummaryStats(mapped);
    } catch (err: any) {
      setError(formatApiError(err, 'Failed to load procurement data'));
    } finally {
      setLoading(false);
    }
  };

  const buildIncompleteCoverageMessage = (response: any) => {
    const incompleteItems = response?.incomplete_items_requiring_confirmation || [];
    if (!incompleteItems.length) return '';
    return incompleteItems.map((item: any) => {
      const missing = (item.missing_components || [])
        .slice(0, 5)
        .map((m: any) => {
          const label = m.name || m.component || 'component';
          return `- ${label}: missing ${m.missing}`;
        })
        .join('\n');
      return (
        `${item.item_code || item.project_item_id}: coverage ${Math.round(item.coverage_percentage || 0)}%\n` +
        (missing || '- Missing required quantities')
      );
    }).join('\n\n');
  };

  const submitToOptimizationGate = async (payload: any, label: string) => {
    const first = await packagesAPI.submitToOptimization(payload);
    let data = first.data;
    const incompleteItems = data?.incomplete_items_requiring_confirmation || [];
    if (incompleteItems.length > 0) {
      const message =
        `Some items are incomplete and require confirmation before submission:\n\n` +
        `${buildIncompleteCoverageMessage(data)}\n\n` +
        `Send incomplete items anyway?`;
      const confirmed = window.confirm(message);
      if (confirmed) {
        const confirmedIds = incompleteItems.map((item: any) => item.project_item_id);
        const second = await packagesAPI.submitToOptimization({
          ...payload,
          include_incomplete_with_confirmation: true,
          confirmed_incomplete_item_ids: confirmedIds,
        });
        data = second.data;
      }
    }

    const submitted = data?.submitted_items?.length || 0;
    const skipped = data?.skipped_items?.length || 0;
    setNotice(`${label}: submitted ${submitted}, skipped ${skipped}`);
    if ((data?.warnings || []).length > 0) {
      setError((data.warnings as string[]).join('\n'));
    }
    setPackageRefreshTrigger(p => p + 1);
    await fetchData();
  };

  const handleRollbackOptimizationSubmission = async (item: ItemWithDetails) => {
    const yes = window.confirm(
      t('procurement.confirmRollbackOptimization') ||
      'Rollback optimization submission for this item and unlock package editing?'
    );
    if (!yes) return;
    try {
      await packagesAPI.rollbackOptimizationSubmission(item.project_item_id);
      setNotice(
        t('procurement.rollbackSuccess') ||
        `Rollback completed for ${item.item_code}`
      );
      setPackageRefreshTrigger(p => p + 1);
      await fetchData();
    } catch (err: any) {
      setError(formatApiError(err, t('procurement.rollbackFailed') || 'Rollback failed'));
    }
  };

  const buildBulkRollbackPayload = () => ({
    filters: {
      ...bulkRollbackFilters,
      min_total_cost_irr:
        bulkRollbackFilters.min_total_cost_irr === undefined ||
        Number.isNaN(Number(bulkRollbackFilters.min_total_cost_irr))
          ? undefined
          : Number(bulkRollbackFilters.min_total_cost_irr),
      max_total_cost_irr:
        bulkRollbackFilters.max_total_cost_irr === undefined ||
        Number.isNaN(Number(bulkRollbackFilters.max_total_cost_irr))
          ? undefined
          : Number(bulkRollbackFilters.max_total_cost_irr),
      date_from: bulkRollbackFilters.date_from || undefined,
      date_to: bulkRollbackFilters.date_to || undefined,
    },
  });

  const openBulkRollbackDialog = () => {
    setBulkRollbackOpen(true);
    setBulkRollbackPreview(null);
    setBulkRollbackSelectedIds([]);
    setBulkRollbackNote('');
  };

  const runBulkRollbackPreview = async () => {
    if (!hasAnyRollbackChecklistFilterSelected) {
      setError(
        t('procurement.rollbackSelectAtLeastOneFilter') ||
        'Select at least one rollback filter before preview.'
      );
      return;
    }
    try {
      setBulkRollbackLoading(true);
      const response = await packagesAPI.previewBulkRollback(buildBulkRollbackPayload());
      const preview = response.data as BulkRollbackPreviewResponse;
      setBulkRollbackPreview(preview);
      setBulkRollbackSelectedIds(
        (preview.rollbackable_items || []).map((item) => Number(item.project_item_id))
      );
    } catch (err: any) {
      setError(formatApiError(err, t('procurement.rollbackFailed') || 'Rollback preview failed'));
    } finally {
      setBulkRollbackLoading(false);
    }
  };

  const executeBulkRollback = async () => {
    if (!hasAnyRollbackChecklistFilterSelected) {
      setError(
        t('procurement.rollbackSelectAtLeastOneFilter') ||
        'Select at least one rollback filter before confirmation.'
      );
      return;
    }
    if (bulkRollbackSelectedIds.length === 0) {
      setError(t('procurement.noRollbackSelection') || 'Select at least one rollbackable item.');
      return;
    }
    const yes = window.confirm(
      t('procurement.confirmBulkRollback') ||
      'Rollback selected items from optimization and unlock package editing?'
    );
    if (!yes) return;

    try {
      setBulkRollbackExecuting(true);
      const response = await packagesAPI.executeBulkRollback({
        ...buildBulkRollbackPayload(),
        selected_item_ids: bulkRollbackSelectedIds,
        confirmed: true,
        notes: bulkRollbackNote || undefined,
      });
      const data = response.data || {};
      const rolledBack = data?.rolled_back_items?.length || 0;
      const skipped = data?.skipped_items?.length || 0;
      setNotice(
        `${t('procurement.bulkRollbackSummary') || 'Bulk rollback'}: ${rolledBack} ${t('procurement.rolledBack') || 'rolled back'}, ${skipped} ${t('procurement.skipped') || 'skipped'}`
      );
      if ((data?.warnings || []).length > 0) {
        setError((data.warnings as string[]).join('\n'));
      }
      setBulkRollbackOpen(false);
      setBulkRollbackPreview(null);
      setBulkRollbackSelectedIds([]);
      setPackageRefreshTrigger((p) => p + 1);
      await fetchData();
    } catch (err: any) {
      setError(formatApiError(err, t('procurement.rollbackFailed') || 'Bulk rollback failed'));
    } finally {
      setBulkRollbackExecuting(false);
    }
  };

  const toggleRollbackSelection = (projectItemId: number) => {
    setBulkRollbackSelectedIds((prev) => (
      prev.includes(projectItemId)
        ? prev.filter((id) => id !== projectItemId)
        : [...prev, projectItemId]
    ));
  };

  const selectAllRollbackChecklistFilters = () => {
    setBulkRollbackFilters((prev) => ({
      ...prev,
      include_full_package_items: true,
      include_partial_package_items: true,
      include_complete_coverage_items: true,
      include_incomplete_coverage_items: true,
      include_over_covered_items: true,
      include_domestic_suppliers: true,
      include_foreign_suppliers: true,
      include_single_supplier_items: true,
      include_multiple_supplier_items: true,
      include_warning_incomplete_submissions: true,
    }));
  };

  const deselectAllRollbackChecklistFilters = () => {
    setBulkRollbackFilters((prev) => ({
      ...prev,
      include_full_package_items: false,
      include_partial_package_items: false,
      include_complete_coverage_items: false,
      include_incomplete_coverage_items: false,
      include_over_covered_items: false,
      include_domestic_suppliers: false,
      include_foreign_suppliers: false,
      include_single_supplier_items: false,
      include_multiple_supplier_items: false,
      include_warning_incomplete_submissions: false,
    }));
    setBulkRollbackPreview(null);
    setBulkRollbackSelectedIds([]);
  };

  const selectAllRollbackableItems = () => {
    setBulkRollbackSelectedIds(
      (bulkRollbackPreview?.rollbackable_items || []).map((item) => Number(item.project_item_id))
    );
  };

  const deselectAllRollbackableItems = () => {
    setBulkRollbackSelectedIds([]);
  };

  const calculateSummaryStats = async (items?: ItemWithDetails[]) => {
    const toProcess = items || itemsWithDetails;
    const uniqueProjectIds = Array.from(new Set(toProcess.map((it) => it.project_id)));

    let allPackages: any[] = [];
    try {
      const packageResponses = await Promise.all(
        uniqueProjectIds.map((projectId) =>
          packagesAPI.listByProject(projectId, true).catch(() => ({ data: [] }))
        )
      );
      allPackages = packageResponses.flatMap((res: any) => (Array.isArray(res.data) ? res.data : []));
    } catch {
      allPackages = [];
    }

    const uniqueSuppliers = new Set<string>();
    allPackages.forEach((pkg: any) => {
      if (pkg?.supplier?.company_name) uniqueSuppliers.add(pkg.supplier.company_name);
    });

    const itemIdsWithPackage = new Set<number>(
      allPackages.map((pkg: any) => Number(pkg.project_item_id)).filter((id: number) => Number.isFinite(id))
    );

    setSummaryStats({
      totalItems: toProcess.length,
      totalPackages: allPackages.length,
      activePackages: allPackages.filter((pkg: any) => pkg.is_active).length,
      itemsWithPackages: toProcess.filter((it) => itemIdsWithPackage.has(it.project_item_id)).length,
      uniqueSuppliers: uniqueSuppliers.size,
      suppliers: Array.from(uniqueSuppliers),
    });
  };

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

  const sentItemsCount = itemsWithDetails.filter((item) => item.is_sent_to_optimization).length;

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
        is_finalized: packageData.is_finalized ?? packageOption?.is_finalized ?? false,
        base_cost: packageOption?.base_cost || packageOption?.cost_amount || 0,
        currency_id: packageOption?.currency_id || null, shipping_cost: packageOption?.shipping_cost || 0,
        delivery_option_id: packageOption?.delivery_option_id || null, lomc_lead_time: packageOption?.lomc_lead_time || 0,
        purchase_date: packageOption?.purchase_date || new Date().toISOString().split('T')[0],
        expected_delivery_date: packageOption?.expected_delivery_date || '',
        payment_terms: packageOption?.payment_terms || { type: 'cash', discount_percent: 0 },
        discount_bundle_threshold: packageOption?.discount_bundle_threshold,
        discount_bundle_percent: packageOption?.discount_bundle_percent,
        option_id: packageOption?.id || null,
        payment_method_id: packageOption?.payment_method_id || null,
        payment_date:
          packageOption?.planned_supplier_payment_date ||
          packageOption?.purchase_date ||
          new Date().toISOString().split('T')[0],
        planned_supplier_payment_date: packageOption?.planned_supplier_payment_date || '',
        supplier_effective_receipt_date: packageOption?.supplier_effective_receipt_date || '',
        cost_components: [],
        project_requested_delivery_date: packageOption?.project_requested_delivery_date || '',
        supplier_actual_delivery_date: packageOption?.supplier_actual_delivery_date || '',
        selected_delivery_date: packageOption?.selected_delivery_date || '',
        delivery_date_source: packageOption?.delivery_date_source || null,
        delivery_date_variance_days: packageOption?.delivery_date_variance_days ?? null,
        forecast_customer_invoice_date: packageOption?.forecast_customer_invoice_date || '',
        forecast_customer_invoice_date_source:
          packageOption?.forecast_customer_invoice_date_source || null,
        forecast_customer_receipt_date: packageOption?.forecast_customer_receipt_date || '',
        forecast_customer_receipt_date_source:
          packageOption?.forecast_customer_receipt_date_source || null,
        forecast_customer_receipt_delay_days:
          packageOption?.forecast_customer_receipt_delay_days ?? null,
        date_calculation_trace: packageOption?.date_calculation_trace || [],
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
                setSelectedProjectItemIdForCoverage(null); // full project analysis from header action
                setCoverageModalOpen(true);
              }}
            >
              {t('procurement.analyzeCoverage') || 'Analyze Coverage'}
            </Button>
            <Button
              variant="contained"
              size="small"
              startIcon={<SendIcon sx={{ fontSize: 15 }} />}
              onClick={async () => {
                try {
                  await submitToOptimizationGate(
                    { send_all_finalized: true },
                    t('procurement.bulkSendFinalized') || 'Bulk send finalized packages'
                  );
                } catch (err: any) {
                  setError(formatApiError(err, t('procurement.sendToOptimizerFailed') || 'Failed to send finalized packages'));
                }
              }}
            >
              {t('procurement.sendAllFinalizedToOptimization') || 'Send all finalized packages to optimization'}
            </Button>
            <Button
              variant="outlined"
              size="small"
              color="warning"
              startIcon={<RestartAltIcon sx={{ fontSize: 15 }} />}
              disabled={sentItemsCount === 0}
              onClick={openBulkRollbackDialog}
            >
              {t('procurement.bulkRollbackFromOptimization') || 'Rollback from optimization'}
            </Button>
          </>
        ) : undefined}
      />

      {canViewProcurementAssignments(user) && <MyProcurementAssignmentsPanel />}

      {notice && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setNotice('')}>
          {notice}
        </Alert>
      )}

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
              <FormControl size="small" sx={{ minWidth: 190 }}>
                <InputLabel>{t('procurement.optimizationState') || 'Optimization state'}</InputLabel>
                <Select
                  label={t('procurement.optimizationState') || 'Optimization state'}
                  value={optimizationFilter}
                  onChange={(e) => setOptimizationFilter(e.target.value as any)}
                >
                  <MenuItem value="all">{t('procurement.allOptimizationStates') || 'All'}</MenuItem>
                  <MenuItem value="not_sent">{t('procurement.notSentToOptimization') || 'Not sent'}</MenuItem>
                  <MenuItem value="sent">{t('procurement.sentToOptimization') || 'Sent to optimization'}</MenuItem>
                  <MenuItem value="rolled_back">{t('procurement.rolledBackFromOptimization') || 'Rolled back'}</MenuItem>
                </Select>
              </FormControl>
              <FormControl size="small" sx={{ minWidth: 190 }}>
                <InputLabel>{t('procurement.coverageState') || 'Coverage state'}</InputLabel>
                <Select
                  label={t('procurement.coverageState') || 'Coverage state'}
                  value={coverageFilter}
                  onChange={(e) => setCoverageFilter(e.target.value as any)}
                >
                  <MenuItem value="all">{t('procurement.allCoverageStates') || 'All'}</MenuItem>
                  <MenuItem value="no_package">{t('procurement.noPackageDefined') || 'No package defined'}</MenuItem>
                  <MenuItem value="partial">{t('procurement.partiallyCovered') || 'Partially covered'}</MenuItem>
                  <MenuItem value="full">{t('procurement.fullyCovered') || 'Fully covered'}</MenuItem>
                  <MenuItem value="over_covered">{t('procurement.overCovered') || 'Over-covered'}</MenuItem>
                  <MenuItem value="missing_components">{t('procurement.missingComponents') || 'Missing components'}</MenuItem>
                </Select>
              </FormControl>
              {(searchTerm || selectedProjects.length > 0 || optimizationFilter !== 'all' || coverageFilter !== 'all') && (
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => {
                    setSearchTerm('');
                    setSelectedProjects([]);
                    setOptimizationFilter('all');
                    setCoverageFilter('all');
                  }}
                >
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
                          {item.optimization_state === 'sent_to_optimization' && (
                            <RivarStatusPill
                              label={t('procurement.sentToOptimization') || 'Sent to optimization'}
                              variant="accent"
                            />
                          )}
                          {item.optimization_state === 'rolled_back_from_optimization' && (
                            <RivarStatusPill
                              label={t('procurement.rolledBackFromOptimization') || 'Rolled back'}
                              variant="warn"
                            />
                          )}
                          {item.coverage_state && (
                            <RivarStatusPill
                              label={`${t('procurement.coverage') || 'Coverage'}: ${item.coverage_state.replace(/_/g, ' ')}`}
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
                        enabled={expandedAccordion === accordionKey}
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
                        refreshTrigger={packageRefreshTrigger}
                      />
                      {canProcure && (
                        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-start', gap: 1 }}>
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<AnalyticsIcon sx={{ fontSize: 15 }} />}
                            onClick={() => {
                              setSelectedProjectIdForCoverage(item.project_id);
                              setSelectedProjectItemIdForCoverage(item.project_item_id);
                              setCoverageModalOpen(true);
                            }}
                          >
                            {t('procurement.analyzeCoverage') || 'Analyze Coverage'}
                          </Button>
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<SendIcon sx={{ fontSize: 15 }} />}
                            disabled={item.is_sent_to_optimization || (item.finalized_package_count || 0) === 0}
                            onClick={async () => {
                              try {
                                await submitToOptimizationGate(
                                  { project_item_id: item.project_item_id },
                                  t('procurement.sendToOptimizer') || 'Send to optimization'
                                );
                              } catch (err: any) {
                                setError(formatApiError(err, t('procurement.sendToOptimizerFailed') || 'Failed to send to optimizer'));
                              }
                            }}
                          >
                            {t('procurement.sendToOptimizer') || 'Send to Optimizer'}
                          </Button>
                          {item.is_sent_to_optimization && (
                            <Button
                              variant="outlined"
                              size="small"
                              color="warning"
                              startIcon={<RestartAltIcon sx={{ fontSize: 15 }} />}
                              disabled={!item.can_rollback_optimization_submission}
                              onClick={() => handleRollbackOptimizationSubmission(item)}
                            >
                              {t('procurement.rollbackOptimizationSubmission') || 'Rollback submission'}
                            </Button>
                          )}
                          <Button
                            variant="contained"
                            size="small"
                            startIcon={<AddIcon sx={{ fontSize: 15 }} />}
                            disabled={item.is_sent_to_optimization}
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

      <Dialog
        open={bulkRollbackOpen}
        onClose={() => !bulkRollbackExecuting && setBulkRollbackOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {t('procurement.bulkRollbackFromOptimization') || 'Rollback from optimization'}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ color: rivarTokens.ink500, mb: 2 }}>
            {t('procurement.bulkRollbackHint') || 'Preview safe rollbackable sent items, then confirm to unlock package editing.'}
          </Typography>

          <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
            <Button size="small" variant="outlined" onClick={selectAllRollbackChecklistFilters}>
              {t('procurement.selectAllFilters') || 'Select all filters'}
            </Button>
            <Button size="small" variant="outlined" color="inherit" onClick={deselectAllRollbackChecklistFilters}>
              {t('procurement.deselectAllFilters') || 'Deselect all filters'}
            </Button>
          </Box>

          <FormGroup row sx={{ mb: 1 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_full_package_items}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_full_package_items: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterFullPackages') || 'Full package items'}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_partial_package_items}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_partial_package_items: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterPartialPackages') || 'Partial package items'}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_complete_coverage_items}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_complete_coverage_items: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterCompleteCoverage') || 'Complete coverage'}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_incomplete_coverage_items}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_incomplete_coverage_items: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterIncompleteCoverage') || 'Incomplete coverage'}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_over_covered_items}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_over_covered_items: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterOverCovered') || 'Over-covered / surplus'}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_domestic_suppliers}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_domestic_suppliers: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterDomestic') || 'Domestic suppliers'}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_foreign_suppliers}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_foreign_suppliers: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterForeign') || 'Foreign suppliers'}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_single_supplier_items}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_single_supplier_items: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterSingleSupplier') || 'Single supplier'}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_multiple_supplier_items}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_multiple_supplier_items: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterMultipleSupplier') || 'Multiple suppliers'}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={bulkRollbackFilters.include_warning_incomplete_submissions}
                  onChange={(e) => setBulkRollbackFilters((prev) => ({ ...prev, include_warning_incomplete_submissions: e.target.checked }))}
                />
              }
              label={t('procurement.rollbackFilterWarningIncomplete') || 'Warning-based incomplete submissions'}
            />
          </FormGroup>

          <Divider sx={{ my: 1.5 }} />
          <Grid container spacing={1.5} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={4}>
              <TextField
                label={t('procurement.minCostIrr') || 'Min Cost (IRR)'}
                type="number"
                value={bulkRollbackFilters.min_total_cost_irr ?? ''}
                onChange={(e) =>
                  setBulkRollbackFilters((prev) => ({
                    ...prev,
                    min_total_cost_irr: e.target.value === '' ? undefined : Number(e.target.value),
                  }))
                }
                size="small"
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label={t('procurement.maxCostIrr') || 'Max Cost (IRR)'}
                type="number"
                value={bulkRollbackFilters.max_total_cost_irr ?? ''}
                onChange={(e) =>
                  setBulkRollbackFilters((prev) => ({
                    ...prev,
                    max_total_cost_irr: e.target.value === '' ? undefined : Number(e.target.value),
                  }))
                }
                size="small"
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>{t('procurement.rollbackDateField') || 'Date Field'}</InputLabel>
                <Select
                  label={t('procurement.rollbackDateField') || 'Date Field'}
                  value={bulkRollbackFilters.date_field}
                  onChange={(e) =>
                    setBulkRollbackFilters((prev) => ({ ...prev, date_field: e.target.value as RollbackDateField }))
                  }
                >
                  <MenuItem value="submitted_at">{t('procurement.rollbackDateSubmittedAt') || 'Sent-to-optimization date'}</MenuItem>
                  <MenuItem value="delivery_date">{t('procurement.rollbackDateDelivery') || 'Supplier expected delivery date'}</MenuItem>
                  <MenuItem value="purchase_date">{t('procurement.rollbackDatePurchase') || 'Purchase/order date'}</MenuItem>
                  <MenuItem value="project_need_date">{t('procurement.rollbackDateNeed') || 'Project need/delivery date'}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <LocalizedDateProvider>
                <DatePicker
                  label={t('procurement.fromDate') || 'From Date'}
                  value={bulkRollbackFilters.date_from ? new Date(`${bulkRollbackFilters.date_from}T00:00:00`) : null}
                  onChange={(newValue) => {
                    if (newValue && !Number.isNaN(newValue.getTime())) {
                      setBulkRollbackFilters((prev) => ({
                        ...prev,
                        date_from: gregorianFormat(newValue, 'yyyy-MM-dd'),
                      }));
                    } else {
                      setBulkRollbackFilters((prev) => ({ ...prev, date_from: undefined }));
                    }
                  }}
                  slotProps={{ textField: { size: 'small', fullWidth: true } }}
                />
              </LocalizedDateProvider>
            </Grid>
            <Grid item xs={12} sm={6}>
              <LocalizedDateProvider>
                <DatePicker
                  label={t('procurement.toDate') || 'To Date'}
                  value={bulkRollbackFilters.date_to ? new Date(`${bulkRollbackFilters.date_to}T00:00:00`) : null}
                  onChange={(newValue) => {
                    if (newValue && !Number.isNaN(newValue.getTime())) {
                      setBulkRollbackFilters((prev) => ({
                        ...prev,
                        date_to: gregorianFormat(newValue, 'yyyy-MM-dd'),
                      }));
                    } else {
                      setBulkRollbackFilters((prev) => ({ ...prev, date_to: undefined }));
                    }
                  }}
                  slotProps={{ textField: { size: 'small', fullWidth: true } }}
                />
              </LocalizedDateProvider>
            </Grid>
          </Grid>

          <Button
            variant="outlined"
            onClick={runBulkRollbackPreview}
            disabled={bulkRollbackLoading || !hasAnyRollbackChecklistFilterSelected}
            sx={{ mb: 2 }}
          >
            {bulkRollbackLoading
              ? (t('procurement.previewingRollback') || 'Previewing...')
              : (t('procurement.previewRollback') || 'Preview rollback')}
          </Button>

          {bulkRollbackPreview && (
            <Box>
              <Box sx={{ mb: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label={`${t('procurement.matchedItems') || 'Matched'}: ${bulkRollbackPreview.summary.matched_count}`} size="small" />
                <Chip label={`${t('procurement.rollbackableItems') || 'Rollbackable'}: ${bulkRollbackPreview.summary.rollbackable_count}`} size="small" color="success" />
                <Chip label={`${t('procurement.unsafeItems') || 'Unsafe'}: ${bulkRollbackPreview.summary.unsafe_count}`} size="small" color="warning" />
              </Box>

              {(bulkRollbackPreview.warnings || []).length > 0 && (
                <Alert severity="warning" sx={{ mb: 1 }}>
                  {(bulkRollbackPreview.warnings || []).slice(0, 4).join(' | ')}
                </Alert>
              )}

              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                {t('procurement.rollbackableSelection') || 'Rollbackable item selection'}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 0.75 }}>
                <Button size="small" variant="outlined" onClick={selectAllRollbackableItems}>
                  {t('procurement.selectAllItems') || 'Select all'}
                </Button>
                <Button size="small" variant="outlined" color="inherit" onClick={deselectAllRollbackableItems}>
                  {t('procurement.deselectAllItems') || 'Deselect all'}
                </Button>
              </Box>
              <Box sx={{ maxHeight: 180, overflowY: 'auto', border: `1px solid ${rivarTokens.line}`, borderRadius: rivarTokens.radiusSm, p: 1 }}>
                {(bulkRollbackPreview.rollbackable_items || []).map((item) => (
                  <FormControlLabel
                    key={item.project_item_id}
                    control={
                      <Checkbox
                        checked={bulkRollbackSelectedIds.includes(item.project_item_id)}
                        onChange={() => toggleRollbackSelection(item.project_item_id)}
                      />
                    }
                    label={`${item.item_code} · ${item.package_type_bucket} · ${item.coverage_state} · ${item.total_cost_irr ? `${Math.round(item.total_cost_irr).toLocaleString()} IRR` : (t('procurement.costUnavailable') || 'Cost unavailable')}`}
                  />
                ))}
              </Box>

              {(bulkRollbackPreview.unsafe_items || []).length > 0 && (
                <>
                  <Typography variant="body2" sx={{ fontWeight: 600, mt: 1.5, mb: 0.5 }}>
                    {t('procurement.unsafeItems') || 'Unsafe items'}
                  </Typography>
                  <Box sx={{ maxHeight: 140, overflowY: 'auto', border: `1px solid ${rivarTokens.line}`, borderRadius: rivarTokens.radiusSm, p: 1 }}>
                    {(bulkRollbackPreview.unsafe_items || []).slice(0, 12).map((item) => (
                      <Typography key={item.project_item_id} variant="caption" display="block" sx={{ color: rivarTokens.ink500, mb: 0.5 }}>
                        {item.item_code}: {(item.skip_reasons || []).map((r) => r.reason || r.code).join(' | ')}
                      </Typography>
                    ))}
                  </Box>
                </>
              )}

              <TextField
                label={t('procurement.rollbackNotes') || 'Rollback notes'}
                value={bulkRollbackNote}
                onChange={(e) => setBulkRollbackNote(e.target.value)}
                fullWidth
                multiline
                minRows={2}
                sx={{ mt: 1.5 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkRollbackOpen(false)} disabled={bulkRollbackExecuting}>
            {t('common.cancel') || 'Cancel'}
          </Button>
          <Button
            variant="contained"
            color="warning"
            onClick={executeBulkRollback}
            disabled={
              bulkRollbackExecuting ||
              bulkRollbackSelectedIds.length === 0 ||
              !hasAnyRollbackChecklistFilterSelected
            }
          >
            {bulkRollbackExecuting
              ? (t('procurement.rollbackExecuting') || 'Rolling back...')
              : (t('procurement.confirmRollback') || 'Confirm rollback')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Coverage Summary Modal */}
      {coverageModalOpen && selectedProjectIdForCoverage && (
        <CoverageSummaryModal
          open={coverageModalOpen}
          onClose={() => {
            setCoverageModalOpen(false);
            setSelectedProjectIdForCoverage(null);
            setSelectedProjectItemIdForCoverage(null);
          }}
          projectId={selectedProjectIdForCoverage}
          projectItemId={selectedProjectItemIdForCoverage || undefined}
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
              setSelectedProjectItemIdForCoverage(null);
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
            setEditingPackageId(null);
            setWizardInitialData(null);
            try {
              await calculateSummaryStats();
            } catch {
              // Best-effort: do not block package UX on summary refresh.
            }
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
