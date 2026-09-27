"""Testes de E3: wizard de cadastro, escopo e exclusão lógica (PRD RF-03, AC-05)."""
import pytest
from django.urls import reverse

from prospeccao.models import Cidade, ProdutoInteresse, Revendedora

pytestmark = pytest.mark.django_db


@pytest.fixture
def promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo@test.com", password="x", username="promo"
    )


@pytest.fixture
def outra_promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo2@test.com", password="x", username="promo2"
    )


def _wizard_completo(client, **dados_extra):
    """Roda as 4 etapas + revisão + salvar."""
    url = reverse("prospeccao:revendedora_nova")

    r1 = client.post(url, {
        "etapa": 1, "acao": "avancar",
        "nome_completo": dados_extra.get("nome", "Ana Silva"),
        "email": "ana@exemplo.com",
        "telefone": dados_extra.get("telefones", ["41999998888"]),
    })
    assert r1.status_code == 302 and "etapa=2" in r1["Location"]

    r2 = client.post(url, {
        "etapa": 2, "acao": "avancar",
        "cpf": dados_extra.get("cpf", ""),
        "rg": "12345",
        "data_nascimento": "15/03/1990",
        "cep": "80010010",
        "endereco": "Rua das Flores, 100",
        "bairro": "Centro",
        "cidade_nome": "Curitiba",
        "cidade_uf": "PR",
    })
    assert r2.status_code == 302 and "etapa=3" in r2["Location"]

    r3 = client.post(url, {
        "etapa": 3, "acao": "avancar",
        "vende_outras_marcas": dados_extra.get("vende", "nao"),
        "marca_id": dados_extra.get("marca_ids", []),
    })
    assert r3.status_code == 302 and "etapa=4" in r3["Location"], getattr(r3, "content", b"")[:300]

    r4 = client.post(url, {
        "etapa": 4, "acao": "avancar",
        "interesse_id": dados_extra.get("interesses", []),
    })
    assert r4.status_code == 302 and "etapa=5" in r4["Location"]

    revisao = client.get(f"{url}?etapa=5")
    assert revisao.status_code == 200

    r5 = client.post(url, {"etapa": 5, "acao": "salvar"})
    assert r5.status_code == 302 and "sucesso" in r5["Location"]
    return r5


def test_login_obrigatorio(client):
    response = client.get(reverse("prospeccao:revendedora_nova"))
    assert response.status_code == 302
    assert "/contas/entrar/" in response["Location"]


def test_wizard_happy_path_cria_revendedora(client, promotora):
    client.force_login(promotora)
    interesse = ProdutoInteresse.objects.first()
    r5 = _wizard_completo(client, interesses=[interesse.pk])

    pagina_sucesso = client.get(r5["Location"])
    assert pagina_sucesso.status_code == 200
    assert "sucesso" in pagina_sucesso.content.decode().lower()

    revendedora = Revendedora.objects.get()
    assert revendedora.nome_completo == "Ana Silva"
    assert revendedora.promotora == promotora
    assert revendedora.cidade.nome == "Curitiba"
    assert revendedora.ja_revende is False
    assert revendedora.telefones.count() == 1
    assert revendedora.interesses.count() == 1
    assert revendedora.data_nascimento.year == 1990


def test_etapa1_sem_nome_mostra_erro(client, promotora):
    client.force_login(promotora)
    response = client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 1, "acao": "avancar", "nome_completo": "", "telefone": ["41999998888"],
    })
    assert response.status_code == 200
    assert b"obrigat" in response.content.lower() or b"informe" in response.content.lower()


def test_etapa1_sem_telefone_mostra_erro(client, promotora):
    client.force_login(promotora)
    response = client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 1, "acao": "avancar", "nome_completo": "Ana Silva", "telefone": [""],
    })
    assert response.status_code == 200
    assert b"telefone" in response.content.lower()


def test_etapa2_cpf_duplicado_bloqueia(client, promotora, django_user_model):
    from prospeccao.services import criar_revendedora

    cidade = Cidade.objects.create(nome="Curitiba", uf="PR")
    interesse = ProdutoInteresse.objects.first()
    criar_revendedora(
        promotora=promotora,
        dados={"nome_completo": "Primeira", "cidade": cidade, "cpf": "12345678901"},
        telefones=[{"numero": "41999998888"}],
        interesses=[interesse.pk],
    )
    client.force_login(promotora)
    client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 1, "acao": "avancar", "nome_completo": "Segunda",
        "telefone": ["41999997777"],
    })
    response = client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 2, "acao": "avancar", "cpf": "123.456.789-01",
        "cidade_nome": "Curitiba", "cidade_uf": "PR",
    })
    assert response.status_code == 200
    assert b"em uso" in response.content
    assert Revendedora.objects.count() == 1


def test_etapa3_sim_sem_marca_bloqueia(client, promotora):
    client.force_login(promotora)
    client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 1, "acao": "avancar", "nome_completo": "Ana Silva",
        "telefone": ["41999998888"],
    })
    client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 2, "acao": "avancar", "cidade_nome": "Curitiba", "cidade_uf": "PR",
    })
    response = client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 3, "acao": "avancar", "vende_outras_marcas": "sim",
    })
    assert response.status_code == 200
    assert b"marca" in response.content.lower()


def test_escopo_promotora_nao_ve_de_outra(client, promotora, outra_promotora):
    from prospeccao.services import criar_revendedora

    cidade = Cidade.objects.create(nome="Curitiba", uf="PR")
    interesse = ProdutoInteresse.objects.first()
    revendedora = criar_revendedora(
        promotora=outra_promotora,
        dados={"nome_completo": "De Outra", "cidade": cidade},
        telefones=[{"numero": "41999998888"}],
        interesses=[interesse.pk],
    )
    client.force_login(promotora)

    lista = client.get(reverse("prospeccao:revendedora_list"))
    assert b"De Outra" not in lista.content

    detalhe = client.get(reverse("prospeccao:revendedora_detail", args=[revendedora.pk]))
    assert detalhe.status_code == 404

    exclui = client.post(reverse("prospeccao:revendedora_delete", args=[revendedora.pk]))
    assert exclui.status_code == 404
    assert Revendedora.objects.filter(pk=revendedora.pk, desativado_em__isnull=True).exists()


def test_gestor_ve_tudo(client, promotora, django_user_model):
    from prospeccao.services import criar_revendedora

    gestor = django_user_model.objects.create_user(
        email="gestor@test.com", password="x", username="gestor"
    )
    gestor.perfil.role = "gestor"
    gestor.perfil.save()

    cidade = Cidade.objects.create(nome="Curitiba", uf="PR")
    interesse = ProdutoInteresse.objects.first()
    criar_revendedora(
        promotora=promotora,
        dados={"nome_completo": "Da Promo", "cidade": cidade},
        telefones=[{"numero": "41999998888"}],
        interesses=[interesse.pk],
    )
    client.force_login(gestor)
    lista = client.get(reverse("prospeccao:revendedora_list"))
    assert b"Da Promo" in lista.content


def test_exclusao_e_logica(client, promotora):
    from prospeccao.services import criar_revendedora

    cidade = Cidade.objects.create(nome="Curitiba", uf="PR")
    interesse = ProdutoInteresse.objects.first()
    revendedora = criar_revendedora(
        promotora=promotora,
        dados={"nome_completo": "Vai Sair", "cidade": cidade},
        telefones=[{"numero": "41999998888"}],
        interesses=[interesse.pk],
    )
    client.force_login(promotora)
    response = client.post(reverse("prospeccao:revendedora_delete", args=[revendedora.pk]))
    assert response.status_code == 302

    revendedora.refresh_from_db()
    assert revendedora.desativado_em is not None
    assert Revendedora.ativas().count() == 0
    assert Revendedora.objects.count() == 1  # histórico preservado


def test_edicao_via_wizard(client, promotora):
    from prospeccao.services import criar_revendedora

    cidade = Cidade.objects.create(nome="Curitiba", uf="PR")
    interesse = ProdutoInteresse.objects.first()
    revendedora = criar_revendedora(
        promotora=promotora,
        dados={"nome_completo": "Nome Antigo", "cidade": cidade},
        telefones=[{"numero": "41999998888"}],
        interesses=[interesse.pk],
    )
    client.force_login(promotora)

    abre = client.get(f"{reverse('prospeccao:revendedora_nova')}?editar={revendedora.pk}")
    assert abre.status_code == 302

    client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 1, "acao": "avancar", "nome_completo": "Nome Novo",
        "telefone": ["41999997777"],
    })
    client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 2, "acao": "avancar", "cidade_nome": "Curitiba", "cidade_uf": "PR",
    })
    client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 3, "acao": "avancar", "vende_outras_marcas": "nao",
    })
    client.post(reverse("prospeccao:revendedora_nova"), {
        "etapa": 4, "acao": "avancar", "interesse_id": [interesse.pk],
    })
    client.post(reverse("prospeccao:revendedora_nova"), {"etapa": 5, "acao": "salvar"})

    revendedora.refresh_from_db()
    assert revendedora.nome_completo == "Nome Novo"
    assert revendedora.telefones.count() == 1
    assert Revendedora.objects.count() == 1
