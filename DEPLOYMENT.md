# Deployment Checklist

## Pre-deployment

### 1. Environment Setup
- [ ] PostgreSQL database created and accessible
- [ ] Redis server running
- [ ] Environment variables configured (.env file)
- [ ] API keys obtained:
  - [ ] OpenAI API key
  - [ ] Google Cloud credentials
  - [ ] Fireflies.ai API key (if using)
  - [ ] Translation service keys
- [ ] Storage configured (S3 or local)

### 2. Code Preparation
- [ ] All dependencies installed (`pip install -e .`)
- [ ] Database migrations created (`python manage.py makemigrations`)
- [ ] Database migrations applied (`python manage.py migrate`)
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] Superuser created (`python manage.py createsuperuser`)

### 3. Security Configuration
- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] `ALLOWED_HOSTS` configured
- [ ] CORS settings configured
- [ ] SSL/TLS certificates obtained
- [ ] Firewall rules configured

### 4. Service Configuration
- [ ] Celery worker configured as systemd service
- [ ] Celery beat configured as systemd service
- [ ] Nginx/Apache configured
- [ ] Gunicorn/uWSGI configured
- [ ] Log rotation configured

## Deployment Steps

### Docker Deployment (Recommended)

1. **Create Docker Compose file**
   ```yaml
   version: '3.8'
   
   services:
     db:
       image: postgres:15
       environment:
         POSTGRES_DB: asr_middleware
         POSTGRES_USER: asruser
         POSTGRES_PASSWORD: ${DB_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
     
     redis:
       image: redis:7
       command: redis-server --appendonly yes
       volumes:
         - redis_data:/data
     
     web:
       build: .
       command: gunicorn core.wsgi:application --bind 0.0.0.0:8000
       volumes:
         - ./:/app
         - media_files:/app/media
       ports:
         - "8000:8000"
       env_file:
         - .env
       depends_on:
         - db
         - redis
     
     celery:
       build: .
       command: celery -A core worker -l info
       volumes:
         - ./:/app
       env_file:
         - .env
       depends_on:
         - db
         - redis
     
     celery-beat:
       build: .
       command: celery -A core beat -l info
       volumes:
         - ./:/app
       env_file:
         - .env
       depends_on:
         - db
         - redis
     
     nginx:
       image: nginx:latest
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
         - ./ssl:/etc/nginx/ssl
         - media_files:/app/media
       depends_on:
         - web
   
   volumes:
     postgres_data:
     redis_data:
     media_files:
   ```

2. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       postgresql-client \
       ffmpeg \
       libsndfile1 \
       && rm -rf /var/lib/apt/lists/*
   
   # Set work directory
   WORKDIR /app
   
   # Install Python dependencies
   COPY pyproject.toml ./
   RUN pip install --upgrade pip
   RUN pip install -e .
   
   # Copy project
   COPY . .
   
   # Create media directory
   RUN mkdir -p /app/media
   
   # Run migrations and collect static
   RUN python manage.py collectstatic --noinput
   
   EXPOSE 8000
   ```

3. **Deploy**
   ```bash
   docker-compose up -d
   ```

### Manual Deployment (Ubuntu/Debian)

1. **Install system dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv postgresql redis-server nginx ffmpeg
   ```

2. **Set up application**
   ```bash
   cd /opt
   sudo git clone <your-repo> asr-middleware
   cd asr-middleware
   sudo chown -R www-data:www-data .
   
   sudo -u www-data python3.11 -m venv venv
   sudo -u www-data venv/bin/pip install -e .
   ```

3. **Configure environment**
   ```bash
   sudo -u www-data cp .env.example .env
   sudo -u www-data nano .env  # Edit configuration
   ```

4. **Set up database**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE asr_middleware;
   CREATE USER asruser WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE asr_middleware TO asruser;
   \q
   
   sudo -u www-data venv/bin/python manage.py migrate
   sudo -u www-data venv/bin/python manage.py createsuperuser
   sudo -u www-data venv/bin/python manage.py collectstatic
   ```

5. **Create systemd services**

   `/etc/systemd/system/asr-middleware.service`:
   ```ini
   [Unit]
   Description=ASR Middleware Django Application
   After=network.target postgresql.service redis.service
   
   [Service]
   Type=notify
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/asr-middleware
   Environment="PATH=/opt/asr-middleware/venv/bin"
   ExecStart=/opt/asr-middleware/venv/bin/gunicorn \
             --workers 4 \
             --bind unix:/run/asr-middleware.sock \
             core.wsgi:application
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

   `/etc/systemd/system/asr-celery.service`:
   ```ini
   [Unit]
   Description=ASR Middleware Celery Worker
   After=network.target redis.service
   
   [Service]
   Type=forking
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/asr-middleware
   Environment="PATH=/opt/asr-middleware/venv/bin"
   ExecStart=/opt/asr-middleware/venv/bin/celery -A core worker \
             --loglevel=info --concurrency=4
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

   `/etc/systemd/system/asr-celery-beat.service`:
   ```ini
   [Unit]
   Description=ASR Middleware Celery Beat
   After=network.target redis.service
   
   [Service]
   Type=simple
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/asr-middleware
   Environment="PATH=/opt/asr-middleware/venv/bin"
   ExecStart=/opt/asr-middleware/venv/bin/celery -A core beat \
             --loglevel=info
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

6. **Configure Nginx**

   `/etc/nginx/sites-available/asr-middleware`:
   ```nginx
   upstream asr_middleware {
       server unix:/run/asr-middleware.sock;
   }
   
   server {
       listen 80;
       server_name your-domain.com;
       
       # Redirect to HTTPS
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
       
       ssl_certificate /etc/ssl/certs/your-cert.pem;
       ssl_certificate_key /etc/ssl/private/your-key.pem;
       
       client_max_body_size 500M;
       
       location / {
           proxy_pass http://asr_middleware;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       location /media/ {
           alias /opt/asr-middleware/media/;
       }
       
       location /static/ {
           alias /opt/asr-middleware/static/;
       }
   }
   ```

7. **Enable and start services**
   ```bash
   sudo systemctl enable asr-middleware asr-celery asr-celery-beat
   sudo systemctl start asr-middleware asr-celery asr-celery-beat
   
   sudo ln -s /etc/nginx/sites-available/asr-middleware /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Post-deployment

### 1. Verification
- [ ] Web server responding (`curl http://localhost`)
- [ ] API accessible (`curl http://localhost/api/`)
- [ ] Admin panel accessible
- [ ] Celery workers running (`systemctl status asr-celery`)
- [ ] Celery beat running (`systemctl status asr-celery-beat`)
- [ ] Database connectivity working
- [ ] Redis connectivity working

### 2. Testing
- [ ] Create test meeting via API
- [ ] Upload test audio file
- [ ] Trigger processing
- [ ] Verify transcription completes
- [ ] Verify translation works
- [ ] Test export functionality
- [ ] Test Fireflies webhook (if configured)

### 3. Monitoring Setup
- [ ] Configure Sentry for error tracking
- [ ] Set up log aggregation (ELK/Grafana)
- [ ] Configure uptime monitoring
- [ ] Set up performance monitoring
- [ ] Configure backup schedule
- [ ] Set up alerting for failures

### 4. Documentation
- [ ] Document deployment-specific configurations
- [ ] Create runbook for common issues
- [ ] Document backup/restore procedures
- [ ] Create monitoring dashboard
- [ ] Document scaling procedures

## Maintenance

### Daily Tasks
- [ ] Check service status
- [ ] Monitor error logs
- [ ] Review failed jobs
- [ ] Check disk space

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Check API usage
- [ ] Review and optimize slow queries
- [ ] Test backup restoration

### Monthly Tasks
- [ ] Update dependencies
- [ ] Review and optimize costs
- [ ] Update ASR models
- [ ] Security audit
- [ ] Clean up old data

## Rollback Procedure

1. **Stop services**
   ```bash
   sudo systemctl stop asr-middleware asr-celery asr-celery-beat
   ```

2. **Restore previous version**
   ```bash
   cd /opt/asr-middleware
   git checkout <previous-commit>
   ```

3. **Restore database (if needed)**
   ```bash
   psql -U asruser -d asr_middleware < backup.sql
   ```

4. **Restart services**
   ```bash
   sudo systemctl start asr-middleware asr-celery asr-celery-beat
   ```

## Scaling

### Horizontal Scaling
- Add more Celery workers
- Use load balancer for multiple web servers
- Implement database read replicas
- Use CDN for static/media files

### Vertical Scaling
- Increase worker concurrency
- Upgrade server resources
- Optimize database queries
- Implement caching (Redis)

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u asr-middleware -n 50
sudo journalctl -u asr-celery -n 50

# Check configuration
sudo -u www-data /opt/asr-middleware/venv/bin/python manage.py check
```

### Database connection errors
```bash
# Test database connection
psql -U asruser -d asr_middleware -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql
```

### Celery tasks not running
```bash
# Check Redis
redis-cli ping

# Check Celery worker logs
sudo journalctl -u asr-celery -f

# Restart Celery
sudo systemctl restart asr-celery asr-celery-beat
```

### High memory usage
```bash
# Check process memory
top -o %MEM

# Reduce Celery workers
# Edit /etc/systemd/system/asr-celery.service
# Change --concurrency=4 to --concurrency=2

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart asr-celery
```

---

**Important**: Always test deployment in staging environment before production!
