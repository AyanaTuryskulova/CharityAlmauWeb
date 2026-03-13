from django.conf import settings


def vapid_key(request):
    return {'VAPID_PUBLIC_KEY': getattr(settings, 'VAPID_PUBLIC_KEY', '')}
