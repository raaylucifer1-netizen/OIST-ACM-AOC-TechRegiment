import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '@/lib/api';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_verified: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (access_token: string, refresh_token: string) => void;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      
      login: (access_token: string, refresh_token: string) => {
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        set({ isAuthenticated: true });
        get().fetchUser();
      },
      
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, isAuthenticated: false, isLoading: false });
      },
      
      fetchUser: async () => {
        try {
          const response = await api.get('/auth/me');
          set({ user: response.data, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ isAuthenticated: state.isAuthenticated }), // Only persist auth status initially
    }
  )
);
