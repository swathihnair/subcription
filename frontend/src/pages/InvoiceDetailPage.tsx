import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { invoiceService } from '@/services/billing'
import { InvoiceWithDetails, Payment } from '@/types'

export const InvoiceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showRecordPayment, setShowRecordPayment] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => invoiceService.getInvoice(id!),
    enabled: !!id,
  })

  const { data: paymentsData } = useQuery({
    queryKey: ['invoice-payments', id],
    queryFn: () => invoiceService.getInvoicePayments(id!),
    enabled: !!id,
  })

  const issueMutation = useMutation({
    mutationFn: (invoiceId: string) => invoiceService.issueInvoice(invoiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] })
      alert('Invoice issued successfully')
    },
    onError: () => {
      alert('Failed to issue invoice')
    },
  })

  const voidMutation = useMutation({
    mutationFn: (invoiceId: string) => {
      const reason = prompt('Enter reason for voiding (optional):')
      return invoiceService.voidInvoice(invoiceId, reason || undefined)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] })
      alert('Invoice voided successfully')
    },
    onError: () => {
      alert('Failed to void invoice')
    },
  })

  const handleDownloadPdf = async () => {
    if (!data?.data) return
    try {
      const blob = await invoiceService.downloadInvoicePdf(data.data.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `invoice_${data.data.invoice_number}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      alert('Failed to download PDF')
    }
  }

  const handleIssueInvoice = () => {
    if (id && confirm('Are you sure you want to issue this invoice?')) {
      issueMutation.mutate(id)
    }
  }

  const handleVoidInvoice = () => {
    if (id && confirm('Are you sure you want to void this invoice? This cannot be undone.')) {
      voidMutation.mutate(id)
    }
  }

  if (isLoading) {
    return (
      <div className="p-6 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        <p className="mt-2 text-gray-600">Loading invoice...</p>
      </div>
    )
  }

  if (error || !data?.data) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Failed to load invoice. Please try again.
        </div>
      </div>
    )
  }

  const invoice: InvoiceWithDetails = data.data

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex justify-between items-start">
        <div>
          <button
            onClick={() => navigate('/invoices')}
            className="text-blue-600 hover:text-blue-800 mb-2"
          >
            ← Back to Invoices
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{invoice.invoice_number}</h1>
          <p className="text-gray-600">Invoice Details</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleDownloadPdf}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Download PDF
          </button>
          {invoice.status === 'draft' && (
            <button
              onClick={handleIssueInvoice}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Issue Invoice
            </button>
          )}
          {invoice.status !== 'void' && invoice.status !== 'paid' && (
            <button
              onClick={handleVoidInvoice}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Void Invoice
            </button>
          )}
        </div>
      </div>

      {/* Invoice Info */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-3">Invoice Information</h3>
            <dl className="space-y-2">
              <div className="flex justify-between">
                <dt className="text-sm text-gray-600">Status:</dt>
                <dd className="text-sm font-medium text-gray-900">{invoice.status}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-600">Invoice Date:</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {new Date(invoice.invoice_date).toLocaleDateString()}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-sm text-gray-600">Due Date:</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {new Date(invoice.due_date).toLocaleDateString()}
                </dd>
              </div>
              {invoice.billing_period_start && invoice.billing_period_end && (
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-600">Billing Period:</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {new Date(invoice.billing_period_start).toLocaleDateString()} - {new Date(invoice.billing_period_end).toLocaleDateString()}
                  </dd>
                </div>
              )}
            </dl>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-3">Customer</h3>
            <div className="text-sm text-gray-900">
              <p className="font-medium">{invoice.customer?.company_name || 'N/A'}</p>
              <p>{invoice.customer?.email}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Line Items */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Line Items</h3>
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr>
              <th className="text-left text-xs font-medium text-gray-500 uppercase">Description</th>
              <th className="text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
              <th className="text-right text-xs font-medium text-gray-500 uppercase">Unit Price</th>
              <th className="text-right text-xs font-medium text-gray-500 uppercase">Discount</th>
              <th className="text-right text-xs font-medium text-gray-500 uppercase">Tax</th>
              <th className="text-right text-xs font-medium text-gray-500 uppercase">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {invoice.line_items?.map((item) => (
              <tr key={item.id}>
                <td className="py-3 text-sm text-gray-900">{item.description}</td>
                <td className="py-3 text-sm text-right text-gray-900">{item.quantity}</td>
                <td className="py-3 text-sm text-right text-gray-900">${item.unit_price.toFixed(2)}</td>
                <td className="py-3 text-sm text-right text-gray-900">${item.discount_amount.toFixed(2)}</td>
                <td className="py-3 text-sm text-right text-gray-900">${item.tax_amount.toFixed(2)}</td>
                <td className="py-3 text-sm text-right font-medium text-gray-900">${item.total_amount.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Totals */}
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="max-w-xs ml-auto space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Subtotal:</span>
            <span className="text-gray-900">${invoice.subtotal_amount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Tax:</span>
            <span className="text-gray-900">${invoice.tax_amount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-base font-bold border-t pt-2">
            <span className="text-gray-900">Total:</span>
            <span className="text-gray-900">${invoice.total_amount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Paid:</span>
            <span className="text-green-600">${invoice.amount_paid.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-base font-bold border-t pt-2">
            <span className="text-gray-900">Amount Due:</span>
            <span className="text-red-600">${invoice.amount_due.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Payment History */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Payment History</h3>
          {invoice.status !== 'void' && invoice.status !== 'paid' && (
            <button
              onClick={() => navigate(`/invoices/${id}/record-payment`)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              Record Payment
            </button>
          )}
        </div>
        {paymentsData?.data && paymentsData.data.length > 0 ? (
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 uppercase">Payment #</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {paymentsData.data.map((payment: Payment) => (
                <tr key={payment.id}>
                  <td className="py-3 text-sm text-gray-900">{payment.payment_number}</td>
                  <td className="py-3 text-sm text-gray-900">
                    {new Date(payment.payment_date).toLocaleDateString()}
                  </td>
                  <td className="py-3 text-sm text-gray-900">{payment.payment_method}</td>
                  <td className="py-3 text-sm text-right text-gray-900">${payment.amount.toFixed(2)}</td>
                  <td className="py-3 text-sm text-gray-900">{payment.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-gray-500 text-center py-4">No payments recorded</p>
        )}
      </div>
    </div>
  )
}
