import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header: React.FC = () => {
  const { logout, user, loading } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="header">
      <h1>KeneyApp</h1>
      <nav>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/patients">Patients</Link>
        <Link to="/appointments">Appointments</Link>
        <Link to="/prescriptions">Prescriptions</Link>
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
