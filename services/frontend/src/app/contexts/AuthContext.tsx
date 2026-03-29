import React, { createContext, useContext, useState, useEffect } from 'react';
import { login, register as apiRegister, getProfile } from '../api/auth';
import api from '../api/client';

export type UserRole = 'driver' | 'enforcement' | 'admin';
export type Region = 'IE' | 'GB' | 'FR';

// Map backend region strings → frontend Region type
const REGION_MAP: Record<string, Region> = {
  EU_WEST_IRELAND: 'IE',
  EU_WEST_UK: 'GB',
  EU_WEST_FRANCE: 'FR',
  IE: 'IE', GB: 'GB', FR: 'FR',
};

// Map backend role strings → frontend UserRole
const ROLE_MAP: Record<string, UserRole> = {
  driver: 'driver',
  enforcement_agent: 'enforcement',
  admin: 'admin',
};

// Map frontend Region → backend region string
const REGION_TO_BACKEND: Record<Region, string> = {
  IE: 'EU_WEST_IRELAND',
  GB: 'EU_WEST_UK',
  FR: 'EU_WEST_FRANCE',
};

export interface User {
  id: string;
  email: string;
  role: UserRole;
  region: Region;
  plateNumber?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, role: UserRole, region: Region, plateNumber?: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Rehydrate from token on mount
  useEffect(() => {
    const token = localStorage.getItem('routepass_token');
    const stored = localStorage.getItem('routepass_user');
    if (token && stored) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setUser(JSON.parse(stored));
    }
    setLoading(false);
  }, []);

  const signIn = async (email: string, password: string) => {
    const res = await login(email, password);
    const { access_token, user_id, role } = res.data;

    localStorage.setItem('routepass_token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    // Fetch full profile to get plate_number and region
    const profile = await getProfile();
    const userData: User = {
      id: user_id,
      email,
      role: ROLE_MAP[role] ?? 'driver',
      region: REGION_MAP[profile.data.region ?? ''] ?? 'IE',
      plateNumber: profile.data.plate_number,
    };
    localStorage.setItem('routepass_user', JSON.stringify(userData));
    setUser(userData);
  };

  const signUp = async (
    email: string,
    password: string,
    role: UserRole,
    region: Region,
    plateNumber?: string
  ) => {
    const backendRole = role === 'enforcement' ? 'enforcement_agent' : role;
    const payload: any = {
      email,
      password,
      role: backendRole,
      region: REGION_TO_BACKEND[region],
    };
    if (plateNumber) payload.plate_number = plateNumber;

    const res = await apiRegister(payload);
    const { access_token, user_id } = res.data;

    localStorage.setItem('routepass_token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    const userData: User = { id: user_id, email, role, region, plateNumber };
    localStorage.setItem('routepass_user', JSON.stringify(userData));
    setUser(userData);
  };

  const signOut = () => {
    localStorage.removeItem('routepass_token');
    localStorage.removeItem('routepass_user');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  };

  if (loading) return null;

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
