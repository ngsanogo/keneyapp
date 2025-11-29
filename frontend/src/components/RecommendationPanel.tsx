import { useEffect, useState } from 'react';
import axios from 'axios';
import './RecommendationPanel.css';

interface Recommendation {
  type: string;
  priority: string;
  title: string;
  description: string;
  action: string;
  metadata: Record<string, any>;
}

interface RecommendationPanelProps {
  patientId?: number;
  token: string;
  onActionClick?: (recommendation: Recommendation) => void;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const RecommendationPanel = ({ patientId, token, onActionClick }: RecommendationPanelProps) => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId) return;

    const fetchRecommendations = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await axios.get(
          `${API_URL}/api/v1/recommendations/patient/${patientId}/care`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setRecommendations(response.data);
      } catch (err) {
        console.error('Failed to fetch recommendations:', err);
        setError('Unable to load recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [patientId, token]);

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return '⚠️';
      case 'medium':
        return '⚡';
      case 'low':
        return 'ℹ️';
      default:
        return '•';
    }
  };

  const getPriorityClass = (priority: string) => {
    return `priority-${priority}`;
  };

  if (!patientId) {
    return (
      <div className="recommendation-panel">
        <div className="empty-state">
          <p>Select a patient to view care recommendations</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="recommendation-panel">
        <div className="loading-state">
          <div className="spinner" />
          <p>Analyzing patient data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="recommendation-panel">
        <div className="error-state">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="recommendation-panel">
        <div className="empty-state">
          <span className="icon">✓</span>
          <h3>All Up to Date</h3>
          <p>No recommendations at this time</p>
        </div>
      </div>
    );
  }

  return (
    <div className="recommendation-panel">
      <header className="panel-header">
        <h2>
          <span className="icon">🎯</span>
          Care Recommendations
        </h2>
        <span className="count">{recommendations.length}</span>
      </header>

      <div className="recommendations-list">
        {recommendations.map((rec, index) => (
          <article
            key={index}
            className={`recommendation-card ${getPriorityClass(rec.priority)}`}
            aria-label={`${rec.priority} priority recommendation: ${rec.title}`}
          >
            <div className="card-header">
              <span className="priority-badge" aria-label={`Priority: ${rec.priority}`}>
                {getPriorityIcon(rec.priority)} {rec.priority.toUpperCase()}
              </span>
              <span className="type-label">{rec.type.replace('_', ' ')}</span>
            </div>

            <h3>{rec.title}</h3>
            <p className="description">{rec.description}</p>

            {rec.metadata && Object.keys(rec.metadata).length > 0 && (
              <div className="metadata">
                {Object.entries(rec.metadata).map(([key, value]) => (
                  <div key={key} className="metadata-item">
                    <span className="key">{key.replace('_', ' ')}:</span>
                    <span className="value">{String(value)}</span>
                  </div>
                ))}
              </div>
            )}

            <button
              className="action-button"
              onClick={() => onActionClick && onActionClick(rec)}
              aria-label={`Take action: ${rec.action.replace('_', ' ')}`}
            >
              {rec.action.replace('_', ' ')}
            </button>
          </article>
        ))}
      </div>
    </div>
  );
};

export default RecommendationPanel;
