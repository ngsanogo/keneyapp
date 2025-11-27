import { useEffect, useState } from 'react';
import AddPatientForm from '../components/AddPatientForm';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import axios from 'axios';

interface Patient {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  gender: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const PatientsPage = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const { isAuthenticated, token } = useAuth();
  const navigate = useNavigate();

  const [showAdd, setShowAdd] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    const fetchPatients = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/patients/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setPatients(response.data);
      } catch (error) {
        console.error('Failed to fetch patients:', error);
      }
    };

    fetchPatients();
  }, [isAuthenticated, token, navigate]);

  return (
    <div>
      <Header />
      <main id="main-content" className="container">
        <div className="page-heading">
          <div>
            <p className="page-subtitle">Patient registry</p>
            <h1>Patients</h1>
          </div>
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
            Add patient
          </button>
        </div>

        <p className="surface-muted" style={{ marginBottom: '1rem' }}>
          Keep demographic and contact information current to speed up scheduling, billing, and on-call coordination.
        </p>

        <div className="card" aria-live="polite">
          <h2>Patient List</h2>
          {patients.length === 0 ? (
            <p>No patients found.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Name</th>
                  <th scope="col">Email</th>
                  <th scope="col">Phone</th>
                  <th scope="col">Gender</th>
                </tr>
              </thead>
              <tbody>
                {patients.map(patient => (
                  <tr key={patient.id}>
                    <td>{patient.id}</td>
                    <td>
                      {patient.first_name} {patient.last_name}
                    </td>
                    <td>{patient.email || 'N/A'}</td>
                    <td>{patient.phone}</td>
                    <td>{patient.gender}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        {showAdd && (
          <AddPatientForm
            token={token!}
            onAdd={patient => setPatients([patient, ...patients])}
            onClose={() => setShowAdd(false)}
          />
        )}
      </main>
    </div>
  );
};

export default PatientsPage;
