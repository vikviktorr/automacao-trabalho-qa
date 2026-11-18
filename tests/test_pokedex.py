import pytest

from pages.dex_page import DexPage


@pytest.mark.ct("CT_0003")
def test_ct0003_listar_pokemon_que_aprendem_um_golpe(driver):
    """Listar Pokémon que aprendem um golpe"""
    dex = DexPage(driver)

    dex.passo(1, 'Pesquisa "Stealth Rock" na Pokédex e abre o resultado')
    dex.abrir_inicio()
    dex.pesquisar("Stealth Rock")
    dex.abrir_resultado("move|Stealth Rock")
    assert "Stealth Rock" in dex.titulo()

    dex.passo(2, "Confere os dados principais do golpe")
    tipo = dex.texto(".dexentry dl.movetypeentry dd")
    pp = dex.texto(".dexentry dl.ppentry dd")
    assert tipo and pp, "atributos do golpe não exibidos"
    dex.ok(f"atributos exibidos: tipo/categoria {tipo}; PP {pp}")

    dex.passo(3, "Rola até a lista de Pokémon que aprendem o golpe")
    dex.resultado_esperado("Agrupa as espécies por método (Level-up, TM/HM, Egg e outros) e inclui Pokémon que "
                           "aprendem o golpe, como Garchomp, cada um com link para a própria página.")
    grupos = dex.grupos_aprendizado()
    assert "Level-up" in grupos and "TM/HM" in grupos, grupos
    garchomp = dex.rolar_ate_pokemon("Garchomp")
    assert garchomp is not None, "Garchomp não aparece na lista"
    assert garchomp.get_attribute("href").endswith("/pokemon/garchomp")
    dex.ok(f"grupos {grupos}; Garchomp listado em '{dex.grupo_do_item(garchomp)}' com link próprio")
