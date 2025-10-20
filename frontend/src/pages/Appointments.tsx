import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Chip,
} from '@mui/material';
import { Add, Edit, Delete } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import axios from 'axios';

interface Appointment {
  id: number;
  patient_id: number;
  doctor_id: number;
  appointment_date: string;
  duration_minutes: number;
  status: string;
  notes?: string;
  diagnosis?: string;
  treatment_plan?: string;
}

const Appointments: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  const [formData, setFormData] = useState({
    patient_id: '',
    doctor_id: '',
    appointment_date: '',
    duration_minutes: 30,
    notes: '',
    diagnosis: '',
    treatment_plan: '',
  });

  const queryClient = useQueryClient();

  const { data: appointments, isLoading } = useQuery('appointments', () =>
    axios.get('/api/appointments').then(res => res.data)
  );

  const { data: patients } = useQuery('patients', () =>
    axios.get('/api/patients').then(res => res.data)
  );

  const createMutation = useMutation(
    (data: any) => axios.post('/api/appointments', data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('appointments');
        setOpen(false);
        resetForm();
      },
    }
  );

  const updateMutation = useMutation(
    ({ id, data }: { id: number; data: any }) => axios.put(`/api/appointments/${id}`, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('appointments');
        setOpen(false);
        resetForm();
      },
    }
  );

  const deleteMutation = useMutation(
    (id: number) => axios.delete(`/api/appointments/${id}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('appointments');
      },
    }
  );

  const resetForm = () => {
    setFormData({
      patient_id: '',
      doctor_id: '',
      appointment_date: '',
      duration_minutes: 30,
      notes: '',
      diagnosis: '',
      treatment_plan: '',
    });
    setEditingAppointment(null);
  };

  const handleOpen = (appointment?: Appointment) => {
    if (appointment) {
      setEditingAppointment(appointment);
      setFormData({
        patient_id: appointment.patient_id.toString(),
        doctor_id: appointment.doctor_id.toString(),
        appointment_date: appointment.appointment_date,
        duration_minutes: appointment.duration_minutes,
        notes: appointment.notes || '',
        diagnosis: appointment.diagnosis || '',
        treatment_plan: appointment.treatment_plan || '',
      });
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    resetForm();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      patient_id: parseInt(formData.patient_id),
      doctor_id: parseInt(formData.doctor_id),
    };
    
    if (editingAppointment) {
      updateMutation.mutate({ id: editingAppointment.id, data: submitData });
    } else {
      createMutation.mutate(submitData);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'default';
      case 'confirmed': return 'info';
      case 'in_progress': return 'warning';
      case 'completed': return 'success';
      case 'cancelled': return 'error';
      case 'no_show': return 'error';
      default: return 'default';
    }
  };

  if (isLoading) return <Typography>Loading...</Typography>;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Appointments</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpen()}
        >
          Schedule Appointment
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Patient</TableCell>
              <TableCell>Date & Time</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Notes</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {appointments?.map((appointment: Appointment) => {
              const patient = patients?.find((p: any) => p.id === appointment.patient_id);
              return (
                <TableRow key={appointment.id}>
                  <TableCell>
                    {patient ? `${patient.first_name} ${patient.last_name}` : 'Unknown Patient'}
                  </TableCell>
                  <TableCell>
                    {new Date(appointment.appointment_date).toLocaleString()}
                  </TableCell>
                  <TableCell>{appointment.duration_minutes} min</TableCell>
                  <TableCell>
                    <Chip
                      label={appointment.status}
                      color={getStatusColor(appointment.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{appointment.notes || '-'}</TableCell>
                  <TableCell>
                    <IconButton onClick={() => handleOpen(appointment)}>
                      <Edit />
                    </IconButton>
                    <IconButton onClick={() => deleteMutation.mutate(appointment.id)}>
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingAppointment ? 'Edit Appointment' : 'Schedule New Appointment'}
        </DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Patient"
                  select
                  value={formData.patient_id}
                  onChange={(e) => setFormData({ ...formData, patient_id: e.target.value })}
                  required
                >
                  {patients?.map((patient: any) => (
                    <option key={patient.id} value={patient.id}>
                      {patient.first_name} {patient.last_name}
                    </option>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Doctor ID"
                  type="number"
                  value={formData.doctor_id}
                  onChange={(e) => setFormData({ ...formData, doctor_id: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Date & Time"
                  type="datetime-local"
                  value={formData.appointment_date}
                  onChange={(e) => setFormData({ ...formData, appointment_date: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                  required
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Duration (minutes)"
                  type="number"
                  value={formData.duration_minutes}
                  onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Notes"
                  multiline
                  rows={3}
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Diagnosis"
                  multiline
                  rows={2}
                  value={formData.diagnosis}
                  onChange={(e) => setFormData({ ...formData, diagnosis: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Treatment Plan"
                  multiline
                  rows={2}
                  value={formData.treatment_plan}
                  onChange={(e) => setFormData({ ...formData, treatment_plan: e.target.value })}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit" variant="contained">
              {editingAppointment ? 'Update' : 'Schedule'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
};

export default Appointments;
