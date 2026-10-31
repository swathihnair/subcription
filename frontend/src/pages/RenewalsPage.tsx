import { useQuery } from '@tanstack/react-query';
import { renewalsApi } from '../services/module4';
import { Card } from '../components/ui/Card';
import { useState } from 'react';

export default function RenewalsPage() {
  const [activeTab, setActiveTab] = useState<string>('due_soon');

  const { data: renewalsData } = useQuery({
    queryKey: ['renewals'],
    queryFn: renewalsApi.getRenewals
  });

  const { data: summary } = useQuery({
    queryKey: ['renewals-summary'],
    queryFn: renewalsApi.getSummary
  });

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'suspended':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const tabs = [
    { key: 'due_soon', label: 'Due Soon', count: renewalsData?.due_soon?.length || 0 },
    { key: 'due_later', label: 'Due Later', count: renewalsData?.due_later?.length || 0 },
    { key: 'past_due', label: 'Past Due', count: renewalsData?.past_due?.length || 0 },
    { key: 'scheduled_cancellation', label: 'Scheduled Cancellation', count: renewalsData?.scheduled_cancellation?.length || 0 },
    { key: 'recently_renewed', label: 'Recently Renewed', count: renewalsData?.recently_renewed?.length || 0 }
  ];

  const activeSubscriptions = renewalsData?.[activeTab] || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Renewal Management</h1>
        <p className="text-gray-600 mt-2">Track and manage subscription renewals</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-600">Due within 7 days</h3>
          <p className="text-2xl font-bold text-orange-600">{summary?.due_within_7_days || 0}</p>
        </Card>
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-600">Due within 30 days</h3>
          <p className="text-2xl font-bold text-blue-600">{summary?.due_within_30_days || 0}</p>
        </Card>
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-600">Past Due</h3>
          <p className="text-2xl font-bold text-red-600">{summary?.past_due || 0}</p>
        </Card>
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-600">Total Active</h3>
          <p className="text-2xl font-bold text-green-600">{summary?.total_active || 0}</p>
        </Card>
      </div>

      {/* Tabs */}
      <Card className="p-4">
        <div className="flex gap-2 border-b overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 font-medium whitespace-nowrap ${
                activeTab === tab.key
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        {/* Subscription List */}
        <div className="mt-6">
          {activeSubscriptions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No subscriptions in this category</p>
          ) : (
            <div className="space-y-4">
              {activeSubscriptions.map((sub: any) => (
                <div key={sub.id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold text-lg">{sub.subscription_number}</h3>
                        <span className={`text-xs px-2 py-1 rounded ${getStatusColor(sub.status)}`}>
                          {sub.status}
                        </span>
                      </div>
                      <p className="text-gray-600 mt-1">{sub.customer?.name}</p>
                      <div className="flex gap-6 mt-2 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">Plan:</span> {sub.plan?.name}
                        </div>
                        <div>
                          <span className="font-medium">Start:</span> {formatDate(sub.start_date)}
                        </div>
                        {sub.next_billing_date && (
                          <div>
                            <span className="font-medium">Next Billing:</span>{' '}
                            {formatDate(sub.next_billing_date)}
                          </div>
                        )}
                        {sub.end_date && (
                          <div>
                            <span className="font-medium">End:</span> {formatDate(sub.end_date)}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-600">
                        ${parseFloat(sub.monthly_recurring_revenue || 0).toFixed(2)}/mo
                      </p>
                      {sub.auto_renew !== undefined && (
                        <p className="text-xs text-gray-500 mt-1">
                          {sub.auto_renew ? 'Auto-renew enabled' : 'Auto-renew disabled'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
