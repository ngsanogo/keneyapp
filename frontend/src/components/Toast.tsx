import React from 'react';

type ToastProps = {
  message: string | null;
  type?: 'success' | 'error' | 'info';
  onClose?: () => void;
};

export const Toast: React.FC<ToastProps> = ({ message, type = 'info', onClose }) => {
  if (!message) return null;
  const cls = type === 'error' ? 'alert alert-error' : type === 'success' ? 'alert alert-success' : 'alert';
  return (
    <div role="status" className={cls} style={{ position: 'fixed', right: 16, bottom: 16, zIndex: 1000 }}>
      <span>{message}</span>
      {onClose && (
        <button aria-label="Close" className="btn btn-sm" onClick={onClose} style={{ marginLeft: 8 }}>
          ×
        </button>
      )}
    </div>
  );
};
