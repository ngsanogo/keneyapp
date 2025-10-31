import React, { useEffect, useState } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

interface NotificationToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose?: () => void;
}

/**
 * NotificationToast component for displaying temporary notifications.
 * Automatically dismisses after the specified duration.
 */
const NotificationToast: React.FC<NotificationToastProps> = ({
  message,
  type = 'info',
  duration = 5000,
  onClose,
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      if (onClose) onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  if (!isVisible) return null;

  const typeColors = {
    success: { bg: '#d4edda', border: '#c3e6cb', text: '#155724' },
    error: { bg: '#f8d7da', border: '#f5c6cb', text: '#721c24' },
    warning: { bg: '#fff3cd', border: '#ffeeba', text: '#856404' },
    info: { bg: '#d1ecf1', border: '#bee5eb', text: '#0c5460' },
  };

  const colors = typeColors[type];

  const toastStyle: React.CSSProperties = {
    position: 'fixed',
    top: '20px',
    right: '20px',
    minWidth: '300px',
    maxWidth: '500px',
    backgroundColor: colors.bg,
    color: colors.text,
    padding: '16px',
    borderRadius: '4px',
    border: `1px solid ${colors.border}`,
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    zIndex: 10000,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    animation: 'slideInRight 0.3s ease-out',
  };

  const iconMap = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
  };

  const handleClose = () => {
    setIsVisible(false);
    if (onClose) onClose();
  };

  return (
    <>
      <style>
        {`
          @keyframes slideInRight {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}
      </style>
      <div style={toastStyle} role="alert">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span
            style={{
              fontSize: '20px',
              fontWeight: 'bold',
              width: '24px',
              height: '24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {iconMap[type]}
          </span>
          <span style={{ flex: 1 }}>{message}</span>
        </div>
        <button
          onClick={handleClose}
          style={{
            background: 'none',
            border: 'none',
            color: colors.text,
            fontSize: '20px',
            cursor: 'pointer',
            padding: '0 8px',
            marginLeft: '12px',
          }}
          aria-label="Close notification"
        >
          ×
        </button>
      </div>
    </>
  );
};

export default NotificationToast;
