import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './MedicalHistoryTimeline.css';

interface TimelineEvent {
  id: number;
  date: string;
  type: 'appointment' | 'prescription' | 'lab_result' | 'document' | 'note';
  title: string;
  description: string;
  doctor?: string;
  status?: string;
  metadata?: Record<string, any>;
}

interface MedicalHistoryTimelineProps {
  patientId: number;
  startDate?: string;
  endDate?: string;
  eventTypes?: string[];
}

const MedicalHistoryTimeline: React.FC<MedicalHistoryTimelineProps> = ({
  patientId,
  startDate,
  endDate,
  eventTypes,
}) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchMedicalHistory();
  }, [patientId, startDate, endDate, eventTypes, sortOrder]);

  const fetchMedicalHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const params = new URLSearchParams();

      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (eventTypes && eventTypes.length > 0) {
        eventTypes.forEach((type) => params.append('event_types', type));
      }
      params.append('sort', sortOrder);

      const response = await axios.get(
        `/api/v1/patients/${patientId}/history?${params.toString()}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setEvents(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load medical history');
      console.error('Medical history error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (type: string): string => {
    const icons: Record<string, string> = {
      appointment: '📅',
      prescription: '💊',
      lab_result: '🧪',
      document: '📄',
      note: '📝',
    };
    return icons[type] || '📋';
  };

  const getEventColor = (type: string): string => {
    const colors: Record<string, string> = {
      appointment: '#4CAF50',
      prescription: '#2196F3',
      lab_result: '#FF9800',
      document: '#9C27B0',
      note: '#607D8B',
    };
    return colors[type] || '#757575';
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  };

  const filteredEvents = filterType === 'all' 
    ? events 
    : events.filter(e => e.type === filterType);

  const exportTimeline = async (format: 'pdf' | 'csv') => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `/api/v1/patients/${patientId}/history/export/${format}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob',
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `medical_history_${patientId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export failed:', err);
      alert('Failed to export medical history');
    }
  };

  if (loading) {
    return (
      <div className="timeline-loading">
        <div className="spinner"></div>
        <p>Loading medical history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="timeline-error">
        <p>⚠️ {error}</p>
        <button onClick={fetchMedicalHistory} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="medical-history-timeline">
      <div className="timeline-header">
        <h2>Medical History Timeline</h2>
        <div className="timeline-controls">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Events</option>
            <option value="appointment">Appointments</option>
            <option value="prescription">Prescriptions</option>
            <option value="lab_result">Lab Results</option>
            <option value="document">Documents</option>
            <option value="note">Notes</option>
          </select>

          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="sort-button"
            title={`Sort ${sortOrder === 'asc' ? 'Newest First' : 'Oldest First'}`}
          >
            {sortOrder === 'asc' ? '🔼' : '🔽'} Sort
          </button>

          <div className="export-buttons">
            <button onClick={() => exportTimeline('pdf')} className="export-btn">
              📄 PDF
            </button>
            <button onClick={() => exportTimeline('csv')} className="export-btn">
              📊 CSV
            </button>
          </div>

          <button onClick={fetchMedicalHistory} className="refresh-button" title="Refresh">
            🔄
          </button>
        </div>
      </div>

      <div className="timeline-stats">
        <div className="stat-card">
          <span className="stat-value">{events.length}</span>
          <span className="stat-label">Total Events</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">
            {events.filter(e => e.type === 'appointment').length}
          </span>
          <span className="stat-label">Appointments</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">
            {events.filter(e => e.type === 'prescription').length}
          </span>
          <span className="stat-label">Prescriptions</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">
            {events.filter(e => e.type === 'lab_result').length}
          </span>
          <span className="stat-label">Lab Results</span>
        </div>
      </div>

      {filteredEvents.length === 0 ? (
        <div className="timeline-empty">
          <p>No events found for the selected filters.</p>
        </div>
      ) : (
        <div className="timeline-container">
          {filteredEvents.map((event, index) => (
            <div
              key={event.id}
              className="timeline-item"
              style={{ borderLeftColor: getEventColor(event.type) }}
              onClick={() => setSelectedEvent(event)}
            >
              <div className="timeline-marker" style={{ backgroundColor: getEventColor(event.type) }}>
                {getEventIcon(event.type)}
              </div>
              <div className="timeline-content">
                <div className="timeline-date">{formatDate(event.date)}</div>
                <div className="timeline-actual-date">
                  {new Date(event.date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </div>
                <h3 className="timeline-title">{event.title}</h3>
                <p className="timeline-description">{event.description}</p>
                {event.doctor && (
                  <div className="timeline-doctor">👨‍⚕️ {event.doctor}</div>
                )}
                {event.status && (
                  <span className={`timeline-status status-${event.status.toLowerCase()}`}>
                    {event.status}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedEvent && (
        <div className="timeline-modal" onClick={() => setSelectedEvent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedEvent(null)}>
              ✕
            </button>
            <div className="modal-header">
              <span className="modal-icon">{getEventIcon(selectedEvent.type)}</span>
              <h2>{selectedEvent.title}</h2>
            </div>
            <div className="modal-body">
              <div className="modal-field">
                <strong>Date:</strong>{' '}
                {new Date(selectedEvent.date).toLocaleString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
              <div className="modal-field">
                <strong>Type:</strong>{' '}
                <span className="modal-type-badge">{selectedEvent.type}</span>
              </div>
              {selectedEvent.doctor && (
                <div className="modal-field">
                  <strong>Doctor:</strong> {selectedEvent.doctor}
                </div>
              )}
              {selectedEvent.status && (
                <div className="modal-field">
                  <strong>Status:</strong> {selectedEvent.status}
                </div>
              )}
              <div className="modal-field">
                <strong>Description:</strong>
                <p>{selectedEvent.description}</p>
              </div>
              {selectedEvent.metadata && Object.keys(selectedEvent.metadata).length > 0 && (
                <div className="modal-field">
                  <strong>Additional Details:</strong>
                  <pre className="modal-metadata">
                    {JSON.stringify(selectedEvent.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MedicalHistoryTimeline;
