# Production Deployment Guide

## 🚀 Quick Deployment Options

### Option 1: Google Cloud Run (Recommended)

**Advantages:**
- Serverless (auto-scaling)
- Pay only for usage
- Built-in HTTPS
- Simple deployment

**Steps:**

1. **Install Google Cloud SDK**
```bash
# Download from: https://cloud.google.com/sdk/docs/install
gcloud init
```

2. **Set project**
```bash
gcloud config set project YOUR_PROJECT_ID
```

3. **Deploy**
```bash
gcloud run deploy KNOWALLEDGE-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_NAME=YOUR_PROJECT_ID \
  --set-secrets ACCESS_TOKEN=ACCESS_TOKEN:latest \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10
```

4. **Note the service URL**
```
Service URL: https://KNOWALLEDGE-api-xxxxx-uc.a.run.app
```

5. **Update frontend to use this URL**

---

### Option 2: Docker Container

1. **Build image**
```bash
docker build -t KNOWALLEDGE-api .
```

2. **Run container**
```bash
docker run -d \
  -p 5000:5000 \
  -e PROJECT_NAME=your-project-id \
  -e ACCESS_TOKEN=your-token \
  --name KNOWALLEDGE-api \
  KNOWALLEDGE-api
```

3. **View logs**
```bash
docker logs -f KNOWALLEDGE-api
```

---

### Option 3: Traditional Server (VPS/VM)

1. **Server setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.9 python3.9-venv python3-pip -y

# Install Nginx
sudo apt install nginx -y
```

2. **Deploy application**
```bash
# Clone repo
git clone https://github.com/yourusername/KNOWALLEDGE.git
cd KNOWALLEDGE/backend

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Set environment variables
cp .env.example .env
nano .env  # Edit with your values
```

3. **Create systemd service**
```bash
sudo nano /etc/systemd/system/KNOWALLEDGE.service
```

```ini
[Unit]
Description=KNOWALLEDGE API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/user/KNOWALLEDGE/backend
Environment="PATH=/home/user/KNOWALLEDGE/backend/venv/bin"
ExecStart=/home/user/KNOWALLEDGE/backend/venv/bin/gunicorn \
  --workers 4 \
  --bind 127.0.0.1:5000 \
  --timeout 120 \
  --access-logfile /var/log/KNOWALLEDGE/access.log \
  --error-logfile /var/log/KNOWALLEDGE/error.log \
  main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. **Configure Nginx**
```bash
sudo nano /etc/nginx/sites-available/KNOWALLEDGE
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

5. **Enable and start**
```bash
sudo ln -s /etc/nginx/sites-available/KNOWALLEDGE /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

sudo systemctl enable KNOWALLEDGE
sudo systemctl start KNOWALLEDGE
```

6. **Setup SSL with Let's Encrypt**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.yourdomain.com
```

---

## 🔒 Security Checklist

### Before Production:

- [ ] Update CORS origins in `main.py` to your frontend domain
- [ ] Set `debug=False` in production
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Review file upload limits
- [ ] Test error handling
- [ ] Set up logging aggregation

### Environment Variables:

```bash
# Required
PROJECT_NAME=your-gcp-project-id
ACCESS_TOKEN=your-access-token

# Optional
FLASK_ENV=production
LOG_LEVEL=INFO
MAX_SUBTOPICS=20
CACHE_TTL=3600
RATE_LIMIT_REQUESTS=100
```

---

## 📊 Monitoring Setup

### Option 1: Google Cloud Monitoring

```bash
# Enable API
gcloud services enable monitoring.googleapis.com

# Cloud Run automatically sends logs to Cloud Logging
# View at: https://console.cloud.google.com/logs
```

### Option 2: Application Monitoring

Install monitoring libraries:
```bash
pip install prometheus-flask-exporter
```

Add to `main.py`:
```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

### Option 3: Error Tracking (Sentry)

```bash
pip install sentry-sdk[flask]
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1
)
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - id: 'auth'
      uses: 'google-github-actions/auth@v1'
      with:
        credentials_json: '${{ secrets.GCP_SA_KEY }}'
    
    - name: 'Deploy to Cloud Run'
      uses: 'google-github-actions/deploy-cloudrun@v1'
      with:
        service: 'KNOWALLEDGE-api'
        region: 'us-central1'
        source: './backend'
```

---

## 📈 Performance Tuning

### Gunicorn Configuration

```bash
gunicorn \
  --workers 4 \              # 2-4 per CPU core
  --threads 2 \              # Enable threading
  --worker-class gthread \   # Use threaded workers
  --timeout 120 \            # Request timeout
  --keep-alive 5 \           # Keep-alive timeout
  --max-requests 1000 \      # Restart worker after N requests
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile - \
  main:app
```

### Redis Caching (Production)

```bash
pip install redis

# In main.py
import redis

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)
```

---

## 🧪 Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test endpoint
ab -n 1000 -c 10 -T 'application/json' -p test_data.json \
  http://localhost:5000/api/health
```

---

## 🆘 Troubleshooting

### Issue: Rate limiting too aggressive
**Solution:** Adjust in `main.py`:
```python
RATE_LIMIT_REQUESTS = 200  # Increase limit
```

### Issue: Slow AI responses
**Solution:** 
- Use caching
- Reduce concurrent requests
- Increase timeout values

### Issue: Memory usage high
**Solution:**
- Clear cache periodically
- Reduce worker count
- Monitor with `/api/metrics`

### Issue: Upload failures
**Solution:**
- Check `MAX_FILE_SIZE`
- Verify `uploads/` directory permissions
- Check disk space

---

## 📞 Support

- GitHub Issues: [Your Repo URL]
- Documentation: `/api/docs`
- Metrics: `/api/metrics`
- Health: `/api/health`
