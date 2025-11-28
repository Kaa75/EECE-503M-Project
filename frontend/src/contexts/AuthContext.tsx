import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, UserRole } from '../types';
import apiService from '../services/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, phone: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  hasRole: (role: UserRole | UserRole[]) => boolean;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check if user is already logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (token) {
          const profile = await apiService.getProfile();
          setUser(profile);
        }
      } catch (err) {
        localStorage.removeItem('accessToken');
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.login({ username, password });
      if (response.success && response.access_token) {
        // Fetch CSRF token after successful login and store it in API client
        try {
          await apiService.fetchCsrfToken();
        } catch (csrfErr) {
          // Non-fatal: surface error but continue to get profile
          console.warn('Failed to fetch CSRF token:', csrfErr);
        }
        const profile = await apiService.getProfile();
        setUser(profile);
        return !!response.must_change_credentials;
      } else {
        throw new Error(response.error || 'Login failed');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (
    username: string,
    email: string,
    phone: string,
    password: string,
    fullName: string
  ) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.register({
        username,
        email,
        phone,
        password,
        full_name: fullName
      });
      if (!response.success) {
        throw new Error(response.error || 'Registration failed');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await apiService.logout();
      setUser(null);
    } catch (err) {
      // Still logout even if API call fails
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const hasRole = (role: UserRole | UserRole[]): boolean => {
    if (!user) return false;
    if (Array.isArray(role)) {
      return role.includes(user.role);
    }
    return user.role === role;
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;

    // Define permissions by role
    const permissions: Record<UserRole, Set<string>> = {
      [UserRole.CUSTOMER]: new Set([
        'create_accounts',
        'internal_transfers',
        'external_transfers',
        'view_own_transactions',
        'create_support_ticket',
        'manage_own_profile'
      ]),
      [UserRole.SUPPORT_AGENT]: new Set([
        'view_all_accounts',
        'view_all_transactions',
        'view_open_tickets',
        'update_ticket_status',
        'add_ticket_notes'
      ]),
      [UserRole.AUDITOR]: new Set([
        'view_all_accounts',
        'view_all_transactions',
        'view_audit_logs',
        'view_login_attempts',
        'view_suspicious_activities'
      ]),
      [UserRole.ADMIN]: new Set([
        'manage_users',
        'assign_roles',
        'freeze_unfreeze_accounts',
        'close_accounts',
        'view_all_accounts',
        'view_all_transactions',
        'view_audit_logs',
        'view_open_tickets',
        'assign_tickets'
      ])
    };

    return permissions[user.role]?.has(permission) ?? false;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        register,
        logout,
        clearError,
        hasRole,
        hasPermission
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
