"""Formulários do wizard de cadastro de revendedora (PRD RF-03, App Flow §2)."""
from django import forms
from localflavor.br.br_states import STATE_CHOICES

from .models import Cidade, Marca, ProdutoInteresse, RedeSocial

ETAPAS = {
    1: ("Contato", ["nome_completo", "email", "telefones", "redes"]),
    2: ("Endereço", ["cpf", "rg", "data_nascimento", "cep", "endereco", "bairro", "cidade"]),
    3: ("Mercado", ["vende_outras_marcas", "marcas"]),
    4: ("Interesse", ["interesses"]),
}
ULTIMA_ETAPA = 4
REVISAO = 5

MAX_TELEFONES = 3
MAX_REDES = 3


def normaliza_digitos(valor: str) -> str:
    return "".join(ch for ch in (valor or "") if ch.isdigit())


class RevendedoraForm(forms.Form):
    """Campos escalares do wizard; listas (telefones, marcas...) são tratadas à parte."""

    nome_completo = forms.CharField(
        max_length=120,
        label="Nome completo *",
        widget=forms.TextInput(attrs={"placeholder": "Nome e sobrenome", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        required=False,
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "email@exemplo.com", "autocomplete": "email"}),
    )
    data_nascimento = forms.DateField(
        required=False,
        label="Data de nascimento",
        input_formats=["%d/%m/%Y"],
        widget=forms.TextInput(attrs={"placeholder": "DD/MM/AAAA", "data-mask": "data"}),
    )
    cpf = forms.CharField(
        required=False,
        label="CPF",
        max_length=14,
        widget=forms.TextInput(attrs={"placeholder": "000.000.000-00", "data-mask": "cpf", "inputmode": "numeric"}),
    )
    rg = forms.CharField(
        required=False, label="RG", max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "Somente números e letras"}),
    )
    cep = forms.CharField(
        required=False,
        label="CEP",
        max_length=9,
        widget=forms.TextInput(attrs={"placeholder": "00000-000", "data-mask": "cep", "inputmode": "numeric"}),
    )
    endereco = forms.CharField(
        required=False, label="Endereço", max_length=160,
        widget=forms.TextInput(attrs={"placeholder": "Rua, número, complemento"}),
    )
    bairro = forms.CharField(
        required=False, label="Bairro", max_length=80,
        widget=forms.TextInput(attrs={"placeholder": "Bairro"}),
    )
    cidade_nome = forms.CharField(
        required=False, label="Cidade *", max_length=80,
        widget=forms.TextInput(attrs={"placeholder": "Cidade", "list": "cidade-list"}),
    )
    cidade_uf = forms.ChoiceField(
        required=False, label="UF *", choices=[("", "UF")] + list(STATE_CHOICES),
        widget=forms.Select(attrs={"class": "select-uf"}),
    )
    vende_outras_marcas = forms.ChoiceField(
        required=False,
        label="Vende outras marcas? *",
        choices=[("sim", "Sim"), ("nao", "Não")],
        initial="nao",
        widget=forms.RadioSelect,
    )

    def clean_cpf(self):
        cpf = normaliza_digitos(self.cleaned_data.get("cpf", ""))
        if not cpf:
            return ""
        if len(cpf) != 11:
            raise forms.ValidationError("CPF deve ter 11 dígitos.")
        return cpf

    def clean_cep(self):
        cep = normaliza_digitos(self.cleaned_data.get("cep", ""))
        if not cep:
            return ""
        if len(cep) != 8:
            raise forms.ValidationError("CEP deve ter 8 dígitos.")
        return cep

    def clean_cidade_nome(self):
        return (self.cleaned_data.get("cidade_nome") or "").strip()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("cidade_nome") and not cleaned.get("cidade_uf"):
            self.add_error("cidade_uf", "Selecione a UF da cidade.")
        if cleaned.get("cidade_uf") and not cleaned.get("cidade_nome"):
            self.add_error("cidade_nome", "Informe a cidade.")
        return cleaned


def limpa_telefones(valores: list[str]) -> list[str]:
    """Normaliza e valida a lista de telefones da etapa 1 (RF-03.1/RF-03.4)."""
    digitos = [normaliza_digitos(v) for v in valores]
    unicos = []
    for numero in digitos:
        if numero and numero not in unicos:
            unicos.append(numero)
    erros = [n for n in unicos if len(n) < 10 or len(n) > 11]
    if erros:
        raise forms.ValidationError(f"Telefone inválido: {', '.join(erros)}. Use DDD + número.")
    return unicos


def valida_etapa(form: RevendedoraForm, draft: dict, etapa: int) -> dict[str, list[str]]:
    """Valida apenas os campos da etapa atual; demais erros ficam para depois."""
    form.is_valid()
    erros: dict[str, list[str]] = {}
    _, campos = ETAPAS[etapa]
    for campo in campos:
        if campo in form.errors:
            erros[campo] = form.errors[campo]

    if etapa == 1:
        if not draft.get("telefones"):
            erros["telefones"] = ["Informe ao menos um telefone/WhatsApp."]
        for i, rede in enumerate(draft.get("redes", [])):
            if rede.get("perfil") and not rede.get("rede_id"):
                erros[f"rede_id_{i}"] = ["Selecione a rede social."]

    if etapa == 3:
        if draft.get("vende_outras_marcas") == "sim" and not draft.get("marcas"):
            erros["marcas"] = ["Selecione ao menos uma marca ou escolha 'Não'."]

    if etapa == 4:
        if not draft.get("interesses"):
            erros["interesses"] = ["Selecione ao menos um produto de interesse."]

    return erros


def draft_de_revendedora(revendedora) -> dict:
    """Preenche o draft a partir de uma revendedora existente (modo edição)."""
    from .models import RedeSocialVinculo

    return {
        "nome_completo": revendedora.nome_completo,
        "email": revendedora.email,
        "data_nascimento": revendedora.data_nascimento.strftime("%d/%m/%Y")
        if revendedora.data_nascimento
        else "",
        "cpf": revendedora.cpf or "",
        "rg": revendedora.rg,
        "cep": revendedora.cep or "",
        "endereco": revendedora.endereco,
        "bairro": revendedora.bairro,
        "cidade_nome": revendedora.cidade.nome,
        "cidade_uf": revendedora.cidade.uf,
        "vende_outras_marcas": "sim" if revendedora.vende_outras_marcas else "nao",
        "telefones": list(revendedora.telefones.values_list("numero", flat=True)),
        "marca_ids": list(revendedora.marcas_revendidas.values_list("id", flat=True)),
        "marca_nova": "",
        "interesses": list(revendedora.interesses.values_list("id", flat=True)),
        "redes": [
            {
                "rede_id": v.rede_id,
                "perfil": v.perfil,
                "contato": v.para_contato,
                "seguir": v.para_seguir,
            }
            for v in RedeSocialVinculo.objects.filter(revendedora=revendedora)
        ],
    }


def opcoes_catalogo():
    """Dados para os templates de chips e selects."""
    return {
        "marcas": Marca.objects.filter(ativa=True),
        "interesses": ProdutoInteresse.objects.filter(ativa=True),
        "redes": RedeSocial.objects.all(),
        "cidades": Cidade.objects.order_by("nome", "uf"),
    }
