import { useQuery } from '@tanstack/react-query';
import { portalApi } from '../services/module4';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Link } from 'react-router-dom';

export default function CustomerPortalPage() {
  const { data: profile } = useQuery({
    queryKey: ['portal-profile'],
    queryFn: portalApi.getProfile
  });

  const { data: subscriptions } = useQuery({
    queryKey: ['portal-subscriptions'],
    queryFn: portalApi.getSubscriptions
  });

  const { data: invoices } = useQuery({
    queryKey: ['portal-invoices'],
    queryFn: portalApi.getInvoices
  });

  const activeSubscriptions = subscriptions?.filter(s => s.status === 'active') || [];
  const unpaidInvoices = invoices?.filter(i => i.amount_due > 0) || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Customer Portal</h1>
        <p className="text-gray-600 mt-2">
          Welcome back, {profile?.user?.first_name || 'Customer'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-2">Active Subscriptions</h3>
          <p className="text-3xl font-bold text-blue-600">{activeSubscriptions.length}</p>
          <Link to="/portal/subscriptions">
            <Button variant="link" className="mt-4 p-0">View All →</Button>
          </Link>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-2">Unpaid Invoices</h3>
          <p className="text-3xl font-bold text-orange-600">{unpaidInvoices.length}</p>
          <Link to="/portal/invoices">
            <Button variant="link" className="mt-4 p-0">View All →</Button>
          </Link>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-2">Total Outstanding</h3>
          <p className="text-3xl font-bold text-red-600">
            ${unpaidInvoices.reduce((sum, inv) => sum + parseFloat(inv.amount_due), 0).toFixed(2)}
          </p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Subscriptions</h2>
          {activeSubscriptions.length === 0 ? (
            <p className="text-gray-500">No active subscriptions</p>
          ) : (
            <div className="space-y-3">
              {activeSubscriptions.slice(0, 3).map((sub: any) => (
                <div key={sub.id} className="border-b pb-3 last:border-0">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{sub.subscription_number}</p>
                      <p className="text-sm text-gray-600">
                        Next billing: {sub.next_billing_date ? new Date(sub.next_billing_date).toLocaleDateString() : 'N/A'}
                      </p>
                    </div>
                    <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded">
                      {sub.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Invoices</h2>
          {invoices?.length === 0 ? (
            <p className="text-gray-500">No invoices</p>
          ) : (
            <div className="space-y-3">
              {invoices?.slice(0, 3).map((invoice: any) => (
                <div key={invoice.id} className="border-b pb-3 last:border-0">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{invoice.invoice_number}</p>
                      <p className="text-sm text-gray-600">
                        Due: {new Date(invoice.due_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">${parseFloat(invoice.total_amount).toFixed(2)}</p>
                      <span className={`text-xs px-2 py-1 rounded ${
                        invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                        invoice.status === 'overdue' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {invoice.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
