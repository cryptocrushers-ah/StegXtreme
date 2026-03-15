import { useAuthStore } from '../store/authStore';

const BASE_URL = 'http://localhost:8000';

export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const { token, logout } = useAuthStore.getState();

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    logout();
    throw new Error('Session expired. Please log in again.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'An unexpected error occurred');
  }

  return response.json();
}
