import { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const StatusPage = () => {
  const { token, isAuthenticated } = useAuth();
  const [data, setData] = useState<{ version: string; environment: string; uptime_seconds: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchStatus = async () => {
      if (!isAuthenticated || !token) {
        setError('You must be logged in to view status.');
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(`${API_URL}/api/v1/status`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setData(res.data);
      } catch (e: any) {
        setError(e?.response?.data?.detail || 'Failed to load status');
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
  }, [isAuthenticated, token]);

  return (
    <main id="main-content" className="page">
      <h1>System Status</h1>
      {loading && <p>Loading…</p>}
      {error && <p role="alert" style={{ color: 'red' }}>{error}</p>}
      {data && (
        <div className="card" aria-live="polite">
          <p><strong>Version:</strong> {data.version}</p>
          <p><strong>Environment:</strong> {data.environment}</p>
          <p><strong>Uptime (s):</strong> {data.uptime_seconds}</p>
        </div>
      )}
    </main>
  );
};

export default StatusPage;
