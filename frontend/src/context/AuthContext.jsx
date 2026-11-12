import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI, businessAPI } from '../services/api';

const AuthContext = createContext();

/**
 * AuthProvider — wraps the app and provides authentication state.
 * Separates bootstrap initialization loading (initialLoading) from
 * form-level action handling to prevent unmounting active forms.
 */
export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('subwise_token') || null);
  const [user, setUser] = useState(null);
  const [business, setBusiness] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);

  /* ------------------------------------------------------------------ */
  /* Profile fetch                                                      */
  /* ------------------------------------------------------------------ */
  const fetchProfile = useCallback(async () => {
    try {
      const data = await authAPI.getMe();
      setUser(data.user);
      setBusiness(data.business);
      if (data.business?.is_demo) {
        localStorage.setItem('subwise_demo_mode', 'true');
      } else {
        localStorage.removeItem('subwise_demo_mode');
      }
      return data;
    } catch (err) {
      console.warn('Profile verification failed:', err?.response?.status || err.message);
      if (err?.response?.status === 401) {
        _clearAuth();
      }
      throw err;
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    const initializeAuth = async () => {
      const savedToken = localStorage.getItem('subwise_token');
      if (savedToken) {
        try {
          await fetchProfile();
        } catch {
          // Handled in fetchProfile
        }
      }
      if (isMounted) {
        setInitialLoading(false);
      }
    };

    initializeAuth();
    return () => {
      isMounted = false;
    };
  }, [fetchProfile]);

  /* ------------------------------------------------------------------ */
  /* Helpers                                                            */
  /* ------------------------------------------------------------------ */
  const _clearAuth = () => {
    localStorage.removeItem('subwise_token');
    localStorage.removeItem('subwise_user');
    localStorage.removeItem('subwise_demo_mode');
    setToken(null);
    setUser(null);
    setBusiness(null);
  };

  /* ------------------------------------------------------------------ */
  /* Auth actions                                                       */
  /* ------------------------------------------------------------------ */
  const login = async (email, password) => {
    try {
      const data = await authAPI.login(email, password);
      if (!data || !data.access_token) {
        throw new Error('Authentication succeeded but no access token was returned.');
      }

      localStorage.setItem('subwise_token', data.access_token);
      setToken(data.access_token);

      try {
        const meData = await authAPI.getMe();
        setUser(meData.user);
        setBusiness(meData.business);
      } catch (profileErr) {
        console.warn('Secondary profile fetch failed, using login payload:', profileErr);
        setUser({ id: data.user_id, email: data.email, full_name: data.company_name });
        setBusiness({ id: data.business_id, company_name: data.company_name, paypal_mode: data.paypal_mode || 'sandbox', paypal_connected: true });
      }

      return { success: true };
    } catch (err) {
      console.error('Login action error:', err);
      let errorMsg = 'Login failed. Please check your credentials.';
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.message && !err.response) {
        errorMsg = 'Cannot reach backend server. Please verify the backend is running.';
      }
      return {
        success: false,
        message: errorMsg,
      };
    }
  };

  const register = async (formData) => {
    try {
      const data = await authAPI.register(formData);
      if (!data || !data.access_token) {
        throw new Error('Registration completed but no access token was returned.');
      }

      localStorage.setItem('subwise_token', data.access_token);
      setToken(data.access_token);

      try {
        const meData = await authAPI.getMe();
        setUser(meData.user);
        setBusiness(meData.business);
      } catch (profileErr) {
        console.warn('Secondary profile fetch failed after register:', profileErr);
        setUser({ id: data.user_id, email: data.email, full_name: data.company_name });
        setBusiness({ id: data.business_id, company_name: data.company_name, paypal_mode: data.paypal_mode || 'sandbox', paypal_connected: true });
      }

      return { success: true };
    } catch (err) {
      console.error('Registration action error:', err);
      let errorMsg = 'Registration failed. Please check the entered information.';
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.message && !err.response) {
        errorMsg = 'Cannot reach backend server. Please verify the backend is running.';
      }
      return {
        success: false,
        message: errorMsg,
      };
    }
  };

  const logout = () => {
    _clearAuth();
  };

  const refreshBusiness = async () => {
    try {
      // GET /business/profile respects active_business_id on the backend.
      // Do not carry a stale demo header — read current state first, then fetch.
      const b = await businessAPI.getProfile();
      setBusiness(b);
      if (b?.is_demo) {
        localStorage.setItem('subwise_demo_mode', 'true');
      } else {
        localStorage.removeItem('subwise_demo_mode');
      }
      return b;
    } catch (e) {
      console.error('Business refresh failed:', e);
    }
  };

  const switchBusinessMode = async (mode) => {
    try {
      // Clear (or set) the demo localStorage flag BEFORE making any API calls
      // so the axios interceptor does not send a stale X-SubWise-Demo-Mode header
      // on the switch-profile request or the subsequent refreshBusiness call.
      if (mode === 'demo') {
        localStorage.setItem('subwise_demo_mode', 'true');
      } else {
        localStorage.removeItem('subwise_demo_mode');
      }

      const switched = await businessAPI.switchProfile(mode);
      setBusiness(switched);

      // Keep localStorage in sync with actual server response
      if (switched?.is_demo) {
        localStorage.setItem('subwise_demo_mode', 'true');
      } else {
        localStorage.removeItem('subwise_demo_mode');
      }
      return { success: true, business: switched };
    } catch (e) {
      console.error('Business profile switch failed:', e);
      return { success: false, error: e };
    }
  };

  const isDemoMode = Boolean(business?.is_demo || business?.profile_type === 'DEMO');
  const isDemoUser = Boolean(user?.email === 'demo@subwise.io');

  const exitDemoSession = () => {
    _clearAuth();
    return true;
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        business,
        isDemoMode,
        isDemoUser,
        exitDemoSession,
        loading: initialLoading,
        initialLoading,
        login,
        register,
        logout,
        refreshBusiness,
        switchBusinessMode,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
