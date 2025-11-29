# AI-Powered Recommendation System

## Overview

The KeneyApp recommendation system provides intelligent, data-driven care recommendations to healthcare providers, helping optimize patient care quality, appointment scheduling, and clinical workflows. The system uses collaborative filtering and rule-based algorithms to analyze patient data and generate actionable insights.

## Features

### 1. Patient Care Recommendations

Automatically analyzes patient records to recommend:

- **Appointment Scheduling**: Identifies patients overdue for appointments or with upcoming appointment needs
- **Preventive Care**: Suggests routine screenings and preventive measures based on patient age and medical history
- **Medication Review**: Flags medications that may need review based on prescription age
- **Follow-up Care**: Recommends follow-up appointments after recent visits or procedures

### 2. Priority-Based System

All recommendations are assigned priority levels:

- **High Priority** (🔴): Urgent actions requiring immediate attention (e.g., overdue appointments >90 days)
- **Medium Priority** (🟠): Important actions that should be addressed soon (e.g., overdue 30-90 days)
- **Low Priority** (🔵): Routine actions for optimal care (e.g., upcoming preventive care)

### 3. Real-Time Updates

- Recommendations refresh automatically every 5 minutes
- Manual refresh available via UI button
- Tenant-isolated recommendations ensure data privacy

## Architecture

### Backend Components

#### RecommendationService (`app/services/recommendation_service.py`)

**Core Service Methods:**

```python
class RecommendationService:
    def get_patient_care_recommendations(
        self, 
        patient_id: int, 
        tenant_id: int
    ) -> List[PatientCareRecommendation]
```

**Recommendation Algorithms:**

1. **Appointment Analysis**
   - Queries patient appointment history
   - Calculates days since last appointment
   - Assigns priority based on time elapsed:
     - >90 days: High priority
     - 30-90 days: Medium priority
     - <30 days: Low priority (preventive reminder)

2. **Preventive Care**
   - Age-based screening recommendations
   - Gender-specific preventive measures
   - Evidence-based medical guidelines

3. **Medication Review**
   - Analyzes prescription dates
   - Flags medications >90 days old for review
   - Considers medication type and refill requirements

4. **Follow-up Care**
   - Tracks recent visits (last 30 days)
   - Recommends follow-ups for specific conditions
   - Ensures continuity of care

**Priority Scoring:**
```python
def _calculate_priority_score(self, factors: dict) -> tuple[str, int]:
    """
    Calculates priority and score based on weighted factors:
    - Days overdue: High weight
    - Clinical urgency: Medium weight
    - Patient history: Low weight
    
    Returns: (priority_level, numeric_score)
    """
```

#### RecommendationsRouter (`app/routers/recommendations.py`)

**API Endpoints:**

```
GET /api/v1/recommendations/{patient_id}
- Retrieves recommendations for a specific patient
- Requires: Doctor or Nurse role
- Rate limit: 100 requests/minute
- Returns: PatientCareRecommendationList

POST /api/v1/recommendations/{recommendation_id}/acknowledge
- Marks a recommendation as acknowledged/completed
- Requires: Doctor or Nurse role
- Rate limit: 20 requests/minute
- Body: { "acknowledged_by_user_id": int, "notes": str }
```

**Security Features:**
- RBAC enforcement (Doctor/Nurse only)
- Tenant isolation (automatic via JWT token)
- Audit logging for all recommendation access
- Rate limiting to prevent abuse
- Input validation via Pydantic schemas

#### Pydantic Schemas (`app/schemas/recommendation.py`)

```python
class PatientCareRecommendation(BaseModel):
    recommendation_id: str
    patient_id: int
    recommendation_type: str
    priority: str  # "high" | "medium" | "low"
    title: str
    description: str
    suggested_action: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Frontend Components

#### RecommendationPanel (`frontend/src/components/RecommendationPanel.tsx`)

**Features:**
- Auto-refresh every 5 minutes
- Manual refresh button
- Priority-based color coding
- Loading states and error handling
- Empty state for no recommendations
- Acknowledge/complete actions

**Props:**
```typescript
interface RecommendationPanelProps {
  patientId: number;
  token: string;
}
```

**State Management:**
```typescript
const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
const [loading, setLoading] = useState<boolean>(true);
const [error, setError] = useState<string | null>(null);
const [refreshing, setRefreshing] = useState<boolean>(false);
```

**API Integration:**
```typescript
const fetchRecommendations = async () => {
  const response = await axios.get(
    `${API_URL}/api/v1/recommendations/${patientId}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  setRecommendations(response.data.recommendations);
};
```

#### AdvancedPatientSearch (`frontend/src/components/AdvancedPatientSearch.tsx`)

**Features:**
- Real-time search with debouncing (500ms)
- Advanced filters:
  - Gender filter
  - Age range (min/max)
  - Sort by (name, age, date added)
  - Sort order (ascending/descending)
- Pagination (20 results per page)
- Click-to-select patient
- Responsive design

**Filters:**
```typescript
interface SearchFilters {
  query: string;
  gender: '' | 'male' | 'female' | 'other';
  ageMin: string;
  ageMax: string;
  sortBy: 'last_name' | 'first_name' | 'date_of_birth' | 'created_at';
  sortOrder: 'asc' | 'desc';
}
```

#### EnhancedAnalyticsDashboard (`frontend/src/components/EnhancedAnalyticsDashboard.tsx`)

**Features:**
- Real-time metrics dashboard
- Auto-refresh every 5 minutes
- Time range selection (7/30/90 days)
- Interactive charts (Chart.js):
  - Line chart: Appointment trends
  - Bar chart: Revenue overview
  - Doughnut chart: Department distribution
- Responsive grid layout
- Print-friendly styles

**Key Metrics:**
- Total patients
- Completed appointments
- Pending appointments
- Cancelled appointments
- Monthly revenue with growth percentage
- Average wait time

## Integration Guide

### Adding Recommendations to a Page

1. **Import the component:**
```typescript
import RecommendationPanel from '../components/RecommendationPanel';
```

2. **Add state for patient selection:**
```typescript
const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
```

3. **Render the panel conditionally:**
```typescript
{selectedPatientId && token && (
  <RecommendationPanel patientId={selectedPatientId} token={token} />
)}
```

4. **Example: PatientsPage integration:**
```typescript
// Make table rows clickable
<tr 
  onClick={() => setSelectedPatientId(patient.id)}
  style={{ cursor: 'pointer' }}
  className={selectedPatientId === patient.id ? 'selected-row' : ''}
>
  {/* Patient data */}
</tr>

// Show recommendations panel below table
{selectedPatientId && token && (
  <RecommendationPanel patientId={selectedPatientId} token={token} />
)}
```

### Database Requirements

No additional database migrations required. The recommendation system uses existing patient, appointment, and prescription data.

### Environment Variables

No new environment variables needed. Uses existing:
- `REACT_APP_API_URL`: Backend API endpoint
- JWT authentication (automatic via AuthContext)

## Usage Examples

### Backend: Getting Recommendations

```python
from app.services.recommendation_service import RecommendationService

service = RecommendationService(db=session)
recommendations = service.get_patient_care_recommendations(
    patient_id=123,
    tenant_id=1
)

for rec in recommendations:
    print(f"{rec.priority}: {rec.title}")
    print(f"  {rec.description}")
    print(f"  Action: {rec.suggested_action}")
```

### Frontend: Using the Component

```typescript
import RecommendationPanel from '../components/RecommendationPanel';

function PatientDetail({ patient, token }) {
  return (
    <div>
      {/* Patient information */}
      <RecommendationPanel 
        patientId={patient.id} 
        token={token} 
      />
    </div>
  );
}
```

### API: Fetching Recommendations

```bash
curl -X GET \
  'http://localhost:8000/api/v1/recommendations/123' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Response:**
```json
{
  "recommendations": [
    {
      "recommendation_id": "rec_123_appt_20250603",
      "patient_id": 123,
      "recommendation_type": "appointment_scheduling",
      "priority": "high",
      "title": "Schedule Follow-up Appointment",
      "description": "Patient overdue for routine check-up (95 days since last visit)",
      "suggested_action": "Schedule appointment within next 7 days",
      "due_date": "2025-06-10T00:00:00Z",
      "created_at": "2025-06-03T10:30:00Z"
    }
  ],
  "total": 1
}
```

## Testing

### Unit Tests

Located in `tests/test_recommendations.py` (258 lines, 13 tests):

```bash
# Run recommendation tests
pytest tests/test_recommendations.py -v

# Run with coverage
pytest tests/test_recommendations.py --cov=app.services.recommendation_service --cov=app.routers.recommendations
```

**Test Coverage:**
- ✅ Appointment recommendations (overdue patients)
- ✅ Preventive care suggestions
- ✅ Medication review flagging
- ✅ Follow-up care recommendations
- ✅ Priority scoring algorithm
- ✅ Empty state handling (no data)
- ✅ Tenant isolation
- ✅ RBAC enforcement
- ✅ API endpoints (GET, POST)

### Integration Testing

```bash
# Start backend
uvicorn app.main:app --reload

# Start frontend
cd frontend && npm start

# Test flow:
1. Login as doctor/nurse
2. Navigate to Patients page
3. Click on a patient
4. Verify recommendations appear below
5. Click "Mark Complete" on a recommendation
6. Verify recommendation updates/disappears
```

### Manual API Testing

```bash
# Get recommendations
curl -X GET \
  'http://localhost:8000/api/v1/recommendations/1' \
  -H 'Authorization: Bearer TOKEN'

# Acknowledge recommendation
curl -X POST \
  'http://localhost:8000/api/v1/recommendations/rec_1_appt_20250603/acknowledge' \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "acknowledged_by_user_id": 2,
    "notes": "Appointment scheduled for next week"
  }'
```

## Performance Considerations

### Caching Strategy

**Recommended caching pattern** (to be implemented):

```python
# Cache key: recommendations:patient:{patient_id}:{tenant_id}
# TTL: 300 seconds (5 minutes)

@cache_result(key_prefix="recommendations:patient", ttl=300)
def get_patient_care_recommendations(patient_id, tenant_id):
    # ... recommendation logic
    pass
```

**Cache invalidation triggers:**
- New appointment created
- Patient data updated
- Prescription modified
- Manual refresh requested

### Query Optimization

Current queries are optimized with:
- Indexed joins on `patient_id` and `tenant_id`
- Date range filters to limit result sets
- Pagination support (not yet exposed in API)

**Potential improvements:**
- Batch recommendation generation for multiple patients
- Materialized views for frequent queries
- Redis caching for hot recommendations

### Frontend Performance

- Debounced search (500ms) to reduce API calls
- React.memo() for expensive components (future optimization)
- Lazy loading for large patient lists
- Pagination (20 results per page)

## Security & Compliance

### Data Protection

- **PHI Encryption**: Recommendations do not expose raw PHI; uses encrypted patient references
- **Audit Logging**: All recommendation access logged with:
  - User ID
  - Patient ID
  - Timestamp
  - Action (view/acknowledge)
  - Correlation ID for tracing
- **Tenant Isolation**: Strict filtering by `tenant_id` from JWT token

### RBAC

Recommendation endpoints require:
- **Roles**: Doctor or Nurse (NOT Receptionist or Patient)
- **Justification**: Clinical recommendations contain medical insights

### Rate Limiting

- **Read operations**: 100 requests/minute (GET recommendations)
- **Write operations**: 20 requests/minute (POST acknowledge)
- **Protection**: Prevents abuse and ensures fair resource allocation

### Audit Trail

All recommendation operations logged:

```python
log_audit_event(
    action="RECOMMENDATIONS_VIEWED",
    resource_type="recommendations",
    resource_id=patient_id,
    details={
        "patient_id": patient_id,
        "recommendation_count": len(recommendations)
    },
    user_id=current_user.id,
    request=request
)
```

## Troubleshooting

### No Recommendations Showing

**Possible causes:**
1. Patient has no appointment history
2. Patient has recent appointments (no overdue visits)
3. Insufficient medical data
4. Tenant isolation issue

**Debug steps:**
```python
# Check patient data
patient = db.query(Patient).filter_by(id=patient_id).first()
print(f"Patient exists: {patient is not None}")

# Check appointments
appointments = db.query(Appointment).filter_by(patient_id=patient_id).all()
print(f"Appointment count: {len(appointments)}")

# Check tenant_id match
print(f"Patient tenant: {patient.tenant_id}")
print(f"User tenant: {current_user.tenant_id}")
```

### Recommendations Not Updating

**Possible causes:**
1. Caching (if implemented)
2. Frontend not refetching
3. Background calculation pending

**Solutions:**
- Click manual refresh button in UI
- Clear browser cache
- Restart backend service
- Check Redis cache (if enabled)

### Permission Denied

**Cause**: User role is Receptionist or Patient

**Solution**: Log in with Doctor or Nurse account

### Slow Performance

**Possible causes:**
1. Large number of patients
2. Complex appointment history
3. Missing database indexes

**Optimization:**
```sql
-- Add indexes if missing
CREATE INDEX idx_appointments_patient_tenant 
ON appointments(patient_id, tenant_id, appointment_date);

CREATE INDEX idx_prescriptions_patient_tenant 
ON prescriptions(patient_id, tenant_id, created_at);
```

## Future Enhancements

### Phase 2 Features

1. **Machine Learning Integration**
   - Predictive analytics for no-show risk
   - Personalized care recommendations based on patient history
   - Anomaly detection for unusual patterns

2. **Real-Time Notifications**
   - WebSocket push for urgent recommendations
   - Email/SMS alerts for high-priority items
   - In-app notification center

3. **Advanced Analytics**
   - Recommendation effectiveness metrics
   - Provider adherence tracking
   - Patient outcome correlation

4. **Bulk Operations**
   - Generate recommendations for all patients
   - Batch acknowledge/dismiss
   - Export recommendations to CSV/PDF

5. **Customization**
   - Configurable priority thresholds
   - Tenant-specific recommendation rules
   - Custom recommendation types

### Integration Opportunities

- **FHIR R4**: Export recommendations as CarePlan resources
- **MSSanté**: Send recommendations via secure messaging
- **DMP Integration**: Share recommendations with patient portal
- **Calendar Integration**: Auto-schedule appointments from recommendations

## Related Documentation

- [API Reference](API_REFERENCE.md) - Complete API endpoint documentation
- [Service Layer Pattern](patterns/new_resource_scaffold.md) - Service architecture
- [Caching Strategy](patterns/cache_keys.md) - Cache key conventions
- [Security Best Practices](SECURITY_BEST_PRACTICES.md) - Security guidelines
- [Testing Guide](TESTING_GUIDE.md) - Testing strategies

## Support

For issues or questions:
- GitHub Issues: [keneyapp/issues](https://github.com/keneyapp/keneyapp/issues)
- Documentation: [docs/](.)
- Copilot Instructions: [.github/copilot-instructions.md](../.github/copilot-instructions.md)

---

**Version**: 3.1.0  
**Last Updated**: June 3, 2025  
**Author**: KeneyApp Development Team
