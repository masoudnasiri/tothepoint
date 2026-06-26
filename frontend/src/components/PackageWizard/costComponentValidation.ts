import type {
  ProcurementCostComponentPaymentMetadata,
  ProcurementCostComponentType,
} from '../../types/index.ts';

export type CostComponentValidationErrorCode =
  | 'amountRequired'
  | 'amountPositive'
  | 'currencyRequired'
  | 'typeRequired'
  | 'otherDescriptionRequired';

export interface CostComponentDraftForValidation {
  id?: number;
  component_type?: ProcurementCostComponentType | '' | null | string;
  description?: string | null;
  amount_value?: number | '' | null;
  amount_currency?: string | null;
  amount_irr?: number | null;
  exchange_rate_date?: string;
  payment_metadata?: ProcurementCostComponentPaymentMetadata | null;
}

export interface ValidatedCostComponentDraft {
  id?: number;
  component_type: ProcurementCostComponentType;
  description?: string;
  amount_value: number;
  amount_currency: string;
  amount_irr?: number;
  exchange_rate_date?: string;
  payment_metadata?: ProcurementCostComponentPaymentMetadata;
}

export interface CostComponentValidationIssue {
  index: number;
  code: CostComponentValidationErrorCode;
}

export interface CostComponentsValidationResult {
  valid: boolean;
  validComponents: ValidatedCostComponentDraft[];
  issues: CostComponentValidationIssue[];
  invalidIndexes: number[];
}

export const ALLOWED_COST_COMPONENT_TYPES: ProcurementCostComponentType[] = [
  'BASE_PRICE',
  'SHIPPING',
  'VAT',
  'CUSTOMS',
  'CLEARANCE',
  'INSURANCE',
  'BANK_FEE',
  'OTHER',
];

const ALLOWED_COST_COMPONENT_TYPES_SET = new Set<string>(ALLOWED_COST_COMPONENT_TYPES);

const isBlank = (value: unknown): boolean =>
  value === undefined ||
  value === null ||
  (typeof value === 'string' && value.trim() === '');

const isAmountMissing = (amountValue: CostComponentDraftForValidation['amount_value']): boolean =>
  amountValue === undefined || amountValue === null || amountValue === '';

const isFullyEmptyCostComponent = (component: CostComponentDraftForValidation): boolean => {
  const componentType = String(component.component_type || '').trim();
  const currency = String(component.amount_currency || '').trim();
  const description = String(component.description || '').trim();
  const amountMissing = isAmountMissing(component.amount_value);
  return componentType === '' && currency === '' && description === '' && amountMissing;
};

export const getCostComponentValidationMessage = (
  code: CostComponentValidationErrorCode,
  t: (key: string, options?: Record<string, unknown>) => string
): string => t(`procurement.costComponentValidation.${code}`);

export const validateCostComponentDraft = (
  component: CostComponentDraftForValidation
): CostComponentValidationErrorCode | null => {
  const normalizedType = String(component.component_type || '').trim().toUpperCase();
  if (!ALLOWED_COST_COMPONENT_TYPES_SET.has(normalizedType)) {
    return 'typeRequired';
  }

  if (isAmountMissing(component.amount_value)) {
    return 'amountRequired';
  }

  const normalizedAmount = Number(component.amount_value);
  if (!Number.isFinite(normalizedAmount) || normalizedAmount <= 0) {
    return 'amountPositive';
  }

  if (isBlank(component.amount_currency)) {
    return 'currencyRequired';
  }

  if (normalizedType === 'OTHER' && isBlank(component.description)) {
    return 'otherDescriptionRequired';
  }

  return null;
};

export const validateCostComponentsForSave = (
  components: CostComponentDraftForValidation[]
): CostComponentsValidationResult => {
  const issues: CostComponentValidationIssue[] = [];
  const validComponents: ValidatedCostComponentDraft[] = [];

  (components || []).forEach((component, index) => {
    const isFullyEmpty = isFullyEmptyCostComponent(component);

    // Ignore accidental blank rows that were never persisted/touched.
    if (isFullyEmpty && !component.id) {
      return;
    }

    const validationCode = validateCostComponentDraft(component);
    if (validationCode) {
      issues.push({ index, code: validationCode });
      return;
    }

    validComponents.push({
      id: component.id,
      component_type: String(component.component_type).trim().toUpperCase() as ProcurementCostComponentType,
      description: String(component.description || '').trim() || undefined,
      amount_value: Number(component.amount_value),
      amount_currency: String(component.amount_currency || '').trim().toUpperCase(),
      amount_irr:
        component.amount_irr !== undefined && component.amount_irr !== null
          ? Number(component.amount_irr)
          : undefined,
      exchange_rate_date: component.exchange_rate_date || undefined,
      payment_metadata: component.payment_metadata || undefined,
    });
  });

  return {
    valid: issues.length === 0,
    validComponents,
    issues,
    invalidIndexes: Array.from(new Set(issues.map((issue) => issue.index))).sort((a, b) => a - b),
  };
};

