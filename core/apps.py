import logging
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


def _preload_image_classifier():
    """Предзагрузка модели в фоне, чтобы первый запрос по фото не ждал 1–2 минуты."""
    try:
        from core.services.image_autofill import _classifier
        _classifier()
        logger.info("Image classifier (ViT) preloaded.")
    except Exception:
        logger.exception("Image classifier preload failed (will load on first use).")


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    def ready(self):
        # Модель тяжёлая: загружаем в фоне при старте, чтобы определение по фото не «висело» при первом запросе
        threading.Thread(target=_preload_image_classifier, daemon=True).start()

