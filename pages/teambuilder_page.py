import time

from selenium.webdriver.common.by import By

from .base_page import BasePage

URL_TEAMBUILDER = "https://play.pokemonshowdown.com/teambuilder"


class TeambuilderPage(BasePage):
    """Teambuilder do cliente. Os times ficam no localStorage do navegador, então funciona sem login."""

    SALA = "#room-teambuilder"

    def abrir_teambuilder(self):
        self.abrir(URL_TEAMBUILDER, permite_arquivo=False)
        self._esperar_pronto()

    def _esperar_pronto(self):
        self.esperar_visivel(f"{self.SALA} button[name=newTop]")
        # o cliente redesenha a tela quando termina de conectar; "Choose name" só aparece depois disso
        self.achar(".userbar button[name=login]")

    def _esperar_redesenho(self):
        """Ao abrir um time o cliente baixa os dados do formato e redesenha o formulário quando eles chegam.
        Espera os downloads pendentes terminarem para não interagir com elementos que vão ser trocados."""
        self.wait.until(lambda d: d.execute_script("return !!window.jQuery && jQuery.active === 0"))
        time.sleep(0.4)
        self.wait.until(lambda d: d.execute_script("return jQuery.active === 0"))

    # --- listagem ---

    def nomes_dos_times(self):
        return [el.text for el in self.driver.find_elements(By.CSS_SELECTOR, f"{self.SALA} .teamlist .team strong")]

    def quantidade_de_times(self):
        return len(self.driver.find_elements(By.CSS_SELECTOR, f"{self.SALA} .teamlist .team"))

    # --- edição do time ---

    def voltar_para_lista(self):
        self.clicar(self.esperar_visivel(f"{self.SALA} button[name=back]"))
        self.esperar_visivel(f"{self.SALA} button[name=newTop]")

    # --- pré-condições ---
    def criar_times_salvos(self, times):
        """Grava times direto no armazenamento do Teambuilder (pré-condição dos casos, não é um passo).
        times: lista de (nome, formato, texto no formato de exportação do Showdown)."""
        self.driver.execute_script(
            "arguments[0].forEach(function (t) {"
            "  Storage.teams.push({name: t[0], format: t[1], team: Storage.packTeam(Storage.importTeam(t[2])),"
            "                      folder: '', iconCache: '', capacity: 6});"
            "});"
            "Storage.saveAllTeams(); app.rooms.teambuilder.update();",
            [list(t) for t in times],
        )
        self.wait.until(lambda d: self.quantidade_de_times() >= len(times))
        self.demo_pausa()

    def times_salvos(self):
        """[(nome, pasta, formato, pacote)] do jeito que estão gravados no navegador."""
        return [tuple(t) for t in self.driver.execute_script(
            "return Storage.teams.map(function (t) { return [t.name, t.folder || '', t.format, t.team]; })"
        )]

    # --- pastas ---
    def pastas(self):
        """Textos da coluna de pastas (formatos e pastas criadas)."""
        return [el.text.strip() for el in self.driver.find_elements(By.CSS_SELECTOR, f"{self.SALA} .folderpane .selectFolder") if el.text.strip()]

    def clicar_add_folder(self):
        self.clicar(self.esperar_visivel(f"{self.SALA} .selectFolder[data-value='++']"))
        return self.esperar_visivel(".ps-popup input[name=data]")

    def texto_popup(self):
        return self.esperar_visivel(".ps-popup").text

    def confirmar_nome_da_pasta(self, nome):
        self.digitar(".ps-popup input[name=data]", nome)
        self.clicar(self.esperar_visivel(".ps-popup button[type=submit]"))
        self.wait.until(lambda d: not self.visiveis(".ps-popup"))
        self.esperar_visivel(f"{self.SALA} .selectFolder[data-value='{nome}/']")

    def selecionar_pasta(self, valor):
        """valor: 'all' para todos os times ou 'Nome/' para uma pasta criada."""
        self.clicar(self.esperar_visivel(f"{self.SALA} .selectFolder[data-value='{valor}']"))
        self.demo_pausa()

    def titulo_da_listagem(self):
        el = self.esperar_visivel(f"{self.SALA} .teampane h2:last-of-type")
        return el.text

    def arrastar_time_para_pasta(self, indice, pasta):
        """Arrasta o time da lista até a pasta da lateral.
        O Teambuilder usa o arrastar-e-soltar do HTML5, que o WebDriver não gera no Firefox;
        por isso os eventos do arraste (dragstart, dragenter, drop, dragend) são disparados via JavaScript."""
        time_el = self.esperar_visivel(f"{self.SALA} .team[data-value='{indice}']")
        pasta_el = self.esperar_visivel(f"{self.SALA} .selectFolder[data-value='{pasta}']")
        self.destacar(time_el)
        self.driver.execute_script(
            "var time = arguments[0], pasta = arguments[1], dados = new DataTransfer();"
            "function evento(alvo, tipo) { alvo.dispatchEvent(new DragEvent(tipo, {bubbles: true, cancelable: true, dataTransfer: dados})); }"
            "evento(time, 'dragstart'); evento(pasta, 'dragenter'); evento(pasta, 'drop'); evento(time, 'dragend');",
            time_el, pasta_el,
        )
        self.destacar(pasta_el)
        self.demo_pausa()

    def duplicar_time(self, indice):
        self.clicar(self.esperar_visivel(f"{self.SALA} button[name=duplicate][value='{indice}']"))
        self.esperar_visivel(f"{self.SALA} input.teamnameedit")
        self._esperar_redesenho()

    def nome_em_edicao(self):
        return self.esperar_visivel(f"{self.SALA} input.teamnameedit").get_attribute("value")
