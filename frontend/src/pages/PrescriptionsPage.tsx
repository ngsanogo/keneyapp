import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import axios from 'axios';

interface Prescription {
  id: number;
  patient_id: number;
  doctor_id: number;
  medication_name: string;
  dosage: string;
  frequency: string;
  prescribed_date: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const PrescriptionsPage = () => {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const { isAuthenticated, token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    const fetchPrescriptions = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/prescriptions/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setPrescriptions(response.data);
      } catch (error) {
        console.error('Failed to fetch prescriptions:', error);
      }
    };

    fetchPrescriptions();
  }, [isAuthenticated, token, navigate]);

  return (
    <div>
      <Header />
      <div className="container">
        <h1>Prescriptions</h1>

        <div className="card">
          <h2>Prescription List</h2>

          {prescriptions.length === 0 ? (
            <p>No prescriptions found.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Medication</th>
                  <th>Dosage</th>
                  <th>Frequency</th>
                  <th>Patient ID</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {prescriptions.map(prescription => (
                  <tr key={prescription.id}>
                    <td>{prescription.id}</td>
                    <td>{prescription.medication_name}</td>
                    <td>{prescription.dosage}</td>
                    <td>{prescription.frequency}</td>
                    <td>{prescription.patient_id}</td>
                    <td>{new Date(prescription.prescribed_date).toLocaleDateString()}</td>
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

export default PrescriptionsPage;
