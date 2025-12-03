import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import {
  Pill,
  ShoppingCart,
  FileText,
  Users,
  AlertTriangle,
  TrendingUp,
  DollarSign,
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const { user, isAdmin, isPharmacist, isDoctor, isPatient } = useAuth();

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await reportsAPI.getDashboard();
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Admin/Pharmacist Dashboard
  if (isAdmin || isPharmacist) {
    const stats = [
      {
        name: 'Total Drugs',
        value: dashboardData?.inventory?.total_drugs || 0,
        icon: Pill,
        color: 'bg-blue-500',
        change: '+12%',
      },
      {
        name: "Today's Sales",
        value: dashboardData?.sales?.today || 0,
        icon: ShoppingCart,
        color: 'bg-green-500',
        change: '+8%',
      },
      {
        name: 'Today Revenue',
        value: `$${dashboardData?.sales?.today_revenue?.toFixed(2) || 0}`,
        icon: DollarSign,
        color: 'bg-purple-500',
        change: '+15%',
      },
      {
        name: 'Pending Prescriptions',
        value: dashboardData?.prescriptions?.pending || 0,
        icon: FileText,
        color: 'bg-yellow-500',
        change: '',
      },
    ];

    return (
      <div>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Welcome back, {user?.full_name}!</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.name} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">{stat.name}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                    {stat.change && (
                      <p className="text-sm text-green-600 mt-1">{stat.change}</p>
                    )}
                  </div>
                  <div className={`${stat.color} p-3 rounded-lg`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Alerts */}
        {dashboardData?.alerts && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <div>
                  <p className="font-medium text-yellow-900">Low Stock Alert</p>
                  <p className="text-sm text-yellow-700">
                    {dashboardData.alerts.low_stock_drugs} drugs need reordering
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <div>
                  <p className="font-medium text-red-900">Expiring Soon</p>
                  <p className="text-sm text-red-700">
                    {dashboardData.alerts.expiring_drugs} drugs expiring within 30 days
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="font-medium text-blue-900">Pending Prescriptions</p>
                  <p className="text-sm text-blue-700">
                    {dashboardData.alerts.pending_prescriptions} prescriptions to fill
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Inventory Overview</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Drugs</span>
                <span className="font-medium">{dashboardData?.inventory?.total_drugs || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Low Stock</span>
                <span className="font-medium text-yellow-600">
                  {dashboardData?.inventory?.low_stock || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Out of Stock</span>
                <span className="font-medium text-red-600">
                  {dashboardData?.inventory?.out_of_stock || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Value</span>
                <span className="font-medium">
                  ${dashboardData?.inventory?.total_value?.toFixed(2) || 0}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Last 30 Days Sales</span>
                <span className="font-medium">{dashboardData?.sales?.last_30_days || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">30 Days Revenue</span>
                <span className="font-medium text-green-600">
                  ${dashboardData?.sales?.last_30_days_revenue?.toFixed(2) || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Users</span>
                <span className="font-medium">{dashboardData?.users?.total || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Active Prescriptions</span>
                <span className="font-medium">{dashboardData?.prescriptions?.total_active || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Doctor Dashboard
  if (isDoctor) {
    return (
      <div>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Doctor Dashboard</h1>
          <p className="text-gray-600">Welcome, Dr. {user?.last_name}!</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Prescriptions</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {dashboardData?.prescriptions?.total_issued || 0}
                </p>
              </div>
              <FileText className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {dashboardData?.prescriptions?.pending || 0}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-yellow-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Patients</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {dashboardData?.patients?.total || 0}
                </p>
              </div>
              <Users className="h-8 w-8 text-green-500" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Patient Dashboard
  if (isPatient) {
    return (
      <div>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Patient Dashboard</h1>
          <p className="text-gray-600">Welcome, {user?.full_name}!</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">My Prescriptions</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total</span>
                <span className="font-medium">{dashboardData?.prescriptions?.total || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Pending</span>
                <span className="font-medium text-yellow-600">
                  {dashboardData?.prescriptions?.pending || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Filled</span>
                <span className="font-medium text-green-600">
                  {dashboardData?.prescriptions?.filled || 0}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Purchase History</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Purchases</span>
                <span className="font-medium">{dashboardData?.purchases?.total || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Spent</span>
                <span className="font-medium text-green-600">
                  ${dashboardData?.purchases?.total_spent?.toFixed(2) || 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default Dashboard;