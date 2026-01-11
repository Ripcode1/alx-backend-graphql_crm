"""
Django Settings Configuration for CRM Cron Jobs
Add these configurations to your crm/settings.py file
"""

# ============================================================================
# INSTALLED APPS - Add django_crontab to your INSTALLED_APPS
# ============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'graphene_django',
    'django_crontab',  # <-- Add this for django-crontab support
    'django_celery_beat',  # <-- Add this for Celery Beat support
    
    # Your apps
    'crm',
]

# ============================================================================
# GRAPHENE CONFIGURATION - For GraphQL support
# ============================================================================

GRAPHENE = {
    'SCHEMA': 'crm.schema.schema',
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware',
    ],
}

# ============================================================================
# CRON JOBS CONFIGURATION - Define all scheduled tasks
# ============================================================================

CRONJOBS = [
    # Task 2: Heartbeat logger - runs every 5 minutes
    # Cron format: */5 * * * * = every 5 minutes
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    
    # Task 3: Update low stock products - runs every 12 hours
    # Cron format: 0 */12 * * * = every 12 hours (at :00 minutes)
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]

# ============================================================================
# CRONTAB ADDITIONAL SETTINGS (Optional but recommended)
# ============================================================================

# Lock jobs to prevent overlapping executions
CRONTAB_LOCK_JOBS = True

# Command prefix (useful if you need to activate virtual environment)
# CRONTAB_COMMAND_PREFIX = 'source /path/to/venv/bin/activate && '

# Specify the command suffix (useful for logging)
CRONTAB_COMMAND_SUFFIX = '>> /tmp/django_cron.log 2>&1'

# ============================================================================
# LOGGING CONFIGURATION (Optional but recommended for debugging)
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/tmp/crm_django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'crm': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django_crontab': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# TIMEZONE SETTINGS (Important for cron jobs)
# ============================================================================

# Make sure you have the correct timezone set
USE_TZ = True
TIME_ZONE = 'UTC'  # Change this to your timezone, e.g., 'America/New_York'

# ============================================================================
# CELERY CONFIGURATION - For asynchronous task processing
# ============================================================================

# Celery Configuration Options
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}

# ============================================================================
# INSTRUCTIONS FOR USING DJANGO-CRONTAB
# ============================================================================

"""
After adding these settings, run the following commands:

1. Add cron jobs to system crontab:
   python manage.py crontab add

2. Show currently active cron jobs:
   python manage.py crontab show

3. Remove all cron jobs from system crontab:
   python manage.py crontab remove

4. Test individual cron functions manually:
   python manage.py shell
   >>> from crm.cron import log_crm_heartbeat, update_low_stock
   >>> log_crm_heartbeat()
   >>> update_low_stock()
"""
