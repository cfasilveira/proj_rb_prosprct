"""Popula o banco de desenvolvimento com dados realistas para testes manuais.

Uso:
    ./manage.py popular_banco                    # 60 revendedoras (padrão)
    ./manage.py popular_banco --revendedoras 120
    ./manage.py popular_banco --reset            # apaga o seed anterior

Cria promotoras (@local.com), cidades, marcas e revendedoras com telefone,
interesses, redes e marcas — sempre pelo service `criar_revendedora`, para que
telefones/interesses obrigatórios e a flag `ja_revende` fiquem coerentes.
Datas de cadastro são retroagidas até 90 dias para exercitar os filtros de
período do dashboard e das análises.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from unicodedata import normalize

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import AuditLog, Perfil
from prospeccao.models import Cidade, Marca, ProdutoInteresse, RedeSocial, Revendedora
from prospeccao.services import criar_revendedora

User = get_user_model()

SENHA = "TesteForte123"

PROMOTORAS = [
    ("Promotora Teste", "promotora@local.com", "Recife/PE"),
    ("Ana Souza", "promo2@local.com", "Olinda/PE"),
    ("Beatriz Lima", "promo3@local.com", "Caruaru/PE"),
    ("Carla Dias", "promo4@local.com", "São Paulo/SP"),
]

CIDADES = [
    ("Recife", "PE"),
    ("Olinda", "PE"),
    ("Jaboatão dos Guararapes", "PE"),
    ("Caruaru", "PE"),
    ("Petrolina", "PE"),
    ("São Paulo", "SP"),
    ("Curitiba", "PR"),
]

MARCAS = ["Natura", "O Boticário", "Mary Kay", "Avon", "Eudora", "Granado", "Phebo"]

PRIMEIROS = [
    "Ana", "Beatriz", "Carla", "Duda", "Fernanda", "Gabriela", "Helena", "Isabela",
    "Juliana", "Larissa", "Mariana", "Natália", "Olívia", "Patrícia", "Renata",
    "Sabrina", "Tainá", "Vanessa", "Aline", "Bruna", "Camila", "Débora", "Elaine",
    "Flávia",
]

ULTIMOS = [
    "Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Ribeiro",
    "Almeida", "Nascimento", "Carvalho", "Araújo", "Fernandes", "Gomes", "Martins",
    "Rocha", "Barbosa", "Dias", "Moreira", "Nunes",
]

DDD = ["81", "11", "41", "81", "81", "11", "41", "21", "31", "71"]

REDES = ["Instagram", "Facebook", "TikTok", "WhatsApp"]


def _ascii(texto: str) -> str:
    """Remove acentos: o validador de e-mail do Django é ASCII-only."""
    return normalize("NFKD", texto).encode("ascii", "ignore").decode()


class Command(BaseCommand):
    help = "Popula o banco de desenvolvimento com promotoras e revendedoras de teste."

    def add_arguments(self, parser):
        parser.add_argument("--revendedoras", type=int, default=60)
        parser.add_argument("--reset", action="store_true", help="apaga revendedoras antes")
        parser.add_argument("--seed", type=int, default=42, help="aleatoriedade reproduzível")

    def handle(self, *args, **opcoes):
        rng = random.Random(opcoes["seed"])
        alvo = opcoes["revendedoras"]

        if opcoes["reset"]:
            removidas, _ = Revendedora.objects.all().delete()
            AuditLog.objects.filter(model="Revendedora").delete()
            self.stdout.write(f"reset: {removidas} objetos removidos")

        promotoras = self._promotoras()
        cidades = self._cidades()
        marcas = self._marcas()
        produtos = list(ProdutoInteresse.objects.filter(ativa=True))
        redes = list(RedeSocial.objects.filter(nome__in=REDES))

        existentes = Revendedora.objects.count()
        cpfs = set()
        for _ in range(max(0, alvo - existentes)):
            rev = self._revendedora(rng, promotoras, cidades, marcas, produtos, redes, cpfs)
            self._retroage(rev, rng)
            if rng.random() < 0.06:
                self._desativa(rev, rng)

        self._resumo(alvo)

    def _promotoras(self):
        perfis = []
        for nome, email, territorio in PROMOTORAS:
            user, _ = User.objects.get_or_create(
                email=email, defaults={"username": email, "first_name": nome.split()[0]}
            )
            user.set_password(SENHA)
            user.save()
            perfil, _ = Perfil.objects.get_or_create(
                user=user, defaults={"nome_completo": nome, "role": Perfil.ROLE_PROMOTORA}
            )
            perfil.nome_completo = nome
            perfil.role = Perfil.ROLE_PROMOTORA
            perfil.territorio = territorio
            perfil.ativo = True
            perfil.save()
            perfis.append(user)
        return perfis

    def _cidades(self):
        return [Cidade.objects.get_or_create(nome=nome, uf=uf)[0] for nome, uf in CIDADES]

    def _marcas(self):
        return [Marca.objects.get_or_create(nome=nome)[0] for nome in MARCAS]

    def _revendedora(self, rng, promotoras, cidades, marcas, produtos, redes, cpfs):
        primeiro = rng.choice(PRIMEIROS)
        sobrenome = rng.choice(ULTIMOS)
        vende_outras = rng.random() < 0.65
        marcas_escolhidas = None
        if vende_outras:
            k = rng.randint(1, min(3, len(marcas)))
            marcas_escolhidas = [m.nome for m in rng.sample(marcas, k)]

        cpf = str(rng.randint(10**10, 10**11 - 1))
        while cpf in cpfs:
            cpf = str(rng.randint(10**10, 10**11 - 1))
        cpfs.add(cpf)

        telefone = rng.choice(DDD) + "9" + str(rng.randint(10**7, 10**8 - 1))
        dados = {
            "nome_completo": f"{primeiro} {sobrenome}",
            "cpf": cpf,
            "rg": str(rng.randint(10**6, 10**7)),
            "email": f"{_ascii(primeiro).lower()}.{_ascii(sobrenome).lower()}"
            f"{rng.randint(1, 99)}@exemplo.com",
            "data_nascimento": date(rng.randint(1975, 2005), rng.randint(1, 12), rng.randint(1, 28)),
            "endereco": f"Rua {rng.choice(['das Flores', 'Nova', 'do Sol', 'Central', 'Aurora'])}, "
            f"{rng.randint(1, 2000)}",
            "bairro": rng.choice(["Centro", "Boa Vista", "Jardim", "Estrela", "Umuarama"]),
            "cidade": rng.choice(cidades),
            "cep": str(rng.randint(10**7, 10**8 - 1)),
            "vende_outras_marcas": vende_outras,
            "observacao": rng.choice(["", "", "Chegou pela indicação", "Prefere contato à tarde"]),
        }

        rev = criar_revendedora(
            promotora=rng.choice(promotoras),
            dados=dados,
            telefones=[{"numero": telefone, "tipo": "whatsapp", "principal": True}],
            marcas=marcas_escolhidas,
            interesses=[p.pk for p in rng.sample(produtos, rng.randint(1, 3))],
            redes=(
                [
                    {
                        "rede_id": rng.choice(redes).pk,
                        "perfil": f"@{_ascii(primeiro).lower()}{rng.randint(100, 999)}",
                        "para_contato": True,
                        "para_seguir": True,
                    }
                ]
                if redes and rng.random() < 0.6
                else None
            ),
        )
        return rev

    @staticmethod
    def _retroage(rev, rng):
        """Espalha as datas de cadastro nos últimos 90 dias (filtros de período)."""
        sorte = rng.random()
        if sorte < 0.12:
            dias, horas = 0, rng.randint(1, 20)
        elif sorte < 0.37:
            dias, horas = rng.randint(1, 7), rng.randint(0, 23)
        elif sorte < 0.72:
            dias, horas = rng.randint(8, 30), rng.randint(0, 23)
        else:
            dias, horas = rng.randint(31, 90), rng.randint(0, 23)

        quando = timezone.now() - timedelta(days=dias, hours=horas)
        Revendedora.objects.filter(pk=rev.pk).update(criado_em=quando, atualizado_em=quando)
        rev.refresh_from_db()

    @staticmethod
    def _desativa(rev, rng):
        """Exclusão lógica com data coerente (>= criado_em e <= agora)."""
        rev.desativar()
        max_dias = max(0, (timezone.now() - rev.criado_em).days - 1)
        quando = min(
            rev.criado_em + timedelta(days=rng.randint(0, max_dias), hours=rng.randint(1, 12)),
            timezone.now() - timedelta(minutes=1),
        )
        Revendedora.objects.filter(pk=rev.pk).update(desativado_em=quando)

    def _resumo(self, alvo):
        ativas = Revendedora.ativas()
        total = ativas.count()
        ja_revende = ativas.filter(ja_revende=True).count()
        desativadas = Revendedora.objects.filter(desativado_em__isnull=False).count()
        pct = round(100 * ja_revende / total) if total else 0

        self.stdout.write(self.style.SUCCESS(f"\nrevendedoras ativas: {total}/{alvo}"))
        self.stdout.write(f"  já revendem: {ja_revende} ({pct}%)")
        self.stdout.write(f"  desativadas: {desativadas}")
        self.stdout.write(f"  cidades: {Cidade.objects.count()} | marcas: {Marca.objects.count()}")
        self.stdout.write("\npromotoras (senha " + SENHA + "):")
        for _, email, territorio in PROMOTORAS:
            self.stdout.write(f"  {email}  ({territorio})")
