"""Ajustes de import para os testes que exercitam o app Streamlit.

As páginas em `analytics/pages/` usam imports chapados (`import db`,
`import graficos`, `from ui import ...`) porque o Streamlit roda com o
diretório `analytics/` no `sys.path`. Os testes precisam do mesmo caminho
para carregar esses módulos.
"""
import sys
from pathlib import Path

_ANALYTICS = Path(__file__).resolve().parents[2] / "analytics"
if str(_ANALYTICS) not in sys.path:
    sys.path.insert(0, str(_ANALYTICS))
