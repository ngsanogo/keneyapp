/**
 * Notification Preferences Settings Page
 * Allows users to configure notification channels and quiet hours
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './NotificationPreferencesPage.css';

interface NotificationPreferences {
  email_enabled: boolean;
  email_appointment_reminder: boolean;
  email_lab_result: boolean;
  email_prescription_ready: boolean;
  email_message_received: boolean;
  email_system_alert: boolean;
  email_security_alert: boolean;
  email_payment_reminder: boolean;
  
  sms_enabled: boolean;
  sms_appointment_reminder: boolean;
  sms_security_alert: boolean;
  sms_lab_result: boolean;
  sms_urgent_only: boolean;
  
  push_enabled: boolean;
  push_appointment_reminder: boolean;
  push_message_received: boolean;
  push_lab_result: boolean;
  push_system_alert: boolean;
  push_security_alert: boolean;
  
  websocket_enabled: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
}

const NotificationPreferencesPage: React.FC = () => {
  const navigate = useNavigate();
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchPreferences = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/v1/notifications/preferences', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setPreferences(response.data);
      } catch (err: any) {
        console.error('Failed to fetch preferences:', err);
        setError(err.response?.data?.detail || 'Failed to load preferences');
        
        if (err.response?.status === 401) {
          navigate('/login');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPreferences();
  }, [token, navigate]);

  const handleSave = async () => {
    if (!token || !preferences) return;

    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      await axios.put('/api/v1/notifications/preferences', preferences, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setSuccessMessage('Preferences saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      console.error('Failed to save preferences:', err);
      setError(err.response?.data?.detail || 'Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (window.confirm('Reset all preferences to defaults?')) {
      const defaultPreferences: NotificationPreferences = {
        email_enabled: true,
        email_appointment_reminder: true,
        email_lab_result: true,
        email_prescription_ready: true,
        email_message_received: true,
        email_system_alert: true,
        email_security_alert: true,
        email_payment_reminder: true,
        
        sms_enabled: false,
        sms_appointment_reminder: false,
        sms_security_alert: false,
        sms_lab_result: false,
        sms_urgent_only: false,
        
        push_enabled: true,
        push_appointment_reminder: true,
        push_message_received: true,
        push_lab_result: true,
        push_system_alert: true,
        push_security_alert: true,
        
        websocket_enabled: true,
        quiet_hours_enabled: false,
        quiet_hours_start: '22:00',
        quiet_hours_end: '08:00',
      };
      setPreferences(defaultPreferences);
    }
  };

  const updatePreference = (key: keyof NotificationPreferences, value: any) => {
    setPreferences((prev) => (prev ? { ...prev, [key]: value } : null));
  };

  if (loading) {
    return (
      <div className="preferences-page">
        <div className="loading-spinner">Loading preferences...</div>
      </div>
    );
  }

  if (!preferences) {
    return (
      <div className="preferences-page">
        <div className="error-state">Failed to load preferences</div>
      </div>
    );
  }

  return (
    <div className="preferences-page">
      <div className="preferences-header">
        <div>
          <h1>Notification Preferences</h1>
          <p className="subtitle">Manage how and when you receive notifications</p>
        </div>
        <button className="btn btn-ghost" onClick={() => navigate('/notifications')}>
          ← Back to Notifications
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {successMessage && <div className="success-message">{successMessage}</div>}

      <div className="preferences-content">
        {/* Email Preferences */}
        <div className="preference-section">
          <div className="section-header">
            <h2>📧 Email Notifications</h2>
            <label className="toggle">
              <input
                type="checkbox"
                checked={preferences.email_enabled}
                onChange={(e) => updatePreference('email_enabled', e.target.checked)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          {preferences.email_enabled && (
            <div className="preference-options">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.email_appointment_reminder}
                  onChange={(e) => updatePreference('email_appointment_reminder', e.target.checked)}
                />
                Appointment Reminders
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.email_lab_result}
                  onChange={(e) => updatePreference('email_lab_result', e.target.checked)}
                />
                Lab Results
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.email_prescription_ready}
                  onChange={(e) => updatePreference('email_prescription_ready', e.target.checked)}
                />
                Prescription Ready
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.email_message_received}
                  onChange={(e) => updatePreference('email_message_received', e.target.checked)}
                />
                New Messages
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.email_system_alert}
                  onChange={(e) => updatePreference('email_system_alert', e.target.checked)}
                />
                System Alerts
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.email_security_alert}
                  onChange={(e) => updatePreference('email_security_alert', e.target.checked)}
                />
                Security Alerts
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.email_payment_reminder}
                  onChange={(e) => updatePreference('email_payment_reminder', e.target.checked)}
                />
                Payment Reminders
              </label>
            </div>
          )}
        </div>

        {/* SMS Preferences */}
        <div className="preference-section">
          <div className="section-header">
            <h2>📱 SMS Notifications</h2>
            <label className="toggle">
              <input
                type="checkbox"
                checked={preferences.sms_enabled}
                onChange={(e) => updatePreference('sms_enabled', e.target.checked)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          {preferences.sms_enabled && (
            <div className="preference-options">
              <div className="info-box">
                <strong>Note:</strong> SMS notifications may incur carrier charges. We recommend enabling only critical notifications.
              </div>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.sms_appointment_reminder}
                  onChange={(e) => updatePreference('sms_appointment_reminder', e.target.checked)}
                />
                Appointment Reminders
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.sms_security_alert}
                  onChange={(e) => updatePreference('sms_security_alert', e.target.checked)}
                />
                Security Alerts
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.sms_lab_result}
                  onChange={(e) => updatePreference('sms_lab_result', e.target.checked)}
                />
                Lab Results
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.sms_urgent_only}
                  onChange={(e) => updatePreference('sms_urgent_only', e.target.checked)}
                />
                Urgent Notifications Only
              </label>
            </div>
          )}
        </div>

        {/* Push Preferences */}
        <div className="preference-section">
          <div className="section-header">
            <h2>🔔 Push Notifications</h2>
            <label className="toggle">
              <input
                type="checkbox"
                checked={preferences.push_enabled}
                onChange={(e) => updatePreference('push_enabled', e.target.checked)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          {preferences.push_enabled && (
            <div className="preference-options">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.push_appointment_reminder}
                  onChange={(e) => updatePreference('push_appointment_reminder', e.target.checked)}
                />
                Appointment Reminders
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.push_message_received}
                  onChange={(e) => updatePreference('push_message_received', e.target.checked)}
                />
                New Messages
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.push_lab_result}
                  onChange={(e) => updatePreference('push_lab_result', e.target.checked)}
                />
                Lab Results
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.push_system_alert}
                  onChange={(e) => updatePreference('push_system_alert', e.target.checked)}
                />
                System Alerts
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.push_security_alert}
                  onChange={(e) => updatePreference('push_security_alert', e.target.checked)}
                />
                Security Alerts
              </label>
            </div>
          )}
        </div>

        {/* WebSocket Preferences */}
        <div className="preference-section">
          <div className="section-header">
            <h2>⚡ Real-time Notifications</h2>
            <label className="toggle">
              <input
                type="checkbox"
                checked={preferences.websocket_enabled}
                onChange={(e) => updatePreference('websocket_enabled', e.target.checked)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
          <p className="section-description">
            Receive instant notifications while using the application
          </p>
        </div>

        {/* Quiet Hours */}
        <div className="preference-section">
          <div className="section-header">
            <h2>🌙 Quiet Hours</h2>
            <label className="toggle">
              <input
                type="checkbox"
                checked={preferences.quiet_hours_enabled}
                onChange={(e) => updatePreference('quiet_hours_enabled', e.target.checked)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          {preferences.quiet_hours_enabled && (
            <div className="preference-options">
              <p className="section-description">
                Non-critical notifications will be held during quiet hours
              </p>
              <div className="time-picker-group">
                <div className="time-picker">
                  <label>Start Time:</label>
                  <input
                    type="time"
                    value={preferences.quiet_hours_start || '22:00'}
                    onChange={(e) => updatePreference('quiet_hours_start', e.target.value)}
                  />
                </div>
                <div className="time-picker">
                  <label>End Time:</label>
                  <input
                    type="time"
                    value={preferences.quiet_hours_end || '08:00'}
                    onChange={(e) => updatePreference('quiet_hours_end', e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="preferences-actions">
        <button className="btn btn-ghost" onClick={handleReset}>
          Reset to Defaults
        </button>
        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </div>
    </div>
  );
};

export default NotificationPreferencesPage;
