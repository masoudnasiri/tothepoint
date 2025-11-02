import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Autocomplete,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip,
  Rating,
  InputAdornment,
  Chip as MuiChip,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  Avatar,
  Link
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Description as DocumentIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  ExpandMore as ExpandMoreIcon,
  LocationOn as LocationIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Language as LanguageIcon,
  Schedule as ScheduleIcon,
  Star as StarIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Pending as PendingIcon,
  LinkedIn as LinkedInIcon,
  Telegram as TelegramIcon,
  WhatsApp as WhatsAppIcon,
  WeChat as WeChatIcon,
  AttachFile as AttachFileIcon,
  CloudUpload as CloudUploadIcon,
  FileDownload as FileDownloadIcon,
  Verified as VerifiedIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  AccountBalance as AccountBalanceIcon,
  Factory as FactoryIcon,
  LocalShipping as LocalShippingIcon,
  Payment as PaymentIcon,
  Public as PublicIcon,
  Group as GroupIcon,
  Work as WorkIcon,
  School as SchoolIcon,
  EmojiEvents as EmojiEventsIcon,
  Store as StoreIcon,
  Home as HomeIcon,
  Flag as FlagIcon,
  CalendarToday as CalendarTodayIcon,
  AccessTime as AccessTimeIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Precision as PrecisionIcon,
  Support as SupportIcon,
  Policy as PolicyIcon,
  Gavel as GavelIcon,
  Description as DescriptionIcon,
  Assignment as AssignmentIcon,
  Receipt as ReceiptIcon,
  Assessment as AssessmentIcon2,
  Folder as FolderIcon,
  InsertDriveFile as InsertDriveFileIcon,
  PictureAsPdf as PictureAsPdfIcon,
  Image as ImageIcon,
  VideoFile as VideoFileIcon,
  AudioFile as AudioFileIcon,
  Archive as ArchiveIcon,
  CloudDone as CloudDoneIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Help as HelpIcon,
  Close as CloseIcon,
  Save as SaveIcon,
  Cancel as CancelIcon2,
  Check as CheckIcon,
  AddCircle as AddCircleIcon,
  RemoveCircle as RemoveCircleIcon,
  Edit as EditIcon2,
  Delete as DeleteIcon2,
  MoreVert as MoreVertIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountCircleIcon,
  ExitToApp as ExitToAppIcon,
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Inventory as InventoryIcon,
  ShoppingCart as ShoppingCartIcon,
  TrendingUp as TrendingUpIcon2,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  ShowChart as ShowChartIcon,
  TableChart as TableChartIcon,
  Timeline as TimelineIcon2,
  DateRange as DateRangeIcon,
  Today as TodayIcon,
  Schedule as ScheduleIcon2,
  Event as EventIcon,
  EventNote as EventNoteIcon,
  EventAvailable as EventAvailableIcon,
  EventBusy as EventBusyIcon,
  EventSeat as EventSeatIcon,
  ConfirmationNumber as ConfirmationNumberIcon,
  LocalActivity as LocalActivityIcon,
  LocalAtm as LocalAtmIcon,
  LocalBar as LocalBarIcon,
  LocalCafe as LocalCafeIcon,
  LocalCarWash as LocalCarWashIcon,
  LocalConvenienceStore as LocalConvenienceStoreIcon,
  LocalDining as LocalDiningIcon,
  LocalDrink as LocalDrinkIcon,
  LocalFireDepartment as LocalFireDepartmentIcon,
  LocalFlorist as LocalFloristIcon,
  LocalGasStation as LocalGasStationIcon,
  LocalGroceryStore as LocalGroceryStoreIcon,
  LocalHospital as LocalHospitalIcon,
  LocalHotel as LocalHotelIcon,
  LocalLaundryService as LocalLaundryServiceIcon,
  LocalLibrary as LocalLibraryIcon,
  LocalMall as LocalMallIcon,
  LocalMovies as LocalMoviesIcon,
  LocalOffer as LocalOfferIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useTranslation } from 'react-i18next';
import { suppliersAPI } from '../services/api.ts';

interface Supplier {
  id: number;
  supplier_id: string;
  company_name: string;
  legal_entity_type?: string;
  registration_number?: string;
  tax_id?: string;
  established_year?: number;
  country?: string;
  city?: string;
  address?: string;
  website?: string;
  domain?: string;
  primary_email?: string;
  main_phone?: string;
  linkedin_url?: string;
  wechat_id?: string;
  telegram_id?: string;
  other_social_media?: string[];
  category?: string;
  industry?: string;
  product_service_lines?: string[];
  main_brands_represented?: string[];
  main_markets_regions?: string[];
  certifications?: string[];
  ownership_type?: string;
  annual_revenue_range?: string;
  number_of_employees?: string;
  warehouse_locations?: string[];
  key_clients_references?: string[];
  payment_terms?: string;
  currency_preference?: string;
  shipping_methods?: string[];
  incoterms?: string[];
  average_lead_time_days?: number;
  quality_assurance_process?: string;
  warranty_policy?: string;
  after_sales_policy?: string;
  delivery_accuracy_percent?: number;
  response_time_hours?: number;
  business_license_path?: string;
  tax_certificate_path?: string;
  iso_certificates_path?: string;
  financial_report_path?: string;
  supplier_evaluation_path?: string;
  compliance_status: string;
  last_review_date?: string;
  last_audit_date?: string;
  status: string;
  risk_level: string;
  internal_rating?: number;
  performance_metrics?: any;
  notes?: string;
  created_at: string;
  updated_at?: string;
  created_by_id?: number;
  last_updated_by_id?: number;
  contacts?: SupplierContact[];
  documents?: SupplierDocument[];
  // File upload fields for creation
  business_license_file?: File;
  tax_certificate_file?: File;
  iso_certificates_file?: File;
  financial_report_file?: File;
  supplier_evaluation_file?: File;
  additional_documents?: File[];
}

interface SupplierContact {
  id: number;
  contact_id: string;
  supplier_id: number;
  full_name: string;
  job_title?: string;
  role?: string;
  department?: string;
  email?: string;
  phone?: string;
  whatsapp_id?: string;
  telegram_id?: string;
  language_preference?: string;
  timezone?: string;
  working_hours?: string;
  is_primary_contact: boolean;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at?: string;
  created_by_id?: number;
  supplier?: {
    id: number;
    supplier_id: string;
    company_name: string;
  };
}

interface SupplierDocument {
  id: number;
  document_id: string;
  supplier_id: number;
  document_name: string;
  document_type: string;
  file_name: string;
  file_path: string;
  file_size?: number;
  mime_type?: string;
  description?: string;
  document_number?: string;
  issued_by?: string;
  issued_date?: string;
  expiry_date?: string;
  is_active: boolean;
  is_verified: boolean;
  notes?: string;
  created_at: string;
  updated_at?: string;
  created_by_id?: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`supplier-tabpanel-${index}`}
      aria-labelledby={`supplier-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SuppliersPage: React.FC = () => {
  const { t } = useTranslation();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [complianceFilter, setComplianceFilter] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');
  const [countryFilter, setCountryFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  // Main page tab state
  const [mainTabValue, setMainTabValue] = useState(0);

  // Contacts tab state
  const [contacts, setContacts] = useState<SupplierContact[]>([]);
  const [contactsLoading, setContactsLoading] = useState(false);
  const [contactSearchTerm, setContactSearchTerm] = useState('');
  const [contactSupplierFilter, setContactSupplierFilter] = useState('all');
  const [contactPage, setContactPage] = useState(1);
  const [contactTotalPages, setContactTotalPages] = useState(0);

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [contactDialogOpen, setContactDialogOpen] = useState(false);
  const [documentDialogOpen, setDocumentDialogOpen] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [selectedContact, setSelectedContact] = useState<SupplierContact | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<SupplierDocument | null>(null);

  // Form states
  const [supplierForm, setSupplierForm] = useState<Partial<Supplier>>({});
  const [contactForm, setContactForm] = useState<Partial<SupplierContact>>({});
  const [documentForm, setDocumentForm] = useState<Partial<SupplierDocument>>({});
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Tab states
  const [supplierTabValue, setSupplierTabValue] = useState(0);

  // Form validation
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Load suppliers
  const loadSuppliers = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page,
        size: 10,
        search: searchTerm || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        compliance_status: complianceFilter !== 'all' ? complianceFilter : undefined,
        risk_level: riskFilter !== 'all' ? riskFilter : undefined,
        country: countryFilter !== 'all' ? countryFilter : undefined,
      };

      const response = await suppliersAPI.list(params);
      setSuppliers(response.data.suppliers);
      setTotalPages(response.data.pages);
    } catch (err) {
      setError(t('suppliers.failedToLoadSuppliers'));
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm, statusFilter, complianceFilter, riskFilter, countryFilter, t]);

  // Load contacts
  const loadContacts = useCallback(async () => {
    try {
      setContactsLoading(true);
      const params = {
        page: contactPage,
        size: 10,
        search: contactSearchTerm || undefined,
        supplier_id: contactSupplierFilter !== 'all' ? parseInt(contactSupplierFilter) : undefined,
      };

      const response = await suppliersAPI.listAllContacts(params);
      setContacts(response.data.contacts);
      setContactTotalPages(response.data.pages);
    } catch (err) {
      setError(t('suppliers.failedToLoadContacts'));
    } finally {
      setContactsLoading(false);
    }
  }, [contactPage, contactSearchTerm, contactSupplierFilter, t]);

  useEffect(() => {
    loadSuppliers();
  }, [loadSuppliers]);

  useEffect(() => {
    if (mainTabValue === 1) { // Contacts tab
      loadContacts();
    }
  }, [loadContacts, mainTabValue]);

  // Handle supplier creation
  const handleCreateSupplier = async () => {
    try {
      setUploading(true);
      
      // First create the supplier without file fields and contacts
      const supplierData = { ...supplierForm };
      const fileFields = ['business_license_file', 'tax_certificate_file', 'iso_certificates_file', 'financial_report_file', 'supplier_evaluation_file', 'additional_documents'];
      
      // Remove file fields and contacts from supplier data
      fileFields.forEach(field => delete supplierData[field]);
      delete supplierData.contacts;
      
      const response = await suppliersAPI.create(supplierData);
      const newSupplier = response.data;
      
      // Upload documents if any
      const documentTypes = [
        { field: 'business_license_file', type: 'BUSINESS_LICENSE' },
        { field: 'tax_certificate_file', type: 'TAX_CERTIFICATE' },
        { field: 'iso_certificates_file', type: 'ISO_CERTIFICATE' },
        { field: 'financial_report_file', type: 'FINANCIAL_REPORT' },
        { field: 'supplier_evaluation_file', type: 'SUPPLIER_EVALUATION' }
      ];
      
      // Upload single documents
      for (const docType of documentTypes) {
        const file = supplierForm[docType.field as keyof typeof supplierForm] as File;
        if (file) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('document_type', docType.type);
          formData.append('title', docType.type.replace('_', ' '));
          
          try {
            console.log(`Uploading ${docType.type} for supplier ${newSupplier.id}`);
            await suppliersAPI.createDocument(newSupplier.id, formData);
            console.log(`Successfully uploaded ${docType.type}`);
          } catch (uploadError) {
            console.error(`Failed to upload ${docType.type}:`, uploadError);
            setError(`Failed to upload ${docType.type}: ${uploadError.message || 'Unknown error'}`);
          }
        }
      }
      
      // Upload additional documents
      const additionalFiles = supplierForm.additional_documents as File[];
      if (additionalFiles && additionalFiles.length > 0) {
        for (const file of additionalFiles) {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('document_type', 'OTHER');
          formData.append('title', file.name);
          
          try {
            console.log(`Uploading additional document ${file.name} for supplier ${newSupplier.id}`);
            await suppliersAPI.createDocument(newSupplier.id, formData);
            console.log(`Successfully uploaded additional document ${file.name}`);
          } catch (uploadError) {
            console.error(`Failed to upload additional document ${file.name}:`, uploadError);
            setError(`Failed to upload additional document ${file.name}: ${uploadError.message || 'Unknown error'}`);
          }
        }
      }
      
      setSuppliers([...suppliers, newSupplier]);
      setCreateDialogOpen(false);
      setSupplierForm({});
      setFormErrors({});
      // Show success message
    } catch (err) {
      setError(t('suppliers.failedToCreateSupplier'));
    } finally {
      setUploading(false);
    }
  };

  // Handle supplier update
  const handleUpdateSupplier = async () => {
    if (!selectedSupplier) return;

    try {
      setUploading(true);
      const response = await suppliersAPI.update(selectedSupplier.id, supplierForm);
      setSuppliers(suppliers.map(s => s.id === selectedSupplier.id ? response.data : s));
      setEditDialogOpen(false);
      setSupplierForm({});
      setFormErrors({});
      // Show success message
    } catch (err) {
      setError(t('suppliers.failedToUpdateSupplier'));
    } finally {
      setUploading(false);
    }
  };

  // Handle supplier deletion
  const handleDeleteSupplier = async () => {
    if (!selectedSupplier) return;

    try {
      await suppliersAPI.delete(selectedSupplier.id);
      setSuppliers(suppliers.filter(s => s.id !== selectedSupplier.id));
      setDeleteDialogOpen(false);
      setSelectedSupplier(null);
      // Show success message
    } catch (err) {
      setError(t('suppliers.failedToDeleteSupplier'));
    }
  };

  // Handle contact creation
  const handleCreateContact = async () => {
    // Validate required fields
    if (!contactForm.supplier_id) {
      setFormErrors({ supplier_id: t('suppliers.supplierRequired') });
      return;
    }
    if (!contactForm.full_name) {
      setFormErrors({ full_name: t('suppliers.fullNameRequired') });
      return;
    }

    try {
      setUploading(true);
      const response = await suppliersAPI.createContact(contactForm.supplier_id, contactForm);
      
      // Refresh contacts list
      await loadContacts();
      
      setContactDialogOpen(false);
      setContactForm({});
      setFormErrors({});
      // Show success message
    } catch (err) {
      setError(t('suppliers.failedToCreateContact'));
    } finally {
      setUploading(false);
    }
  };

  // Handle document upload
  const handleUploadDocument = async () => {
    if (!selectedSupplier || !documentFile) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', documentFile);
      formData.append('document_name', documentForm.document_name || '');
      formData.append('document_type', documentForm.document_type || '');
      formData.append('description', documentForm.description || '');
      formData.append('document_number', documentForm.document_number || '');
      formData.append('issued_by', documentForm.issued_by || '');
      formData.append('issued_date', documentForm.issued_date || '');
      formData.append('expiry_date', documentForm.expiry_date || '');

      const response = await suppliersAPI.uploadDocument(selectedSupplier.id, formData);
      // Update supplier with new document
      const updatedSupplier = { ...selectedSupplier };
      updatedSupplier.documents = [...(updatedSupplier.documents || []), response.data];
      setSuppliers(suppliers.map(s => s.id === selectedSupplier.id ? updatedSupplier : s));
      setDocumentDialogOpen(false);
      setDocumentForm({});
      setDocumentFile(null);
      setFormErrors({});
      // Show success message
    } catch (err) {
      setError(t('suppliers.failedToUploadDocument'));
    } finally {
      setUploading(false);
    }
  };

  // Open dialogs
  const openCreateDialog = () => {
    setSupplierForm({
      status: 'ACTIVE',
      compliance_status: 'PENDING',
      risk_level: 'MEDIUM',
      currency_preference: 'IRR',
      language_preference: 'en'
    });
    setSupplierTabValue(0);
    setCreateDialogOpen(true);
  };

  const openEditDialog = (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    setSupplierForm(supplier);
    setSupplierTabValue(0);
    setEditDialogOpen(true);
  };

  const openViewDialog = (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    setViewDialogOpen(true);
  };

  const openDeleteDialog = (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    setDeleteDialogOpen(true);
  };

  const openContactDialog = (supplier: Supplier, contact?: SupplierContact) => {
    setSelectedSupplier(supplier);
    if (contact) {
      setSelectedContact(contact);
      setContactForm(contact);
    } else {
      setSelectedContact(null);
      setContactForm({
        is_primary_contact: false,
        is_active: true,
        language_preference: 'en'
      });
    }
    setContactTabValue(0);
    setContactDialogOpen(true);
  };

  const openDocumentDialog = (supplier: Supplier, document?: SupplierDocument) => {
    setSelectedSupplier(supplier);
    if (document) {
      setSelectedDocument(document);
      setDocumentForm(document);
    } else {
      setSelectedDocument(null);
      setDocumentForm({
        is_active: true,
        is_verified: false
      });
    }
    setDocumentTabValue(0);
    setDocumentDialogOpen(true);
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'success';
      case 'INACTIVE': return 'default';
      case 'SUSPENDED': return 'warning';
      case 'PENDING_APPROVAL': return 'info';
      default: return 'default';
    }
  };

  // Get compliance color
  const getComplianceColor = (status: string) => {
    switch (status) {
      case 'APPROVED': return 'success';
      case 'PENDING': return 'warning';
      case 'REJECTED': return 'error';
      case 'UNDER_REVIEW': return 'info';
      default: return 'default';
    }
  };

  // Get risk color
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'success';
      case 'MEDIUM': return 'warning';
      case 'HIGH': return 'error';
      default: return 'default';
    }
  };

  // Render supplier creation/edit dialog
  const renderSupplierDialog = () => {
    const isEdit = editDialogOpen;
    const title = isEdit ? t('suppliers.editSupplier') : t('suppliers.createSupplier');

    return (
      <Dialog
        open={createDialogOpen || editDialogOpen}
        onClose={(event, reason) => {
          // Only close on backdrop click or escape key, not on content clicks
          if (reason === 'backdropClick' || reason === 'escapeKeyDown') {
            setCreateDialogOpen(false);
            setEditDialogOpen(false);
            setSupplierForm({});
            setFormErrors({});
          }
        }}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>{title}</DialogTitle>
        <DialogContent onClick={(e) => e.stopPropagation()}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={supplierTabValue} onChange={(e, v) => setSupplierTabValue(v)}>
              <Tab label={t('suppliers.generalInfo')} />
              <Tab label={t('suppliers.businessInfo')} />
              <Tab label={t('suppliers.operationalInfo')} />
              <Tab label={t('suppliers.documentCompliance')} />
              <Tab label={t('suppliers.internalMeta')} />
            </Tabs>
          </Box>

          {/* General Information Tab */}
          <TabPanel value={supplierTabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={t('suppliers.supplierId')}
                  value={supplierForm.supplier_id || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, supplier_id: e.target.value })}
                  helperText={t('suppliers.supplierIdHelper')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  label={t('suppliers.companyName')}
                  value={supplierForm.company_name || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, company_name: e.target.value })}
                  error={!!formErrors.company_name}
                  helperText={formErrors.company_name}
                  autoComplete="off"
                  name="company_name"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectLegalEntityType')}</InputLabel>
                  <Select
                    value={supplierForm.legal_entity_type || ''}
                    onChange={(e) => setSupplierForm({ ...supplierForm, legal_entity_type: e.target.value })}
                  >
                    <MenuItem value="Corporation">{t('suppliers.corporation')}</MenuItem>
                    <MenuItem value="LLC">{t('suppliers.llc')}</MenuItem>
                    <MenuItem value="Ltd.">{t('suppliers.ltd')}</MenuItem>
                    <MenuItem value="AG">{t('suppliers.ag')}</MenuItem>
                    <MenuItem value="Partnership">{t('suppliers.partnership')}</MenuItem>
                    <MenuItem value="Joint Venture">{t('suppliers.jointVenture')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={t('suppliers.registrationNumber')}
                  value={supplierForm.registration_number || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, registration_number: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={t('suppliers.taxId')}
                  value={supplierForm.tax_id || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, tax_id: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('suppliers.establishedYear')}
                  value={supplierForm.established_year || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, established_year: parseInt(e.target.value) })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={t('suppliers.country')}
                  value={supplierForm.country || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, country: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={t('suppliers.city')}
                  value={supplierForm.city || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, city: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label={t('suppliers.address')}
                  value={supplierForm.address || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, address: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={t('suppliers.website')}
                  value={supplierForm.website || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, website: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={t('suppliers.domain')}
                  value={supplierForm.domain || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, domain: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="email"
                  label={t('suppliers.primaryEmail')}
                  value={supplierForm.primary_email || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, primary_email: e.target.value })}
                  autoComplete="off"
                  name="primary_email"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={t('suppliers.mainPhone')}
                  value={supplierForm.main_phone || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, main_phone: e.target.value })}
                />
              </Grid>
            </Grid>
          </TabPanel>

          {/* Business Information Tab */}
          <TabPanel value={supplierTabValue} index={1}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectCategory')}</InputLabel>
                  <Select
                    value={supplierForm.category || ''}
                    onChange={(e) => setSupplierForm({ ...supplierForm, category: e.target.value })}
                  >
                    <MenuItem value="Telecom">{t('suppliers.telecom')}</MenuItem>
                    <MenuItem value="Oil & Gas">{t('suppliers.oilGas')}</MenuItem>
                    <MenuItem value="IT Equipment">{t('suppliers.itEquipment')}</MenuItem>
                    <MenuItem value="Electronics">{t('suppliers.electronics')}</MenuItem>
                    <MenuItem value="Manufacturing">{t('suppliers.manufacturing')}</MenuItem>
                    <MenuItem value="Trading">{t('suppliers.trading')}</MenuItem>
                    <MenuItem value="Precision Components">{t('suppliers.precisionComponents')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectIndustry')}</InputLabel>
                  <Select
                    value={supplierForm.industry || ''}
                    onChange={(e) => setSupplierForm({ ...supplierForm, industry: e.target.value })}
                  >
                    <MenuItem value="Technology">{t('suppliers.technology')}</MenuItem>
                    <MenuItem value="Manufacturing">{t('suppliers.manufacturing')}</MenuItem>
                    <MenuItem value="Industrial">{t('suppliers.industrial')}</MenuItem>
                    <MenuItem value="Commerce">{t('suppliers.commerce')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={supplierForm.product_service_lines || []}
                  onChange={(event, newValue) => {
                    setSupplierForm({ ...supplierForm, product_service_lines: newValue });
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <MuiChip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('suppliers.productServiceLines')}
                      placeholder={t('suppliers.addItem')}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={supplierForm.main_brands_represented || []}
                  onChange={(event, newValue) => {
                    setSupplierForm({ ...supplierForm, main_brands_represented: newValue });
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <MuiChip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('suppliers.mainBrandsRepresented')}
                      placeholder={t('suppliers.addItem')}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={supplierForm.main_markets_regions || []}
                  onChange={(event, newValue) => {
                    setSupplierForm({ ...supplierForm, main_markets_regions: newValue });
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <MuiChip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('suppliers.mainMarketsRegions')}
                      placeholder={t('suppliers.addItem')}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={supplierForm.certifications || []}
                  onChange={(event, newValue) => {
                    setSupplierForm({ ...supplierForm, certifications: newValue });
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <MuiChip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('suppliers.certifications')}
                      placeholder={t('suppliers.addItem')}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectOwnershipType')}</InputLabel>
                  <Select
                    value={supplierForm.ownership_type || ''}
                    onChange={(e) => setSupplierForm({ ...supplierForm, ownership_type: e.target.value })}
                  >
                    <MenuItem value="Private">{t('suppliers.private')}</MenuItem>
                    <MenuItem value="State-owned">{t('suppliers.stateOwned')}</MenuItem>
                    <MenuItem value="Distributor">{t('suppliers.distributor')}</MenuItem>
                    <MenuItem value="Agent">{t('suppliers.agent')}</MenuItem>
                    <MenuItem value="Public">{t('suppliers.public')}</MenuItem>
                    <MenuItem value="Government">{t('suppliers.government')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectRevenueRange')}</InputLabel>
                  <Select
                    value={supplierForm.annual_revenue_range || ''}
                    onChange={(e) => setSupplierForm({ ...supplierForm, annual_revenue_range: e.target.value })}
                  >
                    <MenuItem value="< $1M">{t('suppliers.lessThan1M')}</MenuItem>
                    <MenuItem value="$1M - $10M">{t('suppliers.oneToTenM')}</MenuItem>
                    <MenuItem value="$10M - $100M">{t('suppliers.tenToHundredM')}</MenuItem>
                    <MenuItem value="> $100M">{t('suppliers.moreThanHundredM')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectEmployeeRange')}</InputLabel>
                  <Select
                    value={supplierForm.number_of_employees || ''}
                    onChange={(e) => setSupplierForm({ ...supplierForm, number_of_employees: e.target.value })}
                  >
                    <MenuItem value="< 10">{t('suppliers.lessThan10')}</MenuItem>
                    <MenuItem value="10 - 50">{t('suppliers.tenToFifty')}</MenuItem>
                    <MenuItem value="50 - 200">{t('suppliers.fiftyToTwoHundred')}</MenuItem>
                    <MenuItem value="> 200">{t('suppliers.moreThanTwoHundred')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Operational Information Tab */}
          <TabPanel value={supplierTabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={supplierForm.warehouse_locations || []}
                  onChange={(event, newValue) => {
                    setSupplierForm({ ...supplierForm, warehouse_locations: newValue });
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <MuiChip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('suppliers.warehouseLocations')}
                      placeholder={t('suppliers.addItem')}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={supplierForm.key_clients_references || []}
                  onChange={(event, newValue) => {
                    setSupplierForm({ ...supplierForm, key_clients_references: newValue });
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <MuiChip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('suppliers.keyClientsReferences')}
                      placeholder={t('suppliers.addItem')}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectPaymentTerms')}</InputLabel>
                  <Select
                    value={supplierForm.payment_terms || ''}
                    onChange={(e) => setSupplierForm({ ...supplierForm, payment_terms: e.target.value })}
                  >
                    <MenuItem value="T/T">{t('suppliers.tt')}</MenuItem>
                    <MenuItem value="LC">{t('suppliers.lc')}</MenuItem>
                    <MenuItem value="Net 30">{t('suppliers.net30')}</MenuItem>
                    <MenuItem value="Net 60">{t('suppliers.net60')}</MenuItem>
                    <MenuItem value="Cash">{t('suppliers.cash')}</MenuItem>
                    <MenuItem value="Installments">{t('suppliers.installments')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectCurrency')}</InputLabel>
                  <Select
                    value={supplierForm.currency_preference || 'IRR'}
                    onChange={(e) => setSupplierForm({ ...supplierForm, currency_preference: e.target.value })}
                  >
                    <MenuItem value="USD">{t('suppliers.usd')}</MenuItem>
                    <MenuItem value="EUR">{t('suppliers.eur')}</MenuItem>
                    <MenuItem value="IRR">{t('suppliers.irr')}</MenuItem>
                    <MenuItem value="CNY">{t('suppliers.cny')}</MenuItem>
                    <MenuItem value="AED">{t('suppliers.aed')}</MenuItem>
                    <MenuItem value="CHF">{t('suppliers.chf')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={supplierForm.shipping_methods || []}
                  onChange={(event, newValue) => {
                    setSupplierForm({ ...supplierForm, shipping_methods: newValue });
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <MuiChip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('suppliers.shippingMethods')}
                      placeholder={t('suppliers.addItem')}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12}>
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={supplierForm.incoterms || []}
                  onChange={(event, newValue) => {
                    setSupplierForm({ ...supplierForm, incoterms: newValue });
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <MuiChip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('suppliers.incoterms')}
                      placeholder={t('suppliers.addItem')}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('suppliers.averageLeadTimeDays')}
                  value={supplierForm.average_lead_time_days || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, average_lead_time_days: parseInt(e.target.value) })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('suppliers.deliveryAccuracyPercent')}
                  value={supplierForm.delivery_accuracy_percent || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, delivery_accuracy_percent: parseFloat(e.target.value) })}
                  InputProps={{
                    endAdornment: <InputAdornment position="end">%</InputAdornment>,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label={t('suppliers.responseTimeHours')}
                  value={supplierForm.response_time_hours || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, response_time_hours: parseInt(e.target.value) })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label={t('suppliers.qualityAssuranceProcess')}
                  value={supplierForm.quality_assurance_process || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, quality_assurance_process: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label={t('suppliers.warrantyPolicy')}
                  value={supplierForm.warranty_policy || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, warranty_policy: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label={t('suppliers.afterSalesPolicy')}
                  value={supplierForm.after_sales_policy || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, after_sales_policy: e.target.value })}
                />
              </Grid>
            </Grid>
          </TabPanel>

          {/* Document & Compliance Tab */}
          <TabPanel value={supplierTabValue} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectComplianceStatus')}</InputLabel>
                  <Select
                    value={supplierForm.compliance_status || 'PENDING'}
                    onChange={(e) => setSupplierForm({ ...supplierForm, compliance_status: e.target.value })}
                  >
                    <MenuItem value="APPROVED">{t('suppliers.approved')}</MenuItem>
                    <MenuItem value="PENDING">{t('suppliers.pending')}</MenuItem>
                    <MenuItem value="REJECTED">{t('suppliers.rejected')}</MenuItem>
                    <MenuItem value="UNDER_REVIEW">{t('suppliers.underReview')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                  <DatePicker
                    label={t('suppliers.lastReviewDate')}
                    value={supplierForm.last_review_date ? new Date(supplierForm.last_review_date) : null}
                    onChange={(date) => setSupplierForm({ ...supplierForm, last_review_date: date?.toISOString().split('T')[0] })}
                    textField={(params) => <TextField {...params} fullWidth />}
                  />
                </LocalizationProvider>
              </Grid>
              <Grid item xs={12} sm={6}>
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                  <DatePicker
                    label={t('suppliers.lastAuditDate')}
                    value={supplierForm.last_audit_date ? new Date(supplierForm.last_audit_date) : null}
                    onChange={(date) => setSupplierForm({ ...supplierForm, last_audit_date: date?.toISOString().split('T')[0] })}
                    textField={(params) => <TextField {...params} fullWidth />}
                  />
                </LocalizationProvider>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  {t('suppliers.documentUpload')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('suppliers.documentUploadDescription')}
                </Typography>
              </Grid>

              {/* Business License */}
              <Grid item xs={12} sm={6}>
                <Box sx={{ border: '1px dashed #ccc', p: 2, borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('suppliers.businessLicense')}
                  </Typography>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setSupplierForm({ ...supplierForm, business_license_file: file });
                      }
                    }}
                    style={{ width: '100%', marginBottom: 8 }}
                  />
                  {supplierForm.business_license_file && (
                    <Typography variant="caption" color="success.main">
                      ✓ {supplierForm.business_license_file.name}
                    </Typography>
                  )}
                </Box>
              </Grid>

              {/* Tax Certificate */}
              <Grid item xs={12} sm={6}>
                <Box sx={{ border: '1px dashed #ccc', p: 2, borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('suppliers.taxCertificate')}
                  </Typography>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setSupplierForm({ ...supplierForm, tax_certificate_file: file });
                      }
                    }}
                    style={{ width: '100%', marginBottom: 8 }}
                  />
                  {supplierForm.tax_certificate_file && (
                    <Typography variant="caption" color="success.main">
                      ✓ {supplierForm.tax_certificate_file.name}
                    </Typography>
                  )}
                </Box>
              </Grid>

              {/* ISO Certificates */}
              <Grid item xs={12} sm={6}>
                <Box sx={{ border: '1px dashed #ccc', p: 2, borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('suppliers.isoCertificates')}
                  </Typography>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setSupplierForm({ ...supplierForm, iso_certificates_file: file });
                      }
                    }}
                    style={{ width: '100%', marginBottom: 8 }}
                  />
                  {supplierForm.iso_certificates_file && (
                    <Typography variant="caption" color="success.main">
                      ✓ {supplierForm.iso_certificates_file.name}
                    </Typography>
                  )}
                </Box>
              </Grid>

              {/* Financial Report */}
              <Grid item xs={12} sm={6}>
                <Box sx={{ border: '1px dashed #ccc', p: 2, borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('suppliers.financialReport')}
                  </Typography>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setSupplierForm({ ...supplierForm, financial_report_file: file });
                      }
                    }}
                    style={{ width: '100%', marginBottom: 8 }}
                  />
                  {supplierForm.financial_report_file && (
                    <Typography variant="caption" color="success.main">
                      ✓ {supplierForm.financial_report_file.name}
                    </Typography>
                  )}
                </Box>
              </Grid>

              {/* Supplier Evaluation */}
              <Grid item xs={12} sm={6}>
                <Box sx={{ border: '1px dashed #ccc', p: 2, borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('suppliers.supplierEvaluation')}
                  </Typography>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setSupplierForm({ ...supplierForm, supplier_evaluation_file: file });
                      }
                    }}
                    style={{ width: '100%', marginBottom: 8 }}
                  />
                  {supplierForm.supplier_evaluation_file && (
                    <Typography variant="caption" color="success.main">
                      ✓ {supplierForm.supplier_evaluation_file.name}
                    </Typography>
                  )}
                </Box>
              </Grid>

              {/* Additional Documents */}
              <Grid item xs={12} sm={6}>
                <Box sx={{ border: '1px dashed #ccc', p: 2, borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('suppliers.additionalDocuments')}
                  </Typography>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    multiple
                    onChange={(e) => {
                      const files = Array.from(e.target.files || []);
                      if (files.length > 0) {
                        setSupplierForm({ ...supplierForm, additional_documents: files });
                      }
                    }}
                    style={{ width: '100%', marginBottom: 8 }}
                  />
                  {supplierForm.additional_documents && supplierForm.additional_documents.length > 0 && (
                    <Box>
                      {supplierForm.additional_documents.map((file, index) => (
                        <Typography key={index} variant="caption" color="success.main" display="block">
                          ✓ {file.name}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Internal & Meta Tab */}
          <TabPanel value={supplierTabValue} index={4}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectStatus')}</InputLabel>
                  <Select
                    value={supplierForm.status || 'ACTIVE'}
                    onChange={(e) => setSupplierForm({ ...supplierForm, status: e.target.value })}
                  >
                    <MenuItem value="ACTIVE">{t('suppliers.active')}</MenuItem>
                    <MenuItem value="INACTIVE">{t('suppliers.inactive')}</MenuItem>
                    <MenuItem value="SUSPENDED">{t('suppliers.suspended')}</MenuItem>
                    <MenuItem value="PENDING_APPROVAL">{t('suppliers.pendingApproval')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.selectRiskLevel')}</InputLabel>
                  <Select
                    value={supplierForm.risk_level || 'MEDIUM'}
                    onChange={(e) => setSupplierForm({ ...supplierForm, risk_level: e.target.value })}
                  >
                    <MenuItem value="LOW">{t('suppliers.lowRisk')}</MenuItem>
                    <MenuItem value="MEDIUM">{t('suppliers.mediumRisk')}</MenuItem>
                    <MenuItem value="HIGH">{t('suppliers.highRisk')}</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Box>
                  <Typography component="legend">{t('suppliers.internalRating')}</Typography>
                  <Rating
                    value={Number(supplierForm.internal_rating) || 0}
                    onChange={(event, newValue) => {
                      setSupplierForm({ ...supplierForm, internal_rating: newValue || 0 });
                    }}
                    precision={0.1}
                    size="large"
                  />
                </Box>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label={t('suppliers.notes')}
                  value={supplierForm.notes || ''}
                  onChange={(e) => setSupplierForm({ ...supplierForm, notes: e.target.value })}
                />
              </Grid>
            </Grid>
          </TabPanel>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateDialogOpen(false);
            setEditDialogOpen(false);
            setSupplierForm({});
            setFormErrors({});
          }}>
            {t('suppliers.cancel')}
          </Button>
          <Button
            onClick={isEdit ? handleUpdateSupplier : handleCreateSupplier}
            variant="contained"
            disabled={uploading}
            startIcon={uploading ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            {uploading ? t('suppliers.uploading') : (isEdit ? t('suppliers.update') : t('suppliers.create'))}
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  // Render contact dialog
  const renderContactDialog = () => {
    const isEdit = !!selectedContact;
    const title = isEdit ? t('suppliers.editContact') : t('suppliers.addContact');

    return (
      <Dialog
        open={contactDialogOpen}
        onClose={() => {
          setContactDialogOpen(false);
          setContactForm({});
          setFormErrors({});
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{title}</DialogTitle>
        <DialogContent>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>{t('suppliers.selectSupplier')}</InputLabel>
                <Select
                  value={contactForm.supplier_id || ''}
                  onChange={(e) => setContactForm({ ...contactForm, supplier_id: e.target.value })}
                  error={!!formErrors.supplier_id}
                >
                  {suppliers.map((supplier) => (
                    <MenuItem key={supplier.id} value={supplier.id}>
                      {supplier.company_name} ({supplier.supplier_id})
                    </MenuItem>
                  ))}
                </Select>
                {formErrors.supplier_id && (
                  <Typography variant="caption" color="error">
                    {formErrors.supplier_id}
                  </Typography>
                )}
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label={t('suppliers.fullName')}
                value={contactForm.full_name || ''}
                onChange={(e) => setContactForm({ ...contactForm, full_name: e.target.value })}
                error={!!formErrors.full_name}
                helperText={formErrors.full_name}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('suppliers.jobTitle')}
                value={contactForm.job_title || ''}
                onChange={(e) => setContactForm({ ...contactForm, job_title: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('suppliers.role')}
                value={contactForm.role || ''}
                onChange={(e) => setContactForm({ ...contactForm, role: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>{t('suppliers.selectDepartment')}</InputLabel>
                <Select
                  value={contactForm.department || ''}
                  onChange={(e) => setContactForm({ ...contactForm, department: e.target.value })}
                >
                  <MenuItem value="Sales">{t('suppliers.sales')}</MenuItem>
                  <MenuItem value="Technical">{t('suppliers.technical')}</MenuItem>
                  <MenuItem value="Finance">{t('suppliers.finance')}</MenuItem>
                  <MenuItem value="Procurement">{t('suppliers.procurement')}</MenuItem>
                  <MenuItem value="Business Development">{t('suppliers.businessDevelopment')}</MenuItem>
                  <MenuItem value="Quality">{t('suppliers.quality')}</MenuItem>
                  <MenuItem value="Marketing">{t('suppliers.marketing')}</MenuItem>
                  <MenuItem value="HR">{t('suppliers.hr')}</MenuItem>
                  <MenuItem value="Operations">{t('suppliers.operations')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="email"
                label={t('suppliers.email')}
                value={contactForm.email || ''}
                onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('suppliers.phone')}
                value={contactForm.phone || ''}
                onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('suppliers.whatsappId')}
                value={contactForm.whatsapp_id || ''}
                onChange={(e) => setContactForm({ ...contactForm, whatsapp_id: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('suppliers.telegramId')}
                value={contactForm.telegram_id || ''}
                onChange={(e) => setContactForm({ ...contactForm, telegram_id: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>{t('suppliers.selectLanguage')}</InputLabel>
                <Select
                  value={contactForm.language_preference || 'en'}
                  onChange={(e) => setContactForm({ ...contactForm, language_preference: e.target.value })}
                >
                  <MenuItem value="en">{t('suppliers.english')}</MenuItem>
                  <MenuItem value="fa">{t('suppliers.persian')}</MenuItem>
                  <MenuItem value="ar">{t('suppliers.arabic')}</MenuItem>
                  <MenuItem value="fr">{t('suppliers.french')}</MenuItem>
                  <MenuItem value="de">{t('suppliers.german')}</MenuItem>
                  <MenuItem value="es">{t('suppliers.spanish')}</MenuItem>
                  <MenuItem value="it">{t('suppliers.italian')}</MenuItem>
                  <MenuItem value="pt">{t('suppliers.portuguese')}</MenuItem>
                  <MenuItem value="ru">{t('suppliers.russian')}</MenuItem>
                  <MenuItem value="zh">{t('suppliers.chinese')}</MenuItem>
                  <MenuItem value="ja">{t('suppliers.japanese')}</MenuItem>
                  <MenuItem value="ko">{t('suppliers.korean')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>{t('suppliers.selectTimezone')}</InputLabel>
                <Select
                  value={contactForm.timezone || ''}
                  onChange={(e) => setContactForm({ ...contactForm, timezone: e.target.value })}
                >
                  <MenuItem value="EST">{t('suppliers.est')}</MenuItem>
                  <MenuItem value="CET">{t('suppliers.cet')}</MenuItem>
                  <MenuItem value="CST">{t('suppliers.cst')}</MenuItem>
                  <MenuItem value="GST">{t('suppliers.gst')}</MenuItem>
                  <MenuItem value="PST">{t('suppliers.pst')}</MenuItem>
                  <MenuItem value="JST">{t('suppliers.jst')}</MenuItem>
                  <MenuItem value="AEST">{t('suppliers.aest')}</MenuItem>
                  <MenuItem value="UTC">{t('suppliers.utc')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('suppliers.workingHours')}
                value={contactForm.working_hours || ''}
                onChange={(e) => setContactForm({ ...contactForm, working_hours: e.target.value })}
                placeholder="9:00-17:00 UTC+3"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={contactForm.is_primary_contact || false}
                    onChange={(e) => setContactForm({ ...contactForm, is_primary_contact: e.target.checked })}
                  />
                }
                label={t('suppliers.isPrimaryContact')}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label={t('suppliers.contactNotes')}
                value={contactForm.notes || ''}
                onChange={(e) => setContactForm({ ...contactForm, notes: e.target.value })}
                placeholder={t('suppliers.contactNotesPlaceholder')}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setContactDialogOpen(false);
            setContactForm({});
            setFormErrors({});
          }}>
            {t('suppliers.cancel')}
          </Button>
          <Button
            onClick={handleCreateContact}
            variant="contained"
            disabled={uploading}
            startIcon={uploading ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            {uploading ? t('suppliers.uploading') : (isEdit ? t('suppliers.update') : t('suppliers.create'))}
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  // Render document dialog
  const renderDocumentDialog = () => {
    const isEdit = !!selectedDocument;
    const title = isEdit ? t('suppliers.editDocument') : t('suppliers.uploadDocument');

    return (
      <Dialog
        open={documentDialogOpen}
        onClose={() => {
          setDocumentDialogOpen(false);
          setDocumentForm({});
          setDocumentFile(null);
          setFormErrors({});
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{title}</DialogTitle>
        <DialogContent>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label={t('suppliers.documentName')}
                value={documentForm.document_name || ''}
                onChange={(e) => setDocumentForm({ ...documentForm, document_name: e.target.value })}
                error={!!formErrors.document_name}
                helperText={formErrors.document_name}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>{t('suppliers.selectDocumentType')}</InputLabel>
                <Select
                  value={documentForm.document_type || ''}
                  onChange={(e) => setDocumentForm({ ...documentForm, document_type: e.target.value })}
                  error={!!formErrors.document_type}
                >
                  <MenuItem value="Business License">{t('suppliers.businessLicense')}</MenuItem>
                  <MenuItem value="Tax Certificate">{t('suppliers.taxCertificate')}</MenuItem>
                  <MenuItem value="ISO Certificate">{t('suppliers.isoCertificate')}</MenuItem>
                  <MenuItem value="Financial Report">{t('suppliers.financialReport')}</MenuItem>
                  <MenuItem value="Supplier Evaluation">{t('suppliers.supplierEvaluation')}</MenuItem>
                  <MenuItem value="Other">{t('suppliers.otherDocument')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('suppliers.documentNumber')}
                value={documentForm.document_number || ''}
                onChange={(e) => setDocumentForm({ ...documentForm, document_number: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label={t('suppliers.issuedBy')}
                value={documentForm.issued_by || ''}
                onChange={(e) => setDocumentForm({ ...documentForm, issued_by: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label={t('suppliers.issuedDate')}
                  value={documentForm.issued_date ? new Date(documentForm.issued_date) : null}
                  onChange={(date) => setDocumentForm({ ...documentForm, issued_date: date?.toISOString().split('T')[0] })}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </LocalizationProvider>
            </Grid>
            <Grid item xs={12} sm={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label={t('suppliers.expiryDate')}
                  value={documentForm.expiry_date ? new Date(documentForm.expiry_date) : null}
                  onChange={(date) => setDocumentForm({ ...documentForm, expiry_date: date?.toISOString().split('T')[0] })}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </LocalizationProvider>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label={t('suppliers.description')}
                value={documentForm.description || ''}
                onChange={(e) => setDocumentForm({ ...documentForm, description: e.target.value })}
              />
            </Grid>
            {!isEdit && (
              <Grid item xs={12}>
                <Box
                  sx={{
                    border: '2px dashed #ccc',
                    borderRadius: 2,
                    p: 3,
                    textAlign: 'center',
                    cursor: 'pointer',
                    '&:hover': {
                      borderColor: 'primary.main',
                      backgroundColor: 'action.hover',
                    },
                  }}
                  onClick={() => document.getElementById('file-upload')?.click()}
                >
                  <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    {documentFile ? documentFile.name : t('suppliers.selectFile')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('suppliers.selectFile')}
                  </Typography>
                  <input
                    id="file-upload"
                    type="file"
                    hidden
                    onChange={(e) => setDocumentFile(e.target.files?.[0] || null)}
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  />
                </Box>
              </Grid>
            )}
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={documentForm.is_verified || false}
                    onChange={(e) => setDocumentForm({ ...documentForm, is_verified: e.target.checked })}
                  />
                }
                label={t('suppliers.isVerified')}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label={t('suppliers.notes')}
                value={documentForm.notes || ''}
                onChange={(e) => setDocumentForm({ ...documentForm, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setDocumentDialogOpen(false);
            setDocumentForm({});
            setDocumentFile(null);
            setFormErrors({});
          }}>
            {t('suppliers.cancel')}
          </Button>
          <Button
            onClick={handleUploadDocument}
            variant="contained"
            disabled={uploading || (!isEdit && !documentFile)}
            startIcon={uploading ? <CircularProgress size={20} /> : <UploadIcon />}
          >
            {uploading ? t('suppliers.uploading') : (isEdit ? t('suppliers.update') : t('suppliers.uploadDocument'))}
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  // Render supplier view dialog
  const renderViewDialog = () => {
    if (!selectedSupplier) return null;

    return (
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <BusinessIcon />
            <Typography variant="h6">{selectedSupplier.company_name}</Typography>
            <Chip
              label={t(`suppliers.${selectedSupplier.status.toLowerCase()}`)}
              color={getStatusColor(selectedSupplier.status) as any}
              size="small"
            />
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={supplierTabValue} onChange={(e, v) => setSupplierTabValue(v)}>
              <Tab label={t('suppliers.overview')} />
              <Tab label={t('suppliers.contacts')} />
              <Tab label={t('suppliers.documents')} />
            </Tabs>
          </Box>

          {/* Overview Tab */}
          <TabPanel value={supplierTabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title={t('suppliers.basicInformation')} />
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.supplierId')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.supplier_id}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.legalEntityType')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.legal_entity_type || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.registrationNumber')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.registration_number || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.taxId')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.tax_id || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.establishedYear')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.established_year || '-'}</Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title={t('suppliers.location')} />
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.country')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.country || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.city')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.city || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.address')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.address || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.website')}
                        </Typography>
                        {selectedSupplier.website ? (
                          <Link href={selectedSupplier.website} target="_blank" rel="noopener">
                            {selectedSupplier.website}
                          </Link>
                        ) : (
                          <Typography variant="body1">-</Typography>
                        )}
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title={t('suppliers.businessInformation')} />
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.category')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.category || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.industry')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.industry || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.ownershipType')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.ownership_type || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.annualRevenueRange')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.annual_revenue_range || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.numberOfEmployees')}
                        </Typography>
                        <Typography variant="body1">{selectedSupplier.number_of_employees || '-'}</Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title={t('suppliers.statusAndRatings')} />
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.status')}
                        </Typography>
                        <Chip
                          label={t(`suppliers.${selectedSupplier.status.toLowerCase()}`)}
                          color={getStatusColor(selectedSupplier.status) as any}
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.complianceStatus')}
                        </Typography>
                        <Chip
                          label={t(`suppliers.${selectedSupplier.compliance_status.toLowerCase()}`)}
                          color={getComplianceColor(selectedSupplier.compliance_status) as any}
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.riskLevel')}
                        </Typography>
                        <Chip
                          label={t(`suppliers.${selectedSupplier.risk_level.toLowerCase()}Risk`)}
                          color={getRiskColor(selectedSupplier.risk_level) as any}
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                          {t('suppliers.internalRating')}
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Rating value={Number(selectedSupplier.internal_rating) || 0} readOnly precision={0.1} />
                          <Typography variant="body2">
                            {selectedSupplier.internal_rating && typeof selectedSupplier.internal_rating === 'number' ? selectedSupplier.internal_rating.toFixed(1) : 'N/A'}
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Contacts Tab */}
          <TabPanel value={supplierTabValue} index={1}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">{t('suppliers.contacts')}</Typography>
            </Box>
            {selectedSupplier.contacts && selectedSupplier.contacts.length > 0 ? (
              <Grid container spacing={2}>
                {selectedSupplier.contacts.map((contact) => (
                  <Grid item xs={12} md={6} key={contact.id}>
                    <Card>
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                          <Box>
                            <Typography variant="h6">{contact.full_name}</Typography>
                            {contact.is_primary_contact && (
                              <Chip label={t('suppliers.primary')} color="primary" size="small" />
                            )}
                          </Box>
                          <Box>
                            {/* Contact view only - no edit button */}
                          </Box>
                        </Box>
                        <Grid container spacing={1}>
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">
                              {t('suppliers.jobTitle')}: {contact.job_title || '-'}
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">
                              {t('suppliers.department')}: {contact.department || '-'}
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">
                              {t('suppliers.email')}: {contact.email || '-'}
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">
                              {t('suppliers.phone')}: {contact.phone || '-'}
                            </Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Typography variant="body1" color="text.secondary">
                {t('suppliers.noContacts')}
              </Typography>
            )}
          </TabPanel>

          {/* Documents Tab */}
          <TabPanel value={supplierTabValue} index={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">{t('suppliers.documents')}</Typography>
            </Box>
            {selectedSupplier.documents && selectedSupplier.documents.length > 0 ? (
              <Grid container spacing={2}>
                {selectedSupplier.documents.map((document) => (
                  <Grid item xs={12} md={6} key={document.id}>
                    <Card>
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                          <Box>
                            <Typography variant="h6">{document.document_name}</Typography>
                            <Chip
                              label={document.document_type}
                              color="primary"
                              size="small"
                              sx={{ mt: 1 }}
                            />
                            {document.is_verified && (
                              <Chip
                                label={t('suppliers.verified')}
                                color="success"
                                size="small"
                                sx={{ mt: 1, ml: 1 }}
                              />
                            )}
                          </Box>
                          <Box>
                            <IconButton
                              size="small"
                              onClick={() => {
                                // Handle document download
                                window.open(`/api/suppliers/${selectedSupplier.id}/documents/${document.id}/download`);
                              }}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Box>
                        </Box>
                        <Grid container spacing={1}>
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">
                              {t('suppliers.documentNumber')}: {document.document_number || '-'}
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">
                              {t('suppliers.issuedBy')}: {document.issued_by || '-'}
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">
                              {t('suppliers.issuedDate')}: {document.issued_date || '-'}
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary">
                              {t('suppliers.expiryDate')}: {document.expiry_date || '-'}
                            </Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Typography variant="body1" color="text.secondary">
                {t('suppliers.noDocuments')}
              </Typography>
            )}
          </TabPanel>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>
            {t('suppliers.close')}
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  // Render delete confirmation dialog
  const renderDeleteDialog = () => {
    if (!selectedSupplier) return null;

    return (
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>{t('suppliers.deleteSupplier')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('suppliers.confirmDeleteSupplier', { supplierName: selectedSupplier.company_name })}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            {t('suppliers.cancel')}
          </Button>
          <Button
            onClick={handleDeleteSupplier}
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
          >
            {t('suppliers.delete')}
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" gutterBottom>
              {t('suppliers.title')}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {t('suppliers.description')}
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={openCreateDialog}
          >
            {t('suppliers.addSupplier')}
          </Button>
        </Box>

        {/* Main Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={mainTabValue} onChange={(e, v) => setMainTabValue(v)}>
            <Tab label={t('suppliers.suppliers')} />
            <Tab label={t('suppliers.contacts')} />
          </Tabs>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Suppliers Tab */}
        <TabPanel value={mainTabValue} index={0}>
          {/* Filters */}
          <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                placeholder={t('suppliers.searchPlaceholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>{t('suppliers.status')}</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="all">{t('suppliers.allStatuses')}</MenuItem>
                  <MenuItem value="ACTIVE">{t('suppliers.active')}</MenuItem>
                  <MenuItem value="INACTIVE">{t('suppliers.inactive')}</MenuItem>
                  <MenuItem value="SUSPENDED">{t('suppliers.suspended')}</MenuItem>
                  <MenuItem value="PENDING_APPROVAL">{t('suppliers.pendingApproval')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>{t('suppliers.complianceStatus')}</InputLabel>
                <Select
                  value={complianceFilter}
                  onChange={(e) => setComplianceFilter(e.target.value)}
                >
                  <MenuItem value="all">{t('suppliers.allCompliance')}</MenuItem>
                  <MenuItem value="APPROVED">{t('suppliers.approved')}</MenuItem>
                  <MenuItem value="PENDING">{t('suppliers.pending')}</MenuItem>
                  <MenuItem value="REJECTED">{t('suppliers.rejected')}</MenuItem>
                  <MenuItem value="UNDER_REVIEW">{t('suppliers.underReview')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>{t('suppliers.riskLevel')}</InputLabel>
                <Select
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                >
                  <MenuItem value="all">{t('suppliers.allRisks')}</MenuItem>
                  <MenuItem value="LOW">{t('suppliers.lowRisk')}</MenuItem>
                  <MenuItem value="MEDIUM">{t('suppliers.mediumRisk')}</MenuItem>
                  <MenuItem value="HIGH">{t('suppliers.highRisk')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>{t('suppliers.country')}</InputLabel>
                <Select
                  value={countryFilter}
                  onChange={(e) => setCountryFilter(e.target.value)}
                >
                  <MenuItem value="all">{t('suppliers.allCountries')}</MenuItem>
                  {Array.from(new Set(suppliers.map(s => s.country).filter(Boolean))).map(country => (
                    <MenuItem key={country} value={country}>{country}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={1}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadSuppliers}
                fullWidth
              >
                {t('suppliers.refresh')}
              </Button>
            </Grid>
          </Grid>
        </Paper>

        {/* Suppliers Table */}
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>{t('suppliers.supplierId')}</TableCell>
                  <TableCell>{t('suppliers.companyName')}</TableCell>
                  <TableCell>{t('suppliers.category')}</TableCell>
                  <TableCell>{t('suppliers.country')}</TableCell>
                  <TableCell>{t('suppliers.complianceStatus')}</TableCell>
                  <TableCell>{t('suppliers.riskLevel')}</TableCell>
                  <TableCell>{t('suppliers.internalRating')}</TableCell>
                  <TableCell>{t('suppliers.status')}</TableCell>
                  <TableCell>{t('suppliers.actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {suppliers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Typography variant="body1" color="text.secondary">
                        {searchTerm || statusFilter !== 'all' || complianceFilter !== 'all' || riskFilter !== 'all' || countryFilter !== 'all'
                          ? t('suppliers.noSuppliersFound')
                          : t('suppliers.noSuppliersYet')
                        }
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  suppliers.map((supplier) => (
                    <TableRow key={supplier.id}>
                      <TableCell>{supplier.supplier_id}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <BusinessIcon color="primary" />
                          <Typography variant="body2" fontWeight="medium">
                            {supplier.company_name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{supplier.category || '-'}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <FlagIcon fontSize="small" color="action" />
                          {supplier.country || '-'}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={t(`suppliers.${supplier.compliance_status.toLowerCase()}`)}
                          color={getComplianceColor(supplier.compliance_status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={t(`suppliers.${supplier.risk_level.toLowerCase()}Risk`)}
                          color={getRiskColor(supplier.risk_level) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Rating value={Number(supplier.internal_rating) || 0} readOnly size="small" precision={0.1} />
                          <Typography variant="body2">
                            {supplier.internal_rating && typeof supplier.internal_rating === 'number' ? supplier.internal_rating.toFixed(1) : 'N/A'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={t(`suppliers.${supplier.status.toLowerCase()}`)}
                          color={getStatusColor(supplier.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" gap={1}>
                          <Tooltip title={t('suppliers.view')}>
                            <IconButton
                              size="small"
                              onClick={() => openViewDialog(supplier)}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={t('suppliers.edit')}>
                            <IconButton
                              size="small"
                              onClick={() => openEditDialog(supplier)}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={t('suppliers.delete')}>
                            <IconButton
                              size="small"
                              onClick={() => openDeleteDialog(supplier)}
                              color="error"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {/* Pagination */}
        {totalPages > 1 && (
          <Box display="flex" justifyContent="center" mt={3}>
            <Stack direction="row" spacing={1}>
              <Button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </Button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                <Button
                  key={pageNum}
                  variant={pageNum === page ? 'contained' : 'outlined'}
                  onClick={() => setPage(pageNum)}
                >
                  {pageNum}
                </Button>
              ))}
              <Button
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </Stack>
          </Box>
        )}
        </TabPanel>

        {/* Contacts Tab */}
        <TabPanel value={mainTabValue} index={1}>
          {/* Contacts Header */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">
              {t('suppliers.contacts')}
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setContactDialogOpen(true)}
            >
              {t('suppliers.addContact')}
            </Button>
          </Box>

          {/* Contacts Filters */}
          <Paper sx={{ p: 2, mb: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  placeholder={t('suppliers.searchContacts')}
                  value={contactSearchTerm}
                  onChange={(e) => setContactSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>{t('suppliers.supplier')}</InputLabel>
                  <Select
                    value={contactSupplierFilter}
                    onChange={(e) => setContactSupplierFilter(e.target.value)}
                  >
                    <MenuItem value="all">{t('suppliers.allSuppliers')}</MenuItem>
                    {suppliers.map(supplier => (
                      <MenuItem key={supplier.id} value={supplier.id.toString()}>
                        {supplier.company_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={2}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={loadContacts}
                  fullWidth
                >
                  {t('suppliers.refresh')}
                </Button>
              </Grid>
            </Grid>
          </Paper>

          {/* Contacts Table */}
          <Paper>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('suppliers.contactId')}</TableCell>
                    <TableCell>{t('suppliers.fullName')}</TableCell>
                    <TableCell>{t('suppliers.jobTitle')}</TableCell>
                    <TableCell>{t('suppliers.department')}</TableCell>
                    <TableCell>{t('suppliers.email')}</TableCell>
                    <TableCell>{t('suppliers.phone')}</TableCell>
                    <TableCell>{t('suppliers.supplier')}</TableCell>
                    <TableCell>{t('suppliers.isPrimary')}</TableCell>
                    <TableCell>{t('suppliers.actions')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {contactsLoading ? (
                    <TableRow>
                      <TableCell colSpan={9} align="center">
                        <CircularProgress />
                      </TableCell>
                    </TableRow>
                  ) : contacts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} align="center">
                        <Typography variant="body1" color="text.secondary">
                          {contactSearchTerm || contactSupplierFilter !== 'all'
                            ? t('suppliers.noContactsFound')
                            : t('suppliers.noContactsYet')
                          }
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    contacts.map((contact) => (
                      <TableRow key={contact.id}>
                        <TableCell>{contact.contact_id}</TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <PersonIcon color="primary" />
                            <Typography variant="body2" fontWeight="medium">
                              {contact.full_name}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>{contact.job_title || '-'}</TableCell>
                        <TableCell>{contact.department || '-'}</TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <EmailIcon fontSize="small" color="action" />
                            {contact.email || '-'}
                          </Box>
                        </TableCell>
                        <TableCell>{contact.phone || '-'}</TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <BusinessIcon fontSize="small" color="action" />
                            {contact.supplier?.company_name || '-'}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={contact.is_primary_contact ? t('suppliers.yes') : t('suppliers.no')}
                            color={contact.is_primary_contact ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={1}>
                            <Tooltip title={t('suppliers.edit')}>
                              <IconButton
                                size="small"
                                onClick={() => {
                                  setSelectedContact(contact);
                                  setContactForm(contact);
                                  setContactDialogOpen(true);
                                }}
                              >
                                <EditIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title={t('suppliers.delete')}>
                              <IconButton
                                size="small"
                                onClick={() => {
                                  setSelectedContact(contact);
                                  // Add delete confirmation logic here
                                }}
                                color="error"
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          {/* Contacts Pagination */}
          {contactTotalPages > 1 && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Stack direction="row" spacing={1}>
                <Button
                  disabled={contactPage === 1}
                  onClick={() => setContactPage(contactPage - 1)}
                >
                  Previous
                </Button>
                {Array.from({ length: contactTotalPages }, (_, i) => i + 1).map((pageNum) => (
                  <Button
                    key={pageNum}
                    variant={pageNum === contactPage ? 'contained' : 'outlined'}
                    onClick={() => setContactPage(pageNum)}
                  >
                    {pageNum}
                  </Button>
                ))}
                <Button
                  disabled={contactPage === contactTotalPages}
                  onClick={() => setContactPage(contactPage + 1)}
                >
                  Next
                </Button>
              </Stack>
            </Box>
          )}
        </TabPanel>

        {/* Dialogs */}
        {renderSupplierDialog()}
        {renderContactDialog()}
        {renderDocumentDialog()}
        {renderViewDialog()}
        {renderDeleteDialog()}
      </Box>
    </LocalizationProvider>
  );
};

export default SuppliersPage;