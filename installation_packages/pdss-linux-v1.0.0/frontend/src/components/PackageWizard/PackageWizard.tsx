import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Alert,
  CircularProgress,
  Chip,
  Slider,
  Grid,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Inventory as PackageIcon,
  ShoppingCart as ShoppingCartIcon,
  LocalShipping as LocalShippingIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { packagesAPI, suppliersAPI, itemsAPI, procurementAPI } from '../../services/api.ts';
import { ProcurementPackage } from '../../types/packages.ts';
import { calculateCoverageSummary, SubItemRequirement } from '../../utils/coverageCalculator.ts';
import { formatApiError } from '../../utils/errorUtils.ts';
import { PackageWizardStep1 } from './PackageWizardStep1.tsx';
import { PackageWizardStep2 } from './PackageWizardStep2.tsx';
import { PackageWizardStep3 } from './PackageWizardStep3.tsx';

interface PackageWizardProps {
  open: boolean;
  onClose: () => void;
  projectItemId: number;
  itemCode: string;
  itemName?: string;
  mainItemRequiredQuantity: number;
  subItemRequirements: SubItemRequirement[];
  existingPackages?: ProcurementPackage[];
  onPackageCreated?: (packageId: number) => void;
}

interface PackageWizardData {
  // Step 1: Metadata
  package_name: string;
  supplier_id: number | null;
  package_type: 'FULL' | 'PARTIAL' | 'CUSTOM';
  description?: string;

  // Step 2: Quantity Composition
  main_item_quantity: number;
  subitem_quantities: Record<number, number>; // sub_item_id -> quantity

  // Step 3: Pricing & Delivery
  base_cost: number;
  currency_id: number | null;
  shipping_cost: number;
  delivery_option_id: number | null;
  lomc_lead_time: number;
  purchase_date: string;
  expected_delivery_date: string;
  payment_terms: {
    type: 'cash' | 'installments';
    discount_percent: number;
    installments?: Array<{ days_after_purchase: number; percentage: number }>;
  };
  discount_bundle_threshold?: number;
  discount_bundle_percent?: number;
}

const steps = ['Metadata', 'Quantities', 'Pricing & Delivery'];

export const PackageWizard: React.FC<PackageWizardProps> = ({
  open,
  onClose,
  projectItemId,
  itemCode,
  itemName,
  mainItemRequiredQuantity,
  subItemRequirements,
  existingPackages = [],
  onPackageCreated,
}) => {
  const { t } = useTranslation();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [coverageSummary, setCoverageSummary] = useState<any>(null);

  const [wizardData, setWizardData] = useState<PackageWizardData>({
    package_name: '',
    supplier_id: null,
    package_type: 'FULL',
    description: '',
    main_item_quantity: mainItemRequiredQuantity,
    subitem_quantities: {},
    base_cost: 0,
    currency_id: null,
    shipping_cost: 0,
    delivery_option_id: null,
    lomc_lead_time: 0,
    purchase_date: new Date().toISOString().split('T')[0],
    expected_delivery_date: '',
    payment_terms: {
      type: 'cash',
      discount_percent: 0,
    },
  });

  // Initialize subitem quantities
  useEffect(() => {
    if (open && subItemRequirements.length > 0) {
      const initialQuantities: Record<number, number> = {};
      subItemRequirements.forEach((req) => {
        initialQuantities[req.sub_item_id] = req.required_quantity;
      });
      setWizardData((prev) => ({
        ...prev,
        subitem_quantities: initialQuantities,
      }));
    }
  }, [open, subItemRequirements]);

  // Calculate coverage when quantities change
  useEffect(() => {
    if (activeStep === 1 && wizardData.main_item_quantity > 0) {
      const mockPackageCoverage = {
        package_id: 0,
        package_name: wizardData.package_name || 'New Package',
        package_type: wizardData.package_type,
        main_item_quantity: wizardData.main_item_quantity,
        subitem_coverages: subItemRequirements.map((req) => ({
          sub_item_id: req.sub_item_id,
          covered_quantity: wizardData.subitem_quantities[req.sub_item_id] || 0,
          required_quantity: req.required_quantity,
        })),
      };

      const summary = calculateCoverageSummary(
        mainItemRequiredQuantity,
        subItemRequirements,
        [...existingPackages.map((pkg) => ({
          package_id: pkg.id,
          package_name: pkg.package_name || '',
          package_type: pkg.package_type as 'FULL' | 'PARTIAL' | 'CUSTOM',
          main_item_quantity: 0, // Will be calculated from package_subitems
          subitem_coverages: [],
        })),
        mockPackageCoverage]
      );
      setCoverageSummary(summary);
    }
  }, [
    activeStep,
    wizardData.main_item_quantity,
    wizardData.subitem_quantities,
    wizardData.package_name,
    wizardData.package_type,
    mainItemRequiredQuantity,
    subItemRequirements,
    existingPackages,
  ]);

  const handleNext = () => {
    setError(null);
    if (activeStep === 0) {
      // Validate Step 1
      if (!wizardData.package_name.trim()) {
        setError(t('procurement.packageNameRequired') || 'Package name is required');
        return;
      }
      if (!wizardData.supplier_id) {
        setError(t('procurement.supplierRequired') || 'Supplier is required');
        return;
      }
    } else if (activeStep === 1) {
      // Validate Step 2
      if (wizardData.main_item_quantity <= 0) {
        setError(t('procurement.mainItemQuantityRequired') || 'Main item quantity must be greater than 0');
        return;
      }
    }
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setError(null);
    setActiveStep((prev) => prev - 1);
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);

    try {
      // Create package via API
      const packagePayload = {
        project_item_id: projectItemId,
        package_name: wizardData.package_name,
        package_type: wizardData.package_type,
        supplier_id: wizardData.supplier_id,
        description: wizardData.description,
        is_active: true,
      };

      const packageResponse = await packagesAPI.create(packagePayload);
      const newPackageId = packageResponse.data.id;

      // Create procurement option linked to package
      const optionPayload: any = {
        package_id: newPackageId,
        supplier_id: wizardData.supplier_id,
        base_cost: wizardData.base_cost,
        currency_id: wizardData.currency_id,
        shipping_cost: wizardData.shipping_cost,
        delivery_option_id: wizardData.delivery_option_id,
        lomc_lead_time: wizardData.lomc_lead_time,
        purchase_date: wizardData.purchase_date,
        expected_delivery_date: wizardData.expected_delivery_date,
        payment_terms: wizardData.payment_terms,
        discount_bundle_threshold: wizardData.discount_bundle_threshold,
        discount_bundle_percent: wizardData.discount_bundle_percent,
        is_finalized: wizardData.is_finalized || false,
      };

      // Create procurement option via API
      await procurementAPI.create(optionPayload);

      // Create package subitems
      const subitemPayloads = Object.entries(wizardData.subitem_quantities)
        .filter(([_, qty]) => qty > 0)
        .map(([subItemId, quantity]) => ({
          package_id: newPackageId,
          project_item_subitem_id: parseInt(subItemId),
          quantity_covered: quantity,
        }));

      // Create package subitems via API
      if (subitemPayloads.length > 0) {
        await Promise.all(subitemPayloads.map(payload => packagesAPI.createSubItem(payload)));
      }

      if (onPackageCreated) {
        onPackageCreated(newPackageId);
      }

      onClose();
      // Reset wizard
      setActiveStep(0);
      setWizardData({
        package_name: '',
        supplier_id: null,
        package_type: 'FULL',
        description: '',
        main_item_quantity: mainItemRequiredQuantity,
        subitem_quantities: {},
        base_cost: 0,
        currency_id: null,
        shipping_cost: 0,
        delivery_option_id: null,
        lomc_lead_time: 0,
        purchase_date: new Date().toISOString().split('T')[0],
        expected_delivery_date: '',
        payment_terms: {
          type: 'cash',
          discount_percent: 0,
        },
      });
    } catch (err: any) {
      setError(formatApiError(err, t('procurement.failedToCreatePackage') || 'Failed to create package'));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setActiveStep(0);
      setError(null);
      onClose();
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <PackageWizardStep1
            data={wizardData}
            onChange={(updates) => setWizardData((prev) => ({ ...prev, ...updates }))}
          />
        );
      case 1:
        return (
          <PackageWizardStep2
            data={wizardData}
            mainItemRequiredQuantity={mainItemRequiredQuantity}
            subItemRequirements={subItemRequirements}
            coverageSummary={coverageSummary}
            existingPackages={existingPackages}
            projectItemId={projectItemId}
            onChange={(updates) => setWizardData((prev) => ({ ...prev, ...updates }))}
            onCreateForRemainingDemand={(remainingDemand) => {
              // Pre-fill wizard data with remaining demand
              setWizardData((prev) => ({
                ...prev,
                main_item_quantity: remainingDemand.main_item_remaining,
                subitem_quantities: remainingDemand.subitem_remaining.reduce((acc: Record<number, number>, item: any) => {
                  acc[item.sub_item_id] = item.remaining_quantity;
                  return acc;
                }, {}),
                package_type: remainingDemand.main_item_remaining > 0 ? 'PARTIAL' : 'CUSTOM',
              }));
            }}
          />
        );
      case 2:
        return (
          <PackageWizardStep3
            data={wizardData}
            projectItemId={projectItemId}
            onChange={(updates) => setWizardData((prev) => ({ ...prev, ...updates }))}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <PackageIcon color="primary" />
          <Typography variant="h6">
            {t('procurement.createPackage') || 'Create Package'}
          </Typography>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {itemCode} {itemName && `- ${itemName}`}
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3, mt: 2 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {renderStepContent()}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          {t('common.cancel') || 'Cancel'}
        </Button>
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={loading}>
            {t('common.back') || 'Back'}
          </Button>
        )}
        {activeStep < steps.length - 1 ? (
          <Button onClick={handleNext} variant="contained" disabled={loading}>
            {t('common.next') || 'Next'}
          </Button>
        ) : (
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : <CheckCircleIcon />}
          >
            {loading ? (t('common.creating') || 'Creating...') : (t('common.create') || 'Create Package')}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

