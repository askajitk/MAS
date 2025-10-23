from .settings import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
# Generate a new secret key for production
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'CHANGE-THIS-TO-A-RANDOM-SECRET-KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Add your PythonAnywhere domain
ALLOWED_HOSTS = ['yourusername.pythonanywhere.com', 'localhost', '127.0.0.1']

# Database - Use MySQL on PythonAnywhere (free tier includes MySQL)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'yourusername$mas',
#         'USER': 'yourusername',
#         'PASSWORD': 'your-mysql-password',
#         'HOST': 'yourusername.mysql.pythonanywhere-services.com',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         }
#     }
# }

# For starting with SQLite (easier), keep the default SQLite database
# You can migrate to MySQL later if needed

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# For development/testing on PythonAnywhere, you might want to set these to False initially
# CSRF_COOKIE_SECURE = False
# SESSION_COOKIE_SECURE = False
# SECURE_SSL_REDIRECT = False
