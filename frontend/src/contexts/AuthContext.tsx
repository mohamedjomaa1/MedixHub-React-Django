import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../services/api';
import { jwtDecode } from 'jwt-decode';
import toast from 'react-hot-toast';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  full_name: string;
  profile_picture?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isPharmacist: boolean;
  isDoctor: boolean;
  isReceptionist: boolean;
  isPatient: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      try {
        const decoded: any = jwtDecode(token);
        
        // Check if token is expired
        if (decoded.exp * 1000 < Date.now()) {
          logout();
          return;
        }

        // Fetch user profile
        const response = await authAPI.getProfile();
        setUser(response.data);
      } catch (error) {
        logout();
      }
    }
    
    setLoading(false);
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password);
      const { access, refresh } = response.data;

      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);

      // Fetch user profile
      const profileResponse = await authAPI.getProfile();
      setUser(profileResponse.data);

      toast.success('Login successful!');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed';
      toast.error(message);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    toast.success('Logged out successfully');
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'ADMIN',
    isPharmacist: user?.role === 'PHARMACIST',
    isDoctor: user?.role === 'DOCTOR',
    isReceptionist: user?.role === 'RECEPTIONIST',
    isPatient: user?.role === 'PATIENT',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};