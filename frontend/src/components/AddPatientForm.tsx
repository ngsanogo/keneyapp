import { useState, type ChangeEvent, type FormEvent } from 'react';
// Shim for process typing until @types/node is installed
declare const process: { env: Record<string, string | undefined> };
// Temporary JSX typing until @types/react is installed (remove after installing types)
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elem: string]: any;
    }
  }
}

interface AddPatientFormProps {
  onAdd: (patient: any) => void;
  onClose: () => void;
  token: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Lightweight type for the outbound payload (kept minimal)
type PatientPayload = {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: 'female' | 'male' | 'other';
  email?: string;
  phone: string;
  address?: string;
  medical_history?: string;
  allergies?: string;
  blood_type?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  tenant_id?: string;
};

// Helper: base64url-safe decode for JWT payloads
function base64UrlDecode(input: string): string {
  const base64 = input
    .replace(/-/g, '+')
    .replace(/_/g, '/')
    .padEnd(Math.ceil(input.length / 4) * 4, '=');
  return atob(base64);
}

// Helper: today's ISO date (yyyy-mm-dd) for max on date input
function todayIsoDate(): string {
  return new Date().toISOString().split('T')[0];
}

// Configurable request timeout
const DEFAULT_TIMEOUT_MS = 15000;
function getTimeoutMs(): number {
  const v = Number(process.env.REACT_APP_API_TIMEOUT_MS);
  return Number.isFinite(v) && v > 0 ? v : DEFAULT_TIMEOUT_MS;
}

// Extract tenant_id from JWT (base64url-safe)
function getTenantIdFromToken(token: string): string | null {
  try {
    const [, payload] = token.split('.');
    const decoded = JSON.parse(base64UrlDecode(payload));
    return decoded?.tenant_id || decoded?.tenant || null;
  } catch {
    return null;
  }
}

// Generate a correlation/request ID
function getRequestId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `req_${Math.random().toString(36).slice(2)}_${Date.now()}`;
}

type FieldErrors = Partial<Record<keyof PatientPayload, string>>;

const AddPatientForm = ({ onAdd, onClose, token }: AddPatientFormProps) => {
  const [form, setForm] = useState<{
    first_name: string;
    last_name: string;
    date_of_birth: string;
    gender: 'female' | 'male' | 'other';
    email: string;
    phone: string;
    address: string;
    medical_history: string;
    allergies: string;
    blood_type: string;
    emergency_contact: string;
    emergency_phone: string;
  }>({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'female',
    email: '',
    phone: '',
    address: '',
    medical_history: '',
    allergies: '',
    blood_type: '',
    emergency_contact: '',
    emergency_phone: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const validateForm = (): FieldErrors => {
    const errs: FieldErrors = {};
    // Date of birth must be valid and not in the future
    if (form.date_of_birth) {
      const dob = new Date(form.date_of_birth);
      const today = new Date(todayIsoDate());
      if (isNaN(dob.getTime())) errs.date_of_birth = 'Invalid date';
      else if (dob > today) errs.date_of_birth = 'Date cannot be in the future';
      else {
        const age = (today.getTime() - dob.getTime()) / (365.25 * 24 * 3600 * 1000);
        if (age > 130) errs.date_of_birth = 'Please enter a valid date of birth';
      }
    }
    // Email (if provided) must be valid
    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      errs.email = 'Enter a valid email';
    }
    // Phone: basic sanity
    if (!form.phone || form.phone.replace(/[^\d]/g, '').length < 7) {
      errs.phone = 'Enter a valid phone number';
    }
    // Blood type (if provided)
    if (form.blood_type && !/^(A|B|AB|O)[+-]$/.test(form.blood_type)) {
      errs.blood_type = 'Use types like A+, O-, AB+';
    }
    return errs;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setFieldErrors({});

    // Client-side validation
    const errs = validateForm();
    if (Object.keys(errs).length) {
      setFieldErrors(errs);
      setError('Please fix the highlighted fields.');
      setLoading(false);
      return;
    }

    // Normalize/trim values
    const normalized = Object.fromEntries(
      Object.entries(form).map(([k, v]) => [k, typeof v === 'string' ? v.trim() : v])
    ) as typeof form;

    // Build payload, drop empty optional fields, and add tenant_id
    const tenantId = getTenantIdFromToken(token);
    const basePayload: PatientPayload = {
      ...normalized,
      ...(tenantId ? { tenant_id: tenantId } : {}),
    };
    Object.keys(basePayload).forEach(k => {
      // remove empty optional fields
      // @ts-expect-error dynamic key
      if (basePayload[k] === '') delete basePayload[k];
    });

    const requestId = getRequestId();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), getTimeoutMs());

    try {
      const res = await fetch(`${API_URL}/api/v1/patients/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Request-ID': requestId,
        },
        body: JSON.stringify(basePayload),
        signal: controller.signal,
      });

      if (!res.ok) {
        let msg = 'Failed to add patient';
        const ct = res.headers.get('content-type') || '';
        try {
          if (res.status === 429) {
            msg = 'Rate limit exceeded. Please try again shortly.';
          } else if (ct.includes('application/json')) {
            const data = await res.json();
            // Map FastAPI validation errors to fields if present
            if (Array.isArray(data?.detail)) {
              const fe: FieldErrors = {};
              for (const d of data.detail) {
                const loc = Array.isArray(d?.loc) ? d.loc[d.loc.length - 1] : d?.loc;
                if (typeof loc === 'string' && typeof d?.msg === 'string')
                  fe[loc as keyof FieldErrors] = d.msg;
              }
              if (Object.keys(fe).length) setFieldErrors(fe);
              msg = data?.title || 'Please correct the highlighted fields.';
            } else {
              msg = data?.detail || msg;
            }
          } else {
            const text = await res.text();
            msg = text || msg;
          }
        } catch {
          // keep default msg
        }
        // include correlation for support
        throw new Error(`${msg} (Ref: ${requestId})`);
      }

      const data = await res.json();
      onAdd(data);
      onClose();
    } catch (err: any) {
      if (err?.name === 'AbortError') {
        setError('Request timed out. Please try again.'); // no Ref: because request didn’t reach server reliably
      } else {
        setError(err?.message || 'Failed to add patient');
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Add Patient</h2>
        <form onSubmit={handleSubmit} aria-label="Add new patient form">
          <div className="form-row">
            <input
              name="first_name"
              placeholder="First Name"
              value={form.first_name}
              onChange={handleChange}
              required
              aria-label="First name"
              autoComplete="given-name"
              aria-invalid={!!fieldErrors.first_name}
              aria-describedby={fieldErrors.first_name ? 'first_name_error' : undefined}
            />
            {fieldErrors.first_name && (
              <span id="first_name_error" className="field-error">
                {fieldErrors.first_name}
              </span>
            )}
            <input
              name="last_name"
              placeholder="Last Name"
              value={form.last_name}
              onChange={handleChange}
              required
              aria-label="Last name"
              autoComplete="family-name"
              aria-invalid={!!fieldErrors.last_name}
              aria-describedby={fieldErrors.last_name ? 'last_name_error' : undefined}
            />
            {fieldErrors.last_name && (
              <span id="last_name_error" className="field-error">
                {fieldErrors.last_name}
              </span>
            )}
          </div>
          <div className="form-row">
            <input
              name="date_of_birth"
              type="date"
              value={form.date_of_birth}
              onChange={handleChange}
              required
              aria-label="Date of birth"
              max={todayIsoDate()}
              aria-invalid={!!fieldErrors.date_of_birth}
              aria-describedby={fieldErrors.date_of_birth ? 'dob_error' : undefined}
            />
            {fieldErrors.date_of_birth && (
              <span id="dob_error" className="field-error">
                {fieldErrors.date_of_birth}
              </span>
            )}
            <select
              name="gender"
              value={form.gender}
              onChange={handleChange}
              required
              aria-label="Gender"
            >
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="form-row">
            <input
              name="email"
              placeholder="Email"
              value={form.email}
              onChange={handleChange}
              type="email"
              aria-label="Email"
              autoComplete="email"
              aria-invalid={!!fieldErrors.email}
              aria-describedby={fieldErrors.email ? 'email_error' : undefined}
            />
            {fieldErrors.email && (
              <span id="email_error" className="field-error">
                {fieldErrors.email}
              </span>
            )}
            <input
              name="phone"
              placeholder="Phone"
              value={form.phone}
              onChange={handleChange}
              required
              type="tel"
              inputMode="tel"
              pattern="^[0-9+\-\s()]{7,}$"
              aria-label="Phone"
              autoComplete="tel"
              title="Enter a valid phone number"
              aria-invalid={!!fieldErrors.phone}
              aria-describedby={fieldErrors.phone ? 'phone_error' : undefined}
            />
            {fieldErrors.phone && (
              <span id="phone_error" className="field-error">
                {fieldErrors.phone}
              </span>
            )}
          </div>
          <div className="form-row">
            <input
              name="address"
              placeholder="Address"
              value={form.address}
              onChange={handleChange}
              autoComplete="street-address"
            />
          </div>
          <div className="form-row">
            <input
              name="medical_history"
              placeholder="Medical History"
              value={form.medical_history}
              onChange={handleChange}
            />
            <input
              name="allergies"
              placeholder="Allergies"
              value={form.allergies}
              onChange={handleChange}
            />
          </div>
          <div className="form-row">
            <input
              name="blood_type"
              placeholder="Blood Type"
              value={form.blood_type}
              onChange={handleChange}
              pattern="^(A|B|AB|O)[+-]$"
              title="A+, A-, B+, B-, AB+, AB-, O+, O-"
              aria-invalid={!!fieldErrors.blood_type}
              aria-describedby={fieldErrors.blood_type ? 'blood_error' : undefined}
            />
            {fieldErrors.blood_type && (
              <span id="blood_error" className="field-error">
                {fieldErrors.blood_type}
              </span>
            )}
            <input
              name="emergency_contact"
              placeholder="Emergency Contact"
              value={form.emergency_contact}
              onChange={handleChange}
              autoComplete="name"
            />
            <input
              name="emergency_phone"
              placeholder="Emergency Phone"
              value={form.emergency_phone}
              onChange={handleChange}
              type="tel"
              autoComplete="tel"
            />
          </div>
          {error && (
            <div className="error" role="alert">
              {error}
            </div>
          )}
          <div className="form-actions">
            <button type="submit" disabled={loading}>
              {loading ? 'Adding...' : 'Add Patient'}
            </button>
            <button type="button" onClick={onClose}>
              Cancel
            </button>
          </div>
        </form>
      </div>
      <style>{`
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem; }
        .modal { background: linear-gradient(145deg, rgba(255,255,255,0.02), rgba(255,255,255,0.04)); padding: 1.5rem; border-radius: 16px; min-width: 340px; max-width: 520px; box-shadow: 0 30px 80px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08); color: #e2e8f0; }
        .form-row { display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
        .form-row input, .form-row select { flex: 1; padding: 0.75rem; border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; background: rgba(255,255,255,0.04); color: #e2e8f0; }
        .form-row input:focus, .form-row select:focus { outline: 2px solid rgba(56, 189, 248, 0.8); box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.15); }
        .form-actions { display: flex; gap: 1rem; justify-content: flex-end; flex-wrap: wrap; }
        .form-actions button { padding: 0.75rem 1.2rem; border-radius: 10px; font-weight: 700; border: none; cursor: pointer; }
        .form-actions button[type='submit'] { background: linear-gradient(135deg, #38bdf8, #06b6d4); color: #0b1020; }
        .form-actions button[type='button'] { background: rgba(148, 163, 184, 0.2); color: #e2e8f0; border: 1px solid rgba(148, 163, 184, 0.4); }
        .error { color: #fecdd3; background: rgba(239, 68, 68, 0.15); padding: 0.75rem 1rem; border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.35); margin-bottom: 1rem; }
        .field-error { color: #fecdd3; font-size: 0.85rem; margin-top: -0.5rem; }
      `}</style>
    </div>
  );
};

export default AddPatientForm;
