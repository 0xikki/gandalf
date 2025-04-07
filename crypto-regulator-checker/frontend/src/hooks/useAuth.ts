import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>(() => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    return {
      token,
      user: userStr ? JSON.parse(userStr) : null,
    };
  });
  
  const navigate = useNavigate();

  const login = useCallback(async (email: string, password: string) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: email, // FastAPI OAuth2 expects 'username'
          password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      const { access_token } = data;

      // Fetch user details
      const userResponse = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${access_token}`,
        },
      });

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user details');
      }

      const user = await userResponse.json();

      // Update local storage and state
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      setAuthState({ token: access_token, user });

      // Redirect to home page
      navigate('/');
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }, [navigate]);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setAuthState({ token: null, user: null });
    navigate('/login');
  }, [navigate]);

  const checkAuth = useCallback(async () => {
    const { token } = authState;
    if (!token) {
      logout();
      return;
    }

    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Session expired');
      }

      const user = await response.json();
      setAuthState({ token, user });
    } catch (error) {
      logout();
    }
  }, [authState.token, logout]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return {
    user: authState.user,
    token: authState.token,
    login,
    logout,
    isAuthenticated: !!authState.token,
  };
}; 