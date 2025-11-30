/**
 * Notifications Management Page
 * Displays user notifications with filtering, pagination, and bulk actions
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './NotificationsPage.css';

interface Notification {
  id: number;
  type: string;
  channel: string;
  status: string;
  title: string;
  message: string;
  action_url?: string;
  sent_at?: string;
  delivered_at?: string;
  read_at?: string;
  created_at: string;
}

interface NotificationStats {
  total: number;
  unread: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
}

const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(20);
  
  // Selection
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const token = localStorage.getItem('token');

  const fetchNotifications = useCallback(async () => {
    if (!token) {
      navigate('/login');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params: any = {
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
      };

      if (selectedType !== 'all') params.type = selectedType;
      if (selectedStatus !== 'all') params.status = selectedStatus;
      if (showUnreadOnly) params.unread_only = true;

      const response = await axios.get('/api/v1/notifications/', {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });

      setNotifications(response.data.items || []);
      setTotalPages(Math.ceil((response.data.total || 0) / pageSize));
    } catch (err: any) {
      console.error('Failed to fetch notifications:', err);
      setError(err.response?.data?.detail || 'Failed to load notifications');
      
      if (err.response?.status === 401) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  }, [token, navigate, currentPage, pageSize, selectedType, selectedStatus, showUnreadOnly]);

  const fetchStats = useCallback(async () => {
    if (!token) return;

    try {
      const response = await axios.get('/api/v1/notifications/stats', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch notification stats:', err);
    }
  }, [token]);

  useEffect(() => {
    fetchNotifications();
    fetchStats();
  }, [fetchNotifications, fetchStats]);

  const handleMarkAsRead = async (ids?: number[]) => {
    if (!token) return;

    const notificationIds = ids || Array.from(selectedIds);
    if (notificationIds.length === 0) return;

    try {
      await axios.post(
        '/api/v1/notifications/mark-read',
        { notification_ids: notificationIds },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Update local state
      setNotifications((prev) =>
        prev.map((n) =>
          notificationIds.includes(n.id) ? { ...n, status: 'read', read_at: new Date().toISOString() } : n
        )
      );
      setSelectedIds(new Set());
      fetchStats();
    } catch (err: any) {
      console.error('Failed to mark as read:', err);
      alert(err.response?.data?.detail || 'Failed to mark notifications as read');
    }
  };

  const handleSelectAll = () => {
    if (selectedIds.size === notifications.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(notifications.map((n) => n.id)));
    }
  };

  const handleToggleSelect = (id: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const getNotificationIcon = (type: string): string => {
    const icons: Record<string, string> = {
      appointment_reminder: '📅',
      appointment_confirmed: '✅',
      appointment_cancelled: '❌',
      lab_result: '🔬',
      prescription_ready: '💊',
      message_received: '💬',
      system_alert: '⚠️',
      security_alert: '🔒',
      payment_reminder: '💰',
      general: '📢',
    };
    return icons[type] || '📢';
  };

  const getStatusBadge = (status: string): JSX.Element => {
    const colors: Record<string, string> = {
      pending: 'gray',
      sent: 'blue',
      delivered: 'green',
      failed: 'red',
      read: 'teal',
    };
    return <span className={`status-badge status-${colors[status] || 'gray'}`}>{status}</span>;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading && notifications.length === 0) {
    return (
      <div className="notifications-page">
        <div className="loading-spinner">Loading notifications...</div>
      </div>
    );
  }

  return (
    <div className="notifications-page">
      <div className="notifications-header">
        <h1>Notifications</h1>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/notifications/preferences')}
        >
          ⚙️ Preferences
        </button>
      </div>

      {stats && (
        <div className="notification-stats">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total</div>
          </div>
          <div className="stat-card highlight">
            <div className="stat-value">{stats.unread}</div>
            <div className="stat-label">Unread</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.by_status?.delivered || 0}</div>
            <div className="stat-label">Delivered</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.by_status?.failed || 0}</div>
            <div className="stat-label">Failed</div>
          </div>
        </div>
      )}

      <div className="notifications-filters">
        <div className="filter-group">
          <label>Type:</label>
          <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
            <option value="all">All Types</option>
            <option value="appointment_reminder">Appointment Reminder</option>
            <option value="appointment_confirmed">Appointment Confirmed</option>
            <option value="lab_result">Lab Result</option>
            <option value="prescription_ready">Prescription Ready</option>
            <option value="message_received">Message Received</option>
            <option value="system_alert">System Alert</option>
            <option value="security_alert">Security Alert</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Status:</label>
          <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)}>
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="sent">Sent</option>
            <option value="delivered">Delivered</option>
            <option value="read">Read</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div className="filter-group">
          <label>
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={(e) => setShowUnreadOnly(e.target.checked)}
            />
            Unread only
          </label>
        </div>
      </div>

      {selectedIds.size > 0 && (
        <div className="bulk-actions">
          <span>{selectedIds.size} selected</span>
          <button className="btn btn-secondary" onClick={() => handleMarkAsRead()}>
            Mark as Read
          </button>
          <button className="btn btn-ghost" onClick={() => setSelectedIds(new Set())}>
            Clear Selection
          </button>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <div className="notifications-list">
        {notifications.length === 0 ? (
          <div className="empty-state">
            <p>No notifications found</p>
          </div>
        ) : (
          <>
            <div className="list-header">
              <input
                type="checkbox"
                checked={selectedIds.size === notifications.length && notifications.length > 0}
                onChange={handleSelectAll}
              />
              <span>Select All</span>
            </div>

            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`notification-item ${notification.read_at ? 'read' : 'unread'}`}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(notification.id)}
                  onChange={() => handleToggleSelect(notification.id)}
                />
                
                <div className="notification-icon">
                  {getNotificationIcon(notification.type)}
                </div>

                <div className="notification-content">
                  <div className="notification-header-row">
                    <h3>{notification.title}</h3>
                    {getStatusBadge(notification.status)}
                  </div>
                  <p className="notification-message">{notification.message}</p>
                  <div className="notification-meta">
                    <span className="notification-time">{formatDate(notification.created_at)}</span>
                    <span className="notification-channel">{notification.channel}</span>
                    {notification.read_at && (
                      <span className="read-time">Read {formatDate(notification.read_at)}</span>
                    )}
                  </div>
                </div>

                <div className="notification-actions">
                  {!notification.read_at && (
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => handleMarkAsRead([notification.id])}
                    >
                      Mark Read
                    </button>
                  )}
                  {notification.action_url && (
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => navigate(notification.action_url!)}
                    >
                      View
                    </button>
                  )}
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-secondary"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((p) => p - 1)}
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            className="btn btn-secondary"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default NotificationsPage;
