/**
 * Module 2 API Services: Customers, Products, Plans, Quotations, Subscriptions
 */
import { apiClient } from './api'
import {
  Customer,
  CreateCustomerPayload,
  UpdateCustomerPayload,
  Product,
  ProductWithPlans,
  CreateProductPayload,
  UpdateProductPayload,
  Plan,
  PlanWithProduct,
  CreatePlanPayload,
  UpdatePlanPayload,
  Quotation,
  QuotationWithDetails,
  CreateQuotationPayload,
  UpdateQuotationPayload,
  Subscription,
  SubscriptionWithDetails,
  CreateSubscriptionPayload,
  UpdateSubscriptionPayload,
  CancelSubscriptionPayload,
  PaginatedResponse,
  ApiResponse,
} from '@/types'

// ==================== CUSTOMERS ====================

export const customerService = {
  /**
   * Get list of customers with optional filters
   */
  async getCustomers(params?: {
    page?: number
    pageSize?: number
    status?: string
    search?: string
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }): Promise<PaginatedResponse<Customer>> {
    const response = await apiClient.get<Customer[]>('/customers', { params })
    return response as PaginatedResponse<Customer>
  },

  /**
   * Get single customer by ID
   */
  async getCustomer(id: string): Promise<ApiResponse<Customer>> {
    return apiClient.get<Customer>(`/customers/${id}`)
  },

  /**
   * Create a new customer
   */
  async createCustomer(payload: CreateCustomerPayload): Promise<ApiResponse<Customer>> {
    return apiClient.post<Customer>('/customers', payload)
  },

  /**
   * Update an existing customer
   */
  async updateCustomer(id: string, payload: UpdateCustomerPayload): Promise<ApiResponse<Customer>> {
    return apiClient.patch<Customer>(`/customers/${id}`, payload)
  },

  /**
   * Deactivate a customer
   */
  async deactivateCustomer(id: string): Promise<ApiResponse<Customer>> {
    return apiClient.post<Customer>(`/customers/${id}/deactivate`)
  },
}

// ==================== PRODUCTS ====================

export const productService = {
  /**
   * Get list of products with optional filters
   */
  async getProducts(params?: {
    page?: number
    pageSize?: number
    status?: string
    search?: string
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }): Promise<PaginatedResponse<Product>> {
    const response = await apiClient.get<Product[]>('/products', { params })
    return response as PaginatedResponse<Product>
  },

  /**
   * Get single product by ID with associated plans
   */
  async getProduct(id: string): Promise<ApiResponse<ProductWithPlans>> {
    return apiClient.get<ProductWithPlans>(`/products/${id}`)
  },

  /**
   * Create a new product
   */
  async createProduct(payload: CreateProductPayload): Promise<ApiResponse<Product>> {
    return apiClient.post<Product>('/products', payload)
  },

  /**
   * Update an existing product
   */
  async updateProduct(id: string, payload: UpdateProductPayload): Promise<ApiResponse<Product>> {
    return apiClient.patch<Product>(`/products/${id}`, payload)
  },

  /**
   * Deactivate a product
   */
  async deactivateProduct(id: string): Promise<ApiResponse<Product>> {
    return apiClient.post<Product>(`/products/${id}/deactivate`)
  },
}

// ==================== PLANS ====================

export const planService = {
  /**
   * Get list of plans with optional filters
   */
  async getPlans(params?: {
    page?: number
    pageSize?: number
    status?: string
    product_id?: string
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }): Promise<PaginatedResponse<PlanWithProduct>> {
    const response = await apiClient.get<PlanWithProduct[]>('/plans', { params })
    return response as PaginatedResponse<PlanWithProduct>
  },

  /**
   * Get single plan by ID
   */
  async getPlan(id: string): Promise<ApiResponse<PlanWithProduct>> {
    return apiClient.get<PlanWithProduct>(`/plans/${id}`)
  },

  /**
   * Create a new plan
   */
  async createPlan(payload: CreatePlanPayload): Promise<ApiResponse<Plan>> {
    return apiClient.post<Plan>('/plans', payload)
  },

  /**
   * Update an existing plan
   */
  async updatePlan(id: string, payload: UpdatePlanPayload): Promise<ApiResponse<Plan>> {
    return apiClient.patch<Plan>(`/plans/${id}`, payload)
  },

  /**
   * Deactivate a plan
   */
  async deactivatePlan(id: string): Promise<ApiResponse<Plan>> {
    return apiClient.post<Plan>(`/plans/${id}/deactivate`)
  },
}

// ==================== QUOTATIONS ====================

export const quotationService = {
  /**
   * Get list of quotations with optional filters
   */
  async getQuotations(params?: {
    page?: number
    pageSize?: number
    status?: string
    customer_id?: string
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }): Promise<PaginatedResponse<QuotationWithDetails>> {
    const response = await apiClient.get<QuotationWithDetails[]>('/quotations', { params })
    return response as PaginatedResponse<QuotationWithDetails>
  },

  /**
   * Get single quotation by ID
   */
  async getQuotation(id: string): Promise<ApiResponse<QuotationWithDetails>> {
    return apiClient.get<QuotationWithDetails>(`/quotations/${id}`)
  },

  /**
   * Create a new quotation
   */
  async createQuotation(payload: CreateQuotationPayload): Promise<ApiResponse<Quotation>> {
    return apiClient.post<Quotation>('/quotations', payload)
  },

  /**
   * Update an existing quotation
   */
  async updateQuotation(id: string, payload: UpdateQuotationPayload): Promise<ApiResponse<Quotation>> {
    return apiClient.patch<Quotation>(`/quotations/${id}`, payload)
  },

  /**
   * Accept a quotation
   */
  async acceptQuotation(id: string): Promise<ApiResponse<Quotation>> {
    return apiClient.post<Quotation>(`/quotations/${id}/accept`)
  },

  /**
   * Reject a quotation
   */
  async rejectQuotation(id: string): Promise<ApiResponse<Quotation>> {
    return apiClient.post<Quotation>(`/quotations/${id}/reject`)
  },

  /**
   * Convert accepted quotation to subscription
   */
  async convertToSubscription(id: string): Promise<ApiResponse<Subscription>> {
    return apiClient.post<Subscription>(`/quotations/${id}/convert-to-subscription`)
  },
}

// ==================== SUBSCRIPTIONS ====================

export const subscriptionService = {
  /**
   * Get list of subscriptions with optional filters
   */
  async getSubscriptions(params?: {
    page?: number
    pageSize?: number
    status?: string
    customer_id?: string
    sortBy?: string
    sortOrder?: 'asc' | 'desc'
  }): Promise<PaginatedResponse<SubscriptionWithDetails>> {
    const response = await apiClient.get<SubscriptionWithDetails[]>('/subscriptions', { params })
    return response as PaginatedResponse<SubscriptionWithDetails>
  },

  /**
   * Get single subscription by ID
   */
  async getSubscription(id: string): Promise<ApiResponse<SubscriptionWithDetails>> {
    return apiClient.get<SubscriptionWithDetails>(`/subscriptions/${id}`)
  },

  /**
   * Create a new subscription
   */
  async createSubscription(payload: CreateSubscriptionPayload): Promise<ApiResponse<Subscription>> {
    return apiClient.post<Subscription>('/subscriptions', payload)
  },

  /**
   * Update an existing subscription
   */
  async updateSubscription(id: string, payload: UpdateSubscriptionPayload): Promise<ApiResponse<Subscription>> {
    return apiClient.patch<Subscription>(`/subscriptions/${id}`, payload)
  },

  /**
   * Pause a subscription
   */
  async pauseSubscription(id: string): Promise<ApiResponse<Subscription>> {
    return apiClient.post<Subscription>(`/subscriptions/${id}/pause`)
  },

  /**
   * Resume a paused subscription
   */
  async resumeSubscription(id: string): Promise<ApiResponse<Subscription>> {
    return apiClient.post<Subscription>(`/subscriptions/${id}/resume`)
  },

  /**
   * Cancel a subscription
   */
  async cancelSubscription(id: string, payload?: CancelSubscriptionPayload): Promise<ApiResponse<Subscription>> {
    return apiClient.post<Subscription>(`/subscriptions/${id}/cancel`, payload)
  },
}
