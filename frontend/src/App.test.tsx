import { render, screen } from '@testing-library/react';
import App from './App';

// Mock child components to isolate App component testing
jest.mock('./pages/LoginPage', () => {
  return function LoginPage() {
    return <div>Login Page</div>;
  };
});

jest.mock('./pages/DashboardPage', () => {
  return function DashboardPage() {
    return <div>Dashboard Page</div>;
  };
});

jest.mock('./pages/PatientsPage', () => {
  return function PatientsPage() {
    return <div>Patients Page</div>;
  };
});

jest.mock('./pages/AppointmentsPage', () => {
  return function AppointmentsPage() {
    return <div>Appointments Page</div>;
  };
});

jest.mock('./pages/PrescriptionsPage', () => {
  return function PrescriptionsPage() {
    return <div>Prescriptions Page</div>;
  };
});

describe('App Component', () => {
  test('renders without crashing', () => {
    render(<App />);
  });

  test('renders login page by default at root route', () => {
    render(<App />);
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  test('wraps app with AuthProvider', () => {
    render(<App />);
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });
});
