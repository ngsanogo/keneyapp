import { Outlet, NavLink } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { LogOut, LayoutDashboard, Users } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuthStore();

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside style={{ 
        width: '250px', 
        background: '#1f2937', 
        color: 'white', 
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>KeneyApp</h1>
          <p style={{ fontSize: '0.875rem', color: '#9ca3af', marginTop: '0.25rem' }}>Healthcare Management</p>
        </div>

        <nav style={{ flex: 1 }}>
          <NavLink
            to="/dashboard"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              padding: '0.75rem',
              borderRadius: '0.5rem',
              marginBottom: '0.5rem',
              background: isActive ? '#374151' : 'transparent',
              color: 'white',
              textDecoration: 'none',
            })}
          >
            <LayoutDashboard size={20} style={{ marginRight: '0.75rem' }} />
            Dashboard
          </NavLink>
          
          <NavLink
            to="/patients"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              padding: '0.75rem',
              borderRadius: '0.5rem',
              marginBottom: '0.5rem',
              background: isActive ? '#374151' : 'transparent',
              color: 'white',
              textDecoration: 'none',
            })}
          >
            <Users size={20} style={{ marginRight: '0.75rem' }} />
            Patients
          </NavLink>
        </nav>

        <div style={{ 
          borderTop: '1px solid #374151', 
          paddingTop: '1rem' 
        }}>
          <div style={{ marginBottom: '1rem' }}>
            <p style={{ fontWeight: 500 }}>{user?.username}</p>
            <p style={{ fontSize: '0.875rem', color: '#9ca3af' }}>{user?.role}</p>
          </div>
          <button
            onClick={logout}
            style={{
              display: 'flex',
              alignItems: 'center',
              width: '100%',
              padding: '0.75rem',
              borderRadius: '0.5rem',
              background: '#dc2626',
              color: 'white',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            <LogOut size={20} style={{ marginRight: '0.75rem' }} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, padding: '2rem', background: '#f9fafb' }}>
        <Outlet />
      </main>
    </div>
  );
}
