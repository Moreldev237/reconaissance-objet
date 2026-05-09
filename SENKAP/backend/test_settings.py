# Minimal settings override for running Django tests without external env vars.

from backend.tontine.settings import *  # noqa: F403


# Fix ROOT_URLCONF import when running from this repo layout.
ROOT_URLCONF = "backend.tontine.urls"


# Ensure apps are importable when running from /home/morel/SENKAP.
# The base settings refer to 'authentification' and 'welcome' as top-level apps,
# but in this repository they live under backend/.
INSTALLED_APPS = [
("backend." + app) if app in {"authentification", "welcome"} else app

    for app in INSTALLED_APPS
]


# Use in-memory sqlite for reliability in CI/dev.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# Avoid external email configuration during tests.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "test@example.com"

