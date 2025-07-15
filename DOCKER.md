# Baby Buddy Docker Deployment

This repository includes Docker configuration that closely matches the LinuxServer.io Baby Buddy container (`lscr.io/linuxserver/babybuddy`).

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository:**

   ```bash
   git clone https://github.com/babybuddy/babybuddy.git
   cd babybuddy
   ```

2. **Create environment file:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application:**

   ```bash
   docker-compose up -d
   ```

4. **Access Baby Buddy:**
   - Open http://localhost:8000
   - Default login: `admin` / `admin`
   - **Important:** Change the default password immediately!

### Using Docker CLI

```bash
docker build -t babybuddy .

docker run -d \
  --name babybuddy \
  -p 8000:8000 \
  -v babybuddy_data:/app/data \
  -e SECRET_KEY="your-secret-key-here" \
  -e DJANGO_SUPERUSER_USERNAME=admin \
  -e DJANGO_SUPERUSER_PASSWORD=admin \
  babybuddy
```

## Configuration

### Environment Variables

| Variable               | Default     | Description                            |
| ---------------------- | ----------- | -------------------------------------- |
| `SECRET_KEY`           | (generated) | Django secret key for security         |
| `DEBUG`                | `False`     | Enable debug mode (not for production) |
| `ALLOWED_HOSTS`        | `*`         | Comma-separated list of allowed hosts  |
| `CSRF_TRUSTED_ORIGINS` | (empty)     | Trusted origins for CSRF               |
| `TZ`                   | `UTC`       | Container timezone                     |

### Database Configuration

**SQLite (Default):**

```yaml
# No additional configuration needed
# Database stored in /app/data/db.sqlite3
```

**PostgreSQL:**

```yaml
environment:
  - DATABASE_URL=postgresql://user:password@db:5432/babybuddy
  # OR
  - DB_ENGINE=django.db.backends.postgresql
  - DB_NAME=babybuddy
  - DB_USER=babybuddy
  - DB_PASSWORD=password
  - DB_HOST=db
  - DB_PORT=5432
```

**MySQL/MariaDB:**

```yaml
environment:
  - DATABASE_URL=mysql://user:password@db:3306/babybuddy
  # OR
  - DB_ENGINE=django.db.backends.mysql
  - DB_NAME=babybuddy
  - DB_USER=babybuddy
  - DB_PASSWORD=password
  - DB_HOST=db
  - DB_PORT=3306
```

### Volumes

- `/app/data` - Persistent data storage (SQLite database, media files)

## Comparison with LinuxServer.io Container

This Docker setup provides similar functionality to `lscr.io/linuxserver/babybuddy`:

### Similarities:

- ✅ Alpine Linux base
- ✅ Nginx reverse proxy
- ✅ Automatic asset building
- ✅ Health checks
- ✅ Non-root user execution
- ✅ Persistent data volume
- ✅ Environment-based configuration
- ✅ Database migration on startup

### Differences:

- Uses Python 3.12 (vs. system Python)
- Simplified configuration structure
- Direct GitHub source (vs. release download)
- Supervisor for process management
- Custom nginx configuration

## Development

### Building the Image

```bash
docker build -t babybuddy:local .
```

### Running with Development Settings

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Accessing Container Shell

```bash
docker exec -it babybuddy /bin/sh
```

### Running Management Commands

```bash
# Database migration
docker exec -it babybuddy python manage.py migrate

# Create superuser
docker exec -it babybuddy python manage.py createsuperuser

# Collect static files
docker exec -it babybuddy python manage.py collectstatic
```

## Production Deployment

### Security Considerations

1. **Set a secure SECRET_KEY:**

   ```bash
   SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
   ```

2. **Configure ALLOWED_HOSTS:**

   ```yaml
   environment:
     - ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

3. **Use HTTPS:**

   ```yaml
   environment:
     - CSRF_TRUSTED_ORIGINS=https://yourdomain.com
   ```

4. **Use external database for production:**
   ```yaml
   environment:
     - DATABASE_URL=postgresql://user:password@db:5432/babybuddy
   ```

### With Reverse Proxy

If using a reverse proxy (Traefik, nginx, etc.), configure headers:

```yaml
environment:
  - CSRF_TRUSTED_ORIGINS=https://yourdomain.com
  - ALLOWED_HOSTS=yourdomain.com
```

## Troubleshooting

### Container Won't Start

- Check logs: `docker logs babybuddy`
- Verify SECRET_KEY is set
- Check volume permissions

### Database Issues

- For PostgreSQL/MySQL: ensure database server is running
- Check database credentials
- Verify network connectivity

### Static Files Not Loading

- Run: `docker exec -it babybuddy python manage.py collectstatic`
- Check volume mounts

### Permission Errors

```bash
# Fix data directory permissions
docker exec -it babybuddy chown -R babybuddy:babybuddy /app/data
```

## Migration from LinuxServer.io Container

If migrating from `lscr.io/linuxserver/babybuddy`:

1. **Backup your data:**

   ```bash
   docker cp babybuddy:/config ./backup
   ```

2. **Stop old container:**

   ```bash
   docker stop babybuddy
   docker rm babybuddy
   ```

3. **Update docker-compose.yml to use new image**

4. **Migrate data volume structure if needed**

5. **Start new container:**
   ```bash
   docker-compose up -d
   ```

## Support

For issues specific to this Docker configuration, please check:

1. [Baby Buddy Documentation](https://docs.babybuddy.app)
2. [Baby Buddy GitHub Issues](https://github.com/babybuddy/babybuddy/issues)
3. [Docker Documentation](https://docs.docker.com)
