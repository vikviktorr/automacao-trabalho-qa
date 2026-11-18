import re

import pytest

from pages.ladder_page import LadderPage


@pytest.mark.ct("CT_0001")
def test_ct0001_ranking_da_ladder_por_formato(driver):
    """Consultar ranking da ladder por formato"""
    ladder = LadderPage(driver)

    ladder.passo(1, 'Acessa a ladder do formato "OverUsed" (gen9ou)')
    ladder.abrir_formato("gen9ou")
    assert "OverUsed" in ladder.titulo()
    colunas = ladder.colunas()
    for coluna in ["Name", "Elo", "GXE", "Glicko-1", "COIL"]:
        assert coluna in colunas, f"coluna {coluna} ausente: {colunas}"
    ladder.ok(f"tabela carregada com as colunas {colunas}")

    ladder.passo(2, "Confere posição e Elo dos 10 primeiros colocados")
    linhas = ladder.linhas(10)
    posicoes = [p for p, _, _, _ in linhas]
    elos = [e for _, _, e, _ in linhas]
    assert posicoes == list(range(1, len(linhas) + 1)), f"posições com salto: {posicoes}"
    assert elos == sorted(elos, reverse=True), f"Elo fora de ordem: {elos}"
    ladder.ok(f"posições {posicoes[0]}..{posicoes[-1]} em sequência; Elo decrescente {elos}")

    ladder.passo(3, "Clica no nome do primeiro colocado")
    _, nome, _, link = linhas[0]
    id_usuario = re.sub(r"[^a-z0-9]", "", nome.lower())
    href = ladder.abrir_perfil(link)
    assert href.rstrip("/").endswith("/users/" + id_usuario)
    assert driver.current_url.rstrip("/").endswith("/users/" + id_usuario)
    if ladder.usando_arquivo:
        ladder.nota("Perfil não arquivado no Web Archive: validado apenas o link/URL do perfil.")
    else:
        # o perfil abre em um painel ao lado da ladder, sem recarregar a página
        perfil = ladder.esperar_perfil(nome)
        assert "gen9ou" in perfil, f"pontuação do formato ausente no perfil: {perfil[:200]}"
    ladder.ok(f"perfil de '{nome}' aberto em {driver.current_url}, com as pontuações por formato")
