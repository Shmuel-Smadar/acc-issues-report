import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-secret")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "web.middleware.EnsureForgeAuthMiddleware",
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
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Jerusalem"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FORGE_CLIENT_ID = env("FORGE_CLIENT_ID")
FORGE_CLIENT_SECRET = env("FORGE_CLIENT_SECRET")
FORGE_CALLBACK_URL = env("FORGE_CALLBACK_URL")
FORGE_SCOPE = env(
    "FORGE_SCOPE",
    default="account:read data:read bucket:read user:read"
)
ACC_PROJECT_ID = env("ACC_PROJECT_ID", default="")
FORGE_BASE_URL = env("FORGE_BASE_URL", default="https://developer.api.autodesk.com")
ACC_ACCOUNT_ID = env("ACC_ACCOUNT_ID", default="")
REPORT_OUTPUT_DIR = env("REPORT_OUTPUT_DIR", default=str(BASE_DIR / "reports"))
TARGET_PROJECT_NAME = env("TARGET_PROJECT_NAME", default="DEV TASK 1 Project")

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
APP_LOG_FILE = LOG_DIR / "app.log"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "kv": {
            "format": "%(asctime)s level=%(levelname)s logger=%(name)s %(message)s"
        }
    },
    "handlers": {
        "app_file": {
            "class": "logging.FileHandler",
            "filename": str(APP_LOG_FILE),
            "formatter": "kv",
            "level": "INFO",
            "encoding": "utf-8",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["null"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["null"],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}
