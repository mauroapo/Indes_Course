"""
Django settings for ong_platform project.
"""

from pathlib import Path
import os
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

#ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


ALLOWED_HOSTS  = [
    "lunar.salesforcedevhelp.com",
    "solar.salesforcedevhelp.com",
    "salesforcedevhelp.com",
    "www.salesforcedevhelp.com",
    "lms.appbemestar.com.br",
    "appbemestar.com.br",

    "162.240.98.188",
    "162.240.98.188:8001",
    "https://lms.indes.org.br",
    "lms.indes.org.br",
    "https://appbemestar.com.br",
    "http://80.91.86.135",
    "http://lunar.salesforcedevhelp.com",
    "https://lunar.salesforcedevhelp.com",
    "http://salesforcedevhelp.com",
    "https://salesforcedevhelp.com",
    "http://127.0.0.1:6000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]




# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    # Project apps
    'accounts',
    'courses',
    'cart',
    'checkout',
    'orgs',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AuthRequiredMiddleware',
]

ROOT_URLCONF = 'ong_platform.urls'

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
                'cart.context_processors.cart_item_count',
                'core.context_processors.asset_version',
            ],
        },
    },
]

WSGI_APPLICATION = 'ong_platform.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='ong_platform'),
        'USER': config('DB_USER', default='ong_user'),
        'PASSWORD': config('DB_PASSWORD', default='ong_password'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@ongplatform.com')

# Course Area Integration
COURSE_AREA_BASE_URL = config('COURSE_AREA_BASE_URL', default='http://localhost:7000')
COURSE_TOKEN_EXPIRY_MINUTES = 15

# Email Verification
EMAIL_VERIFICATION_EXPIRY = config('EMAIL_VERIFICATION_EXPIRY', default=10, cast=int)

# Resend Email Service
RESEND_API_KEY = config('RESEND_API_KEY', default='')
RESEND_FROM_EMAIL = config('RESEND_FROM_EMAIL', default='noreply@ongplatform.com')

# Password Reset
PASSWORD_RESET_EXPIRY_MINUTES = config('PASSWORD_RESET_EXPIRY_MINUTES', default=10, cast=int)

# Login URL
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/home/'
LOGOUT_REDIRECT_URL = '/login/'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://162.240.98.188",
    "https://162.240.98.188:8001",
    "https://lms.indes.org.br",
    "https://appbemestar.com.br",
    "http://80.91.86.135",
    "http://lunar.salesforcedevhelp.com",
    "https://lunar.salesforcedevhelp.com",
    "https://solar.salesforcedevhelp.com",
    "https://www.salesforcedevhelp.com",
    "http://salesforcedevhelp.com",
    "https://salesforcedevhelp.com",
    "http://127.0.0.1:6000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]

# Security settings
CSRF_TRUSTED_ORIGINS = [
    "https://162.240.98.188",
    "https://162.240.98.188:8001",
    "https://lms.appbemestar.com.br",
    "https://appbemestar.com.br",
    "https://lms.indes.org.br",
    "https://lms.indes.org.br",
    "http://80.91.86.135",
    "http://lunar.salesforcedevhelp.com",
    "https://lunar.salesforcedevhelp.com",
    "https://solar.salesforcedevhelp.com",
    "http://solar.salesforcedevhelp.com",
    "https://www.salesforcedevhelp.com",
    "http://salesforcedevhelp.com",
    "https://salesforcedevhelp.com",
    "http://127.0.0.1:6000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]

# Cloudflare proxy settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
