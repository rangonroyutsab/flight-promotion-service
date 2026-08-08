import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Fail fast if DJANGO_SECRET_KEY is not set — never silently use an insecure default
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.promotions",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "flight_promotions"),
        "USER": os.environ.get("POSTGRES_USER", "flight_app"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": int(os.environ.get("POSTGRES_PORT", "5432")),
    }
}


if DEBUG and (
    not os.environ.get("POSTGRES_HOST")
    or os.environ.get("USE_SQLITE", "").lower() == "true"
):
    # Fallback to sqlite if postgres env isn't provided locally and we are in debug mode
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = os.environ.get("TZ", "Asia/Dhaka")

USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apps.promotions.api.exceptions.custom_exception_handler"
}


# Elasticsearch Settings
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ELASTICSEARCH_USERNAME = os.environ.get("ELASTICSEARCH_USERNAME", "elastic")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD", "")
ELASTICSEARCH_INDEX = os.environ.get(
    "ELASTICSEARCH_INDEX", "kibana_sample_data_flights"
)

# MinIO Settings
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "flight-promotions")

# AI Settings
AI_PROVIDER = os.environ.get("AI_PROVIDER", "mock")
AI_MODEL = os.environ.get("AI_MODEL", "mock-model")
AI_API_KEY = os.environ.get("AI_API_KEY", "")
GEMINI_API_URL = os.environ.get("GEMINI_API_URL", "")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("DEFAULT_TIMEOUT_SECONDS", "10"))
AI_MAX_RETRIES = int(os.environ.get("AI_MAX_RETRIES", "3"))
# Centralized retry limit used by all external clients (MinIO, Elasticsearch, Gemini)
DEFAULT_MAX_RETRIES = int(os.environ.get("DEFAULT_MAX_RETRIES", "3"))
