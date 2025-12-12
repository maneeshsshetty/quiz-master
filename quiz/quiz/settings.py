"""
Django settings for quiz project.

This is the configuration heart of the application.
It tells Django:
1. Where the database is.
2. Which apps are installed.
3. How to handle security.
4. How to format dates/times.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

from pathlib import Path
# BASE_DIR:
# Points to the absolute path of the project root.
# Why? So we can say "look for database file at BASE_DIR + /db.sqlite3" without knowing the full path on deploy.
BASE_DIR = Path(__file__).resolve().parent.parent

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')



# SECURITY CRITICAL SETTINGS

# SECRET_KEY:
# A long random string used for cryptographic signing.
# It signs session cookies (so users can't fake being logged in).
# It generates password reset tokens.
# WARNING: If an attacker gets this, they can take over any user account.
SECRET_KEY = os.getenv('SECRET_KEY')

# DEBUG:
# True: Shows detailed error pages with stack traces. Helpful for dev.
# False: Shows standard 404/500 error pages. Mandatory for production.
# WARNING: Never run with DEBUG=True in production. It leaks sensitive variables.
DEBUG = True

# ALLOWED_HOSTS:
# White-list of domain names this site can serve.
# Why? Prevents "Host Header Attacks" where an attacker spoofs the domain to generate malicious password reset links.
# '*' is unsafe for production but convenient for local dev.
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    # Core framework components
    'django.contrib.admin',       # The admin site
    'django.contrib.auth',        # User authentication system
    'django.contrib.contenttypes', # Tracks all models installed in the project
    'django.contrib.sessions',    # Stores data across requests (e.g. "Who is logged in?")
    'django.contrib.messages',    # "Toast" notifications
    'django.contrib.staticfiles', # Manages CSS/JS files
    
    # Custom apps
    # We must register our 'quiz_master' app so Django finds its models, views, and migrations.
    'quiz_master',
]

# Email Configuration
# Defines how the app talks to the outside world.
  

MIDDLEWARE = [
    # Layered Hooks.
    # Every request passes through this list top-to-bottom.
    # Every response passes through this list bottom-to-top.
    
    'django.middleware.security.SecurityMiddleware',          # Adds security headers (HSTS, XSS protection)
    'django.contrib.sessions.middleware.SessionMiddleware',   # Reads the session cookie -> available as request.session
    'django.middleware.common.CommonMiddleware',              # Normalizes URLs
    'django.middleware.csrf.CsrfViewMiddleware',              # Checks for the anti-hacking token on POST forms
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Reads session -> sets request.user
    'django.contrib.messages.middleware.MessageMiddleware',    # Handles flash messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Prevents site from being embedded in iframes
]

ROOT_URLCONF = 'quiz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], 
        'APP_DIRS': True, # Automatically look for a 'templates' folder inside every installed app.
        'OPTIONS': {
            'context_processors': [
                # Global variables available in every template (e.g. {{ user.username }})
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'quiz.wsgi.application' # The entry point for web servers (like Gunicorn/uWSGI)


# Database
# Using SQLite: A simple file-based database. 
# Pros: No setup, great for dev. Cons: Does not handle high concurrency well.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# Checks new passwords against rules to prevent "password123".
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization

LANGUAGE_CODE = 'en-us'

# We are forcing local time for simplicity in this specific project
# USE_TZ = False means Django stores datetimes as "naive" (no timezone info).
# This avoids confusion when comparing `datetime.now()` with DB values but makes global apps harder.
USE_TZ = False                
TIME_ZONE = "Asia/Kolkata" 

USE_I18N = True
USE_L10N = True

# Static files
# Where to find CSS/JS.
STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' # Use 64-bit integers for IDs (future proofing).

# Auth Redirects
LOGIN_URL = 'login' # If anonymous user hits a protected page, go here.
LOGIN_REDIRECT_URL = 'dashboard' # After successful login, go here.

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
