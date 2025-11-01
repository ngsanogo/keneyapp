import { renderHook } from '@testing-library/react';
import { useApi } from './useApi';
import { AuthContext } from '../contexts/AuthContext';
import React from 'react';

const mockAuthContextValue = {
  user: {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    fullName: 'Test User',
    role: 'doctor' as const,
    tenantId: 1,
    mfaEnabled: false,
    isLocked: false,
  },
  token: 'fake-token',
  login: jest.fn(),
  logout: jest.fn(),
  refreshUser: jest.fn(),
  isAuthenticated: true,
  loading: false,
};

const wrapper = ({ children }: { children: React.ReactNode }) => (
  React.createElement(AuthContext.Provider, { value: mockAuthContextValue }, children)
);

describe('useApi Hook', () => {
  test('returns api instance', () => {
    const { result } = renderHook(() => useApi(), { wrapper });
    expect(result.current).toBeDefined();
    expect(result.current.defaults.baseURL).toBeDefined();
  });

  test('includes authorization header when token is present', () => {
    const { result } = renderHook(() => useApi(), { wrapper });
    expect(result.current.defaults.headers.common['Authorization']).toBe('Bearer fake-token');
  });

  test('sets correct base URL', () => {
    const { result } = renderHook(() => useApi(), { wrapper });
    const baseURL = result.current.defaults.baseURL;
    expect(baseURL).toMatch(/^http/);
  });
});
