import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import axios from 'axios';

interface Appointment {
  id: number;
  patient_id: number;
  doctor_id: number;
  appointment_date: string;
  status: string;
  reason: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AppointmentsPage: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const { isAuthenticated, token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    const fetchAppointments = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/appointments/`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        setAppointments(response.data);
      } catch (error) {
        console.error('Failed to fetch appointments:', error);
      }
    };

    fetchAppointments();
  }, [isAuthenticated, token, navigate]);

  return (
    <div>
      <Header />
      <div className="container">
        <h1>Appointments</h1>
        
        <div className="card">
          <h2>Appointment List</h2>
          
          {appointments.length === 0 ? (
            <p>No appointments found.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Date & Time</th>
                  <th>Patient ID</th>
                  <th>Doctor ID</th>
                  <th>Reason</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((appointment) => (
                  <tr key={appointment.id}>
                    <td>{appointment.id}</td>
                    <td>{new Date(appointment.appointment_date).toLocaleString()}</td>
                    <td>{appointment.patient_id}</td>
                    <td>{appointment.doctor_id}</td>
                    <td>{appointment.reason}</td>
                    <td>
                      <span className={`status-${appointment.status}`}>
                        {appointment.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default AppointmentsPage;
