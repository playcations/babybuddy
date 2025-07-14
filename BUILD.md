# Baby Buddy Build Guide

This document explains how to properly build Baby Buddy from source and what files are generated vs. tracked in the repository.

## Quick Start

For developers who just want to get Baby Buddy running locally:

```bash
# 1. Clone and setup
git clone <repository-url>
cd babybuddy
pipenv install --python 3.12 --dev
npm install
nvm use

# 2. Build everything
npx gulp updateglyphs
npx gulp build
echo "yes" | npx gulp collectstatic
npx gulp compilemessages
npx gulp migrate

# 3. Create admin user and run server
pipenv run python manage.py createsuperuser
npx gulp

# Visit http://127.0.0.1:8000 in your browser
```

## Prerequisites

1. **Python 3.12+** with pipenv
2. **Node.js 18.x** (use `nvm use` to activate correct version)
3. **Git** for version control

## Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd babybuddy

# Install Python dependencies (including dev tools)
pipenv install --python 3.12 --dev

# Install Node.js dependencies
npm install

# Activate correct Node.js version
nvm use
```

## Build Process

### 1. Generate Fontello Icon Fonts

Baby Buddy uses custom icon fonts generated from Fontello. The source configuration is tracked in git, but the generated files are not.

```bash
# Generate font files and CSS from config.json
npx gulp updateglyphs
```

**What this generates:**

- `babybuddy/static_src/fontello/css/*.css` - Font CSS files
- `babybuddy/static_src/fontello/font/*` - Font files (woff, ttf, etc.)
- `babybuddy/static_src/fontello/demo.html` - Font preview

### 2. Build Static Assets

```bash
# Build all static assets (CSS, JavaScript, fonts, images)
npx gulp build
```

**What this does:**

- Compiles SCSS to CSS
- Minifies and concatenates JavaScript files
- Copies fonts, images, and other static files
- Outputs to `*/static/` directories

**Individual build commands:**

```bash
npx gulp styles    # Compile SCSS only
npx gulp scripts   # Build JavaScript only
npx gulp extras    # Copy fonts/images only
```

### 3. Collect Static Files for Django

```bash
# Collect and process static files for Django
echo "yes" | npx gulp collectstatic
```

**What this generates:**

- `/static/` directory with all static files
- Versioned files with cache-busting hashes (e.g., `app.9d499eb6fc8d.css`)
- Compressed files (gzip)

### 4. Database Setup

```bash
# Run database migrations
npx gulp migrate

# Optional: Generate fake data for development
npx gulp fake
```

### 5. Compile Translations

```bash
# Compile translation files (.po → .mo)
npx gulp compilemessages
```

### 6. Generate API Schema (Optional)

```bash
# Generate OpenAPI schema
npx gulp generateschema
```

## Complete Build Command

For a complete build from scratch:

```bash
# Clean previous builds
npx gulp clean

# Generate icons, build assets, and collect static files
npx gulp updateglyphs
npx gulp build
echo "yes" | npx gulp collectstatic

# Compile translations
npx gulp compilemessages

# Run migrations
npx gulp migrate
```

## Running the Server

### Development Server

For active development, use the integrated watch mode:

```bash
# Start development server with file watching (recommended)
npx gulp

# This runs:
# - gulp build (initial build)
# - gulp watch (watches for file changes and rebuilds)
# - gulp runserver (starts Django dev server on http://127.0.0.1:8000)
```

### Manual Server Control

If you need more control over the server:

```bash
# Run Django development server only
npx gulp runserver

# Run with custom IP address
npx gulp runserver --ip 0.0.0.0:8080

# Run server manually with pipenv
pipenv run python manage.py runserver

# Run server with specific settings
pipenv run python manage.py runserver --settings=babybuddy.settings.development
```

### Production Server

For production deployment, use a proper WSGI server:

```bash
# Example with gunicorn (install separately)
pipenv install gunicorn
pipenv run gunicorn babybuddy.wsgi:application --bind 0.0.0.0:8000

# Example with uwsgi (install separately)
pipenv install uwsgi
pipenv run uwsgi --http :8000 --module babybuddy.wsgi
```

### Default URLs

- **Development:** http://127.0.0.1:8000
- **Admin Interface:** http://127.0.0.1:8000/admin/
- **API Documentation:** http://127.0.0.1:8000/api/
- **User Registration:** http://127.0.0.1:8000/accounts/signup/

### Creating Admin User

```bash
# Create superuser for admin access
pipenv run python manage.py createsuperuser
```

## Development Workflow

## Repository Structure

### Source Files (Tracked in Git)

```
├── */static_src/           # Source static files
│   ├── js/                # Source JavaScript
│   ├── scss/              # Source SCSS/CSS
│   └── **/                # Other source assets
├── babybuddy/static_src/fontello/config.json  # Fontello configuration
├── locale/*/LC_MESSAGES/*.po                  # Translation source files
├── docs/                  # Documentation source
├── gulpfile.js            # Build configuration
├── package.json           # Node.js dependencies
├── Pipfile               # Python dependencies
└── *.py                  # Python source code
```

### Generated Files (Ignored by Git)

```
├── */static/              # Built static files
├── /static/               # Django collectstatic output
├── babybuddy/static_src/fontello/css/     # Generated font CSS
├── babybuddy/static_src/fontello/font/    # Generated font files
├── locale/*/LC_MESSAGES/*.mo              # Compiled translations
├── openapi-schema.yml     # Generated API schema
├── /data/                 # Development database
└── /site/                 # Built documentation
```

## Code Quality

```bash
# Run linting
npx gulp lint

# Auto-format code
npx gulp format

# Run tests
npx gulp test

# Run tests with coverage
npx gulp coverage
```

## Production Deployment

For production builds, ensure all static files are built and collected:

```bash
# Set production environment
export DJANGO_SETTINGS_MODULE=babybuddy.settings.production

# Build everything
npx gulp updateglyphs
npx gulp build
echo "yes" | npx gulp collectstatic --settings=babybuddy.settings.production

# Compile translations
npx gulp compilemessages

# Run migrations
npx gulp migrate
```

## Troubleshooting

### Missing Icons

If icons aren't displaying:

1. Run `npx gulp updateglyphs` to regenerate font files
2. Run `npx gulp build` to rebuild static assets
3. Run `echo "yes" | npx gulp collectstatic` to update served files
4. Clear browser cache (fonts may be cached)

### Build Errors

If builds fail:

1. Ensure all dependencies are installed (`pipenv install --dev` and `npm install`)
2. Check Node.js version with `nvm use`
3. Try `npx gulp clean` then rebuild

### Static Files Not Loading

1. Verify `DEBUG = True` in development settings
2. Ensure `npx gulp collectstatic` was run
3. Check that `/static/` directory exists and contains files

## Environment Variables

Set these for different environments:

```bash
# Development (default)
export DJANGO_SETTINGS_MODULE=babybuddy.settings.development

# Production
export DJANGO_SETTINGS_MODULE=babybuddy.settings.production

# Testing
export DJANGO_SETTINGS_MODULE=babybuddy.settings.test
```
