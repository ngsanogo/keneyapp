/**
 * Audit Log Viewer Page (Admin Only)
 * Displays comprehensive audit trail of system activities
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './AuditLogPage.css';

interface AuditLog {
  id: number;
  action: string;
  resource_type: string;
  resource_id?: number;
  user_id: number;
  username?: string;
  details?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
  correlation_id?: string;
}

const AuditLogPage: React.FC = () => {
  const navigate = useNavigate();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [resourceFilter, setResourceFilter] = useState<string>('all');
  const [userFilter, setUserFilter] = useState<string>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(50);

  // Selected log for details
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const token = localStorage.getItem('token');

  const fetchAuditLogs = useCallback(async () => {
    if (!token) {
      navigate('/login');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params: any = {
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
      };

      if (actionFilter !== 'all') params.action = actionFilter;
      if (resourceFilter !== 'all') params.resource_type = resourceFilter;
      if (userFilter) params.username = userFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      // Note: This endpoint would need to be created in the backend
      const response = await axios.get('/api/v1/audit/logs', {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });

      setLogs(response.data.items || []);
      setTotalPages(Math.ceil((response.data.total || 0) / pageSize));
    } catch (err: any) {
      console.error('Failed to fetch audit logs:', err);
      setError(err.response?.data?.detail || 'Failed to load audit logs');

      if (err.response?.status === 401) {
        navigate('/login');
      } else if (err.response?.status === 403) {
        setError('Access denied. Admin privileges required.');
      }
    } finally {
      setLoading(false);
    }
  }, [token, navigate, currentPage, pageSize, actionFilter, resourceFilter, userFilter, dateFrom, dateTo]);

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  const getActionBadge = (action: string): JSX.Element => {
    const colors: Record<string, string> = {
      CREATE: 'green',
      READ: 'blue',
      UPDATE: 'yellow',
      DELETE: 'red',
      LOGIN: 'purple',
      LOGOUT: 'gray',
      ACCESS_DENIED: 'red',
      SECURITY_ALERT: 'red',
    };
    const color = colors[action] || 'gray';
    return <span className={`action-badge badge-${color}`}>{action}</span>;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const exportLogs = async () => {
    if (!token) return;

    try {
      const params: any = {};
      if (actionFilter !== 'all') params.action = actionFilter;
      if (resourceFilter !== 'all') params.resource_type = resourceFilter;
      if (userFilter) params.username = userFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const response = await axios.get('/api/v1/audit/export', {
        headers: { Authorization: `Bearer ${token}` },
        params,
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      const timestamp = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `audit_logs_${timestamp}.csv`);

      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Export failed:', err);
      alert(err.response?.data?.detail || 'Failed to export audit logs');
    }
  };

  if (loading && logs.length === 0) {
    return (
      <div className="audit-log-page">
        <div className="loading-spinner">Loading audit logs...</div>
      </div>
    );
  }

  return (
    <div className="audit-log-page">
      <div className="audit-header">
        <div>
          <h1>🔍 Audit Log</h1>
          <p className="subtitle">Complete system activity trail</p>
        </div>
        <button className="btn btn-primary" onClick={exportLogs}>
          📥 Export Logs
        </button>
      </div>

      {/* Filters */}
      <div className="audit-filters">
        <div className="filter-row">
          <div className="filter-group">
            <label>Action:</label>
            <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}>
              <option value="all">All Actions</option>
              <option value="CREATE">Create</option>
              <option value="READ">Read</option>
              <option value="UPDATE">Update</option>
              <option value="DELETE">Delete</option>
              <option value="LOGIN">Login</option>
              <option value="LOGOUT">Logout</option>
              <option value="ACCESS_DENIED">Access Denied</option>
              <option value="SECURITY_ALERT">Security Alert</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Resource:</label>
            <select value={resourceFilter} onChange={(e) => setResourceFilter(e.target.value)}>
              <option value="all">All Resources</option>
              <option value="patient">Patient</option>
              <option value="appointment">Appointment</option>
              <option value="prescription">Prescription</option>
              <option value="user">User</option>
              <option value="tenant">Tenant</option>
            </select>
          </div>

          <div className="filter-group">
            <label>User:</label>
            <input
              type="text"
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              placeholder="Filter by username..."
            />
          </div>
        </div>

        <div className="filter-row">
          <div className="filter-group">
            <label>From:</label>
            <input
              type="datetime-local"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label>To:</label>
            <input
              type="datetime-local"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>

          <button className="btn btn-secondary" onClick={() => {
            setActionFilter('all');
            setResourceFilter('all');
            setUserFilter('');
            setDateFrom('');
            setDateTo('');
          }}>
            Clear Filters
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Audit Logs Table */}
      <div className="audit-table-container">
        {logs.length === 0 ? (
          <div className="empty-state">
            <p>No audit logs found</p>
          </div>
        ) : (
          <table className="audit-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action</th>
                <th>Resource</th>
                <th>User</th>
                <th>IP Address</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} onClick={() => setSelectedLog(log)} className="clickable-row">
                  <td className="timestamp-cell">{formatDate(log.timestamp)}</td>
                  <td>{getActionBadge(log.action)}</td>
                  <td>
                    <span className="resource-type">{log.resource_type}</span>
                    {log.resource_id && <span className="resource-id">#{log.resource_id}</span>}
                  </td>
                  <td className="user-cell">{log.username || `User ${log.user_id}`}</td>
                  <td className="ip-cell">{log.ip_address || 'N/A'}</td>
                  <td>
                    <button className="btn-view-details">View Details</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-secondary"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((p) => p - 1)}
          >
            Previous
          </button>
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <button
            className="btn btn-secondary"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}

      {/* Details Modal */}
      {selectedLog && (
        <div className="modal-overlay" onClick={() => setSelectedLog(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Audit Log Details</h2>
              <button className="close-btn" onClick={() => setSelectedLog(null)}>
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="detail-grid">
                <div className="detail-item">
                  <strong>Action:</strong>
                  {getActionBadge(selectedLog.action)}
                </div>
                <div className="detail-item">
                  <strong>Resource:</strong>
                  <span>{selectedLog.resource_type}</span>
                </div>
                <div className="detail-item">
                  <strong>Resource ID:</strong>
                  <span>{selectedLog.resource_id || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <strong>User:</strong>
                  <span>{selectedLog.username || `User ${selectedLog.user_id}`}</span>
                </div>
                <div className="detail-item">
                  <strong>IP Address:</strong>
                  <span>{selectedLog.ip_address || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <strong>Timestamp:</strong>
                  <span>{formatDate(selectedLog.timestamp)}</span>
                </div>
                {selectedLog.correlation_id && (
                  <div className="detail-item full-width">
                    <strong>Correlation ID:</strong>
                    <code>{selectedLog.correlation_id}</code>
                  </div>
                )}
                {selectedLog.user_agent && (
                  <div className="detail-item full-width">
                    <strong>User Agent:</strong>
                    <code>{selectedLog.user_agent}</code>
                  </div>
                )}
              </div>

              {selectedLog.details && Object.keys(selectedLog.details).length > 0 && (
                <div className="details-section">
                  <strong>Additional Details:</strong>
                  <pre className="json-display">{JSON.stringify(selectedLog.details, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditLogPage;
