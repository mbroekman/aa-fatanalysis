INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'esi',
    'eveuniverse',
    'allianceauth',
    'allianceauth.authentication',
    'allianceauth.eveonline',
    'fatanalysis',
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
SECRET_KEY = 'dummy'
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
