# Automação de testes – Pokémon Showdown (Selenium + Python + Firefox)

Automação dos casos de teste **CT_0001 a CT_0012** do documento de casos de uso revisado
`qatrabalho_revisado_QA.docx` (Desafio 4.0 – Qualidade e Teste de Software). Os testes abrem o
[Pokémon Showdown](https://pokemonshowdown.com/) num Firefox de verdade, executam os passos de cada caso como um
usuário faria e comparam o que o site mostra com o resultado esperado do documento.

Sumário: [Como rodar](#como-rodar) · [O que foi utilizado e por quê](#o-que-foi-utilizado-e-por-quê) ·
[Como o código funciona](#como-o-código-funciona) · [Arquivo por arquivo, função por função](#arquivo-por-arquivo-função-por-função) ·
[Decisões e limitações](#decisões-e-limitações)

---

## Como rodar

```bash
./apresentacao.sh                         # apresentação: Firefox visível, devagar, elementos destacados em vermelho
./apresentacao.sh -k ct0007               # só um caso
./apresentacao.sh tests/test_batalha.py   # só uma área
./apresentacao.sh --pausa 2               # ainda mais devagar

.venv/bin/pytest --headless               # execução rápida, sem janela (cerca de 4 minutos)
```

Na primeira execução o `apresentacao.sh` cria o `.venv` e instala o `requirements.txt`. Para recriar o ambiente
do zero: `rm -rf .venv && ./apresentacao.sh`.

No Zed, abra a pasta do projeto e use o ▶ ao lado de cada `def test_...` (tarefas em `.zed/tasks.json`:
"este caso" em modo apresentação ou rápido, e "arquivo atual"). Também dá para rodar pela paleta com `task: spawn`.

**Saídas:** `reports/relatorio.html` (relatório) e `evidencias/` (um PNG por caso, com o código, o status e a
data/hora no nome do arquivo).

| Caso | Nome | Arquivo de teste |
|---|---|---|
| CT_0001 | Consultar ranking da ladder por formato | `tests/test_ladder.py` |
| CT_0002 | Buscar replays por usuário e formato | `tests/test_replays.py` |
| CT_0003 | Listar Pokémon que aprendem um golpe | `tests/test_pokedex.py` |
| CT_0004 | Escolher nome de usuário já registrado | `tests/test_cliente.py` |
| CT_0005 | Organizar times em pastas no Teambuilder | `tests/test_teambuilder.py` |
| CT_0006 | Duplicar time para uma pasta criada | `tests/test_teambuilder.py` |
| CT_0007 | Mudar o Pokémon durante o combate | `tests/test_batalha.py` |
| CT_0008 | Terastalizar Pokémon durante a batalha | `tests/test_batalha.py` |
| CT_0009 | Desistir de uma batalha em andamento | `tests/test_batalha.py` |
| CT_0010 | Cancelar busca de partida na fila | `tests/test_cliente.py` |
| CT_0011 | Assistir batalha como espectador | `tests/test_cliente.py` |
| CT_0012 | Abrir chat com outro usuário | `tests/test_cliente.py` |

---

## O que foi utilizado e por quê

| Ferramenta | Para que serve aqui | Por que foi escolhida |
|---|---|---|
| **Python 3** | Linguagem dos testes | Sintaxe simples de ler numa apresentação; é a linguagem mais usada com Selenium e pytest. |
| **Selenium WebDriver** (`selenium`) | Controla o navegador: abre páginas, clica, digita, lê textos | É o padrão de mercado para testes de interface web e o que a disciplina pede. Interage com o site como um usuário, pela interface, que é o nível de teste do documento (sistema/interface, caixa-preta). |
| **Mozilla Firefox** + **geckodriver** | Navegador onde os testes rodam; o geckodriver é a "ponte" entre o Selenium e o Firefox | O Firefox já vem no Parrot. O geckodriver certo para a versão instalada é baixado pelo **Selenium Manager** (vem junto com o Selenium), sem instalação manual. |
| **pytest** | Executa os testes, mostra o resultado e trata falhas e *skips* | Testes são funções simples com `assert`; as *fixtures* abrem e fecham o navegador automaticamente; os *hooks* permitem montar evidências e relatório. |
| **pytest-html** | Gera `reports/relatorio.html` | Relatório num único arquivo, com print, resultado esperado, dados do ambiente e notas de cada caso — é a evidência pedida pelo documento. |
| **Page Object** (padrão de projeto) | Organiza o código: cada página do site é uma classe em `pages/` | Os testes ficam legíveis (parecem os passos do documento) e os seletores CSS ficam num lugar só: se o site mudar, conserta-se a página, não todos os testes. |
| **Seletores CSS** | Localizam elementos na página (`button[name=search]`, `.ps-popup` …) | Mais curtos e estáveis que XPath; usam os atributos que o próprio site usa (`name`, `value`, classes). |
| **Esperas explícitas** (`WebDriverWait`) | Esperam uma condição (elemento visível, texto no log, turno avançar) antes de seguir | O site é dinâmico (WebSocket, telas redesenhadas). Esperar uma condição é mais rápido e confiável que pausas fixas (`sleep`). |
| **Bash** (`apresentacao.sh`) | Prepara o ambiente e roda a suíte em modo apresentação | Um comando só para a demonstração; abre o relatório no fim. |
| **Zed** (`.zed/tasks.json`) | Botão ▶ para rodar cada caso pelo editor | Facilita rodar um caso específico durante a apresentação. |

Dependências exatas em `requirements.txt`: `selenium>=4.20`, `pytest>=8.0`, `pytest-html>=4.1`.

---

## Como o código funciona

### Fluxo de uma execução

```
pytest
 ├─ conftest.py: pytest_addoption / pytest_configure   → lê --demo, --headless, --pausa; cria as pastas de saída
 ├─ para cada teste (tests/test_*.py):
 │   ├─ fixture driver        → abre um Firefox limpo (sem cookies, sem login)
 │   ├─ fixture outra_sessao  → (só em batalha e CT_0012) abre um 2º Firefox independente
 │   ├─ o teste:
 │   │    passo(1, …) → ação na página (Page Object)
 │   │    passo(2, …) → ação …
 │   │    resultado_esperado("texto do documento")
 │   │    assert …    → compara o que o site mostra com o resultado esperado
 │   ├─ pytest_runtest_makereport → print da tela + data/hora, URL, navegador, viewport, zoom → relatório
 │   └─ fim da fixture → fecha o(s) navegador(es)
 └─ reports/relatorio.html
```

### Estrutura de um teste

Cada teste segue a estrutura do documento revisado: a coluna "Sistema" traz só o **resultado esperado,
consolidado na última etapa**, e as etapas intermediárias são ações do usuário. Por isso o teste:

1. executa os passos do documento, anunciando cada um com `passo(n, "...")`;
2. imprime o **"Resultado esperado"** com o texto do caso (`resultado_esperado(...)`), que também vai para o relatório;
3. faz as verificações finais (`assert`) e registra cada uma com `ok(...)`.

As verificações que aparecem no meio dos passos só garantem que a ação aconteceu antes de seguir (por exemplo,
que a janela abriu) — sem elas, o passo seguinte falharia com um erro difícil de entender.

Exemplo (CT_0004):

```python
cliente.passo(1, 'Clica em "Choose name"')
cliente.clicar_choose_name()

cliente.passo(2, 'Informa o nome já registrado "Zarel" e confirma em "Choose name"')
cliente.informar_nome("Zarel")
cliente.resultado_esperado("Identifica que o nome pertence a uma conta registrada e pede a autenticação ...")
assert "The name you chose is registered" in cliente.esperar_texto_popup("registered")
```

### Resultado de cada caso

| Status no relatório | Significado |
|---|---|
| **passed** (aprovado) | O site se comportou como o resultado esperado. |
| **failed** (reprovado) | Alguma verificação falhou; a mensagem do `assert` diz o que foi visto. |
| **skipped** (ignorado) | O caso não pôde ser verificado por motivo externo (servidor fora do ar, limite de partidas do servidor, adversário real encontrado na fila). O motivo aparece no relatório. |

---

## Arquivo por arquivo, função por função

### `conftest.py` — configuração do pytest

Arquivo carregado automaticamente pelo pytest. Concentra tudo o que é comum a todos os testes.

| Função / classe | O que faz | Por quê |
|---|---|---|
| `pytest_addoption` | Cria as opções `--demo`, `--headless` e `--pausa` | Um mesmo código serve para a apresentação (devagar, visível) e para a execução rápida. |
| `pytest_configure` | Cria `evidencias/` e `reports/`; no `--demo`, define a pausa entre ações | As pastas precisam existir antes do primeiro print; a pausa vale para todas as páginas (`BasePage.pausa`). |
| `Firefox` (classe) | O `webdriver.Firefox` com dois campos a mais: `notas` e `resultado_esperado` | O teste guarda ali o que deve aparecer no relatório; declarar os campos deixa o editor (basedpyright) entender o código. |
| `criar_driver` | Abre um Firefox novo: perfil limpo, janela 1366×900, `page_load_strategy = "eager"`, limite de 90 s para carregar | Perfil limpo garante que um teste não herda login/cookies do outro. "eager" não espera anúncios e imagens: cada página já tem sua própria espera. |
| `geckodriver` | Pede ao Selenium Manager o geckodriver compatível com o Firefox, ignorando o do PATH (`@cache`: uma vez por execução) | No Parrot, `/usr/bin/geckodriver` vem do pacote eyewitness e é antigo demais para o Firefox atual. |
| `driver` (fixture) | Abre o navegador antes do teste e fecha depois | Todo teste recebe um navegador pronto e nunca deixa um aberto, mesmo se falhar. |
| `outra_sessao` (fixture) | Abre um segundo Firefox independente, que compartilha as notas com o primeiro | Faz o papel do outro jogador (batalhas) ou do usuário procurado (CT_0012). |
| `pytest_runtest_makereport` | Depois de cada teste: tira o print, define o status e adiciona ao relatório o print, a URL final, o resultado esperado, os dados do ambiente e as notas | É a evidência de execução que o documento pede. |
| `registro_do_ambiente` | Monta o texto com data/hora, URL, navegador e versão, sistema, viewport, zoom e orientação | O documento revisado pede esses dados junto de cada captura. |
| `pytest_html_report_title` / `pytest_html_results_summary` | Título e texto de abertura do relatório | Identifica a disciplina, o documento e o navegador usados. |

### `pages/base_page.py` — funções comuns a todas as páginas

Todas as páginas herdam de `BasePage`.

| Função | O que faz | Por quê |
|---|---|---|
| `__init__` | Guarda o navegador e cria o `WebDriverWait` (30 s por padrão) | Toda página precisa esperar elementos; o tempo fica num lugar só. |
| `abrir` | Abre a URL; se o site responder 503, abre a cópia do Web Archive e registra uma nota | A ladder e a Pokédex às vezes saem do ar; a cópia permite demonstrar o caso mesmo assim. |
| `_get` | `driver.get` que ignora o erro de tempo de carregamento | O Web Archive às vezes demora em recursos secundários; a página em si já está utilizável. |
| `indisponivel` | Diz se o título da página indica "503 / Service Unavailable" | Usada por `abrir` e pelos testes que dão *skip* quando o servidor está fora. |
| `nota` | Registra uma observação que vai para o relatório | Documenta diferenças entre o documento e o site sem reprovar o caso. |
| `passo` | Imprime "Passo n: …" | Liga a saída do teste aos passos do documento. |
| `ok` | Imprime "OK - …" | Mostra o que foi verificado com sucesso. |
| `resultado_esperado` | Imprime e guarda o resultado esperado do caso | Segue a estrutura do documento revisado (resultado consolidado na última etapa) e leva o texto ao relatório. |
| `achar` | Espera um elemento ficar visível (ou só existir) e o devolve destacado | Ponto central de espera: evita clicar em algo que ainda não apareceu. |
| `achar_todos` | Espera o primeiro aparecer e devolve todos | Usada para listas (linhas da ladder, títulos). |
| `clicar` | Clica num elemento (ou seletor), com destaque e pausa no modo demo | Uma forma única de clicar, que já espera o elemento. |
| `digitar` | Limpa o campo e digita; no modo demo, letra por letra | A plateia acompanha a digitação na apresentação. |
| `substituir` | Troca o conteúdo com Ctrl+A + Backspace | Para campos em que o `clear()` do Selenium não funciona. |
| `visiveis` | Elementos visíveis do seletor, ignorando os que somem durante a checagem | O cliente do Showdown mantém cópias ocultas de vários elementos e redesenha telas o tempo todo. |
| `textos` | Textos dos elementos visíveis, ignorando os redesenhados durante a leitura | Mesma razão: leitura resistente a redesenho. |
| `esperar_visivel` | Espera e devolve o primeiro elemento **visível** do seletor | `achar` pegaria uma cópia oculta; esta escolhe a que o usuário vê. |
| `destacar` | No modo demo, rola até o elemento e desenha uma borda vermelha | Mostra na apresentação onde o teste está agindo. |
| `demo_pausa` | No modo demo, pausa entre ações | Deixa a execução acompanhável; fora do demo não faz nada. |

### `pages/ladder_page.py` — ranking (CT_0001)

| Função | O que faz | Por quê |
|---|---|---|
| `abrir_formato` | Abre `pokemonshowdown.com/ladder/<formato>` e espera a tabela | Passo 1 do caso. |
| `titulo` | Título da ladder (ex.: "OverUsed") | Confirma que o formato exibido é o selecionado. |
| `linhas` | `[(posição, nome, Elo, link)]` dos primeiros colocados | Permite conferir a ordenação (posições em sequência, Elo decrescente). |
| `abrir_perfil` | Clica no nome e espera a URL `/users/...` | Passo 3; devolve o link para comparar com o jogador clicado. |
| `esperar_perfil` | Espera o painel do perfil com o nome do jogador | Confirma que o perfil aberto corresponde ao jogador selecionado. |

### `pages/replays_page.py` — busca de replays (CT_0002)

| Função | O que faz | Por quê |
|---|---|---|
| `abrir_busca` | Abre `replay.pokemonshowdown.com` (sem Web Archive) | A busca depende da API do servidor, que a cópia arquivada não tem. |
| `buscar` | Preenche usuário e formato, clica em "Search" e espera a URL mudar | A mudança de URL indica que a busca nova foi feita. |
| `resultados` | `[(formato, jogador1, jogador2)]` da última seção de resultados | Permite verificar formato, usuário e participantes de cada replay. |

### `pages/dex_page.py` — Pokédex (CT_0003)

| Função | O que faz | Por quê |
|---|---|---|
| `abrir_inicio` | Abre a Pokédex e espera o campo de busca | Ponto de partida do caso. |
| `pesquisar` | Digita o termo e espera os resultados | Passo 1. |
| `abrir_resultado` | Clica no resultado (`move|Stealth Rock`) e espera o título | Abre a página do golpe. |
| `entrada` | Painel aberto por último | A Pokédex abre painéis lado a lado; o último é o atual. Espera sem destacar porque rolar a página atrapalha as listas. |
| `titulo` | Título da página aberta | Confirma que o golpe certo foi aberto. |
| `texto` | `textContent` de um elemento | Lê o texto real, sem o `uppercase` aplicado pelo CSS. |
| `grupos_aprendizado` | Cabeçalhos da lista (Level-up, TM/HM, Egg …) | Verifica o agrupamento por método de aprendizado. |
| `rolar_ate_entrada` | Rola o painel até o item aparecer | A lista é virtual: só os itens visíveis existem na página. |
| `rolar_ate_pokemon` | Atalho de `rolar_ate_entrada` para Pokémon | Legibilidade do teste. |
| `grupo_do_item` | Cabeçalho sob o qual um link aparece | Mostra no relatório em que grupo o Garchomp está. |

### `pages/client_page.py` — cliente de batalha (CT_0004, CT_0010, CT_0011, CT_0012)

| Função | O que faz | Por quê |
|---|---|---|
| `abrir_lobby` | Abre `play.pokemonshowdown.com` e espera "Battle!" e "Choose name" | "Choose name" só aparece quando o cliente conectou ao servidor. |
| `clicar_choose_name` / `informar_nome` | Abre a janela de nome, digita e confirma | Passos do CT_0004 e base de `conectar`. |
| `texto_popup` / `esperar_texto_popup` | Texto da janela (popup) aberta / espera um trecho aparecer | Lê avisos como "The name you chose is registered". |
| `popup_tem_senha` | Diz se a janela pede senha | Resultado esperado do CT_0004 (pede autenticação). |
| `nome_conectado` / `esperar_nome_conectado` | Nome exibido no topo / espera ser o nome escolhido | Confirma se a sessão está ou não conectada com um nome. |
| `clicar_watch_a_battle` | Abre "Watch a battle" e espera a lista | Passo 1 do CT_0011. |
| `filtrar_formato` | Escolhe o formato e espera a lista só ter esse formato | Garante uma batalha 1v1 (Random Battle). |
| `formato_do_filtro` | Texto do filtro atual | Confere que a lista abriu sem filtro. |
| `batalhas_listadas` | `[(link, formato, jogador1, jogador2)]` das batalhas em andamento | Escolhe uma batalha para assistir. |
| `resumo_da_lista` | Texto de resumo da lista | Informação para o relatório. |
| `abrir_batalha` | Abre a batalha e espera campo e log | Passo 2 do CT_0011. |
| `turno` / `log` | Turno atual / texto do log da sala | Verifica que a batalha avança em tempo real. |
| `botoes_da_batalha` | Botões disponíveis na sala | Confirma que o espectador não recebe golpes nem trocas. |
| `usuarios_na_sala` | Contagem de usuários na sala | Informação para o relatório. |
| `procurar_usuario` | "Find a user": digita o nome e devolve o texto do perfil | Usada para desafiar o oponente nas batalhas. |
| `campo_de_busca_de_usuario` | Abre "Find a user" e devolve o campo | Passo 1 do CT_0012. |
| `botoes_do_popup` | `{texto: habilitado}` dos botões da janela | Confere que "Chat" está disponível (usuário online). |
| `clicar_no_popup` | Espera o botão com o texto e clica | A janela é desenhada em etapas; o botão pode aparecer depois. |
| `janela_de_mensagem` | Janela de mensagem privada com o usuário | Resultado esperado do CT_0012. |
| `ler_janela_de_mensagem` | Texto da janela de mensagem e se ela tem campo para escrever (lê de novo se a janela for redesenhada) | Verificação final do CT_0012, resistente ao redesenho quando o histórico chega. |
| `enviar_desafio` | Escolhe formato, marca "Don't allow spectators" e envia | Inicia a batalha de teste sem expor a partida. |
| `aceitar_desafio` | Aceita o desafio do outro lado (repete se a janela for redesenhada) | O oponente aceita para a batalha começar. |
| `esperar_sala_de_batalha` | Espera abrir a sala `/battle-...` | As duas sessões precisam estar na mesma sala. |
| `escolher_formato_da_fila` | Escolhe o formato da fila (com busca) | CT_0010 usa um formato pouco jogado. |
| `clicar_battle` / `cancelar_busca` / `texto_da_busca` | Entra na fila / cancela / lê o estado ("Searching…", "Battle!") | Passos do CT_0010. |
| `em_batalha` | Diz se alguma sala de batalha abriu | Resultado esperado do CT_0010: nenhuma batalha depois do Cancel. |

### `pages/battle_page.py` — sala de batalha (CT_0007, CT_0008, CT_0009)

| Função | O que faz | Por quê |
|---|---|---|
| `BattlePage.__init__` | Guarda o seletor da sala; espera até 60 s | Turnos dependem do outro jogador e podem demorar. |
| `log` / `esperar_no_log` | Texto do log / espera um trecho | O log é a prova do que aconteceu (troca, Tera, desistência). |
| `turno` | Número do turno, lido via JavaScript | O marcador é recriado a cada turno; a referência do Selenium ficaria inválida. |
| `esperar_turno` | Espera o turno chegar ao número; faz trocas obrigatórias se alguém for nocauteado | Sem isso a batalha travaria esperando uma troca. |
| `fazer_troca_obrigatoria` | Escolhe o primeiro reserva quando o servidor exige troca | Usada por `esperar_turno`. |
| `texto_dos_controles` | Texto da área de ações | Lê avisos como "will switch in". |
| `icones_dos_times` | Quantidade de Pokémon de cada lado | Confirma que a batalha abriu com 6 x 6. |
| `ativo` / `reservas` | Pokémon em campo / Pokémon que podem entrar | Base do CT_0007 (troca). |
| `golpes` / `esperar_acoes` | Golpes disponíveis / espera o turno pedir decisão | Sincroniza as ações dos dois jogadores. |
| `trocar_para` | Clica no Pokémon da lista "Switch" | Passo 2 do CT_0007. |
| `jogar_turno` | Oponente escolhe um golpe e confirma o registro (tenta de novo se a tela for redesenhada) | O turno só anda quando os dois lados jogam. |
| `usar_golpe` | Clica num golpe | Passo 3 do CT_0008. |
| `caixa_tera` / `tipo_tera` | Opção "Terastallize" / tipo Tera do Pokémon | Base do CT_0008. |
| `aguardando_oponente` | Espera "Waiting for opponent" | Confirma que a escolha foi registrada. |
| `fechar_aba` / `texto_popup` / `confirmar_desistencia` | Tenta fechar a aba / lê a confirmação / escolhe "Forfeit" | Passos do CT_0009. |
| `desistir_se_em_andamento` | Encerra a partida no fim do teste | Limpeza: não deixa partidas de teste abertas no servidor. |
| `repetir` | Repete uma ação se a tela for redesenhada no meio dela (*stale element*) | O cliente redesenha janelas quando chegam dados do servidor. |
| `nome_de_teste` | Gera um nome de convidado único (`QA Jogador 1234`) | Evita conflito entre execuções e com nomes reais. |
| `conectar` | Abre o lobby e conecta com um nome de convidado | Pré-condição de vários casos ("usuário logado"). |
| `iniciar_batalha` | Conecta as duas sessões, uma desafia a outra (partida privada) e espera a sala | Pré-condição das batalhas sem envolver jogadores reais. |

### `pages/teambuilder_page.py` — Teambuilder (CT_0005, CT_0006)

| Função | O que faz | Por quê |
|---|---|---|
| `abrir_teambuilder` / `_esperar_pronto` | Abre o Teambuilder e espera o cliente terminar de conectar | O cliente redesenha a tela ao conectar; agir antes perderia o clique. |
| `_esperar_redesenho` | Espera os downloads do formato terminarem (`jQuery.active === 0`) | Ao abrir um time, o formulário é refeito quando os dados chegam. |
| `nomes_dos_times` / `quantidade_de_times` | Times exibidos na listagem | Verifica a listagem atualizada. |
| `voltar_para_lista` | Volta da edição para a lista | Depois de duplicar, a cópia abre em edição. |
| `criar_times_salvos` | Grava dois times direto no armazenamento do navegador | Pré-condição ("usuário com pelo menos dois times salvos"), não é passo do caso. Os times ficam no `localStorage`, então não precisa de login. |
| `times_salvos` | `[(nome, pasta, formato, conteúdo)]` como estão gravados | Prova que o original não mudou e que a cópia é idêntica. |
| `pastas` | Textos da coluna de pastas | Confere que a pasta foi criada. |
| `clicar_add_folder` / `texto_popup` / `confirmar_nome_da_pasta` | "(add folder)" / lê a janela / digita o nome e confirma | Passos 1 e 2 do CT_0005. |
| `selecionar_pasta` | Abre uma pasta ou "(all)" | Filtra a listagem pela pasta. |
| `titulo_da_listagem` | Título da listagem atual | Confirma qual pasta está aberta. |
| `arrastar_time_para_pasta` | Arrasta o time até a pasta disparando os eventos de arraste via JavaScript | O Teambuilder usa o arrastar-e-soltar do HTML5, que o WebDriver não gera no Firefox. |
| `duplicar_time` / `nome_em_edicao` | Clica em duplicar / lê o nome do time em edição | Passo 1 do CT_0006. |

### `tests/` — os casos de teste

Cada função `test_ct00NN_...` é um caso do documento, marcada com `@pytest.mark.ct("CT_00NN")` (o código vai
para o nome do print e para o relatório). Detalhes que não estão nas páginas:

| Arquivo | Detalhe |
|---|---|
| `test_batalha.py` | Fixture `batalha`: inicia a partida entre as duas sessões e, no fim, desiste dela. Se o servidor limitar novas partidas, dá *skip*. `passo_1_abrir_batalha` é o passo 1 comum aos três casos. |
| `test_cliente.py` | `CONTA_REGISTRADA = "Zarel"` (conta pública do criador do site, citada no documento); `FORMATO_FILA` é um formato pouco jogado, para o Cancel acontecer antes de achar adversário. |
| `test_teambuilder.py` | `TIME` e `TIMES_SALVOS`: times no formato de exportação do Showdown usados como pré-condição. |

### Outros arquivos

| Arquivo | Para que serve |
|---|---|
| `apresentacao.sh` | Cria o `.venv` na primeira vez, roda com `--demo -s` e abre o relatório. |
| `pytest.ini` | Pasta dos testes, opções padrão (`-v`, relatório HTML num arquivo só) e o marcador `ct`. |
| `requirements.txt` | Dependências Python. |
| `.zed/tasks.json` / `.zed/settings.json` | Tarefas do botão ▶ no Zed e uso do pytest como executor. |
| `.gitignore` | Não versiona `.venv`, relatórios, evidências e caches. |

---

## Decisões e limitações

### Batalhas sem envolver outros jogadores

CT_0007, CT_0008 e CT_0009 precisam de uma batalha em andamento. Entrar na fila do "Battle!" colocaria o teste
contra um jogador real, então cada caso abre **dois navegadores** com nomes de convidado próprios (`QA Jogador ####`
e `QA Oponente ####`): um desafia o outro em [Gen 9] Random Battle com "Don't allow spectators" marcado.
O oponente só escolhe um golpe para o turno andar. No fim do caso a partida é encerrada.

Se a suíte for repetida muitas vezes seguidas, o servidor pode recusar novas partidas por alguns minutos
("Due to high load, you are limited to 12 battles and team validations every 3 minutes"). Nesse caso os casos de
batalha aparecem como *skipped* (ou o CT_0010 demora a entrar na fila); basta esperar uns minutos e rodar de novo.

O CT_0012 também usa duas sessões (o usuário procurado está na segunda) e só abre a janela de chat; nenhuma
mensagem é enviada. O CT_0010 entra na fila de um formato pouco jogado (Challenge Cup 2v2) e cancela em seguida;
se mesmo assim um adversário for encontrado antes do Cancel, o teste desiste da partida e o caso aparece como *skipped*.

### Telas redesenhadas

O cliente do Showdown recebe dados pelo servidor e redesenha janelas a qualquer momento. Um elemento encontrado
pode ser substituído antes do clique (erro *stale element*). Por isso o código usa esperas que devolvem o próprio
valor lido, leituras que ignoram elementos redesenhados (`visiveis`, `textos`) e a função `repetir` nas ações
mais sujeitas a isso.

### Diferenças entre o documento e o site

Os testes validam o comportamento real; quando ele difere do texto do documento, o relatório registra uma nota.

| Caso | Documento | Site |
|---|---|---|
| CT_0006 | Passo 3: clicar em "Paste copy here" | Esse botão não existe. A cópia vai para a pasta arrastando-a, que é o recurso do Teambuilder. |
| CT_0007 a CT_0009 | Passo 1: clicar em "Battle" | A partida começa por desafio direto entre as duas sessões de teste (ver acima). |
| CT_0008 | Resultado esperado: "Teraliza o ataque do Pokémon selecionado" | O teste confere no log que o Pokémon terastalizou para o Tera Type do time, como diz o resumo do caso. |
| CT_0012 | Dois usuários registrados | Duas sessões de convidado com nome. O perfil não escreve "Online"; só usuários offline recebem "(Offline)". |

### Site fora do ar

Se a ladder ou a Pokédex responderem 503, o teste usa a cópia mais recente do Web Archive e registra uma nota no
relatório. Replays e cliente dependem do servidor; nesse caso o teste é marcado como *skipped* com o motivo.

### Dados e credenciais

Nenhuma senha ou conta real é usada: todas as sessões são de convidado, com nomes gerados pelo teste, e os prints
não contêm credenciais. Os times do Teambuilder ficam só no navegador de teste, que é descartado no fim de cada caso.
