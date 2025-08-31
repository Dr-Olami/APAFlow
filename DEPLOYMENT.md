# SMEFlow Production Deployment Guide

This guide covers deploying SMEFlow to production with SSL/TLS encryption, reverse proxy, and security best practices.

## Architecture Overview

```
Internet → Nginx (SSL/Proxy) → SMEFlow API
                            → Keycloak Auth
                            → PostgreSQL
                            → Redis Cache
```

## Prerequisites

- Domain name pointing to your server
- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Ports 80 and 443 open in firewall

## Quick Start

1. **Clone and setup**:

   ```bash
   git clone <repository>
   cd smeflow
   cp .env.prod.example .env.prod
   ```

2. **Configure environment**:
   Edit `.env.prod` with your actual values:
   - Database passwords
   - Domain name
   - SSL email
   - API keys

3. **Setup SSL certificates**:

   ```bash
   chmod +x scripts/ssl-setup.sh
   ./scripts/ssl-setup.sh your-domain.com admin@your-domain.com
   ```

4. **Deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## SSL/TLS Configuration

### Automatic Setup (Recommended)

Use the provided script:

```bash
./scripts/ssl-setup.sh smeflow.com admin@smeflow.com
```

### Manual Setup

1. **Create directories**:

   ```bash
   mkdir -p nginx/ssl nginx/certbot
   ```

2. **Get certificates**:
   ```bash
   docker run --rm \
     -v $PWD/nginx/ssl:/etc/letsencrypt \
     -v $PWD/nginx/certbot:/var/www/certbot \
     certbot/certbot certonly --webroot \
     --webroot-path=/var/www/certbot \
     --email admin@smeflow.com \
     --agree-tos --no-eff-email \
     -d smeflow.com
   ```

### Certificate Renewal

Certificates auto-renew via cron job:

```bash
# Add to crontab
0 12 * * * docker-compose -f /path/to/docker-compose.prod.yml exec certbot certbot renew --quiet
```

## Nginx Configuration

The Nginx configuration provides:

- **SSL/TLS termination** with modern security settings
- **HTTP to HTTPS redirect** for all traffic
- **Rate limiting** for API and auth endpoints
- **Security headers** (HSTS, CSP, etc.)
- **Gzip compression** for better performance
- **WebSocket support** for real-time features

Key features:

- TLS 1.2/1.3 only
- Strong cipher suites
- OCSP stapling
- Perfect Forward Secrecy

## Security Features

### Network Security

- All services isolated in Docker network
- No direct database access from internet
- Rate limiting on API endpoints
- DDoS protection via Nginx

### Application Security

- JWT token authentication
- CORS protection
- SQL injection prevention
- XSS protection headers

### Data Security

- Encrypted database connections
- Redis password protection
- Secrets via environment variables
- Regular security updates

## Monitoring & Maintenance

### Health Checks

```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Check specific service logs
docker-compose -f docker-compose.prod.yml logs smeflow-api
```

### SSL Certificate Status

```bash
# Check certificate expiration
openssl x509 -in nginx/ssl/live/smeflow.com/cert.pem -text -noout | grep "Not After"
```

### Database Backups

```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U smeflow smeflow > backup.sql

# Automated backup (add to crontab)
0 2 * * * /path/to/backup-script.sh
```

## Scaling & Performance

### Horizontal Scaling

- Add multiple API instances behind Nginx
- Use Redis for session storage
- Database read replicas

### Performance Tuning

- Nginx worker processes = CPU cores
- PostgreSQL connection pooling
- Redis memory optimization
- Application-level caching

## Troubleshooting

### Common Issues

1. **SSL Certificate Issues**:

   ```bash
   # Check certificate files
   ls -la nginx/ssl/live/smeflow.com/

   # Test SSL configuration
   nginx -t
   ```

2. **Database Connection Issues**:

   ```bash
   # Check PostgreSQL logs
   docker-compose logs postgres

   # Test connection
   docker-compose exec postgres psql -U smeflow -d smeflow
   ```

3. **High Memory Usage**:

   ```bash
   # Check container resource usage
   docker stats

   # Restart services if needed
   docker-compose -f docker-compose.prod.yml restart
   ```

### Log Locations

- Nginx: `/var/log/nginx/`
- Application: `docker-compose logs smeflow-api`
- Database: `docker-compose logs postgres`
- Authentication: `docker-compose logs keycloak`

## Security Checklist

- [ ] SSL certificates configured and auto-renewing
- [ ] Strong passwords for all services
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] Regular security updates scheduled
- [ ] Database backups automated
- [ ] Monitoring and alerting configured
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Secrets stored securely (not in code)
- [ ] Access logs monitored

## Updates & Maintenance

### Application Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Support

For production support:

- Check logs first: `docker-compose logs`
- Review health endpoints: `https://your-domain.com/health`
- Monitor resource usage: `docker stats`
- Verify SSL status: SSL checker tools
