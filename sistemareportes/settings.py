# settings.py — listo para Render.com
from pathlib import Path
import os
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad / Debug ---
DEBUG = config("DEBUG", default=False, cast=bool)

# Usa SECRET_KEY desde env (no dejes hardcode).
SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-secret-not-for-prod")

# ALLOWED_HOSTS y CSRF en Render
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOST:
    ALLOWED_HOSTS = [RENDER_HOST, "localhost", "127.0.0.1"]
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_HOST}"]
else:
    # Para desarrollo local
    ALLOWED_HOSTS = ["*"]

# --- Apps ---
INSTALLED_APPS = [
    # Apps propias
    "proyectos",
    "estatus",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# --- Middleware ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Whitenoise para estáticos en producción
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sistemareportes.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sistemareportes.wsgi.application"

# --- Base de datos (Render: usa DATABASE_URL) ---
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default="postgres://user:pass@localhost:5432/db"),
        conn_max_age=600,
        ssl_require=True,
    )
}



# --- Passwords ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalización ---
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Primarias por defecto ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Proxy/HTTPS en Render ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
