#!/bin/bash

# Medicine Feature Configuration Management Script
# This script helps configure the medicine feature settings and validates the setup
# Author: Claude Code Assistant
# Version: 1.0

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SETTINGS_MODULE="babybuddy.settings.production"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Medicine Feature Configuration Management Script

OPTIONS:
    -h, --help              Show this help message
    -e, --env ENV          Environment settings module (default: $SETTINGS_MODULE)
    -c, --check            Check current medicine configuration
    -s, --setup            Set up medicine feature with default settings
    -t, --test             Test medicine functionality
    -v, --validate         Validate medicine configuration

EXAMPLES:
    $0 --check            # Check current configuration
    $0 --setup            # Set up with defaults
    $0 --test             # Test medicine functionality
    $0 --validate         # Full validation

EOF
}

# Function to check current configuration
check_configuration() {
    print_section "Medicine Feature Configuration Check"
    
    # Check if medicine model exists
    print_status "Checking medicine model..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
import django
django.setup()
from core.models import Medicine
print('✓ Medicine model is available')
"
    
    # Check migrations
    print_status "Checking migrations..."
    migration_status=$(DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py showmigrations core | grep -E "medicine|Medicine" || echo "None found")
    echo "Medicine migrations: $migration_status"
    
    # Check user settings
    print_status "Checking user settings..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
import django
django.setup()
from babybuddy.models import Settings
settings_fields = [f.name for f in Settings._meta.fields]
if 'medicine_card_hide_threshold' in settings_fields:
    print('✓ Medicine user settings are configured')
else:
    print('✗ Medicine user settings not found')
"
    
    # Check API endpoints
    print_status "Checking API configuration..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
import django
django.setup()
from django.urls import reverse
try:
    url = reverse('api:medicine-list')
    print(f'✓ Medicine API endpoint available at {url}')
except:
    print('✗ Medicine API endpoint not configured')
"
    
    # Check dashboard cards
    print_status "Checking dashboard cards..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
import django
django.setup()
from dashboard.templatetags.cards import card_medicine_last, card_medicine_due
print('✓ Medicine dashboard cards are available')
"
    
    # Check reports
    print_status "Checking reports..."
    report_files=['reports/graphs/medicine_frequency.py', 'reports/graphs/medicine_intervals.py']
    for report in report_files:
        if [[ -f "$report" ]]; then
            echo "✓ $report exists"
        else
            echo "✗ $report not found"
        fi
    done
}

# Function to set up medicine feature
setup_medicine_feature() {
    print_section "Setting Up Medicine Feature"
    
    # Apply migrations if needed
    print_status "Ensuring migrations are applied..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py migrate
    
    # Create default user settings
    print_status "Setting up default user settings..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
import django
django.setup()
from django.contrib.auth.models import User
from babybuddy.models import Settings
from datetime import timedelta

# Ensure all users have medicine settings
for user in User.objects.all():
    settings, created = Settings.objects.get_or_create(user=user)
    if not settings.medicine_card_hide_threshold:
        settings.medicine_card_hide_threshold = timedelta(hours=24)
        settings.save()
        print(f'✓ Updated settings for user: {user.username}')
    else:
        print(f'✓ User {user.username} already has medicine settings')
"
    
    # Rebuild static assets
    print_status "Rebuilding static assets..."
    gulp build
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py collectstatic --noinput
    
    # Generate API schema
    print_status "Updating API schema..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python manage.py generateschema --file openapi-schema.yml
    
    print_status "Medicine feature setup completed"
}

# Function to test medicine functionality
test_medicine_functionality() {
    print_section "Testing Medicine Functionality"
    
    print_status "Running comprehensive medicine tests..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
import django
django.setup()
from core.models import Medicine, Child
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json

# Test model functionality
print('Testing Medicine model...')

# Get or create a test child
try:
    child = Child.objects.first()
    if not child:
        # Create a test child
        child = Child.objects.create(
            first_name='Test',
            last_name='Child',
            birth_date=timezone.localdate()
        )
        print('✓ Created test child')
    else:
        print('✓ Using existing child for tests')
        
    # Test medicine creation
    medicine = Medicine.objects.create(
        child=child,
        medicine_name='Test Medicine',
        dosage=5.0,
        dosage_unit='ml',
        time=timezone.now(),
        next_dose_interval=timedelta(hours=4),
        notes='Test medicine entry'
    )
    print('✓ Medicine creation successful')
    
    # Test calculated properties
    print(f'✓ Next dose time: {medicine.next_dose_time}')
    print(f'✓ Next dose ready: {medicine.next_dose_ready}')
    
    # Test validation
    medicine.full_clean()
    print('✓ Medicine validation passed')
    
    # Test tags
    medicine.tags.add('test', 'configuration')
    print(f'✓ Tags added: {list(medicine.tags.names())}')
    
    # Test string representation
    print(f'✓ String representation: {str(medicine)}')
    
    # Test deletion
    medicine_id = medicine.id
    medicine.delete()
    print(f'✓ Medicine {medicine_id} deleted successfully')
    
    print('✓ All medicine model tests passed')
    
except Exception as e:
    print(f'✗ Medicine model test failed: {e}')
    exit(1)
"
    
    # Test dashboard cards
    print_status "Testing dashboard cards..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
import django
django.setup()
from django.template import Context, Template
from django.contrib.auth.models import User
from core.models import Child

# Test card template tags
try:
    child = Child.objects.first()
    if child:
        # Test medicine last card
        template = Template('{% load cards %}{% card_medicine_last child %}')
        context = Context({'child': child})
        output = template.render(context)
        print('✓ Medicine last card renders successfully')
        
        # Test medicine due card
        template = Template('{% load cards %}{% card_medicine_due child %}')
        output = template.render(context)
        print('✓ Medicine due card renders successfully')
    else:
        print('! No children available for card testing')
        
except Exception as e:
    print(f'✗ Dashboard card test failed: {e}')
"
    
    # Test API endpoints
    print_status "Testing API endpoints..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
import django
django.setup()
from django.test import Client
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

try:
    client = Client()
    
    # Get or create test user with token
    user = User.objects.first()
    if user:
        token, created = Token.objects.get_or_create(user=user)
        
        # Test medicine list endpoint
        response = client.get('/api/medicine/', HTTP_AUTHORIZATION=f'Token {token.key}')
        if response.status_code == 200:
            print('✓ Medicine API list endpoint accessible')
        else:
            print(f'! Medicine API list returned status {response.status_code}')
    else:
        print('! No users available for API testing')
        
except Exception as e:
    print(f'✗ API endpoint test failed: {e}')
"
    
    print_status "Medicine functionality tests completed"
}

# Function to validate configuration
validate_configuration() {
    print_section "Medicine Feature Validation"
    
    print_status "Running full validation suite..."
    
    # Check all required files exist
    required_files=(
        "core/models.py"
        "core/forms.py"
        "core/views.py"
        "core/templates/core/medicine_form.html"
        "core/templates/core/medicine_list.html"
        "api/serializers.py"
        "api/views.py"
        "dashboard/templatetags/cards.py"
        "dashboard/templates/cards/medicine_last.html"
        "dashboard/templates/cards/medicine_due.html"
        "reports/graphs/medicine_frequency.py"
        "reports/graphs/medicine_intervals.py"
    )
    
    print_status "Checking required files..."
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            echo "✓ $file"
        else
            echo "✗ $file (missing)"
        fi
    done
    
    # Check database schema
    print_status "Validating database schema..."
    DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE" pipenv run python -c "
import django
django.setup()
from django.db import connection
from core.models import Medicine

# Check if medicine table exists
with connection.cursor() as cursor:
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='core_medicine'\")
    result = cursor.fetchone()
    if result:
        print('✓ Medicine table exists in database')
        
        # Check for indexes
        cursor.execute('PRAGMA index_list(core_medicine)')
        indexes = cursor.fetchall()
        index_names = [idx[1] for idx in indexes]
        
        expected_indexes = [
            'medicine_child_time_idx',
            'medicine_next_dose_time_idx',
            'medicine_duplicate_check_idx'
        ]
        
        for idx in expected_indexes:
            if idx in index_names:
                print(f'✓ Index {idx} exists')
            else:
                print(f'! Index {idx} missing')
    else:
        print('✗ Medicine table not found in database')
"
    
    # Check API schema
    print_status "Validating API schema..."
    if [[ -f "openapi-schema.yml" ]]; then
        if grep -q "medicine" openapi-schema.yml; then
            print "✓ Medicine endpoints found in API schema"
        else
            print "! Medicine endpoints not found in API schema"
        fi
    else
        print "! OpenAPI schema file not found"
    fi
    
    # Check static assets
    print_status "Checking static assets..."
    static_files=(
        "babybuddy/static/babybuddy/font/babybuddy.woff2"
        "babybuddy/static/babybuddy/css/app.css"
        "babybuddy/static/babybuddy/js/app.js"
    )
    
    for file in "${static_files[@]}"; do
        if [[ -f "$file" ]]; then
            echo "✓ $file"
        else
            echo "! $file (may need rebuild)"
        fi
    done
    
    print_status "Validation completed"
}

# Main function
main() {
    # Parse command line arguments
    local action=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -e|--env)
                SETTINGS_MODULE="$2"
                shift 2
                ;;
            -c|--check)
                action="check"
                shift
                ;;
            -s|--setup)
                action="setup"
                shift
                ;;
            -t|--test)
                action="test"
                shift
                ;;
            -v|--validate)
                action="validate"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    if [[ -z "$action" ]]; then
        print_error "No action specified. Use --help for usage information."
        exit 1
    fi
    
    print_section "Medicine Feature Configuration Management"
    print_status "Settings module: $SETTINGS_MODULE"
    
    case "$action" in
        check)
            check_configuration
            ;;
        setup)
            setup_medicine_feature
            ;;
        test)
            test_medicine_functionality
            ;;
        validate)
            validate_configuration
            ;;
    esac
    
    print_status "Operation completed successfully"
}

# Error handling
trap 'print_error "Configuration script failed at line $LINENO"; exit 1' ERR

# Run main function
main "$@"