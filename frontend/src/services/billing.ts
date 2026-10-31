/**
 * Module 3 API Services: Invoices, Payments, Billing, Finance
 */
import { apiClient } from './api'
import {
  Invoice,
  InvoiceWithDetails,
  CreateInvoicePayload,
  Payment,
  PaymentWithDetails,
  CreatePaymentPayload,
  BillingJob,
  FinanceSummary,
  OutstandingBalance,
  PaginatedResponse,
  ApiResponse,
} from '@/types'

// ==================== INVOICES ====================

export const invoiceService = {
  /**
   * Get list of invoices with optional filters
   */
  async getInvoices(params?: {
    page?: number
    pageSize?: number
    status?: string
    customer_id?: string
    subscription_id?: string
    from_date?: string
    to_date?: string
  }): Promise<PaginatedResponse<Invoice>> {
    const response = await apiClient.get<Invoice[]>('/invoices', { params })
    return response as PaginatedResponse<Invoice>
  },

  /**
   * Get single invoice by ID with line items
   */
  async getInvoice(id: string): Promise<ApiResponse<InvoiceWithDetails>> {
    return apiClient.get<InvoiceWithDetails>(`/invoices/${id}`)
  },

  /**
   * Create a new invoice
   */
  async createInvoice(payload: CreateInvoicePayload): Promise<ApiResponse<Invoice>> {
    return apiClient.post<Invoice>('/invoices', payload)
  },

  /**
   * Issue an invoice (draft → open)
   */
  async issueInvoice(id: string): Promise<ApiResponse<Invoice>> {
    return apiClient.post<Invoice>(`/invoices/${id}/issue`)
  },

  /**
   * Void an invoice
   */
  async voidInvoice(id: string, reason?: string): Promise<ApiResponse<Invoice>> {
    return apiClient.post<Invoice>(`/invoices/${id}/void`, { reason })
  },

  /**
   * Get payment history for an invoice
   */
  async getInvoicePayments(id: string): Promise<ApiResponse<Payment[]>> {
    return apiClient.get<Payment[]>(`/invoices/${id}/payments`)
  },

  /**
   * Download invoice PDF
   */
  async downloadInvoicePdf(id: string): Promise<Blob> {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'}/invoices/${id}/pdf`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('Failed to download PDF')
    }
    
    return response.blob()
  },
}

// ==================== PAYMENTS ====================

export const paymentService = {
  /**
   * Get list of payments with optional filters
   */
  async getPayments(params?: {
    page?: number
    pageSize?: number
    status?: string
    customer_id?: string
    invoice_id?: string
    payment_method?: string
    from_date?: string
    to_date?: string
  }): Promise<PaginatedResponse<Payment>> {
    const response = await apiClient.get<Payment[]>('/payments', { params })
    return response as PaginatedResponse<Payment>
  },

  /**
   * Get single payment by ID
   */
  async getPayment(id: string): Promise<ApiResponse<PaymentWithDetails>> {
    return apiClient.get<PaymentWithDetails>(`/payments/${id}`)
  },

  /**
   * Record a new payment
   */
  async recordPayment(payload: CreatePaymentPayload): Promise<ApiResponse<Payment>> {
    return apiClient.post<Payment>('/payments', payload)
  },

  /**
   * Reverse a payment
   */
  async reversePayment(id: string, reason?: string): Promise<ApiResponse<Payment>> {
    return apiClient.post<Payment>(`/payments/${id}/reverse`, { reason })
  },
}

// ==================== BILLING ====================

export const billingService = {
  /**
   * Trigger manual billing run
   */
  async runBilling(asOfDate?: string): Promise<ApiResponse<BillingJob>> {
    return apiClient.post<BillingJob>('/billing/run', { as_of_date: asOfDate })
  },

  /**
   * Get billing job history
   */
  async getBillingJobs(params?: {
    page?: number
    pageSize?: number
    status?: string
  }): Promise<PaginatedResponse<BillingJob>> {
    const response = await apiClient.get<BillingJob[]>('/billing/jobs', { params })
    return response as PaginatedResponse<BillingJob>
  },

  /**
   * Get billing job details
   */
  async getBillingJob(id: number): Promise<ApiResponse<BillingJob>> {
    return apiClient.get<BillingJob>(`/billing/jobs/${id}`)
  },
}

// ==================== FINANCE ====================

export const financeService = {
  /**
   * Get financial summary
   */
  async getSummary(): Promise<ApiResponse<FinanceSummary>> {
    return apiClient.get<FinanceSummary>('/finance/summary')
  },

  /**
   * Get outstanding balances per customer
   */
  async getOutstandingBalances(params?: {
    page?: number
    pageSize?: number
    customer_id?: string
  }): Promise<PaginatedResponse<OutstandingBalance>> {
    const response = await apiClient.get<OutstandingBalance[]>('/finance/outstanding-balances', { params })
    return response as PaginatedResponse<OutstandingBalance>
  },
}
