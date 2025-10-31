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
        errorMessage = error.response.data?.detail || error.response.data?.message || errorMessage;
      } else if (error.request) {
        // Request made but no response received
        errorMessage = 'Network error. Please check your connection.';
      } else {
        // Something else happened
        errorMessage = error.message || errorMessage;
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
