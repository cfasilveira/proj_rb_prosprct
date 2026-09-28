"""Signals de prospecção: flag derivada `ja_revende` e auditoria (RF-04, RNF-05)."""
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from core.middleware import usuario_atual
from core.models import AuditLog

from .models import Revendedora, RevendedoraMarca


def _recalcula(revendedora_id):
    revendedora = Revendedora.objects.filter(pk=revendedora_id).first()
    if revendedora:
        revendedora.atualizar_ja_revende()


@receiver(m2m_changed, sender=Revendedora.marcas_revendidas.through)
def ja_revende_via_manager(sender, instance, action, reverse, **kwargs):
    """Caminho .add()/.set()/.remove()/.clear() no manager (RF-04.1)."""
    if not reverse and action in {"post_add", "post_remove", "post_clear"}:
        _recalcula(instance.pk)


@receiver([post_save, post_delete], sender=RevendedoraMarca)
def ja_revende_via_through(sender, instance, **kwargs):
    """Caminho direto no modelo through (objects.create()/delete())."""
    _recalcula(instance.revendedora_id)


@receiver(post_save, sender=Revendedora)
def audita_criacao_edicao(sender, instance, created, **kwargs):
    AuditLog.objects.create(
        user=usuario_atual(),
        model="Revendedora",
        obj_id=instance.pk,
        acao="create" if created else "update",
        payload={"nome": instance.nome_completo},
    )


@receiver(post_delete, sender=Revendedora)
def audita_exclusao(sender, instance, **kwargs):
    """Auditoria mínima: sem dado pessoal (RNF-06/LGPD)."""
    AuditLog.objects.create(
        user=usuario_atual(),
        model="Revendedora",
        obj_id=instance.pk,
        acao="delete",
        payload={},
    )
