"""Seed: grupos de perfil (PRD RF-02)."""
from django.db import migrations


def cria_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nome in ("promotora", "gestor"):
        Group.objects.get_or_create(name=nome)


def remove_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=("promotora", "gestor")).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(cria_grupos, remove_grupos),
    ]
