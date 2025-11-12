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
      <div className="container">
        <h1>Patients</h1>
        <button
          className="btn btn-primary"
          style={{ marginBottom: '1rem' }}
          onClick={() => setShowAdd(true)}
        >
          Add Patient
        </button>
        <div className="card">
          <h2>Patient List</h2>
          {patients.length === 0 ? (
            <p>No patients found.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Gender</th>
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
      </div>
    </div>
  );
};

export default PatientsPage;
