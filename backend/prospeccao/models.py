"""Modelos de prospecção (docs/Backend_Schema.md §2)."""
from __future__ import annotations

import re
from unicodedata import normalize

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from localflavor.br.br_states import STATE_CHOICES

apenas_digitos = RegexValidator(r"^\d+$", "Use apenas dígitos.")
valida_cpf = RegexValidator(r"^\d{11}$", "CPF deve ter 11 dígitos (sem pontos/hífen).")
valida_cep = RegexValidator(r"^\d{8}$", "CEP deve ter 8 dígitos (sem hífen).")


class Cidade(models.Model):
    """Cidade normalizada para agregação nas análises (schema §2.3)."""

    nome = models.CharField(max_length=80)
    uf = models.CharField(max_length=2, choices=STATE_CHOICES)
    nome_norm = models.CharField(max_length=80, editable=False)

    class Meta:
        verbose_name = "cidade"
        verbose_name_plural = "cidades"
        ordering = ["nome", "uf"]
        constraints = [
            models.UniqueConstraint(fields=["nome_norm", "uf"], name="uniq_cidade_nome_uf")
        ]

    def save(self, *args, **kwargs):
        self.nome_norm = normalize("NFKD", self.nome).encode("ascii", "ignore").decode().lower().strip()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.nome}/{self.uf}"


class Marca(models.Model):
    """Marca que a revendedora já revende (alimenta análise A3)."""

    nome = models.CharField(max_length=80, unique=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "marca"
        verbose_name_plural = "marcas"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class ProdutoInteresse(models.Model):
    """Categoria de produto de interesse (alimenta análise A4)."""

    nome = models.CharField(max_length=60, unique=True)
    ordem = models.SmallIntegerField(default=0)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "produto de interesse"
        verbose_name_plural = "produtos de interesse"
        ordering = ["ordem", "nome"]

    def __str__(self) -> str:
        return self.nome


class RedeSocial(models.Model):
    """Catálogo de redes sociais (schema §2.9)."""

    nome = models.CharField(max_length=40, unique=True)

    class Meta:
        verbose_name = "rede social"
        verbose_name_plural = "redes sociais"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Revendedora(models.Model):
    """Entidade central: revendedora cadastrada em campo (schema §2.2)."""

    promotora = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="revendedoras",
        verbose_name="promotora",
    )
    nome_completo = models.CharField(max_length=120, verbose_name="nome completo")
    cpf = models.CharField(
        max_length=11,
        null=True,
        blank=True,
        unique=True,
        validators=[valida_cpf],
        verbose_name="CPF",
    )
    rg = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    data_nascimento = models.DateField(
        null=True, blank=True, verbose_name="data de nascimento"
    )
    endereco = models.CharField(max_length=160, blank=True, verbose_name="endereço")
    bairro = models.CharField(max_length=80, blank=True)
    cidade = models.ForeignKey(
        Cidade, on_delete=models.PROTECT, related_name="revendedoras", verbose_name="cidade"
    )
    cep = models.CharField(
        max_length=8, blank=True, validators=[valida_cep], verbose_name="CEP"
    )
    vende_outras_marcas = models.BooleanField(default=False, verbose_name="vende outras marcas")
    ja_revende = models.BooleanField(default=False, verbose_name="já revende")
    observacao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    desativado_em = models.DateTimeField(null=True, blank=True, verbose_name="desativada em")

    marcas_revendidas = models.ManyToManyField(
        Marca,
        through="RevendedoraMarca",
        related_name="revendedoras",
        verbose_name="marcas revendidas",
    )
    interesses = models.ManyToManyField(
        ProdutoInteresse,
        through="RevendedoraInteresse",
        related_name="revendedoras",
        verbose_name="interesses",
    )

    class Meta:
        verbose_name = "revendedora"
        verbose_name_plural = "revendedoras"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["promotora", "criado_em"], name="ix_revend_promotora"),
            models.Index(fields=["ja_revende"], name="ix_revend_ja_revende"),
            models.Index(fields=["cidade"], name="ix_revend_cidade"),
        ]

    def __str__(self) -> str:
        return self.nome_completo

    def clean(self):
        super().clean()
        if self.data_nascimento and self.data_nascimento > timezone.localdate():
            raise ValidationError({"data_nascimento": "Data de nascimento não pode ser futura."})
        if self.email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", self.email):
            raise ValidationError({"email": "E-mail inválido."})

    def desativar(self):
        """Exclusão lógica (RF-03, schema §2.5)."""
        self.desativado_em = timezone.now()
        self.save(update_fields=["desativado_em", "atualizado_em"])

    @property
    def ativa(self) -> bool:
        return self.desativado_em is None

    def atualizar_ja_revende(self):
        """Recalcula a flag derivada (RF-04.1) a partir das marcas revendidas."""
        novo = self.marcas_revendidas.exists()
        if novo != self.ja_revende:
            self.ja_revende = novo
            self.save(update_fields=["ja_revende", "atualizado_em"])

    @classmethod
    def para_promotora(cls, user):
        """Escopo de acesso da promotora (RF-05.1) - usar sempre nas views."""
        return cls.objects.filter(promotora=user, desativado_em__isnull=True)

    @classmethod
    def ativas(cls):
        return cls.objects.filter(desativado_em__isnull=True)


class RevendedoraMarca(models.Model):
    """N:N revendedora × marca (schema §2.6)."""

    revendedora = models.ForeignKey(
        Revendedora, on_delete=models.CASCADE, related_name="marcas_vinculadas"
    )
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name="vinculos")

    class Meta:
        verbose_name = "marca da revendedora"
        verbose_name_plural = "marcas das revendedoras"
        constraints = [
            models.UniqueConstraint(
                fields=["revendedora", "marca"], name="uniq_revend_marca"
            )
        ]

    def __str__(self) -> str:
        return f"{self.revendedora} → {self.marca}"


class RevendedoraInteresse(models.Model):
    """N:N revendedora × produto de interesse (schema §2.8)."""

    revendedora = models.ForeignKey(
        Revendedora, on_delete=models.CASCADE, related_name="interesses_vinculados"
    )
    produto = models.ForeignKey(
        ProdutoInteresse, on_delete=models.CASCADE, related_name="vinculos"
    )

    class Meta:
        verbose_name = "interesse da revendedora"
        verbose_name_plural = "interesses das revendedoras"
        constraints = [
            models.UniqueConstraint(
                fields=["revendedora", "produto"], name="uniq_revend_produto"
            )
        ]

    def __str__(self) -> str:
        return f"{self.revendedora} → {self.produto}"


class Telefone(models.Model):
    """Telefone/WhatsApp da revendedora (schema §2.4, RF-03.4)."""

    TIPO_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("telefone", "Telefone"),
        ("outro", "Outro"),
    ]

    revendedora = models.ForeignKey(
        Revendedora, on_delete=models.CASCADE, related_name="telefones"
    )
    numero = models.CharField(
        max_length=11, validators=[apenas_digitos], verbose_name="número"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="whatsapp")
    principal = models.BooleanField(default=False)

    class Meta:
        verbose_name = "telefone"
        verbose_name_plural = "telefones"
        constraints = [
            models.UniqueConstraint(
                fields=["revendedora", "numero"], name="uniq_revend_telefone"
            )
        ]
        indexes = [models.Index(fields=["numero"], name="ix_telefone_numero")]

    def clean(self):
        super().clean()
        if len(self.numero) < 10:
            raise ValidationError({"numero": "Telefone deve ter DDD + número (mín. 10 dígitos)."})

    def __str__(self) -> str:
        return self.numero


class RedeSocialVinculo(models.Model):
    """N:N com atributo: rede social da revendedora (schema §2.10, RF-03.6)."""

    revendedora = models.ForeignKey(
        Revendedora, on_delete=models.CASCADE, related_name="redes"
    )
    rede = models.ForeignKey(RedeSocial, on_delete=models.CASCADE, related_name="vinculos")
    perfil = models.CharField(max_length=120, verbose_name="perfil")
    para_contato = models.BooleanField(default=False, verbose_name="para contato")
    para_seguir = models.BooleanField(default=False, verbose_name="para seguir")

    class Meta:
        verbose_name = "rede social da revendedora"
        verbose_name_plural = "redes sociais das revendedoras"
        constraints = [
            models.UniqueConstraint(
                fields=["revendedora", "rede"], name="uniq_revend_rede"
            )
        ]

    def __str__(self) -> str:
        return f"{self.revendedora} @ {self.rede.nome}"
