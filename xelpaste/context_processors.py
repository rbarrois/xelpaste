from django.conf import settings


def xelpaste_settings(request):
    return {
        'DPASTE_BASE_URL': settings.DPASTE_BASE_URL,
        'DPASTE_DOMAIN': settings.DPASTE_DOMAIN,
    }
