from django import template
from django.conf import settings

import fatanalysis

register = template.Library()


@register.simple_tag
def fatanalysis_version() -> str:
    """Returns the package version."""
    return getattr(fatanalysis, "__version__", "1.0.0")


@register.simple_tag
def fatanalysis_app_name() -> str:
    """Returns the configured or default app name."""
    return getattr(settings, "FATANALYSIS_APP_NAME", "FAT Analysis")
