/**
 * Tests for PatientExport Component
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import PatientExport from '../components/PatientExport';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('PatientExport', () => {
  const mockToken = 'test-token';
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders export component', () => {
    render(<PatientExport token={mockToken} onClose={mockOnClose} />);

    expect(screen.getByText('Export Patient Data')).toBeInTheDocument();
    expect(screen.getByText('CSV')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('JSON')).toBeInTheDocument();
  });

  it('selects export format', () => {
    render(<PatientExport token={mockToken} onClose={mockOnClose} />);

    const pdfRadio = screen.getByLabelText(/PDF/i);
    fireEvent.click(pdfRadio);

    expect(pdfRadio).toBeChecked();
  });

  it('applies filters', () => {
    render(<PatientExport token={mockToken} onClose={mockOnClose} />);

    const searchInput = screen.getByPlaceholderText('Search patients...');
    fireEvent.change(searchInput, { target: { value: 'John' } });

    expect(searchInput).toHaveValue('John');
  });

  it('exports data successfully', async () => {
    const mockBlob = new Blob(['test data'], { type: 'text/csv' });
    mockedAxios.get.mockResolvedValue({ data: mockBlob });

    // Mock URL.createObjectURL
    global.URL.createObjectURL = jest.fn(() => 'blob:test');
    global.URL.revokeObjectURL = jest.fn();

    render(<PatientExport token={mockToken} onClose={mockOnClose} />);

    const exportButton = screen.getByText(/Export CSV/i);
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/v1/patients/export/csv',
        expect.objectContaining({
          headers: { Authorization: `Bearer ${mockToken}` },
          responseType: 'blob',
        })
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/Export completed successfully/i)).toBeInTheDocument();
    });
  });

  it('handles export error', async () => {
    mockedAxios.get.mockRejectedValue({
      response: { data: { detail: 'Export failed' } },
    });

    render(<PatientExport token={mockToken} onClose={mockOnClose} />);

    const exportButton = screen.getByText(/Export CSV/i);
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(screen.getByText('Export failed')).toBeInTheDocument();
    });
  });
});
