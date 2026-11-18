# Automação de testes – Pokémon Showdown (Selenium + Python + Firefox)

Automação dos casos de teste **CT_0001 a CT_0012** do documento de casos de uso revisado
`qatrabalho_revisado_QA.docx` (Desafio 4.0 – Qualidade e Teste de Software).

Na revisão, a coluna "Sistema" de cada caso registra só o **resultado esperado, consolidado na última etapa**;
as etapas intermediárias são apenas ações do usuário. Os testes seguem a mesma estrutura: executam os passos
do documento, imprimem o "Resultado esperado" com o texto do caso e só então fazem as verificações finais.
As verificações intermediárias que restaram servem para garantir que o passo aconteceu antes de seguir.

| Área | Casos | Arquivo de teste |
|---|---|---|
| Ladder | CT_0001 | `tests/test_ladder.py` |
| Replays | CT_0002 | `tests/test_replays.py` |
| Pokédex | CT_0003 | `tests/test_pokedex.py` |
| Cliente de batalha | CT_0004, CT_0010, CT_0011, CT_0012 | `tests/test_cliente.py` |
| Teambuilder | CT_0005, CT_0006 | `tests/test_teambuilder.py` |
| Batalha | CT_0007, CT_0008, CT_0009 | `tests/test_batalha.py` |

## Como rodar

```bash
./apresentacao.sh                         # apresentação: Firefox visível, devagar, elementos destacados em vermelho
./apresentacao.sh -k ct0007               # só um caso
./apresentacao.sh tests/test_batalha.py   # só uma área
./apresentacao.sh --pausa 2               # ainda mais devagar

.venv/bin/pytest --headless               # execução rápida, sem janela
```

Na primeira execução o script cria o `.venv` e instala o `requirements.txt` (Selenium, pytest e pytest-html).
O Selenium Manager encontra o Firefox instalado e baixa o geckodriver sozinho. A suíte completa leva cerca de 4 minutos.

No Zed, abra a pasta do projeto e use o ▶ ao lado de cada `def test_...` (tarefas em `.zed/tasks.json`:
"este caso" em modo apresentação ou rápido, e "arquivo atual"). Também dá para rodar pela paleta com `task: spawn`.

Saídas: `reports/relatorio.html` e `evidencias/` (PNG por caso). Para cada caso o relatório traz o resultado
esperado, a captura de tela (sem credenciais: os testes usam só sessões de convidado) e o registro pedido pelo
documento: data/hora, URL final, navegador e versão, viewport, zoom e orientação.

## Estrutura (Page Object)

| Arquivo | Página |
|---|---|
| `conftest.py` | Abre o Firefox, cria a segunda sessão (`outra_sessao`), tira as evidências e monta o relatório |
| `pages/base_page.py` | Funções comuns: abrir, esperar, clicar, digitar, destaque e pausas do modo apresentação |
| `pages/ladder_page.py` | Ladder (pokemonshowdown.com/ladder) |
| `pages/replays_page.py` | Busca de replays |
| `pages/dex_page.py` | Pokédex: busca e página de golpe |
| `pages/client_page.py` | Cliente (play.pokemonshowdown.com): nome, fila, desafio, "Watch a battle", "Find a user" e chat |
| `pages/teambuilder_page.py` | Teambuilder: pastas, arrastar time e duplicar |
| `pages/battle_page.py` | Sala de batalha: troca, golpes, Tera, desistência; e o início da partida entre as duas sessões |

## Como os casos de batalha são feitos sem envolver outros jogadores

CT_0007, CT_0008 e CT_0009 precisam de uma batalha em andamento. Entrar na fila do "Battle!" colocaria o teste
contra um jogador real, então cada caso abre **dois navegadores** com nomes de convidado próprios (`QA Jogador ####`
e `QA Oponente ####`): um desafia o outro em [Gen 9] Random Battle com "Don't allow spectators" marcado.
O oponente só escolhe um golpe para o turno andar. No fim do caso a partida é encerrada.

Se a suíte for repetida muitas vezes seguidas, o servidor pode recusar novas partidas por alguns minutos
("Due to high load, you are limited to 12 battles and team validations every 3 minutes"). Nesse caso os casos de
batalha aparecem como *skipped* com esse motivo; basta esperar uns minutos e rodar de novo.

O CT_0012 também usa duas sessões (o usuário procurado está na segunda) e só abre a janela de chat; nenhuma
mensagem é enviada. O CT_0010 entra na fila de um formato pouco jogado (Challenge Cup 2v2) e cancela em seguida;
se mesmo assim um adversário for encontrado antes do Cancel, o teste desiste da partida e o caso aparece como *skipped*.

## Diferenças entre o documento e o site

Os testes validam o comportamento real; quando ele difere do texto do documento, o relatório registra uma nota.

| Caso | Documento | Site |
|---|---|---|
| CT_0006 | Passo 3: clicar em "Paste copy here" | Esse botão não existe. A cópia vai para a pasta arrastando-a, que é o recurso do Teambuilder. O arraste é disparado por JavaScript, porque o WebDriver não gera o arrastar-e-soltar do HTML5 no Firefox. |
| CT_0007 a CT_0009 | Passo 1: clicar em "Battle" | A partida começa por desafio direto entre as duas sessões de teste (ver acima). |
| CT_0008 | Resultado esperado: "Teraliza o ataque do Pokémon selecionado" | O teste confere no log que o Pokémon terastalizou para o Tera Type do time, como diz o resumo do caso. |
| CT_0012 | Dois usuários registrados | Duas sessões de convidado com nome. O perfil não escreve "Online"; só usuários offline recebem "(Offline)". |

## Site fora do ar

Se a ladder ou a Pokédex responderem 503, o teste usa a cópia mais recente do Web Archive e registra uma nota no
relatório. Replays e cliente dependem do servidor; nesse caso o teste é marcado como *skipped* com o motivo.
