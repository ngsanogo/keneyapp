# WebSocket Real-Time Notifications

## Overview

KeneyApp provides real-time notifications via WebSocket connections for patient updates, appointments, and other events. This enables instant UI updates without polling.

## Connection

### Endpoint

```
ws://localhost:8000/ws?token=YOUR_JWT_TOKEN
```

Production:
```
wss://your-domain.com/ws?token=YOUR_JWT_TOKEN
```

### Authentication

WebSocket connections require JWT authentication via query parameter:

```javascript
const token = localStorage.getItem('token');
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
```

## Message Format

All messages are JSON-formatted:

```json
{
  "type": "event_type",
  "data": { ... }
}
```

## Event Types

### Connection Events

#### Connected

Sent immediately after successful connection:

```json
{
  "type": "connected",
  "message": "Successfully connected to real-time notifications"
}
```

### Patient Events

#### Patient Created

Broadcast when new patient is created:

```json
{
  "type": "patient_created",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    "last_name": "Doe",
    "tenant_id": "tenant-123"
  }
}
```

#### Patient Updated

Broadcast when patient is updated:

```json
{
  "type": "patient_updated",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+9999999999",
    "updated_at": "2024-01-15T10:35:00Z"
  }
}
```

#### Patient Deleted

Broadcast when patient is deleted:

```json
{
  "type": "patient_deleted",
  "data": {
    "patient_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Appointment Events

#### Appointment Created

```json
{
  "type": "appointment_created",
  "data": {
    "id": "appt-123",
    "patient_id": "patient-456",
    "datetime": "2024-01-20T14:00:00Z",
    "type": "consultation"
  }
}
```

## Client Implementation

### JavaScript/TypeScript

```typescript
class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  connect(token: string) {
    this.ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.reconnect(token);
    };
  }
  
  handleMessage(message: any) {
    switch (message.type) {
      case 'connected':
        console.log('Connection established');
        break;
      
      case 'patient_created':
        console.log('New patient:', message.data);
        // Update UI - add patient to list
        break;
      
      case 'patient_updated':
        console.log('Patient updated:', message.data);
        // Update UI - refresh patient details
        break;
      
      case 'patient_deleted':
        console.log('Patient deleted:', message.data.patient_id);
        // Update UI - remove patient from list
        break;
      
      case 'appointment_created':
        console.log('New appointment:', message.data);
        // Update UI - add to calendar
        break;
      
      default:
        console.log('Unknown message type:', message.type);
    }
  }
  
  startHeartbeat() {
    setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000); // Ping every 30 seconds
  }
  
  reconnect(token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(token), delay);
    }
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Usage
const wsClient = new WebSocketClient();
const token = localStorage.getItem('token');
wsClient.connect(token);
```

### React Hook

```typescript
import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  data?: any;
  message?: string;
}

export const useWebSocket = (token: string | null) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    if (!token) return;
    
    const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
    wsRef.current = ws;
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket closed');
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    // Heartbeat
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000);
    
    return () => {
      clearInterval(heartbeat);
      ws.close();
    };
  }, [token]);
  
  return { isConnected, lastMessage };
};

// Usage in component
function PatientsPage() {
  const token = localStorage.getItem('token');
  const { isConnected, lastMessage } = useWebSocket(token);
  
  useEffect(() => {
    if (lastMessage?.type === 'patient_created') {
      // Refresh patient list or add to state
      console.log('New patient:', lastMessage.data);
    }
  }, [lastMessage]);
  
  return (
    <div>
      <div className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? '🟢 Live' : '🔴 Offline'}
      </div>
      {/* Rest of component */}
    </div>
  );
}
```

### Python Client

```python
import asyncio
import websockets
import json

async def connect_websocket(token: str):
    uri = f"ws://localhost:8000/ws?token={token}"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Send heartbeat every 30 seconds
        async def heartbeat():
            while True:
                await asyncio.sleep(30)
                await websocket.send("ping")
        
        # Start heartbeat task
        asyncio.create_task(heartbeat())
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data['type']}")
            
            if data['type'] == 'patient_created':
                print(f"New patient: {data['data']}")
            elif data['type'] == 'patient_updated':
                print(f"Updated patient: {data['data']}")
            elif data['type'] == 'patient_deleted':
                print(f"Deleted patient: {data['data']['patient_id']}")

# Run client
token = "your-jwt-token"
asyncio.run(connect_websocket(token))
```

## Tenant Isolation

WebSocket notifications are tenant-scoped:

- Users only receive events from their tenant
- Super Admin receives all events
- Events include `tenant_id` for filtering

## Error Handling

### Connection Errors

#### Missing Token

```
Close Code: 1008 (Policy Violation)
Reason: "Missing authentication token"
```

#### Invalid Token

```
Close Code: 1008 (Policy Violation)
Reason: "Authentication failed"
```

### Reconnection Strategy

Implement exponential backoff:

```typescript
const reconnect = (attempt: number) => {
  const delay = Math.min(1000 * 2 ** attempt, 30000);
  setTimeout(() => connect(), delay);
};
```

## Heartbeat/Keepalive

Send ping every 30 seconds to maintain connection:

```javascript
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);
```

Server responds with `"pong"` message.

## Best Practices

### Connection Management

1. **Connect on login**: Establish WebSocket after successful authentication
2. **Disconnect on logout**: Close WebSocket when user logs out
3. **Reconnect on drop**: Implement exponential backoff reconnection
4. **Single connection**: Reuse connection across components

### Performance

1. **Debounce UI updates**: Batch rapid updates (e.g., bulk operations)
2. **Selective subscriptions**: Filter events by type if needed
3. **Lazy connection**: Connect only when needed (e.g., after user action)

### Security

1. **Use WSS**: Always use secure WebSocket (wss://) in production
2. **Validate messages**: Check message structure before processing
3. **Token refresh**: Reconnect with new token when JWT expires
4. **Rate limiting**: Backend enforces connection limits per tenant

## Integration with React Query

Combine WebSocket with React Query for optimal caching:

```typescript
import { useQueryClient } from 'react-query';

function useRealtimePatients() {
  const queryClient = useQueryClient();
  const token = localStorage.getItem('token');
  const { lastMessage } = useWebSocket(token);
  
  useEffect(() => {
    if (!lastMessage) return;
    
    switch (lastMessage.type) {
      case 'patient_created':
      case 'patient_updated':
      case 'patient_deleted':
        // Invalidate patient queries to trigger refetch
        queryClient.invalidateQueries(['patients']);
        break;
    }
  }, [lastMessage, queryClient]);
}
```

## Monitoring

Track WebSocket connections via metrics:

```
websocket_connections_total{tenant_id="tenant-123"} 5
websocket_messages_sent_total{type="patient_created"} 142
websocket_messages_received_total 1024
```

## Testing

### Manual Testing

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c "ws://localhost:8000/ws?token=YOUR_TOKEN"

# Send ping
> ping

# Receive messages
< {"type":"connected","message":"Successfully connected..."}
< pong
< {"type":"patient_created","data":{...}}
```

### Automated Testing

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket_authentication(client):
    """Test WebSocket requires authentication."""
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        # Should close with 1008

def test_websocket_patient_notifications(client, test_user_token):
    """Test patient event notifications."""
    with client.websocket_connect(f"/ws?token={test_user_token}") as websocket:
        # Receive connected message
        data = websocket.receive_json()
        assert data['type'] == 'connected'
        
        # Create patient in another thread/process
        # Should receive patient_created event
```

## Troubleshooting

### Connection Drops

1. Check token expiration
2. Verify network connectivity
3. Review server logs for errors
4. Increase heartbeat frequency

### Missing Events

1. Verify tenant_id matches
2. Check WebSocket is connected
3. Review event broadcasting logic
4. Check server-side filtering

### Performance Issues

1. Reduce message payload size
2. Implement client-side debouncing
3. Limit concurrent connections
4. Use message compression

## Production Deployment

### Nginx Configuration

```nginx
location /ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 86400;
}
```

### Environment Variables

```bash
# Enable WebSocket
ENABLE_WEBSOCKET=true

# Connection limits
MAX_WEBSOCKET_CONNECTIONS_PER_TENANT=100
WEBSOCKET_HEARTBEAT_INTERVAL=30
```

## Support

For WebSocket issues:

1. Check browser console for connection errors
2. Review server logs: `logs/app.log`
3. Monitor metrics: `http://localhost:8000/metrics`
4. Test with wscat for debugging
