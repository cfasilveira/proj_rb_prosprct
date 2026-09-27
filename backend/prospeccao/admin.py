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
