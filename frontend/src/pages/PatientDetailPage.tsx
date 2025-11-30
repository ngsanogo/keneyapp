import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import apiClient from '../lib/api';
import { ArrowLeft, Calendar, Mail, Phone, MapPin } from 'lucide-react';

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: patient, isLoading, error } = useQuery(
    ['patient', id],
    () => apiClient.getPatient(id!),
    { enabled: !!id }
  );

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <div className="loading" style={{ width: '3rem', height: '3rem' }} />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="card">
        <p style={{ color: '#dc2626' }}>Failed to load patient details</p>
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={() => navigate('/patients')}
        style={{ display: 'flex', alignItems: 'center', marginBottom: '1.5rem', background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer' }}
      >
        <ArrowLeft size={20} style={{ marginRight: '0.5rem' }} />
        Back to Patients
      </button>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          {patient.first_name} {patient.last_name}
        </h1>
        <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
          Patient ID: {patient.id}
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
              <Calendar size={18} style={{ color: '#6b7280', marginRight: '0.5rem' }} />
              <span style={{ fontWeight: 500 }}>Date of Birth</span>
            </div>
            <p style={{ color: '#374151', marginLeft: '1.75rem' }}>{patient.date_of_birth}</p>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 500 }}>Gender</span>
            </div>
            <p style={{ color: '#374151', textTransform: 'capitalize' }}>{patient.gender}</p>
          </div>

          {patient.phone && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                <Phone size={18} style={{ color: '#6b7280', marginRight: '0.5rem' }} />
                <span style={{ fontWeight: 500 }}>Phone</span>
              </div>
              <p style={{ color: '#374151', marginLeft: '1.75rem' }}>{patient.phone}</p>
            </div>
          )}

          {patient.email && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                <Mail size={18} style={{ color: '#6b7280', marginRight: '0.5rem' }} />
                <span style={{ fontWeight: 500 }}>Email</span>
              </div>
              <p style={{ color: '#374151', marginLeft: '1.75rem' }}>{patient.email}</p>
            </div>
          )}

          {patient.address && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
                <MapPin size={18} style={{ color: '#6b7280', marginRight: '0.5rem' }} />
                <span style={{ fontWeight: 500 }}>Address</span>
              </div>
              <p style={{ color: '#374151', marginLeft: '1.75rem' }}>{patient.address}</p>
            </div>
          )}
        </div>
      </div>

      {patient.medical_history && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            Medical History
          </h2>
          <p style={{ color: '#374151', whiteSpace: 'pre-wrap' }}>{patient.medical_history}</p>
        </div>
      )}

      {patient.allergies && (
        <div className="card">
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            Allergies
          </h2>
          <p style={{ color: '#dc2626', fontWeight: 500 }}>{patient.allergies}</p>
        </div>
      )}
    </div>
  );
}
