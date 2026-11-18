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
    assert resultados, "nenhum replay retornado; não há jogador para o passo 2"

    replays.passo(2, "Adiciona no campo de usuário um jogador presente nos resultados e repete a busca")
    jogador = resultados[0][1]
    filtrados = replays.buscar(usuario=jogador, formato=FORMATO)

    replays.resultado_esperado(f"os resultados exibidos atendem simultaneamente ao formato {FORMATO} e ao "
                               "usuário informado; cada resultado identifica os participantes.")
    assert filtrados, f"nenhum replay de '{jogador}' em {FORMATO}"
    for formato, p1, p2 in filtrados:
        assert "Random Battle" in formato and "Gen 9" in formato, formato
        assert p1 and p2, f"participantes não identificados: {p1!r} vs. {p2!r}"
        assert jogador.lower() in (p1.lower(), p2.lower()), f"{jogador} não participa de {p1} vs. {p2}"
    replays.ok(f"{len(filtrados)} replays, todos de [Gen 9] Random Battle com '{jogador}' entre os participantes, "
               "cada um identificando os dois jogadores")
