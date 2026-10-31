/**
 * Create Subscription Page - Module 2
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { subscriptionService, customerService, productService, planService } from '../services/module2'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'

export function CreateSubscriptionPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    customer_id: '',
    plan_id: '',
    start_date: new Date().toISOString().split('T')[0],
    quantity: '1',
  })
  const [selectedProductId, setSelectedProductId] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Fetch customers
  const { data: customersData } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customerService.getCustomers({ page: 1, pageSize: 100 }),
  })

  // Fetch products
  const { data: productsData } = useQuery({
    queryKey: ['products'],
    queryFn: () => productService.getProducts({ page: 1, pageSize: 100, status: 'active' }),
  })

  // Fetch plans for selected product
  const { data: plansData } = useQuery({
    queryKey: ['plans', selectedProductId],
    queryFn: () => planService.getPlans({ page: 1, pageSize: 100, product_id: selectedProductId, status: 'active' }),
    enabled: !!selectedProductId,
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => subscriptionService.createSubscription(data),
    onSuccess: () => {
      navigate('/subscriptions')
    },
    onError: (error: any) => {
      if (error.response?.data?.error?.details) {
        setErrors(error.response.data.error.details)
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    // Validate
    const newErrors: Record<string, string> = {}
    if (!formData.customer_id) newErrors.customer_id = 'Customer is required'
    if (!formData.plan_id) newErrors.plan_id = 'Plan is required'
    if (!formData.start_date) newErrors.start_date = 'Start date is required'
    if (!formData.quantity || parseInt(formData.quantity) < 1) {
      newErrors.quantity = 'Valid quantity is required'
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    createMutation.mutate({
      ...formData,
      quantity: parseInt(formData.quantity),
    })
  }

  const selectedPlan = plansData?.data?.items?.find((p: any) => p.id === formData.plan_id)

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <Button variant="outline" onClick={() => navigate('/subscriptions')}>
            ← Back to Subscriptions
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Create Subscription</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer <span className="text-red-500">*</span>
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  required
                >
                  <option value="">Select a customer</option>
                  {customersData?.data?.items?.map((customer: any) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.name} ({customer.email})
                    </option>
                  ))}
                </select>
                {errors.customer_id && (
                  <p className="mt-1 text-sm text-red-600">{errors.customer_id}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Product <span className="text-red-500">*</span>
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={selectedProductId}
                  onChange={(e) => {
                    setSelectedProductId(e.target.value)
                    setFormData({ ...formData, plan_id: '' })
                  }}
                  required
                >
                  <option value="">Select a product</option>
                  {productsData?.data?.items?.map((product: any) => (
                    <option key={product.id} value={product.id}>
                      {product.name} - ${product.base_price}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Plan <span className="text-red-500">*</span>
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={formData.plan_id}
                  onChange={(e) => setFormData({ ...formData, plan_id: e.target.value })}
                  required
                  disabled={!selectedProductId}
                >
                  <option value="">Select a plan</option>
                  {plansData?.data?.items?.map((plan: any) => (
                    <option key={plan.id} value={plan.id}>
                      {plan.name} - ${plan.price}/{plan.billing_cycle}
                    </option>
                  ))}
                </select>
                {errors.plan_id && (
                  <p className="mt-1 text-sm text-red-600">{errors.plan_id}</p>
                )}
              </div>

              <Input
                label="Start Date"
                type="date"
                required
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                error={errors.start_date}
              />

              <Input
                label="Quantity"
                type="number"
                min="1"
                required
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                error={errors.quantity}
              />

              {selectedPlan && (
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="pt-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Subscription Summary</h4>
                    <div className="space-y-1 text-sm">
                      <p><span className="font-medium">Plan:</span> {selectedPlan.name}</p>
                      <p><span className="font-medium">Price:</span> ${selectedPlan.price}</p>
                      <p><span className="font-medium">Billing:</span> {selectedPlan.billing_cycle}</p>
                      <p><span className="font-medium">Quantity:</span> {formData.quantity || 1}</p>
                      <p className="text-lg font-bold mt-2">
                        Total: ${(parseFloat(selectedPlan.price) * parseInt(formData.quantity || '1')).toFixed(2)}/{selectedPlan.billing_cycle}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {createMutation.error && (
                <div className="rounded-md bg-red-50 p-4">
                  <p className="text-sm font-medium text-red-800">
                    {(createMutation.error as any).response?.data?.error?.message || 'Failed to create subscription'}
                  </p>
                </div>
              )}

              <div className="flex gap-4">
                <Button
                  type="submit"
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Subscription'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/subscriptions')}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
