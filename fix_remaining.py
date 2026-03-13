import pathlib

BASE = pathlib.Path(__file__).resolve().parent

# requests.html fixes
r = BASE / 'core/templates/requests.html'
text = r.read_text(encoding='utf-8')
text = text.replace(
    '<span class="req-card__label">Продавец:</span>',
    '<span class="req-card__label">{% trans "Продавец:" %}</span>')
text = text.replace(
    'Действие: {{ r.get_action_display }}',
    '{% trans "Действие:" %} {{ r.get_action_display }}')
text = text.replace(
    'Статус: {{ r.get_status_display }}',
    '{% trans "Статус:" %} {{ r.get_status_display }}')
text = text.replace(
    '">Завершить</button>',
    '">{% trans "Завершить" %}</button>')
text = text.replace(
    '<span class="req-card__label">Запросил:</span>',
    '<span class="req-card__label">{% trans "Запросил:" %}</span>')
text = text.replace(
    'value="accept" class="req-btn req-btn--secondary">Принять</button>',
    'value="accept" class="req-btn req-btn--secondary">{% trans "Принять" %}</button>')
text = text.replace(
    'value="reject" class="req-btn req-btn--secondary">Отклонить</button>',
    'value="reject" class="req-btn req-btn--secondary">{% trans "Отклонить" %}</button>')
r.write_text(text, encoding='utf-8')
print('requests.html updated')

# my_ads.html fixes
m = BASE / 'core/templates/my_ads.html'
text = m.read_text(encoding='utf-8')
text = text.replace(
    '\n            Избранное\n',
    '\n            {% trans "Избранное" %}\n')
text = text.replace(
    '<span aria-hidden="true">📄</span> Мои объявления',
    '<span aria-hidden="true">📄</span> {% trans "Мои объявления" %}')
text = text.replace(
    'if p.is_approved %}Активно{% else %}На модерации{% endif %}',
    'if p.is_approved %}{% trans "Активно" %}{% else %}{% trans "На модерации" %}{% endif %}')
m.write_text(text, encoding='utf-8')
print('my_ads.html updated')

# recompile .mo
import polib
for po_path in (BASE / 'locale').rglob('django.po'):
    mo_path = po_path.with_suffix('.mo')
    po = polib.pofile(str(po_path))
    po.save_as_mofile(str(mo_path))
    print(f'Compiled: {mo_path.relative_to(BASE)}')

print('Done.')
