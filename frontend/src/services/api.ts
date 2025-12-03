import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_URL}/auth/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);

        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email: string, password: string) =>
    axios.post(`${API_URL}/auth/login/`, { email, password }),
  
  register: (data: any) =>
    api.post('/users/', data),
  
  getProfile: () =>
    api.get('/users/profile/'),
  
  updateProfile: (data: any) =>
    api.patch('/users/profile/', data),
  
  changePassword: (data: any) =>
    api.post('/users/change_password/', data),
};

// Users API
export const usersAPI = {
  getAll: (params?: any) =>
    api.get('/users/', { params }),
  
  getById: (id: number) =>
    api.get(`/users/${id}/`),
  
  create: (data: any) =>
    api.post('/users/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/users/${id}/`, data),
  
  delete: (id: number) =>
    api.delete(`/users/${id}/`),
  
  getStats: () =>
    api.get('/users/stats/'),
};

// Drugs API
export const drugsAPI = {
  getAll: (params?: any) =>
    api.get('/drugs/', { params }),
  
  getById: (id: number) =>
    api.get(`/drugs/${id}/`),
  
  create: (data: any) =>
    api.post('/drugs/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/drugs/${id}/`, data),
  
  delete: (id: number) =>
    api.delete(`/drugs/${id}/`),
  
  getLowStock: () =>
    api.get('/drugs/low_stock/'),
  
  getOutOfStock: () =>
    api.get('/drugs/out_of_stock/'),
  
  getExpiringSoon: () =>
    api.get('/drugs/expiring_soon/'),
  
  getStats: () =>
    api.get('/drugs/stats/'),
};

// Categories API
export const categoriesAPI = {
  getAll: () =>
    api.get('/categories/'),
  
  create: (data: any) =>
    api.post('/categories/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/categories/${id}/`, data),
  
  delete: (id: number) =>
    api.delete(`/categories/${id}/`),
};

// Manufacturers API
export const manufacturersAPI = {
  getAll: () =>
    api.get('/manufacturers/'),
  
  create: (data: any) =>
    api.post('/manufacturers/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/manufacturers/${id}/`, data),
  
  delete: (id: number) =>
    api.delete(`/manufacturers/${id}/`),
};

// Prescriptions API
export const prescriptionsAPI = {
  getAll: (params?: any) =>
    api.get('/prescriptions/', { params }),
  
  getById: (id: number) =>
    api.get(`/prescriptions/${id}/`),
  
  create: (data: any) =>
    api.post('/prescriptions/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/prescriptions/${id}/`, data),
  
  fill: (id: number, data: any) =>
    api.post(`/prescriptions/${id}/fill/`, data),
  
  cancel: (id: number) =>
    api.post(`/prescriptions/${id}/cancel/`),
  
  getMyPrescriptions: () =>
    api.get('/prescriptions/my_prescriptions/'),
};

// Sales API
export const salesAPI = {
  getAll: (params?: any) =>
    api.get('/sales/', { params }),
  
  getById: (id: number) =>
    api.get(`/sales/${id}/`),
  
  create: (data: any) =>
    api.post('/sales/', data),
  
  getToday: () =>
    api.get('/sales/today/'),
  
  getStats: (days?: number) =>
    api.get('/sales/stats/', { params: { days } }),
  
  getDailyReport: (date?: string) =>
    api.get('/sales/daily_report/', { params: { date } }),
};

// Reports API
export const reportsAPI = {
  getDashboard: () =>
    api.get('/reports/dashboard/'),
  
  getInventoryReport: (type?: string) =>
    api.get('/reports/inventory/', { params: { type } }),
  
  getSalesReport: (days?: number) =>
    api.get('/reports/sales/', { params: { days } }),
};

// Stock Transactions API
export const stockAPI = {
  getAll: (params?: any) =>
    api.get('/stock-transactions/', { params }),
  
  create: (data: any) =>
    api.post('/stock-transactions/', data),
  
  getByDrug: (drugId: number) =>
    api.get('/stock-transactions/by_drug/', { params: { drug_id: drugId } }),
};

export default api;