import React, { createContext, useState, useEffect, useContext } from 'react';
import { api } from '../services/api';
import { ZarUser } from '../model/User';


const AuthContext = createContext(null);


export const useAuth = (): {
  user: ZarUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<any>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<ZarUser | null>
} => useContext(AuthContext as any);


export const AuthProvider = ({ children }: {children: any}) => {
  
  const [user, setUser] = useState<ZarUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkUser = async () => {
      try {
        const u: ZarUser = await api.getMe();
        setUser(u);
      } catch (error) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    checkUser();
  }, []);

  const login = async (email: string, password: string) => {
    const u = await api.login({ email, password })
    setUser(u)
    return u
  };

  const signup = async (email: string, password: string) => {
    await api.signup({ email, password })
  };

  const logout = async () => {
    try {
      await api.logout()
    } catch (error) {
      console.error("Logout failed, but clearing user state.", error);
    } finally {
      setUser(null);
    }
  };

  const refreshUser = async (): Promise<ZarUser | null> => {
    try {
      const u = await api.refreshSession()
      setUser(u)
      return u
    } catch (err) {
      console.log(err)
    }
    return null
  }

  const value: {
    user: ZarUser | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<any>;
    signup: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<ZarUser | null>;
} = {
    user,
    loading,
    login,
    signup,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value as any}>
      {!loading && children}
    </AuthContext.Provider>
  );
};