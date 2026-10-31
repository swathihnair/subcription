import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../services/module4';
import { Card } from '../components/ui/Card';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function AnalyticsDashboardPage() {
  const { data: overview } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: analyticsApi.getOverview
  });

  const { data: mrr } = useQuery({
    queryKey: ['analytics-mrr'],
    queryFn: analyticsApi.getMRR
  });

  const { data: subscriptionData } = useQuery({
    queryKey: ['analytics-subscriptions'],
    queryFn: analyticsApi.getSubscriptions
  });

  const { data: invoiceData } = useQuery({
    queryKey: ['analytics-invoices'],
    queryFn: analyticsApi.getInvoices
  });

  // Transform data for charts
  const subscriptionStatusData = subscriptionData?.by_status
    ? Object.entries(subscriptionData.by_status).map(([status, count]) => ({
        name: status,
        value: count as number
      }))
    : [];

  const planDistributionData = subscriptionData?.by_plan
    ? Object.entries(subscriptionData.by_plan).map(([plan, count]) => ({
        name: plan,
        subscriptions: count as number
      }))
    : [];

  const invoiceStatusData = invoiceData?.by_status
    ? Object.entries(invoiceData.by_status).map(([status, data]: [string, any]) => ({
        name: status,
        count: data.count,
        amount: data.total_amount
      }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <p className="text-gray-600 mt-2">Business metrics and insights</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6">
          <h3 className="text-sm font-medium text-gray-600">Total Customers</h3>
          <p className="text-3xl font-bold mt-2">{overview?.total_customers || 0}</p>
        </Card>

        <Card className="p-6">
          <h3 className="text-sm font-medium text-gray-600">Active Subscriptions</h3>
          <p className="text-3xl font-bold mt-2">{overview?.active_subscriptions || 0}</p>
        </Card>

        <Card className="p-6">
          <h3 className="text-sm font-medium text-gray-600">MRR</h3>
          <p className="text-3xl font-bold mt-2 text-green-600">
            ${overview?.monthly_recurring_revenue?.toFixed(2) || '0.00'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            ARR: ${overview?.annual_recurring_revenue?.toFixed(2) || '0.00'}
          </p>
        </Card>

        <Card className="p-6">
          <h3 className="text-sm font-medium text-gray-600">Outstanding</h3>
          <p className="text-3xl font-bold mt-2 text-orange-600">
            ${overview?.total_outstanding?.toFixed(2) || '0.00'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {overview?.overdue_invoices || 0} overdue invoices
          </p>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subscription Status Distribution */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Subscription Status</h2>
          {subscriptionStatusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={subscriptionStatusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {subscriptionStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-12">No data available</p>
          )}
        </Card>

        {/* Subscriptions by Plan */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Subscriptions by Plan</h2>
          {planDistributionData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={planDistributionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="subscriptions" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-12">No data available</p>
          )}
        </Card>

        {/* Invoice Status */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Invoice Status Overview</h2>
          {invoiceStatusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={invoiceStatusData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8" name="Count" />
                <Bar dataKey="amount" fill="#82ca9d" name="Amount ($)" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-12">No data available</p>
          )}
        </Card>

        {/* MRR by Plan */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">MRR by Plan</h2>
          {mrr?.by_plan && Object.keys(mrr.by_plan).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(mrr.by_plan).map(([plan, value]) => (
                <div key={plan} className="flex justify-between items-center border-b pb-2">
                  <span className="font-medium">{plan}</span>
                  <span className="text-green-600 font-bold">
                    ${(value as number).toFixed(2)}
                  </span>
                </div>
              ))}
              <div className="flex justify-between items-center pt-2 border-t-2">
                <span className="font-bold">Total MRR</span>
                <span className="text-green-600 font-bold text-lg">
                  ${mrr.current_mrr?.toFixed(2)}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-12">No MRR data available</p>
          )}
        </Card>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Subscription Growth</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">New subscriptions</span>
              <span className="font-bold text-green-600">+{subscriptionData?.new_subscriptions || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Cancelled</span>
              <span className="font-bold text-red-600">-{subscriptionData?.cancelled_subscriptions || 0}</span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Outstanding Invoices</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Total amount</span>
              <span className="font-bold">${invoiceData?.outstanding_amount?.toFixed(2) || '0.00'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Overdue amount</span>
              <span className="font-bold text-red-600">${invoiceData?.overdue_amount?.toFixed(2) || '0.00'}</span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Revenue Metrics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">MRR</span>
              <span className="font-bold text-green-600">${overview?.monthly_recurring_revenue?.toFixed(2) || '0.00'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">ARR</span>
              <span className="font-bold text-blue-600">${overview?.annual_recurring_revenue?.toFixed(2) || '0.00'}</span>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <p className="text-sm text-gray-500">
          <strong>Note:</strong> MRR is calculated from active subscription monthly_recurring_revenue fields. 
          ARR is MRR × 12. Metrics reflect current state of the database.
        </p>
      </Card>
    </div>
  );
}
