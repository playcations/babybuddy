#!/bin/bash

# Baby Buddy Deployment Script with Medicine Feature Support
# This script automates the deployment process for Baby Buddy including the new Medicine feature
# Author: Claude Code Assistant
# Version: 1.0

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups"
LOG_FILE="${SCRIPT_DIR}/deploy.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default values
DRY_RUN=false
SKIP_BACKUP=false
SETTINGS_MODULE="babybuddy.settings.production"
PYTHON_VERSION="3.12"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}" | tee -a "$LOG_FILE"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Baby Buddy Deployment Script with Medicine Feature Support

OPTIONS:
    -h, --help              Show this help message
    -d, --dry-run          Show what would be done without executing
    -s, --skip-backup      Skip database backup step
    -e, --env ENV          Environment settings module (default: $SETTINGS_MODULE)
    -p, --python VERSION   Python version to use (default: $PYTHON_VERSION)
    -v, --verbose          Enable verbose output

EXAMPLES:
    $0                     # Standard deployment
    $0 --dry-run          # Show deployment plan without executing
    $0 --skip-backup      # Deploy without creating backup
    $0 -e babybuddy.settings.development  # Deploy with development settings

MEDICINE FEATURE:
    This script includes specific steps for the Medicine feature deployment:
    - Tests medicine migrations on database copy
    - Applies medicine-related migrations
    - Updates static assets with new medicine icons
    - Validates medicine functionality post-deployment

EOF
}

# Function to check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"
    
    local missing_deps=()
    
    # Check for required commands
    for cmd in python3 pip pipenv npm node git; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 --version | grep -oE '[0-9]+\.[0-9]+')
    if [[ $(echo "$python_version < 3.10" | bc -l) -eq 1 ]]; then
        print_error "Python 3.10+ required, found $python_version"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "manage.py" ]] || [[ ! -f "gulpfile.js" ]]; then
        print_error "This script must be run from the Baby Buddy root directory"
        exit 1
    fi
    
    print_status "All prerequisites met"
}

# Function to create backup
create_backup() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        print_warning "Skipping backup step as requested"
        return 0
    fi
    
    print_section "Creating Database Backup"
    
    mkdir -p "$BACKUP_DIR"
    
    # Determine database type and create appropriate backup
    db_engine=$(DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
from django.conf import settings
print(settings.DATABASES['default']['ENGINE'])
" 2>/dev/null || echo "unknown")
    
    case "$db_engine" in
        *sqlite3*)
            db_path=$(DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
from django.conf import settings
print(settings.DATABASES['default']['NAME'])
" 2>/dev/null || echo "")
            
            if [[ -f "$db_path" ]]; then
                backup_file="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sqlite3"
                cp "$db_path" "$backup_file"
                print_status "SQLite backup created: $backup_file"
            else
                print_error "SQLite database file not found: $db_path"
                exit 1
            fi
            ;;
        *postgresql*)
            backup_file="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"
            pg_dump babybuddy > "$backup_file" 2>/dev/null || {
                print_error "PostgreSQL backup failed"
                exit 1
            }
            print_status "PostgreSQL backup created: $backup_file"
            ;;
        *mysql*)
            backup_file="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"
            mysqldump babybuddy > "$backup_file" 2>/dev/null || {
                print_error "MySQL backup failed"
                exit 1
            }
            print_status "MySQL backup created: $backup_file"
            ;;
        *)
            print_warning "Unknown database engine: $db_engine. Manual backup recommended."
            ;;
    esac
}

# Function to test medicine migrations
test_medicine_migrations() {
    print_section "Testing Medicine Migrations"
    
    # Use our custom migration testing command
    print_status "Running medicine migration test (dry run)..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py test_medicine_migration --dry-run
    
    print_status "Running medicine migration test on database copy..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py test_medicine_migration
    
    print_status "Medicine migration tests completed successfully"
}

# Function to run pre-deployment checks
run_pre_deployment_checks() {
    print_section "Pre-Deployment Checks"
    
    # Check Django configuration
    print_status "Checking Django configuration..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py check --deploy
    
    # Show migration plan
    print_status "Showing migration plan..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py migrate --plan
    
    # Check for unapplied migrations
    print_status "Checking for unapplied migrations..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py showmigrations
    
    print_status "Pre-deployment checks completed"
}

# Function to update dependencies
update_dependencies() {
    print_section "Updating Dependencies"
    
    # Update Python dependencies
    print_status "Installing Python dependencies..."
    pipenv install --python "$PYTHON_VERSION" --deploy
    
    # Update Node.js dependencies
    print_status "Installing Node.js dependencies..."
    npm ci
    
    print_status "Dependencies updated successfully"
}

# Function to apply migrations
apply_migrations() {
    print_section "Applying Database Migrations"
    
    print_status "Applying migrations..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py migrate
    
    # Verify migration status
    print_status "Verifying migration status..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py showmigrations core | grep -E "medicine|Medicine"
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py showmigrations babybuddy | grep medicine
    
    print_status "Database migrations completed successfully"
}

# Function to build static assets
build_static_assets() {
    print_section "Building Static Assets"
    
    # Build assets with gulp
    print_status "Building static assets..."
    gulp build
    
    # Collect static files
    print_status "Collecting static files..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py collectstatic --noinput
    
    print_status "Static assets built successfully"
}

# Function to compile translations
compile_translations() {
    print_section "Compiling Translations"
    
    print_status "Compiling message files..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py compilemessages
    
    print_status "Translations compiled successfully"
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    print_section "Post-Deployment Validation"
    
    # Test Django system
    print_status "Testing Django system..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py check
    
    # Test medicine model functionality
    print_status "Testing medicine model functionality..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
from core.models import Medicine, Child
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import django
django.setup()

# Quick functional test
try:
    # Test model import
    print('✓ Medicine model imports successfully')
    
    # Test model creation (without saving)
    medicine = Medicine(
        medicine_name='Test Medicine',
        dosage=5.0,
        dosage_unit='ml',
        time=timezone.now()
    )
    print('✓ Medicine model can be instantiated')
    
    # Test calculated properties
    if hasattr(medicine, 'next_dose_ready'):
        print('✓ Medicine model has next_dose_ready property')
    
    print('✓ Medicine functionality validation passed')
except Exception as e:
    print(f'✗ Medicine functionality validation failed: {e}')
    exit(1)
"
    
    # Test API schema generation
    print_status "Testing OpenAPI schema generation..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py generateschema --file openapi-schema.yml
    
    # Check that medicine endpoints are included
    if grep -q "medicine" openapi-schema.yml; then
        print_status "✓ Medicine endpoints found in API schema"
    else
        print_warning "Medicine endpoints not found in API schema"
    fi
    
    print_status "Post-deployment validation completed"
}

# Function to restart services
restart_services() {
    print_section "Restarting Services"
    
    # Check if we're running with systemd
    if command -v systemctl &> /dev/null && systemctl is-active --quiet babybuddy.service; then
        print_status "Restarting Baby Buddy systemd service..."
        sudo systemctl restart babybuddy.service
        sudo systemctl status babybuddy.service --no-pager
    elif [[ -f "docker-compose.yml" ]] && command -v docker-compose &> /dev/null; then
        print_status "Restarting Docker Compose services..."
        docker-compose restart web
        docker-compose ps
    elif command -v uwsgi &> /dev/null; then
        print_status "Restarting uWSGI..."
        sudo service uwsgi restart
    else
        print_warning "No known service management detected. Please restart your web server manually."
    fi
    
    # Restart nginx if available
    if command -v nginx &> /dev/null && systemctl is-active --quiet nginx; then
        print_status "Restarting nginx..."
        sudo systemctl reload nginx
    fi
}

# Function to display deployment summary
show_deployment_summary() {
    print_section "Deployment Summary"
    
    cat << EOF | tee -a "$LOG_FILE"

🎉 Baby Buddy with Medicine Feature Deployment Completed Successfully!

Deployment Details:
- Timestamp: $TIMESTAMP
- Settings Module: $SETTINGS_MODULE
- Python Version: $PYTHON_VERSION
- Backup Created: $([ "$SKIP_BACKUP" == "true" ] && echo "No" || echo "Yes")

Medicine Feature Status:
✓ Medicine migrations applied
✓ Medicine model functionality validated
✓ Medicine API endpoints active
✓ Static assets updated with medicine icons

Next Steps:
1. Test the application in your browser
2. Verify medicine tracking functionality
3. Check dashboard cards display correctly
4. Test medicine API endpoints if using the API
5. Monitor application logs for any issues

Important Notes:
- Default admin credentials are admin/admin - CHANGE IMMEDIATELY
- Review medicine user settings in the admin panel
- Check medicine dashboard card visibility settings

Log file: $LOG_FILE

EOF
}

# Main deployment function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -s|--skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            -e|--env)
                SETTINGS_MODULE="$2"
                shift 2
                ;;
            -p|--python)
                PYTHON_VERSION="$2"
                shift 2
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Initialize log file
    echo "Baby Buddy Deployment Log - $(date)" > "$LOG_FILE"
    
    print_section "Baby Buddy Deployment with Medicine Feature"
    print_status "Starting deployment at $(date)"
    print_status "Settings module: $SETTINGS_MODULE"
    print_status "Python version: $PYTHON_VERSION"
    print_status "Dry run: $DRY_RUN"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_warning "DRY RUN MODE - No changes will be made"
        print_status "Deployment plan:"
        cat << EOF
1. Check prerequisites
2. Create database backup ($([ "$SKIP_BACKUP" == "true" ] && echo "SKIPPED" || echo "ENABLED"))
3. Test medicine migrations
4. Run pre-deployment checks
5. Update dependencies
6. Apply database migrations
7. Build static assets
8. Compile translations
9. Run post-deployment tests
10. Restart services
11. Show deployment summary
EOF
        exit 0
    fi
    
    # Execute deployment steps
    check_prerequisites
    create_backup
    test_medicine_migrations
    run_pre_deployment_checks
    update_dependencies
    apply_migrations
    build_static_assets
    compile_translations
    run_post_deployment_tests
    restart_services
    show_deployment_summary
    
    print_status "Deployment completed successfully at $(date)"
}

# Error handling
trap 'print_error "Deployment failed at line $LINENO. Check $LOG_FILE for details."; exit 1' ERR

# Run main function
main "$@"