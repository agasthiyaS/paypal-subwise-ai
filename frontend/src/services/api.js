import axios from 'axios';

// Leverage Vite dev proxy and production relative routing by default
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization JWT Token if available and active Demo header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('subwise_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const isDemo = localStorage.getItem('subwise_demo_mode');
  if (isDemo === 'true') {
    config.headers['X-SubWise-Demo-Mode'] = 'true';
  }
  return config;
});

// Response interceptor for auth expiration
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't auto-redirect if trying to login
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('subwise_token');
        localStorage.removeItem('subwise_user');
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (email, password) => {
    // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
    const params = new URLSearchParams();
    params.append('username', email.trim());
    params.append('password', password);
    const res = await apiClient.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return res.data;
  },
  register: async (data) => {
    const res = await apiClient.post('/auth/register', data);
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

export const businessAPI = {
  getProfile: async () => {
    const res = await apiClient.get('/business/profile');
    return res.data;
  },
  updateProfile: async (data) => {
    const res = await apiClient.put('/business/profile', data);
    return res.data;
  },
  connectPayPal: async (data) => {
    const res = await apiClient.post('/business/paypal-connect', data);
    return res.data;
  },
  disconnectPayPal: async () => {
    const res = await apiClient.post('/business/paypal-disconnect');
    return res.data;
  },
  getProfiles: async () => {
    const res = await apiClient.get('/business/profiles');
    return res.data;
  },
  switchProfile: async (mode) => {
    // Synchronously clear the demo localStorage flag before the request so
    // the axios interceptor does not attach a stale X-SubWise-Demo-Mode: true
    // header when switching back to sandbox.
    if (mode !== 'demo') {
      localStorage.removeItem('subwise_demo_mode');
    } else {
      localStorage.setItem('subwise_demo_mode', 'true');
    }
    const res = await apiClient.post('/business/switch-profile', { mode });
    return res.data;
  },
};

export const transactionsAPI = {
  getTransactions: async (params) => {
    const res = await apiClient.get('/transactions/', { params });
    return res.data;
  },
  syncTransactions: async (forceDemo = false) => {
    const res = await apiClient.post(`/transactions/sync?force_demo=${forceDemo}`);
    return res.data;
  },
};

export const paypalAPI = {
  getStatus: async () => {
    const res = await apiClient.get('/paypal/status');
    return res.data;
  },
  sync: async (params = {}) => {
    const res = await apiClient.post('/paypal/sync', params);
    return res.data;
  },
  getSyncStatus: async () => {
    const res = await apiClient.get('/paypal/sync-status');
    return res.data;
  },
  createOrder: async (data = {}) => {
    const res = await apiClient.post('/paypal/orders/create', data);
    return res.data;
  },
  captureOrder: async (orderId) => {
    const res = await apiClient.post('/paypal/orders/capture', { order_id: orderId });
    return res.data;
  },
};

export const subscriptionsAPI = {
  getSubscriptions: async () => {
    const res = await apiClient.get('/subscriptions/');
    return res.data;
  },
  getAnalysis: async () => {
    const res = await apiClient.get('/subscriptions/analysis');
    return res.data;
  },
  updateSubscription: async (id, data) => {
    const res = await apiClient.patch(`/subscriptions/${id}`, data);
    return res.data;
  },
};

export const simulationAPI = {
  runSimulation: async (data) => {
    const res = await apiClient.post('/simulation/run', data);
    return res.data;
  },
};

export const forecastAPI = {
  getForecast: async (months = 6) => {
    const res = await apiClient.get('/forecast', { params: { months } });
    return res.data;
  },
};

export const financialIntelligenceAPI = {
  /**
   * Returns the complete Financial Intelligence Overview for the authenticated
   * business: health index, historical actuals, forward commitments, projected
   * estimates, risk items, and the monthly business briefing.
   */
  getOverview: async () => {
    const res = await apiClient.get('/financial-intelligence');
    return res.data;
  },
};

export const reportsAPI = {
  getMonthlyReport: async (params = {}) => {
    const res = await apiClient.get('/reports/monthly', { params });
    return res.data;
  },
  getSubscriptionsReport: async () => {
    const res = await apiClient.get('/reports/subscriptions');
    return res.data;
  },
  getRenewalsReport: async () => {
    const res = await apiClient.get('/reports/renewals');
    return res.data;
  },
  getForecastReport: async () => {
    const res = await apiClient.get('/reports/forecast');
    return res.data;
  },
  getComprehensiveReport: async (params = {}) => {
    const res = await apiClient.get('/reports/comprehensive', { params });
    return res.data;
  },
  downloadCSV: async (exportType = 'transactions', params = {}) => {
    const res = await apiClient.get('/reports/export/csv', {
      params: { export_type: exportType, ...params },
      responseType: 'blob',
    });
    return res;
  },
  downloadPDF: async (reportType = 'comprehensive', params = {}) => {
    const res = await apiClient.get('/reports/export/pdf', {
      params: { report_type: reportType, ...params },
      responseType: 'blob',
    });
    return res;
  },
};

export const recommendationsAPI = {
  getRecommendations: async () => {
    const res = await apiClient.get('/recommendations/');
    return res.data;
  },
  generateRecommendations: async () => {
    const res = await apiClient.post('/recommendations/generate');
    return res.data;
  },
  simulatePurchase: async (data) => {
    const res = await apiClient.post('/recommendations/simulate-purchase', data);
    return res.data;
  },
  updateRecommendation: async (id, data) => {
    const res = await apiClient.patch(`/recommendations/${id}`, data);
    return res.data;
  },
  getAIBriefing: async () => {
    const res = await apiClient.get('/recommendations/ai-briefing');
    return res.data;
  },
};

export const assistantAPI = {
  chat: async (data) => {
    const res = await apiClient.post('/assistant/chat', data);
    return res.data;
  },
  getConversations: async () => {
    const res = await apiClient.get('/assistant/conversations');
    return res.data;
  },
  getConversation: async (id) => {
    const res = await apiClient.get(`/assistant/conversations/${id}`);
    return res.data;
  },
  renameConversation: async (id, title) => {
    const res = await apiClient.patch(`/assistant/conversations/${id}`, { title });
    return res.data;
  },
  deleteConversation: async (id) => {
    const res = await apiClient.delete(`/assistant/conversations/${id}`);
    return res.data;
  },
  query: async (data) => {
    const res = await apiClient.post('/assistant/query', data);
    return res.data;
  },
  getSuggestions: async () => {
    const res = await apiClient.get('/assistant/suggestions');
    return res.data;
  },
  getProviderStatus: async () => {
    const res = await apiClient.get('/assistant/provider-status');
    return res.data;
  },
};

export const demoAPI = {
  getStatus: async () => {
    const res = await apiClient.get('/demo/status');
    return res.data;
  },
  generate: async () => {
    const res = await apiClient.post('/demo/generate');
    return res.data;
  },
  reset: async () => {
    const res = await apiClient.post('/demo/reset');
    return res.data;
  },
  switchMode: async (mode) => {
    const res = await apiClient.post('/demo/switch', { mode });
    return res.data;
  },
};

export const expensesAPI = {
  getExpenses: async (params) => {
    const res = await apiClient.get('/expenses', { params });
    return res.data;
  },
  createExpense: async (data) => {
    const res = await apiClient.post('/expenses', data);
    return res.data;
  },
  updateExpense: async (id, data) => {
    const res = await apiClient.put(`/expenses/${id}`, data);
    return res.data;
  },
  deleteExpense: async (id) => {
    const res = await apiClient.delete(`/expenses/${id}`);
    return res.data;
  },
  getSummary: async (params) => {
    const res = await apiClient.get('/expenses/summary', { params });
    return res.data;
  },
  syncPayPal: async () => {
    const res = await apiClient.post('/expenses/sync-paypal');
    return res.data;
  },
};

export const householdAPI = {
  getMembers: async () => {
    const res = await apiClient.get('/household/members');
    return res.data;
  },
  createMember: async (data) => {
    const res = await apiClient.post('/household/members', data);
    return res.data;
  },
  updateMember: async (id, data) => {
    const res = await apiClient.put(`/household/members/${id}`, data);
    return res.data;
  },
  deleteMember: async (id) => {
    const res = await apiClient.delete(`/household/members/${id}`);
    return res.data;
  },
  getSummary: async (params) => {
    const res = await apiClient.get('/household/summary', { params });
    return res.data;
  },
};

export const budgetsAPI = {
  getBudgets: async () => {
    const res = await apiClient.get('/budgets');
    return res.data;
  },
  setBudget: async (data) => {
    const res = await apiClient.post('/budgets', data);
    return res.data;
  },
  deleteBudget: async (id) => {
    const res = await apiClient.delete(`/budgets/${id}`);
    return res.data;
  },
};

// ─── Phase 3: Financial Intelligence (Consumer) ───────────────────────────────
export const intelligenceAPI = {
  /**
   * Unified consumer financial intelligence: spending analysis, health score,
   * top recommendations, and forecast snapshot.
   */
  getUnified: async () => {
    const res = await apiClient.get('/financial-intelligence/unified');
    return res.data;
  },
  getSpendingAnalysis: async (params = {}) => {
    const res = await apiClient.get('/financial-intelligence/spending-analysis', { params });
    return res.data;
  },
  getHealthScore: async () => {
    const res = await apiClient.get('/financial-intelligence/health-score');
    return res.data;
  },
  getForecastScenarios: async (params = {}) => {
    const res = await apiClient.get('/financial-intelligence/forecast-scenarios', { params });
    return res.data;
  },
};

// ─── Phase 4: Smart Savings Discovery ────────────────────────────────────────
export const savingsAPI = {
  /** Personalized savings opportunities matched to user's active subscriptions */
  getOpportunities: async () => {
    const res = await apiClient.get('/savings-discovery');
    return res.data;
  },
  /** Full verified vendor comparison catalog */
  getCatalog: async () => {
    const res = await apiClient.get('/savings-discovery/catalog');
    return res.data;
  },
  /** Search vendor alternatives by keyword */
  search: async (query) => {
    const res = await apiClient.get('/savings-discovery/search', { params: { query } });
    return res.data;
  },
};

// ─── Phase 6: Admin, Vendors & Entitlements ──────────────────────────────────
export const adminAPI = {
  getStats: async () => {
    const res = await apiClient.get('/admin/stats');
    return res.data;
  },
  getUsers: async (limit = 50) => {
    const res = await apiClient.get('/admin/users', { params: { limit } });
    return res.data;
  },
  updateUserRole: async (userId, isAdmin) => {
    const res = await apiClient.put(`/admin/users/${userId}/role`, null, { params: { is_admin: isAdmin } });
    return res.data;
  },
};

export const vendorsAPI = {
  getVendors: async (params = {}) => {
    const res = await apiClient.get('/vendors', { params });
    return res.data;
  },
  getCategories: async () => {
    const res = await apiClient.get('/vendors/categories');
    return res.data;
  },
  getVendor: async (id) => {
    const res = await apiClient.get(`/vendors/${id}`);
    return res.data;
  },
  createVendor: async (data) => {
    const res = await apiClient.post('/vendors', data);
    return res.data;
  },
  updateVendor: async (id, data) => {
    const res = await apiClient.put(`/vendors/${id}`, data);
    return res.data;
  },
  deleteVendor: async (id) => {
    const res = await apiClient.delete(`/vendors/${id}`);
    return res.data;
  },
  addPlan: async (vendorId, planData) => {
    const res = await apiClient.post(`/vendors/${vendorId}/plans`, planData);
    return res.data;
  },
  deletePlan: async (vendorId, planId) => {
    const res = await apiClient.delete(`/vendors/${vendorId}/plans/${planId}`);
    return res.data;
  },
};

export const entitlementsAPI = {
  getEntitlements: async () => {
    const res = await apiClient.get('/entitlements');
    return res.data;
  },
};

export default apiClient;
