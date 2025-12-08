# Performance Optimization Guide

## Overview

This guide provides performance optimization strategies for KeneyApp, focusing on database queries, caching, API response times, and resource utilization.

## Database Optimization

### 1. Query Optimization

**Current Issues:**
- Some queries load entire objects when only IDs are needed
- N+1 queries in relationships
- Missing indexes on frequently queried columns

**Recommendations:**

```python
# ❌ Bad: Loading full objects
patients = db.query(Patient).filter(Patient.tenant_id == tenant_id).all()
patient_ids = [p.id for p in patients]

# ✅ Good: Load only needed columns
from sqlalchemy import select
patient_ids = db.execute(
    select(Patient.id).where(Patient.tenant_id == tenant_id)
).scalars().all()

# ❌ Bad: N+1 query problem
patients = db.query(Patient).all()
for patient in patients:
    appointments = patient.appointments  # Triggers separate query each time

# ✅ Good: Eager loading with joinedload
from sqlalchemy.orm import joinedload
patients = db.query(Patient).options(
    joinedload(Patient.appointments)
).all()
```

### 2. Database Indexes

**Add missing indexes:**

```sql
-- Frequently queried columns
CREATE INDEX idx_patient_email ON patients(email);
CREATE INDEX idx_patient_phone ON patients(phone_number);
CREATE INDEX idx_appointment_date ON appointments(appointment_date);
CREATE INDEX idx_appointment_status ON appointments(status);
CREATE INDEX idx_message_receiver ON messages(receiver_id);
CREATE INDEX idx_message_status ON messages(status);

-- Composite indexes for common queries
CREATE INDEX idx_patient_tenant_active ON patients(tenant_id, is_deleted) 
WHERE is_deleted = false;
CREATE INDEX idx_appointment_tenant_date ON appointments(tenant_id, appointment_date);
```

### 3. Connection Pooling

**Current configuration:**
```python
# app/core/config.py
DB_POOL_SIZE: int = 10
DB_MAX_OVERFLOW: int = 10
DB_POOL_TIMEOUT: int = 30
DB_POOL_RECYCLE: int = 1800
```

**Optimization for production:**
```python
# For high-traffic production environments
DB_POOL_SIZE: int = 20  # Increase base pool
DB_MAX_OVERFLOW: int = 30  # Allow more overflow
DB_POOL_PRE_PING: bool = True  # Check connections before use
DB_POOL_RECYCLE: int = 3600  # Recycle connections hourly
```

## Caching Strategy

### 1. Multi-Level Caching

**Current implementation:**
- Memory cache (LRU) for hot data
- Redis cache for distributed access
- TTL-based invalidation

**Optimization patterns:**

```python
from app.services.cache_service import CacheService

cache_service = CacheService()

# 1. Cache with specific TTL
@cache_service.cached(ttl=300, prefix="patient")
async def get_patient_expensive(patient_id: int):
    # Expensive operation
    return result

# 2. Cache with smart invalidation
async def update_patient(patient_id: int, data: dict):
    # Update database
    updated = await db_update(patient_id, data)
    
    # Invalidate related caches
    await cache_service.delete_pattern(f"patient:{patient_id}:*")
    await cache_service.delete_pattern(f"dashboard:*")
    
    return updated

# 3. Batch cache operations
patient_ids = [1, 2, 3, 4, 5]
cache_keys = [f"patient:detail:{id}" for id in patient_ids]
cached_data = await cache_service.get_many(cache_keys)
```

### 2. Cache Warming

**Implement cache warming for frequently accessed data:**

```python
# app/tasks.py
from app.core.celery_app import celery_app

@celery_app.task
def warm_dashboard_cache():
    """Warm up dashboard cache for all tenants."""
    for tenant in get_all_tenants():
        # Pre-compute and cache dashboard stats
        stats = compute_dashboard_stats(tenant.id)
        cache_set(f"dashboard:stats:{tenant.id}", stats, ttl=300)

# Schedule in celerybeat_schedule
celery_beat_schedule = {
    'warm-dashboard-cache': {
        'task': 'app.tasks.warm_dashboard_cache',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

### 3. Cache Compression

**For large cached objects:**

```python
import gzip
import json

def cache_set_compressed(key: str, value: any, ttl: int):
    """Cache with compression for large objects."""
    json_data = json.dumps(value).encode('utf-8')
    compressed = gzip.compress(json_data)
    redis_client.setex(key, ttl, compressed)

def cache_get_compressed(key: str):
    """Retrieve and decompress cached data."""
    compressed = redis_client.get(key)
    if compressed:
        json_data = gzip.decompress(compressed)
        return json.loads(json_data)
    return None
```

## API Response Optimization

### 1. Response Pagination

**Standard pagination pattern:**

```python
from app.schemas.common import PaginatedResponse

@router.get("/patients", response_model=PaginatedResponse[PatientResponse])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # Efficient query with pagination
    total = db.query(Patient).count()
    patients = db.query(Patient).offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        items=patients,
        total=total,
        skip=skip,
        limit=limit
    )
```

### 2. Field Selection

**Allow clients to request only needed fields:**

```python
@router.get("/patients/{patient_id}")
async def get_patient(
    patient_id: int,
    fields: Optional[str] = Query(None, description="Comma-separated fields"),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    if fields:
        # Return only requested fields
        requested_fields = fields.split(",")
        return {k: getattr(patient, k) for k in requested_fields}
    
    return patient
```

### 3. Response Compression

**Enable gzip compression:**

```python
# app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Background Task Optimization

### 1. Celery Task Prioritization

```python
# app/tasks.py
@celery_app.task(priority=9)  # High priority (0-9, 9 is highest)
def send_urgent_notification(user_id: int, message: str):
    # Critical notification
    pass

@celery_app.task(priority=5)  # Medium priority
def generate_report(patient_id: int):
    # Regular task
    pass

@celery_app.task(priority=1)  # Low priority
def cleanup_old_files():
    # Background maintenance
    pass
```

### 2. Task Batching

```python
@celery_app.task
def send_appointment_reminders(appointment_ids: list[int]):
    """Batch process appointment reminders."""
    # Process in chunks to avoid memory issues
    chunk_size = 100
    for i in range(0, len(appointment_ids), chunk_size):
        chunk = appointment_ids[i:i+chunk_size]
        appointments = db.query(Appointment).filter(
            Appointment.id.in_(chunk)
        ).all()
        
        for appointment in appointments:
            send_reminder(appointment)
```

### 3. Task Result Optimization

```python
# Don't store results for tasks that don't need them
@celery_app.task(ignore_result=True)
def log_audit_event(event_data: dict):
    # Fire and forget task
    save_audit_log(event_data)
```

## File Upload Optimization

### 1. Chunked Upload for Large Files

```python
from fastapi import UploadFile
import aiofiles

@router.post("/documents/upload-chunked")
async def upload_file_chunked(
    file: UploadFile,
    chunk_size: int = 1024 * 1024  # 1MB chunks
):
    file_path = f"uploads/{file.filename}"
    
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(chunk_size):
            await f.write(chunk)
    
    return {"filename": file.filename, "size": file.size}
```

### 2. Direct S3 Upload (Future Implementation)

```python
# For production with S3/MinIO
import boto3

def generate_presigned_upload_url(filename: str, content_type: str):
    """Generate presigned URL for direct S3 upload."""
    s3_client = boto3.client('s3')
    return s3_client.generate_presigned_post(
        Bucket='keneyapp-documents',
        Key=filename,
        Fields={'Content-Type': content_type},
        Conditions=[
            {'Content-Type': content_type},
            ['content-length-range', 0, 10485760]  # Max 10MB
        ],
        ExpiresIn=3600
    )
```

## WebSocket Optimization

### 1. Connection Pooling

```python
# app/core/websocket.py
class ConnectionManager:
    def __init__(self, max_connections_per_user: int = 5):
        self.active_connections: dict[int, list[WebSocket]] = {}
        self.max_connections = max_connections_per_user
    
    async def connect(self, websocket: WebSocket, user_id: int):
        # Limit connections per user
        if user_id in self.active_connections:
            if len(self.active_connections[user_id]) >= self.max_connections:
                await websocket.close(code=1008, reason="Too many connections")
                return False
        
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)
        return True
```

### 2. Message Batching

```python
import asyncio

class MessageBatcher:
    def __init__(self, batch_size: int = 10, delay: float = 0.1):
        self.batch_size = batch_size
        self.delay = delay
        self.queue: list = []
    
    async def add_message(self, message: dict):
        self.queue.append(message)
        
        if len(self.queue) >= self.batch_size:
            await self.flush()
    
    async def flush(self):
        if self.queue:
            messages = self.queue[:]
            self.queue.clear()
            await self.send_batch(messages)
```

## Monitoring & Profiling

### 1. Query Performance Monitoring

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop()
    if total > 1.0:  # Log slow queries
        logger.warning(f"Slow query ({total:.2f}s): {statement}")
```

### 2. Endpoint Performance Monitoring

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow endpoints
    if process_time > 2.0:
        logger.warning(
            f"Slow endpoint: {request.method} {request.url.path} "
            f"took {process_time:.2f}s"
        )
    
    return response
```

### 3. Memory Profiling

```python
# Install: pip install memory-profiler
from memory_profiler import profile

@profile
def memory_intensive_function():
    large_list = [i for i in range(1000000)]
    return len(large_list)
```

## Load Testing

### 1. Locust Test Configuration

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class KeneyAppUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def list_patients(self):
        self.client.get("/api/v1/patients", headers=self.headers)
    
    @task(2)
    def get_dashboard(self):
        self.client.get("/api/v1/dashboard/stats", headers=self.headers)
    
    @task(1)
    def create_appointment(self):
        self.client.post("/api/v1/appointments", json={
            "patient_id": 1,
            "appointment_date": "2025-12-15T10:00:00",
            "reason": "Check-up"
        }, headers=self.headers)
```

**Run load test:**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Performance Benchmarks

### Target Metrics

| Endpoint | Target Response Time | Current | Status |
|----------|---------------------|---------|--------|
| GET /patients | < 200ms | TBD | 🔄 |
| GET /patients/{id} | < 100ms | TBD | 🔄 |
| POST /patients | < 300ms | TBD | 🔄 |
| GET /dashboard/stats | < 500ms | TBD | 🔄 |
| GET /appointments | < 200ms | TBD | 🔄 |
| WebSocket message | < 50ms | TBD | 🔄 |

### Resource Utilization Targets

- **CPU**: < 70% average, < 90% peak
- **Memory**: < 2GB per worker
- **Database Connections**: < 80% of pool size
- **Redis Memory**: < 1GB
- **Response Time P95**: < 1s
- **Response Time P99**: < 2s

## Next Steps

1. **Baseline Measurement**: Run load tests to establish current performance
2. **Identify Bottlenecks**: Use profiling tools to find slow paths
3. **Implement Optimizations**: Apply optimizations from this guide
4. **Measure Improvements**: Re-run load tests to validate changes
5. **Monitor Production**: Set up alerts for performance degradation

## References

- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/faq/performance.html)
- [Redis Best Practices](https://redis.io/topics/optimization)
- [Celery Optimization](https://docs.celeryproject.org/en/stable/userguide/optimizing.html)
