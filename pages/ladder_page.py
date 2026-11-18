from .base_page import BasePage

URL_LADDER = "https://pokemonshowdown.com/ladder/"


class LadderPage(BasePage):
    def abrir_formato(self, formato):
        self.abrir(URL_LADDER + formato)
        self.achar(".ladder table")

    def titulo(self):
        return self.achar(".ladder h1").text

    def linhas(self, quantidade=10):
        """Retorna [(posicao, nome, elo, link)] dos primeiros colocados."""
        resultado = []
        for tr in self.achar_todos(".ladder table tr")[1 : quantidade + 1]:
            tds = tr.find_elements("css selector", "td")
            link = tds[1].find_element("css selector", "a")
            resultado.append((int(tds[0].text), link.text.strip(), int(tds[2].text), link))
        return resultado

    def abrir_perfil(self, link):
        href = link.get_attribute("href")
        self.clicar(link)
        self.wait.until(lambda d: "/users/" in d.current_url)
        return href

    def esperar_perfil(self, nome):
        """Espera o painel do perfil (aberto ao lado da ladder) e devolve o texto dele."""
        def painel(d):
            for p in d.find_elements("css selector", ".pfx-panel"):
                titulos = p.find_elements("css selector", "h1")
                if titulos and titulos[0].text.strip().lower() == nome.lower():
                    return p
            return None

        el = self.wait.until(painel)
        self.destacar(el.find_element("css selector", "h1"))
        return el.text
