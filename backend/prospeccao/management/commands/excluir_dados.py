"""Anonimiza dados pessoais de uma revendedora (LGPD, PRD RNF-06).

Uso:
    ./manage.py excluir_dados --cpf 12345678901
    ./manage.py excluir_dados --email ana@exemplo.com
    ./manage.py excluir_dados --cpf 12345678901 --usuario gestor@empresa.com

Apaga nome, CPF, RG, e-mail, nascimento, endereço, observação, telefones e
redes. A linha permanece anonimizada e o registro de auditoria é preservado
(sem dados pessoais).
"""
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from prospeccao.models import Revendedora


class Command(BaseCommand):
    help = "Anonimiza (exclui) os dados pessoais de uma revendedora."

    def add_arguments(self, parser):
        parser.add_argument("--cpf", help="CPF da revendedora (com ou sem pontuação)")
        parser.add_argument("--email", help="E-mail da revendedora")
        parser.add_argument(
            "--usuario", help="E-mail do gestor responsável (para a auditoria)"
        )

    def handle(self, *args, **opcoes):
        if not opcoes["cpf"] and not opcoes["email"]:
            raise CommandError("Informe --cpf ou --email.")
        if opcoes["cpf"] and opcoes["email"]:
            raise CommandError("Informe apenas um identificador (--cpf ou --email).")

        revendedora = self._localizar(opcoes)
        usuario = self._usuario(opcoes)
        rotulo = f"{revendedora.nome_completo} (CPF *{self._cpf_mascarado(revendedora.cpf)})"
        revendedora.excluir_dados_pessoais(usuario=usuario)
        self.stdout.write(self.style.SUCCESS(f"Dados pessoais excluídos: {rotulo}"))

    def _localizar(self, opcoes) -> Revendedora:
        if opcoes["cpf"]:
            cpf = re.sub(r"\D", "", opcoes["cpf"])
            if len(cpf) != 11:
                raise CommandError("CPF deve ter 11 dígitos.")
            encontradas = Revendedora.objects.filter(cpf=cpf)
            descricao = f"CPF {self._cpf_mascarado(cpf)}"
        else:
            encontradas = Revendedora.objects.filter(email__iexact=opcoes["email"].strip())
            descricao = f"e-mail {opcoes['email'].strip()}"

        if not encontradas.exists():
            raise CommandError(f"Nenhuma revendedora com {descricao}.")
        if encontradas.count() > 1:
            raise CommandError(
                f"Mais de uma revendedora com {descricao}; use o identificador único."
            )
        return encontradas.get()

    def _usuario(self, opcoes):
        if not opcoes["usuario"]:
            return None
        email = opcoes["usuario"].strip().lower()
        usuario = get_user_model().objects.filter(email=email).first()
        if usuario is None:
            raise CommandError(f"Usuário {email} não encontrado.")
        return usuario

    @staticmethod
    def _cpf_mascarado(cpf) -> str:
        digitos = re.sub(r"\D", "", cpf or "")
        return digitos[-3:] if len(digitos) == 11 else "***"
