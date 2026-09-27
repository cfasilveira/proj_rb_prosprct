"""Forms de contas: login com checagem de ativo e gestão de promotoras (RF-02)."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from core.models import Perfil

User = get_user_model()


class AtivoAuthenticationForm(AuthenticationForm):
    """Impede login de promotoras desativadas (RF-02); campo exibido como e-mail."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "E-mail"
        self.fields["username"].widget.attrs.update({
            "autocomplete": "email",
            "placeholder": "email@exemplo.com",
        })
        self.fields["password"].widget.attrs.update({"placeholder": "Senha"})

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        perfil = getattr(user, "perfil", None)
        if perfil and not perfil.ativo:
            raise forms.ValidationError(
                "Esta conta foi desativada. Fale com o gestor.", code="inactive",
            )


class PromotoraForm(forms.Form):
    nome_completo = forms.CharField(
        max_length=120, label="Nome completo *",
        widget=forms.TextInput(attrs={"placeholder": "Nome e sobrenome"}),
    )
    email = forms.EmailField(label="E-mail *", widget=forms.EmailInput(attrs={"placeholder": "email@exemplo.com"}))
    territorio = forms.CharField(
        required=False, max_length=120, label="Território",
        widget=forms.TextInput(attrs={"placeholder": "Cidade/UF que cobre"}),
    )
    senha = forms.CharField(
        required=False, label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Deixe vazio para manter"}),
        help_text="Obrigatória ao criar. Mínimo de 6 caracteres.",
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance:
            self.fields["senha"].required = False

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").lower()
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean_senha(self):
        senha = self.cleaned_data.get("senha", "")
        if not self.instance and len(senha) < 6:
            raise forms.ValidationError("A senha deve ter ao menos 6 caracteres.")
        if senha and len(senha) < 6:
            raise forms.ValidationError("A senha deve ter ao menos 6 caracteres.")
        return senha

    def save(self):
        dados = self.cleaned_data
        if self.instance:
            user = self.instance.user
            user.email = dados["email"]
            if dados["senha"]:
                user.set_password(dados["senha"])
            user.save()
            perfil = self.instance
            perfil.nome_completo = dados["nome_completo"]
            perfil.territorio = dados["territorio"]
            perfil.save()
            return perfil

        user = User.objects.create_user(
            email=dados["email"],
            username=dados["email"],
            password=dados["senha"],
        )
        perfil = user.perfil
        perfil.nome_completo = dados["nome_completo"]
        perfil.territorio = dados["territorio"]
        perfil.role = Perfil.ROLE_PROMOTORA
        perfil.save()
        return perfil
