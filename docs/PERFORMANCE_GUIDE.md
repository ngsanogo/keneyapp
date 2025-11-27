# KeneyApp Performance Optimization Guide

## Overview

This guide provides comprehensive performance optimization strategies for KeneyApp, covering database, caching, API, and frontend optimizations.

## Database Optimizations

### 1. Indexing Strategy

All critical columns already have indexes:

- Primary keys (automatically indexed)
- Foreign keys (indexed for joins)
- Email fields (for lookups)
- Tenant IDs (for multi-tenancy filtering)

### 2. Query Optimization Tips

#### Use Select Specific Columns

```python
# Bad - Loads all columns
patients = db.query(Patient).all()

# Good - Select only needed columns
patients = db.query(Patient.id, Patient.first_name, Patient.last_name).all()
```

#### Eager Loading for Relationships

```python
from sqlalchemy.orm import joinedload

# Prevents N+1 queries
patients = db.query(Patient).options(
    joinedload(Patient.appointments),
    joinedload(Patient.prescriptions)
).all()
```

#### Use Pagination

```python
# Always paginate large result sets
def get_patients_paginated(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Patient).offset(skip).limit(limit).all()
```

### 3. Connection Pooling

SQLAlchemy connection pooling is already configured with tunable defaults exposed via environment variables to help right-size connections per deployment:

- `DB_POOL_SIZE` (default: 10) — baseline concurrent connections
- `DB_MAX_OVERFLOW` (default: 10) — burst connections allowed beyond the pool size
- `DB_POOL_TIMEOUT` (default: 30s) — how long to wait for a connection before failing
- `DB_POOL_RECYCLE` (default: 1800s) — proactively recycle connections to avoid stale sockets
- `DB_ECHO` (default: False) — enable SQL logging when troubleshooting

Monitor pool usage directly when tuning:

```python
# Check pool status
from app.core.database import engine
print(engine.pool.status())
```

### 4. Database Monitoring

Monitor slow queries:

```sql
-- PostgreSQL slow query log
ALTER DATABASE keneyapp SET log_min_duration_statement = 1000;  -- Log queries > 1s

-- View slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Caching Strategy

### 1. Redis Caching Layers

#### Dashboard Statistics (5 minutes)

```python
DASHBOARD_CACHE_KEY = "dashboard:stats"
DASHBOARD_CACHE_TTL = 300  # 5 minutes
```

The dashboard endpoint now aggregates counts in a single database round-trip per model and then caches the rendered payload for five minutes, which keeps read pressure low even under frequent refreshes.

#### Patient Lists (2 minutes)

```python
PATIENT_LIST_CACHE_PREFIX = "patients:list"
PATIENT_LIST_TTL = 120  # 2 minutes
```

#### Patient Details (5 minutes)

```python
PATIENT_DETAIL_CACHE_PREFIX = "patients:detail:{id}"
PATIENT_DETAIL_TTL = 300  # 5 minutes
```

### 2. Cache Invalidation Patterns

#### On Create/Update/Delete

```python
# Invalidate related caches
cache_clear_pattern("patients:*")
cache_clear_pattern("dashboard:*")
```

#### Time-based Expiration

Let cache naturally expire for frequently changing data.

### 3. Cache Monitoring

Monitor Redis performance:

```bash
# Redis stats
redis-cli INFO stats

# Monitor cache hit rate
redis-cli INFO stats | grep keyspace_hits
redis-cli INFO stats | grep keyspace_misses
```

## API Performance

### 1. Rate Limiting

Already implemented with slowapi:

```python
@limiter.limit("10/minute")  # Create operations
@limiter.limit("100/minute")  # Read operations
```

### 2. Response Compression

Enable gzip compression in production:

```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 3. Async Operations

Use Celery for long-running tasks:

```python
# Async report generation
task = generate_patient_report.delay(patient_id)
return {"task_id": task.id, "status": "processing"}
```

### 4. Pagination Best Practices

```python
# Always provide pagination
@router.get("/patients/")
def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return db.query(Patient).offset(skip).limit(limit).all()
```

## Frontend Optimizations

### 1. Code Splitting

```typescript
// Lazy load pages
const DashboardPage = React.lazy(() => import('./pages/DashboardPage'));

// Use with Suspense
<Suspense fallback={<LoadingSpinner fullScreen />}>
  <DashboardPage />
</Suspense>
```

### 2. Memoization

```typescript
// Memoize expensive computations
const memoizedValue = useMemo(() => {
  return expensiveComputation(data);
}, [data]);

// Memoize callbacks
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

### 3. Virtual Scrolling

For large lists, use virtual scrolling:

```bash
npm install react-window
```

```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={patients.length}
  itemSize={50}
>
  {renderPatientRow}
</FixedSizeList>
```

### 4. Image Optimization

- Use appropriate image formats (WebP, AVIF)
- Implement lazy loading
- Use srcset for responsive images
- Compress images before upload

### 5. Bundle Size Optimization

```bash
# Analyze bundle size
npm run build
npx source-map-explorer 'build/static/js/*.js'

# Tree-shake unused code
# Import only what you need
import { debounce } from 'lodash-es';  # Good
import _ from 'lodash';  # Bad - imports everything
```

## Monitoring & Profiling

### 1. Backend Profiling

```python
# Add profiling middleware for development
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... run code ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### 2. Prometheus Metrics

Monitor key metrics:

- Request duration: `http_request_duration_seconds`
- Request rate: `http_requests_total`
- Error rate: `http_requests_total{status="5xx"}`
- Database connections: `database_connections`
- Cache hit rate: Custom metric

### 3. Frontend Performance

```typescript
// Measure performance
import { onCLS, onFID, onFCP, onLCP, onTTFB } from 'web-vitals';

onCLS(console.log);
onFID(console.log);
onFCP(console.log);
onLCP(console.log);
onTTFB(console.log);
```

### 4. APM Tools

Consider integrating:

- Sentry for error tracking
- New Relic for full-stack monitoring
- DataDog for infrastructure monitoring

## Load Testing

### 1. Using Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class KeneyAppUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def view_dashboard(self):
        self.client.get("/api/v1/dashboard/stats")

    @task(3)
    def list_patients(self):
        self.client.get("/api/v1/patients/")
```

Run test:

```bash
locust -f locustfile.py --host=http://localhost:8000
```

### 2. Using Apache Bench

```bash
# Test endpoint performance
ab -n 1000 -c 10 http://localhost:8000/api/v1/patients/

# With authentication
ab -n 1000 -c 10 -H "Authorization: Bearer TOKEN" \
   http://localhost:8000/api/v1/dashboard/stats
```

## Production Optimization Checklist

### Backend

- [ ] Enable production mode (DEBUG=False)
- [ ] Use gunicorn with multiple workers
- [ ] Configure proper connection pool sizes
- [ ] Enable query result caching
- [ ] Set up database read replicas
- [ ] Configure Redis persistence
- [ ] Enable request compression
- [ ] Set up CDN for static files

### Frontend

- [ ] Build with production optimizations
- [ ] Enable code splitting
- [ ] Implement service workers for offline support
- [ ] Use lazy loading for images
- [ ] Minify and compress assets
- [ ] Enable HTTP/2
- [ ] Implement aggressive caching strategies
- [ ] Use CDN for asset delivery

### Infrastructure

- [ ] Enable auto-scaling (Kubernetes HPA)
- [ ] Set up load balancing
- [ ] Configure health checks
- [ ] Implement circuit breakers
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Implement backup strategies
- [ ] Set up disaster recovery

## Performance Targets

### API Response Times

- GET endpoints: < 100ms (95th percentile)
- POST endpoints: < 200ms (95th percentile)
- Complex queries: < 500ms (95th percentile)

### Frontend

- First Contentful Paint: < 1.5s
- Largest Contentful Paint: < 2.5s
- Time to Interactive: < 3.5s
- Cumulative Layout Shift: < 0.1

### Database

- Query response time: < 50ms (average)
- Connection pool utilization: < 80%
- Cache hit rate: > 85%

### System

- CPU utilization: < 70% (average)
- Memory utilization: < 80% (average)
- Error rate: < 0.1%
- Uptime: > 99.9%

## Troubleshooting

### Slow Database Queries

1. Check query execution plan: `EXPLAIN ANALYZE`
2. Verify indexes are being used
3. Consider adding composite indexes
4. Check for N+1 query problems

### Memory Issues

1. Check for memory leaks with profiling
2. Verify connection pools are closed
3. Monitor Redis memory usage
4. Review cache expiration policies

### High CPU Usage

1. Profile application code
2. Check for infinite loops
3. Review background task queue
4. Consider horizontal scaling

## Resources

- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Best Practices](https://redis.io/topics/optimization)
- [React Performance Optimization](https://react.dev/learn/render-and-commit#optimizing-performance)

## Conclusion

Performance optimization is an ongoing process. Regularly monitor metrics, profile bottlenecks, and implement improvements iteratively. Focus on the 20% of optimizations that will provide 80% of the benefits.
