import re
import time

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By

from .base_page import BasePage

URL_CLIENTE = "https://play.pokemonshowdown.com/"


class ClientPage(BasePage):
    BOTAO_NOME = ".userbar button[name=login]"
    POPUP = ".ps-popup"

    def abrir_lobby(self):
        self.abrir(URL_CLIENTE, permite_arquivo=False)
        self.achar("button[name=search]")  # botão "Battle!" indica que o lobby carregou
        self.achar(self.BOTAO_NOME)  # só aparece depois que o cliente conecta ao servidor

    def clicar_choose_name(self):
        self.clicar(self.BOTAO_NOME)
        return self.achar(f"{self.POPUP} input[name=username]")

    def informar_nome(self, nome):
        self.digitar(f"{self.POPUP} input[name=username]", nome)
        self.clicar(f"{self.POPUP} button[type=submit]")

    def texto_popup(self):
        return self.achar(self.POPUP).text

    def esperar_texto_popup(self, trecho):
        self.wait.until(lambda d: any(trecho in p.text for p in d.find_elements(By.CSS_SELECTOR, self.POPUP)))
        return self.texto_popup()

    def popup_tem_senha(self):
        return bool(self.driver.find_elements(By.CSS_SELECTOR, f"{self.POPUP} input[type=password]"))

    def nome_conectado(self):
        """Nome exibido no topo, ou None se a sessão continua sem nome."""
        nomes = self.driver.find_elements(By.CSS_SELECTOR, ".userbar .usernametext")
        return nomes[0].text.strip() if nomes else None

    def esperar_nome_conectado(self, nome):
        self.wait.until(lambda d: self.nome_conectado() == nome)
        self.destacar(self.driver.find_element(By.CSS_SELECTOR, ".userbar .username"))

    # --- assistir batalhas (Watch a battle) ---
    SALA_BATALHAS = "#room-battles"

    def clicar_watch_a_battle(self):
        botao = next(b for b in self.visiveis(".mainmenu button[name=joinRoom][value=battles]"))
        self.clicar(botao)
        self.achar(f"{self.SALA_BATALHAS} button[name=selectFormat]")
        self.wait.until(lambda d: self.batalhas_listadas())

    def filtrar_formato(self, valor):
        self.clicar(f"{self.SALA_BATALHAS} button[name=selectFormat]")
        self.clicar(self.esperar_visivel(f"{self.POPUP} button[name=selectFormat][value='{valor}']"))
        # a lista é refeita pelo servidor; espera só sobrarem salas do formato escolhido
        self.wait.until(lambda d: (lista := self.batalhas_listadas()) and all(f"/battle-{valor}-" in h for h, *_ in lista))
        self.demo_pausa()

    def formato_do_filtro(self):
        return self.achar(f"{self.SALA_BATALHAS} button[name=selectFormat]").text.strip()

    def batalhas_listadas(self):
        """[(href, formato, jogador1, jogador2)] das batalhas em andamento."""
        resultado = []
        for a in self.driver.find_elements(By.CSS_SELECTOR, f"{self.SALA_BATALHAS} .list a.blocklink"):
            try:
                # partidas ranqueadas têm um <small> a mais, com o rating; o formato é o que vem entre colchetes
                formato = next(s.text for s in a.find_elements(By.CSS_SELECTOR, "small") if s.text.startswith("["))
                resultado.append((a.get_attribute("href"), formato, a.find_element(By.CSS_SELECTOR, "em.p1").text, a.find_element(By.CSS_SELECTOR, "em.p2").text))
            except Exception:
                pass  # a lista foi redesenhada no meio da leitura
        return resultado

    def resumo_da_lista(self):
        return self.achar(f"{self.SALA_BATALHAS} .list > p").text

    def abrir_batalha(self, href):
        link = self.driver.find_element(By.CSS_SELECTOR, f"{self.SALA_BATALHAS} .list a[href$='{href.split('/')[-1]}']")
        self.clicar(link)
        sala = "#room-" + href.split("/")[-1]
        self.achar(f"{sala} .battle")
        self.achar(f"{sala} .battle-log")
        return sala

    def turno(self, sala):
        marcadores = [t.text for t in self.driver.find_elements(By.CSS_SELECTOR, f"{sala} .battle .turn")]
        achou = re.search(r"\d+", marcadores[0]) if marcadores else None
        return int(achou.group()) if achou else 0

    def log(self, sala):
        return self.driver.find_element(By.CSS_SELECTOR, f"{sala} .battle-log").get_attribute("innerText")

    def botoes_da_batalha(self, sala):
        return [b.get_attribute("name") for b in self.visiveis(f"{sala} .battle-controls button")]

    def usuarios_na_sala(self, sala):
        el = self.achar(f"{sala} .battle-userlist .userlist-count", visivel=False)
        return el.get_attribute("textContent").strip()

    # --- encontrar um usuário (Find a user) e mensagem privada ---
    def procurar_usuario(self, nome):
        self.clicar(self.esperar_visivel(".mainmenu button[name=finduser]"))
        self.digitar(f"{self.POPUP} input[name=data]", nome)
        self.clicar(f"{self.POPUP} button[type=submit]")
        # o perfil é redesenhado quando os dados do usuário chegam; devolve a primeira leitura completa
        return self.wait.until(lambda d: next((t for t in self.textos(f"{self.POPUP} .userdetails") if nome in t), None)
                               if self.textos(f"{self.POPUP} .buttonbar") else None)

    def campo_de_busca_de_usuario(self):
        self.clicar(self.esperar_visivel(".mainmenu button[name=finduser]"))
        return self.esperar_visivel(f"{self.POPUP} input[name=data]")

    def botoes_do_popup(self):
        for _ in range(5):
            try:
                return {b.text.strip(): b.is_enabled() for b in self.visiveis(f"{self.POPUP} .buttonbar button")}
            except StaleElementReferenceException:
                time.sleep(0.5)  # janela redesenhada no meio da leitura
        return {}

    def clicar_no_popup(self, texto):
        # espera o botão existir: a janela é desenhada em etapas
        botao = self.wait.until(lambda d: next((b for b in self.visiveis(f"{self.POPUP} button") if b.text.strip() == texto), None))
        self.clicar(botao)

    def janela_de_mensagem(self, nome):
        """Janela de mensagem privada (PM) aberta com o usuário."""
        uid = re.sub(r"[^a-z0-9]", "", nome.lower())
        return self.esperar_visivel(f".pm-window-{uid}")

    # --- desafio direto e fila ---
    def enviar_desafio(self, formato, privado=True):
        form = self.esperar_visivel(".challenge form.battleform")
        assert form.find_element(By.CSS_SELECTOR, "button[name=format]").get_attribute("value") == formato
        caixa = form.find_element(By.CSS_SELECTOR, "input[name=private]")
        if caixa.is_selected() != privado:
            self.clicar(caixa)  # "Don't allow spectators": a partida de teste fica fechada
        self.clicar(form.find_element(By.CSS_SELECTOR, "button[name=makeChallenge]"))
        try:
            self.wait.until(lambda d: any("Waiting for" in t for t in self.textos(".challenge")))
        except TimeoutException:
            avisos = self.textos(self.POPUP) + self.textos(".challenge")
            raise AssertionError(f"o desafio não foi enviado; tela: {avisos}") from None

    def aceitar_desafio(self, nome):
        uid = re.sub(r"[^a-z0-9]", "", nome.lower())
        seletor = f".pm-window-{uid} .challenge button[name=acceptChallenge]"
        # a janela do desafio é redesenhada quando chega; tenta de novo se o botão for trocado no meio do clique
        for _ in range(5):
            try:
                self.clicar(self.esperar_visivel(seletor))
                return
            except StaleElementReferenceException:
                time.sleep(0.5)
        self.clicar(self.esperar_visivel(seletor))

    def esperar_sala_de_batalha(self):
        self.wait.until(lambda d: "/battle-" in d.current_url)
        sala = "#room-" + self.driver.current_url.split("/")[-1]
        self.achar(f"{sala} .battle")
        return sala

    def escolher_formato_da_fila(self, valor, busca):
        self.clicar(self.esperar_visivel(".mainmenu button[name=format]"))
        self.digitar(f"{self.POPUP} input[name=search]", busca)  # formatos menos comuns ficam fora da lista inicial
        self.clicar(self.esperar_visivel(f"{self.POPUP} button[name=selectFormat][value='{valor}']"))
        self.wait.until(lambda d: self.visiveis(f".mainmenu button[name=format][value='{valor}']"))

    def clicar_battle(self):
        self.clicar(self.esperar_visivel(".mainmenu button[name=search]"))

    def texto_da_busca(self):
        return self.esperar_visivel(".mainmenu .searchbutton, .mainmenu form.battleform").text

    def cancelar_busca(self):
        self.clicar(self.esperar_visivel(".mainmenu button[name=cancelSearch]"))

    def em_batalha(self):
        return "/battle-" in self.driver.current_url or bool(self.driver.find_elements(By.CSS_SELECTOR, "[id^=room-battle-]"))
