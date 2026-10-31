import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { financeService } from '@/services/billing'
import { OutstandingBalance } from '@/types'

export const FinanceDashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['finance-summary'],
    queryFn: () => financeService.getSummary(),
  })

  const { data: outstandingData, isLoading: outstandingLoading } = useQuery({
    queryKey: ['outstanding-balances', page, pageSize],
    queryFn: () => financeService.getOutstandingBalances({ page, pageSize }),
  })

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const summary = summaryData?.data

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Finance Dashboard</h1>
        <p className="text-gray-600">Financial overview and outstanding balances</p>
      </div>

      {/* Summary Cards */}
      {summaryLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      ) : summary ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Total Invoiced */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Invoiced</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">
                    {formatCurrency(summary.total_invoiced)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {summary.total_invoices} invoices
                  </p>
                </div>
                <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Total Paid */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Paid</p>
                  <p className="text-2xl font-bold text-green-600 mt-2">
                    {formatCurrency(summary.total_paid)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {summary.by_status?.paid?.count || 0} paid invoices
                  </p>
                </div>
                <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Total Outstanding */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Outstanding</p>
                  <p className="text-2xl font-bold text-orange-600 mt-2">
                    {formatCurrency(summary.total_outstanding)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {(summary.by_status?.open?.count || 0) + (summary.by_status?.partially_paid?.count || 0)} invoices
                  </p>
                </div>
                <div className="h-12 w-12 bg-orange-100 rounded-full flex items-center justify-center">
                  <svg className="h-6 w-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Total Overdue */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Overdue</p>
                  <p className="text-2xl font-bold text-red-600 mt-2">
                    {formatCurrency(summary.total_overdue)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {summary.by_status?.overdue?.count || 0} overdue invoices
                  </p>
                </div>
                <div className="h-12 w-12 bg-red-100 rounded-full flex items-center justify-center">
                  <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* Status Breakdown */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Invoice Status Breakdown</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {summary.by_status && Object.entries(summary.by_status).map(([status, data]) => (
                <div key={status} className="border border-gray-200 rounded-lg p-4">
                  <p className="text-xs font-medium text-gray-500 uppercase">{status}</p>
                  <p className="text-xl font-bold text-gray-900 mt-1">{data.count}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {formatCurrency(data.amount_due)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : null}

      {/* Outstanding Balances */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Outstanding Balances by Customer</h2>
          <button
            onClick={() => navigate('/invoices?status=open,partially_paid,overdue')}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            View All Invoices →
          </button>
        </div>

        {outstandingLoading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
          </div>
        ) : outstandingData && outstandingData.data && outstandingData.data.length > 0 ? (
          <>
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Invoices
                  </th>
                  <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Outstanding
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {outstandingData.data.map((balance: OutstandingBalance) => (
                  <tr key={balance.customer_id} className="hover:bg-gray-50">
                    <td className="py-3 text-sm font-medium text-gray-900">
                      {balance.company_name}
                    </td>
                    <td className="py-3 text-sm text-gray-600">
                      {balance.email}
                    </td>
                    <td className="py-3 text-sm text-right text-gray-900">
                      {balance.invoice_count}
                    </td>
                    <td className="py-3 text-sm text-right font-medium text-red-600">
                      {formatCurrency(balance.total_outstanding)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {outstandingData.pagination && outstandingData.pagination.totalPages > 1 && (
              <div className="mt-4 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Page {outstandingData.pagination.page} of {outstandingData.pagination.totalPages}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page >= (outstandingData.pagination.totalPages || 1)}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <p className="text-center py-8 text-gray-500">No outstanding balances</p>
        )}
      </div>
    </div>
  )
}
