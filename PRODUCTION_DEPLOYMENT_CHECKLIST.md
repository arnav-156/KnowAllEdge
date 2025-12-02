# Production Deployment Checklist

## Pre-Deployment

### 1. Code Quality
- [ ] All tests passing (unit, integration, property tests)
- [ ] Code coverage >= 80%
- [ ] No critical or high security issues
- [ ] Code review completed
- [ ] Documentation updated

### 2. Security
- [ ] All secrets stored in environment variables
- [ ] No hardcoded credentials in code
- [ ] Security headers configured
- [ ] HTTPS enforced
- [ ] SSL/TLS certificates valid
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified

### 3. Database
- [ ] Database migrations tested
- [ ] Backup system configured
- [ ] Connection pooling optimized
- [ ] Indexes created for performance
- [ ] Database credentials secured
- [ ] TLS encryption enabled

### 4. Monitoring & Logging
- [ ] Health check endpoint working
- [ ] Metrics collection configured
- [ ] Alerting rules set up
- [ ] Log aggregation configured
- [ ] Error tracking enabled (Sentry/similar)
- [ ] Performance monitoring enabled

### 5. Performance
- [ ] CDN configured for static assets
- [ ] Image optimization enabled
- [ ] Response compression enabled
- [ ] Caching headers configured
- [ ] Database queries optimized
- [ ] Load testing completed

### 6. GDPR Compliance
- [ ] Data export functionality tested
- [ ] Data deletion functionality tested
- [ ] Consent management implemented
- [ ] Audit logging enabled
- [ ] Data encryption at rest enabled
- [ ] Privacy policy updated

## Deployment Steps

### 1. Pre-Deployment Verification
```bash
# Run full test suite
python backend/run_full_test_suite.py

# Run security audit
python backend/security_audit.py

# Verify environment variables
python backend/verify_environment.py
```

### 2. Database Migration
```bash
# Backup current database
python backend/database_backup.py

# Run migrations
alembic upgrade head

# Verify migration
alembic current
```

### 3. Build & Deploy
```bash
# Build Docker images
docker-compose build

# Tag images with version
docker tag app:latest app:v1.0.0

# Push to registry
docker push app:v1.0.0

# Deploy to production
kubectl apply -f k8s/deployment.yaml

# Or use deployment script
./scripts/deploy.sh production
```

### 4. Post-Deployment Verification
```bash
# Check health endpoint
curl https://api.example.com/health

# Verify metrics endpoint
curl https://api.example.com/metrics

# Check logs
kubectl logs -f deployment/app

# Run smoke tests
python backend/smoke_tests.py --url https://api.example.com
```

### 5. Monitor
- [ ] Check application logs
- [ ] Verify metrics in Grafana
- [ ] Check error rates
- [ ] Monitor response times
- [ ] Verify database connections
- [ ] Check Redis connectivity

## Rollback Procedure

### If Issues Detected

1. **Immediate Rollback**
```bash
# Rollback to previous version
kubectl rollout undo deployment/app

# Or deploy previous version
docker pull app:v0.9.0
kubectl set image deployment/app app=app:v0.9.0
```

2. **Database Rollback** (if needed)
```bash
# Rollback migration
alembic downgrade -1

# Restore from backup
python backend/restore_backup.py --backup-file backup_20231201.sql
```

3. **Verify Rollback**
```bash
# Check health
curl https://api.example.com/health

# Verify version
curl https://api.example.com/version
```

4. **Notify Team**
- Post in incident channel
- Update status page
- Document issues found

## Environment Variables

### Required Production Variables
```bash
# Application
FLASK_ENV=production
SECRET_KEY=<strong-secret-key-32-chars-min>
DEBUG=False

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=<strong-redis-password>
REDIS_DB=0

# JWT
JWT_SECRET_KEY=<strong-jwt-secret-32-chars-min>
JWT_ACCESS_TOKEN_EXPIRES=86400

# API Keys
GOOGLE_API_KEY=<google-api-key>

# CDN
CDN_URL=https://cdn.example.com

# Encryption
ENCRYPTION_KEY=<base64-encoded-encryption-key>

# Monitoring
SENTRY_DSN=<sentry-dsn>
PROMETHEUS_METRICS_PORT=9090

# Email (if applicable)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=<smtp-user>
SMTP_PASSWORD=<smtp-password>
```

## Monitoring Checklist

### Metrics to Monitor
- [ ] Request rate (requests/second)
- [ ] Response time (P50, P95, P99)
- [ ] Error rate (%)
- [ ] Database connection pool usage
- [ ] Redis connection pool usage
- [ ] Memory usage
- [ ] CPU usage
- [ ] Disk usage

### Alerts to Configure
- [ ] Error rate > 1%
- [ ] P95 response time > 500ms
- [ ] Database connection pool > 90%
- [ ] Memory usage > 85%
- [ ] Disk usage > 80%
- [ ] Health check failures
- [ ] SSL certificate expiring (< 30 days)

## Security Checklist

### Pre-Production Security Audit
- [ ] Run OWASP ZAP scan
- [ ] Run Bandit security scan
- [ ] Check dependency vulnerabilities (safety)
- [ ] Verify all security headers
- [ ] Test authentication flows
- [ ] Test authorization rules
- [ ] Verify rate limiting
- [ ] Test input validation
- [ ] Check for exposed secrets

### Security Headers Verification
```bash
# Check security headers
curl -I https://api.example.com

# Should include:
# - Content-Security-Policy
# - X-Frame-Options: DENY
# - X-Content-Type-Options: nosniff
# - Strict-Transport-Security
# - Referrer-Policy
```

## Performance Checklist

### Load Testing Results
- [ ] 100 concurrent users: Error rate < 0.1%
- [ ] 500 concurrent users: Error rate < 0.1%
- [ ] 1000 concurrent users: Error rate < 0.1%
- [ ] P95 response time < 500ms
- [ ] P99 response time < 1000ms

### CDN Configuration
- [ ] Static assets served from CDN
- [ ] Cache headers configured
- [ ] Image optimization enabled
- [ ] Compression enabled (Gzip/Brotli)

## Incident Response Plan

### Severity Levels

**Critical (P0)**
- Complete service outage
- Data breach
- Security vulnerability exploited

**High (P1)**
- Major feature broken
- Significant performance degradation
- High error rates (> 5%)

**Medium (P2)**
- Minor feature broken
- Moderate performance issues
- Elevated error rates (1-5%)

**Low (P3)**
- Cosmetic issues
- Minor bugs
- Documentation issues

### Response Procedures

**For Critical Issues (P0)**
1. Immediately notify on-call engineer
2. Create incident channel
3. Assess impact
4. Decide: Fix forward or rollback
5. Implement fix/rollback
6. Verify resolution
7. Post-mortem within 24 hours

**For High Issues (P1)**
1. Notify engineering team
2. Create incident ticket
3. Assess impact
4. Plan fix
5. Deploy fix
6. Verify resolution
7. Post-mortem within 48 hours

### Contact Information
- On-call Engineer: [Phone/Slack]
- Engineering Lead: [Phone/Slack]
- DevOps Team: [Slack Channel]
- Incident Channel: #incidents

## Post-Deployment

### Within 1 Hour
- [ ] Verify all services running
- [ ] Check error rates
- [ ] Monitor response times
- [ ] Verify database connectivity
- [ ] Check Redis connectivity

### Within 24 Hours
- [ ] Review logs for errors
- [ ] Check metrics trends
- [ ] Verify backup completed
- [ ] Review alert triggers
- [ ] Update documentation

### Within 1 Week
- [ ] Conduct post-deployment review
- [ ] Document lessons learned
- [ ] Update runbooks
- [ ] Review performance metrics
- [ ] Plan next deployment

## Useful Commands

### Check Application Status
```bash
# Health check
curl https://api.example.com/health

# Metrics
curl https://api.example.com/metrics

# Version
curl https://api.example.com/version
```

### View Logs
```bash
# Kubernetes
kubectl logs -f deployment/app
kubectl logs -f deployment/app --previous

# Docker
docker logs -f container_name

# Application logs
tail -f /var/log/app/production.log
```

### Database Operations
```bash
# Connect to database
psql $DATABASE_URL

# Check connections
SELECT count(*) FROM pg_stat_activity;

# Check slow queries
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### Redis Operations
```bash
# Connect to Redis
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD

# Check memory usage
INFO memory

# Check connected clients
CLIENT LIST
```

## Sign-Off

### Deployment Approval
- [ ] Engineering Lead: _________________ Date: _______
- [ ] DevOps Lead: _________________ Date: _______
- [ ] Security Review: _________________ Date: _______

### Post-Deployment Verification
- [ ] Deployment Successful: _________________ Date: _______
- [ ] Monitoring Verified: _________________ Date: _______
- [ ] No Critical Issues: _________________ Date: _______

---

**Version:** 1.0.0  
**Last Updated:** 2024-12-02  
**Next Review:** 2025-01-02
