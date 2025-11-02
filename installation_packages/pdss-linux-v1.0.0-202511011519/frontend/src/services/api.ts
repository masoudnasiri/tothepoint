import axios from 'axios';
/* eslint-disable @typescript-eslint/no-explicit-any */
// Minimal shim to satisfy type checking in environments without @types/node
declare const process: any;

// Configure axios
// Note: In development, the proxy in package.json handles routing to the backend
// In production, set REACT_APP_API_URL to the actual backend URL
const API_BASE_URL = process.env.REACT_APP_API_URL || '';
console.log('API Base URL:', API_BASE_URL || '(using proxy from package.json)');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login', credentials),
  me: () => api.get('/auth/me'),
  refresh: () => api.post('/auth/refresh'),
};

// Users API
export const usersAPI = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get('/users/', { params }),
  listPMs: () => api.get('/users/pm-list'),  // For PM assignment (PMO/Admin)
  get: (id: number) => api.get(`/users/${id}`),
  create: (user: any) => api.post('/users/', user),
  update: (id: number, user: any) => api.put(`/users/${id}`, user),
  delete: (id: number) => api.delete(`/users/${id}`),
};

// Projects API
export const projectsAPI = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get('/projects/', { params }),
  get: (id: number) => api.get(`/projects/${id}`),
  create: (project: any) => api.post('/projects/', project),
  update: (id: number, project: any) => api.put(`/projects/${id}`, project),
  delete: (id: number) => api.delete(`/projects/${id}`),
  assignUser: (assignment: { user_id: number; project_id: number }) =>
    api.post('/projects/assignments', assignment),
  removeUser: (userId: number, projectId: number) =>
    api.delete(`/projects/assignments/${userId}/${projectId}`),
  getUserAssignments: (userId: number) =>
    api.get(`/projects/assignments/${userId}`),
  getAssignments: (projectId: number) =>
    api.get(`/projects/${projectId}/assignments`),
};

// Items Master API
export const itemsMasterAPI = {
  list: (params?: { skip?: number; limit?: number; search?: string; category?: string; active_only?: boolean }) =>
    api.get('/items-master/', { params }),
  get: (id: number) => api.get(`/items-master/${id}`),
  create: (item: any) => api.post('/items-master/', item),
  update: (id: number, item: any) => api.put(`/items-master/${id}`, item),
  delete: (id: number) => api.delete(`/items-master/${id}`),
  previewCode: (company: string, itemName: string, model?: string) => {
    const params: any = { company, item_name: itemName };
    if (model) params.model = model;
    return api.get('/items-master/preview/code', { params });
  },
  getByCode: (itemCode: string) => api.get(`/items-master/search/by-code/${itemCode}`),
  // Sub-items nested under items master
  listSubItems: (itemId: number) => api.get(`/items-master/${itemId}/subitems`),
  createSubItem: (itemId: number, data: { name: string; description?: string; part_number?: string }) =>
    api.post(`/items-master/${itemId}/subitems`, data),
  updateSubItem: (itemId: number, subItemId: number, data: { name?: string; description?: string; part_number?: string }) =>
    api.put(`/items-master/${itemId}/subitems/${subItemId}`, data),
  deleteSubItem: (itemId: number, subItemId: number) =>
    api.delete(`/items-master/${itemId}/subitems/${subItemId}`),
};

// Project Items API
export const itemsAPI = {
  listByProject: (projectId: number, params?: { skip?: number; limit?: number }) =>
    api.get(`/items/project/${projectId}`, { params }),
  get: (id: number) => api.get(`/items/${id}`),
  create: (item: any) => api.post('/items/', item),
  update: (id: number, item: any) => api.put(`/items/${id}`, item),
  delete: (id: number) => api.delete(`/items/${id}`),
  finalize: (id: number, data: any) => api.put(`/items/${id}/finalize`, data),
  unfinalize: (id: number) => api.put(`/items/${id}/unfinalize`, {}),
  finalizeAll: (projectId: number) => api.put(`/items/project/${projectId}/finalize-all`, {}),
  listFinalized: (params?: { skip?: number; limit?: number }) =>
    api.get('/items/finalized', { params }),
};

// Project Phases API
export const phasesAPI = {
  listByProject: (projectId: number) =>
    api.get(`/phases/project/${projectId}`),
  get: (id: number) => api.get(`/phases/${id}`),
  create: (projectId: number, phase: any) => 
    api.post(`/phases/project/${projectId}`, phase),
  update: (id: number, phase: any) => api.put(`/phases/${id}`, phase),
  delete: (id: number) => api.delete(`/phases/${id}`),
};

// Decision Factor Weights API
export const weightsAPI = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get('/weights/', { params }),
  get: (id: number) => api.get(`/weights/${id}`),
  create: (weight: any) => api.post('/weights/', weight),
  update: (id: number, weight: any) => api.put(`/weights/${id}`, weight),
  delete: (id: number) => api.delete(`/weights/${id}`),
};

// Finalized Decisions API
export const decisionsAPI = {
  list: (params?: { 
    skip?: number; 
    limit?: number; 
    run_id?: string; 
    project_id?: number;
    search?: string;
    status?: string;
  }) => api.get('/decisions/', { params }),
  count: (params?: { 
    run_id?: string; 
    project_id?: number;
    search?: string;
    status?: string;
  }) => api.get('/decisions/count', { params }),
  summary: (params?: { 
    run_id?: string; 
    project_id?: number;
    search?: string;
  }) => api.get('/decisions/summary', { params }),
  get: (id: number) => api.get(`/decisions/${id}`),
  save: (decisions: any[]) => api.post('/decisions/', decisions),
  saveBatch: (runId: string, itemIds: number[], optionIds: number[]) =>
    api.post('/decisions/batch', { 
      run_id: runId, 
      project_item_ids: itemIds, 
      procurement_option_ids: optionIds 
    }),
  saveProposal: (proposalData: {
    run_id: string;
    proposal_name: string;
    decisions: any[];
  }) => api.post('/decisions/save-proposal', proposalData),
  finalize: (request: { decision_ids: number[]; finalize_all?: boolean }) =>
    api.post('/decisions/finalize', request),
  enterActualInvoice: (decisionId: number, data: {
    actual_invoice_issue_date: string;
    actual_invoice_amount: number;
    actual_invoice_received_date?: string;
    notes?: string;
  }) => api.post(`/decisions/${decisionId}/actual-invoice`, data),
  enterActualPayment: (decisionId: number, data: {
    actual_payment_amount: number;
    actual_payment_date: string;
    actual_payment_installments?: Array<{ date: string; amount: number }>;
    notes?: string;
  }) => api.post(`/decisions/${decisionId}/actual-payment`, data),
  updateStatus: (id: number, statusUpdate: { status: string; notes?: string }) =>
    api.put(`/decisions/${id}/status`, statusUpdate),
  update: (id: number, decision: any) => api.put(`/decisions/${id}`, decision),
  delete: (id: number) => api.delete(`/decisions/${id}`),
  getBudgetAnalysis: (params?: { 
    project_ids?: string; 
    start_date?: string; 
    end_date?: string;
  }) => api.get('/decisions/budget-analysis', { params }),
};

// Analytics API
export const analyticsAPI = {
  getEVA: (projectId: number | 'all', currencyView: string = 'unified') => 
    projectId === 'all' ? api.get('/analytics/portfolio/eva', { params: { currency_view: currencyView } }) : api.get(`/analytics/eva/${projectId}`, { params: { currency_view: currencyView } }),
  getCashflowForecast: (projectId: number | 'all', monthsAhead: number = 12, currencyView: string = 'unified') => 
    projectId === 'all' 
      ? api.get('/analytics/portfolio/cashflow-forecast', { params: { months_ahead: monthsAhead, currency_view: currencyView } })
      : api.get(`/analytics/cashflow-forecast/${projectId}`, { params: { months_ahead: monthsAhead, currency_view: currencyView } }),
  getRisk: (projectId: number | 'all') => 
    projectId === 'all' ? api.get('/analytics/portfolio/risk') : api.get(`/analytics/risk/${projectId}`),
  getAllProjectsSummary: () => api.get('/analytics/all-projects-summary'),
  getItemFollowUp: (projectId: number | 'all') => 
    projectId === 'all' ? api.get('/analytics/portfolio/item-follow-up') : api.get(`/analytics/item-follow-up/${projectId}`),
};

// Procurement API
export const procurementAPI = {
  getItemCodes: () => api.get('/procurement/item-codes'),
  getItemsWithDetails: () => api.get('/procurement/items-with-details'),
  getSuppliers: () => api.get('/procurement/suppliers'),
  listOptions: (params?: { skip?: number; limit?: number; item_code?: string }) =>
    api.get('/procurement/options', { params }),
  listByItemCode: (itemCode: string) =>
    api.get(`/procurement/options/${itemCode}`),
  listByProjectItem: (projectItemId: number) =>
    api.get(`/procurement/options/by-project-item/${projectItemId}`),
  get: (id: number) => api.get(`/procurement/option/${id}`),
  create: (option: any) => api.post('/procurement/options', option),
  update: (id: number, option: any) => api.put(`/procurement/option/${id}`, option),
  delete: (id: number) => api.delete(`/procurement/option/${id}`),
};

// Finance API
export const financeAPI = {
  getDashboard: () => api.get('/finance/dashboard'),
  listBudget: () => api.get('/finance/budget'),
  createBudget: (budget: any) => api.post('/finance/budget', budget),
  getBudget: (timeSlot: number) => api.get(`/finance/budget/${timeSlot}`),
  updateBudget: (timeSlot: number, budget: any) =>
    api.put(`/finance/budget/${timeSlot}`, budget),
  deleteBudget: (timeSlot: number) => api.delete(`/finance/budget/${timeSlot}`),
  runOptimization: (request: any) => api.post('/finance/optimize', request),
  runEnhancedOptimization: (request: any, queryParams?: string) => 
    api.post(`/finance/optimize-enhanced?${queryParams || ''}`, request),
  getSolverInfo: () => api.get('/finance/solver-info'),
  getOptimizationAnalysis: (runId: string) => api.get(`/finance/optimization-analysis/${runId}`),
  listOptimizationRuns: (params?: { skip?: number; limit?: number }) =>
    api.get('/finance/optimization-runs', { params }),
  getOptimizationRun: (runId: string) => api.get(`/finance/optimization-run/${runId}`),
  listResults: (params?: { run_id?: string; skip?: number; limit?: number }) =>
    api.get('/finance/optimization-results', { params }),
  getResults: (runId: string) => api.get(`/finance/optimization-results/${runId}`),
  getLatestRun: () => api.get('/finance/latest-optimization'),
  deleteOptimizationResults: (runId: string) => api.delete(`/finance/optimization-results/${runId}`),
};

// Excel API
export const excelAPI = {
  // Project Items
  downloadItemsTemplate: () => api.get('/excel/templates/items', { responseType: 'blob' }),
  exportItems: (projectId?: number) =>
    api.get('/excel/export/items', { 
      params: projectId ? { project_id: projectId } : {},
      responseType: 'blob'
    }),
  importItems: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/excel/import/items', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // Procurement Options
  downloadProcurementTemplate: () => 
    api.get('/excel/templates/procurement', { responseType: 'blob' }),
  exportProcurement: (itemCode?: string) =>
    api.get('/excel/export/procurement', { 
      params: itemCode ? { item_code: itemCode } : {},
      responseType: 'blob'
    }),
  importProcurement: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/excel/import/procurement', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // Budget Data
  downloadBudgetTemplate: () => 
    api.get('/excel/templates/budget', { responseType: 'blob' }),
  exportBudget: () => api.get('/excel/export/budget', { responseType: 'blob' }),
  importBudget: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/excel/import/budget', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Dashboard API
export const dashboardAPI = {
  getCashflow: (options?: { startDate?: string; endDate?: string; forecast_type?: string; project_ids?: string; currency_view?: string }) => {
    const params = new URLSearchParams();
    if (options?.startDate) params.append('start_date', options.startDate);
    if (options?.endDate) params.append('end_date', options.endDate);
    if (options?.forecast_type) params.append('forecast_type', options.forecast_type);
    if (options?.project_ids) params.append('project_ids', options.project_ids);
    if (options?.currency_view) params.append('currency_view', options.currency_view);
    return api.get(`/dashboard/cashflow${params.toString() ? `?${params.toString()}` : ''}`);
  },
  getSummary: () => api.get('/dashboard/summary'),
  exportCashflow: (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return api.get(`/dashboard/cashflow/export${params.toString() ? `?${params.toString()}` : ''}`, {
      responseType: 'blob'
    });
  },
};

// Delivery Options API
export const deliveryOptionsAPI = {
  listByItem: (projectItemId: number) =>
    api.get(`/delivery-options/item/${projectItemId}`),
  get: (id: number) => api.get(`/delivery-options/${id}`),
  create: (option: any) => api.post('/delivery-options/', option),
  update: (id: number, option: any) => api.put(`/delivery-options/${id}`, option),
  delete: (id: number) => api.delete(`/delivery-options/${id}`),
  getByItemCode: (itemCode: string, projectId?: number) => {
    const url = projectId 
      ? `/delivery-options/by-item-code/${itemCode}?project_id=${projectId}`
      : `/delivery-options/by-item-code/${itemCode}`;
    return api.get(url);
  },
};

// Procurement Plan & Delivery Tracking API
export const procurementPlanAPI = {
  list: (params?: { 
    status_filter?: string; 
    project_id?: number;
    page?: number;
    limit?: number;
    search?: string;
    invoice_status?: string;
    payment_status?: string;
    start_date?: string;
    end_date?: string;
  }) =>
    api.get('/procurement-plan/', { params }),
  get: (decisionId: number) => api.get(`/procurement-plan/${decisionId}`),
  confirmDelivery: (decisionId: number, data: any) =>
    api.post(`/procurement-plan/${decisionId}/confirm-delivery`, data),
  acceptDelivery: (decisionId: number, data: any) =>
    api.post(`/procurement-plan/${decisionId}/accept-delivery`, data),
  enterInvoice: (decisionId: number, data: any) =>
    api.post(`/procurement-plan/${decisionId}/enter-invoice`, data),
  export: () =>
    api.get('/procurement-plan/export/excel', { responseType: 'blob' }),
};

// Reports & Analytics API
export const reportsAPI = {
  getData: (params?: {
    start_date?: string;
    end_date?: string;
    project_ids?: string;
    supplier_names?: string;
  }) => api.get('/reports/', { params: { ...params, currency_view: 'unified' } }),
  export: (params?: {
    start_date?: string;
    end_date?: string;
    project_ids?: string;
    supplier_names?: string;
  }) => api.get('/reports/export/excel', { params: { ...params, currency_view: 'unified' }, responseType: 'blob' }),
  getProjects: () => api.get('/reports/filters/projects'),
  getSuppliers: () => api.get('/reports/filters/suppliers'),
  getDataSummary: () => api.get('/reports/data-summary'),
};

// Currency Management API
export const currencyAPI = {
  // Currency management
  list: (includeInactive = false) => api.get('/currencies/', { params: { include_inactive: includeInactive } }),
  create: (currency: any) => api.post('/currencies/', currency),
  get: (id: number) => api.get(`/currencies/${id}`),
  update: (id: number, currency: any) => api.put(`/currencies/${id}`, currency),
  delete: (id: number) => api.delete(`/currencies/${id}`),
  getBaseCurrency: () => api.get('/currencies/base-currency'),
  
  // Exchange rate management (NEW structure)
  listExchangeRates: (fromCurrency?: string, toCurrency?: string, startDate?: string, endDate?: string) =>
    api.get('/currencies/rates/list', {
      params: { from_currency: fromCurrency, to_currency: toCurrency, start_date: startDate, end_date: endDate }
    }),
  addExchangeRate: (date: string, fromCurrency: string, toCurrency: string, rate: number) =>
    api.post('/currencies/rates/add', null, {
      params: { date_str: date, from_currency: fromCurrency, to_currency: toCurrency, rate }
    }),
  updateExchangeRateValue: (rateId: number, rate: number) =>
    api.put(`/currencies/rates/${rateId}`, null, {
      params: { rate }
    }),
  deleteExchangeRate: (rateId: number) => {
    console.log('API: deleteExchangeRate called with rateId:', rateId);
    console.log('API: Making DELETE request to:', `/currencies/rates/${rateId}`);
    return api.delete(`/currencies/rates/${rateId}`);
  },
  
  // OLD Exchange rate management (kept for backward compatibility)
  getExchangeRates: (currencyId: number, startDate?: string, endDate?: string) => 
    api.get(`/currencies/${currencyId}/exchange-rates`, { 
      params: { start_date: startDate, end_date: endDate } 
    }),
  createExchangeRate: (currencyId: number, rate: any) => 
    api.post(`/currencies/${currencyId}/exchange-rates`, rate),
  updateExchangeRate: (rateId: number, rate: any) => 
    api.put(`/currencies/exchange-rates/${rateId}`, rate),
  
  // Currency conversion
  convert: (amount: number, fromCurrencyId: number, toCurrencyId: number, conversionDate?: string) =>
    api.post('/currencies/convert', null, {
      params: {
        amount,
        from_currency_id: fromCurrencyId,
        to_currency_id: toCurrencyId,
        conversion_date: conversionDate
      }
    }),

  // BrsApi Currency conversion
  brsApi: {
    getCurrencies: () => api.get('/brs-api/currencies'),
    getCurrencyRate: (symbol: string) => api.get(`/brs-api/currencies/${symbol}`),
    convert: (amount: number, fromCurrency: string, toCurrency: string, forceRefresh?: boolean) =>
      api.post('/brs-api/convert', null, {
        params: {
          amount,
          from_currency: fromCurrency,
          to_currency: toCurrency,
          force_refresh: forceRefresh
        }
      }),
    getSupportedCurrencies: () => api.get('/brs-api/supported-currencies'),
    healthCheck: () => api.get('/brs-api/health')
  },
};

// Supplier Payments API
export const supplierPaymentsAPI = {
  // List supplier payments with filtering and pagination
  list: (params?: {
    skip?: number;
    limit?: number;
    project_id?: number;
    supplier_name?: string;
    item_code?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  }) => api.get('/supplier-payments/', { params }),
  
  // Get specific supplier payment
  get: (id: number) => api.get(`/supplier-payments/${id}`),
  
  // Create new supplier payment
  create: (data: {
    decision_id: number;
    supplier_name: string;
    item_code: string;
    project_id: number;
    payment_date: string;
    payment_amount: number;
    currency: string;
    payment_method: string;
    reference_number?: string;
    notes?: string;
    status?: string;
  }) => api.post('/supplier-payments/', data),
  
  // Update supplier payment
  update: (id: number, data: {
    supplier_name?: string;
    payment_date?: string;
    payment_amount?: number;
    currency?: string;
    payment_method?: string;
    reference_number?: string;
    notes?: string;
    status?: string;
  }) => api.put(`/supplier-payments/${id}`, data),
  
  // Delete supplier payment
  delete: (id: number) => api.delete(`/supplier-payments/${id}`),
  
  // Get payments for a specific decision
  getByDecision: (decisionId: number) => api.get(`/supplier-payments/decisions/${decisionId}/payments`),
};

// Suppliers API
export const suppliersAPI = {
  // List suppliers with filters and pagination
  list: (params?: {
    page?: number;
    size?: number;
    search?: string;
    status?: string;
    compliance_status?: string;
    risk_level?: string;
    country?: string;
  }) => api.get('/suppliers/', { params }),
  
  // Get supplier by ID
  get: (id: number) => api.get(`/suppliers/${id}`),
  
  // Create supplier
  create: (data: any) => api.post('/suppliers/', data),
  
  // Update supplier
  update: (id: number, data: any) => api.put(`/suppliers/${id}`, data),
  
  // Delete supplier
  delete: (id: number) => api.delete(`/suppliers/${id}`),
  
  // Supplier contacts
  listContacts: (supplierId: number, params?: { page?: number; size?: number }) =>
    api.get(`/suppliers/${supplierId}/contacts`, { params }),
  
  // List all contacts with filters and pagination
  listAllContacts: (params?: {
    page?: number;
    size?: number;
    search?: string;
    supplier_id?: number;
  }) => api.get('/suppliers/contacts', { params }),
  
  createContact: (supplierId: number, data: any) =>
    api.post(`/suppliers/${supplierId}/contacts`, data),
  
  updateContact: (supplierId: number, contactId: number, data: any) =>
    api.put(`/suppliers/${supplierId}/contacts/${contactId}`, data),
  
  deleteContact: (supplierId: number, contactId: number) =>
    api.delete(`/suppliers/${supplierId}/contacts/${contactId}`),
  
  // Supplier documents
  listDocuments: (supplierId: number, params?: { page?: number; size?: number }) =>
    api.get(`/suppliers/${supplierId}/documents`, { params }),
  
  uploadDocument: (supplierId: number, formData: FormData) =>
    api.post(`/suppliers/${supplierId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  downloadDocument: (supplierId: number, documentId: number) =>
    api.get(`/suppliers/${supplierId}/documents/${documentId}/download`, {
      responseType: 'blob'
    }),
  
  updateDocument: (supplierId: number, documentId: number, data: any) =>
    api.put(`/suppliers/${supplierId}/documents/${documentId}`, data),
  
  deleteDocument: (supplierId: number, documentId: number) =>
    api.delete(`/suppliers/${supplierId}/documents/${documentId}`),
  
  // Utility endpoints
  getCategories: () => api.get('/suppliers/categories/list'),
  getIndustries: () => api.get('/suppliers/industries/list'),
  getCountries: () => api.get('/suppliers/countries/list'),
};

export default api;
