from django import template
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.filter(name='user_avatar_url')
def user_avatar_url(user):
    """URL аватара из профиля или пустая строка, если профиля/фото нет."""
    if user is None:
        return ''
    try:
        avatar = user.profile.avatar
        if avatar:
            return avatar.url
    except ObjectDoesNotExist:
        pass
    return ''
