import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Header: React.FC = () => {
  const { logout } = useAuth();
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
        <button onClick={handleLogout} className="btn btn-secondary">
          Logout
        </button>
      </nav>
    </header>
  );
};

export default Header;
