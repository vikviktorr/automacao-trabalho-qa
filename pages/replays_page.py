from selenium.webdriver.common.by import By

from .base_page import BasePage

URL_REPLAYS = "https://replay.pokemonshowdown.com/"


class ReplaysPage(BasePage):
    CAMPO_USUARIO = "input[name=user]"
    CAMPO_FORMATO = "input[name=format]"

    def abrir_busca(self):
        # a busca depende da API do servidor, que não existe na cópia do Web Archive
        self.abrir(URL_REPLAYS, permite_arquivo=False)

    def buscar(self, usuario="", formato=""):
        self.digitar(self.CAMPO_USUARIO, usuario)
        self.digitar(self.CAMPO_FORMATO, formato)
        url_antes = self.driver.current_url
        self.clicar("form button[type=submit]")
        self.wait.until(lambda d: d.current_url != url_antes)
        return self.resultados()

    def resultados(self):
        """Lista [(formato, jogador1, jogador2)] da seção de resultados."""
        def carregou(d):
            secoes = d.find_elements(By.CSS_SELECTOR, "#main section")
            return secoes and secoes[-1].find_elements(By.CSS_SELECTOR, "a.blocklink")

        self.wait.until(carregou)
        secao = self.driver.find_elements(By.CSS_SELECTOR, "#main section")[-1]
        self.destacar(secao)
        resultado = []
        for a in secao.find_elements(By.CSS_SELECTOR, "a.blocklink"):
            jogadores = [s.text for s in a.find_elements(By.CSS_SELECTOR, "strong")]
            formato = a.find_element(By.CSS_SELECTOR, "small").text
            resultado.append((formato, *jogadores[:2]))
        return resultado
