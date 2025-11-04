// API Types
export interface User {
  id: number;
  username: string;
  role: 'admin' | 'pmo' | 'pm' | 'procurement' | 'finance';
  created_at: string;
  is_active: boolean;
}

// Currency Types
export interface Currency {
  id: number;
  code: string;
  name: string;
  symbol: string;
  is_base_currency: boolean;
  is_active: boolean;
  decimal_places: number;
  created_at: string;
  updated_at?: string;
  created_by_id?: number;
}

export interface ExchangeRate {
  id: number;
  currency_id: number;
  rate_date: string;
  rate_to_base: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  created_by_id?: number;
  currency?: Currency;
}

export interface CurrencyWithRates extends Currency {
  latest_rate?: ExchangeRate;
  rate_to_base?: number;
}

export interface CurrencyCreate {
  code: string;
  name: string;
  symbol: string;
  is_base_currency?: boolean;
  is_active?: boolean;
  decimal_places?: number;
}

export interface CurrencyUpdate {
  name?: string;
  symbol?: string;
  is_base_currency?: boolean;
  is_active?: boolean;
  decimal_places?: number;
}

export interface ExchangeRateCreate {
  currency_id: number;
  rate_date: string;
  rate_to_base: number;
  is_active?: boolean;
}

export interface CurrencyConversion {
  original_amount: number;
  converted_amount: number;
  from_currency_id: number;
  to_currency_id: number;
  conversion_date: string;
  from_rate: number;
  to_rate: number;
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
  part_number?: string;
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
  part_number?: string;
  specifications?: any;
  category?: string;
  unit?: string;
  description?: string;
}

export interface ItemMasterUpdate {
  company?: string;
  item_name?: string;
  model?: string;
  part_number?: string;
  specifications?: any;
  category?: string;
  unit?: string;
  description?: string;
  is_active?: boolean;
}

// Sub-items under Items Master
export interface ItemSubItem {
  id: number;
  item_master_id: number;
  name: string;
  description?: string;
  part_number?: string;
}

export interface ItemSubItemCreate {
  name: string;
  description?: string;
  part_number?: string;
}

export interface ItemSubItemUpdate {
  name?: string;
  description?: string;
  part_number?: string;
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
  is_finalized: boolean;
  finalized_by: number | null;
  finalized_at: string | null;
  created_at: string;
  updated_at: string | null;
  // Procurement workflow fields (computed from backend)
  procurement_options_count?: number;
  has_finalized_decision?: boolean;
  // Sub-items breakdown returned from backend
  sub_items?: Array<{ sub_item_id: number; name?: string; part_number?: string; quantity: number }>;
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
  sub_items?: Array<{ sub_item_id: number; quantity: number }>; // quantities per sub-item
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
  sub_items?: Array<{ sub_item_id: number; quantity: number }>;
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
  currency_id: number;
  lomc_lead_time: number;
  purchase_date?: string; // When to place the order (purchase date)
  expected_delivery_date?: string; // Expected delivery date from supplier
  delivery_option_id?: number; // Add delivery option ID field
  discount_bundle_threshold: number | null;
  discount_bundle_percent: number | null;
  payment_terms: PaymentTerms;
  created_at: string;
  updated_at: string | null;
  is_active: boolean;
  is_finalized: boolean;
}

export interface ProcurementOptionCreate {
  item_code: string;
  supplier_name: string;
  base_cost: number;
  currency_id: number;
  lomc_lead_time?: number;
  discount_bundle_threshold?: number;
  discount_bundle_percent?: number;
  payment_terms: PaymentTerms;
  is_finalized?: boolean;
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
  is_finalized?: boolean;
}

export interface BudgetData {
  id: number;
  budget_date: string;
  available_budget: number;
  multi_currency_budget?: { [currencyCode: string]: number };
  created_at: string;
  updated_at: string | null;
}

export interface BudgetDataCreate {
  budget_date: string;
  available_budget: number;
  multi_currency_budget?: { [currencyCode: string]: number };
}

export interface BudgetDataUpdate {
  budget_date?: string;
  available_budget?: number;
  multi_currency_budget?: { [currencyCode: string]: number };
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

// Procurement Plan & Delivery Tracking Types
export type DeliveryStatus = 
  | 'AWAITING_DELIVERY'
  | 'CONFIRMED_BY_PROCUREMENT'
  | 'DELIVERY_COMPLETE';

export interface ProcurementPlanItem {
  id: number;
  item_code: string;
  item_name?: string;
  item_description?: string;
  project_id: number;
  project_name?: string;
  project_code?: string;
  quantity: number;
  delivery_date: string;
  delivery_status: DeliveryStatus;
  actual_delivery_date?: string;
  serial_number?: string;
  customer_delivery_date?: string;
  
  // Procurement Team fields (not visible to PM)
  final_cost?: number;
  final_cost_currency?: string;
  purchase_date?: string;
  supplier_name?: string;
  procurement_option_id?: number;
  is_correct_item_confirmed?: boolean;
  procurement_delivery_notes?: string;
  procurement_confirmed_at?: string;
  procurement_confirmed_by_id?: number;
  
  // Invoice fields (Procurement/Finance only)
  actual_invoice_issue_date?: string;
  actual_invoice_amount?: number;
  actual_invoice_currency?: string;
  actual_invoice_received_date?: string;
  invoice_entered_by_id?: number;
  invoice_entered_at?: string;
  
  // Payment fields (Finance only)
  actual_payment_amount?: number;
  actual_payment_currency?: string;
  actual_payment_date?: string;
  payment_entered_by_id?: number;
  payment_entered_at?: string;
  
  // Payment In and Payment Out statuses
  payment_in_status?: 'not_paid' | 'partially_paid' | 'fully_paid';
  payment_out_status?: 'not_paid' | 'partially_paid' | 'fully_paid';
  
  // PM fields
  is_accepted_by_pm?: boolean;
  pm_acceptance_notes?: string;
  pm_accepted_at?: string;
  pm_accepted_by_id?: number;
  
  // User names (when loaded)
  procurement_confirmed_by_name?: string;
  pm_accepted_by_name?: string;
}

export interface ProcurementDeliveryConfirmation {
  actual_delivery_date: string;
  is_correct_item: boolean;
  serial_number?: string;
  delivery_notes?: string;
}

export interface PMDeliveryAcceptance {
  is_accepted_for_project: boolean;
  customer_delivery_date?: string;
  acceptance_notes?: string;
}

export interface ActualInvoiceData {
  actual_invoice_issue_date: string;
  actual_invoice_amount: number;
  actual_invoice_received_date?: string;
  notes?: string;
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

// Reports & Analytics Types
export interface ReportsFilters {
  start_date?: string;
  end_date?: string;
  project_ids?: number[];
  supplier_ids?: number[];
}

export interface CashFlowData {
  dates: string[];
  inflow: number[];
  outflow: number[];
  net_flow: number[];
  cumulative_balance: number[];
}

export interface BudgetVsActual {
  project_name: string;
  planned_cost: number;
  actual_cost: number;
  variance_amount: number;
  variance_percent: number;
}

export interface FinancialSummaryData {
  cash_flow: CashFlowData;
  budget_vs_actual: BudgetVsActual[];
}

export interface EVMPerformanceData {
  dates: string[];
  pv: number[];
  ev: number[];
  ac: number[];
}

export interface KPITrendsData {
  dates: string[];
  cpi: number[];
  spi: number[];
}

export interface ProjectKPI {
  project_name: string;
  pv: number;
  ev: number;
  ac: number;
  sv: number;
  cv: number;
  spi: number;
  cpi: number;
  eac: number;
  etc: number;
}

export interface EVMAnalyticsData {
  evm_performance: EVMPerformanceData;
  kpi_trends: KPITrendsData;
  project_kpis: ProjectKPI[];
}

export interface DelayForecast {
  p50: number;
  p90: number;
}

export interface PaymentDelayHistogram {
  delay_bucket: number;
  count: number;
}

export interface RiskItem {
  item_name: string;
  project_name: string;
  cost_variance: number;
  schedule_delay: number;
  risk_score?: number;
}

export interface RiskForecastsData {
  delay_forecast: DelayForecast;
  payment_delay_histogram: PaymentDelayHistogram[];
  top_risk_items: RiskItem[];
}

export interface SupplierScorecard {
  supplier_name: string;
  total_orders: number;
  on_time_delivery_rate: number;
  avg_cost_variance_percent: number;
}

export interface ProcurementCycleTime {
  cycle_time_bucket: number;
  count: number;
}

export interface OperationalPerformanceData {
  supplier_scorecard: SupplierScorecard[];
  procurement_cycle_time: ProcurementCycleTime[];
}

export interface ReportsData {
  financial_summary: FinancialSummaryData;
  evm_analytics: EVMAnalyticsData;
  risk_forecasts: RiskForecastsData;
  operational_performance: OperationalPerformanceData;
}

export interface FilterOption {
  id: number;
  name: string;
  code?: string;
}

export interface DataSummary {
  overall: {
    total_locked_items: number;
    total_projects: number;
    total_suppliers: number;
    data_quality_score: number;
    quality_status: string;
  };
  actuals_data: {
    with_invoice: { count: number; percent: number };
    with_payment: { count: number; percent: number };
    with_pm_acceptance: { count: number; percent: number };
    with_delivery_complete: { count: number; percent: number };
    cashflow_inflow_events: number;
  };
  report_readiness: {
    financial_summary: string;
    evm_analytics: string;
    risk_forecasts: string;
    operational_performance: string;
  };
  recommendations: Array<{
    priority: string;
    action: string;
    current: number;
    target: number;
    impact: string;
  } | null>;
}
