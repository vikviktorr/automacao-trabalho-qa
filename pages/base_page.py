import time

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ARQUIVO = "https://web.archive.org/web/2026/"
SINAIS_INDISPONIVEL = ("503", "Service Unavailable", "Temporarily Unavailable")


class BasePage:
    """Funções comuns a todas as páginas: abrir URL, esperar, destacar e pausar no modo demo."""

    pausa = 0.0  # ajustado pelo conftest quando roda com --demo

    def __init__(self, driver, timeout=30):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.usando_arquivo = False

    def abrir(self, url, permite_arquivo=True):
        """Abre a URL. Se o site estiver fora do ar, usa a cópia do Web Archive."""
        self._get(url)
        if self.indisponivel() and permite_arquivo:
            self.nota(f"{url} estava fora do ar; usando a cópia do Web Archive.")
            self.usando_arquivo = True
            self._get(ARQUIVO + url)
        self.demo_pausa()

    def _get(self, url):
        try:
            self.driver.get(url)
        except Exception:
            # o Web Archive às vezes demora para terminar de carregar recursos secundários
            pass

    def indisponivel(self):
        titulo = self.driver.title or ""
        return any(s.lower() in titulo.lower() for s in SINAIS_INDISPONIVEL)

    def nota(self, texto):
        self.driver.notas.append(texto)
        print(f"   [nota] {texto}")

    def passo(self, numero, descricao):
        print(f"\n   Passo {numero}: {descricao}")
        self.demo_pausa()

    def ok(self, descricao):
        print(f"      OK - {descricao}")

    def resultado_esperado(self, texto):
        """Registra o resultado esperado do caso, consolidado na última etapa (coluna "Sistema" do documento)."""
        self.driver.resultado_esperado = texto
        print(f"\n   Resultado esperado: {texto}")
        self.demo_pausa()

    def achar(self, css, visivel=True):
        cond = EC.visibility_of_element_located if visivel else EC.presence_of_element_located
        el = self.wait.until(cond((By.CSS_SELECTOR, css)))
        self.destacar(el)
        return el

    def achar_todos(self, css):
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
        return self.driver.find_elements(By.CSS_SELECTOR, css)

    def clicar(self, el_ou_css):
        el = self.achar(el_ou_css) if isinstance(el_ou_css, str) else el_ou_css
        self.destacar(el)
        el.click()
        self.demo_pausa()

    def digitar(self, css, texto):
        el = self.achar(css)
        el.clear()
        if self.pausa:
            for letra in texto:  # digitação "humana" para a plateia acompanhar
                el.send_keys(letra)
                time.sleep(0.06)
        else:
            el.send_keys(texto)
        self.demo_pausa()
        return el

    def substituir(self, el_ou_css, texto):
        """Troca o conteúdo do campo (Ctrl+A e digita), para campos em que o clear() não funciona."""
        el = self.achar(el_ou_css) if isinstance(el_ou_css, str) else el_ou_css
        el.send_keys(Keys.CONTROL, "a")
        el.send_keys(Keys.BACKSPACE)
        el.send_keys(texto)
        self.demo_pausa()
        return el

    def visiveis(self, css):
        achados = []
        for el in self.driver.find_elements(By.CSS_SELECTOR, css):
            try:
                if el.is_displayed():
                    achados.append(el)
            except StaleElementReferenceException:
                pass  # a tela foi redesenhada entre a busca e a checagem
        return achados

    def textos(self, css):
        """Textos dos elementos visíveis, ignorando os que forem redesenhados durante a leitura."""
        resultado = []
        for el in self.visiveis(css):
            try:
                resultado.append(el.text)
            except StaleElementReferenceException:
                pass
        return resultado

    def esperar_visivel(self, css):
        """Primeiro elemento visível entre os que casam com o seletor (o cliente mantém cópias ocultas)."""
        self.wait.until(lambda d: self.visiveis(css))
        el = self.visiveis(css)[0]
        self.destacar(el)
        return el

    def destacar(self, el):
        if not self.pausa:
            return
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].style.outline='3px solid #e3350d';"
            "arguments[0].style.outlineOffset='2px';",
            el,
        )
        time.sleep(self.pausa / 2)

    def demo_pausa(self, fator=1.0):
        if self.pausa:
            time.sleep(self.pausa * fator)
