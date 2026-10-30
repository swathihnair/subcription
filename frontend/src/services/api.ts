/**
 * API client and HTTP utilities
 */
import axios, { AxiosInstance, AxiosError } from 'axios'
import { ApiResponse, ErrorResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1'

class ApiClient {
  private client: AxiosInstance
  private tokenRefreshPromise: Promise<string> | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any

        // Handle 401 Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const newToken = await this.refreshToken()
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              return this.client(originalRequest)
            }
          } catch (refreshError) {
            this.clearAuth()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  private getAccessToken(): string | null {
    return localStorage.getItem('access_token')
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token')
  }

  private async refreshToken(): Promise<string | null> {
    if (this.tokenRefreshPromise) {
      return this.tokenRefreshPromise
    }

    const refreshToken = this.getRefreshToken()
    if (!refreshToken) {
      return null
    }

    this.tokenRefreshPromise = (async () => {
      try {
        const response = await this.client.post<any>('/auth/refresh', {}, {
          headers: {
            Authorization: `Bearer ${refreshToken}`,
          },
        })

        const newToken = response.data.data.access_token
        localStorage.setItem('access_token', newToken)
        return newToken
      } finally {
        this.tokenRefreshPromise = null
      }
    })()

    return this.tokenRefreshPromise
  }

  public setAuth(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }

  public clearAuth(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  public isAuthenticated(): boolean {
    return !!this.getAccessToken()
  }

  public get<T = any>(url: string, config?: any): Promise<ApiResponse<T>> {
    return this.client.get<ApiResponse<T>>(url, config).then((res) => res.data)
  }

  public post<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    return this.client.post<ApiResponse<T>>(url, data, config).then((res) => res.data)
  }

  public put<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    return this.client.put<ApiResponse<T>>(url, data, config).then((res) => res.data)
  }

  public patch<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    return this.client.patch<ApiResponse<T>>(url, data, config).then((res) => res.data)
  }

  public delete<T = any>(url: string, config?: any): Promise<ApiResponse<T>> {
    return this.client.delete<ApiResponse<T>>(url, config).then((res) => res.data)
  }
}

export const apiClient = new ApiClient()
