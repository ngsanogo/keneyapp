import { CSSProperties } from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
  fullScreen?: boolean;
}

/**
 * LoadingSpinner component to display loading states throughout the application.
 * Provides a consistent loading experience with optional size and message customization.
 */
const LoadingSpinner = ({
  size = 'medium',
  message = 'Loading...',
  fullScreen = false,
}: LoadingSpinnerProps) => {
  const sizeMap = {
    small: '24px',
    medium: '48px',
    large: '72px',
  };

  const spinnerSize = sizeMap[size];

  const spinnerStyle: CSSProperties = {
    border: '4px solid #f3f3f3',
    borderTop: '4px solid #007bff',
    borderRadius: '50%',
    width: spinnerSize,
    height: spinnerSize,
    animation: 'spin 1s linear infinite',
  };

  const containerStyle: CSSProperties = fullScreen
    ? {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        zIndex: 9999,
      }
    : {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      };

  return (
    <>
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
      <div style={containerStyle} role="status" aria-live="polite" aria-label={message}>
        <div style={spinnerStyle} aria-hidden="true" />
        {message && (
          <p
            style={{
              marginTop: '16px',
              color: '#6c757d',
              fontSize: size === 'small' ? '14px' : '16px',
            }}
          >
            {message}
          </p>
        )}
      </div>
    </>
  );
};

export default LoadingSpinner;
