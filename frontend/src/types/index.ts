// API Types
export interface User {
  id: number;
  username: string;
  role: 'admin' | 'pmo' | 'pm' | 'procurement' | 'finance';
  created_at: string;
  is_active: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Project {
  id: number;
  project_code: string;
  name: string;
  priority_weight: number;
  created_at: string;
  is_active: boolean;
  phases?: ProjectPhase[];
}

export interface ProjectSummary {
  id: number;
  project_code: string;
  name: string;
  item_count: number;
  total_quantity: number;
  estimated_cost: number;
  estimated_revenue: number;
}

export interface ProjectPhase {
  id: number;
  project_id: number;
  phase_name: string;
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string | null;
}

export interface ProjectPhaseCreate {
  project_id: number;
  phase_name: string;
  start_date: string;
  end_date: string;
}

export interface ProjectPhaseUpdate {
  phase_name?: string;
  start_date?: string;
  end_date?: string;
}

// Items Master (Centralized Catalog)
export interface ItemMaster {
  id: number;
  item_code: string;
  company: string;
  item_name: string;
  model?: string;
  specifications?: any;
  category?: string;
  unit: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  created_by_id?: number;
  is_active: boolean;
}

export interface ItemMasterCreate {
  company: string;
  item_name: string;
  model?: string;
  specifications?: any;
  category?: string;
  unit?: string;
  description?: string;
}

export interface ItemMasterUpdate {
  company?: string;
  item_name?: string;
  model?: string;
  specifications?: any;
  category?: string;
  unit?: string;
  description?: string;
  is_active?: boolean;
}

export type ProjectItemStatus = 
  | 'PENDING'
  | 'SUGGESTED'
  | 'DECIDED'
  | 'PROCURED'
  | 'FULFILLED'
  | 'PAID'
  | 'CASH_RECEIVED';

export interface ProjectItem {
  id: number;
  project_id: number;
  item_code: string;
  item_name: string | null;
  quantity: number;
  delivery_options: string[];  // Array of possible delivery dates
  status: ProjectItemStatus;
  external_purchase: boolean;
  description?: string | null;  // Item description/specifications
  file_path?: string | null;    // Attached file path
  file_name?: string | null;    // Attached file name
  decision_date: string | null;
  procurement_date: string | null;
  payment_date: string | null;
  invoice_submission_date: string | null;
  expected_cash_in_date: string | null;
  actual_cash_in_date: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ProjectItemCreate {
  project_id: number;
  master_item_id?: number;  // Reference to Items Master
  item_code: string;
  item_name?: string;
  quantity: number;
  delivery_options: string[];  // Array of possible delivery dates (at least 1)
  external_purchase?: boolean;
  description?: string;  // Project-specific context
}

export interface ProjectItemUpdate {
  item_code?: string;
  item_name?: string;
  quantity?: number;
  delivery_options?: string[];  // Array of possible delivery dates
  status?: ProjectItemStatus;
  external_purchase?: boolean;
  description?: string;  // Item description/specifications
  decision_date?: string;
  procurement_date?: string;
  payment_date?: string;
  invoice_submission_date?: string;
  expected_cash_in_date?: string;
  actual_cash_in_date?: string;
}

export interface PaymentTermsCash {
  type: 'cash';
  discount_percent?: number;
}

export interface PaymentTermsInstallments {
  type: 'installments';
  schedule: Array<{
    due_offset: number;
    percent: number;
  }>;
}

export type PaymentTerms = PaymentTermsCash | PaymentTermsInstallments;

export interface ProcurementOption {
  id: number;
  item_code: string;
  supplier_name: string;
  base_cost: number;
  lomc_lead_time: number;
  discount_bundle_threshold: number | null;
  discount_bundle_percent: number | null;
  payment_terms: PaymentTerms;
  created_at: string;
  updated_at: string | null;
  is_active: boolean;
}

export interface ProcurementOptionCreate {
  item_code: string;
  supplier_name: string;
  base_cost: number;
  lomc_lead_time?: number;
  discount_bundle_threshold?: number;
  discount_bundle_percent?: number;
  payment_terms: PaymentTerms;
}

export interface ProcurementOptionUpdate {
  item_code?: string;
  supplier_name?: string;
  base_cost?: number;
  lomc_lead_time?: number;
  discount_bundle_threshold?: number;
  discount_bundle_percent?: number;
  payment_terms?: PaymentTerms;
  is_active?: boolean;
}

export interface BudgetData {
  id: number;
  budget_date: string;
  available_budget: number;
  created_at: string;
  updated_at: string | null;
}

export interface BudgetDataCreate {
  budget_date: string;
  available_budget: number;
}

export interface BudgetDataUpdate {
  budget_date?: string;
  available_budget?: number;
}

export interface OptimizationResult {
  id: number;
  run_id: string;
  run_timestamp: string;
  project_id: number | null;
  item_code: string;
  procurement_option_id: number;
  purchase_time: number;
  delivery_time: number;
  quantity: number;
  final_cost: number;
}

export interface OptimizationRunRequest {
  max_time_slots?: number;
  time_limit_seconds?: number;
}

export interface OptimizationRunResponse {
  run_id: string;
  status: string;
  total_cost: number;
  items_optimized: number;
  execution_time_seconds: number;
  message?: string;
}

export interface DecisionFactorWeight {
  id: number;
  factor_name: string;
  weight: number;
  description: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface DecisionFactorWeightCreate {
  factor_name: string;
  weight: number;
  description?: string;
}

export interface DecisionFactorWeightUpdate {
  factor_name?: string;
  weight?: number;
  description?: string;
}

export interface DashboardStats {
  total_projects: number;
  total_items: number;
  total_procurement_options: number;
  total_budget: number;
  last_optimization: string | null;
  pending_items: number;
}

export interface ExcelImportResponse {
  success: boolean;
  imported_count: number;
  errors: string[];
  message: string;
}

// UI Types
export interface TableColumn {
  id: string;
  label: string;
  minWidth?: number;
  align?: 'right' | 'left' | 'center';
  format?: (value: any) => string;
}

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'email' | 'password' | 'select' | 'checkbox' | 'textarea';
  required?: boolean;
  options?: Array<{ value: any; label: string }>;
  multiline?: boolean;
  rows?: number;
}
