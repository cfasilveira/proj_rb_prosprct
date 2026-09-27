"""Testes da importação em lote de revendedoras por planilha Excel (PRD fase 2)."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from prospeccao import importacao
from prospeccao.models import Revendedora

pytestmark = pytest.mark.django_db

CONTEUDO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
URL = reverse("prospeccao:importar")


@pytest.fixture
def gestor(django_user_model):
    user = django_user_model.objects.create_user(
        email="gestor@imp.com", password="x", username="gestor_imp"
    )
    user.perfil.role = "gestor"
    user.perfil.save()
    return user


@pytest.fixture
def promotora(django_user_model):
    return django_user_model.objects.create_user(
        email="promo@imp.com", password="x", username="promo_imp"
    )


def _arquivo(cabecalho, linhas, nome="revendedoras.xlsx"):
    pasta = Workbook()
    aba = pasta.active
    aba.append(cabecalho)
    for linha in linhas:
        aba.append(linha)
    buffer = io.BytesIO()
    pasta.save(buffer)
    return SimpleUploadedFile(nome, buffer.getvalue(), content_type=CONTEUDO_XLSX)


def _linha(**sobrescreve):
    dados = dict(importacao.EXEMPLO)
    dados.update(sobrescreve)
    return [dados[coluna] for coluna in importacao.COLUNAS]


def _analisar(client, linhas, **extra):
    payload = {"acao": "analisar", "planilha": _arquivo(importacao.COLUNAS, linhas)}
    payload.update(extra)
    return client.post(URL, payload)


# ---------------------------------------------------------------- planilha


def test_ler_planilha_normaliza_cabecalho_com_alias():
    linhas = importacao.ler_planilha(
        _arquivo(
            ["Nome", "Cidade", "Estado", "Whatsapp", "Produtos"],
            [["Ana Souza", "Recife", "PE", "81999998888", "Cosméticos"]],
        )
    )
    assert linhas == [
        {
            "nome_completo": "Ana Souza",
            "cidade": "Recife",
            "uf": "PE",
            "telefone": "81999998888",
            "interesses": "Cosméticos",
            "_linha": "2",
        }
    ]


def test_ler_planilha_reclama_de_coluna_obrigatoria_ausente():
    with pytest.raises(importacao.ErroDePlanilha) as erro:
        importacao.ler_planilha(_arquivo(["Nome"], [["Ana"]]))
    assert "telefone" in str(erro.value)


def test_ler_planilha_reclama_de_planilha_sem_dados():
    with pytest.raises(importacao.ErroDePlanilha) as erro:
        importacao.ler_planilha(_arquivo(importacao.COLUNAS, []))
    assert "linha de dados" in str(erro.value)


def test_ler_planilha_ignora_linha_em_branco():
    linhas = importacao.ler_planilha(
        _arquivo(importacao.COLUNAS, [[None] * len(importacao.COLUNAS), _linha()])
    )
    assert len(linhas) == 1
    assert linhas[0]["nome_completo"] == importacao.EXEMPLO["nome_completo"]


def test_ler_planilha_limita_a_mil_linhas():
    with pytest.raises(importacao.ErroDePlanilha) as erro:
        importacao.ler_planilha(
            _arquivo(importacao.COLUNAS, [_linha() for _ in range(importacao.MAX_LINHAS + 1)])
        )
    assert str(importacao.MAX_LINHAS) in str(erro.value)


def test_arquivo_nao_e_planilha():
    arquivo = SimpleUploadedFile("x.xlsx", b"nao e xlsx", content_type=CONTEUDO_XLSX)
    with pytest.raises(importacao.ErroDePlanilha) as erro:
        importacao.ler_planilha(arquivo)
    assert "Não consegui abrir" in str(erro.value)


# ------------------------------------------------------------- validação


def test_linha_valida_passa_com_erro_vazio():
    resultado = importacao.analisa(importacao.ler_planilha(_arquivo(importacao.COLUNAS, [_linha()])))[0]
    assert resultado.ok, resultado.erros
    assert resultado.dados["cidade_nome"] == "Recife"
    assert resultado.telefones == [
        {"numero": "81999990001", "tipo": "whatsapp", "principal": True}
    ]
    assert resultado.marcas == ["Natura", "Avon"]
    assert resultado.interesses  # ids resolvidos a partir do catálogo


def test_analisa_agrupa_todos_os_erros_da_linha():
    linha = _linha(
        nome_completo="",
        telefone="123",
        uf="XX",
        cpf="123",
        vende_outras_marcas="sim",
        marcas="",
        interesses="Produto Inexistente",
        data_nascimento="31/12/2099",
    )
    resultado = importacao.analisa(importacao.ler_planilha(_arquivo(importacao.COLUNAS, [linha])))[0]
    assert not resultado.ok
    assert "nome completo obrigatório" in resultado.erros
    assert "telefone precisa ter DDD + número (10 ou 11 dígitos)" in resultado.erros
    assert "UF inválida: XX" in resultado.erros
    assert "CPF precisa ter 11 dígitos" in resultado.erros
    assert 'marque "sim" e informe as marcas, ou marque "não"' in resultado.erros
    assert "interesse desconhecido" in resultado.erros[5] or any(
        "interesse desconhecido" in e for e in resultado.erros
    )
    assert "data de nascimento não pode ser futura" in resultado.erros


def test_analisa_detecta_cpf_repetido_na_planilha():
    linhas = [
        _linha(nome_completo="Ana Silva", cpf="99988877766"),
        _linha(nome_completo="Bia Silva", cpf="99988877766"),
    ]
    resultados = importacao.analisa(importacao.ler_planilha(_arquivo(importacao.COLUNAS, linhas)))
    assert resultados[0].ok, resultados[0].erros
    assert "CPF repetido na planilha (linha 2)" in resultados[1].erros


def test_analisa_marca_vende_sem_marcas_como_erro():
    resultado = importacao.analisa(
        importacao.ler_planilha(_arquivo(importacao.COLUNAS, [_linha(marcas="")]))
    )[0]
    assert not resultado.ok
    assert 'marque "sim" e informe as marcas, ou marque "não"' in resultado.erros


def test_analisa_aceita_voutras_como_nao():
    resultado = importacao.analisa(
        importacao.ler_planilha(_arquivo(importacao.COLUNAS, [_linha(vende_outras_marcas="não")]))
    )[0]
    assert resultado.ok, resultado.erros
    assert resultado.marcas is None
    assert resultado.resumo["ja_revende"] == "não"


def test_modelo_baixado_valida_sem_erro():
    """O modelo precisa sobreviver à própria rotina de importação."""
    linhas = importacao.ler_planilha(io.BytesIO(importacao.modelo()))
    assert len(linhas) == 2
    resultados = importacao.analisa(linhas)
    assert all(r.ok for r in resultados), [r.erros for r in resultados if not r.ok]


# ------------------------------------------------------------------ view


def test_requer_login(client):
    assert client.get(URL).status_code == 302


def test_modelo_baixa_arquivo_xlsx(client, promotora):
    client.force_login(promotora)
    resposta = client.get(f"{URL}?modelo=1")
    assert resposta.status_code == 200
    assert resposta["Content-Type"] == CONTEUDO_XLSX
    assert "attachment" in resposta["Content-Disposition"]
    assert resposta.content.startswith(b"PK")


def test_analisar_sem_arquivo_mostra_erro(client, promotora):
    client.force_login(promotora)
    resposta = client.post(URL, {"acao": "analisar"})
    assert "Escolha um arquivo .xlsx" in resposta.content.decode()


def test_analisar_grava_a_previa_na_session(client, promotora):
    client.force_login(promotora)
    resposta = _analisar(
        client,
        [_linha(), _linha(nome_completo="Bia Teste", cpf="11122233344", telefone="")],
    )
    pacote = client.session["importacao_planilha"]
    assert pacote["promotora_id"] == promotora.pk
    assert len(pacote["linhas"]) == 2
    html = resposta.content.decode()
    assert "Prévia da importação" in html
    assert "telefone obrigatório" in html


def test_confirmar_grava_somente_as_linhas_validas(client, promotora):
    client.force_login(promotora)
    _analisar(
        client,
        [
            _linha(),
            _linha(nome_completo="Sem Telefone", cpf="11122233344", telefone=""),
        ],
    )
    client.post(URL, {"acao": "confirmar"})

    assert Revendedora.objects.count() == 1
    criada = Revendedora.objects.get()
    assert criada.nome_completo == "Maria da Silva"
    assert criada.promotora_id == promotora.pk
    assert criada.cidade.nome == "Recife"
    assert criada.telefones.get().numero == "81999990001"
    assert "importacao_planilha" not in client.session


def test_confirmar_revalida_e_nao_duplica_se_repetir(client, promotora):
    client.force_login(promotora)
    _analisar(client, [_linha()])
    client.post(URL, {"acao": "confirmar"})
    _analisar(client, [_linha()])
    resposta = client.post(URL, {"acao": "confirmar"})

    assert Revendedora.objects.count() == 1
    assert "CPF já cadastrado no sistema" in resposta.content.decode()


def test_confirmar_sem_previa_redireciona_com_erro(client, promotora):
    client.force_login(promotora)
    resposta = client.post(URL, {"acao": "confirmar"})
    assert resposta.status_code == 302


def test_cancelar_limpa_a_session(client, promotora):
    client.force_login(promotora)
    _analisar(client, [_linha()])
    client.post(URL, {"acao": "cancelar"})
    assert "importacao_planilha" not in client.session
    assert Revendedora.objects.count() == 0


def test_gestor_precisa_escolher_a_promotora(client, gestor):
    client.force_login(gestor)
    resposta = _analisar(client, [_linha()])
    assert "Escolha a promotora" in resposta.content.decode()
    assert "importacao_planilha" not in client.session


def test_gestor_importa_para_a_promotora_escolhida(client, gestor, promotora):
    client.force_login(gestor)
    _analisar(client, [_linha()], promotora_id=str(promotora.pk))
    client.post(URL, {"acao": "confirmar"})
    assert Revendedora.objects.get().promotora_id == promotora.pk


def test_promotora_importa_para_a_propria_carteira(client, promotora, django_user_model):
    outra = django_user_model.objects.create_user(
        email="outra@imp.com", password="x", username="outra_imp"
    )
    client.force_login(promotora)
    _analisar(client, [_linha()], promotora_id=str(outra.pk))
    client.post(URL, {"acao": "confirmar"})
    assert Revendedora.objects.get().promotora_id == promotora.pk
