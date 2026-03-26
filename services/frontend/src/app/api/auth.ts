import api from './client';

export interface RegisterPayload {
  email: string;
  password: string;
  role: string;
  region: string;
  plate_number?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  role: string;
}

export interface ProfileResponse {
  id: string;
  email: string;
  role: string;
  plate_number?: string;
  region?: string;
}

// POST /auth/register
export const register = (data: RegisterPayload) =>
  api.post<AuthResponse>('/auth/register', data);

// POST /auth/login
export const login = (email: string, password: string) =>
  api.post<AuthResponse>('/auth/login', { email, password });

// GET /auth/profile
export const getProfile = () =>
  api.get<ProfileResponse>('/auth/profile');
