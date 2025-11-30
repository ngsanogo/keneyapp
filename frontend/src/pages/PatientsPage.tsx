import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import apiClient, { Patient } from '../lib/api';
import { Search, Plus, Edit, Trash2, Eye } from 'lucide-react';

function PatientModal({ 
  isOpen, 
  onClose, 
  patient 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  patient?: Patient;
}) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Partial<Patient>>({
    first_name: patient?.first_name || '',
    last_name: patient?.last_name || '',
    date_of_birth: patient?.date_of_birth || '',
    gender: patient?.gender || 'male',
    phone: patient?.phone || '',
    email: patient?.email || '',
    address: patient?.address || '',
  });

  const mutation = useMutation(
    (data: Partial<Patient>) =>
      patient?.id
        ? apiClient.updatePatient(patient.id, data)
        : apiClient.createPatient(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('patients');
        onClose();
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 50,
      padding: '1rem'
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '600px', maxHeight: '90vh', overflow: 'auto' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
          {patient ? 'Edit Patient' : 'New Patient'}
        </h2>

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label className="label">First Name *</label>
              <input
                className="input"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Last Name *</label>
              <input
                className="input"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                required
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label className="label">Date of Birth *</label>
              <input
                type="date"
                className="input"
                value={formData.date_of_birth}
                onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="label">Gender *</label>
              <select
                className="input"
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                required
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label className="label">Phone</label>
            <input
              type="tel"
              className="input"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label className="label">Email</label>
            <input
              type="email"
              className="input"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label className="label">Address</label>
            <textarea
              className="input"
              rows={3}
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={mutation.isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={mutation.isLoading}
            >
              {mutation.isLoading ? 'Saving...' : patient ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function PatientsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | undefined>();

  const { data: patients, isLoading } = useQuery(
    ['patients', search],
    () => apiClient.getPatients({ search, limit: 50 })
  );

  const deleteMutation = useMutation(
    (id: string) => apiClient.deletePatient(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('patients');
      },
    }
  );

  const handleEdit = (patient: Patient) => {
    setSelectedPatient(patient);
    setIsModalOpen(true);
  };

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete ${name}?`)) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedPatient(undefined);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 'bold' }}>Patients</h1>
        <button
          className="btn btn-primary"
          onClick={() => setIsModalOpen(true)}
        >
          <Plus size={20} style={{ marginRight: '0.5rem' }} />
          New Patient
        </button>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ position: 'relative' }}>
          <Search 
            size={20} 
            style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} 
          />
          <input
            className="input"
            style={{ paddingLeft: '2.5rem' }}
            placeholder="Search patients by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
          <div className="loading" style={{ width: '3rem', height: '3rem' }} />
        </div>
      ) : patients && patients.length > 0 ? (
        <div className="card" style={{ overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 600 }}>Name</th>
                <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 600 }}>DOB</th>
                <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 600 }}>Gender</th>
                <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 600 }}>Phone</th>
                <th style={{ padding: '0.75rem', textAlign: 'left', fontWeight: 600 }}>Email</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr key={patient.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: '0.75rem' }}>
                    {patient.first_name} {patient.last_name}
                  </td>
                  <td style={{ padding: '0.75rem' }}>{patient.date_of_birth}</td>
                  <td style={{ padding: '0.75rem', textTransform: 'capitalize' }}>{patient.gender}</td>
                  <td style={{ padding: '0.75rem' }}>{patient.phone || '-'}</td>
                  <td style={{ padding: '0.75rem' }}>{patient.email || '-'}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => navigate(`/patients/${patient.id}`)}
                        style={{ padding: '0.5rem', border: 'none', background: '#eff6ff', borderRadius: '0.375rem', cursor: 'pointer' }}
                        title="View"
                      >
                        <Eye size={16} style={{ color: '#2563eb' }} />
                      </button>
                      <button
                        onClick={() => handleEdit(patient)}
                        style={{ padding: '0.5rem', border: 'none', background: '#fef3c7', borderRadius: '0.375rem', cursor: 'pointer' }}
                        title="Edit"
                      >
                        <Edit size={16} style={{ color: '#f59e0b' }} />
                      </button>
                      <button
                        onClick={() => handleDelete(patient.id, `${patient.first_name} ${patient.last_name}`)}
                        style={{ padding: '0.5rem', border: 'none', background: '#fee2e2', borderRadius: '0.375rem', cursor: 'pointer' }}
                        title="Delete"
                      >
                        <Trash2 size={16} style={{ color: '#dc2626' }} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ color: '#6b7280' }}>No patients found</p>
        </div>
      )}

      <PatientModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        patient={selectedPatient}
      />
    </div>
  );
}
