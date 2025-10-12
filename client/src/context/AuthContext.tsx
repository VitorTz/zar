import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';
import { ZarUser } from '../model/User';

const AuthContext = createContext(null);


export const useAuth = (): {
  user: ZarUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<any>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
} => useContext(AuthContext as any);


export const AuthProvider = ({ children }: {children: any}) => {
  
  const [user, setUser] = useState<ZarUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    
    const checkUser = async () => {
      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
      } catch (error) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    checkUser();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    setUser(response.data);
    return response.data;
  };

  const signup = async (email: string, password: string) => {
    await api.post('/auth/signup', { email, password });
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error("Logout failed, but clearing user state.", error);
    } finally {
      setUser(null);
    }
  };

  const value: {
    user: ZarUser | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<any>;
    signup: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
} = {
    user,
    loading,
    login,
    signup,
    logout,
  };

  return (
    <AuthContext.Provider value={value as any}>
      {!loading && children}
    </AuthContext.Provider>
  );
};