#!/bin/bash

# SSL Setup Script for SMEFlow Production Deployment
# This script sets up Let's Encrypt SSL certificates using Certbot

set -e

# Configuration
DOMAIN=${1:-"smeflow.com"}
EMAIL=${2:-"admin@smeflow.com"}
NGINX_CONF_DIR="./nginx"
SSL_DIR="./nginx/ssl"
WEBROOT_DIR="./nginx/certbot"

echo "🔒 Setting up SSL certificates for SMEFlow"
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"

# Create necessary directories
mkdir -p "$SSL_DIR"
mkdir -p "$WEBROOT_DIR"
mkdir -p "$NGINX_CONF_DIR"

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create temporary Nginx config for initial certificate generation
cat > "$NGINX_CONF_DIR/nginx-temp.conf" << EOF
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name $DOMAIN;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 200 'OK';
            add_header Content-Type text/plain;
        }
    }
}
EOF

echo "📋 Starting temporary Nginx for certificate generation..."

# Start temporary Nginx container
docker run -d \
    --name nginx-temp \
    -p 80:80 \
    -v "$PWD/$NGINX_CONF_DIR/nginx-temp.conf:/etc/nginx/nginx.conf:ro" \
    -v "$PWD/$WEBROOT_DIR:/var/www/certbot" \
    nginx:1.25-alpine

# Wait for Nginx to start
sleep 5

echo "🔐 Requesting SSL certificate from Let's Encrypt..."

# Request certificate using Certbot
docker run --rm \
    -v "$PWD/$SSL_DIR:/etc/letsencrypt" \
    -v "$PWD/$WEBROOT_DIR:/var/www/certbot" \
    certbot/certbot \
    certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d "$DOMAIN"

# Stop temporary Nginx
echo "🛑 Stopping temporary Nginx..."
docker stop nginx-temp
docker rm nginx-temp

# Clean up temporary config
rm "$NGINX_CONF_DIR/nginx-temp.conf"

# Update Nginx config with correct domain
sed -i "s/smeflow\.com/$DOMAIN/g" "$NGINX_CONF_DIR/nginx.conf"

echo "✅ SSL certificate generated successfully!"
echo "📁 Certificate files are stored in: $SSL_DIR"
echo ""
echo "🚀 You can now start the production environment with:"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "🔄 To renew certificates, run:"
echo "   docker-compose -f docker-compose.prod.yml exec certbot certbot renew"
