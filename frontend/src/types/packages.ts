/**
 * Procurement Package Types (Phase 3)
 */

export interface ProcurementPackage {
  id: number;
  project_item_id: number;
  package_name: string | null;
  package_type: 'FULL' | 'PARTIAL' | 'CUSTOM';
  supplier_id: number | null;
  description: string | null;
  is_active: boolean;
  is_finalized?: boolean;
  status?: 'DRAFT' | 'FINALIZED' | 'SENT_TO_OPTIMIZATION' | 'INACTIVE';
  is_locked_for_optimization?: boolean;
  main_item_quantity?: number | null;
  supplier?: {
    id: number;
    supplier_id: string;
    company_name: string;
  } | null;
  subitems?: Array<{
    id: number;
    package_id: number;
    project_item_subitem_id: number;
    quantity_covered: number;
    is_fully_covered: boolean;
    coverage_percentage?: number | null;
  }>;
  created_at: string;
  updated_at: string | null;
  created_by_id: number | null;
}

export interface ProcurementPackageCreate {
  project_item_id: number;
  package_name?: string | null;
  package_type: 'FULL' | 'PARTIAL' | 'CUSTOM';
  supplier_id?: number | null;
  description?: string | null;
  is_active?: boolean;
  is_finalized?: boolean;
}

