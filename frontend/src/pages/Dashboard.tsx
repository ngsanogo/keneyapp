import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
} from '@mui/material';
import {
  People,
  CalendarToday,
  LocalPharmacy,
  TrendingUp,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import axios from 'axios';

const Dashboard: React.FC = () => {
  const { data: patients } = useQuery('patients', () =>
    axios.get('/api/patients').then(res => res.data)
  );
  
  const { data: appointments } = useQuery('appointments', () =>
    axios.get('/api/appointments').then(res => res.data)
  );
  
  const { data: prescriptions } = useQuery('prescriptions', () =>
    axios.get('/api/prescriptions').then(res => res.data)
  );

  const stats = [
    {
      title: 'Total Patients',
      value: patients?.length || 0,
      icon: <People />,
      color: '#1976d2',
    },
    {
      title: 'Appointments',
      value: appointments?.length || 0,
      icon: <CalendarToday />,
      color: '#2e7d32',
    },
    {
      title: 'Prescriptions',
      value: prescriptions?.length || 0,
      icon: <LocalPharmacy />,
      color: '#ed6c02',
    },
    {
      title: 'Active Users',
      value: '12',
      icon: <TrendingUp />,
      color: '#9c27b0',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Box
                    sx={{
                      backgroundColor: stat.color,
                      color: 'white',
                      borderRadius: 1,
                      p: 1,
                      mr: 2,
                    }}
                  >
                    {stat.icon}
                  </Box>
                  <Box>
                    <Typography variant="h4" component="div">
                      {stat.value}
                    </Typography>
                    <Typography color="text.secondary">
                      {stat.title}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Appointments
            </Typography>
            <Typography variant="body2" color="text.secondary">
              No recent appointments
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            <Typography variant="body2" color="text.secondary">
              All systems operational
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
