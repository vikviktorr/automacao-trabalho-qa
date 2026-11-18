import pytest

from pages.teambuilder_page import TeambuilderPage

PASTA = "Ranqueada"

TIME = """Garchomp @ Rocky Helmet
Ability: Rough Skin
Tera Type: Steel
EVs: 252 HP / 4 Def / 252 Spe
Jolly Nature
- Earthquake
- Dragon Tail
- Stealth Rock
- Spikes

Pikachu @ Light Ball
Ability: Static
Tera Type: Electric
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
IVs: 0 Atk
- Thunderbolt
- Volt Switch
- Surf
- Grass Knot
"""

# pré-condição de CT_0005 e CT_0006: dois times completos já salvos
TIMES_SALVOS = [
    ("Time Ofensivo", "gen9ou", TIME),
    ("Time Defensivo", "gen9ou", "Corviknight @ Leftovers\nAbility: Pressure\n- Roost\n- Brave Bird\n- U-turn\n- Defog\n"),
]


@pytest.mark.ct("CT_0005")
def test_ct0005_organizar_times_em_pastas(driver):
    """Organizar times em pastas no Teambuilder"""
    tb = TeambuilderPage(driver)
    tb.abrir_teambuilder()
    tb.criar_times_salvos(TIMES_SALVOS)

    tb.passo(1, 'Clica em "(add folder)" na lateral do Teambuilder')
    tb.clicar_add_folder()
    assert "Folder name:" in tb.texto_popup()
    tb.ok('janela pedindo o nome da pasta ("Folder name:") exibida')

    tb.passo(2, f'Informa o nome "{PASTA}" e confirma')
    tb.confirmar_nome_da_pasta(PASTA)
    pastas = tb.pastas()
    assert PASTA in pastas, pastas
    assert pastas.index("Folders") < pastas.index(PASTA) if "Folders" in pastas else True
    tb.ok(f"pasta criada e exibida na seção Folders da lateral: {pastas}")

    tb.passo(3, "Arrasta um dos times para a pasta criada")
    tb.selecionar_pasta("all")
    tb.arrastar_time_para_pasta(0, f"{PASTA}/")
    tb.resultado_esperado("Move o time para a pasta e atualiza a listagem.")
    tb.wait.until(lambda d: f"{PASTA}/Time Ofensivo" in " ".join(tb.nomes_dos_times()))
    salvos = {nome: pasta for nome, pasta, *_ in tb.times_salvos()}
    assert salvos == {"Time Ofensivo": PASTA, "Time Defensivo": ""}, salvos
    tb.ok(f"time movido para a pasta e listagem atualizada: {tb.nomes_dos_times()}")

    # o resumo do caso também pede a listagem filtrada pela pasta
    tb.selecionar_pasta(f"{PASTA}/")
    assert PASTA in tb.titulo_da_listagem()
    assert tb.quantidade_de_times() == 1 and "Time Ofensivo" in tb.nomes_dos_times()[0], tb.nomes_dos_times()
    tb.ok(f"ao abrir a pasta '{PASTA}' a listagem mostra só o time movido")


@pytest.mark.ct("CT_0006")
def test_ct0006_duplicar_time_para_uma_pasta_criada(driver):
    """Duplicar time para uma pasta criada"""
    tb = TeambuilderPage(driver)
    tb.abrir_teambuilder()
    tb.criar_times_salvos(TIMES_SALVOS)
    tb.clicar_add_folder()
    tb.confirmar_nome_da_pasta(PASTA)  # pré-condição: pasta criada
    tb.selecionar_pasta("all")
    original = tb.times_salvos()[0]

    tb.passo(1, 'Clica no botão de duplicar do "Time Ofensivo" na listagem')
    tb.duplicar_time(0)
    assert tb.nome_em_edicao() == "Copy of Time Ofensivo", tb.nome_em_edicao()
    assert tb.times_salvos()[0][0] == "Copy of Time Ofensivo", tb.times_salvos()
    tb.ok("cópia 'Copy of Time Ofensivo' criada no topo da lista e aberta para edição")
    tb.voltar_para_lista()

    tb.passo(2, "Leva a cópia para a pasta criada")
    tb.arrastar_time_para_pasta(0, f"{PASTA}/")
    tb.selecionar_pasta(f"{PASTA}/")
    assert PASTA in tb.titulo_da_listagem()
    assert tb.quantidade_de_times() == 1 and "Copy of Time Ofensivo" in tb.nomes_dos_times()[0], tb.nomes_dos_times()
    tb.ok(f"pasta '{PASTA}' aberta contendo a cópia: {tb.nomes_dos_times()}")
    tb.nota('O botão "Paste copy here" citado no passo 3 do documento não existe no Teambuilder; '
            "a cópia é levada para a pasta arrastando-a, que é o recurso oferecido pelo site.")

    tb.passo(3, "Confere o time original e a cópia na pasta")
    tb.resultado_esperado("Mantém o time original sem nenhuma alteração, além de criar uma nova cópia "
                          "para a pasta selecionada.")
    salvos = tb.times_salvos()
    copia = next(t for t in salvos if t[0] == "Copy of Time Ofensivo")
    atual = next(t for t in salvos if t[0] == "Time Ofensivo")
    assert atual == original, f"o original mudou: {original} -> {atual}"
    assert copia[1] == PASTA and copia[3] == original[3], copia
    assert len(salvos) == 3
    tb.ok("original sem nenhuma alteração (fora da pasta, mesmos Pokémon) e cópia idêntica dentro da pasta")
