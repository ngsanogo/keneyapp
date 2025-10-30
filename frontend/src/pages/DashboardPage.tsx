import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import axios from 'axios';

interface DashboardStats {
  total_patients: number;
  total_appointments: number;
  total_prescriptions: number;
  today_appointments: number;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const { isAuthenticated, token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/dashboard/stats`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };

    fetchStats();
  }, [isAuthenticated, token, navigate]);

  if (!stats) {
    return (
      <div>
        <Header />
        <div className="container">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Header />
      <div className="container">
        <h1>Dashboard</h1>

        <div className="dashboard-grid">
          <div className="stat-card">
            <h3>{stats.total_patients}</h3>
            <p>Total Patients</p>
          </div>

          <div className="stat-card">
            <h3>{stats.total_appointments}</h3>
            <p>Total Appointments</p>
          </div>

          <div className="stat-card">
            <h3>{stats.today_appointments}</h3>
            <p>Today's Appointments</p>
          </div>

          <div className="stat-card">
            <h3>{stats.total_prescriptions}</h3>
            <p>Total Prescriptions</p>
          </div>
        </div>

        <div className="card">
          <h2>Welcome to KeneyApp</h2>
          <p>Healthcare Data Management Platform</p>
          <p>Use the navigation menu to manage patients, appointments, and prescriptions.</p>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
