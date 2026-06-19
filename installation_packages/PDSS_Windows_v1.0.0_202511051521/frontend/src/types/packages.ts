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
}

