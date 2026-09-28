from django.contrib import admin

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


class TelefoneInline(admin.TabularInline):
    model = Telefone
    extra = 1


class RevendedoraMarcaInline(admin.TabularInline):
    model = RevendedoraMarca
    extra = 1


class RevendedoraInteresseInline(admin.TabularInline):
    model = RevendedoraInteresse
    extra = 1


@admin.register(Revendedora)
class RevendedoraAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "promotora", "cidade", "ja_revende", "criado_em"]
    list_filter = ["ja_revende", "cidade", "criado_em"]
    search_fields = ["nome_completo", "cpf", "email"]
    inlines = [TelefoneInline, RevendedoraMarcaInline, RevendedoraInteresseInline]
    readonly_fields = ["ja_revende", "criado_em", "atualizado_em"]
    actions = ["excluir_dados_pessoais"]

    @admin.action(description="Excluir dados pessoais (LGPD RNF-06)")
    def excluir_dados_pessoais(self, request, queryset):
        """Anonimiza em lote; registros já anonimizados são ignorados."""
        a_excluir = [revendedora for revendedora in queryset if not revendedora.anonimizada]
        for revendedora in a_excluir:
            revendedora.excluir_dados_pessoais(usuario=request.user)

        if a_excluir:
            self.message_user(request, f"{len(a_excluir)} revendedora(s) anonimizada(s).")
        else:
            self.message_user(
                request,
                "Nada a fazer: os registros selecionados já estavam anonimizados.",
                level="warning",
            )


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ["nome", "ativa"]
    list_editable = ["ativa"]
    search_fields = ["nome"]


@admin.register(ProdutoInteresse)
class ProdutoInteresseAdmin(admin.ModelAdmin):
    list_display = ["nome", "ordem", "ativa"]
    list_editable = ["ordem", "ativa"]
    ordering = ["ordem"]


admin.site.register([Cidade, RedeSocial, RedeSocialVinculo])
