from pathlib import Path
from datetime import timedelta
from decouple import config

# ────────────────────────────────────────────────────────────────
# Base Directories
# ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ────────────────────────────────────────────────────────────────
# Security / Secret Key
# ────────────────────────────────────────────────────────────────
SECRET_KEY = config(
    "DJANGO_SECRET_KEY",
    default="b^ygeo-d4=^op$+&)l%gn8eph7f)u+28hb-dud!=8%zhi**g#5",
)

# ────────────────────────────────────────────────────────────────
# Installed Applications
# ────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "corsheaders",
    "ninja",
    "ninja_jwt",

    # Internal Apps
    "core",
]

# ────────────────────────────────────────────────────────────────
# Middleware
# ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",

    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ────────────────────────────────────────────────────────────────
# URL / WSGI / ASGI
# ────────────────────────────────────────────────────────────────
ROOT_URLCONF = "mainProj.urls"
WSGI_APPLICATION = "mainProj.wsgi.application"
ASGI_APPLICATION = "mainProj.asgi.application"

# ────────────────────────────────────────────────────────────────
# Templates
# ────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ────────────────────────────────────────────────────────────────
# Password Validation
# ────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ────────────────────────────────────────────────────────────────
# Internationalization
# ────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Accra"
USE_I18N = True
USE_TZ = True

# ────────────────────────────────────────────────────────────────
# Static / Media Files
# ────────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ────────────────────────────────────────────────────────────────
# Primary Key
# ────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ────────────────────────────────────────────────────────────────
# Django Ninja JWT Configuration
# ────────────────────────────────────────────────────────────────
NINJA_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

DJANGO_CELERY_RESULTS_TASK_ID_MAX_LENGTH=191
