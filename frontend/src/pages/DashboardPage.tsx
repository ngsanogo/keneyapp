import { useQuery } from 'react-query';
import apiClient from '../lib/api';
import { TrendingUp, TrendingDown, Users, Calendar, DollarSign } from 'lucide-react';

function StatCard({ 
  title, 
  value, 
  change, 
  icon: Icon,
  trend 
}: { 
  title: string; 
  value: string | number; 
  change: number; 
  icon: any;
  trend: 'up' | 'down';
}) {
  const isPositive = change >= 0;
  
  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '0.5rem' }}>{title}</p>
          <p style={{ fontSize: '2rem', fontWeight: 'bold' }}>{value}</p>
          <div style={{ display: 'flex', alignItems: 'center', marginTop: '0.5rem' }}>
            {isPositive ? (
              <TrendingUp size={16} style={{ color: '#10b981', marginRight: '0.25rem' }} />
            ) : (
              <TrendingDown size={16} style={{ color: '#ef4444', marginRight: '0.25rem' }} />
            )}
            <span style={{ 
              fontSize: '0.875rem', 
              color: isPositive ? '#10b981' : '#ef4444' 
            }}>
              {Math.abs(change)}%
            </span>
            <span style={{ fontSize: '0.875rem', color: '#6b7280', marginLeft: '0.25rem' }}>
              from last month
            </span>
          </div>
        </div>
        <div style={{ 
          padding: '0.75rem', 
          background: '#eff6ff', 
          borderRadius: '0.5rem' 
        }}>
          <Icon size={24} style={{ color: '#2563eb' }} />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useQuery(
    'dashboard-stats',
    () => apiClient.getDashboardStats(),
    { refetchInterval: 30000 }
  );

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <div className="loading" style={{ width: '3rem', height: '3rem' }} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '1rem', background: '#fee2e2', color: '#dc2626', borderRadius: '0.5rem' }}>
        Failed to load dashboard data
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
        Dashboard
      </h1>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        <StatCard
          title="Total Patients"
          value={stats?.total_patients || 0}
          change={stats?.patients_change || 0}
          icon={Users}
          trend={stats && stats.patients_change >= 0 ? 'up' : 'down'}
        />
        <StatCard
          title="Appointments"
          value={stats?.total_appointments || 0}
          change={stats?.appointments_change || 0}
          icon={Calendar}
          trend={stats && stats.appointments_change >= 0 ? 'up' : 'down'}
        />
        <StatCard
          title="Revenue"
          value={`$${stats?.revenue?.toLocaleString() || 0}`}
          change={stats?.revenue_change || 0}
          icon={DollarSign}
          trend={stats && stats.revenue_change >= 0 ? 'up' : 'down'}
        />
      </div>

      <div className="card">
        <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          Quick Actions
        </h2>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => window.location.href = '/patients'}>
            View All Patients
          </button>
          <button className="btn btn-secondary" onClick={() => window.location.href = '/patients'}>
            Add New Patient
          </button>
        </div>
      </div>
    </div>
  );
}
