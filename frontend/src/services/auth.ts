/**
 * Authentication service
 */
import { apiClient } from './api'
import { AuthResponse, LoginCredentials, User } from '../types'

export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials)
    if (response.success && response.data) {
      apiClient.setAuth(response.data.access_token, response.data.refresh_token || '')
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }
    return response
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout')
    } finally {
      apiClient.clearAuth()
      localStorage.removeItem('user')
    }
  },

  getCurrentUser: (): User | null => {
    const user = localStorage.getItem('user')
    return user ? JSON.parse(user) : null
  },

  fetchCurrentUser: async (): Promise<AuthResponse> => {
    const response = await apiClient.get<User>('/auth/me')
    if (response.success && response.data) {
      localStorage.setItem('user', JSON.stringify(response.data))
    }
    return response as AuthResponse
  },

  isAuthenticated: (): boolean => {
    return apiClient.isAuthenticated()
  },

  register: async (email: string, password: string, firstName?: string, lastName?: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/register', {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
    })
    if (response.success && response.data) {
      apiClient.setAuth(response.data.access_token, response.data.refresh_token || '')
      localStorage.setItem('user', JSON.stringify(response.data.user))
    }
    return response
  },
}
