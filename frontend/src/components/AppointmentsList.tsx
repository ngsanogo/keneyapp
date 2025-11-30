import React, { useEffect, useState } from 'react';

type Appointment = {
  id: number;
  patient_id: number;
  doctor_id: number;
  appointment_date: string;
  duration_minutes: number;
  status?: string;
  reason: string;
  notes?: string;
};

export const AppointmentsList: React.FC = () => {
  const [items, setItems] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const res = await fetch('/api/v1/appointments/');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setItems(data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div>Loading appointments…</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Appointments</h2>
      {items.length === 0 ? (
        <div>No appointments found.</div>
      ) : (
        <ul>
          {items.map((a) => (
            <li key={a.id}>
              <strong>#{a.id}</strong> — Patient {a.patient_id} with Doctor {a.doctor_id} on{' '}
              {new Date(a.appointment_date).toLocaleString()} ({a.duration_minutes} min)
              {a.status ? ` — ${a.status}` : ''}
              {a.reason ? ` — ${a.reason}` : ''}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
