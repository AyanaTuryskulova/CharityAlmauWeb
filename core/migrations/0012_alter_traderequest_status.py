from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_remove_product_name_product_condition_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='traderequest',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Ожидает'),
                    ('accepted', 'Подтверждено'),
                    ('in_progress', 'В аренде'),
                    ('rejected', 'Отклонена'),
                    ('completed', 'Завершена'),
                    ('cancelled', 'Отменена'),
                ],
                default='pending',
                max_length=20,
                verbose_name='Статус',
            ),
        ),
    ]
