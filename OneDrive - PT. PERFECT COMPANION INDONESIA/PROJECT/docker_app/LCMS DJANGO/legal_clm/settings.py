import os
from pathlib import Path
from decouple import config

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-default-key-change-me')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    # Modern admin theme
    'unfold',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third party
    'django_celery_beat',
    
    # Local apps
    'contracts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'legal_clm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'legal_clm.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='legal_clm_db'),
        'USER': config('DB_USER', default='clm_user'),
        'PASSWORD': config('DB_PASSWORD', default='clm_pass123'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@legalclm.com')

# Site Configuration
SITE_URL = config('SITE_URL', default='http://localhost')

# Security Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Login URLs
LOGIN_URL = 'login'

# ======================
# UNFOLD ADMIN CONFIGURATION
# ======================
UNFOLD = {
    "SITE_HEADER": "Legal CLM - Admin Dashboard",
    "SITE_TITLE": "Legal CLM",
    "SITE_URL": "/admin/",
    "LOGO": None,
    "FAVICON": None,
    "COLORS": {
        "primary": {
            "50": "f0f9ff",
            "100": "e0f2fe",
            "200": "bae6fd",
            "300": "7dd3fc",
            "400": "38bdf8",
            "500": "0ea5e9",
            "600": "0284c7",
            "700": "0369a1",
            "800": "075985",
            "900": "0c3d66",
        },
        "accent": {
            "50": "f5f3ff",
            "100": "ede9fe",
            "200": "ddd6fe",
            "300": "c4b5fd",
            "400": "a78bfa",
            "500": "8b5cf6",
            "600": "7c3aed",
            "700": "6d28d9",
            "800": "5b21b6",
            "900": "4c1d95",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "📋 Contract Management",
                "items": [
                    {
                        "title": "Contracts",
                        "icon": "description",
                        "link": "/admin/contracts/contract/",
                    },
                    {
                        "title": "Participants",
                        "icon": "person",
                        "link": "/admin/contracts/contractparticipant/",
                    },
                    {
                        "title": "Contract Data",
                        "icon": "storage",
                        "link": "/admin/contracts/contractdata/",
                    },
                ],
            },
            {
                "title": "⚙️ Configuration",
                "items": [
                    {
                        "title": "Company Profile",
                        "icon": "business",
                        "link": "/admin/contracts/companyprofile/",
                    },
                    {
                        "title": "Role Permissions",
                        "icon": "shield",
                        "link": "/admin/contracts/contractrolepermission/",
                    },
                    {
                        "title": "Business Documents",
                        "icon": "file_copy",
                        "link": "/admin/contracts/businessentitydocument/",
                    },
                ],
            },
            {
                "title": "👥 System",
                "items": [
                    {
                        "title": "Users",
                        "icon": "account_circle",
                        "link": "/admin/auth/user/",
                    },
                    {
                        "title": "Groups",
                        "icon": "groups",
                        "link": "/admin/auth/group/",
                    },
                ],
            },
            {
                "title": "📝 Logs",
                "items": [
                    {
                        "title": "Audit Logs",
                        "icon": "assignment",
                        "link": "/admin/contracts/auditlog/",
                    },
                ],
            },
        ],
    },
}
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
