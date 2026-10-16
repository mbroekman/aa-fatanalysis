import os
import tempfile

import fakeredis

INSTALLED_APPS = [
    "allianceauth",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "esi",
    "eveuniverse",
    "allianceauth.framework",
    "allianceauth.authentication",
    "allianceauth.eveonline",
    "allianceauth.groupmanagement",
    "allianceauth.notifications",
    "allianceauth.thirdparty.navhelper",
    "allianceauth.menu",
    "allianceauth.theme",
    "allianceauth.theme.darkly",
    "allianceauth.custom_css",
    "sri",
    "fatanalysis",
]

SRI_ALGORITHM = "sha512"

STATIC_URL = "/static/"

STATIC_ROOT = os.path.join(tempfile.gettempdir(), "fatanalysis_test_static")
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "fatanalysis.tests.test_urls"

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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

SECRET_KEY = "dummy_secret_key_for_testing"
DEFAULT_THEME = "allianceauth.theme.darkly.auth_hooks.DarklyThemeHook"
SITE_NAME = "TestAuth"
SITE_URL = "http://localhost:8000"
LOGIN_TOKEN_SCOPES = ["publicData"]
ESI_API_URL = "https://esi.evetech.net/"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CONNECTION_POOL_KWARGS": {
                "connection_class": fakeredis.FakeRedisConnection,
            },
        },
    }
}

LOGIN_URL = "/account/login/"
