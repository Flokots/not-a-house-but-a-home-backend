from .settings import *
import dj_database_url

# Production-specific settings
DEBUG = False

# Railway provides DATABASE_URL automatically
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Production-only allowed hosts
ALLOWED_HOSTS = [
    '.railway.app',  # Railway backend domain
    '.vercel.app',   # If you want to allow any Vercel domain (optional)
]

# Production CORS - only your frontend
CORS_ALLOWED_ORIGINS = [
    "https://nahbah-frontend.vercel.app",
    # Railway backend URL will be added later when we get it
]

CSRF_TRUSTED_ORIGINS = [
    "https://nahbah-frontend.vercel.app",
    # Railway backend URL will be added later
]

# Static files handling for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Production frontend URL
FRONTEND_URL = "https://nahbah-frontend.vercel.app"

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'