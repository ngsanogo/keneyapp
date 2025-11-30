/**
 * Advanced Analytics Dashboard with Custom Date Ranges
 * Uses new v3.1 analytics endpoints
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import './AdvancedAnalytics.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

interface CustomPeriodMetrics {
  total_patients: number;
  new_patients: number;
  total_appointments: number;
  completed_appointments: number;
  cancelled_appointments: number;
  total_prescriptions: number;
  total_doctors: number;
  average_appointments_per_patient: number;
  completion_rate: number;
  cancellation_rate: number;
}

interface AgeRange {
  range: string;
  count: number;
}

interface DoctorPerformance {
  doctor_id: number;
  doctor_name: string;
  total_appointments: number;
  completed_appointments: number;
  completion_rate: number;
  average_rating: number;
}

const AdvancedAnalytics: React.FC<{ token: string }> = ({ token }) => {
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [metrics, setMetrics] = useState<CustomPeriodMetrics | null>(null);
  const [ageDistribution, setAgeDistribution] = useState<AgeRange[]>([]);
  const [doctorPerformance, setDoctorPerformance] = useState<DoctorPerformance[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'patients' | 'doctors'>('overview');

  // Set default date range (last 30 days)
  useEffect(() => {
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);

    setDateFrom(thirtyDaysAgo.toISOString().split('T')[0]);
    setDateTo(today.toISOString().split('T')[0]);
  }, []);

  const fetchAnalytics = async () => {
    if (!token) return;

    try {
      setLoading(true);
      setError(null);

      const params: any = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const [metricsRes, ageRes, doctorRes] = await Promise.all([
        axios.get('/api/v1/analytics/custom-period', {
          headers: { Authorization: `Bearer ${token}` },
          params,
        }),
        axios.get('/api/v1/analytics/age-distribution', {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get('/api/v1/analytics/doctor-performance', {
          headers: { Authorization: `Bearer ${token}` },
          params,
        }).catch(() => ({ data: [] })), // Admin only - may fail for non-admins
      ]);

      setMetrics(metricsRes.data);
      setAgeDistribution(ageRes.data.age_ranges || []);
      setDoctorPerformance(doctorRes.data || []);
    } catch (err: any) {
      console.error('Failed to fetch analytics:', err);
      setError(err.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (dateFrom || dateTo) {
      fetchAnalytics();
    }
  }, [dateFrom, dateTo]);

  const handleQuickRange = (days: number) => {
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - days);

    setDateFrom(startDate.toISOString().split('T')[0]);
    setDateTo(today.toISOString().split('T')[0]);
  };

  // Age Distribution Chart
  const ageDistributionData = {
    labels: ageDistribution.map((a) => a.range),
    datasets: [
      {
        label: 'Patients',
        data: ageDistribution.map((a) => a.count),
        backgroundColor: [
          '#4a90e2',
          '#52c41a',
          '#faad14',
          '#f759ab',
          '#13c2c2',
          '#722ed1',
          '#ff4d4f',
          '#fa8c16',
          '#eb2f96',
        ],
      },
    ],
  };

  // Doctor Performance Chart
  const doctorPerformanceData = {
    labels: doctorPerformance.slice(0, 10).map((d) => d.doctor_name),
    datasets: [
      {
        label: 'Total Appointments',
        data: doctorPerformance.slice(0, 10).map((d) => d.total_appointments),
        backgroundColor: '#4a90e2',
      },
      {
        label: 'Completed',
        data: doctorPerformance.slice(0, 10).map((d) => d.completed_appointments),
        backgroundColor: '#52c41a',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };

  return (
    <div className="advanced-analytics">
      <div className="analytics-header">
        <h1>Advanced Analytics</h1>
        <p className="subtitle">Custom date range analysis and insights</p>
      </div>

      {/* Date Range Selector */}
      <div className="date-range-selector">
        <div className="date-inputs">
          <div className="input-group">
            <label>From:</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              max={dateTo || undefined}
            />
          </div>
          <div className="input-group">
            <label>To:</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              min={dateFrom || undefined}
              max={new Date().toISOString().split('T')[0]}
            />
          </div>
        </div>

        <div className="quick-ranges">
          <button onClick={() => handleQuickRange(7)} className="btn-quick">
            Last 7 Days
          </button>
          <button onClick={() => handleQuickRange(30)} className="btn-quick">
            Last 30 Days
          </button>
          <button onClick={() => handleQuickRange(90)} className="btn-quick">
            Last 90 Days
          </button>
          <button onClick={fetchAnalytics} className="btn-primary" disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'patients' ? 'active' : ''}`}
          onClick={() => setActiveTab('patients')}
        >
          Patient Analytics
        </button>
        <button
          className={`tab ${activeTab === 'doctors' ? 'active' : ''}`}
          onClick={() => setActiveTab('doctors')}
        >
          Doctor Performance
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && metrics && (
        <div className="tab-content">
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-icon">👥</div>
              <div className="metric-info">
                <h3>Total Patients</h3>
                <p className="metric-value">{metrics.total_patients.toLocaleString()}</p>
                <span className="metric-badge new">+{metrics.new_patients} new</span>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">📅</div>
              <div className="metric-info">
                <h3>Appointments</h3>
                <p className="metric-value">{metrics.total_appointments.toLocaleString()}</p>
                <span className="metric-badge">{metrics.completed_appointments} completed</span>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">💊</div>
              <div className="metric-info">
                <h3>Prescriptions</h3>
                <p className="metric-value">{metrics.total_prescriptions.toLocaleString()}</p>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">👨‍⚕️</div>
              <div className="metric-info">
                <h3>Active Doctors</h3>
                <p className="metric-value">{metrics.total_doctors.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <h3>Completion Rate</h3>
              <div className="progress-circle">
                <span className="percentage">{metrics.completion_rate.toFixed(1)}%</span>
              </div>
              <p>Appointments completed successfully</p>
            </div>

            <div className="stat-card">
              <h3>Cancellation Rate</h3>
              <div className="progress-circle red">
                <span className="percentage">{metrics.cancellation_rate.toFixed(1)}%</span>
              </div>
              <p>Appointments cancelled</p>
            </div>

            <div className="stat-card">
              <h3>Avg Appointments/Patient</h3>
              <div className="progress-circle blue">
                <span className="percentage">{metrics.average_appointments_per_patient.toFixed(1)}</span>
              </div>
              <p>Average patient engagement</p>
            </div>
          </div>
        </div>
      )}

      {/* Patient Analytics Tab */}
      {activeTab === 'patients' && (
        <div className="tab-content">
          <div className="chart-section">
            <h2>Patient Age Distribution</h2>
            {ageDistribution.length > 0 ? (
              <div className="chart-container">
                <Doughnut data={ageDistributionData} options={chartOptions} />
              </div>
            ) : (
              <p className="no-data">No age distribution data available</p>
            )}
          </div>

          <div className="age-table">
            <h3>Age Range Breakdown</h3>
            <table>
              <thead>
                <tr>
                  <th>Age Range</th>
                  <th>Count</th>
                  <th>Percentage</th>
                </tr>
              </thead>
              <tbody>
                {ageDistribution.map((range, idx) => {
                  const total = ageDistribution.reduce((sum, r) => sum + r.count, 0);
                  const percentage = ((range.count / total) * 100).toFixed(1);
                  return (
                    <tr key={idx}>
                      <td>{range.range}</td>
                      <td>{range.count.toLocaleString()}</td>
                      <td>
                        <div className="percentage-bar">
                          <div className="bar" style={{ width: `${percentage}%` }}></div>
                          <span>{percentage}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Doctor Performance Tab */}
      {activeTab === 'doctors' && (
        <div className="tab-content">
          {doctorPerformance.length > 0 ? (
            <>
              <div className="chart-section">
                <h2>Top 10 Doctors by Appointments</h2>
                <div className="chart-container">
                  <Bar data={doctorPerformanceData} options={chartOptions} />
                </div>
              </div>

              <div className="doctor-table">
                <h3>Detailed Doctor Performance</h3>
                <table>
                  <thead>
                    <tr>
                      <th>Doctor</th>
                      <th>Total Appointments</th>
                      <th>Completed</th>
                      <th>Completion Rate</th>
                      <th>Avg Rating</th>
                    </tr>
                  </thead>
                  <tbody>
                    {doctorPerformance.map((doctor) => (
                      <tr key={doctor.doctor_id}>
                        <td className="doctor-name">{doctor.doctor_name}</td>
                        <td>{doctor.total_appointments.toLocaleString()}</td>
                        <td>{doctor.completed_appointments.toLocaleString()}</td>
                        <td>
                          <span className={`rate-badge ${doctor.completion_rate >= 80 ? 'high' : doctor.completion_rate >= 60 ? 'medium' : 'low'}`}>
                            {doctor.completion_rate.toFixed(1)}%
                          </span>
                        </td>
                        <td>
                          <span className="rating">
                            {'⭐'.repeat(Math.round(doctor.average_rating))} {doctor.average_rating.toFixed(1)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="no-data-state">
              <p>Doctor performance data requires admin access</p>
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Loading analytics...</p>
        </div>
      )}
    </div>
  );
};

export default AdvancedAnalytics;
