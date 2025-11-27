import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import LoadingSpinner from '../components/LoadingSpinner';

interface DashboardStats {
  total_patients: number;
  total_appointments: number;
  total_prescriptions: number;
  today_appointments: number;
  appointments_by_status: {
    scheduled: number;
    completed: number;
    cancelled: number;
  };
  recent_activity: {
    patients: number;
    appointments: number;
    prescriptions: number;
  };
  activity_window_days?: number;
  generated_at?: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const DashboardPage = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const { isAuthenticated, token, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    const fetchStats = async () => {
      setIsLoading(true);
      try {
        const response = await axios.get(`${API_URL}/api/v1/dashboard/stats`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [isAuthenticated, token, navigate]);

  const handleRefresh = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_URL}/api/v1/dashboard/stats`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setStats(response.data);
    } catch (error) {
      console.error('Failed to refresh stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const appointmentTotals = stats
    ? stats.appointments_by_status.scheduled +
      stats.appointments_by_status.completed +
      stats.appointments_by_status.cancelled
    : 0;

  const formatPercent = (value: number, total: number) => {
    if (total === 0) return 0;
    return Math.round((value / total) * 100);
  };

  return (
    <div>
      <Header />
      <main id="main-content" className="container" aria-live="polite">
        <div className="page-heading">
          <div>
            <p className="page-subtitle">Welcome back{user ? `, ${user.fullName}` : ''}</p>
            <h1>Care Operations Overview</h1>
          </div>
          <div className="pill" aria-label="Environment status: Healthy">
            <span className="spark-dot" aria-hidden /> Live environment
          </div>
        </div>

        {!stats ? (
          <div className="panel" role="status">
            <LoadingSpinner message="Preparing your dashboard" />
          </div>
        ) : (
          <>
            <section className="page-actions" aria-label="Dashboard controls">
              <div className="pill" aria-label={`Data last updated ${stats.generated_at ? new Date(stats.generated_at).toLocaleString() : 'recently'}`}>
                <span className="spark-dot" aria-hidden />
                Last updated {stats.generated_at ? new Date(stats.generated_at).toLocaleString() : 'just now'}
              </div>
              <button className="btn btn-secondary" onClick={handleRefresh} disabled={isLoading}>
                Refresh data
              </button>
            </section>

            <section aria-label="Key performance indicators" className="grid-responsive" style={{ marginBottom: '1.25rem' }}>
              <article className="stat-card">
                <header>
                  <h3>Total Patients</h3>
                  <span className="spark-dot" aria-hidden />
                </header>
                <strong>{stats.total_patients}</strong>
                <small>Registered profiles across all locations</small>
              </article>

              <article className="stat-card">
                <header>
                  <h3>Total Appointments</h3>
                  <span className="spark-dot" aria-hidden />
                </header>
                <strong>{stats.total_appointments}</strong>
                <small>Completed and upcoming visits</small>
              </article>

              <article className="stat-card">
                <header>
                  <h3>Today's Appointments</h3>
                  <span className="spark-dot" aria-hidden />
                </header>
                <strong>{stats.today_appointments}</strong>
                <small>Patients expected today</small>
              </article>

              <article className="stat-card">
                <header>
                  <h3>Total Prescriptions</h3>
                  <span className="spark-dot" aria-hidden />
                </header>
                <strong>{stats.total_prescriptions}</strong>
                <small>Active medication records</small>
              </article>
            </section>

            <section className="grid-responsive" aria-label="Operational insights">
              <article className="panel" aria-label="Appointment status distribution">
                <div className="panel-header">
                  <h3>Appointment status</h3>
                  <span className="pill">Today & upcoming</span>
                </div>
                <div className="metric-list" role="list">
                  {(
                    [
                      { label: 'Scheduled', value: stats.appointments_by_status.scheduled, tone: 'info' },
                      { label: 'Completed', value: stats.appointments_by_status.completed, tone: 'success' },
                      { label: 'Cancelled', value: stats.appointments_by_status.cancelled, tone: 'warning' },
                    ] as const
                  ).map((item) => (
                    <div key={item.label} className="metric-row" role="listitem">
                      <div>
                        <p className="metric-label">{item.label}</p>
                        <p className="metric-value">{item.value} cases</p>
                      </div>
                      <div className={`progress ${item.tone}`} aria-label={`${item.label} share`}>
                        <div
                          className="progress-track"
                          role="presentation"
                        >
                          <div
                            className="progress-fill"
                            style={{ width: `${formatPercent(item.value, appointmentTotals)}%` }}
                            aria-hidden
                          />
                        </div>
                        <span className="progress-caption">{formatPercent(item.value, appointmentTotals)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </article>

              <article className="panel" aria-label="Recent activity summary">
                <div className="panel-header">
                  <h3>Recent activity</h3>
                  <span className="pill">
                    Last {stats.activity_window_days ?? 7} days
                  </span>
                </div>
                <div className="metric-grid">
                  <div className="mini-card">
                    <p className="metric-label">New patients</p>
                    <p className="metric-value">{stats.recent_activity.patients}</p>
                    <p className="metric-caption">Registered in the last {stats.activity_window_days ?? 7} days</p>
                  </div>
                  <div className="mini-card">
                    <p className="metric-label">Appointments booked</p>
                    <p className="metric-value">{stats.recent_activity.appointments}</p>
                    <p className="metric-caption">Created during the same window</p>
                  </div>
                  <div className="mini-card">
                    <p className="metric-label">Prescriptions issued</p>
                    <p className="metric-value">{stats.recent_activity.prescriptions}</p>
                    <p className="metric-caption">Medication orders created recently</p>
                  </div>
                </div>
              </article>
            </section>

            <section className="grid-responsive" aria-label="Workspace guidance">
              <article className="panel">
                <div className="panel-header">
                  <h3>Quick actions</h3>
                  <span className="pill">Faster workflows</span>
                </div>
                <div className="quick-actions" role="list">
                  <button className="btn btn-primary" role="listitem" onClick={() => navigate('/patients')}>
                    Register new patient
                  </button>
                  <button className="btn btn-secondary" role="listitem" onClick={() => navigate('/appointments')}>
                    Schedule appointment
                  </button>
                  <button className="btn btn-secondary" role="listitem" onClick={() => navigate('/prescriptions')}>
                    Review prescriptions
                  </button>
                </div>
              </article>

              <article className="panel">
                <div className="panel-header">
                  <h3>System health</h3>
                  <span className="pill success">Operational</span>
                </div>
                <p className="surface-muted">
                  Access controls, audit logging, and secure sessions are enforced. Data transfers use TLS and all API
                  calls are authenticated. Reach out to operations if you notice anomalies while working with patient
                  records.
                </p>
              </article>
            </section>
          </>
        )}
      </main>
    </div>
  );
};

export default DashboardPage;
