import base64
from datetime import datetime
from functools import cache
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.selenium_manager import SeleniumManager
from selenium.common.exceptions import WebDriverException

from pages.base_page import BasePage

RAIZ = Path(__file__).parent
EVIDENCIAS = RAIZ / "evidencias"


def pytest_addoption(parser):
    parser.addoption("--demo", action="store_true", help="Firefox visível, com pausas e destaque dos elementos (apresentação)")
    parser.addoption("--headless", action="store_true", help="Roda o Firefox sem janela")
    parser.addoption("--pausa", type=float, default=1.2, help="Segundos de pausa entre ações no modo --demo")


def pytest_configure(config):
    EVIDENCIAS.mkdir(exist_ok=True)
    (RAIZ / "reports").mkdir(exist_ok=True)
    if config.getoption("--demo"):
        BasePage.pausa = config.getoption("--pausa")
    config.stash["inicio"] = datetime.now()


class Firefox(webdriver.Firefox):
    """Firefox do Selenium com dois campos a mais, lidos pelo relatório de cada caso."""

    notas: list[str]  # observações registradas pelo teste (diferenças entre o documento e o site)
    resultado_esperado: str | None  # texto do resultado esperado do caso, registrado na última etapa


def criar_driver(config):
    """Abre um Firefox novo, com perfil limpo (sem cookies, sem localStorage e sem login)."""
    opcoes = webdriver.FirefoxOptions()
    if config.getoption("--headless"):
        opcoes.add_argument("-headless")
    # não espera anúncios e imagens terminarem de carregar; cada página tem sua própria espera explícita
    opcoes.page_load_strategy = "eager"
    drv = Firefox(options=opcoes, service=webdriver.FirefoxService(geckodriver()))
    drv.set_window_size(1366, 900)
    drv.set_page_load_timeout(90)
    drv.notas = []
    drv.resultado_esperado = None
    return drv


@cache  # pergunta ao Selenium Manager uma vez só por execução
def geckodriver():
    """Caminho do geckodriver compatível com o Firefox instalado, baixado pelo Selenium Manager.

    Ignora o geckodriver do PATH: no Parrot, /usr/bin/geckodriver vem do pacote eyewitness e é antigo demais
    para o Firefox atual.
    """
    return SeleniumManager().binary_paths(["--browser", "firefox", "--skip-driver-in-path"])["driver_path"]


@pytest.fixture
def driver(request):
    drv = criar_driver(request.config)
    marcador = request.node.get_closest_marker("ct")
    print(f"\n=== {marcador.args[0] if marcador else request.node.name}: {request.node.function.__doc__ or ''}")
    yield drv
    drv.quit()


@pytest.fixture
def outra_sessao(request, driver):
    """Segundo navegador, independente do primeiro: faz o papel da janela anônima / outro visitante."""
    drv = criar_driver(request.config)
    drv.notas = driver.notas  # as notas aparecem no relatório do caso
    yield drv
    drv.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    relatorio = resultado.get_result()
    drv = item.funcargs.get("driver")
    if relatorio.when != "call" or drv is None:
        return

    marcador = item.get_closest_marker("ct")
    codigo = marcador.args[0] if marcador else item.name
    if hasattr(relatorio, "wasxfail"):
        # caso marcado com xfail: falhou como previsto (defeito conhecido) ou passou sem que se esperasse
        status = "defeito" if relatorio.skipped else "defeito_corrigido"
    else:
        status = "aprovado" if relatorio.passed else ("ignorado" if relatorio.skipped else "reprovado")
    momento = datetime.now()
    arquivo = EVIDENCIAS / f"{codigo}_{status}_{momento:%Y%m%d_%H%M%S}.png"
    try:
        drv.save_screenshot(str(arquivo))
        ambiente = registro_do_ambiente(drv, momento)
    except WebDriverException:
        # janela fechada ou navegador caído: fica sem evidência, mas a suíte segue para o próximo caso
        return

    extras = getattr(relatorio, "extras", [])
    html_plugin = item.config.pluginmanager.getplugin("html")
    if html_plugin:
        from pytest_html import extras as pytest_html_extras

        imagem = base64.b64encode(arquivo.read_bytes()).decode()
        extras.append(pytest_html_extras.image(imagem, f"Evidência {codigo}"))
        extras.append(pytest_html_extras.url(drv.current_url, "Página final"))
        if drv.resultado_esperado:
            extras.append(pytest_html_extras.html(f"<p><b>Resultado esperado:</b> {drv.resultado_esperado}</p>"))
        extras.append(pytest_html_extras.html(f"<p><b>Evidência:</b> {ambiente}</p>"))
        for nota in drv.notas:
            extras.append(pytest_html_extras.html(f"<p><b>Nota:</b> {nota}</p>"))
    relatorio.extras = extras


def registro_do_ambiente(drv, momento):
    """Dados que o documento pede junto de cada captura: data/hora, URL, navegador/versão, viewport e zoom."""
    caps = drv.capabilities
    largura, altura, zoom = drv.execute_script(
        "return [window.innerWidth, window.innerHeight, Math.round(window.devicePixelRatio * 100)]")
    return (f"{momento:%d/%m/%Y %H:%M:%S}; URL {drv.current_url}; "
            f"navegador {caps.get('browserName', '?')} {caps.get('browserVersion', '?')} "
            f"({caps.get('platformName', '?')}); viewport {largura}x{altura} CSS px; zoom {zoom}%; "
            "orientação paisagem (desktop); captura sem credenciais")


def pytest_html_report_title(report):
    report.title = "Automação de testes - Pokémon Showdown (Selenium)"


def pytest_html_results_summary(prefix, summary, postfix):
    prefix.append("<p>Disciplina Qualidade e Teste de Software - Desafio 4.0. Casos do documento revisado qatrabalho_revisado_QA.docx; cada caso compara o comportamento observado com o resultado esperado consolidado na última etapa. Navegador: Mozilla Firefox (Selenium WebDriver).</p>")
