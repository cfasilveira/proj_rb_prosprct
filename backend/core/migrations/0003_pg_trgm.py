"""Habilita pg_trgm para busca por nome (Backend_Schema §7)."""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("core", "0002_seed_grupos")]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql="-- pg_trgm mantida (não destrutiva)\n",
        ),
    ]
