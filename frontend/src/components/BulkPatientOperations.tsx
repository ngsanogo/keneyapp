/**
 * Bulk Patient Operations Component
 * Allows bulk deletion and other operations on patients
 */

import React, { useState } from 'react';
import axios from 'axios';
import './BulkPatientOperations.css';

interface BulkOperationsProps {
  selectedPatientIds: number[];
  onSuccess: () => void;
  onClose: () => void;
  token: string;
}

interface BulkOperationResult {
  success: boolean;
  processed: number;
  failed: number;
  errors: Array<{ patient_id: number; error: string }>;
}

const BulkPatientOperations: React.FC<BulkOperationsProps> = ({
  selectedPatientIds,
  onSuccess,
  onClose,
  token,
}) => {
  const [operation, setOperation] = useState<'delete' | 'export'>('delete');
  const [confirmText, setConfirmText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BulkOperationResult | null>(null);

  const handleBulkDelete = async () => {
    if (confirmText !== 'DELETE') {
      setError('Please type DELETE to confirm');
      return;
    }

    if (!token) return;

    try {
      setLoading(true);
      setError(null);

      const response = await axios.post(
        '/api/v1/patients/bulk/delete',
        {
          patient_ids: selectedPatientIds,
          confirmed: true,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setResult(response.data);

      if (response.data.success) {
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 2000);
      }
    } catch (err: any) {
      console.error('Bulk delete failed:', err);
      setError(err.response?.data?.detail || 'Failed to delete patients');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkExport = async () => {
    if (!token) return;

    try {
      setLoading(true);
      setError(null);

      const params = {
        patient_ids: selectedPatientIds.join(','),
      };

      const response = await axios.get('/api/v1/patients/export/csv', {
        headers: { Authorization: `Bearer ${token}` },
        params,
        responseType: 'blob',
      });

      // Download file
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      const timestamp = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `selected_patients_${timestamp}.csv`);

      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err: any) {
      console.error('Bulk export failed:', err);
      setError(err.response?.data?.detail || 'Failed to export patients');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    if (operation === 'delete') {
      handleBulkDelete();
    } else if (operation === 'export') {
      handleBulkExport();
    }
  };

  const isDeleteConfirmed = operation === 'delete' ? confirmText === 'DELETE' : true;

  return (
    <div className="bulk-operations-modal">
      <div className="modal-overlay" onClick={onClose}></div>

      <div className="modal-content">
        <div className="modal-header">
          <h2>Bulk Operations</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="selection-info">
            <div className="info-icon">📋</div>
            <div>
              <strong>{selectedPatientIds.length} patients selected</strong>
              <p>Choose an operation to perform on selected patients</p>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          {result && (
            <div className={`result-message ${result.success ? 'success' : 'warning'}`}>
              <div className="result-header">
                <span className="result-icon">{result.success ? '✓' : '⚠️'}</span>
                <strong>Operation Completed</strong>
              </div>
              <ul className="result-details">
                <li>Processed: {result.processed}</li>
                {result.failed > 0 && <li>Failed: {result.failed}</li>}
              </ul>
              {result.errors && result.errors.length > 0 && (
                <div className="errors-list">
                  <strong>Errors:</strong>
                  {result.errors.map((err, idx) => (
                    <div key={idx} className="error-item">
                      Patient ID {err.patient_id}: {err.error}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {!result && (
            <>
              {/* Operation Selection */}
              <div className="operation-selection">
                <h3>Select Operation</h3>
                <div className="operation-options">
                  <label className={`operation-option ${operation === 'delete' ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name="operation"
                      value="delete"
                      checked={operation === 'delete'}
                      onChange={() => setOperation('delete')}
                    />
                    <div className="operation-card danger">
                      <div className="operation-icon">🗑️</div>
                      <div className="operation-info">
                        <h4>Delete Patients</h4>
                        <p>Permanently remove selected patients</p>
                      </div>
                    </div>
                  </label>

                  <label className={`operation-option ${operation === 'export' ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name="operation"
                      value="export"
                      checked={operation === 'export'}
                      onChange={() => setOperation('export')}
                    />
                    <div className="operation-card">
                      <div className="operation-icon">📥</div>
                      <div className="operation-info">
                        <h4>Export to CSV</h4>
                        <p>Download selected patients data</p>
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              {/* Delete Confirmation */}
              {operation === 'delete' && (
                <div className="delete-confirmation">
                  <div className="warning-box">
                    <div className="warning-icon">⚠️</div>
                    <div>
                      <strong>Warning: This action cannot be undone!</strong>
                      <p>
                        You are about to permanently delete {selectedPatientIds.length} patient
                        {selectedPatientIds.length > 1 ? 's' : ''}. This will remove all associated 
                        data including appointments, prescriptions, and medical records.
                      </p>
                    </div>
                  </div>

                  <div className="confirmation-input">
                    <label>
                      Type <strong>DELETE</strong> to confirm:
                    </label>
                    <input
                      type="text"
                      value={confirmText}
                      onChange={(e) => setConfirmText(e.target.value)}
                      placeholder="Type DELETE"
                      autoComplete="off"
                    />
                  </div>
                </div>
              )}

              {/* Export Info */}
              {operation === 'export' && (
                <div className="export-info">
                  <div className="info-box">
                    <div className="info-icon">ℹ️</div>
                    <div>
                      <strong>Export Information</strong>
                      <p>
                        Selected patients will be exported to a CSV file. The export will include 
                        basic patient information while respecting privacy regulations.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose} disabled={loading}>
            {result ? 'Close' : 'Cancel'}
          </button>

          {!result && (
            <button
              className={`btn-primary ${operation === 'delete' ? 'btn-danger' : ''}`}
              onClick={handleSubmit}
              disabled={loading || !isDeleteConfirmed}
            >
              {loading ? (
                <>
                  <span className="spinner-small"></span> Processing...
                </>
              ) : operation === 'delete' ? (
                'Delete Patients'
              ) : (
                'Export CSV'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default BulkPatientOperations;
