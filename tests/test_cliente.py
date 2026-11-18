import time

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from pages.battle_page import BattlePage, conectar, nome_de_teste, repetir
from pages.client_page import ClientPage

CONTA_REGISTRADA = "Zarel"
FORMATO_1V1 = "gen9randombattle"
# formato com time aleatório e pouca gente na fila: diminui a chance de parear com alguém antes do Cancel
FORMATO_FILA = "gen9challengecup2v2"


@pytest.mark.ct("CT_0004")
def test_ct0004_escolher_nome_ja_registrado(driver):
    """Escolher nome de usuário já registrado"""
    cliente = ClientPage(driver)
    cliente.abrir_lobby()

    cliente.passo(1, 'Clica em "Choose name"')
    cliente.clicar_choose_name()

    cliente.passo(2, f'Informa o nome já registrado "{CONTA_REGISTRADA}" e confirma em "Choose name"')
    cliente.informar_nome(CONTA_REGISTRADA)
    cliente.resultado_esperado("Identifica que o nome pertence a uma conta registrada e pede a autenticação "
                               "da conta (senha ou login Google) antes de liberar o nome.")
    texto = cliente.esperar_texto_popup("registered")
    assert "The name you chose is registered" in texto, texto
    # o campo de senha é desenhado logo depois do aviso
    try:
        cliente.wait.until(lambda d: cliente.popup_tem_senha() or "If this is your account" in cliente.texto_popup())
    except TimeoutException:
        pytest.fail(f"o cliente não pediu a autenticação: {cliente.texto_popup()}")
    assert cliente.nome_conectado() is None, "o convidado foi conectado com o nome registrado sem senha"
    cliente.ok("o cliente avisa que o nome é registrado, pede a autenticação do dono da conta "
               "('If this is your account') e não conecta o convidado com esse nome")


@pytest.mark.ct("CT_0011")
def test_ct0011_assistir_batalha_como_espectador(driver):
    """Assistir batalha como espectador"""
    cliente = ClientPage(driver)
    cliente.abrir_lobby()

    cliente.passo(1, 'Clica em "Watch a battle"')
    cliente.clicar_watch_a_battle()
    assert cliente.formato_do_filtro() == "(All formats)"
    cliente.ok(f"lista de batalhas em andamento exibida ({cliente.resumo_da_lista()}) com o filtro de formato")
    cliente.filtrar_formato(FORMATO_1V1)
    batalhas = cliente.batalhas_listadas()
    assert batalhas and all(f == "[Random Battle]" for _, f, _, _ in batalhas), batalhas[:5]
    cliente.ok(f"filtro '{cliente.formato_do_filtro()}' aplicado: {len(batalhas)} batalhas, todas de Random Battle")

    cliente.passo(2, "Clica em uma batalha 1v1 em andamento")
    href, _, p1, p2 = batalhas[0]
    sala = cliente.abrir_batalha(href)
    # o log chega do servidor logo depois de a sala abrir
    cliente.wait.until(lambda d: p1 in cliente.log(sala) and p2 in cliente.log(sala))
    turno_inicial = cliente.turno(sala)
    cliente.ok(f"batalha {p1} vs. {p2} carregada no turno {turno_inicial}, com campo, log e "
               f"lista de usuários ({cliente.usuarios_na_sala(sala)})")

    cliente.passo(3, "Acompanha a partida por alguns turnos")
    cliente.resultado_esperado("Atualiza o campo e o log a cada turno, não exibe golpes nem trocas para o "
                               "espectador e permite apenas o uso do chat da batalha.")
    botoes = cliente.botoes_da_batalha(sala)
    assert not {"chooseMove", "chooseSwitch", "chooseTeamPreview"} & set(botoes), botoes
    assert not cliente.visiveis(f"{sala} .movemenu, {sala} .switchmenu"), "o espectador recebeu opções de golpe/troca"
    cliente.ok(f"sem golpes nem trocas para o espectador; controles disponíveis: {botoes}")
    assert cliente.visiveis(f"{sala} .battle-log-add button[name=login], {sala} .battle-log-add textarea"), "chat da batalha ausente"
    cliente.ok("chat da batalha disponível para o espectador (pede um nome antes de enviar mensagens)")
    try:
        WebDriverWait(driver, 120).until(lambda d: cliente.turno(sala) > turno_inicial or "won the battle" in cliente.log(sala))
    except TimeoutException:
        pytest.fail(f"a batalha não avançou em 2 minutos (continua no turno {turno_inicial})")
    cliente.ok(f"campo e log atualizados em tempo real: turno {turno_inicial} -> {cliente.turno(sala)}")


@pytest.mark.ct("CT_0010")
def test_ct0010_cancelar_busca_de_partida_na_fila(driver):
    """Cancelar busca de partida na fila"""
    cliente = conectar(driver, nome_de_teste("QA Fila"))  # pré-condição: usuário com nome
    cliente.escolher_formato_da_fila(FORMATO_FILA, "challenge cup 2v2")

    cliente.passo(1, 'Clica em "Battle!"')
    cliente.clicar_battle()
    # o cliente espera ~3 s antes de pedir a busca ao servidor; depois mostra "Searching..."
    cliente.wait.until(lambda d: "Searching" in cliente.texto_da_busca() or cliente.em_batalha())
    if cliente.em_batalha():
        BattlePage(driver, cliente.esperar_sala_de_batalha()).desistir_se_em_andamento()
        pytest.skip("um adversário foi encontrado antes do Cancel; a partida foi encerrada e o caso não pôde ser verificado")
    assert cliente.visiveis(".mainmenu button[name=cancelSearch]")
    cliente.ok('usuário na fila: status "Searching..." com o botão "Cancel"')

    cliente.passo(2, 'Clica em "Cancel" antes de um oponente ser encontrado')
    cliente.cancelar_busca()
    cliente.wait.until(lambda d: "Battle!" in cliente.texto_da_busca() and not cliente.visiveis(".mainmenu button[name=cancelSearch]"))
    cliente.ok('busca cancelada e o botão "Battle!" voltou a ser exibido')

    cliente.passo(3, "Permanece um minuto na tela principal")
    cliente.resultado_esperado("Não inicia nenhuma batalha nem abre aba de partida, confirmando que a busca "
                               "foi encerrada no servidor.")
    for _ in range(60):
        assert not cliente.em_batalha(), "uma batalha foi aberta depois do Cancel"
        time.sleep(1)
    assert "Battle!" in cliente.texto_da_busca()
    cliente.ok("nenhuma batalha iniciada nem aba de partida aberta em 60 s: a busca foi encerrada no servidor")


@pytest.mark.ct("CT_0012")
def test_ct0012_abrir_chat_com_outro_usuario(driver, outra_sessao):
    """Abrir chat com outro usuário"""
    nome_outro = nome_de_teste("QA Contato")
    conectar(outra_sessao, nome_outro)  # pré-condição: o outro usuário conectado em outra sessão
    cliente = conectar(driver, nome_de_teste("QA Usuario"))

    cliente.passo(1, 'Clica em "Find a user"')
    # a janela é desenhada em etapas: repete a leitura se o campo for redesenhado no meio dela
    assert repetir(lambda: cliente.campo_de_busca_de_usuario().is_enabled())
    cliente.ok("janela para preencher o nome do usuário exibida")

    cliente.passo(2, f'Preenche com o nome "{nome_outro}" e clica em "Open" (look up)')
    repetir(lambda: cliente.digitar(f"{cliente.POPUP} input[name=data]", nome_outro))
    repetir(lambda: cliente.clicar(f"{cliente.POPUP} button[type=submit]"))
    # o perfil é redesenhado quando os dados do usuário chegam do servidor: a espera devolve a leitura completa,
    # em vez de ler de novo depois (a janela pode estar sendo redesenhada nesse instante)
    perfil = cliente.wait.until(lambda d: next(
        (t for t in cliente.textos(f"{cliente.POPUP} .userdetails") if nome_outro in t), ""))
    botoes = cliente.wait.until(lambda d: (b := cliente.botoes_do_popup()) and "Chat" in b and b)
    cliente.demo_pausa()
    assert nome_outro in perfil and "(Offline)" not in perfil, perfil
    assert botoes.get("Chat") is True, botoes
    cliente.ok(f"perfil de '{nome_outro}' aberto: usuário online, com os botões {list(botoes)}")
    cliente.nota('Para usuários online o perfil não escreve "Online"; só os offline recebem a marca "(Offline)" '
                 'e ficam com "Challenge" e "Chat" desabilitados.')

    cliente.passo(3, 'Clica em "Chat"')
    repetir(lambda: cliente.clicar_no_popup("Chat"))
    cliente.resultado_esperado("Abre um menu de chat com o nome do usuário selecionado além de mostrar o "
                               "histórico de conversa com o mesmo")
    texto_janela, tem_campo = cliente.ler_janela_de_mensagem(nome_outro)
    assert nome_outro in texto_janela, texto_janela
    assert tem_campo, "a janela não tem campo de mensagem"
    cliente.ok(f"janela de chat aberta com o nome '{nome_outro}', campo de mensagem e o histórico da conversa (vazio)")
    cliente.nota("O documento pede dois usuários registrados; o teste usa duas sessões de convidado com nome, "
                 "e nenhuma mensagem é enviada.")

