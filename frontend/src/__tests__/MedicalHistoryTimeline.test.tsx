import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import MedicalHistoryTimeline from '../components/MedicalHistoryTimeline';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('MedicalHistoryTimeline', () => {
  const mockEvents = [
    {
      id: 1,
      date: '2024-11-20T10:00:00Z',
      type: 'appointment',
      title: 'Regular Checkup',
      description: 'Annual physical examination',
      doctor: 'Dr. Smith',
      status: 'completed',
    },
    {
      id: 2,
      date: '2024-11-15T14:30:00Z',
      type: 'prescription',
      title: 'Prescription - Amoxicillin',
      description: '500mg, twice daily, 10 days',
      doctor: 'Dr. Jones',
      status: 'active',
    },
    {
      id: 3,
      date: '2024-11-10T09:00:00Z',
      type: 'lab_result',
      title: 'Lab Test - Blood Panel',
      description: 'Result: Normal range',
      status: 'completed',
    },
  ];

  beforeEach(() => {
    localStorage.setItem('token', 'test-token');
    mockedAxios.get.mockResolvedValue({ data: mockEvents });
  });

  afterEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders timeline header', async () => {
    render(<MedicalHistoryTimeline patientId={1} />);

    expect(screen.getByText('Medical History Timeline')).toBeInTheDocument();
  });

  test('fetches and displays medical history events', async () => {
    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/patients/1/history'),
        expect.any(Object)
      );
    });

    await waitFor(() => {
      expect(screen.getByText('Regular Checkup')).toBeInTheDocument();
      expect(screen.getByText('Prescription - Amoxicillin')).toBeInTheDocument();
      expect(screen.getByText('Lab Test - Blood Panel')).toBeInTheDocument();
    });
  });

  test('displays loading state', () => {
    mockedAxios.get.mockImplementation(() => new Promise(() => {}));
    render(<MedicalHistoryTimeline patientId={1} />);

    expect(screen.getByText('Loading medical history...')).toBeInTheDocument();
  });

  test('displays error state', async () => {
    mockedAxios.get.mockRejectedValue({
      response: { data: { detail: 'Failed to load' } },
    });

    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
    });
  });

  test('filters events by type', async () => {
    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Regular Checkup')).toBeInTheDocument();
    });

    const filterSelect = screen.getByRole('combobox');
    fireEvent.change(filterSelect, { target: { value: 'prescription' } });

    // Should show only prescription, hide others
    await waitFor(() => {
      expect(screen.getByText('Prescription - Amoxicillin')).toBeInTheDocument();
      expect(screen.queryByText('Regular Checkup')).not.toBeInTheDocument();
    });
  });

  test('toggles sort order', async () => {
    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Regular Checkup')).toBeInTheDocument();
    });

    const sortButton = screen.getByTitle(/Sort/);
    fireEvent.click(sortButton);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('sort=asc'),
        expect.any(Object)
      );
    });
  });

  test('displays statistics', async () => {
    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Total Events')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument(); // Total count
      expect(screen.getByText('Appointments')).toBeInTheDocument();
      expect(screen.getByText('Prescriptions')).toBeInTheDocument();
    });
  });

  test('opens event details modal', async () => {
    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Regular Checkup')).toBeInTheDocument();
    });

    const eventItem = screen.getByText('Regular Checkup');
    fireEvent.click(eventItem);

    await waitFor(() => {
      // Modal should show detailed information
      expect(screen.getByText('Type:')).toBeInTheDocument();
      expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
    });
  });

  test('closes modal on click outside', async () => {
    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Regular Checkup')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Regular Checkup'));

    const modal = screen.getByRole('dialog', { hidden: true });
    fireEvent.click(modal);

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  test('exports timeline to PDF', async () => {
    global.URL.createObjectURL = jest.fn(() => 'blob:test');
    const link = document.createElement('a');
    jest.spyOn(document, 'createElement').mockReturnValue(link);
    const clickSpy = jest.spyOn(link, 'click');

    mockedAxios.get.mockResolvedValueOnce({ data: mockEvents });
    mockedAxios.get.mockResolvedValueOnce({ data: new Blob(['pdf content']) });

    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Regular Checkup')).toBeInTheDocument();
    });

    const pdfButton = screen.getByText(/PDF/);
    fireEvent.click(pdfButton);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/export/pdf'),
        expect.objectContaining({ responseType: 'blob' })
      );
      expect(clickSpy).toHaveBeenCalled();
    });
  });

  test('refreshes timeline', async () => {
    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByTitle('Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });
  });

  test('applies date range filters', async () => {
    render(
      <MedicalHistoryTimeline
        patientId={1}
        startDate="2024-11-01"
        endDate="2024-11-30"
      />
    );

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-11-01'),
        expect.any(Object)
      );
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-11-30'),
        expect.any(Object)
      );
    });
  });

  test('filters by event types', async () => {
    render(
      <MedicalHistoryTimeline
        patientId={1}
        eventTypes={['appointment', 'prescription']}
      />
    );

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('event_types=appointment'),
        expect.any(Object)
      );
    });
  });

  test('displays empty state when no events', async () => {
    mockedAxios.get.mockResolvedValue({ data: [] });

    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/No events found/)).toBeInTheDocument();
    });
  });

  test('retries on error', async () => {
    mockedAxios.get.mockRejectedValueOnce({
      response: { data: { detail: 'Server error' } },
    });
    mockedAxios.get.mockResolvedValueOnce({ data: mockEvents });

    render(<MedicalHistoryTimeline patientId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Server error/)).toBeInTheDocument();
    });

    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Regular Checkup')).toBeInTheDocument();
    });
  });
});
