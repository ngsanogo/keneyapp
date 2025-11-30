/**
 * Tests for NotificationsPage Component
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import NotificationsPage from '../pages/NotificationsPage';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

const mockNotifications = [
  {
    id: 1,
    type: 'appointment_reminder',
    channel: 'email',
    status: 'delivered',
    title: 'Appointment Reminder',
    message: 'You have an appointment tomorrow',
    created_at: new Date().toISOString(),
    read_at: null,
  },
  {
    id: 2,
    type: 'lab_result',
    channel: 'push',
    status: 'read',
    title: 'Lab Results Ready',
    message: 'Your lab results are available',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    read_at: new Date().toISOString(),
  },
];

const mockStats = {
  total: 10,
  unread: 5,
  by_type: { appointment_reminder: 3, lab_result: 2 },
  by_status: { delivered: 5, read: 5 },
};

describe('NotificationsPage', () => {
  beforeEach(() => {
    localStorage.setItem('token', 'test-token');
    mockedAxios.get.mockResolvedValue({
      data: { items: mockNotifications, total: 10 },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('renders notifications page', async () => {
    render(
      <BrowserRouter>
        <NotificationsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });
  });

  it('fetches and displays notifications', async () => {
    render(
      <BrowserRouter>
        <NotificationsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Appointment Reminder')).toBeInTheDocument();
      expect(screen.getByText('Lab Results Ready')).toBeInTheDocument();
    });
  });

  it('filters notifications by type', async () => {
    render(
      <BrowserRouter>
        <NotificationsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Appointment Reminder')).toBeInTheDocument();
    });

    const typeSelect = screen.getByLabelText(/Type:/i).closest('select');
    if (typeSelect) {
      fireEvent.change(typeSelect, { target: { value: 'lab_result' } });
    }

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          params: expect.objectContaining({ type: 'lab_result' }),
        })
      );
    });
  });

  it('marks notification as read', async () => {
    mockedAxios.post.mockResolvedValue({ data: { success: true } });

    render(
      <BrowserRouter>
        <NotificationsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Appointment Reminder')).toBeInTheDocument();
    });

    const markReadButtons = screen.getAllByText('Mark Read');
    fireEvent.click(markReadButtons[0]);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/notifications/mark-read',
        expect.objectContaining({ notification_ids: [1] }),
        expect.any(Object)
      );
    });
  });
});
