import time

from selenium.webdriver.common.by import By

from .base_page import BasePage

URL_DEX = "https://dex.pokemonshowdown.com/"


class DexPage(BasePage):
    BUSCA = "input.searchbox"

    def abrir_inicio(self):
        self.abrir(URL_DEX)
        self.achar(self.BUSCA)

    def pesquisar(self, termo):
        self.digitar(self.BUSCA, termo)
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".results li.result"))
        self.demo_pausa()

    def abrir_resultado(self, entrada):
        """entrada no formato 'pokemon|Pikachu' ou 'move|Stealth Rock'."""
        self.clicar(f".results a[data-entry='{entrada}']")
        nome = entrada.split("|")[1]
        self.wait.until(lambda d: nome in d.find_element(By.CSS_SELECTOR, ".dexentry h1").text)

    def entrada(self):
        """Painel da entrada aberta por último (ao seguir um link, a Pokédex abre um painel ao lado)."""
        # espera sem destacar: o destaque rola a página de volta ao topo e atrapalha as listas virtuais
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".dexentry h1"))
        return self.driver.find_elements(By.CSS_SELECTOR, ".dexentry")[-1]

    def titulo(self):
        el = self.entrada().find_element(By.CSS_SELECTOR, "h1")
        self.destacar(el)
        return el.text

    def texto(self, css):
        # textContent ignora o text-transform: uppercase do CSS dos tipos
        return (self.achar(css).get_attribute("textContent") or "").strip()


    # --- lista de Pokémon que aprendem o golpe ---

    def grupos_aprendizado(self):
        self.achar_todos(".dexentry .utilichart h3")
        return [h.text for h in self.entrada().find_elements(By.CSS_SELECTOR, "h3") if h.text]

    def rolar_ate_entrada(self, entrada, tentativas=60):
        """As listas são virtuais: rola o painel até o item ('pokemon|Garchomp', 'move|Surf') aparecer."""
        css = f".utilichart a[data-entry='{entrada}']"
        for _ in range(tentativas):
            achados = self.entrada().find_elements(By.CSS_SELECTOR, css)
            if achados:
                self.destacar(achados[0])
                return achados[0]
            self.driver.execute_script("arguments[0].closest('.pfx-panel').scrollTop += 600", self.entrada())
            time.sleep(0.3)
        return None

    def rolar_ate_pokemon(self, nome, tentativas=60):
        return self.rolar_ate_entrada(f"pokemon|{nome}", tentativas)

    def grupo_do_item(self, link):
        """Cabeçalho (Level-up, TM/HM, ...) sob o qual o link aparece."""
        return self.driver.execute_script(
            "var li = arguments[0].closest('li');"
            "while (li && !li.querySelector('h3')) li = li.previousElementSibling;"
            "return li ? li.textContent : null;",
            link,
        )
