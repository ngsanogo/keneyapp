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

interface Prescription {
  id: number;
  patient_id: number;
  doctor_id: number;
  medication_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions?: string;
  status: string;
  prescribed_date: string;
}

const Prescriptions: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [editingPrescription, setEditingPrescription] = useState<Prescription | null>(null);
  const [formData, setFormData] = useState({
    patient_id: '',
    doctor_id: '',
    medication_name: '',
    dosage: '',
    frequency: '',
    duration: '',
    instructions: '',
  });

  const queryClient = useQueryClient();

  const { data: prescriptions, isLoading } = useQuery('prescriptions', () =>
    axios.get('/api/prescriptions').then(res => res.data)
  );

  const { data: patients } = useQuery('patients', () =>
    axios.get('/api/patients').then(res => res.data)
  );

  const createMutation = useMutation(
    (data: any) => axios.post('/api/prescriptions', data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('prescriptions');
        setOpen(false);
        resetForm();
      },
    }
  );

  const updateMutation = useMutation(
    ({ id, data }: { id: number; data: any }) => axios.put(`/api/prescriptions/${id}`, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('prescriptions');
        setOpen(false);
        resetForm();
      },
    }
  );

  const deleteMutation = useMutation(
    (id: number) => axios.delete(`/api/prescriptions/${id}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('prescriptions');
      },
    }
  );

  const resetForm = () => {
    setFormData({
      patient_id: '',
      doctor_id: '',
      medication_name: '',
      dosage: '',
      frequency: '',
      duration: '',
      instructions: '',
    });
    setEditingPrescription(null);
  };

  const handleOpen = (prescription?: Prescription) => {
    if (prescription) {
      setEditingPrescription(prescription);
      setFormData({
        patient_id: prescription.patient_id.toString(),
        doctor_id: prescription.doctor_id.toString(),
        medication_name: prescription.medication_name,
        dosage: prescription.dosage,
        frequency: prescription.frequency,
        duration: prescription.duration,
        instructions: prescription.instructions || '',
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
      prescribed_date: new Date().toISOString(),
    };
    
    if (editingPrescription) {
      updateMutation.mutate({ id: editingPrescription.id, data: submitData });
    } else {
      createMutation.mutate(submitData);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'completed': return 'info';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  if (isLoading) return <Typography>Loading...</Typography>;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Prescriptions</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpen()}
        >
          New Prescription
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Patient</TableCell>
              <TableCell>Medication</TableCell>
              <TableCell>Dosage</TableCell>
              <TableCell>Frequency</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Prescribed Date</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {prescriptions?.map((prescription: Prescription) => {
              const patient = patients?.find((p: any) => p.id === prescription.patient_id);
              return (
                <TableRow key={prescription.id}>
                  <TableCell>
                    {patient ? `${patient.first_name} ${patient.last_name}` : 'Unknown Patient'}
                  </TableCell>
                  <TableCell>{prescription.medication_name}</TableCell>
                  <TableCell>{prescription.dosage}</TableCell>
                  <TableCell>{prescription.frequency}</TableCell>
                  <TableCell>{prescription.duration}</TableCell>
                  <TableCell>
                    <Chip
                      label={prescription.status}
                      color={getStatusColor(prescription.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(prescription.prescribed_date).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <IconButton onClick={() => handleOpen(prescription)}>
                      <Edit />
                    </IconButton>
                    <IconButton onClick={() => deleteMutation.mutate(prescription.id)}>
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
          {editingPrescription ? 'Edit Prescription' : 'New Prescription'}
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
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Medication Name"
                  value={formData.medication_name}
                  onChange={(e) => setFormData({ ...formData, medication_name: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Dosage"
                  value={formData.dosage}
                  onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Frequency"
                  value={formData.frequency}
                  onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Duration"
                  value={formData.duration}
                  onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Instructions"
                  multiline
                  rows={3}
                  value={formData.instructions}
                  onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button type="submit" variant="contained">
              {editingPrescription ? 'Update' : 'Create'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
};

export default Prescriptions;
