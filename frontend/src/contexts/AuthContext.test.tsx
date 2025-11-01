import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('AuthContext', () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear();
    // Clear all mocks
    jest.clearAllMocks();
  });

  test('provides initial state', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.loading).toBe(false);
  });

  test('login function calls API endpoint', async () => {
    const mockResponse = {
      data: {
        access_token: 'test-token',
        token_type: 'bearer',
      },
    };

    const mockUserResponse = {
      data: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'doctor',
        tenant_id: 1,
        mfa_enabled: false,
        is_locked: false,
      },
    };

    mockedAxios.post.mockResolvedValueOnce(mockResponse);
    mockedAxios.get.mockResolvedValueOnce(mockUserResponse);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login('testuser', 'password');
    });

    // Verify login API was called
    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/login'),
      expect.any(FormData)
    );
  });

  test('logout clears user and token', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  test('throws error when useAuth is used outside AuthProvider', () => {
    // Suppress console.error for this test
    const originalError = console.error;
    console.error = jest.fn();

    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within an AuthProvider');

    console.error = originalError;
  });
});
