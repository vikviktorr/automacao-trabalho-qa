import re

import pytest

from pages.ladder_page import LadderPage


@pytest.mark.ct("CT_0001")
def test_ct0001_ranking_da_ladder_por_formato(driver):
    """Consultar ranking da ladder por formato"""
    ladder = LadderPage(driver)

    ladder.passo(1, 'Acessa a página de ladder do formato "OverUsed" (gen9ou)')
    ladder.abrir_formato("gen9ou")
    titulo = ladder.titulo()

    ladder.passo(2, "Confere a posição e o Elo dos 10 primeiros colocados")
    linhas = ladder.linhas(10)
    posicoes = [p for p, _, _, _ in linhas]
    elos = [e for _, _, e, _ in linhas]

    ladder.passo(3, "Clica no nome do primeiro colocado")
    _, nome, _, link = linhas[0]
    id_usuario = re.sub(r"[^a-z0-9]", "", nome.lower())
    href = ladder.abrir_perfil(link)

    ladder.resultado_esperado("a ladder exibe o formato selecionado; a ordenação observada é conferível "
                              "e o perfil aberto corresponde ao jogador selecionado.")
    assert "OverUsed" in titulo, titulo
    ladder.ok(f"ladder do formato selecionado exibida: '{titulo}'")
    assert posicoes == list(range(1, len(linhas) + 1)), f"posições com salto: {posicoes}"
    assert elos == sorted(elos, reverse=True), f"Elo fora de ordem: {elos}"
    ladder.ok(f"ordenação conferida: posições {posicoes[0]}..{posicoes[-1]} em sequência, Elo decrescente {elos}")
    assert href.rstrip("/").endswith("/users/" + id_usuario)
    assert driver.current_url.rstrip("/").endswith("/users/" + id_usuario)
    if ladder.usando_arquivo:
        ladder.nota("Perfil não arquivado no Web Archive: validado apenas o link/URL do perfil.")
    else:
        # o perfil abre em um painel ao lado da ladder, sem recarregar a página
        ladder.esperar_perfil(nome)
    ladder.ok(f"perfil aberto em {driver.current_url} corresponde ao jogador selecionado ('{nome}')")
