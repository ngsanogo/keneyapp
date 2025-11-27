import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
  const { logout, user, loading } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="header">
      <h1>
        <span aria-hidden>KA</span>
        KeneyApp
      </h1>
      <nav>
        <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : undefined)}>
          Dashboard
        </NavLink>
        <NavLink to="/patients" className={({ isActive }) => (isActive ? 'active' : undefined)}>
          Patients
        </NavLink>
        <NavLink to="/appointments" className={({ isActive }) => (isActive ? 'active' : undefined)}>
          Appointments
        </NavLink>
        <NavLink to="/prescriptions" className={({ isActive }) => (isActive ? 'active' : undefined)}>
          Prescriptions
        </NavLink>
      </nav>
      <div className="header-actions">
        {user && !loading && (
          <span className="header-user">
            {user.fullName} <span className="header-role">({user.role.replace('_', ' ')})</span>
          </span>
        )}
        <button onClick={handleLogout} className="btn btn-secondary">
          Logout
        </button>
      </div>
    </header>
  );
};

export default Header;
