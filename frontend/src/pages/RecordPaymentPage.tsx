import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { invoiceService, paymentService } from '@/services/billing'
import { CreatePaymentPayload } from '@/types'

export const RecordPaymentPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState({
    amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_method: 'credit_card',
    external_transaction_id: '',
    notes: '',
  })

  const { data: invoiceData, isLoading } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => invoiceService.getInvoice(id!),
    enabled: !!id,
  })

  const recordPaymentMutation = useMutation({
    mutationFn: (payload: CreatePaymentPayload) => paymentService.recordPayment(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] })
      queryClient.invalidateQueries({ queryKey: ['invoice-payments', id] })
      alert('Payment recorded successfully')
      navigate(`/invoices/${id}`)
    },
    onError: (error: any) => {
      alert(`Failed to record payment: ${error.response?.data?.error?.message || 'Unknown error'}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const payload: CreatePaymentPayload = {
      invoice_id: id!,
      amount: parseFloat(formData.amount),
      payment_date: new Date(formData.payment_date).toISOString(),
      payment_method: formData.payment_method,
      external_transaction_id: formData.external_transaction_id || undefined,
      notes: formData.notes || undefined,
    }

    recordPaymentMutation.mutate(payload)
  }

  if (isLoading) {
    return (
      <div className="p-6 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (!invoiceData?.data) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Invoice not found.
        </div>
      </div>
    )
  }

  const invoice = invoiceData.data

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <button
          onClick={() => navigate(`/invoices/${id}`)}
          className="text-blue-600 hover:text-blue-800 mb-2"
        >
          ← Back to Invoice
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Record Payment</h1>
        <p className="text-gray-600">Invoice: {invoice.invoice_number}</p>
      </div>

      {/* Invoice Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600">Total Amount:</p>
            <p className="font-medium text-gray-900">${invoice.total_amount.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-gray-600">Already Paid:</p>
            <p className="font-medium text-green-600">${invoice.amount_paid.toFixed(2)}</p>
          </div>
          <div className="col-span-2">
            <p className="text-gray-600">Amount Due:</p>
            <p className="text-xl font-bold text-red-600">${invoice.amount_due.toFixed(2)}</p>
          </div>
        </div>
      </div>

      {/* Payment Form */}
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Amount *
          </label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            max={invoice.amount_due}
            value={formData.amount}
            onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
            required
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="0.00"
          />
          <p className="mt-1 text-xs text-gray-500">
            Maximum: ${invoice.amount_due.toFixed(2)}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Payment Date *
          </label>
          <input
            type="date"
            value={formData.payment_date}
            onChange={(e) => setFormData({ ...formData, payment_date: e.target.value })}
            required
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Payment Method *
          </label>
          <select
            value={formData.payment_method}
            onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
            required
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="credit_card">Credit Card</option>
            <option value="bank_transfer">Bank Transfer</option>
            <option value="check">Check</option>
            <option value="cash">Cash</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            External Transaction ID
          </label>
          <input
            type="text"
            value={formData.external_transaction_id}
            onChange={(e) => setFormData({ ...formData, external_transaction_id: e.target.value })}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="e.g., stripe_ch_abc123"
          />
          <p className="mt-1 text-xs text-gray-500">
            Optional: Reference ID from payment gateway (prevents duplicates)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notes
          </label>
          <textarea
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={3}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="Optional notes about this payment..."
          />
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={recordPaymentMutation.isPending}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {recordPaymentMutation.isPending ? 'Recording...' : 'Record Payment'}
          </button>
          <button
            type="button"
            onClick={() => navigate(`/invoices/${id}`)}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
