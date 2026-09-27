"""Cria o usuário gestor inicial do canal.

Uso:
    ./manage.py criar_gestor gestor@empresa.com --senha SenhaForte123 --nome "Nome"
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from core.models import Perfil

User = get_user_model()


class Command(BaseCommand):
    help = "Cria (ou atualiza) um usuário com perfil de gestor."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("--senha", required=True)
        parser.add_argument("--nome", default="Gestor do Canal")

    def handle(self, *args, **opcoes):
        email = opcoes["email"].strip().lower()
        senha = opcoes["senha"]
        if len(senha) < 6:
            raise CommandError("A senha deve ter ao menos 6 caracteres.")

        user, criado = User.objects.get_or_create(
            email=email, defaults={"username": email, "first_name": opcoes["nome"]}
        )
        user.set_password(senha)
        user.save()

        perfil, _ = Perfil.objects.get_or_create(
            user=user, defaults={"nome_completo": opcoes["nome"]}
        )
        perfil.role = Perfil.ROLE_GESTOR
        perfil.ativo = True
        perfil.nome_completo = opcoes["nome"]
        perfil.save()

        grupo, _ = Group.objects.get_or_create(name="gestor")
        user.groups.add(grupo)

        self.stdout.write(
            self.style.SUCCESS(f"Gestor {'criado' if criado else 'atualizado'}: {email}")
        )
