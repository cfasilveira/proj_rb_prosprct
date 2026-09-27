"""Modelos de núcleo: perfil de usuário e auditoria (Backend_Schema §2.1, §2.11)."""
from django.conf import settings
from django.db import models


class Perfil(models.Model):
    """Perfil 1:1 com User: papel no sistema e dados complementares."""

    ROLE_PROMOTORA = "promotora"
    ROLE_GESTOR = "gestor"
    ROLE_CHOICES = [
        (ROLE_PROMOTORA, "Promotora"),
        (ROLE_GESTOR, "Gestor"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PROMOTORA)
    nome_completo = models.CharField(max_length=120)
    territorio = models.CharField(max_length=120, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfis"

    def __str__(self) -> str:
        return f"{self.nome_completo} ({self.get_role_display()})"

    @property
    def is_gestor(self) -> bool:
        return self.role == self.ROLE_GESTOR


class AuditLog(models.Model):
    """Registro de auditoria de mudanças em entidades críticas (RNF-05)."""

    ACAO_CHOICES = [("create", "criação"), ("update", "edição"), ("delete", "exclusão")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias",
    )
    model = models.CharField(max_length=64)
    obj_id = models.BigIntegerField()
    acao = models.CharField(max_length=16, choices=ACAO_CHOICES)
    payload = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "registro de auditoria"
        verbose_name_plural = "registros de auditoria"
        indexes = [
            models.Index(fields=["model", "obj_id"], name="ix_audit_model_obj"),
            models.Index(fields=["criado_em"], name="ix_audit_criado"),
        ]

    def __str__(self) -> str:
        return f"{self.model}#{self.obj_id} {self.acao}"
