from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError


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
        email = ''
        if sociallogin.account.extra_data:
            email = (
                sociallogin.account.extra_data.get('mail') or
                sociallogin.account.extra_data.get('userPrincipalName') or
                ''
            )
        if not email and sociallogin.user:
            email = sociallogin.user.email or ''

        if email and not email.lower().endswith(f'@{ALLOWED_DOMAIN}'):
            raise ValidationError(
                f'Доступ только для пользователей @{ALLOWED_DOMAIN}'
            )
