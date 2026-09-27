"""Regras de negócio para criação/edição de revendedoras (PRD RF-03)."""
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    Cidade,
    Marca,
    ProdutoInteresse,
    RedeSocial,
    RedeSocialVinculo,
    Revendedora,
    RevendedoraInteresse,
    RevendedoraMarca,
    Telefone,
)


def _valida_regras(telefones, marcas, interesses):
    if not telefones:
        raise ValidationError({"telefones": "Informe ao menos um telefone/WhatsApp (RF-03.1)."})
    if not interesses:
        raise ValidationError(
            {"interesses": "Selecione ao menos um produto de interesse (RF-03.7)."}
        )
    if marcas is not None and len(marcas) == 0:
        raise ValidationError(
            {"marcas": "Selecione ao menos uma marca ou marque 'não vende outras' (RF-03.5)."}
        )


@transaction.atomic
def criar_revendedora(
    *,
    promotora,
    dados: dict,
    telefones: list[dict],
    marcas: list[str] | None = None,
    interesses: list[int],
    redes: list[dict] | None = None,
) -> Revendedora:
    """Cria revendedora + relacionamentos em transação.

    dados: campos simples (nome_completo, cpf, rg, email, data_nascimento,
           endereco, bairro, cidade_id, cep, vende_outras_marcas, observacao).
    telefones: [{"numero": ..., "tipo": ..., "principal": bool}]
    marcas: nomes das marcas revendidas (None = não vende outras marcas)
    interesses: ids de ProdutoInteresse
    redes: [{"rede_id": int, "perfil": ..., "para_contato": bool, "para_seguir": bool}]
    """
    if dados.get("vende_outras_marcas") and marcas is None:
        marcas = []
    if not dados.get("vende_outras_marcas"):
        marcas = None
    if marcas is not None and len(marcas) == 0:
        marcas = []

    _valida_regras(telefones, marcas, interesses)

    revendedora = Revendedora(promotora=promotora, **dados)
    revendedora.full_clean()
    revendedora.save()

    for tel in telefones:
        t = Telefone(
            revendedora=revendedora,
            numero=tel["numero"],
            tipo=tel.get("tipo", "whatsapp"),
            principal=tel.get("principal", False),
        )
        t.full_clean()
        t.save()

    for interesse_id in interesses:
        produto = ProdutoInteresse.objects.get(pk=interesse_id, ativa=True)
        RevendedoraInteresse.objects.create(revendedora=revendedora, produto=produto)

    if marcas is not None:
        for nome in marcas:
            nome = nome.strip()
            if not nome:
                continue
            marca, _ = Marca.objects.get_or_create(nome__iexact=nome, defaults={"nome": nome})
            RevendedoraMarca.objects.create(revendedora=revendedora, marca=marca)

    for rede in redes or []:
        if not rede.get("perfil"):
            continue
        objeto_rede = RedeSocial.objects.get(pk=rede["rede_id"])
        RedeSocialVinculo.objects.create(
            revendedora=revendedora,
            rede=objeto_rede,
            perfil=rede["perfil"],
            para_contato=rede.get("para_contato", False),
            para_seguir=rede.get("para_seguir", False),
        )

    revendedora.atualizar_ja_revende()
    return revendedora


def obter_ou_criar_cidade(nome: str, uf: str) -> Cidade:
    cidade, _ = Cidade.objects.get_or_create(nome=nome.strip(), uf=uf)
    return cidade
