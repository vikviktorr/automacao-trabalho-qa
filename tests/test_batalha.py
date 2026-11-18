import pytest

from pages.battle_page import iniciar_batalha

# Os casos de batalha usam duas sessões de teste (o "jogador" e o "oponente"), cada uma num navegador.
# A partida começa por desafio direto entre elas, privada (sem espectadores), para nunca envolver
# jogadores reais da fila. No fim de cada caso a partida é encerrada.


@pytest.fixture
def batalha(driver, outra_sessao):
    try:
        jogador, oponente, nome_j, nome_o = iniciar_batalha(driver, outra_sessao)
    except AssertionError as erro:
        if "you are limited to" in str(erro):
            # limite do servidor (12 batalhas a cada 3 minutos por conexão); acontece ao repetir a suíte em sequência
            pytest.skip("o servidor limitou novas batalhas por alguns minutos (\"Due to high load...\"); rode de novo depois")
        raise
    yield jogador, oponente, nome_j, nome_o
    jogador.desistir_se_em_andamento()


def passo_1_abrir_batalha(jogador, nome_j, nome_o):
    jogador.passo(1, f"Abre a batalha ({nome_j} desafiou {nome_o} em [Gen 9] Random Battle)")
    meus, deles = jogador.icones_dos_times()
    assert (meus, deles) == (6, 6), f"ícones dos times: {meus} x {deles}"
    assert f"Battle started between {nome_j} and {nome_o}" in jogador.log()
    jogador.ok("batalha aberta mostrando os seis Pokémon de cada lado")


@pytest.mark.ct("CT_0007")
def test_ct0007_mudar_o_pokemon_durante_o_combate(batalha):
    """Mudar o Pokémon durante o combate"""
    jogador, oponente, nome_j, nome_o = batalha
    passo_1_abrir_batalha(jogador, nome_j, nome_o)

    jogador.passo(2, 'Seleciona um dos Pokémon que aparecem embaixo de "Switch"')
    em_campo, reservas = jogador.ativo(), jogador.reservas()
    escolhido = reservas[0]
    jogador.trocar_para(escolhido)
    jogador.aguardando_oponente()
    aviso = next(l for l in jogador.texto_dos_controles().splitlines() if "will switch in" in l)
    # o aviso pode trazer a forma do Pokémon (ex.: "Giratina-Origin") em vez do nome do botão
    assert aviso.startswith(escolhido) and f"replacing {em_campo}" in aviso, aviso
    jogador.ok(f"escolha registrada ('{aviso}') e aguardando o adversário")

    jogador.passo(3, "Espera o turno até a troca acontecer")
    golpe = oponente.jogar_turno(0)  # o oponente decide a ação dele para o turno andar
    jogador.esperar_turno(2, oponente)
    log = jogador.log()
    # o log pode trazer a forma entre parênteses, ex.: "Go! Arceus (Arceus-Dragon)!"
    assert f"{em_campo}, come back!" in log and f"Go! {escolhido}" in log, log[-400:]
    jogador.esperar_acoes()
    if f"{escolhido} fainted" in log:
        # o golpe do oponente nocauteou quem entrou; o teste fez a troca obrigatória para seguir
        jogador.nota(f"{escolhido} entrou e foi nocauteado no mesmo turno; a troca em si foi confirmada pelo log.")
    else:
        assert jogador.ativo() == escolhido
    assert em_campo in jogador.reservas(), f"{em_campo} não voltou para o banco: {jogador.reservas()}"
    jogador.ok(f"{escolhido} entrou em campo (log: 'Go! {escolhido}!'); {em_campo} voltou para o banco "
               f"e continua disponível; o oponente usou {golpe}")


@pytest.mark.ct("CT_0008")
def test_ct0008_terastalizar_pokemon_durante_a_batalha(batalha):
    """Terastalizar Pokémon durante a batalha"""
    jogador, oponente, nome_j, nome_o = batalha
    passo_1_abrir_batalha(jogador, nome_j, nome_o)

    jogador.passo(2, 'Clica em "Tera" (Terastallize)')
    caixa = jogador.caixa_tera()
    tipo = jogador.tipo_tera()
    jogador.clicar(caixa)
    assert caixa.is_selected(), "a opção Terastallize não ficou marcada"
    jogador.ok(f"opção Terastallize marcada; Tera Type definido no time: {tipo}")

    jogador.passo(3, "Seleciona um dos 4 golpes disponíveis")
    pokemon = jogador.ativo()
    assert len(jogador.golpes()) == 4, jogador.golpes()
    if not jogador.caixa_tera().is_selected():
        jogador.clicar(jogador.caixa_tera())  # os controles foram redesenhados e a marcação se perdeu
    golpe = jogador.usar_golpe(0)
    jogador.aguardando_oponente()
    oponente.jogar_turno(0)
    jogador.esperar_turno(2, oponente)
    assert "has Terastallized into" in jogador.log(), f"o Pokémon não terastalizou: {jogador.log()[-400:]}"
    linha = next(l for l in jogador.log().splitlines() if "has Terastallized into" in l)
    assert pokemon in linha and tipo in linha, linha
    jogador.esperar_acoes()
    assert not jogador.visiveis(f"{jogador.sala} .battle-controls input[name=terastallize]"), "Tera continua disponível"
    jogador.ok(f"log: '{linha.strip()}' ao usar {golpe}; a opção Tera não aparece mais")


@pytest.mark.ct("CT_0009")
def test_ct0009_desistir_de_uma_batalha_em_andamento(batalha):
    """Desistir de uma batalha em andamento"""
    jogador, oponente, nome_j, nome_o = batalha
    passo_1_abrir_batalha(jogador, nome_j, nome_o)

    jogador.passo(2, "Tenta fechar a aba da batalha em andamento")
    jogador.fechar_aba()
    texto = jogador.texto_popup()
    assert "Forfeiting makes you lose the battle" in texto and "Forfeit" in texto, texto
    jogador.ok(f"janela pedindo confirmação da desistência: '{texto.splitlines()[0]}'")

    jogador.passo(3, 'Seleciona "Forfeit"')
    jogador.confirmar_desistencia(fechar_sala=False)  # mantém a sala aberta para conferir o log
    jogador.esperar_no_log(f"{nome_o} won the battle!")
    log = jogador.log()
    assert f"{nome_j} forfeited." in log, log[-300:]
    oponente.esperar_no_log(f"{nome_o} won the battle!")
    assert not jogador.visiveis(f"{jogador.sala} .battle-controls button[name=chooseMove]")
    jogador.ok(f"batalha encerrada: log com '{nome_j} forfeited.' e '{nome_o} won the battle!' (também na tela do adversário)")
