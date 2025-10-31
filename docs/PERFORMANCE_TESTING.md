# Performance Testing Guide

This guide provides comprehensive procedures for performance testing, benchmarking, and optimization of the KeneyApp platform.

## Table of Contents

1. [Performance Requirements](#performance-requirements)
2. [Testing Tools](#testing-tools)
3. [Load Testing](#load-testing)
4. [Stress Testing](#stress-testing)
5. [Database Performance](#database-performance)
6. [API Performance](#api-performance)
7. [Frontend Performance](#frontend-performance)
8. [Optimization Strategies](#optimization-strategies)

---

## Performance Requirements

### Service Level Objectives (SLOs)

#### Response Time
- **API Endpoints**:
  - p50 (median): < 100ms
  - p95: < 200ms
  - p99: < 500ms
  - p99.9: < 1000ms

- **Database Queries**:
  - Simple queries: < 10ms
  - Complex queries: < 100ms
  - Reports: < 5 seconds

- **Page Load**:
  - Initial load: < 2 seconds
  - Time to interactive: < 3 seconds

#### Throughput
- **Concurrent Users**: Support 1000+ concurrent users
- **Requests per Second**: 500+ RPS sustained
- **Peak Load**: 1000 RPS for 5 minutes

#### Availability
- **Uptime**: 99.9% (< 43 minutes downtime/month)
- **Mean Time Between Failures (MTBF)**: > 720 hours (30 days)
- **Mean Time To Recovery (MTTR)**: < 30 minutes

#### Resource Utilization
- **CPU**: < 70% average, < 90% peak
- **Memory**: < 75% average, < 85% peak
- **Database Connections**: < 80% of pool
- **Disk I/O**: < 80% capacity

---

## Testing Tools

### Load Testing Tools

#### Apache JMeter
```bash
# Install JMeter
wget https://downloads.apache.org/jmeter/binaries/apache-jmeter-5.6.3.tgz
tar -xzf apache-jmeter-5.6.3.tgz

# Run test
./apache-jmeter-5.6.3/bin/jmeter -n -t test-plan.jmx -l results.jtl
```

#### Locust (Recommended for Python apps)
```python
# locustfile.py
from locust import HttpUser, task, between

class KeneyAppUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def view_patients(self):
        self.client.get(
            "/api/v1/patients",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(2)
    def view_appointments(self):
        self.client.get(
            "/api/v1/appointments",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def view_dashboard(self):
        self.client.get(
            "/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

```bash
# Run Locust
locust -f locustfile.py --host=https://api.keneyapp.com

# Or headless mode
locust -f locustfile.py --host=https://api.keneyapp.com \
    --users 100 --spawn-rate 10 --run-time 10m --headless
```

#### k6 (Modern load testing)
```javascript
// k6-script.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Steady state
    { duration: '2m', target: 200 }, // Spike
    { duration: '5m', target: 200 }, // Steady spike
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const loginRes = http.post('https://api.keneyapp.com/api/v1/auth/login', 
    JSON.stringify({
      username: 'testuser',
      password: 'testpass123',
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(loginRes, {
    'login successful': (r) => r.status === 200,
  });
  
  const token = loginRes.json('access_token');
  
  const patientsRes = http.get('https://api.keneyapp.com/api/v1/patients', {
    headers: { Authorization: `Bearer ${token}` },
  });
  
  check(patientsRes, {
    'patients retrieved': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  sleep(1);
}
```

```bash
# Run k6
k6 run k6-script.js
```

### Monitoring & Profiling

#### Python Profiling
```python
# Profile specific endpoint
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run code to profile
response = client.get("/api/v1/patients")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

#### Memory Profiling
```bash
# Install memory profiler
pip install memory-profiler

# Profile script
python -m memory_profiler app/routers/patients.py
```

#### Line Profiler
```bash
# Install line profiler
pip install line-profiler

# Add @profile decorator to functions
@profile
def get_patients(db: Session):
    return db.query(Patient).all()

# Run profiler
kernprof -l -v script.py
```

---

## Load Testing

### Basic Load Test

**Scenario**: Simulate normal business hours traffic

```bash
# Using Locust
locust -f locustfile.py \
    --host=https://api.keneyapp.com \
    --users 100 \
    --spawn-rate 5 \
    --run-time 30m \
    --headless \
    --html=report.html
```

**Expected Results**:
- Average response time: < 150ms
- 95th percentile: < 200ms
- 99th percentile: < 500ms
- Error rate: < 0.1%
- No memory leaks
- No connection pool exhaustion

### Sustained Load Test

**Scenario**: Continuous load for extended period

```bash
# 2-hour sustained load
locust -f locustfile.py \
    --host=https://api.keneyapp.com \
    --users 200 \
    --spawn-rate 10 \
    --run-time 2h \
    --headless
```

**Monitoring During Test**:
```bash
# Watch resource usage
watch -n 5 'kubectl top pods -n keneyapp'

# Watch database connections
watch -n 5 'kubectl exec -n keneyapp postgres-0 -- \
  psql -c "SELECT count(*) FROM pg_stat_activity;"'

# Watch Redis memory
watch -n 5 'kubectl exec -n keneyapp redis-0 -- \
  redis-cli INFO memory | grep used_memory_human'
```

---

## Stress Testing

### Spike Test

**Scenario**: Sudden traffic spike

```javascript
// k6 spike test
export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Normal load
    { duration: '30s', target: 500 }, // Spike!
    { duration: '2m', target: 500 },  // Sustained spike
    { duration: '1m', target: 50 },   // Back to normal
    { duration: '30s', target: 0 },   // Ramp down
  ],
};
```

**Pass Criteria**:
- System remains available during spike
- Response times return to normal after spike
- No errors during or after spike
- Auto-scaling triggers appropriately

### Breakpoint Test

**Scenario**: Find system limits

```bash
# Incrementally increase load until failure
locust -f locustfile.py \
    --host=https://api.keneyapp.com \
    --users 1000 \
    --spawn-rate 50 \
    --run-time 20m
```

**Document**:
- Maximum concurrent users supported
- Maximum requests per second
- Resource limits hit
- Failure modes observed

---

## Database Performance

### Query Performance Analysis

```sql
-- Enable query statistics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- More than 100ms average
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Check for missing indexes
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
    AND n_distinct > 100
    AND correlation < 0.5;

-- Check table bloat
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_dead_tup
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

### Connection Pool Tuning

```python
# In app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # Core connections
    max_overflow=40,       # Additional connections
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True,    # Verify connections before use
    echo_pool=False,       # Log pool events (debug only)
)
```

### Index Optimization

```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_patients_last_name 
    ON patients(last_name);

CREATE INDEX CONCURRENTLY idx_appointments_patient_date 
    ON appointments(patient_id, appointment_date);

CREATE INDEX CONCURRENTLY idx_audit_logs_timestamp 
    ON audit_logs(timestamp DESC);

-- Partial indexes for specific queries
CREATE INDEX CONCURRENTLY idx_active_users 
    ON users(username) 
    WHERE is_active = true;

-- Multi-column indexes
CREATE INDEX CONCURRENTLY idx_appointments_lookup 
    ON appointments(patient_id, doctor_id, appointment_date);
```

---

## API Performance

### Endpoint Benchmarking

```bash
# Using Apache Bench
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
    https://api.keneyapp.com/api/v1/patients

# Using wrk
wrk -t4 -c100 -d30s -H "Authorization: Bearer $TOKEN" \
    https://api.keneyapp.com/api/v1/patients

# Using hey
hey -n 10000 -c 100 -H "Authorization: Bearer $TOKEN" \
    https://api.keneyapp.com/api/v1/patients
```

### Response Time Optimization

#### Caching Strategy
```python
# In app/core/cache.py
import redis
from functools import wraps
import json

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_response(ttl=300):
    """Cache response with TTL in seconds."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{json.dumps(kwargs)}"
            
            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator

# Usage
@cache_response(ttl=300)  # Cache for 5 minutes
async def get_dashboard_stats(db: Session):
    # Expensive query
    return calculate_stats(db)
```

#### Database Query Optimization
```python
# Use eager loading to avoid N+1 queries
from sqlalchemy.orm import joinedload

# Bad: N+1 query problem
patients = db.query(Patient).all()
for patient in patients:
    print(patient.appointments)  # Triggers new query each time

# Good: Eager loading
patients = db.query(Patient).options(
    joinedload(Patient.appointments)
).all()
for patient in patients:
    print(patient.appointments)  # Already loaded

# Selective loading
from sqlalchemy.orm import selectinload, subqueryload

patients = db.query(Patient).options(
    selectinload(Patient.appointments),
    subqueryload(Patient.prescriptions)
).all()
```

#### Pagination
```python
# Always use pagination for list endpoints
from fastapi import Query

@router.get("/patients")
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    patients = db.query(Patient).offset(skip).limit(limit).all()
    total = db.query(Patient).count()
    
    return {
        "items": patients,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

---

## Frontend Performance

### Performance Metrics

```javascript
// Measure Core Web Vitals
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);  // Cumulative Layout Shift
getFID(console.log);  // First Input Delay
getFCP(console.log);  // First Contentful Paint
getLCP(console.log);  // Largest Contentful Paint
getTTFB(console.log); // Time to First Byte
```

### Optimization Techniques

#### Code Splitting
```javascript
// React lazy loading
import React, { lazy, Suspense } from 'react';

const PatientsPage = lazy(() => import('./pages/PatientsPage'));
const AppointmentsPage = lazy(() => import('./pages/AppointmentsPage'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/patients" element={<PatientsPage />} />
        <Route path="/appointments" element={<AppointmentsPage />} />
      </Routes>
    </Suspense>
  );
}
```

#### Memoization
```javascript
// React memo for expensive components
import { memo, useMemo, useCallback } from 'react';

const PatientList = memo(({ patients, onSelect }) => {
  return (
    <div>
      {patients.map(patient => (
        <PatientCard key={patient.id} patient={patient} onSelect={onSelect} />
      ))}
    </div>
  );
});

// useMemo for expensive calculations
function Dashboard({ data }) {
  const statistics = useMemo(() => {
    return calculateExpensiveStats(data);
  }, [data]);
  
  return <StatsDisplay stats={statistics} />;
}

// useCallback for stable function references
function PatientSearch({ onSearch }) {
  const handleSearch = useCallback((query) => {
    onSearch(query);
  }, [onSearch]);
  
  return <SearchBox onSearch={handleSearch} />;
}
```

#### Asset Optimization
```bash
# Optimize images
npm install imagemin imagemin-webp --save-dev

# In build script
import imagemin from 'imagemin';
import imageminWebp from 'imagemin-webp';

await imagemin(['images/*.{jpg,png}'], {
  destination: 'build/images',
  plugins: [imageminWebp({ quality: 80 })]
});
```

---

## Optimization Strategies

### Backend Optimization

#### 1. Database Connection Pooling
```python
# Optimal pool configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

#### 2. Async Operations
```python
# Use async where possible
from fastapi import BackgroundTasks

@router.post("/patients/{patient_id}/report")
async def generate_report(
    patient_id: int,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(generate_patient_report, patient_id)
    return {"message": "Report generation started"}
```

#### 3. Batch Operations
```python
# Batch database inserts
from sqlalchemy import insert

patients_data = [...]  # List of patient dicts
stmt = insert(Patient).values(patients_data)
db.execute(stmt)
db.commit()
```

#### 4. Response Compression
```python
# Enable gzip compression
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Database Optimization

#### 1. Proper Indexing
- Index foreign keys
- Index frequently queried columns
- Use partial indexes for filtered queries
- Avoid over-indexing (impacts writes)

#### 2. Query Optimization
- Use EXPLAIN ANALYZE
- Avoid SELECT *
- Use appropriate JOIN types
- Limit result sets
- Use covering indexes

#### 3. Materialized Views
```sql
-- Create materialized view for expensive aggregations
CREATE MATERIALIZED VIEW dashboard_stats AS
SELECT 
    COUNT(*) as total_patients,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as new_patients,
    COUNT(DISTINCT doctor_id) as total_doctors
FROM patients;

-- Refresh periodically
REFRESH MATERIALIZED VIEW dashboard_stats;

-- Create index on materialized view
CREATE INDEX ON dashboard_stats(total_patients);
```

### Caching Strategy

#### Multi-Level Caching
```
1. Application Level (in-memory)
   - Function results
   - Configuration
   
2. Redis (distributed cache)
   - Session data
   - API responses
   - Database query results
   
3. CDN (edge caching)
   - Static assets
   - API responses (where appropriate)
```

### Monitoring Performance

```python
# Add performance monitoring
from prometheus_client import Histogram
import time

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint', 'status']
)

@app.middleware("http")
async def monitor_performance(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).observe(duration)
    
    return response
```

---

## Performance Testing Schedule

### Weekly
- [ ] Basic load test (30 minutes, normal load)
- [ ] Review key metrics (response times, error rates)
- [ ] Check for performance degradation

### Monthly
- [ ] Comprehensive load test (2 hours)
- [ ] Stress test to find limits
- [ ] Database performance audit
- [ ] Review and optimize slow queries

### Quarterly
- [ ] Full system performance audit
- [ ] Breakpoint testing
- [ ] Capacity planning review
- [ ] Infrastructure optimization

### Annually
- [ ] Comprehensive performance review
- [ ] Architecture optimization
- [ ] Scalability planning
- [ ] Performance goals reassessment

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Next Review**: 2024-04-15  
**Owner**: DevOps & Engineering Teams
