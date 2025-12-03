import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard,
  Pill,
  FileText,
  ShoppingCart,
  Users,
  BarChart3,
  Menu,
  X,
  LogOut,
  User,
} from 'lucide-react';

const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout, isAdmin, isPharmacist } = useAuth();
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['all'] },
    { name: 'Drugs', href: '/drugs', icon: Pill, roles: ['ADMIN', 'PHARMACIST', 'DOCTOR'] },
    { name: 'Prescriptions', href: '/prescriptions', icon: FileText, roles: ['all'] },
    { name: 'Sales', href: '/sales', icon: ShoppingCart, roles: ['ADMIN', 'PHARMACIST', 'RECEPTIONIST'] },
    { name: 'Users', href: '/users', icon: Users, roles: ['ADMIN'] },
    { name: 'Reports', href: '/reports', icon: BarChart3, roles: ['ADMIN', 'PHARMACIST'] },
  ];

  const filteredNavigation = navigation.filter(
    (item) => item.roles.includes('all') || item.roles.includes(user?.role || '')
  );

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div
        className={`fixed inset-0 z-40 lg:hidden ${sidebarOpen ? '' : 'pointer-events-none'}`}
      >
        <div
          className={`fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity ${
            sidebarOpen ? 'opacity-100' : 'opacity-0'
          }`}
          onClick={() => setSidebarOpen(false)}
        />

        <div
          className={`fixed inset-y-0 left-0 flex w-64 flex-col bg-white transform transition-transform ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <div className="flex h-16 items-center justify-between px-4 bg-primary-600">
            <span className="text-xl font-bold text-white">MedixHub</span>
            <button onClick={() => setSidebarOpen(false)} className="text-white">
              <X className="h-6 w-6" />
            </button>
          </div>

          <nav className="flex-1 space-y-1 px-2 py-4">
            {filteredNavigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg ${
                    isActive(item.href)
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200">
          <div className="flex h-16 items-center px-4 bg-primary-600">
            <span className="text-xl font-bold text-white">MedixHub</span>
          </div>

          <nav className="flex-1 space-y-1 px-2 py-4">
            {filteredNavigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg ${
                    isActive(item.href)
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-10 flex h-16 bg-white border-b border-gray-200">
          <button
            className="px-4 text-gray-500 focus:outline-none lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex flex-1 justify-between px-4">
            <div className="flex flex-1"></div>

            <div className="ml-4 flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                  <User className="h-5 w-5 text-primary-600" />
                </div>
                <div className="hidden md:block">
                  <p className="text-sm font-medium text-gray-700">{user?.full_name}</p>
                  <p className="text-xs text-gray-500">{user?.role}</p>
                </div>
              </div>

              <button
                onClick={logout}
                className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;