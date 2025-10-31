import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary component to catch and display errors in the React component tree.
 * This provides a better user experience by showing a fallback UI instead of crashing the app.
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error details for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });

    // You can also log the error to an error reporting service here
    // Example: logErrorToService(error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: '40px',
            textAlign: 'center',
            maxWidth: '600px',
            margin: '50px auto',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        >
          <h1 style={{ color: '#dc3545', marginBottom: '20px' }}>
            Oops! Something went wrong
          </h1>
          <p style={{ color: '#6c757d', marginBottom: '20px' }}>
            We're sorry for the inconvenience. An error has occurred in the
            application.
          </p>
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details style={{ textAlign: 'left', marginTop: '20px' }}>
              <summary
                style={{
                  cursor: 'pointer',
                  color: '#007bff',
                  marginBottom: '10px',
                }}
              >
                Error Details (Development Mode)
              </summary>
              <pre
                style={{
                  backgroundColor: '#fff',
                  padding: '15px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  border: '1px solid #dee2e6',
                  fontSize: '12px',
                  color: '#212529',
                }}
              >
                {this.state.error.toString()}
                {this.state.errorInfo &&
                  '\n\nComponent Stack:\n' + this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
          <button
            onClick={this.handleReset}
            style={{
              marginTop: '20px',
              padding: '10px 24px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '16px',
            }}
          >
            Try Again
          </button>
          <button
            onClick={() => (window.location.href = '/')}
            style={{
              marginTop: '20px',
              marginLeft: '10px',
              padding: '10px 24px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '16px',
            }}
          >
            Go to Home
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
