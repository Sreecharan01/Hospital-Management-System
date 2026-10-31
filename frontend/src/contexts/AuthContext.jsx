import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/axios';
import toast from 'react-hot-toast';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [tokens, setTokens] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('tokens')) || null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  // Hydrate user from /me on mount if tokens exist
  const fetchMe = useCallback(async () => {
    try {
      const { data } = await api.get('/auth/me/');
      setUser(data);
      localStorage.setItem('user', JSON.stringify(data));
    } catch {
      // Token invalid — clear everything
      setUser(null);
      setTokens(null);
      localStorage.removeItem('tokens');
      localStorage.removeItem('user');
    }
  }, []);

  useEffect(() => {
    if (tokens?.access) {
      fetchMe().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = async (email, password) => {
    const { data } = await api.post('/auth/token/', { email, password });
    const newTokens = { access: data.access, refresh: data.refresh };
    setTokens(newTokens);
    localStorage.setItem('tokens', JSON.stringify(newTokens));

    // Fetch full user profile
    const meRes = await api.get('/auth/me/', {
      headers: { Authorization: `Bearer ${data.access}` },
    });
    setUser(meRes.data);
    localStorage.setItem('user', JSON.stringify(meRes.data));
    toast.success(`Welcome back, ${meRes.data.first_name || meRes.data.email}!`);
    return meRes.data;
  };

  const register = async (formData) => {
    const { data } = await api.post('/auth/register/', formData);
    toast.success('Account created! Please log in.');
    return data;
  };

  const logout = useCallback(() => {
    setUser(null);
    setTokens(null);
    localStorage.removeItem('tokens');
    localStorage.removeItem('user');
    toast.success('Logged out successfully.');
  }, []);

  const value = {
    user,
    tokens,
    loading,
    login,
    register,
    logout,
    fetchMe,
    isAuthenticated: !!user,
    role: user?.role || null,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export default AuthContext;
