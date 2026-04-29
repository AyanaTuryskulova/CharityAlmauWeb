from django.db import migrations


def drop_legacy_product_name_column(apps, schema_editor):
    connection = schema_editor.connection
    table_name = "core_product"
    column_name = "name"

    with connection.cursor() as cursor:
        if connection.vendor == "sqlite":
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            if column_name in columns:
                cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")

        elif connection.vendor == "mysql":
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = %s
                  AND COLUMN_NAME = %s
                LIMIT 1
                """,
                [table_name, column_name],
            )
            if cursor.fetchone():
                cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")

        elif connection.vendor == "postgresql":
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = %s
                  AND column_name = %s
                LIMIT 1
                """,
                [table_name, column_name],
            )
            if cursor.fetchone():
                cursor.execute(f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}"')


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_traderequest_desired_categories_and_more"),
    ]

    operations = [
        migrations.RunPython(drop_legacy_product_name_column, migrations.RunPython.noop),
    ]
