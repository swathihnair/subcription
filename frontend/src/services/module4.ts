/**
 * Module 4: Customer Portal, Analytics, Notifications API Service
 */
import api from './api';

// Portal API
export const portalApi = {
  getProfile: async () => {
    const response = await api.get('/portal/me');
    return response.data;
  },

  getSubscriptions: async () => {
    const response = await api.get('/portal/subscriptions');
    return response.data;
  },

  getSubscription: async (id: number) => {
    const response = await api.get(`/portal/subscriptions/${id}`);
    return response.data;
  },

  getInvoices: async () => {
    const response = await api.get('/portal/invoices');
    return response.data;
  },

  getInvoice: async (id: number) => {
    const response = await api.get(`/portal/invoices/${id}`);
    return response.data;
  },

  getPayments: async () => {
    const response = await api.get('/portal/payments');
    return response.data;
  },

  updateProfile: async (data: any) => {
    const response = await api.patch('/portal/profile', data);
    return response.data;
  }
};

// Notifications API
export const notificationsApi = {
  getNotifications: async (params?: { type?: string; page?: number; pageSize?: number }) => {
    const response = await api.get('/notifications', { params });
    return response.data;
  },

  getUnreadCount: async () => {
    const response = await api.get('/notifications/unread-count');
    return response.data;
  },

  markAsRead: async (id: number) => {
    const response = await api.post(`/notifications/${id}/read`);
    return response.data;
  },

  markAllAsRead: async () => {
    const response = await api.post('/notifications/read-all');
    return response.data;
  }
};

// Renewals API
export const renewalsApi = {
  getRenewals: async (params?: {
    customer_id?: number;
    status?: string;
    plan_id?: number;
    days?: number;
  }) => {
    const response = await api.get('/renewals', { params });
    return response.data;
  },

  getSummary: async () => {
    const response = await api.get('/renewals/summary');
    return response.data;
  }
};

// Analytics API
export const analyticsApi = {
  getOverview: async () => {
    const response = await api.get('/analytics/overview');
    return response.data;
  },

  getMRR: async (days?: number) => {
    const response = await api.get('/analytics/mrr', { params: { days } });
    return response.data;
  },

  getSubscriptions: async (days?: number) => {
    const response = await api.get('/analytics/subscriptions', { params: { days } });
    return response.data;
  },

  getInvoices: async () => {
    const response = await api.get('/analytics/invoices');
    return response.data;
  },

  getPayments: async (days?: number) => {
    const response = await api.get('/analytics/payments', { params: { days } });
    return response.data;
  }
};

// Audit API
export const auditApi = {
  getAuditLogs: async (params?: {
    entity_type?: string;
    entity_id?: number;
    action?: string;
    user_id?: number;
    page?: number;
    pageSize?: number;
  }) => {
    const response = await api.get('/audit-logs', { params });
    return response.data;
  }
};
