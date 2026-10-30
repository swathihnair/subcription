/**
 * useAuth hook for authentication state management
 */
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '@/services/auth'
import { User, LoginCredentials } from '@/types'

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  // Initialize auth state from storage
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          const currentUser = authService.getCurrentUser()
          if (currentUser) {
            setUser(currentUser)
          } else {
            // Try to fetch fresh user data
            const response = await authService.fetchCurrentUser()
            if (response.success && response.data) {
              setUser(response.data)
            } else {
              authService.logout()
            }
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Authentication error')
        authService.logout()
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    setLoading(true)
    setError(null)
    try {
      const response = await authService.login(credentials)
      if (response.success && response.data) {
        setUser(response.data.user)
        navigate('/dashboard')
        return response
      } else {
        const errorMsg = response.error?.message || 'Login failed'
        setError(errorMsg)
        throw new Error(errorMsg)
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Login failed'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [navigate])

  const logout = useCallback(async () => {
    setLoading(true)
    try {
      await authService.logout()
      setUser(null)
      navigate('/login')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Logout failed')
    } finally {
      setLoading(false)
    }
  }, [navigate])

  const hasPermission = useCallback((permission: string): boolean => {
    if (!user?.role) return false

    const rolePermissions: Record<string, string[]> = {
      admin: ['all'],
      finance: ['view_invoices', 'manage_payments', 'view_analytics'],
      sales: ['manage_customers', 'manage_products', 'manage_subscriptions'],
      customer: ['view_own_subscriptions', 'view_own_invoices'],
    }

    const permissions = rolePermissions[user.role.name] || []
    return permissions.includes('all') || permissions.includes(permission)
  }, [user])

  return {
    user,
    loading,
    error,
    login,
    logout,
    hasPermission,
    isAuthenticated: authService.isAuthenticated(),
  }
}
