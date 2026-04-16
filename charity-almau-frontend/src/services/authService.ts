import api from './api';
import type { User } from '../types/user';

const API_URL = import.meta.env.VITE_API_URL;

export const authService = {
  getLoginUrl(): string {
    return `${API_URL}/api/auth/login`;
  },

  async devLogin(email: string, name: string): Promise<{ token: string; user: User }> {
    const res = await api.post('/auth/dev-login', { email, name });
    return (res as unknown as { data: { token: string; user: User } }).data;
  },

  async getMe(): Promise<User> {
    const res = await api.get('/auth/me');
    return (res as unknown as { data: { user: User } }).data.user;
  },
};
