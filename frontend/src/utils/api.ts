import { useAuthStore } from '../store/authStore';

const BASE_URL = 'http://localhost:8000';

export async function apiRequest(endpoint: string, options: RequestInit = {}, returnRaw: boolean = false) {
  const { token, logout } = useAuthStore.getState();

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  try {
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

    if (returnRaw) {
      return response;
    }

    return response.json();
  } catch (err: any) {
    if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
      throw new Error('Backend unreachable. Please ensure the FastAPI server is running on http://localhost:8000.');
    }
    throw err;
  }
}
