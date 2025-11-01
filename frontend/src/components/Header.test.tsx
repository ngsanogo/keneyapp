import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Header from './Header';
import { AuthContext } from '../contexts/AuthContext';

const mockLogout = jest.fn();

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
  logout: mockLogout,
  refreshUser: jest.fn(),
  isAuthenticated: true,
  loading: false,
};

const renderHeader = (authValue = mockAuthContextValue) => {
  return render(
    <AuthContext.Provider value={authValue}>
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    </AuthContext.Provider>
  );
};

describe('Header Component', () => {
  beforeEach(() => {
    mockLogout.mockClear();
  });

  test('renders header with user info', () => {
    renderHeader();
    expect(screen.getByText(/Test User/i)).toBeInTheDocument();
  });

  test('renders navigation links', () => {
    renderHeader();
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Patients/i)).toBeInTheDocument();
  });

  test('calls logout when logout button is clicked', () => {
    renderHeader();
    const logoutButton = screen.getByText(/Logout/i);
    fireEvent.click(logoutButton);
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  test('displays user role', () => {
    renderHeader();
    expect(screen.getByText(/doctor/i)).toBeInTheDocument();
  });
});
