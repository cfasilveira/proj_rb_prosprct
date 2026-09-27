"""Queries das análises A1–A4 (docs/Backend_Schema.md §4).

Sem dependência de Streamlit — testáveis com pytest sobre o Postgres real.
Todos os módulos aceitam o mesmo dicionário de parâmetros:

    {"de": date|None, "ate": date|None,
     "promotora_id": int|None, "cidade_id": int|None}
"""

SQL_BASE = """
WITH base AS (
    SELECT r.id, r.nome_completo, r.ja_revende, r.criado_em,
           r.promotora_id, r.cidade_id,
           c.nome AS cidade_nome, c.uf,
           COALESCE(p.nome_completo, u.email) AS promotora_nome
    FROM prospeccao_revendedora r
    JOIN prospeccao_cidade c ON c.id = r.cidade_id
    JOIN accounts_user u ON u.id = r.promotora_id
    LEFT JOIN core_perfil p ON p.user_id = r.promotora_id
    WHERE r.desativado_em IS NULL
      AND (%(de)s::timestamptz IS NULL OR r.criado_em >= %(de)s::timestamptz)
      AND (%(ate)s::timestamptz IS NULL OR r.criado_em <= %(ate)s::timestamptz)
      AND (%(promotora_id)s::bigint IS NULL OR r.promotora_id = %(promotora_id)s::bigint)
      AND (%(cidade_id)s::bigint IS NULL OR r.cidade_id = %(cidade_id)s::bigint)
)
"""

# A1 — quantidade cadastrada por promotora
SQL_A1 = SQL_BASE + """
SELECT promotora_nome,
       COUNT(*)                                   AS cadastradas,
       COUNT(*) FILTER (WHERE ja_revende)         AS ja_revendem,
       ROUND(100.0 * COUNT(*) FILTER (WHERE ja_revende) / NULLIF(COUNT(*), 0), 1) AS pct
FROM base
GROUP BY promotora_nome
ORDER BY cadastradas DESC, promotora_nome;
"""

# A2 — quantas já revendem (consolidado)
SQL_A2 = SQL_BASE + """
SELECT COUNT(*)                                   AS total,
       COUNT(*) FILTER (WHERE ja_revende)         AS ja_revendem,
       COUNT(*) FILTER (WHERE NOT ja_revende)     AS nao_revendem,
       ROUND(100.0 * COUNT(*) FILTER (WHERE ja_revende) / NULLIF(COUNT(*), 0), 1) AS pct
FROM base;
"""

# A2 por cidade (detalhe secundário)
SQL_A2_CIDADE = SQL_BASE + """
SELECT cidade_nome || '/' || uf AS cidade,
       COUNT(*)                 AS total,
       COUNT(*) FILTER (WHERE ja_revende) AS ja_revendem,
       ROUND(100.0 * COUNT(*) FILTER (WHERE ja_revende) / NULLIF(COUNT(*), 0), 1) AS pct
FROM base
GROUP BY cidade_nome, uf
ORDER BY total DESC;
"""

# A3 — marcas que as revendedoras já revendem
SQL_A3 = SQL_BASE + """
SELECT m.nome AS marca,
       COUNT(*) AS revendedoras,
       ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM base WHERE ja_revende), 0), 1) AS pct
FROM base b
JOIN prospeccao_revendedoramarca rm ON rm.revendedora_id = b.id
JOIN prospeccao_marca m ON m.id = rm.marca_id
GROUP BY m.nome
ORDER BY revendedoras DESC, m.nome;
"""

# A4 — interesse em produtos
SQL_A4 = SQL_BASE + """
SELECT pi.nome AS categoria,
       pi.ordem,
       COUNT(*) AS interessadas,
       ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM base), 0), 1) AS pct
FROM base b
JOIN prospeccao_revendedorainteresse ri ON ri.revendedora_id = b.id
JOIN prospeccao_produtointeresse pi ON pi.id = ri.produto_id
GROUP BY pi.nome, pi.ordem
ORDER BY pi.ordem, interessadas DESC;
"""

QUERIES = {
    "A1": SQL_A1,
    "A2": SQL_A2,
    "A2_CIDADE": SQL_A2_CIDADE,
    "A3": SQL_A3,
    "A4": SQL_A4,
}

PARAMS_PADRAO = {
    "de": None,
    "ate": None,
    "promotora_id": None,
    "cidade_id": None,
}


def params(**kwargs):
    """Monta o dicionário de parâmetros a partir dos filtros informados."""
    saida = dict(PARAMS_PADRAO)
    saida.update({k: v for k, v in kwargs.items() if v not in (None, "")})
    return saida
