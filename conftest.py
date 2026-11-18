import base64
from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver
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


def criar_driver(config):
    """Abre um Firefox novo, com perfil limpo (sem cookies, sem localStorage e sem login)."""
    opcoes = webdriver.FirefoxOptions()
    if config.getoption("--headless"):
        opcoes.add_argument("-headless")
    # não espera anúncios e imagens terminarem de carregar; cada página tem sua própria espera explícita
    opcoes.page_load_strategy = "eager"
    # o Selenium Manager encontra o Firefox instalado e baixa o geckodriver sozinho
    drv = webdriver.Firefox(options=opcoes)
    drv.set_window_size(1366, 900)
    drv.set_page_load_timeout(90)
    drv.notas = []
    return drv


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
    arquivo = EVIDENCIAS / f"{codigo}_{status}_{datetime.now():%Y%m%d_%H%M%S}.png"
    try:
        drv.save_screenshot(str(arquivo))
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
        for nota in drv.notas:
            extras.append(pytest_html_extras.html(f"<p><b>Nota:</b> {nota}</p>"))
    relatorio.extras = extras


def pytest_html_report_title(report):
    report.title = "Automação de testes - Pokémon Showdown (Selenium)"


def pytest_html_results_summary(prefix, summary, postfix):
    prefix.append("<p>Disciplina Qualidade e Teste de Software - Desafio 4.0. Casos do documento qatrabalho.docx. Navegador: Mozilla Firefox (Selenium WebDriver).</p>")
