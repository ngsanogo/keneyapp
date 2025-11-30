import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import apiClient from '../lib/api';

vi.mock('axios');

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Authentication', () => {
    it('should login and store token', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token',
          token_type: 'bearer'
        }
      };

      vi.mocked(axios.post).mockResolvedValue(mockResponse);

      const result = await apiClient.login('testuser', 'password');

      expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/login', {
        username: 'testuser',
        password: 'password'
      });
      expect(result).toEqual(mockResponse.data);
      expect(localStorage.getItem('token')).toBe('test-token');
    });

    it('should logout and clear token', () => {
      localStorage.setItem('token', 'test-token');
      
      apiClient.logout();
      
      expect(localStorage.getItem('token')).toBeNull();
    });

    it('should get current user with auth header', async () => {
      const mockUser = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        role: 'doctor'
      };

      localStorage.setItem('token', 'test-token');
      vi.mocked(axios.get).mockResolvedValue({ data: mockUser });

      const result = await apiClient.getCurrentUser();

      expect(axios.get).toHaveBeenCalledWith('/api/v1/users/me', {
        headers: { Authorization: 'Bearer test-token' }
      });
      expect(result).toEqual(mockUser);
    });
  });

  describe('Patient Operations', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'test-token');
    });

    it('should get patients list', async () => {
      const mockPatients = [
        { id: '1', first_name: 'John', last_name: 'Doe' },
        { id: '2', first_name: 'Jane', last_name: 'Smith' }
      ];

      vi.mocked(axios.get).mockResolvedValue({ data: mockPatients });

      const result = await apiClient.getPatients();

      expect(axios.get).toHaveBeenCalledWith('/api/v1/patients?skip=0&limit=100', {
        headers: { Authorization: 'Bearer test-token' }
      });
      expect(result).toEqual(mockPatients);
    });

    it('should get single patient', async () => {
      const mockPatient = { id: '1', first_name: 'John', last_name: 'Doe' };

      vi.mocked(axios.get).mockResolvedValue({ data: mockPatient });

      const result = await apiClient.getPatient('1');

      expect(axios.get).toHaveBeenCalledWith('/api/v1/patients/1', {
        headers: { Authorization: 'Bearer test-token' }
      });
      expect(result).toEqual(mockPatient);
    });

    it('should create patient', async () => {
      const newPatient = {
        first_name: 'John',
        last_name: 'Doe',
        date_of_birth: '1990-01-01',
        gender: 'male'
      };

      const mockResponse = { ...newPatient, id: '1' };
      vi.mocked(axios.post).mockResolvedValue({ data: mockResponse });

      const result = await apiClient.createPatient(newPatient);

      expect(axios.post).toHaveBeenCalledWith('/api/v1/patients', newPatient, {
        headers: { Authorization: 'Bearer test-token' }
      });
      expect(result).toEqual(mockResponse);
    });

    it('should update patient', async () => {
      const updates = { phone: '+1234567890' };
      const mockResponse = { id: '1', ...updates };

      vi.mocked(axios.put).mockResolvedValue({ data: mockResponse });

      const result = await apiClient.updatePatient('1', updates);

      expect(axios.put).toHaveBeenCalledWith('/api/v1/patients/1', updates, {
        headers: { Authorization: 'Bearer test-token' }
      });
      expect(result).toEqual(mockResponse);
    });

    it('should delete patient', async () => {
      vi.mocked(axios.delete).mockResolvedValue({ data: { success: true } });

      await apiClient.deletePatient('1');

      expect(axios.delete).toHaveBeenCalledWith('/api/v1/patients/1', {
        headers: { Authorization: 'Bearer test-token' }
      });
    });

    it('should search patients', async () => {
      const mockResults = [
        { id: '1', first_name: 'John', last_name: 'Doe' }
      ];

      vi.mocked(axios.get).mockResolvedValue({ data: mockResults });

      const result = await apiClient.searchPatients('John');

      expect(axios.get).toHaveBeenCalledWith('/api/v1/patients?skip=0&limit=100&search=John', {
        headers: { Authorization: 'Bearer test-token' }
      });
      expect(result).toEqual(mockResults);
    });
  });

  describe('Dashboard Operations', () => {
    beforeEach(() => {
      localStorage.setItem('token', 'test-token');
    });

    it('should get dashboard stats', async () => {
      const mockStats = {
        total_patients: 150,
        total_appointments: 45,
        total_revenue: 12500
      };

      vi.mocked(axios.get).mockResolvedValue({ data: mockStats });

      const result = await apiClient.getDashboardStats();

      expect(axios.get).toHaveBeenCalledWith('/api/v1/dashboard/stats', {
        headers: { Authorization: 'Bearer test-token' }
      });
      expect(result).toEqual(mockStats);
    });
  });

  describe('Error Handling', () => {
    it('should handle 401 errors', async () => {
      const error = {
        response: {
          status: 401,
          data: { detail: 'Unauthorized' }
        }
      };

      vi.mocked(axios.get).mockRejectedValue(error);
      localStorage.setItem('token', 'test-token');

      await expect(apiClient.getPatients()).rejects.toEqual(error);
    });

    it('should handle network errors', async () => {
      const error = new Error('Network Error');
      vi.mocked(axios.get).mockRejectedValue(error);

      await expect(apiClient.getPatients()).rejects.toThrow('Network Error');
    });
  });
});
