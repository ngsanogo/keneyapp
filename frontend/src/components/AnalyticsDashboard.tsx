/**
 * Analytics Dashboard Component
 * Displays key metrics and charts for healthcare data
 */

import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import './AnalyticsDashboard.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface MetricCard {
  title: string;
  value: number | string;
  change?: number;
  icon: string;
  color: string;
}

interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string;
    borderWidth?: number;
    tension?: number;
  }>;
}

const AnalyticsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricCard[]>([
    { title: 'Total Patients', value: 0, change: 0, icon: '👥', color: '#007bff' },
    { title: 'Appointments Today', value: 0, change: 0, icon: '📅', color: '#28a745' },
    { title: 'Active Doctors', value: 0, change: 0, icon: '⚕️', color: '#17a2b8' },
    { title: 'Revenue (Month)', value: '$0', change: 0, icon: '💰', color: '#ffc107' },
  ]);

  const [patientTrend, setPatientTrend] = useState<ChartData>({
    labels: [],
    datasets: [],
  });

  const [appointmentStats, setAppointmentStats] = useState<ChartData>({
    labels: [],
    datasets: [],
  });

  const [genderDistribution, setGenderDistribution] = useState<ChartData>({
    labels: [],
    datasets: [],
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch metrics
      const metricsResponse = await fetch('/api/v1/analytics/metrics', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (metricsResponse.ok) {
        const data = await metricsResponse.json();
        updateMetrics(data);
      }

      // Fetch patient trend data
      const trendResponse = await fetch('/api/v1/analytics/patient-trend?period=30d', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (trendResponse.ok) {
        const data = await trendResponse.json();
        setPatientTrend({
          labels: data.labels,
          datasets: [
            {
              label: 'New Patients',
              data: data.values,
              borderColor: '#007bff',
              backgroundColor: 'rgba(0, 123, 255, 0.1)',
              tension: 0.4,
              borderWidth: 2,
            },
          ],
        });
      }

      // Fetch appointment statistics
      const appointmentResponse = await fetch('/api/v1/analytics/appointments?period=7d', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (appointmentResponse.ok) {
        const data = await appointmentResponse.json();
        setAppointmentStats({
          labels: data.labels,
          datasets: [
            {
              label: 'Completed',
              data: data.completed,
              backgroundColor: '#28a745',
            },
            {
              label: 'Pending',
              data: data.pending,
              backgroundColor: '#ffc107',
            },
            {
              label: 'Cancelled',
              data: data.cancelled,
              backgroundColor: '#dc3545',
            },
          ],
        });
      }

      // Fetch gender distribution
      const genderResponse = await fetch('/api/v1/analytics/gender-distribution', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (genderResponse.ok) {
        const data = await genderResponse.json();
        setGenderDistribution({
          labels: data.labels,
          datasets: [
            {
              data: data.values,
              backgroundColor: ['#007bff', '#e83e8c', '#6f42c1'],
              borderWidth: 0,
            },
          ],
        });
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateMetrics = (data: any) => {
    setMetrics([
      {
        title: 'Total Patients',
        value: data.total_patients || 0,
        change: data.patients_change || 0,
        icon: '👥',
        color: '#007bff',
      },
      {
        title: 'Appointments Today',
        value: data.appointments_today || 0,
        change: data.appointments_change || 0,
        icon: '📅',
        color: '#28a745',
      },
      {
        title: 'Active Doctors',
        value: data.active_doctors || 0,
        change: data.doctors_change || 0,
        icon: '⚕️',
        color: '#17a2b8',
      },
      {
        title: 'Revenue (Month)',
        value: `$${(data.monthly_revenue || 0).toLocaleString()}`,
        change: data.revenue_change || 0,
        icon: '💰',
        color: '#ffc107',
      },
    ]);
  };

  const lineOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Patient Registration Trend (Last 30 Days)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  };

  const barOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Appointment Statistics (Last 7 Days)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  };

  const pieOptions: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
      },
      title: {
        display: true,
        text: 'Patient Gender Distribution',
      },
    },
  };

  if (loading) {
    return (
      <div className="analytics-dashboard loading">
        <div className="spinner"></div>
        <p>Loading analytics...</p>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h1>Analytics Dashboard</h1>
        <button className="refresh-btn" onClick={fetchDashboardData}>
          🔄 Refresh
        </button>
      </div>

      <div className="metrics-grid">
        {metrics.map((metric, index) => (
          <div
            key={index}
            className="metric-card"
            style={{ borderTopColor: metric.color }}
          >
            <div className="metric-icon" style={{ color: metric.color }}>
              {metric.icon}
            </div>
            <div className="metric-content">
              <h3>{metric.title}</h3>
              <div className="metric-value">{metric.value}</div>
              {metric.change !== undefined && (
                <div className={`metric-change ${metric.change >= 0 ? 'positive' : 'negative'}`}>
                  {metric.change >= 0 ? '↑' : '↓'} {Math.abs(metric.change)}%
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="charts-grid">
        <div className="chart-container">
          <div className="chart-wrapper">
            <Line data={patientTrend} options={lineOptions} />
          </div>
        </div>

        <div className="chart-container">
          <div className="chart-wrapper">
            <Bar data={appointmentStats} options={barOptions} />
          </div>
        </div>

        <div className="chart-container small">
          <div className="chart-wrapper">
            <Pie data={genderDistribution} options={pieOptions} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
