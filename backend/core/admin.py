from django.contrib import admin

from .models import AuditLog, Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "user", "role", "territorio", "ativo"]
    list_filter = ["role", "ativo"]
    search_fields = ["nome_completo", "user__email"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["model", "obj_id", "acao", "user", "criado_em"]
    list_filter = ["model", "acao"]
    readonly_fields = ["user", "model", "obj_id", "acao", "payload", "criado_em"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
