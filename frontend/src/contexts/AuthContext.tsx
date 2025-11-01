import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from 'react';
import axios from 'axios';

type UserRole = 'admin' | 'doctor' | 'nurse' | 'receptionist' | 'super_admin';

interface User {
  id: number;
  username: string;
  email: string;
  fullName: string;
  role: UserRole;
  tenantId: number;
  mfaEnabled: boolean;
  isLocked: boolean;
  lastLogin?: string | null;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const transformUser = (payload: any): User => ({
  id: payload.id,
  username: payload.username,
  email: payload.email,
  fullName: payload.full_name,
  role: payload.role,
  tenantId: payload.tenant_id,
  mfaEnabled: payload.mfa_enabled,
  isLocked: payload.is_locked,
  lastLogin: payload.last_login,
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState<boolean>(Boolean(localStorage.getItem('token')));

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  }, []);

  const loadUser = useCallback(async (accessToken: string) => {
    const response = await axios.get(`${API_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    setUser(transformUser(response.data));
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) {
      setUser(null);
      return;
    }

    setLoading(true);
    try {
      await loadUser(token);
    } catch (error) {
      console.error('Failed to refresh session:', error);
      logout();
      throw error;
    } finally {
      setLoading(false);
    }
  }, [loadUser, logout, token]);

  const login = useCallback(
    async (username: string, password: string) => {
      setLoading(true);
      try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await axios.post(`${API_URL}/api/v1/auth/login`, formData);
        const { access_token: accessToken } = response.data;

        localStorage.setItem('token', accessToken);
        setToken(accessToken);

        await loadUser(accessToken);
      } catch (error) {
        console.error('Login failed:', error);
        logout();
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [loadUser, logout]
  );

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    let active = true;
    setLoading(true);

    loadUser(token)
      .catch(error => {
        if (!active) {
          return;
        }
        console.error('Session restoration failed:', error);
        logout();
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [loadUser, logout, token]);

  const value = useMemo(
    () => ({
      user,
      token,
      login,
      logout,
      refreshUser,
      isAuthenticated: Boolean(token),
      loading,
    }),
    [user, token, login, logout, refreshUser, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Export AuthContext for testing purposes
export { AuthContext };
