import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './LoginPage.css';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    }
  };

  return (
    <main id="main-content" className="login-container" aria-labelledby="login-heading">
      <div className="login-card" role="presentation">
        <header className="login-header">
          <p className="eyebrow">Secure access</p>
          <h1 id="login-heading">KeneyApp workspace</h1>
          <p className="subtext">
            Sign in to manage patient records, appointments, and prescriptions in a single, protected workspace.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="login-form" aria-describedby="demo-accounts">
          {error && (
            <div className="error-message" role="alert" aria-live="assertive">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoFocus
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <div className="demo-credentials" id="demo-accounts">
          <p className="demo-label">Demo access</p>
          <div className="demo-grid">
            <div>
              <p className="demo-role">Admin</p>
              <p className="demo-creds">admin / admin123</p>
            </div>
            <div>
              <p className="demo-role">Doctor</p>
              <p className="demo-creds">doctor / doctor123</p>
            </div>
            <div>
              <p className="demo-role">Nurse</p>
              <p className="demo-creds">nurse / nurse123</p>
            </div>
            <div>
              <p className="demo-role">Receptionist</p>
              <p className="demo-creds">receptionist / receptionist123</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};

export default LoginPage;
