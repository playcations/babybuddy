# syntax=docker/dockerfile:1

FROM python:3.12-alpine

# Set version labels
ARG BUILD_DATE
ARG VERSION
ARG BABYBUDDY_VERSION
LABEL build_version="Custom Baby Buddy version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="Baby Buddy Community"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=babybuddy.settings.docker \
    SECRET_KEY="" \
    ALLOWED_HOSTS="*" \
    DEBUG=False

# Install system dependencies
RUN apk add --no-cache --virtual .build-deps \
        build-base \
        jpeg-dev \
        libffi-dev \
        libxml2-dev \
        libxslt-dev \
        mariadb-dev \
        postgresql-dev \
        python3-dev \
        zlib-dev \
        nodejs \
        npm && \
    apk add --no-cache \
        jpeg \
        libffi \
        libpq \
        libxml2 \
        libxslt \
        mariadb-connector-c \
        nginx \
        su-exec \
        wget

# Create app directory
WORKDIR /app

# Copy application files
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies and build assets
RUN npm install && \
    npx gulp updateglyphs && \
    npx gulp build && \
    npx gulp compilemessages

# Create config directory for SQLite and media files (LinuxServer compatibility)
RUN mkdir -p /config/media && \
    chmod 755 /config

# Create nginx configuration
RUN mkdir -p /etc/nginx/http.d
COPY docker/nginx.conf /etc/nginx/http.d/default.conf

# No longer using supervisor - using simple shell script approach

# Create startup script
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

# Clean up build dependencies
RUN apk del .build-deps && \
    rm -rf /var/cache/apk/* \
           /tmp/* \
           /var/tmp/* \
           node_modules \
           ~/.cache

# Create non-root user (will be modified by PUID/PGID in start script)
RUN addgroup -g 1000 -S babybuddy && \
    adduser -u 1000 -S babybuddy -G babybuddy

# Set ownership
RUN chown -R babybuddy:babybuddy /app && \
    chown -R babybuddy:babybuddy /config

# Keep running as root for nginx startup, will drop privileges for gunicorn using su-exec

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/ || exit 1

# Start command
CMD ["/start.sh"]

# Volume for persistent data (LinuxServer compatibility)
VOLUME ["/config"]