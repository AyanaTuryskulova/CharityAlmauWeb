import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")  # не падает, если .env нет

# --- Безопасность и базовые ---
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set via environment")

# ALLOWED_HOSTS и CSRF_TRUSTED_ORIGINS читаем из env (через запятую)
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# --- Приложения ---
INSTALLED_APPS = [
    # Django apps...
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",        # важно для allauth

    # 3rd-party
    "whitenoise.runserver_nostatic",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.microsoft",

    # твои приложения
    "core",
]

SITE_ID = int(os.getenv("SITE_ID", "1"))

# --- Middleware (WhiteNoise сразу после Security) ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # статика
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- Шаблоны/авторизация ---
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/onboarding/"  # сделаем простую вью ниже
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_SIGNUP_ENABLED = False
SOCIALACCOUNT_LOGIN_ON_GET = True

MS_TENANT = os.getenv("MS_TENANT", "common")
SOCIALACCOUNT_PROVIDERS = {
    "microsoft": {
        "TENANT": MS_TENANT,
        "APP": {
            "client_id": os.getenv("MS_CLIENT_ID", ""),
            "secret": os.getenv("MS_CLIENT_SECRET", ""),
        },
    }
}

# --- База данных ---
DATABASES = {
    "default": {
        "ENGINE": os.getenv("SQL_ENGINE", "django.db.backends.mysql"),
        "NAME": os.getenv("SQL_DB", ""),
        "USER": os.getenv("SQL_USER", ""),
        "PASSWORD": os.getenv("SQL_PASSWORD", ""),
        "HOST": os.getenv("SQL_HOST", "127.0.0.1"),
        "PORT": os.getenv("SQL_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# --- Статика/медиа ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
SECURE_SSL_REDIRECT = False   # редирект делает Nginx
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# --- Прод-харденинг (включай при DEBUG=False) ---
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = False
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# --- Логирование (минимум) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # ⬅️ важно
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# === Django entrypoints (добавь рядом с BASE_DIR и т.п.) ===
ROOT_URLCONF = "CharityAlmaWeb.urls"     # <-- имя_проекта.urls
WSGI_APPLICATION = "CharityAlmaWeb.wsgi.application"
ASGI_APPLICATION = "CharityAlmaWeb.asgi.application"

# === allauth: новые параметры вместо устаревших ===
# было:
# ACCOUNT_AUTHENTICATION_METHOD = "username_email"
# ACCOUNT_EMAIL_REQUIRED = True

# стало:
ACCOUNT_LOGIN_METHODS = {"username", "email"}   # можно {"email"} или {"username"} — на твой выбор
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]

# остальное можно оставить как было
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_SIGNUP_ENABLED = False
SOCIALACCOUNT_LOGIN_ON_GET = True
