# Баннеры для главной и разделов (по дизайну)

--- Две папки со статикой ---
• core/static/onboarding/ — ИСХОДНИКИ. Сюда добавляйте и редактируйте картинки.
• staticfiles/onboarding/ — сюда Django копирует статику командой collectstatic.
  Не редактируйте staticfiles вручную: при следующем collectstatic изменения затрутся.
  Всегда кладите новые файлы в core/static/onboarding/.

--- Имена файлов в onboarding ---
Категории и герои: slide1.png, slide2.png, slide3.png
Футер: about us.png (О нас), about platform.png (О платформе), almauni.png (AlmaUni)
Лого: Charity Almau 2 6.png (в onboarding). О нас (портрет): about us portret.png

Для продакшена: python manage.py collectstatic --noinput
