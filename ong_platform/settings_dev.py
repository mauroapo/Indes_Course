"""
Local development settings for Indes Portal.

Production keeps using ``ong_platform.settings`` (PostgreSQL, DEBUG off).
Run the project locally with::

    python manage.py runserver 0.0.0.0:9000 --settings=ong_platform.settings_dev

This module only *overrides* a few values; everything else (apps, templates,
middleware, i18n, static/media paths, production database config) is inherited
unchanged from ``settings.py``.
"""

from .settings import *  # noqa: F401,F403  (intentional wildcard re-export)

# ---------------------------------------------------------------------------
# Debug / hosts
# ---------------------------------------------------------------------------
DEBUG = True

# settings.py hardcodes production domains, including entries like
# "http://127.0.0.1:9000" which never match because Django compares the host
# *without* the port. Keep local development reachable.
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver']

# ---------------------------------------------------------------------------
# Database: local SQLite file instead of PostgreSQL
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

# ---------------------------------------------------------------------------
# Local extras (email goes to the console, no real delivery)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Slug-less local usage: allow the Django test client and any local port.
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:9000',
    'http://127.0.0.1:9000',
]