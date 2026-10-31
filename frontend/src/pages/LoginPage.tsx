import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { apiClient } from '@/services/api'

export const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('password123')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const response = await apiClient.post('/auth/login', { email, password })
      
      if (response.success && response.data) {
        // Store tokens and user
        apiClient.setAuth(response.data.access_token, response.data.refresh_token || '')
        localStorage.setItem('user', JSON.stringify(response.data.user))
        
        // Redirect to dashboard
        navigate('/dashboard')
      } else {
        setError(response.error?.message || 'Login failed')
      }
    } catch (err) {
      console.error('Login error:', err)
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        <Card>
          <CardHeader>
            <div className="text-center mb-4">
              <h1 className="text-2xl font-bold text-gray-900">SubscriptIQ</h1>
              <p className="text-sm text-gray-600 mt-1">
                Subscription Management & Revenue Intelligence
              </p>
            </div>
            <CardTitle className="text-center">Sign In</CardTitle>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <p className="text-sm font-medium text-red-800">{error}</p>
                </div>
              )}

              <Input
                type="email"
                label="Email Address"
                placeholder="admin@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />

              <Input
                type="password"
                label="Password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />

              <Button
                type="submit"
                className="w-full"
                isLoading={loading}
                disabled={loading}
              >
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>

              <div className="text-center text-sm text-gray-600">
                <p>
                  Demo credentials:<br />
                  Email: admin@example.com<br />
                  Password: password123
                </p>
              </div>
            </form>
          </CardContent>
        </Card>

        <p className="mt-6 text-center text-sm text-gray-600">
          SubscriptIQ © 2024 Brightloop Software
        </p>
      </div>
    </div>
  )
}
