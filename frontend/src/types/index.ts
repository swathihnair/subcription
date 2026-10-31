/**
 * Shared API and application types
 */

// Authentication
export interface AuthResponse {
  success: boolean
  data?: {
    access_token: string
    refresh_token?: string
    user: User
  }
  error?: ErrorResponse
  message?: string
}

export interface User {
  id: string
  email?: string
  first_name?: string
  last_name?: string
  is_active: boolean
  role: Role
  created_at: string
  updated_at: string
}

export interface Role {
  id: string
  name: string
  description?: string
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: ErrorResponse
  message?: string
}

export interface ErrorResponse {
  code: string
  message: string
  details?: Record<string, any>
}

export interface PaginatedResponse<T> {
  success: boolean
  data: T[]
  pagination?: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
  message?: string
}

// Core Business Models
export interface Customer {
  id: string
  name: string
  email: string
  status: 'active' | 'inactive' | 'churned'
  phone?: string
  total_contract_value?: number
  annual_recurring_revenue?: number
  created_at: string
  updated_at: string
}

export interface Product {
  id: string
  name: string
  sku: string
  description?: string
  status: 'active' | 'discontinued' | 'draft'
  base_price: number
  created_at: string
  updated_at: string
}

export interface Plan {
  id: string
  product_id: string
  name: string
  description?: string
  status: string
  price: number
  billing_cycle: 'monthly' | 'quarterly' | 'annually'
  setup_fee?: number
  created_at: string
  updated_at: string
}

export interface Subscription {
  id: string
  customer_id: string
  plan_id: string
  subscription_number: string
  status: 'active' | 'suspended' | 'cancelled' | 'churned'
  monthly_recurring_revenue?: number
  annual_contract_value?: number
  start_date: string
  end_date?: string
  next_billing_date?: string
  auto_renew: boolean
  created_at: string
  updated_at: string
}

export interface Invoice {
  id: string
  customer_id: string
  subscription_id?: string
  invoice_number: string
  status: 'draft' | 'sent' | 'viewed' | 'partially_paid' | 'paid' | 'overdue' | 'cancelled'
  subtotal: number
  tax_amount?: number
  discount_amount?: number
  total_amount: number
  amount_paid?: number
  amount_due: number
  invoice_date: string
  due_date: string
  created_at: string
  updated_at: string
}

export interface Quotation {
  id: string
  customer_id: string
  plan_id: string
  quote_number: string
  status: 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired'
  amount: number
  discount_amount?: number
  total_amount: number
  valid_until?: string
  created_at: string
  updated_at: string
  customer?: Customer
  plan?: Plan
}

// Module 2 - Create/Update payloads
export interface CreateCustomerPayload {
  name: string
  email: string
  phone?: string
  billing_address?: string
  shipping_address?: string
  status?: 'active' | 'inactive'
}

export interface UpdateCustomerPayload {
  name?: string
  email?: string
  phone?: string
  billing_address?: string
  shipping_address?: string
  status?: string
}

export interface CreateProductPayload {
  name: string
  sku: string
  description?: string
  base_price: number
  status?: 'active' | 'draft'
}

export interface UpdateProductPayload {
  name?: string
  sku?: string
  description?: string
  base_price?: number
  status?: string
}

export interface CreatePlanPayload {
  product_id: string
  name: string
  description?: string
  price: number
  billing_cycle: 'weekly' | 'monthly' | 'quarterly' | 'annually'
  setup_fee?: number
  status?: 'active'
}

export interface UpdatePlanPayload {
  name?: string
  description?: string
  price?: number
  billing_cycle?: 'weekly' | 'monthly' | 'quarterly' | 'annually'
  setup_fee?: number
  status?: string
}

export interface CreateQuotationPayload {
  customer_id: string
  plan_id: string
  amount: number
  discount_amount?: number
  total_amount: number
  valid_until?: string
}

export interface UpdateQuotationPayload {
  amount?: number
  discount_amount?: number
  total_amount?: number
  valid_until?: string
}

export interface CreateSubscriptionPayload {
  customer_id: string
  plan_id: string
  start_date?: string
  status?: 'active' | 'trialing'
  auto_renew?: boolean
}

export interface UpdateSubscriptionPayload {
  auto_renew?: boolean
  end_date?: string | null
}

export interface CancelSubscriptionPayload {
  cancel_immediately?: boolean
}

// Extended types with relations
export interface ProductWithPlans extends Product {
  plans?: Plan[]
}

export interface PlanWithProduct extends Plan {
  product?: Product
}

export interface SubscriptionWithDetails extends Subscription {
  customer?: Customer
  plan?: Plan
  invoices?: Invoice[]
}

export interface QuotationWithDetails extends Quotation {
  customer?: Customer
  plan?: Plan
}

// Feature-specific types
export interface LoginCredentials {
  email: string
  password: string
}

export interface CreateUserPayload {
  email: string
  password: string
  first_name?: string
  last_name?: string
  role_id: string
}

export interface UpdateUserPayload {
  first_name?: string
  last_name?: string
  is_active?: boolean
}

// Dashboard
export interface DashboardMetrics {
  activeSubscriptions: number
  totalCustomers: number
  monthlyRecurringRevenue: number
  outstandingInvoices: number
  recentActivity: ActivityLog[]
}

export interface ActivityLog {
  id: string
  action: string
  entity_type: string
  entity_id: string
  created_at: string
  user?: User
}
