# CareSync Platform - Deployment Guide

## Prerequisites

### System Requirements
- Python 3.8+
- SQLite 3.x (or PostgreSQL for production)
- Node.js 16+ (for frontend)
- 2GB RAM minimum
- 10GB disk space

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=sqlite:///./terminology.db

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production-use-openssl-rand-hex-32

# Jitsi Teleconsult
JITSI_DOMAIN=meet.jit.si
JITSI_APP_ID=caresync
JITSI_SECRET=your-jitsi-secret-key

# Razorpay Payments (use test keys for development)
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=rzp_test_your_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Feature Flags
ENABLE_TELECONSULT=true
ENABLE_PAYMENTS=true
ENABLE_CLAIMS=true

# Monitoring (optional)
SENTRY_DSN=your_sentry_dsn_if_using
```

## Installation Steps

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi, jwt, bcrypt; print('✓ Dependencies installed')"
```

### 2. Apply Database Migrations

```bash
# Apply all migrations in order
python migrations/apply_migration_006.py  # Users & Roles
python migrations/apply_migration_007.py  # Teleconsult & Payments
python migrations/apply_migration_008.py  # Mapping Feedback
python migrations/apply_migration_009.py  # Claims & Admin

# Verify migrations
python -c "from models.database import SessionLocal; print('✓ Database ready')"
```

### 3. Run Tests

```bash
# Run mapping protection tests
pytest tests/test_mapping_write_block.py -v

# Expected: 22/22 passing
```

### 4. Start the Application

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode (with workers)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Verify Deployment

```bash
# Health check
curl http://localhost:8000/api/health

# Metrics
curl http://localhost:8000/api/metrics

# API docs
open http://localhost:8000/docs
```

## Default Credentials

**Default Doctor Account:**
- Email: `doctor@caresync.local`
- Password: (Set during first login via `/api/auth/register`)
- Role: `doctor`

**First Admin Setup:**
1. Register first user via `/api/auth/register`
2. Manually update role to `admin` in database:
   ```sql
   UPDATE users SET role = 'admin' WHERE email = 'your-admin-email@example.com';
   ```

## API Endpoints Overview

### Authentication (`/api/auth/*`)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Current user

### Teleconsult (`/api/teleconsult/*`)
- `POST /api/teleconsult/create-room` - Create video room
- `POST /api/teleconsult/join-room` - Join room
- `POST /api/teleconsult/start-session` - Start session
- `POST /api/teleconsult/end-session` - End session

### Payments (`/api/payments/*`)
- `POST /api/payments/create` - Create payment intent
- `POST /api/payments/verify` - Verify payment
- `POST /api/payments/webhook` - Webhook handler
- `GET /api/payments/{id}` - Get payment status

### Mapping (`/api/mapping/*`)
- `GET /api/mapping/lookup?ayush_term=...` - Lookup term
- `GET /api/mapping/search?query=...` - Search terms
- `GET /api/mapping/stats` - Statistics
- `POST /api/mapping/encounters/{id}/accept` - Accept mappings
- `POST /api/mapping/feedback` - Submit feedback
- `POST /api/mapping/propose-update` - Propose update (Admin)

### Admin (`/api/admin/*`)
- `POST /api/admin/mapping/proposals/{id}/approve` - Approve proposal
- `POST /api/admin/mapping/proposals/{id}/reject` - Reject proposal
- `POST /api/admin/claims/generate` - Generate claim
- `GET /api/admin/claims` - List claims
- `GET /api/admin/config` - Get system config
- `PUT /api/admin/config` - Update config
- `GET /api/admin/audit-logs` - View audit logs

### Monitoring (`/api/*`)
- `GET /api/health` - Health check
- `GET /api/metrics` - Prometheus metrics
- `GET /api/ready` - Readiness probe
- `GET /api/live` - Liveness probe

## Production Deployment

### Using Docker (Recommended)

Create `Dockerfile` for Backend:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Create `Dockerfile` for Frontend:

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY deployment/nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./terminology.db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./terminology.db:/app/terminology.db
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

Deploy:

```bash
docker-compose up -d
```

### Manual Frontend Deployment

1. **Build the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   This creates a `dist` folder with static files.

2. **Serve with Nginx (Production):**
   - Install Nginx: `sudo apt install nginx`
   - Copy `dist` contents to `/var/www/html`
   - Configure Nginx to proxy `/api` requests to `localhost:8000`

   Example Nginx Config:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       root /var/www/html;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
       }

       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Using Kubernetes

See `deployment/kubernetes/` directory for manifests.

## Monitoring Setup

### Prometheus Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'caresync'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/metrics'
```

### Grafana Dashboard

Import dashboard from `deployment/grafana/caresync-dashboard.json`

Key metrics:
- `app_uptime_seconds` - Application uptime
- `app_requests_total` - Total requests
- `mapping_resources_protected` - Protected resources count
- `orchestrator_blocked_writes` - Blocked write attempts
- `users_total`, `encounters_total`, `appointments_total` - Entity counts

## Security Checklist

- [ ] Change `JWT_SECRET_KEY` to secure random value
- [ ] Use production Razorpay keys (not test keys)
- [ ] Enable HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Configure CORS for production domains only
- [ ] Enable rate limiting
- [ ] Set up backup strategy
- [ ] Configure log rotation
- [ ] Review and update default passwords
- [ ] Enable database encryption at rest

## Backup & Recovery

### Database Backup

```bash
# SQLite backup
cp terminology.db terminology.db.backup.$(date +%Y%m%d)

# PostgreSQL backup
pg_dump caresync > backup.sql
```

### Restore

```bash
# SQLite restore
cp terminology.db.backup.20250129 terminology.db

# PostgreSQL restore
psql caresync < backup.sql
```

## Troubleshooting

### Common Issues

**Issue: Mapping tests failing**
```bash
# Check protected resources
python -c "from services.safeguards import MAPPING_DATA_RESOURCES; print(len(MAPPING_DATA_RESOURCES))"

# Should output: 18
```

**Issue: Authentication not working**
```bash
# Verify JWT secret is set
python -c "import os; print('JWT_SECRET_KEY' in os.environ)"
```

**Issue: Database connection errors**
```bash
# Check database file exists
ls -l terminology.db

# Test connection
python -c "from models.database import SessionLocal; SessionLocal().execute('SELECT 1')"
```

## Support & Maintenance

### Log Locations
- Application logs: `stdout` (capture with systemd/docker)
- Audit logs: `audit_logs` table in database
- Admin actions: `admin_actions` table

### Monitoring Alerts
- Orchestrator paused: Check `/api/health` status
- High error rate: Check `/api/metrics` for `app_errors_total`
- Database issues: Check health endpoint

### Regular Maintenance
- Weekly: Review audit logs
- Monthly: Review mapping feedback and proposals
- Quarterly: Database optimization and cleanup
- As needed: Apply approved mapping updates (manual process)

## Next Steps

1. **Pilot Testing**: Deploy to staging environment
2. **User Onboarding**: Train doctors and staff
3. **Monitoring**: Set up alerts and dashboards
4. **Feedback Collection**: Gather user feedback
5. **Iteration**: Improve based on usage patterns
