/**
 * Modal for creating a new subscription
 */
import { useState } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { subscriptionService, customerService, planService } from '../services/module2'
import { Button } from './ui/Button'
import { Card } from './ui/Card'

interface CreateSubscriptionModalProps {
  isOpen: boolean
  onClose: () => void
}

export function CreateSubscriptionModal({ isOpen, onClose }: CreateSubscriptionModalProps) {
  const [customerId, setCustomerId] = useState('')
  const [planId, setPlanId] = useState('')
  const [quantity, setQuantity] = useState('1')
  const [autoRenew, setAutoRenew] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const queryClient = useQueryClient()

  // Fetch customers
  const { data: customersData } = useQuery({
    queryKey: ['customers-select'],
    queryFn: () => customerService.getCustomers({ pageSize: 100 }),
  })

  // Fetch plans
  const { data: plansData } = useQuery({
    queryKey: ['plans-select'],
    queryFn: () => planService.getPlans({ pageSize: 100 }),
  })

  const mutation = useMutation({
    mutationFn: () =>
      subscriptionService.createSubscription({
        customer_id: customerId,
        plan_id: planId,
        auto_renew: autoRenew,
        status: 'active',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      handleClose()
    },
    onError: (err: any) => {
      const message = err?.response?.data?.error?.message || 'Failed to create subscription'
      setError(message)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!customerId) {
      setError('Please select a customer')
      return
    }
    if (!planId) {
      setError('Please select a plan')
      return
    }

    mutation.mutate()
  }

  const handleClose = () => {
    setCustomerId('')
    setPlanId('')
    setQuantity('1')
    setAutoRenew(true)
    setError(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md p-6">
        <h2 className="text-2xl font-bold mb-4">Create Subscription</h2>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Customer *
            </label>
            <select
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select a customer</option>
              {customersData?.data.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} ({customer.email})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Plan *
            </label>
            <select
              value={planId}
              onChange={(e) => setPlanId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select a plan</option>
              {plansData?.data.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.name} - ${plan.price}/month
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Auto-Renew
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoRenew}
                onChange={(e) => setAutoRenew(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="ml-2 text-sm text-gray-600">Enable auto-renewal</span>
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={handleClose} type="button">
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={mutation.isPending}>
              {mutation.isPending ? 'Creating...' : 'Create Subscription'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
