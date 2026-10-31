import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '../services/module4';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useState } from 'react';

export default function NotificationsPage() {
  const [filter, setFilter] = useState<string>('');
  const queryClient = useQueryClient();

  const { data: notificationsData } = useQuery({
    queryKey: ['notifications', filter],
    queryFn: () => notificationsApi.getNotifications({ type: filter || undefined })
  });

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: notificationsApi.getUnreadCount
  });

  const markAsReadMutation = useMutation({
    mutationFn: notificationsApi.markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] });
    }
  });

  const markAllAsReadMutation = useMutation({
    mutationFn: notificationsApi.markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] });
    }
  });

  const notifications = notificationsData || [];

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'invoice_issued':
      case 'invoice_due_soon':
      case 'invoice_overdue':
        return '📄';
      case 'payment_recorded':
        return '💳';
      case 'subscription_created':
      case 'subscription_activated':
        return '✅';
      case 'subscription_cancelled':
        return '❌';
      case 'renewal_approaching':
        return '🔄';
      default:
        return '📌';
    }
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="text-gray-600 mt-2">
            {unreadCount?.count || 0} unread notification{unreadCount?.count !== 1 ? 's' : ''}
          </p>
        </div>
        {notifications.length > 0 && (
          <Button
            onClick={() => markAllAsReadMutation.mutate()}
            disabled={markAllAsReadMutation.isPending}
          >
            Mark All as Read
          </Button>
        )}
      </div>

      <div className="flex gap-2 flex-wrap">
        <Button
          variant={filter === '' ? 'primary' : 'outline'}
          onClick={() => setFilter('')}
          size="sm"
        >
          All
        </Button>
        <Button
          variant={filter === 'invoice_issued' ? 'primary' : 'outline'}
          onClick={() => setFilter('invoice_issued')}
          size="sm"
        >
          Invoices
        </Button>
        <Button
          variant={filter === 'payment_recorded' ? 'primary' : 'outline'}
          onClick={() => setFilter('payment_recorded')}
          size="sm"
        >
          Payments
        </Button>
        <Button
          variant={filter === 'subscription_created' ? 'primary' : 'outline'}
          onClick={() => setFilter('subscription_created')}
          size="sm"
        >
          Subscriptions
        </Button>
        <Button
          variant={filter === 'renewal_approaching' ? 'primary' : 'outline'}
          onClick={() => setFilter('renewal_approaching')}
          size="sm"
        >
          Renewals
        </Button>
      </div>

      {notifications.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-gray-500">No notifications</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {notifications.map((notification: any) => (
            <Card
              key={notification.id}
              className={`p-4 ${notification.is_read ? 'bg-white' : 'bg-blue-50'}`}
            >
              <div className="flex items-start gap-4">
                <div className="text-2xl">{getNotificationIcon(notification.type)}</div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold">{notification.subject}</h3>
                      <p className="text-gray-600 mt-1">{notification.message}</p>
                      <p className="text-sm text-gray-400 mt-2">
                        {formatDate(notification.created_at)}
                      </p>
                    </div>
                    {!notification.is_read && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => markAsReadMutation.mutate(notification.id)}
                        disabled={markAsReadMutation.isPending}
                      >
                        Mark as Read
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
