from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_drop_legacy_product_name_column'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RentItem',
        ),
    ]
