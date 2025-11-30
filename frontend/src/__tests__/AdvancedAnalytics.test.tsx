/**
 * Tests for AdvancedAnalytics Component
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import AdvancedAnalytics from '../components/AdvancedAnalytics';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

const mockMetrics = {
  total_patients: 150,
  new_patients: 20,
  total_appointments: 300,
  completed_appointments: 250,
  cancelled_appointments: 20,
  total_prescriptions: 180,
  total_doctors: 15,
  average_appointments_per_patient: 2.0,
  completion_rate: 83.33,
  cancellation_rate: 6.67,
};

const mockAgeDistribution = {
  age_ranges: [
    { range: '0-10', count: 15 },
    { range: '11-20', count: 25 },
    { range: '21-30', count: 35 },
  ],
};

const mockDoctorPerformance = [
  {
    doctor_id: 1,
    doctor_name: 'Dr. Smith',
    total_appointments: 50,
    completed_appointments: 45,
    completion_rate: 90.0,
    average_rating: 4.5,
  },
];

describe('AdvancedAnalytics', () => {
  const mockToken = 'test-token';

  beforeEach(() => {
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('custom-period')) {
        return Promise.resolve({ data: mockMetrics });
      }
      if (url.includes('age-distribution')) {
        return Promise.resolve({ data: mockAgeDistribution });
      }
      if (url.includes('doctor-performance')) {
        return Promise.resolve({ data: mockDoctorPerformance });
      }
      return Promise.reject(new Error('Unknown URL'));
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders analytics dashboard', async () => {
    render(<AdvancedAnalytics token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('Advanced Analytics')).toBeInTheDocument();
    });
  });

  it('displays metrics correctly', async () => {
    render(<AdvancedAnalytics token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // total patients
      expect(screen.getByText('300')).toBeInTheDocument(); // total appointments
    });
  });

  it('switches between tabs', async () => {
    render(<AdvancedAnalytics token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });

    const patientTab = screen.getByText('Patient Analytics');
    fireEvent.click(patientTab);

    expect(screen.getByText('Patient Age Distribution')).toBeInTheDocument();

    const doctorTab = screen.getByText('Doctor Performance');
    fireEvent.click(doctorTab);

    await waitFor(() => {
      expect(screen.getByText('Top 10 Doctors by Appointments')).toBeInTheDocument();
    });
  });

  it('applies date range filter', async () => {
    render(<AdvancedAnalytics token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('Advanced Analytics')).toBeInTheDocument();
    });

    const fromInput = screen.getAllByLabelText('From:')[0];
    fireEvent.change(fromInput, { target: { value: '2024-01-01' } });

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('custom-period'),
        expect.objectContaining({
          params: expect.objectContaining({ date_from: '2024-01-01' }),
        })
      );
    });
  });

  it('uses quick range buttons', async () => {
    render(<AdvancedAnalytics token={mockToken} />);

    await waitFor(() => {
      expect(screen.getByText('Last 7 Days')).toBeInTheDocument();
    });

    const last7DaysButton = screen.getByText('Last 7 Days');
    fireEvent.click(last7DaysButton);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalled();
    });
  });
});
