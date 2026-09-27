"""Seed: produtos de interesse e redes sociais (PRD RF-03.6/RF-03.7)."""
from django.db import migrations

PRODUTOS = [
    "Cosméticos",
    "Vitaminas",
    "Suplementos",
    "Alimentos",
    "Roupa íntima",
    "Roupa fitness",
    "Bijuteria",
    "Sapato",
    "Remédios",
    "Outros",
]

REDES = ["Instagram", "Facebook", "TikTok", "WhatsApp", "Outra"]


def seeds(apps, schema_editor):
    ProdutoInteresse = apps.get_model("prospeccao", "ProdutoInteresse")
    RedeSocial = apps.get_model("prospeccao", "RedeSocial")
    for i, nome in enumerate(PRODUTOS, start=1):
        ProdutoInteresse.objects.get_or_create(nome=nome, defaults={"ordem": i})
    for nome in REDES:
        RedeSocial.objects.get_or_create(nome=nome)


def unseed(apps, schema_editor):
    ProdutoInteresse = apps.get_model("prospeccao", "ProdutoInteresse")
    RedeSocial = apps.get_model("prospeccao", "RedeSocial")
    ProdutoInteresse.objects.filter(nome__in=PRODUTOS).delete()
    RedeSocial.objects.filter(nome__in=REDES).delete()


class Migration(migrations.Migration):
    dependencies = [("prospeccao", "0001_initial")]

    operations = [
        migrations.RunPython(seeds, unseed),
    ]
