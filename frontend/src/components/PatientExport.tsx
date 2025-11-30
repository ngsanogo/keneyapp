/**
 * Patient Export Component
 * Allows exporting patient data in multiple formats with filtering
 */

import React, { useState } from 'react';
import axios from 'axios';
import './PatientExport.css';

interface ExportFilters {
  search?: string;
  gender?: string;
  city?: string;
  has_allergies?: boolean;
  has_medical_history?: boolean;
}

const PatientExport: React.FC<{ token: string; onClose?: () => void }> = ({ token, onClose }) => {
  const [format, setFormat] = useState<'csv' | 'pdf' | 'json'>('csv');
  const [filters, setFilters] = useState<ExportFilters>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleExport = async () => {
    if (!token) return;

    try {
      setLoading(true);
      setError(null);
      setSuccess(false);

      const params: any = { ...filters };
      
      const response = await axios.get(`/api/v1/patients/export/${format}`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
        responseType: 'blob',
      });

      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `patients_export_${timestamp}.${format}`;
      link.setAttribute('download', filename);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSuccess(true);
      setTimeout(() => {
        if (onClose) onClose();
      }, 2000);
    } catch (err: any) {
      console.error('Export failed:', err);
      setError(err.response?.data?.detail || 'Failed to export patient data');
    } finally {
      setLoading(false);
    }
  };

  const updateFilter = (key: keyof ExportFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({});
  };

  return (
    <div className="patient-export">
      <div className="export-header">
        <h2>Export Patient Data</h2>
        {onClose && (
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        )}
      </div>

      {success && (
        <div className="success-message">
          ✓ Export completed successfully! Your download should start automatically.
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <div className="export-content">
        {/* Format Selection */}
        <div className="section">
          <h3>Export Format</h3>
          <div className="format-options">
            <label className={`format-option ${format === 'csv' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="format"
                value="csv"
                checked={format === 'csv'}
                onChange={() => setFormat('csv')}
              />
              <div className="format-card">
                <div className="format-icon">📊</div>
                <div className="format-info">
                  <h4>CSV</h4>
                  <p>Spreadsheet compatible</p>
                </div>
              </div>
            </label>

            <label className={`format-option ${format === 'pdf' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="format"
                value="pdf"
                checked={format === 'pdf'}
                onChange={() => setFormat('pdf')}
              />
              <div className="format-card">
                <div className="format-icon">📄</div>
                <div className="format-info">
                  <h4>PDF</h4>
                  <p>Formatted report</p>
                </div>
              </div>
            </label>

            <label className={`format-option ${format === 'json' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="format"
                value="json"
                checked={format === 'json'}
                onChange={() => setFormat('json')}
              />
              <div className="format-card">
                <div className="format-icon">💾</div>
                <div className="format-info">
                  <h4>JSON</h4>
                  <p>Integration ready</p>
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Filters */}
        <div className="section">
          <div className="section-header">
            <h3>Filters (Optional)</h3>
            <button className="btn-ghost" onClick={clearFilters}>
              Clear All
            </button>
          </div>

          <div className="filters-grid">
            <div className="filter-item">
              <label>Search (Name/Email/Phone)</label>
              <input
                type="text"
                value={filters.search || ''}
                onChange={(e) => updateFilter('search', e.target.value)}
                placeholder="Search patients..."
              />
            </div>

            <div className="filter-item">
              <label>Gender</label>
              <select
                value={filters.gender || ''}
                onChange={(e) => updateFilter('gender', e.target.value || undefined)}
              >
                <option value="">All</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="filter-item">
              <label>City</label>
              <input
                type="text"
                value={filters.city || ''}
                onChange={(e) => updateFilter('city', e.target.value || undefined)}
                placeholder="Filter by city..."
              />
            </div>

            <div className="filter-item checkbox-filter">
              <label>
                <input
                  type="checkbox"
                  checked={filters.has_allergies || false}
                  onChange={(e) => updateFilter('has_allergies', e.target.checked || undefined)}
                />
                Has Allergies
              </label>
            </div>

            <div className="filter-item checkbox-filter">
              <label>
                <input
                  type="checkbox"
                  checked={filters.has_medical_history || false}
                  onChange={(e) => updateFilter('has_medical_history', e.target.checked || undefined)}
                />
                Has Medical History
              </label>
            </div>
          </div>
        </div>

        {/* Info Box */}
        <div className="info-box">
          <div className="info-icon">ℹ️</div>
          <div>
            <strong>Privacy Notice:</strong> Exported data contains sensitive patient information. 
            Handle with care and ensure compliance with GDPR/HIPAA regulations.
          </div>
        </div>

        {/* Actions */}
        <div className="export-actions">
          {onClose && (
            <button className="btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
          )}
          <button className="btn-primary" onClick={handleExport} disabled={loading}>
            {loading ? (
              <>
                <span className="spinner-small"></span> Exporting...
              </>
            ) : (
              <>📥 Export {format.toUpperCase()}</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PatientExport;
