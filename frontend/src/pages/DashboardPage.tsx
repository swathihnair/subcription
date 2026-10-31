import { useAuth } from '@/hooks/useAuth'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Link } from 'react-router-dom'

export const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">SubscriptIQ</h1>
            <p className="text-sm text-gray-600">Dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">
                {user?.first_name || user?.email}
              </p>
              <p className="text-xs text-gray-600 capitalize">{user?.role?.name}</p>
            </div>
            <Button variant="outline" size="sm" onClick={logout}>
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      {/* Navigation Menu */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8 py-4">
            <Link 
              to="/dashboard" 
              className="text-gray-900 font-medium border-b-2 border-primary-600 pb-1"
            >
              Dashboard
            </Link>
            <Link 
              to="/products" 
              className="text-gray-600 hover:text-gray-900 font-medium pb-1 border-b-2 border-transparent hover:border-gray-300"
            >
              Products
            </Link>
            <Link 
              to="/subscriptions" 
              className="text-gray-600 hover:text-gray-900 font-medium pb-1 border-b-2 border-transparent hover:border-gray-300"
            >
              Subscriptions
            </Link>
            <Link 
              to="/invoices" 
              className="text-gray-600 hover:text-gray-900 font-medium pb-1 border-b-2 border-transparent hover:border-gray-300"
            >
              Invoices
            </Link>
            <Link 
              to="/payments" 
              className="text-gray-600 hover:text-gray-900 font-medium pb-1 border-b-2 border-transparent hover:border-gray-300"
            >
              Payments
            </Link>
            <Link 
              to="/billing/jobs" 
              className="text-gray-600 hover:text-gray-900 font-medium pb-1 border-b-2 border-transparent hover:border-gray-300"
            >
              Billing Jobs
            </Link>
            <Link 
              to="/finance" 
              className="text-gray-600 hover:text-gray-900 font-medium pb-1 border-b-2 border-transparent hover:border-gray-300"
            >
              Finance
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Welcome Section */}
          <Card>
            <CardHeader>
              <CardTitle>Welcome to SubscriptIQ</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">
                You are now on the core platform foundation. This dashboard is a placeholder
                that will be enhanced with real analytics and data from the business modules.
              </p>
              <p className="text-sm text-gray-500">
                Module Integration Status:
              </p>
              <ul className="mt-4 space-y-2 text-sm">
                <li className="flex items-center">
                  <span className="inline-block w-3 h-3 bg-yellow-400 rounded-full mr-2"></span>
                  Module 2: Sales & Subscriptions (In Development)
                </li>
                <li className="flex items-center">
                  <span className="inline-block w-3 h-3 bg-yellow-400 rounded-full mr-2"></span>
                  Module 3: Billing & Payments (In Development)
                </li>
                <li className="flex items-center">
                  <span className="inline-block w-3 h-3 bg-yellow-400 rounded-full mr-2"></span>
                  Module 4: Analytics & Notifications (In Development)
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Placeholder Metrics */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-gray-600 text-sm font-medium">Active Subscriptions</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">—</p>
                  <p className="text-xs text-gray-500 mt-1">Coming from Module 2</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-gray-600 text-sm font-medium">Total Customers</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">—</p>
                  <p className="text-xs text-gray-500 mt-1">Coming from Module 2</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-gray-600 text-sm font-medium">Monthly Recurring Revenue</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">—</p>
                  <p className="text-xs text-gray-500 mt-1">Coming from Module 3</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-gray-600 text-sm font-medium">Outstanding Invoices</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">—</p>
                  <p className="text-xs text-gray-500 mt-1">Coming from Module 3</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Module 3: Billing & Finance Quick Access */}
          <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
            <CardHeader>
              <CardTitle className="text-blue-900">💰 Module 3: Billing, Invoices & Finance</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-blue-800 mb-6">
                Access all billing and finance features - now available!
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Link to="/invoices">
                  <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-4 border border-blue-200 h-full">
                    <div className="text-3xl mb-2">📄</div>
                    <h3 className="font-semibold text-gray-900 mb-1">Invoices</h3>
                    <p className="text-xs text-gray-600">
                      Create, view, and manage invoices
                    </p>
                  </div>
                </Link>

                <Link to="/payments">
                  <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-4 border border-blue-200 h-full">
                    <div className="text-3xl mb-2">💳</div>
                    <h3 className="font-semibold text-gray-900 mb-1">Payments</h3>
                    <p className="text-xs text-gray-600">
                      Record and track payments
                    </p>
                  </div>
                </Link>

                <Link to="/billing/jobs">
                  <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-4 border border-blue-200 h-full">
                    <div className="text-3xl mb-2">🔄</div>
                    <h3 className="font-semibold text-gray-900 mb-1">Recurring Billing</h3>
                    <p className="text-xs text-gray-600">
                      Automated billing jobs & history
                    </p>
                  </div>
                </Link>

                <Link to="/finance">
                  <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow p-4 border border-blue-200 h-full">
                    <div className="text-3xl mb-2">📊</div>
                    <h3 className="font-semibold text-gray-900 mb-1">Finance Dashboard</h3>
                    <p className="text-xs text-gray-600">
                      Financial overview & analytics
                    </p>
                  </div>
                </Link>
              </div>

              <div className="mt-6 pt-4 border-t border-blue-200">
                <p className="text-xs text-blue-700 font-medium mb-2">✨ Key Features Available:</p>
                <ul className="grid grid-cols-2 gap-2 text-xs text-blue-800">
                  <li className="flex items-start">
                    <span className="mr-2">✓</span>
                    <span>Create & issue invoices</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">✓</span>
                    <span>Record payments</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">✓</span>
                    <span>Generate PDF invoices</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">✓</span>
                    <span>Financial reporting</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">✓</span>
                    <span>Automated recurring billing</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">✓</span>
                    <span>Outstanding balances tracking</span>
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* API Documentation Links */}
          <Card>
            <CardHeader>
              <CardTitle>Getting Started</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">
                Review the documentation to understand the API contracts and data models:
              </p>
              <ul className="space-y-2 text-sm">
                <li>
                  <a
                    href="https://github.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:text-primary-700 underline"
                  >
                    📖 API Contracts Documentation
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:text-primary-700 underline"
                  >
                    📊 Database Schema
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:text-primary-700 underline"
                  >
                    🏗️ Architecture Overview
                  </a>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
