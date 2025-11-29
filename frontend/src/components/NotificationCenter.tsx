/**
 * Real-time notifications component with WebSocket support
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useWebSocket, WebSocketMessage } from '../hooks/useWebSocket';
import './NotificationCenter.css';

export interface Notification {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action?: {
    label: string;
    url: string;
  };
}

interface NotificationCenterProps {
  userId?: string;
  token?: string;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({ userId, token }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // WebSocket configuration
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${
    window.location.host
  }/ws/notifications`;

  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'notification') {
      const newNotification: Notification = {
        id: message.data.id || Date.now().toString(),
        type: message.data.type || 'info',
        title: message.data.title,
        message: message.data.message,
        timestamp: message.timestamp || new Date().toISOString(),
        read: false,
        action: message.data.action,
      };

      setNotifications((prev) => [newNotification, ...prev]);
      setUnreadCount((prev) => prev + 1);

      // Show browser notification if permission granted
      if (Notification.permission === 'granted') {
        new Notification(newNotification.title, {
          body: newNotification.message,
          icon: '/logo192.png',
          tag: newNotification.id,
        });
      }
    }
  }, []);

  const { isConnected, sendMessage } = useWebSocket({
    url: wsUrl,
    token,
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('Notification WebSocket connected');
      // Join user's notification room
      if (userId) {
        sendMessage({ type: 'join', room: `user_${userId}` });
      }
    },
  });

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const markAsRead = useCallback((notificationId: string) => {
    setNotifications((prev) =>
      prev.map((notif) =>
        notif.id === notificationId ? { ...notif, read: true } : notif
      )
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((notif) => ({ ...notif, read: true })));
    setUnreadCount(0);
  }, []);

  const clearNotification = useCallback((notificationId: string) => {
    setNotifications((prev) => prev.filter((notif) => notif.id !== notificationId));
    setUnreadCount((prev) => {
      const notif = notifications.find((n) => n.id === notificationId);
      return notif && !notif.read ? prev - 1 : prev;
    });
  }, [notifications]);

  const clearAll = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  const toggleOpen = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const getNotificationIcon = (type: Notification['type']): string => {
    switch (type) {
      case 'success':
        return '✓';
      case 'warning':
        return '⚠';
      case 'error':
        return '✕';
      default:
        return 'ℹ';
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="notification-center">
      <button
        className="notification-bell"
        onClick={toggleOpen}
        aria-label="Notifications"
        aria-expanded={isOpen}
      >
        <span className="bell-icon">🔔</span>
        {unreadCount > 0 && (
          <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
        )}
        {!isConnected && <span className="connection-status offline">●</span>}
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="notification-header">
            <h3>Notifications</h3>
            {notifications.length > 0 && (
              <div className="notification-actions">
                {unreadCount > 0 && (
                  <button className="mark-all-read" onClick={markAllAsRead}>
                    Mark all as read
                  </button>
                )}
                <button className="clear-all" onClick={clearAll}>
                  Clear all
                </button>
              </div>
            )}
          </div>

          <div className="notification-list">
            {notifications.length === 0 ? (
              <div className="no-notifications">
                <span className="empty-icon">📭</span>
                <p>No notifications</p>
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`notification-item ${notif.type} ${notif.read ? 'read' : 'unread'}`}
                  onClick={() => markAsRead(notif.id)}
                >
                  <div className="notification-icon">
                    {getNotificationIcon(notif.type)}
                  </div>
                  <div className="notification-content">
                    <div className="notification-title">{notif.title}</div>
                    <div className="notification-message">{notif.message}</div>
                    <div className="notification-footer">
                      <span className="notification-time">
                        {formatTimestamp(notif.timestamp)}
                      </span>
                      {notif.action && (
                        <a
                          href={notif.action.url}
                          className="notification-action"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {notif.action.label}
                        </a>
                      )}
                    </div>
                  </div>
                  <button
                    className="notification-close"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearNotification(notif.id);
                    }}
                    aria-label="Dismiss notification"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;
