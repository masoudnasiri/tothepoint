import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Inventory as PackageIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { packagesAPI, suppliersAPI, procurementAPI, procurementFinancialsAPI } from '../../services/api.ts';
import { ProcurementPackage } from '../../types/packages.ts';
import type {
  DeliveryDateSource,
  ForecastDateSource,
  ProcurementCostComponentType,
} from '../../types/index.ts';
import { calculateCoverageSummary, SubItemRequirement } from '../../utils/coverageCalculator.ts';
import { formatApiError } from '../../utils/errorUtils.ts';
import {
  getCostComponentValidationMessage,
  validateCostComponentsForSave,
  type ValidatedCostComponentDraft,
} from './costComponentValidation.ts';
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
  editingPackageId?: number | null; // Package ID when editing
  initialData?: Partial<PackageWizardData>; // Initial data for edit mode
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
  is_finalized: boolean;
  option_id: number | null;
  payment_method_id: number | null;
  payment_date: string;
  planned_supplier_payment_date?: string;
  supplier_effective_receipt_date?: string;
  cost_components: CostComponentDraft[];
  project_requested_delivery_date?: string;
  supplier_actual_delivery_date?: string;
  selected_delivery_date?: string;
  delivery_date_source?: DeliveryDateSource | null;
  delivery_date_variance_days?: number | null;
  forecast_customer_invoice_date?: string;
  forecast_customer_invoice_date_source?: ForecastDateSource | null;
  forecast_customer_receipt_date?: string;
  forecast_customer_receipt_date_source?: ForecastDateSource | null;
  forecast_customer_receipt_delay_days?: number | null;
  date_calculation_trace?: string[];
}

interface CostComponentDraft {
  id?: number;
  component_type: ProcurementCostComponentType | '';
  description?: string;
  amount_value: number | '';
  amount_currency: string;
  amount_irr?: number;
  exchange_rate_date?: string;
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
  editingPackageId = null,
  initialData,
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
    is_finalized: false,
    option_id: null,
    payment_method_id: null,
    payment_date: new Date().toISOString().split('T')[0],
    cost_components: [],
    project_requested_delivery_date: '',
    supplier_actual_delivery_date: '',
    selected_delivery_date: '',
    delivery_date_source: null,
    delivery_date_variance_days: null,
    forecast_customer_invoice_date: '',
    forecast_customer_invoice_date_source: null,
    forecast_customer_receipt_date: '',
    forecast_customer_receipt_date_source: null,
    forecast_customer_receipt_delay_days: null,
    date_calculation_trace: [],
  });

  // Initialize wizard data when opening (for create) or when initialData changes (for edit)
  useEffect(() => {
    if (open) {
      if (initialData && editingPackageId) {
        // Edit mode: use initialData
        setWizardData({
          package_name: initialData.package_name || '',
          supplier_id: initialData.supplier_id || null,
          package_type: initialData.package_type || 'FULL',
          description: initialData.description || '',
          main_item_quantity: initialData.main_item_quantity ?? mainItemRequiredQuantity,
          subitem_quantities: initialData.subitem_quantities || {},
          base_cost: initialData.base_cost || 0,
          currency_id: initialData.currency_id || null,
          shipping_cost: initialData.shipping_cost || 0,
          delivery_option_id: initialData.delivery_option_id || null,
          lomc_lead_time: initialData.lomc_lead_time || 0,
          purchase_date: initialData.purchase_date || new Date().toISOString().split('T')[0],
          expected_delivery_date: initialData.expected_delivery_date || '',
          payment_terms: initialData.payment_terms || {
            type: 'cash',
            discount_percent: 0,
          },
          discount_bundle_threshold: initialData.discount_bundle_threshold,
          discount_bundle_percent: initialData.discount_bundle_percent,
          is_finalized: initialData.is_finalized || false,
          option_id: initialData.option_id || null,
          payment_method_id: initialData.payment_method_id || null,
          payment_date:
            initialData.planned_supplier_payment_date ||
            initialData.payment_date ||
            new Date().toISOString().split('T')[0],
          cost_components: initialData.cost_components || [],
          project_requested_delivery_date: initialData.project_requested_delivery_date || '',
          supplier_actual_delivery_date: initialData.supplier_actual_delivery_date || '',
          selected_delivery_date: initialData.selected_delivery_date || '',
          delivery_date_source: initialData.delivery_date_source || null,
          delivery_date_variance_days: initialData.delivery_date_variance_days ?? null,
          forecast_customer_invoice_date: initialData.forecast_customer_invoice_date || '',
          forecast_customer_invoice_date_source:
            initialData.forecast_customer_invoice_date_source || null,
          forecast_customer_receipt_date: initialData.forecast_customer_receipt_date || '',
          forecast_customer_receipt_date_source:
            initialData.forecast_customer_receipt_date_source || null,
          forecast_customer_receipt_delay_days:
            initialData.forecast_customer_receipt_delay_days ?? null,
          date_calculation_trace: initialData.date_calculation_trace || [],
        });
        setActiveStep(0); // Reset to first step when editing
      } else if (subItemRequirements.length > 0) {
        // Create mode: initialize with default quantities
        const initialQuantities: Record<number, number> = {};
        subItemRequirements.forEach((req) => {
          initialQuantities[req.sub_item_id] = req.required_quantity;
        });
        setWizardData((prev) => ({
          ...prev,
          subitem_quantities: initialQuantities,
        }));
      }
    }
  }, [open, subItemRequirements, initialData, editingPackageId, mainItemRequiredQuantity]);

  // Calculate coverage when quantities change
  useEffect(() => {
    // Calculate coverage if there's at least main item quantity or sub-items
    const hasMainItem = wizardData.main_item_quantity > 0;
    const hasSubItems = Object.values(wizardData.subitem_quantities).some(qty => qty > 0);
    
    if (activeStep === 1 && (hasMainItem || hasSubItems)) {
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
          main_item_quantity: Number(pkg.main_item_quantity || 0),
          subitem_coverages: (pkg.subitems || [])
            .map((sub: any) => {
              const requirement = subItemRequirements.find(
                (req) => req.item_subitem_id === sub.project_item_subitem_id
              );
              if (!requirement) return null;
              return {
                sub_item_id: requirement.sub_item_id,
                covered_quantity: Number(sub.quantity_covered || 0),
                required_quantity: requirement.required_quantity || 0,
              };
            })
            .filter((sub): sub is { sub_item_id: number; covered_quantity: number; required_quantity: number } => sub !== null),
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

  const handleNext = async () => {
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
      
      // Check if package name already exists for this project item (exclude current package if editing)
      try {
        const existingPackagesResponse = await packagesAPI.listByProjectItem(projectItemId, true);
        const existingPackages = existingPackagesResponse.data || [];
        const nameExists = existingPackages.some(
          (pkg: any) => 
            pkg.id !== editingPackageId && // Exclude current package when editing
            pkg.package_name?.toLowerCase() === wizardData.package_name.trim().toLowerCase()
        );
        if (nameExists) {
          setError(
            t('procurement.packageNameExists') || 
            `A package with the name "${wizardData.package_name}" already exists for this item. Please choose a different name.`
          );
          return;
        }
      } catch (err) {
        // If check fails, continue anyway (backend will catch it)
        console.warn('Failed to check for existing package names:', err);
      }
    } else if (activeStep === 1) {
      // Validate Step 2 - Allow zero main item if sub-items are specified
      const hasSubItems = Object.values(wizardData.subitem_quantities).some(qty => qty > 0);
      if (wizardData.main_item_quantity <= 0 && !hasSubItems) {
        setError(t('procurement.mainItemOrSubItemsRequired') || 'Either main item quantity or at least one sub-item quantity must be greater than 0');
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
    setError(null);

    const costComponentValidation = validateCostComponentsForSave(wizardData.cost_components || []);
    if (!costComponentValidation.valid) {
      const invalidRows = costComponentValidation.invalidIndexes.map((index) => index + 1);
      const firstIssue = costComponentValidation.issues[0];
      const firstIssueMessage = firstIssue
        ? getCostComponentValidationMessage(firstIssue.code, t)
        : '';

      setError(
        t('procurement.costComponentValidation.invalidRows', {
          rows: invalidRows.join(', '),
          message: firstIssueMessage,
        })
      );
      return;
    }

    const basePriceComponents = costComponentValidation.validComponents.filter(
      (component) => component.component_type === 'BASE_PRICE'
    );
    if (basePriceComponents.length === 0) {
      setError(t('procurement.basePriceRequired'));
      return;
    }
    if (basePriceComponents.length > 1) {
      setError(t('procurement.singleBasePriceOnly'));
      return;
    }

    const shippingComponents = costComponentValidation.validComponents.filter(
      (component) => component.component_type === 'SHIPPING'
    );
    if (shippingComponents.length > 1) {
      setError(t('procurement.singleShippingOnly'));
      return;
    }

    const derivedBaseCost = Number(basePriceComponents[0].amount_value);
    const derivedShippingCost = shippingComponents[0]
      ? Number(shippingComponents[0].amount_value)
      : 0;

    setLoading(true);

    try {
      const syncCostComponents = async (
        optionId: number,
        nextComponents: ValidatedCostComponentDraft[]
      ) => {
        const response = await procurementFinancialsAPI.listCostComponents(optionId, false);
        const existingComponents = response.data || [];
        const nextIds = new Set(
          nextComponents
            .map((component) => component.id)
            .filter((id): id is number => typeof id === 'number')
        );

        const toDeactivate = existingComponents.filter(
          (component) => component.is_active && !nextIds.has(component.id)
        );

        for (const component of toDeactivate) {
          await procurementFinancialsAPI.deactivateCostComponent(component.id);
        }

        const orderedComponents = [...nextComponents].sort((left, right) => {
          const rank = (type: string) =>
            type === 'BASE_PRICE' ? 0 : type === 'SHIPPING' ? 1 : 2;
          return rank(left.component_type) - rank(right.component_type);
        });

        for (const component of orderedComponents) {
          const payload = {
            component_type: component.component_type,
            description: component.description?.trim() || undefined,
            amount_value: Number(component.amount_value),
            amount_currency: (component.amount_currency || '').trim().toUpperCase(),
            amount_irr:
              component.amount_irr !== undefined && component.amount_irr !== null
                ? Number(component.amount_irr)
                : undefined,
            exchange_rate_date: component.exchange_rate_date || undefined,
            is_active: true,
          };

          if (component.id) {
            await procurementFinancialsAPI.updateCostComponent(component.id, payload);
          } else {
            await procurementFinancialsAPI.createCostComponent(optionId, payload);
          }
        }
      };

      // Determine package type based on coverage
      let finalPackageType: 'FULL' | 'PARTIAL' | 'CUSTOM' = 'CUSTOM';
      if (coverageSummary?.is_fully_covered) {
        finalPackageType = 'FULL';
      } else if (wizardData.main_item_quantity > 0 || Object.values(wizardData.subitem_quantities).some(qty => qty > 0)) {
        finalPackageType = 'PARTIAL';
      }

      const packagePayload = {
        project_item_id: projectItemId,
        package_name: wizardData.package_name,
        package_type: finalPackageType,
        supplier_id: wizardData.supplier_id,
        description: wizardData.description,
        is_active: true,
        main_item_quantity: wizardData.main_item_quantity || 0,
        is_finalized: wizardData.is_finalized,
      };

      let newPackageId: number;
      
      if (editingPackageId) {
        // Update existing package
        await packagesAPI.update(editingPackageId, packagePayload);
        newPackageId = editingPackageId;
      } else {
        // Create new package
        const packageResponse = await packagesAPI.create(packagePayload);
        newPackageId = packageResponse.data.id;
      }

      // Get supplier name for procurement option (required legacy field)
      // Use a default name and continue even if supplier fetch fails
      let supplierName = 'Unknown Supplier';
      if (wizardData.supplier_id) {
        try {
          const supplierResponse = await suppliersAPI.get(wizardData.supplier_id);
          supplierName = supplierResponse.data?.company_name || supplierResponse.data?.name || `Supplier ${wizardData.supplier_id}`;
        } catch (err) {
          // If supplier fetch fails, use a fallback name based on supplier_id
          // This allows package creation to continue even if supplier endpoint has issues
          console.warn('Failed to fetch supplier name:', err);
          supplierName = `Supplier ${wizardData.supplier_id}`;
        }
      }
      
      // Create or update procurement option linked to package.
      // A package can still exist without an option, but finalized state for optimization
      // is stored on procurement options, so we persist is_finalized whenever possible.
      let persistedOptionId: number | null = wizardData.option_id || null;
      let costComponentPersistenceError: any = null;
      if (derivedBaseCost > 0 && wizardData.currency_id) {
        try {
          const existingOptionsResponse = await procurementAPI.listByProjectItem(projectItemId);
          const existingOption = (existingOptionsResponse.data || []).find(
            (opt: any) => opt.package_id === newPackageId
          );

          const optionPayload: any = {
            package_id: newPackageId,
            project_item_id: projectItemId,
            item_code: itemCode, // Use item code from props
            supplier_id: wizardData.supplier_id,
            supplier_name: supplierName, // Required legacy field
            base_cost: derivedBaseCost,
            currency_id: wizardData.currency_id,
            shipping_cost: derivedShippingCost,
            delivery_option_id: wizardData.delivery_option_id,
            lomc_lead_time: wizardData.lomc_lead_time || 0,
            purchase_date: wizardData.purchase_date,
            expected_delivery_date: wizardData.expected_delivery_date,
            payment_terms: wizardData.payment_terms,
            payment_method_id: wizardData.payment_method_id || undefined,
            planned_supplier_payment_date: wizardData.payment_date || undefined,
            discount_bundle_threshold: wizardData.discount_bundle_threshold,
            discount_bundle_percent: wizardData.discount_bundle_percent,
            is_finalized: wizardData.is_finalized || false,
            project_requested_delivery_date:
              wizardData.project_requested_delivery_date || undefined,
            supplier_actual_delivery_date:
              wizardData.supplier_actual_delivery_date || undefined,
            selected_delivery_date: wizardData.selected_delivery_date || undefined,
            delivery_date_source: wizardData.delivery_date_source || undefined,
            delivery_date_variance_days:
              wizardData.delivery_date_variance_days !== null &&
              wizardData.delivery_date_variance_days !== undefined
                ? Number(wizardData.delivery_date_variance_days)
                : undefined,
            forecast_customer_invoice_date:
              wizardData.forecast_customer_invoice_date || undefined,
            forecast_customer_invoice_date_source:
              wizardData.forecast_customer_invoice_date_source || undefined,
            forecast_customer_receipt_date:
              wizardData.forecast_customer_receipt_date || undefined,
            forecast_customer_receipt_date_source:
              wizardData.forecast_customer_receipt_date_source || undefined,
            forecast_customer_receipt_delay_days:
              wizardData.forecast_customer_receipt_delay_days !== null &&
              wizardData.forecast_customer_receipt_delay_days !== undefined
                ? Number(wizardData.forecast_customer_receipt_delay_days)
                : undefined,
            date_calculation_trace:
              wizardData.date_calculation_trace && wizardData.date_calculation_trace.length > 0
                ? wizardData.date_calculation_trace
                : undefined,
          };

          if (existingOption?.id) {
            await procurementAPI.update(existingOption.id, optionPayload);
            persistedOptionId = existingOption.id;
          } else {
            const createdOptionResponse = await procurementAPI.create(optionPayload);
            persistedOptionId = createdOptionResponse?.data?.id || null;
          }
        } catch (optionErr: any) {
          throw optionErr;
        }
      }

      if (persistedOptionId) {
        try {
          await syncCostComponents(persistedOptionId, costComponentValidation.validComponents);
        } catch (costComponentErr: any) {
          costComponentPersistenceError = costComponentErr;
        }
      }

      // Handle package subitems
      if (editingPackageId) {
        // Update mode: fetch existing subitems and delete them, then recreate
        try {
          const existingSubitemsResponse = await packagesAPI.get(newPackageId);
          const existingSubitems = existingSubitemsResponse.data?.subitems || [];
          
          // Delete all existing subitems
          for (const existing of existingSubitems) {
            try {
              await packagesAPI.deleteSubItem(existing.id);
            } catch (err) {
              console.warn(`Failed to delete subitem ${existing.id}:`, err);
            }
          }
        } catch (err) {
          console.warn('Failed to fetch existing subitems:', err);
        }
      }
      
      // Create package subitems
      // Note: wizardData.subitem_quantities uses sub_item_id as key, but we need project_item_subitem_id
      // Find the matching requirement to get the correct project_item_subitem_id
      const subitemPayloads = Object.entries(wizardData.subitem_quantities)
        .filter(([_, qty]) => qty > 0 && Number(qty) > 0)
        .map(([subItemId, quantity]) => {
          // Find the requirement that matches this sub_item_id
          const requirement = subItemRequirements.find((req) => req.sub_item_id === parseInt(subItemId));
          if (!requirement || !requirement.item_subitem_id) {
            console.warn(`Could not find requirement for sub_item_id ${subItemId}`);
            return null;
          }
          return {
            package_id: newPackageId,
            project_item_subitem_id: requirement.item_subitem_id, // Use item_subitem_id (the actual DB ID)
            quantity_covered: Number(quantity), // Ensure it's a number
          };
        })
        .filter((payload) => payload !== null); // Remove any null entries

      // Create package subitems via API
      if (subitemPayloads.length > 0) {
        await Promise.all(subitemPayloads.map(payload => packagesAPI.createSubItem(payload)));
      }

      if (costComponentPersistenceError) {
        if (persistedOptionId && persistedOptionId !== wizardData.option_id) {
          setWizardData((prev) => ({ ...prev, option_id: persistedOptionId }));
        }

        const componentSaveError = formatApiError(
          costComponentPersistenceError,
          t('procurement.costComponentSaveFailed')
        );
        setError(
          `${t('procurement.costComponentPartialSaveWarning')} ${componentSaveError}`.trim()
        );
        return;
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
        is_finalized: false,
        option_id: null,
        payment_method_id: null,
        payment_date: new Date().toISOString().split('T')[0],
        cost_components: [],
        project_requested_delivery_date: '',
        supplier_actual_delivery_date: '',
        selected_delivery_date: '',
        delivery_date_source: null,
        delivery_date_variance_days: null,
        forecast_customer_invoice_date: '',
        forecast_customer_invoice_date_source: null,
        forecast_customer_receipt_date: '',
        forecast_customer_receipt_date_source: null,
        forecast_customer_receipt_delay_days: null,
        date_calculation_trace: [],
      });

      if (onPackageCreated) {
        try {
          await Promise.resolve(onPackageCreated(newPackageId));
        } catch (refreshErr) {
          console.warn('Package created but post-create refresh failed:', refreshErr);
        }
      }
    } catch (err: any) {
      // Handle duplicate package name error specifically
      if (err?.response?.status === 409 || err?.response?.status === 400) {
        const errorMessage = formatApiError(err, t('procurement.failedToCreatePackage') || 'Failed to create package');
        setError(errorMessage);
      } else {
        setError(formatApiError(err, t('procurement.failedToCreatePackage') || 'Failed to create package'));
      }
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
            data={{ ...wizardData, main_item_quantity: wizardData.main_item_quantity }}
            projectItemId={projectItemId}
            onChange={(updates) => setWizardData((prev) => ({ ...prev, ...updates }))}
          />
        );
      default:
        return null;
    }
  };

  const stepLabels = [
    t('procurement.stepMetadata') || 'Metadata',
    t('procurement.stepQuantities') || 'Quantities',
    t('procurement.stepPricing') || 'Pricing & Delivery',
  ];

  const coveragePercent = coverageSummary
    ? (coverageSummary.main_item?.covered / (mainItemRequiredQuantity || 1)) * 100
    : 0;
  const coveragePercentLabel = Math.round(coveragePercent);
  const coveragePercentForRing = Math.min(100, Math.max(0, coveragePercent));
  const totalRequiredForCurrent = mainItemRequiredQuantity + subItemRequirements.reduce((sum, req) => sum + (req.required_quantity || 0), 0);
  const totalCurrentPackageCovered =
    (wizardData.main_item_quantity || 0) +
    Object.values(wizardData.subitem_quantities || {}).reduce((sum, qty) => sum + (Number(qty) || 0), 0);
  const currentPackageCoveragePercent = totalRequiredForCurrent > 0
    ? Math.round((totalCurrentPackageCovered / totalRequiredForCurrent) * 100)
    : 0;

  const coverageColor =
    coveragePercent >= 100 ? '#1B7A4D' :
    coveragePercent >= 70  ? '#B4740E' : '#C23A3A';

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: '14px',
          overflow: 'hidden',
          maxHeight: '90vh',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          px: 3,
          py: 2,
          borderBottom: '1px solid #E4E7EC',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#FFFFFF',
        }}
      >
        <Box display="flex" alignItems="center" gap={1.5}>
          <Box
            sx={{
              width: 32, height: 32, borderRadius: '8px',
              background: '#EEF1FD', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
            }}
          >
            <PackageIcon sx={{ fontSize: 18, color: '#3651D4' }} />
          </Box>
          <Box>
            <Typography sx={{ fontWeight: 700, fontSize: '0.9375rem', color: '#14181F', lineHeight: 1.2 }}>
              {editingPackageId
                ? (t('procurement.editPackage') || 'Edit Package')
                : (t('procurement.createPackage') || 'Create Package')}
            </Typography>
            <Typography sx={{ fontSize: '0.75rem', color: '#8A92A1' }}>
              {itemCode}{itemName ? ` — ${itemName}` : ''}
            </Typography>
          </Box>
        </Box>

        {/* Step indicator */}
        <Box display="flex" alignItems="center" gap={0.75}>
          {stepLabels.map((label, idx) => (
            <Box
              key={label}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                opacity: idx > activeStep ? 0.4 : 1,
              }}
            >
              <Box
                sx={{
                  width: 22, height: 22, borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.6875rem', fontWeight: 700,
                  background: idx < activeStep ? '#1B7A4D' : idx === activeStep ? '#3651D4' : '#EEF0F3',
                  color: idx <= activeStep ? '#fff' : '#8A92A1',
                }}
              >
                {idx < activeStep ? '✓' : idx + 1}
              </Box>
              <Typography sx={{ fontSize: '0.75rem', fontWeight: idx === activeStep ? 600 : 400, color: idx === activeStep ? '#14181F' : '#8A92A1', display: { xs: 'none', sm: 'block' } }}>
                {label}
              </Typography>
              {idx < stepLabels.length - 1 && (
                <Box sx={{ width: 16, height: 1, background: '#E4E7EC', mx: 0.25 }} />
              )}
            </Box>
          ))}
        </Box>
      </Box>

      <DialogContent sx={{ p: 0, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
        {/* Main content */}
        <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2.5 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          {renderStepContent()}
        </Box>

        {/* Coverage sidebar (step 1+) */}
        {activeStep >= 1 && (
          <Box
            sx={{
              width: 220,
              flexShrink: 0,
              borderLeft: '1px solid #E4E7EC',
              background: '#F6F7F9',
              p: 2.5,
              overflowY: 'auto',
              display: { xs: 'none', sm: 'block' },
            }}
          >
            <Typography sx={{ fontSize: '0.6875rem', fontWeight: 600, color: '#8A92A1', textTransform: 'uppercase', letterSpacing: '0.06em', mb: 2 }}>
              Coverage
            </Typography>

            {/* Coverage ring */}
            <Box display="flex" justifyContent="center" mb={2}>
              <Box sx={{ position: 'relative', width: 80, height: 80 }}>
                <svg width={80} height={80} style={{ transform: 'rotate(-90deg)' }}>
                  <circle cx={40} cy={40} r={33} fill="none" stroke="#EEF0F3" strokeWidth={7} />
                  <circle
                    cx={40} cy={40} r={33} fill="none"
                    stroke={coverageColor} strokeWidth={7}
                    strokeDasharray={`${(coveragePercentForRing / 100) * 2 * Math.PI * 33} ${2 * Math.PI * 33}`}
                    strokeLinecap="round"
                  />
                </svg>
                <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography sx={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.9375rem', fontWeight: 700, color: coverageColor }}>
                    {coveragePercentLabel}%
                  </Typography>
                </Box>
              </Box>
            </Box>

            <Typography sx={{ fontSize: '0.75rem', fontWeight: 500, color: '#14181F', textAlign: 'center', mb: 0.5 }}>
              {coverageSummary?.is_over_covered
                ? 'Covered with surplus'
                : coverageSummary?.is_fully_covered
                  ? 'Fully covered'
                  : 'Partial coverage'}
            </Typography>

            {coverageSummary && (
              <Box sx={{ mt: 2 }}>
                <Box sx={{ mb: 1.5 }}>
                  <Typography sx={{ fontSize: '0.6875rem', color: '#8A92A1', mb: 0.25 }}>This package coverage</Typography>
                  <Typography sx={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.8125rem', fontWeight: 600, color: '#14181F' }}>
                    {currentPackageCoveragePercent}%
                  </Typography>
                </Box>
                <Box sx={{ mb: 1.5 }}>
                  <Typography sx={{ fontSize: '0.6875rem', color: '#8A92A1', mb: 0.25 }}>Optimization-eligible aggregate coverage</Typography>
                  <Typography sx={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.8125rem', fontWeight: 600, color: '#14181F' }}>
                    {coveragePercentLabel}%
                  </Typography>
                </Box>
                <Box sx={{ mb: 1.5 }}>
                  <Typography sx={{ fontSize: '0.6875rem', color: '#8A92A1', mb: 0.25 }}>Main item aggregate</Typography>
                  <Typography sx={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.8125rem', fontWeight: 600, color: '#14181F' }}>
                    {coverageSummary.main_item?.covered || 0} / {mainItemRequiredQuantity}
                  </Typography>
                </Box>
                {subItemRequirements.length > 0 && (
                  <Box>
                    <Typography sx={{ fontSize: '0.6875rem', color: '#8A92A1', mb: 0.75 }}>Sub-items</Typography>
                    {subItemRequirements.map(req => {
                      const covered = (wizardData.subitem_quantities?.[req.sub_item_id] || 0) as number;
                      const pct = req.required_quantity > 0 ? Math.round((covered / req.required_quantity) * 100) : 0;
                      return (
                        <Box key={req.sub_item_id} sx={{ mb: 1 }}>
                          <Box display="flex" justifyContent="space-between" mb={0.25}>
                            <Typography sx={{ fontSize: '0.6875rem', color: '#5B6472', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {req.name || `SI-${req.sub_item_id}`}
                            </Typography>
                            <Typography sx={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.6875rem', fontWeight: 600, color: pct >= 100 ? '#1B7A4D' : '#B4740E' }}>
                              {pct}%
                            </Typography>
                          </Box>
                          <Box sx={{ height: 4, background: '#EEF0F3', borderRadius: 2 }}>
                            <Box sx={{ height: '100%', width: `${Math.min(pct, 100)}%`, background: pct >= 100 ? '#1B7A4D' : pct >= 70 ? '#B4740E' : '#C23A3A', borderRadius: 2, transition: 'width 0.3s' }} />
                          </Box>
                        </Box>
                      );
                    })}
                  </Box>
                )}
              </Box>
            )}

            {coverageSummary && coverageSummary.is_over_covered && (
              <Box
                sx={{
                  mt: 2, p: 1.5, background: '#EEF5EE',
                  border: '1px solid #CBE8CB', borderRadius: '8px',
                }}
              >
                <Typography sx={{ fontSize: '0.6875rem', fontWeight: 600, color: '#1B7A4D' }}>
                  Surplus coverage
                </Typography>
                <Typography sx={{ fontSize: '0.6875rem', color: '#1B7A4D', mt: 0.25 }}>
                  Aggregate coverage exceeds required demand. Review before optimization submission.
                </Typography>
              </Box>
            )}

            {coverageSummary && !coverageSummary.is_fully_covered && (
              <Box
                sx={{
                  mt: 2, p: 1.5, background: '#FBF1E0',
                  border: '1px solid #F1D9A6', borderRadius: '8px',
                }}
              >
                <Typography sx={{ fontSize: '0.6875rem', fontWeight: 600, color: '#B4740E' }}>
                  Incomplete coverage
                </Typography>
                <Typography sx={{ fontSize: '0.6875rem', color: '#B4740E', mt: 0.25 }}>
                  Review quantities to ensure full project item coverage.
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      {/* Footer */}
      <Box
        sx={{
          px: 3,
          py: 2,
          borderTop: '1px solid #E4E7EC',
          background: '#FFFFFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1.5,
        }}
      >
        <Button
          onClick={handleClose}
          disabled={loading}
          variant="outlined"
          size="small"
        >
          {t('common.cancel') || 'Cancel'}
        </Button>

        <Box display="flex" alignItems="center" gap={1}>
          {activeStep > 0 && (
            <Button onClick={handleBack} disabled={loading} size="small" variant="outlined">
              {t('common.back') || 'Back'}
            </Button>
          )}
          {activeStep < steps.length - 1 ? (
            <Button onClick={handleNext} variant="contained" disabled={loading} size="small">
              {t('common.next') || 'Next'} →
            </Button>
          ) : (
            <Button
              onClick={handleSave}
              variant="contained"
              disabled={loading}
              size="small"
              startIcon={loading ? <CircularProgress size={14} sx={{ color: '#fff' }} /> : <CheckCircleIcon sx={{ fontSize: 15 }} />}
            >
              {loading
                ? (editingPackageId ? (t('common.updating') || 'Updating…') : (t('common.creating') || 'Creating…'))
                : (editingPackageId ? (t('common.update') || 'Update Package') : (t('common.create') || 'Create Package'))}
            </Button>
          )}
        </Box>
      </Box>
    </Dialog>
  );
};

