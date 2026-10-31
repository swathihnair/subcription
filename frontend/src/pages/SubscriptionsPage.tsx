/**
 * Subscriptions listing and management page - Module 2
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { subscriptionService } from '@/services/module2'
import { SubscriptionWithDetails } from '@/types'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

export function SubscriptionsPage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [formData, setFormData] = useState({
    customer_id: '',
    plan_id: '',
    start_date: new Date().toISOString().split('T')[0],
    status: 'active',
    auto_renew: true,
  })
  const queryClient = useQueryClient()

  // Fetch customers for dropdown
  const { data: customersData } = useQuery({
    queryKey: ['customers-dropdown'],
    queryFn: () =>
      subscriptionService.getCustomers({
        page: 1,
        pageSize: 1000,
        status: 'active',
      }),
    enabled: showCreateModal,
  })

  // Fetch plans for dropdown  
  const { data: plansData } = useQuery({
    queryKey: ['plans-dropdown'],
    queryFn: () =>
      subscriptionService.getPlans({
        page: 1,
        pageSize: 1000,
        status: 'active',
      }),
    enabled: showCreateModal,
  })

  // Fetch subscriptions with filters
  const { data, isLoading, error } = useQuery({
    queryKey: ['subscriptions', page, statusFilter],
    queryFn: () =>
      subscriptionService.getSubscriptions({
        page,
        pageSize: 20,
        status: statusFilter || undefined,
      }),
  })

  // Create subscription mutation
  const createMutation = useMutation({
    mutationFn: (data: any) => subscriptionService.createSubscription(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      setShowCreateModal(false)
      setFormData({
        customer_id: '',
        plan_id: '',
        start_date: new Date().toISOString().split('T')[0],
        status: 'active',
        auto_renew: true,
      })
    },
  })

  // Pause subscription mutation
  const pauseMutation = useMutation({
    mutationFn: (id: string) => subscriptionService.pauseSubscription(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
    },
  })

  // Resume subscription mutation
  const resumeMutation = useMutation({
    mutationFn: (id: string) => subscriptionService.resumeSubscription(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
    },
  })

  // Cancel subscription mutation
  const cancelMutation = useMutation({
    mutationFn: ({
      id,
      immediately,
    }: {
      id: string
      immediately: boolean
    }) => subscriptionService.cancelSubscription(id, { cancel_immediately: immediately }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
    },
  })

  const handlePause = (id: string, number: string) => {
    if (confirm(`Pause subscription ${number}?`)) {
      pauseMutation.mutate(id)
    }
  }

  const handleResume = (id: string, number: string) => {
    if (confirm(`Resume subscription ${number}?`)) {
      resumeMutation.mutate(id)
    }
  }

  const handleCancel = (id: string, number: string) => {
    const immediately = confirm(
      `Cancel subscription ${number}?\n\nClick OK to cancel immediately, or Cancel to schedule cancellation at period end.`
    )
    cancelMutation.mutate({ id, immediately: immediately !== null ? immediately : false })
  }

  const handleCreateSubscription = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'trialing':
        return 'bg-blue-100 text-blue-800'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800'
      case 'cancelled':
        return 'bg-red-100 text-red-800'
      case 'expired':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Subscriptions</h1>
            <p className="text-gray-600 mt-1">Manage customer subscriptions</p>
          </div>
          <Button onClick={() => setShowCreateModal(true)}>Create Subscription</Button>
        </div>

        {/* Filters */}
        <Card className="p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="trialing">Trialing</option>
                <option value="paused">Paused</option>
                <option value="cancelled">Cancelled</option>
                <option value="expired">Expired</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button variant="outline" onClick={() => setStatusFilter('')}>
                Clear Filters
              </Button>
            </div>
          </div>
        </Card>

        {/* Subscriptions List */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
            <p className="mt-4 text-gray-600">Loading subscriptions...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-800">Failed to load subscriptions</p>
          </div>
        )}

        {data && data.data.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-600">No subscriptions found</p>
          </div>
        )}

        {data && data.data.length > 0 && (
          <>
            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Subscription
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Plan
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      MRR
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Next Billing
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.data.map((subscription: SubscriptionWithDetails) => (
                    <tr key={subscription.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900">
                          {subscription.subscription_number}
                        </div>
                        <div className="text-sm text-gray-500">
                          Started {new Date(subscription.start_date).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {subscription.customer ? (
                          <div>
                            <div className="font-medium text-gray-900">
                              {subscription.customer.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {subscription.customer.email}
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {subscription.plan?.name || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        ${(subscription.monthly_recurring_revenue || 0).toFixed(2)}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                            subscription.status
                          )}`}
                        >
                          {subscription.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {subscription.next_billing_date
                          ? new Date(subscription.next_billing_date).toLocaleDateString()
                          : '-'}
                      </td>
                      <td className="px-6 py-4 text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="outline">
                            View
                          </Button>
                          {subscription.status === 'active' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                handlePause(subscription.id, subscription.subscription_number)
                              }
                              disabled={pauseMutation.isPending}
                            >
                              Pause
                            </Button>
                          )}
                          {subscription.status === 'paused' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                handleResume(subscription.id, subscription.subscription_number)
                              }
                              disabled={resumeMutation.isPending}
                            >
                              Resume
                            </Button>
                          )}
                          {(subscription.status === 'active' ||
                            subscription.status === 'paused') && (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() =>
                                handleCancel(subscription.id, subscription.subscription_number)
                              }
                              disabled={cancelMutation.isPending}
                            >
                              Cancel
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data.pagination && data.pagination.totalPages > 1 && (
              <div className="flex justify-between items-center mt-6">
                <div className="text-sm text-gray-700">
                  Showing page {data.pagination.page} of {data.pagination.totalPages}
                  {' • '}
                  {data.pagination.total} total subscriptions
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page >= data.pagination.totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Create Subscription Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">Create Subscription</h2>
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>

                <form onSubmit={handleCreateSubscription} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Customer *
                    </label>
                    <select
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      value={formData.customer_id}
                      onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                    >
                      <option value="">Select a customer</option>
                      {customersData?.data?.map((customer: any) => (
                        <option key={customer.id} value={customer.id}>
                          {customer.name} ({customer.email})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Plan *
                    </label>
                    <select
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      value={formData.plan_id}
                      onChange={(e) => setFormData({ ...formData, plan_id: e.target.value })}
                    >
                      <option value="">Select a plan</option>
                      {plansData?.data?.map((plan: any) => (
                        <option key={plan.id} value={plan.id}>
                          {plan.name} - ${plan.price}/{plan.billing_cycle}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Start Date *
                      </label>
                      <input
                        type="date"
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        value={formData.start_date}
                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Status
                      </label>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                        value={formData.status}
                        onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      >
                        <option value="active">Active</option>
                        <option value="trialing">Trialing</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        className="mr-2"
                        checked={formData.auto_renew}
                        onChange={(e) =>
                          setFormData({ ...formData, auto_renew: e.target.checked })
                        }
                      />
                      <span className="text-sm font-medium text-gray-700">Auto-renew</span>
                    </label>
                  </div>

                  {createMutation.isError && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3">
                      <p className="text-sm text-red-800">Failed to create subscription</p>
                    </div>
                  )}

                  <div className="flex justify-end gap-3 pt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setShowCreateModal(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={createMutation.isPending}>
                      {createMutation.isPending ? 'Creating...' : 'Create Subscription'}
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
