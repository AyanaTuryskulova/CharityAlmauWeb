import logging

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.core.exceptions import ValidationError
from django.shortcuts import render

logger = logging.getLogger(__name__)

ALLOWED_DOMAIN = 'almau.edu.kz'


class AlmauAccountAdapter(DefaultAccountAdapter):
    """Запрещает ручную регистрацию с email не из @almau.edu.kz."""

    def clean_email(self, email):
        email = super().clean_email(email)
        if email and not email.lower().endswith(f'@{ALLOWED_DOMAIN}'):
            raise ValidationError(
                f'Регистрация доступна только для почт @{ALLOWED_DOMAIN}'
            )
        return email


class AlmauSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Запрещает вход через Microsoft с email не из @almau.edu.kz."""

    def pre_social_login(self, request, sociallogin):
        extra = sociallogin.account.extra_data or {}
        email = extra.get('mail') or extra.get('userPrincipalName') or ''

        if not email and sociallogin.user:
            email = sociallogin.user.email or ''

        logger.info(
            "Microsoft social login: email=%s, provider=%s, uid=%s, extra_keys=%s",
            email,
            sociallogin.account.provider,
            sociallogin.account.uid,
            list(extra.keys()),
        )

        if email and not email.lower().endswith(f'@{ALLOWED_DOMAIN}'):
            logger.warning("Rejected social login for %s (not @%s)", email, ALLOWED_DOMAIN)
            raise ImmediateHttpResponse(
                render(request, 'socialaccount/login_error.html', {
                    'error_message': f'Доступ только для пользователей @{ALLOWED_DOMAIN}. '
                                     f'Вы вошли как {email}.'
                })
            )

    def on_authentication_error(self, request, provider_id, error=None,
                                exception=None, extra_context=None):
        logger.error(
            "Social auth error: provider=%s, error=%s, exception=%s, extra=%s",
            provider_id, error, exception, extra_context,
        )
        return super().on_authentication_error(
            request, provider_id, error=error,
            exception=exception, extra_context=extra_context,
        )
