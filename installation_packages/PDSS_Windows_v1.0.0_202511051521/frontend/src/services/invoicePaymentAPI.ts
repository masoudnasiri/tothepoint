import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface InvoiceCreate {
  decision_id: number;
  invoice_number: string;
  invoice_date: string;
  invoice_amount: number;
  currency: string;
  due_date: string;
  payment_terms: string;
  is_final_invoice: boolean;
  notes?: string;
}

export interface InvoiceUpdate {
  invoice_number?: string;
  invoice_date?: string;
  invoice_amount?: number;
  currency?: string;
  due_date?: string;
  payment_terms?: string;
  status?: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  notes?: string;
}

export interface PaymentCreate {
  invoice_id: number;
  payment_date: string;
  payment_amount: number;
  currency: string;
  payment_method: 'cash' | 'bank_transfer' | 'check' | 'credit_card';
  reference_number: string;
  notes?: string;
}

export interface PaymentUpdate {
  payment_date?: string;
  payment_amount?: number;
  currency?: string;
  payment_method?: 'cash' | 'bank_transfer' | 'check' | 'credit_card';
  reference_number?: string;
  status?: 'pending' | 'completed' | 'failed' | 'cancelled';
  notes?: string;
}

export interface Invoice {
  id: number;
  decision_id: number;
  item_code: string;
  project_name: string;
  supplier_name: string;
  invoice_number: string;
  invoice_date: string;
  invoice_amount: number;
  currency: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  payment_terms: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: number;
  invoice_id: number;
  decision_id: number;
  item_code: string;
  project_name: string;
  supplier_name: string;
  payment_date: string;
  payment_amount: number;
  currency: string;
  payment_method: 'cash' | 'bank_transfer' | 'check' | 'credit_card';
  reference_number: string;
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface InvoicePaymentSummary {
  total_invoices: number;
  total_payments: number;
  paid_invoices: number;
  pending_invoices: number;
  overdue_invoices: number;
  total_invoice_amount: number;
  total_payment_amount: number;
  pending_payment_amount: number;
}

class InvoicePaymentAPI {
  private baseURL = `${API_BASE_URL}/api/invoice-payment`;

  // Invoice Management
  async listInvoices(params?: {
    search?: string;
    status?: string;
    project_id?: number;
    supplier_id?: number;
    start_date?: string;
    end_date?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await axios.get(`${this.baseURL}/invoices`, { params });
    return response;
  }

  async getInvoice(id: number) {
    const response = await axios.get(`${this.baseURL}/invoices/${id}`);
    return response;
  }

  async createInvoice(data: InvoiceCreate) {
    const response = await axios.post(`${this.baseURL}/invoices`, data);
    return response;
  }

  async updateInvoice(id: number, data: InvoiceUpdate) {
    const response = await axios.put(`${this.baseURL}/invoices/${id}`, data);
    return response;
  }

  async deleteInvoice(id: number) {
    const response = await axios.delete(`${this.baseURL}/invoices/${id}`);
    return response;
  }

  async markInvoiceAsSent(id: number) {
    const response = await axios.post(`${this.baseURL}/invoices/${id}/mark-sent`);
    return response;
  }

  async markInvoiceAsPaid(id: number) {
    const response = await axios.post(`${this.baseURL}/invoices/${id}/mark-paid`);
    return response;
  }

  // Payment Management
  async listPayments(params?: {
    search?: string;
    status?: string;
    project_id?: number;
    supplier_id?: number;
    start_date?: string;
    end_date?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await axios.get(`${this.baseURL}/payments`, { params });
    return response;
  }

  async getPayment(id: number) {
    const response = await axios.get(`${this.baseURL}/payments/${id}`);
    return response;
  }

  async createPayment(data: PaymentCreate) {
    const response = await axios.post(`${this.baseURL}/payments`, data);
    return response;
  }

  async updatePayment(id: number, data: PaymentUpdate) {
    const response = await axios.put(`${this.baseURL}/payments/${id}`, data);
    return response;
  }

  async deletePayment(id: number) {
    const response = await axios.delete(`${this.baseURL}/payments/${id}`);
    return response;
  }

  async markPaymentAsCompleted(id: number) {
    const response = await axios.post(`${this.baseURL}/payments/${id}/mark-completed`);
    return response;
  }

  async markPaymentAsFailed(id: number) {
    const response = await axios.post(`${this.baseURL}/payments/${id}/mark-failed`);
    return response;
  }

  // Summary and Analytics
  async getSummary() {
    const response = await axios.get(`${this.baseURL}/summary`);
    return response;
  }

  async getAnalytics(params?: {
    start_date?: string;
    end_date?: string;
    project_id?: number;
    supplier_id?: number;
  }) {
    const response = await axios.get(`${this.baseURL}/analytics`, { params });
    return response;
  }

  // Export functionality
  async exportInvoices(format: 'excel' | 'csv' = 'excel', params?: any) {
    const response = await axios.get(`${this.baseURL}/invoices/export`, {
      params: { format, ...params },
      responseType: 'blob'
    });
    return response;
  }

  async exportPayments(format: 'excel' | 'csv' = 'excel', params?: any) {
    const response = await axios.get(`${this.baseURL}/payments/export`, {
      params: { format, ...params },
      responseType: 'blob'
    });
    return response;
  }

  // Bulk operations
  async bulkUpdateInvoiceStatus(ids: number[], status: string) {
    const response = await axios.post(`${this.baseURL}/invoices/bulk-update-status`, {
      ids,
      status
    });
    return response;
  }

  async bulkDeleteInvoices(ids: number[]) {
    const response = await axios.post(`${this.baseURL}/invoices/bulk-delete`, {
      ids
    });
    return response;
  }

  async bulkUpdatePaymentStatus(ids: number[], status: string) {
    const response = await axios.post(`${this.baseURL}/payments/bulk-update-status`, {
      ids,
      status
    });
    return response;
  }

  async bulkDeletePayments(ids: number[]) {
    const response = await axios.post(`${this.baseURL}/payments/bulk-delete`, {
      ids
    });
    return response;
  }

  // Integration with decisions
  async getDecisionsForInvoice() {
    const response = await axios.get(`${this.baseURL}/decisions/available-for-invoice`);
    return response;
  }

  async getInvoicesForPayment() {
    const response = await axios.get(`${this.baseURL}/invoices/available-for-payment`);
    return response;
  }
}

export const invoicePaymentAPI = new InvoicePaymentAPI();
