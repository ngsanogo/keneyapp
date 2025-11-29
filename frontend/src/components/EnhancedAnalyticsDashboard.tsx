import { useState, useEffect } from 'react';
import axios from 'axios';
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
  Filler,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import './EnhancedAnalyticsDashboard.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DashboardMetrics {
  total_patients: number;
  total_appointments: number;
  pending_appointments: number;
  completed_appointments: number;
  cancelled_appointments: number;
  revenue_current_month: number;
  revenue_previous_month: number;
  average_wait_time: number;
  patient_satisfaction_score: number;
}

interface AppointmentTrend {
  date: string;
  scheduled: number;
  completed: number;
  cancelled: number;
}

interface RevenueData {
  month: string;
  revenue: number;
  expenses: number;
  profit: number;
}

interface DepartmentStats {
  department: string;
  patients: number;
  appointments: number;
  revenue: number;
}

interface EnhancedAnalyticsDashboardProps {
  token: string;
  tenantId: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const EnhancedAnalyticsDashboard = ({ token, tenantId }: EnhancedAnalyticsDashboardProps) => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [appointmentTrends, setAppointmentTrends] = useState<AppointmentTrend[]>([]);
  const [revenueData, setRevenueData] = useState<RevenueData[]>([]);
  const [departmentStats, setDepartmentStats] = useState<DepartmentStats[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval] = useState<number>(300000); // 5 minutes
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [timeRange, setTimeRange] = useState<'7days' | '30days' | '90days'>('30days');

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [metricsRes, trendsRes, revenueRes, deptRes] = await Promise.all([
        axios.get(`${API_URL}/api/v1/analytics/metrics`, {
          headers: { Authorization: `Bearer ${token}` },
          params: { time_range: timeRange },
        }),
        axios.get(`${API_URL}/api/v1/analytics/appointment-trends`, {
          headers: { Authorization: `Bearer ${token}` },
          params: { days: timeRange === '7days' ? 7 : timeRange === '30days' ? 30 : 90 },
        }),
        axios.get(`${API_URL}/api/v1/analytics/revenue`, {
          headers: { Authorization: `Bearer ${token}` },
          params: { months: 6 },
        }),
        axios.get(`${API_URL}/api/v1/analytics/departments`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setMetrics(metricsRes.data);
      setAppointmentTrends(trendsRes.data);
      setRevenueData(revenueRes.data);
      setDepartmentStats(deptRes.data);
      setLastUpdated(new Date());
    } catch (err: any) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err.response?.data?.detail || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    const interval = setInterval(fetchDashboardData, refreshInterval);
    return () => clearInterval(interval);
  }, [token, tenantId, timeRange, refreshInterval]);

  const appointmentTrendChartData = {
    labels: appointmentTrends.map((t) => new Date(t.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
    datasets: [
      {
        label: 'Scheduled',
        data: appointmentTrends.map((t) => t.scheduled),
        borderColor: '#4a90e2',
        backgroundColor: 'rgba(74, 144, 226, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Completed',
        data: appointmentTrends.map((t) => t.completed),
        borderColor: '#52c41a',
        backgroundColor: 'rgba(82, 196, 26, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Cancelled',
        data: appointmentTrends.map((t) => t.cancelled),
        borderColor: '#ff4d4f',
        backgroundColor: 'rgba(255, 77, 79, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const revenueChartData = {
    labels: revenueData.map((r) => r.month),
    datasets: [
      {
        label: 'Revenue',
        data: revenueData.map((r) => r.revenue),
        backgroundColor: '#52c41a',
      },
      {
        label: 'Expenses',
        data: revenueData.map((r) => r.expenses),
        backgroundColor: '#ff4d4f',
      },
      {
        label: 'Profit',
        data: revenueData.map((r) => r.profit),
        backgroundColor: '#4a90e2',
      },
    ],
  };

  const departmentChartData = {
    labels: departmentStats.map((d) => d.department),
    datasets: [
      {
        label: 'Patients',
        data: departmentStats.map((d) => d.patients),
        backgroundColor: [
          '#4a90e2',
          '#52c41a',
          '#faad14',
          '#f759ab',
          '#13c2c2',
          '#722ed1',
        ],
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

  if (loading && !metrics) {
    return (
      <div className="enhanced-analytics-dashboard">
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="enhanced-analytics-dashboard">
        <div className="error-state">
          <span className="error-icon">⚠️</span>
          <h3>Failed to Load Analytics</h3>
          <p>{error}</p>
          <button onClick={fetchDashboardData} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const revenueGrowth = metrics
    ? ((metrics.revenue_current_month - metrics.revenue_previous_month) / metrics.revenue_previous_month) * 100
    : 0;

  return (
    <div className="enhanced-analytics-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Analytics Dashboard</h1>
          <p className="last-updated">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>

        <div className="header-controls">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="time-range-selector"
          >
            <option value="7days">Last 7 Days</option>
            <option value="30days">Last 30 Days</option>
            <option value="90days">Last 90 Days</option>
          </select>

          <button onClick={fetchDashboardData} className="refresh-btn" disabled={loading}>
            {loading ? '⟳' : '🔄'} Refresh
          </button>
        </div>
      </header>

      {metrics && (
        <section className="metrics-grid">
          <div className="metric-card primary">
            <div className="metric-icon">👥</div>
            <div className="metric-content">
              <h3>Total Patients</h3>
              <p className="metric-value">{metrics.total_patients.toLocaleString()}</p>
            </div>
          </div>

          <div className="metric-card success">
            <div className="metric-icon">✅</div>
            <div className="metric-content">
              <h3>Completed Appointments</h3>
              <p className="metric-value">{metrics.completed_appointments.toLocaleString()}</p>
            </div>
          </div>

          <div className="metric-card warning">
            <div className="metric-icon">⏳</div>
            <div className="metric-content">
              <h3>Pending Appointments</h3>
              <p className="metric-value">{metrics.pending_appointments.toLocaleString()}</p>
            </div>
          </div>

          <div className="metric-card danger">
            <div className="metric-icon">❌</div>
            <div className="metric-content">
              <h3>Cancelled Appointments</h3>
              <p className="metric-value">{metrics.cancelled_appointments.toLocaleString()}</p>
            </div>
          </div>

          <div className="metric-card revenue">
            <div className="metric-icon">💰</div>
            <div className="metric-content">
              <h3>Monthly Revenue</h3>
              <p className="metric-value">${metrics.revenue_current_month.toLocaleString()}</p>
              <span className={`growth-badge ${revenueGrowth >= 0 ? 'positive' : 'negative'}`}>
                {revenueGrowth >= 0 ? '↑' : '↓'} {Math.abs(revenueGrowth).toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="metric-card info">
            <div className="metric-icon">⏱️</div>
            <div className="metric-content">
              <h3>Avg Wait Time</h3>
              <p className="metric-value">{metrics.average_wait_time} min</p>
            </div>
          </div>
        </section>
      )}

      <section className="charts-grid">
        <div className="chart-card large">
          <h2>Appointment Trends</h2>
          <div className="chart-container">
            <Line data={appointmentTrendChartData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h2>Revenue Overview</h2>
          <div className="chart-container">
            <Bar data={revenueChartData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h2>Department Distribution</h2>
          <div className="chart-container">
            <Doughnut data={departmentChartData} options={chartOptions} />
          </div>
        </div>
      </section>

      <section className="department-table">
        <h2>Department Performance</h2>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Department</th>
                <th>Patients</th>
                <th>Appointments</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {departmentStats.map((dept, index) => (
                <tr key={index}>
                  <td className="department-name">{dept.department}</td>
                  <td>{dept.patients.toLocaleString()}</td>
                  <td>{dept.appointments.toLocaleString()}</td>
                  <td className="revenue-cell">${dept.revenue.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

export default EnhancedAnalyticsDashboard;
