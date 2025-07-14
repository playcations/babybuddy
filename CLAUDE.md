# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Baby Buddy is a Django web application for tracking baby care activities like feedings, diaper changes, sleep, and measurements. It uses Django REST Framework for API endpoints and includes a responsive frontend with Bootstrap.

## Development Commands

### Environment Setup

- `pipenv install --python 3.12 --dev` - Install Python dependencies using Python 3.12 (required for django-dbsettings compatibility)
- `npm install` - Install Node.js dependencies
- `nvm use` - Activate correct Node.js version (18.x)
- Use `DJANGO_SETTINGS_MODULE=babybuddy.settings.development` for Django commands

### Build and Development

- `gulp` - Default development command: builds assets, watches for changes, runs Django dev server
- `gulp build` - Build all static assets (scripts, styles, extras) to `babybuddy/static/`
- `gulp clean` - Delete all build folders and static assets
- `gulp watch` - Watch for file changes and rebuild assets
- `gulp runserver` - Run Django development server (accepts `--ip` parameter)

### Asset Management

- `gulp scripts` - Build and minify JavaScript files
- `gulp styles` - Compile SCSS to CSS
- `gulp extras` - Copy fonts, images, and other static files
- `gulp collectstatic` - Run Django's collectstatic management command

### Code Quality

- `gulp lint` - Run linting on Python (Black, djlint), JavaScript (Prettier), and SCSS (stylelint)
- `gulp format` - Auto-format code using Black, djlint, and Prettier
- `lefthook install` - Install git pre-commit hooks that run linting

### Testing

- `gulp test` - Run Django tests (excludes tests tagged "isolate")
- `gulp coverage` - Run tests with coverage reporting
- `pipenv run python manage.py test --settings=babybuddy.settings.test` - Direct test execution

### Django Management

- `gulp migrate` - Run database migrations
- `gulp makemigrations` - Create new migrations
- `gulp fake` - Generate fake data for development
- `gulp reset` - Reset database (non-interactive)
- `gulp compilemessages` - Compile translation messages
- `gulp makemessages` - Extract translatable strings

### Documentation

- `gulp docs:build` - Build documentation site locally
- `gulp docs:watch` - Serve docs with live reloading
- `gulp docs:deploy` - Deploy docs to GitHub Pages

## Architecture

### Django Apps Structure

- `api/` - REST API endpoints using Django REST Framework
- `babybuddy/` - Core Django app with settings, main views, user management
- `core/` - Core models and views for baby tracking (Child, Feeding, Sleep, etc.)
- `dashboard/` - Dashboard views and cards for data visualization
- `reports/` - Reporting functionality with graphs using Plotly

### Key Models (core/models.py)

- `Child` - Represents a baby/child being tracked
- `Feeding` - Feeding sessions with type, amount, duration
- `Sleep` - Sleep sessions with start/end times, nap indicator
- `DiaperChange` - Diaper changes with type and amount
- `Timer` - Active timers for tracking ongoing activities
- `Note` - Text notes with optional images and tags

### Frontend Assets

- SCSS source files in `*/static_src/scss/`
- JavaScript source files in `*/static_src/js/`
- Built assets go to `*/static/` directories
- Uses Bootstrap 5, jQuery, Plotly.js, and custom components

### Settings Structure

- `babybuddy/settings/base.py` - Base Django settings
- `babybuddy/settings/development.py` - Development overrides
- `babybuddy/settings/production.py` - Production configuration
- `babybuddy/settings/test.py` - Test-specific settings

### Template System

- Django templates in `*/templates/` directories
- Custom template tags in `*/templatetags/`
- Form rendering with django-widget-tweaks
- Timeline rendering for activity feeds

## Development Workflow

1. Set up environment with `pipenv install --three --dev` and `npm install`
2. Run `gulp` for development (builds assets, watches files, starts server)
3. Use `gulp lint` before committing (automatically runs via lefthook pre-commit)
4. Run `gulp test` to verify functionality
5. Use Django admin at `/admin/` for data management

## Code Style

- Python: Black formatter with djlint for Django templates
- JavaScript: Prettier
- SCSS: stylelint with SCSS-specific rules
- Pre-commit hooks enforce style via lefthook

## API

- REST API available at `/api/`
- Token-based authentication
- Endpoints for all core models (children, feedings, sleep, etc.)
- OpenAPI schema generated with `gulp generateschema`
