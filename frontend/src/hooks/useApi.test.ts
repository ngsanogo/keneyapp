import { renderHook } from '@testing-library/react';
import { useApi } from './useApi';

describe('useApi Hook', () => {
  test('returns correct initial state', () => {
    const { result } = renderHook(() => useApi());
    
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.execute).toBe('function');
    expect(typeof result.current.reset).toBe('function');
  });

  test('has execute function for API calls', () => {
    const { result } = renderHook(() => useApi());
    expect(result.current.execute).toBeDefined();
    expect(typeof result.current.execute).toBe('function');
  });

  test('has reset function to clear state', () => {
    const { result } = renderHook(() => useApi());
    expect(result.current.reset).toBeDefined();
    expect(typeof result.current.reset).toBe('function');
  });
});
