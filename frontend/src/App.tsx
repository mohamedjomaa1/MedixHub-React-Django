import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
//import Drugs from './pages/Drugs';
//import Prescriptions from './pages/Prescriptions';
//import Sales from './pages/Sales';
//import Users from './pages/Users';
//import Reports from './pages/Reports';
import Layout from './components/Layout';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode; roles?: string[] }> = ({
  children,
  roles,
}) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="drugs" element={<Drugs />} />
        <Route path="prescriptions" element={<Prescriptions />} />
        <Route
          path="sales"
          element={
            <ProtectedRoute roles={['ADMIN', 'PHARMACIST', 'RECEPTIONIST']}>
              <Sales />
            </ProtectedRoute>
          }
        />
        <Route
          path="users"
          element={
            <ProtectedRoute roles={['ADMIN']}>
              <Users />
            </ProtectedRoute>
          }
        />
        <Route
          path="reports"
          element={
            <ProtectedRoute roles={['ADMIN', 'PHARMACIST']}>
              <Reports />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
          <Toaster position="top-right" />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;