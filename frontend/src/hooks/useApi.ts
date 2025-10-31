import { useState, useCallback } from 'react';
import axios, { AxiosError, AxiosRequestConfig } from 'axios';

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (config: AxiosRequestConfig) => Promise<T | null>;
  reset: () => void;
}

/**
 * Custom hook for making API calls with built-in loading and error states.
 * Provides a consistent pattern for handling API interactions throughout the app.
 *
 * @example
 * ```typescript
 * const { data, loading, error, execute } = useApi<Patient[]>();
 *
 * useEffect(() => {
 *   execute({
 *     method: 'GET',
 *     url: '/api/v1/patients',
 *     headers: { Authorization: `Bearer ${token}` }
 *   });
 * }, []);
 * ```
 */
export function useApi<T = any>(): UseApiReturn<T> {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async (config: AxiosRequestConfig): Promise<T | null> => {
    setState({ data: null, loading: true, error: null });

    try {
      const response = await axios(config);
      setState({ data: response.data, loading: false, error: null });
      return response.data;
    } catch (err) {
      const error = err as AxiosError<any>;
      let errorMessage = 'An unexpected error occurred';

      if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        
        // Map common status codes to user-friendly messages
        if (status === 401) {
          errorMessage = 'Authentication required. Please log in again.';
        } else if (status === 403) {
          errorMessage = 'You do not have permission to perform this action.';
        } else if (status === 404) {
          errorMessage = 'The requested resource was not found.';
        } else if (status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else {
          // Only use server message for client errors (400-499)
          errorMessage = error.response.data?.detail || error.response.data?.message || errorMessage;
        }
      } else if (error.request) {
        // Request made but no response received
        errorMessage = 'Network error. Please check your connection.';
      } else {
        // Something else happened
        errorMessage = 'An unexpected error occurred. Please try again.';
      }

      setState({ data: null, loading: false, error: errorMessage });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    data: state.data,
    loading: state.loading,
    error: state.error,
    execute,
    reset,
  };
}

export default useApi;
