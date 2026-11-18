import random
import re
import time

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from .base_page import BasePage
from .client_page import ClientPage


class BattlePage(BasePage):
    """Sala de uma batalha no cliente, vista por um dos jogadores."""

    def __init__(self, driver, sala, timeout=60):
        super().__init__(driver, timeout)
        self.sala = sala  # seletor da sala, ex.: "#room-battle-gen9randombattle-123-abc"

    # --- leitura ---
    def log(self):
        return self.driver.find_element(By.CSS_SELECTOR, f"{self.sala} .battle-log").get_attribute("innerText")

    def esperar_no_log(self, trecho):
        self.wait.until(lambda d: trecho in self.log())

    def turno(self):
        marcadores = [t.text for t in self.driver.find_elements(By.CSS_SELECTOR, f"{self.sala} .battle .turn")]
        achou = re.search(r"\d+", marcadores[0]) if marcadores else None
        return int(achou.group()) if achou else 0

    def esperar_turno(self, numero):
        self.wait.until(lambda d: self.turno() >= numero)

    def texto_dos_controles(self):
        return self.esperar_visivel(f"{self.sala} .battle-controls").text

    def icones_dos_times(self):
        """(quantidade de ícones do meu lado, quantidade do lado adversário)."""
        perto = self.driver.find_elements(By.CSS_SELECTOR, f"{self.sala} .trainer-near .teamicons .picon")
        longe = self.driver.find_elements(By.CSS_SELECTOR, f"{self.sala} .trainer-far .teamicons .picon")
        return len(perto), len(longe)

    def ativo(self):
        """Pokémon em campo do meu lado (é o botão desabilitado da lista "Switch")."""
        return self.esperar_visivel(f"{self.sala} .battle-controls button[name=chooseDisabled]").text.strip()

    def reservas(self):
        """Pokémon do banco que podem entrar (botões habilitados da lista "Switch")."""
        return [b.text.strip() for b in self.visiveis(f"{self.sala} .battle-controls button[name=chooseSwitch]")]

    def golpes(self):
        return [b.get_attribute("data-move") for b in self.visiveis(f"{self.sala} .battle-controls button[name=chooseMove]")]

    def esperar_acoes(self):
        """Espera o turno pedir uma decisão (golpes na tela)."""
        self.wait.until(lambda d: self.visiveis(f"{self.sala} .battle-controls button[name=chooseMove]"))

    # --- ações do turno ---
    def trocar_para(self, nome):
        botao = next(b for b in self.visiveis(f"{self.sala} .battle-controls button[name=chooseSwitch]") if b.text.strip() == nome)
        self.clicar(botao)

    def usar_golpe(self, indice=0):
        botoes = self.visiveis(f"{self.sala} .battle-controls button[name=chooseMove]")
        nome = botoes[indice].get_attribute("data-move")
        self.clicar(botoes[indice])
        return nome

    def caixa_tera(self):
        return self.esperar_visivel(f"{self.sala} .battle-controls input[name=terastallize]")

    def tipo_tera(self):
        """Tipo para o qual o Pokémon vai terastalizar (ícone ao lado da opção)."""
        return self.esperar_visivel(f"{self.sala} .battle-controls label.megaevo img").get_attribute("alt")

    def aguardando_oponente(self):
        self.wait.until(lambda d: "Waiting for opponent" in self.texto_dos_controles())

    # --- sair da batalha ---
    def fechar_aba(self):
        aba = self.esperar_visivel(f".tabbar button[name=closeRoom][value='{self.sala[len('#room-'):]}']")
        self.clicar(aba)

    def texto_popup(self):
        return self.esperar_visivel(".ps-popup").text

    def confirmar_desistencia(self, fechar_sala=False):
        caixa = self.esperar_visivel(".ps-popup input[name=closeroom]")
        if caixa.is_selected() != fechar_sala:
            self.clicar(caixa)
        self.clicar(next(b for b in self.visiveis(".ps-popup button[type=submit]") if b.text.strip() == "Forfeit"))

    def desistir_se_em_andamento(self):
        """Limpeza: encerra a partida de teste para não deixá-la aberta no servidor."""
        try:
            if "won the battle" not in self.log() and "forfeited" not in self.log():
                self.driver.execute_script("arguments[0].send('/forfeit')", self.driver.execute_script(
                    "return app.rooms[arguments[0]]", self.sala[len("#room-"):]))
        except Exception:
            pass


def repetir(acao, tentativas=5):
    """Executa a ação de novo se a tela for redesenhada no meio dela (elemento "stale")."""
    for _ in range(tentativas - 1):
        try:
            return acao()
        except StaleElementReferenceException:
            time.sleep(0.5)
    return acao()


def nome_de_teste(prefixo):
    """Nome de convidado único (o servidor aceita até 18 caracteres)."""
    return f"{prefixo} {random.randint(1000, 9999)}"[:18]


def conectar(driver, nome):
    cliente = ClientPage(driver)
    cliente.abrir_lobby()
    cliente.clicar_choose_name()
    cliente.informar_nome(nome)
    cliente.esperar_nome_conectado(nome)
    return cliente


def iniciar_batalha(jogador, oponente, formato="gen9randombattle"):
    """Pré-condição dos casos de batalha: as duas sessões de teste entram numa partida privada.
    O desafio direto entre duas sessões próprias evita parear com jogadores reais na fila."""
    nome_j, nome_o = nome_de_teste("QA Jogador"), nome_de_teste("QA Oponente")
    cliente_j = conectar(jogador, nome_j)
    cliente_o = conectar(oponente, nome_o)
    cliente_j.procurar_usuario(nome_o)
    # o perfil e o formulário do desafio são redesenhados quando os dados chegam do servidor
    repetir(lambda: cliente_j.clicar_no_popup("Challenge"))
    repetir(lambda: cliente_j.enviar_desafio(formato, privado=True))
    repetir(lambda: cliente_o.aceitar_desafio(nome_j))
    sala = cliente_j.esperar_sala_de_batalha()
    assert cliente_o.esperar_sala_de_batalha() == sala
    batalha_j, batalha_o = BattlePage(jogador, sala), BattlePage(oponente, sala)
    batalha_j.esperar_acoes()
    batalha_o.esperar_acoes()
    return batalha_j, batalha_o, nome_j, nome_o
