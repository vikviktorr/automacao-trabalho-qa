#!/usr/bin/env bash
# Roda a suíte com o Firefox visível, pausas e destaque dos elementos, e abre o relatório no final.
# Uso:  ./apresentacao.sh                 -> todos os casos automatizados
#       ./apresentacao.sh -k ct0007       -> só um caso
#       ./apresentacao.sh tests/test_batalha.py -> só uma área
#       ./apresentacao.sh --pausa 2       -> mais devagar
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/pytest ]; then
    echo ">> Preparando ambiente (só na primeira vez)..."
    python3 -m venv .venv
    .venv/bin/pip install -q -r requirements.txt
fi

clear
echo "=============================================================="
echo "  Pokémon Showdown - testes automatizados (Selenium + Firefox)"
echo "  12 casos: CT_0001 a CT_0012 (documento qatrabalho_revisado_QA.docx)"
echo "=============================================================="

set +e
.venv/bin/pytest --demo -s "$@"
resultado=$?
set -e

echo
echo ">> Relatório: reports/relatorio.html   Evidências: evidencias/"
xdg-open reports/relatorio.html >/dev/null 2>&1 || true
exit $resultado
