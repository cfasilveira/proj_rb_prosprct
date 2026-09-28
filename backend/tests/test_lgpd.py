"""Testes de LGPD/RNF-06: anonimização de dados pessoais (exclusão sob demanda)."""
from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.models import AuditLog
from prospeccao.models import Cidade, RedeSocial, RedeSocialVinculo, Revendedora, Telefone

pytestmark = pytest.mark.django_db


def _comando(**opcoes):
    """Executa `manage.py excluir_dados` e devolve a saída."""
    saida = StringIO()
    call_command("excluir_dados", stdout=saida, **opcoes)
    return saida.getvalue()


@pytest.fixture
def cidade():
    return Cidade.objects.create(nome="Curitiba", uf="PR")


@pytest.fixture
def promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo@test.com", password="x", username="promo"
    )


@pytest.fixture
def revendedora(cidade, promotora):
    revenda = Revendedora.objects.create(
        nome_completo="Ana Silva",
        cpf="12345678901",
        rg="MG123456",
        email="ana@exemplo.com",
        data_nascimento=date(1990, 5, 1),
        endereco="Rua A, 100",
        bairro="Centro",
        cep="80010000",
        observacao="Prefere WhatsApp à noite",
        promotora=promotora,
        cidade=cidade,
    )
    Telefone.objects.create(revendedora=revenda, numero="41999990000", principal=True)
    rede, _ = RedeSocial.objects.get_or_create(nome="Instagram")
    RedeSocialVinculo.objects.create(revendedora=revenda, rede=rede, perfil="@anasilva")
    return revenda


def test_exclui_dados_pessoais_e_preserva_estrutura(revendedora, promotora):
    """RNF-06: dados pessoais saem, linha + vínculo com a promotora ficam."""
    revendedora.excluir_dados_pessoais(usuario=promotora)

    revenda = Revendedora.objects.get(pk=revendedora.pk)
    assert revenda.nome_completo == Revendedora.NOME_EXCLUIDA
    assert revenda.cpf is None
    assert revenda.rg == ""
    assert revenda.email == ""
    assert revenda.data_nascimento is None
    assert revenda.endereco == ""
    assert revenda.bairro == ""
    assert revenda.cep == ""
    assert revenda.observacao == ""
    assert revenda.telefones.count() == 0
    assert revenda.redes.count() == 0
    # estrutura preservada: promotora, cidade e datas originais
    assert revenda.promotora == promotora
    assert revenda.cidade_id == revendedora.cidade_id
    assert revenda.anonimizada is True
    assert revenda.ativa is False


def test_registro_anonimo_fica_na_auditoria_sem_nome(revendedora, promotora):
    """Auditoria mínima: quem fez, o quê e quando — sem dado pessoal."""
    revendedora.excluir_dados_pessoais(usuario=promotora)

    registros = AuditLog.objects.filter(model="Revendedora", obj_id=revendedora.pk)
    registro = registros.get(payload__motivo="lgpd")
    assert registro.acao == "delete"
    assert registro.user == promotora
    assert registro.payload == {"motivo": "lgpd", "anonimizado": True}
    # entradas antigas (create/update) foram esvaziadas pelo mesmo procedimento
    dados = str(list(registros.values_list("payload", flat=True)))
    assert "Ana" not in dados
    assert "12345678901" not in dados
    assert registros.filter(payload={"anonimizado": True}).count() > 0


def test_exclusao_e_idempotente(revendedora, promotora):
    """Chamar duas vezes não repete a ação nem duplica a auditoria."""
    revendedora.excluir_dados_pessoais(usuario=promotora)
    revendedora.excluir_dados_pessoais(usuario=promotora)

    registros = AuditLog.objects.filter(
        model="Revendedora", obj_id=revendedora.pk, payload__motivo="lgpd"
    )
    assert registros.count() == 1
    assert Revendedora.objects.get(pk=revendedora.pk).nome_completo == (
        Revendedora.NOME_EXCLUIDA
    )


def test_anonimizada_some_das_consultas_ativas(revendedora, promotora):
    """Escopo de acesso e análises continuam sem a revendedora excluída."""
    revendedora.excluir_dados_pessoais(usuario=promotora)

    assert not Revendedora.ativas().filter(pk=revendedora.pk).exists()
    assert not Revendedora.para_promotora(promotora).filter(pk=revendedora.pk).exists()
    # mas o gestor ainda encontra o registro (admin), para efeito de auditoria
    assert Revendedora.objects.filter(pk=revendedora.pk).exists()


def test_comando_anonimiza_por_cpf_com_pontuacao(revendedora, promotora):
    """O gestor cola o CPF como veio do sistema — a pontuação é ignorada."""
    saida = _comando(cpf="123.456.789-01", usuario=promotora.email)

    revenda = Revendedora.objects.get(pk=revendedora.pk)
    assert revenda.anonimizada
    assert "901" in saida and "excluídos" in saida
    registro = AuditLog.objects.get(
        model="Revendedora", obj_id=revenda.pk, payload__motivo="lgpd"
    )
    assert registro.user == promotora


def test_comando_anonimiza_por_email(revendedora):
    saida = _comando(email="ana@exemplo.com")

    assert Revendedora.objects.get(pk=revendedora.pk).anonimizada
    assert "excluídos" in saida


def test_comando_exige_um_identificador_unico(revendedora):
    with pytest.raises(CommandError, match="Informe --cpf ou --email"):
        _comando()
    with pytest.raises(CommandError, match="apenas um identificador"):
        _comando(cpf="12345678901", email="ana@exemplo.com")
    with pytest.raises(CommandError, match="11 dígitos"):
        _comando(cpf="123")
    with pytest.raises(CommandError, match="Nenhuma revendedora"):
        _comando(cpf="99999999999")


def test_comando_repetido_sai_com_erro_de_nao_encontrada(revendedora, promotora):
    """Após a exclusão não sobra identificador — reexecução não achou nada."""
    _comando(cpf="12345678901", usuario=promotora.email)
    with pytest.raises(CommandError, match="Nenhuma revendedora"):
        _comando(cpf="12345678901", usuario=promotora.email)

    registros = AuditLog.objects.filter(
        model="Revendedora", obj_id=revendedora.pk, payload__motivo="lgpd"
    )
    assert registros.count() == 1


@pytest.fixture
def gestor_admin(django_user_model):
    usuario = django_user_model.objects.create_user(
        email="gestor@test.com", password="x", username="gestor"
    )
    usuario.is_staff = True
    usuario.is_superuser = True
    usuario.save(update_fields=["is_staff", "is_superuser"])
    return usuario


def _acao_admin(client, usuario, pks):
    """Dispara a ação do admin sobre os registros selecionados."""
    client.force_login(usuario)
    return client.post(
        "/admin/prospeccao/revendedora/",
        data={
            "action": "excluir_dados_pessoais",
            "_selected_action": [str(pk) for pk in pks],
            "index": 0,
            "select_across": 0,
        },
        follow=True,
    )


def test_acao_admin_anonimiza_em_lote_e_audita(client, revendedora, cidade, gestor_admin):
    outra = Revendedora.objects.create(
        nome_completo="Bruna Souza",
        cpf="10987654321",
        promotora=revendedora.promotora,
        cidade=cidade,
    )

    resposta = _acao_admin(client, gestor_admin, [revendedora.pk, outra.pk])

    assert resposta.status_code == 200
    assert "2 revendedora(s) anonimizada(s)" in resposta.content.decode()
    for pk in [revendedora.pk, outra.pk]:
        revenda = Revendedora.objects.get(pk=pk)
        assert revenda.anonimizada
        registro = AuditLog.objects.get(
            model="Revendedora", obj_id=pk, payload__motivo="lgpd"
        )
        assert registro.user == gestor_admin


def test_acao_admin_avisa_quando_ja_anonimizada(client, revendedora, promotora, gestor_admin):
    revendedora.excluir_dados_pessoais(usuario=promotora)

    resposta = _acao_admin(client, gestor_admin, [revendedora.pk])

    assert "já estavam anonimizados" in resposta.content.decode()
    registros = AuditLog.objects.filter(
        model="Revendedora", obj_id=revendedora.pk, payload__motivo="lgpd"
    )
    assert registros.count() == 1
    assert registros.get().user == promotora


def test_exclusao_dura_do_admin_nao_guarda_nome(revendedora):
    """Delete real também precisa deixar auditoria sem dado pessoal (RNF-06)."""
    pk = revendedora.pk
    revendedora.delete()

    registros = AuditLog.objects.filter(model="Revendedora", obj_id=pk, acao="delete")
    assert registros.filter(payload={}).exists()
    assert "Ana" not in str(list(registros.values_list("payload", flat=True)))
