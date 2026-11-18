import pytest

from pages.replays_page import ReplaysPage

FORMATO = "gen9randombattle"


@pytest.mark.ct("CT_0002")
def test_ct0002_buscar_replays_por_usuario_e_formato(driver):
    """Buscar replays por usuário e formato"""
    replays = ReplaysPage(driver)
    replays.abrir_busca()
    if replays.indisponivel():
        pytest.skip("replay.pokemonshowdown.com está fora do ar e a busca depende da API do servidor")

    replays.passo(1, f'Informa somente o formato "{FORMATO}" e clica em "Search"')
    resultados = replays.buscar(formato=FORMATO)
    assert f"format={FORMATO}" in driver.current_url
    assert resultados, "nenhum replay retornado"
    assert all("Random Battle" in f and "Gen 9" in f for f, *_ in resultados), resultados
    replays.ok(f"{len(resultados)} replays, todos de [Gen 9] Random Battle; URL {driver.current_url}")

    replays.passo(2, "Adiciona um jogador dos resultados e repete a busca")
    jogador = resultados[0][1]
    filtrados = replays.buscar(usuario=jogador, formato=FORMATO)
    assert filtrados
    for formato, p1, p2 in filtrados:
        assert "Random Battle" in formato
        assert jogador.lower() in (p1.lower(), p2.lower()), f"{jogador} não participa de {p1} vs. {p2}"
    replays.ok(f"{len(filtrados)} replays de '{jogador}' em {FORMATO}, cada um com os dois participantes")
