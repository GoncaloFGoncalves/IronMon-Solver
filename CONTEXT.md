# CONTEXT.md — Mon

Contexto persistente do projeto. Estado atual, objetivo, e o que separa um do outro.

---

## 0. North Star

> Estou a jogar **Kaizo IronMON em FireRed**. Quero um **guide** que me diga, em geral, coisas
> como *"um Snorlax que rolou physical e não é frágil, com STAB, bate em média um Alakazam
> special, porque tem melhores matchups contra o pool"*. E quando apanho o mon no lab, quero
> estreitar isso até ao caso concreto: **quão bom é este mon**, em que categoria cai, e **qual o
> impacto de ter ou não ter um determinado move**.

É um **solver**, não uma tabela: uma core strategy sobre ranges largos, refinada à medida que a
informação chega. Ver §1.2. Se uma funcionalidade não contribui para isto, está fora de âmbito.

---

## 1. Contexto de jogo: Kaizo IronMON, não FireRed vanilla

Isto não é uma run normal, e a diferença condiciona todo o design:

- **Um só mon.** Usa-se um Pokémon de cada vez; se morre, a run acaba. A análise é
  genuinamente de **um atacante contra um pool**, não de equipas.
- **Tudo randomizado.** Encontros, equipas de treinadores, movesets, abilities, evoluções, TMs.
  Não se sabe o que vem a seguir — **é exatamente por isso que faz sentido comparar contra o
  pool inteiro de mons possíveis**. O modelo do projeto encaixa no problema real.
- **Base stats redistribuídos ao acaso, com o BST preservado.** Não é uma permutação dos seis
  valores da espécie — é uma distribuição nova sujeita a somar o mesmo BST. Um Snorlax
  (BST 540) pode sair `160/100/20/20/110/130`. É a razão pela qual o Snorlax pode aparecer com
  Special Attack alto. Ver §3.2.
- **Os tipos das espécies mantêm-se.** Um Snorlax é sempre NORMAL. A análise de type chart
  assenta em terreno firme.
- **Level boost de +50%** nos treinadores face ao vanilla.
- **Forced fully evolved** a partir de um certo nível (~30, a confirmar): o pool adversário
  encolhe para **só evoluções finais**.
- **Cap de BST 551 no teu mon, verificado no momento em que o apanhas.** Não podes apanhar um
  mon com BST > 551. Mas o cap **não é permanente**: com forced evolution ligado e evoluções
  randomizadas, o teu mon pode evoluir para lá de 551 e continua a ser jogável. O pool atacante
  é portanto `{BST <= 551} + {destinos de evolução desses}`.
- Como **defensores, todos os mons estão disponíveis**, sem cap. Os dois pools são diferentes
  — ver §1.2.
- **Regras de rota** que fixam a ordem dos checkpoints: Misty imediatamente após o Nugget da
  Nugget Bridge; Erika antes de entrar no Rocket Hideout; Rival no S.S. Anne antes de qualquer
  outro treinador; Rival obrigatório para sair de Lavender Town na primeira visita.

**Versão: FireRed.**

### 1.1 O que sobrevive à randomização

Por espécie, o que é invariante entre runs:

| Propriedade | Invariante? |
|---|---|
| Tipos | **sim** |
| BST | **sim** |
| Distribuição dos stats pelos 6 slots | não — sorteada por run |
| Moveset (quais os moves) | não — sorteados do pool inteiro |
| **Calendário de aprendizagem** | **sim** — vanilla, nível 1 preenchido até 4 (validado, 386/386) |
| Compatibilidade de TMs | não — 50/50 por mon, ~25 TMs |
| Linha evolutiva | não — randomizada |

**O calendário sobrevive, os moves não.** Se o Snorlax aprende um move ao nível 9 no vanilla,
aprende um move ao nível 9 na run — mas sorteado. Logo o *número* de moves que uma espécie já
aprendeu a um dado nível é invariante, e varia muito: ao checkpoint do Erika (nível 43) o Abra
tem **1** move de level-up e o Medicham tem **16**.

Isso importa porque o moveset são os **4 melhores de N sorteios**: mais sorteios, melhor
moveset. Com qualidade uniforme, a média dos percentis dos 4 melhores passa de 0.50 (N=4) para
0.85 (N=16). O mon com 16 sorteios não é um pouco melhor — joga num campeonato diferente.

**Consequência na chave:** a chave passa a `(tipos, BST, curva de aprendizagem)`, e sobe de
330 para **375** entradas (+14%). Continua abaixo das 386 espécies, logo o colapso mantém-se,
só que menor.

A consequência **não** é que uma tier-list estática seja inútil. É que **a unidade da tier-list
não é a espécie — é a espécie mais o tipo de roll**. "Snorlax-physical-não-frágil" e
"Snorlax-special" são linhas diferentes da mesma tabela, e é entre linhas dessas que a
comparação do §1.2 faz sentido.

### 1.2 Modelo: solver, não tabela

O sistema funciona por **camadas de range**, como um solver de poker. A camada base dá a *core
strategy* sobre ranges largos; cada informação nova estreita o range e refina a resposta. É
sempre **o mesmo motor de scoring**, parameterizado por uma especificação de range.

| Camada | O que se sabe | Range do adversário | Range do próprio | Resposta típica |
|---|---|---|---|---|
| **0. Core** | nada | pool inteiro | 27 perfis de roll | "Snorlax-physical com STAB bate Alakazam-special em média" |
| **1. Checkpoint** | onde estás na run | só evoluções finais, níveis fixos | 27 perfis | "e depois do Erika, muda para..." |
| **2. Roll** | os teus stats reais | idem | **1** (lido no tracker) | "o teu Snorlax concreto vale isto" |
| **3. Moveset** | os teus moves reais | idem | 1, moveset fixo | "e com estes 4 moves, isto" |
| **4. Encontro** | o que tens à frente | 1 espécie | 1 | matchup único |

A camada 0 é o produto principal — o "guide". As camadas 2-4 são o mesmo cálculo com o range
colapsado. Nada disto precisa de motores diferentes.

**A introdução de dados é opcional.** As camadas 0-1 respondem sem input nenhum: abres, procuras
um mon, lês. As camadas 2-4 desbloqueiam-se se — e só se — quiseres introduzir os dados reais da
run (stats rolados, moveset). O modo por omissão é **consulta**; introduzir uma entrada é uma
ação deliberada, nunca um passo obrigatório antes de obter resposta.

**Chave da tabela core.** Como só `(tipos, BST, curva de aprendizagem)` sobrevivem ao roll, duas
espécies que coincidam nos três são a mesma linha — são **375** (medido). O nome da espécie passa a ser um *índice* para a linha
(`Snorlax -> NORMAL, 540`), não a chave. Continuas a perguntar "e o Snorlax?" e a resposta vem
por baixo de uma tabela muito mais compacta que 386 espécies.

**Sem buckets de BST — indexa-se pelo valor exato.** O espaço *possível* de chaves é
`171 combinações de tipo x gama de BST`, o que dá milhares. Mas o espaço *ocupado* é **330**
(medido), porque cada espécie mapeia para exatamente uma chave. Agrupar BST em intervalos não
reduz nada abaixo disso e só perde resolução — logo indexa-se pelo BST exato.

**Os dois pools não são o mesmo.** O cap de 551 aplica-se só ao teu mon, e só na aquisição:

| Lado | Pool | Espécies | Chaves `(tipos, BST)` | x 27 perfis |
|---|---|---|---|---|
| Atacante (o teu mon) | `BST <= 551` (+ destinos de evolução) | 359 | **307** `(tipos, BST)` | 8 289 |
| Defensor | todos | 386 | **330** `(tipos, BST)` | 8 910 |

Com a curva de aprendizagem na chave do **atacante** (§1.1), esse lado sobe para 375 entradas.
O defensor não precisa dela — o que interessa nele é aguentar, não o moveset.

*Números reais, medidos sobre os dados do veekun (§2.1).* O colapso da chave é de ~15%: 48 chaves
são partilhadas por mais de uma espécie — por exemplo `FIGHTING / BST 455` cobre Primeape,
Hitmonlee, Hitmonchan e Hitmontop de uma vez, e `NORMAL / BST 490` cobre Kangaskhan, Tauros,
Miltank e Exploud.

São duas tabelas separadas, ambas pequenas. **A camada 0 não é a parte cara do projeto** — a
parte cara continua a ser a seleção de moveset (§4.3).

---

## 2. Estado do código

### 2.1 Os módulos

Construído com TDD, sem dependências além do numpy.

```
mon/
  stats.py      stat_at_level(base, nivel, iv, is_hp)      formula de Gen 3
  skew.py       profiles(bst) -> 27 StatProfile            modelo de 3 pares (3.2)
  typechart.py  TypeChart.effectiveness(atk, defs)         chart Gen 2-5 (corrige 5.7)
  dex.py        build_species(...) -> list[Species]        parsing puro dos CSVs
  veekun.py     load_species() -> 386 especies             I/O + cache em data/veekun/
  damage.py     probability_of_ko(dano, hp, golpes)        distribuicao dos 16 rolls (3.6)
  formula.py    damage_before_roll(...)                    formula de dano de Gen 3
  battle.py     win_probability(me, them)                  desfecho da troca (3.6)
  moves.py      build_moves(...) -> list[Move]             208 moves, filtros do GRUPOS.md
  learnset.py   learn_schedule / moves_known_at            calendario de aprendizagem
  tms.py        tms_available_at(checkpoint)               recolha de TMs pela run
  checkpoints.py CHECKPOINTS, kaizo_levels(...)            os 9 splits da run (3.3)
  status.py     paralysed / burned / poisoned / ...        efeitos de status de Gen 3
  abilities.py  utilization(ability, ctx) -> swing          aproveitamento (3.5b, 3.6b)
  conditional.py turns_per_hit / focus_punch                moves com condicao (3.6b)
  dungeons.py   mandatory_battles(section)                  orcamento sem cura (3.6b)
  sequence.py   resolve / run_section -> Outcome            estados encadeados (3.6b)
  ivs.py        BANDS, band_of(iv)                          bandas do atacante (3.4)
  vector.py     ko_table / win_block / win_probabilities    score vectorizado (3.7)
  upside.py     scenarios / value -> swing do efeito        upside real (3.5b)
  batch.py      partitions / pending / run                  camada 0 retomavel (3.7)
  firered.py    load_species_info() -> expYield, curva       disassembly de Gen 3
  exp.py        thresholds / level_at / exp_from_defeating   curvas de EXP (3.3)
  trainers.py   load_trainers / trainers_before              345 treinadores (3.3)
  levels.py     expected_levels() -> nivel por curva         simulacao de EXP (3.3)
  pool.py       DefenderPool.damage_matrix(...)              defensores em arrays
  orderstat.py  expected_best / subset_weights               melhor de N aleatorios
  variants.py   variants(especie, nivel, iv) -> 27           especie -> numeros
  score.py      score_variant(...) -> Cell                   o kernel
  run.py        python -m mon.run                            a camada 0, retomavel
  export.py     build_payload(...) -> 1.5 MB                 empacota a camada 0
  viewer.py     python -m mon.viewer                         constroi docs/index.html
viewer/
  template.html a pagina                                     ranking + lookup + ao vivo
  engine.js     port do kernel para JS                       movesets concretos, <20 ms
tests/          196 testes, todos verdes
```

Notas:

- Os três módulos são **puros**: sem I/O, sem prints, sem estado global. Nenhum depende
  das decisões ainda abertas no §5.
- `skew.profiles` devolve stats em **vírgula flutuante** (frações exatas de BST), para
  preservar a garantia de conservação do BST. **A conversão para inteiro acontece em
  `stats.stat_at_level`**, que arredonda o base stat antes de aplicar a fórmula — no jogo
  um base stat é sempre inteiro. Há teste de regressão.
- `damage.probability_of_ko` recebe o dano **antes do roll** (o valor máximo), não a média.
  O parâmetro chamava-se `average_damage` e estava a induzir em erro; agora é `base_damage`.
- **A ordem de ataque sai do perfil**: `Speed = BST/6` (híbrido), `BST/4` (fast), `BST/12`
  (bulky). Com dois mons híbridos, o de BST maior ataca primeiro, por construção. Os "mais
  buckets" do futuro são mais variantes de tempo, sem mexer no resto.
- **`moves.py` dá 208 moves utilizáveis** dos 354 de Gen 3: 195 por BP, 8 status com dano,
  2 de dano fixo, 2 de dano igual ao nível, 1 por fração de HP. A categoria física/especial
  sai do **tipo**, nunca do `damage_class` do veekun (que é Gen 4+).
- **`learnset.py` — regra do calendário, validada contra um log real do randomizer.**
  O calendário é o do **FRLG vanilla, com o nível 1 preenchido até pelo menos 4 moves**
  (o Kaizo garante 4 moves à saída do lab). Bate em **386 de 386 espécies**.
  Duas armadilhas de dados que só apareceram na validação: o Deoxys guarda o learnset
  sob uma *forma* e não sob o número base (cada jogo de Gen 3 usa uma forma diferente),
  e fundir as formas soma os calendários — tem de se escolher uma.
- **`checkpoints.py` guarda a derivação, não os valores finais.** Os níveis vanilla de FRLG
  são a fonte e os do Kaizo saem de `LEVEL_BOOST = 1.5` — se o ruleset mudar, muda um número.
  O mesmo para `FORCED_FULLY_EVOLVED_AT = 30`, que decide a partir de que checkpoint o pool
  adversário encolhe (o Erika, porque é onde o nível mínimo passa os 30).
  Os nomes dos checkpoints estão duplicados em `tms.py`; há um teste que falha se divergirem.
- **O pool real de candidatos é metade do que eu tinha estimado.** Medido sobre as 386
  espécies, combinando level-up e TMs disponíveis:

  | Checkpoint | Nível | Level-up (mediana) | TMs | Utilizáveis (50%) | **N** |
  |---|---|---|---|---|---|
  | Brock | 21 | 7 | 3 | 1.5 | **8.5** |
  | Erika | 43 | 11 | 11 | 5.5 | **16.5** |
  | Koga | 64 | 12 | 15 | 7.5 | **19.5** |
  | Elite 4 | 94 | 12 | 25 | 12.5 | **24.5** |

  Não são ~50 candidatos por mon — são **8.5 no início e 24.5 no fim**. Isso derruba o custo
  da seleção exaustiva de 2 085 h para **74 h**, e o guloso para **1.2 h**.
- **O motor cobre agora turnos perdidos e dano residual.** `Combatant` ganhou
  `action_chance` (paralisia, flinch, freeze) e `residual` (burn, poison, leech seed).
  Turnos decorridos deixaram de ser golpes acertados: a probabilidade de KO soma-se sobre
  quantos golpes o atacante chegou a dar, ponderado pela binomial. Com `action_chance = 1`
  reduz-se exatamente ao cálculo anterior.
- **O swing de cada efeito, medido em troca equilibrada** (pontos percentuais de vitória):

  | Efeito | Atacante lento | Igual | Rápido |
  |---|---|---|---|
  | paralisia | **+70.7** | +39.5 | **+8.2** |
  | burn (vs físico) | +81.2 | +50.0 | +18.8 |
  | freeze | +78.6 | +48.3 | +18.0 |
  | confusion | +63.3 | +38.7 | +14.1 |
  | poison | +56.2 | +37.5 | +18.8 |

  Confirma o §3.5b em números: **o mesmo efeito vale 9x mais a um mon lento que a um rápido**.
  A paralisia é a de maior spread (70.7 → 8.2), porque é a única cujo valor é quase todo
  ordem de ataque; o poison é a de menor (56.2 → 18.8), porque o dano por turno vale o mesmo
  a quem quer que seja. Nenhuma tabela de "paralisia vale X" apanharia isto. Há regressão.
  (Tabela recalculada depois do bug de truncagem do §5 — os valores anteriores estavam todos
  2 a 8 pp abaixo.)
- **O `moves.csv` do veekun guarda os valores ATUAIS, não os de Gen 3.** 90 dos 354 moves
  de Gen 3 diferem. Resolvido com `gen_3_value()` + `move_changelog.csv`: a mudança mais
  antiga posterior à Gen 3 guarda o valor que vigorava na Gen 3. **60 dos 208 moves
  utilizáveis estavam errados** — giga-drain 75→60 BP e 10→5 PP, leech-life 80→20,
  petal-dance 120→70, future-sight 120→80, high-jump-kick 130→85, knock-off 65→20.
  Terceira vez que a mesma armadilha aparece (depois do `damage_class` e das abilities):
  **tudo o que vem do veekun é moderno até prova em contrário.**
- **`Move` ganhou `pp` e `drain`** — os dois recursos que a dungeon põe em causa (3.6b).
- **`abilities.py` implementa a opção (c)**: só as habilidades com mecânica modelada
  produzem swing (`guts`, `truant`, `intimidate`, `rock-head`); as restantes valem **zero**
  em vez de valerem um palpite. O swing é `score(efeito sempre) − score(efeito nunca)`
  sobre o motor do `battle.py`, e o `utilization()` desconta a acessibilidade da condição
  dentro da dungeon. Medido numa troca a 0.417 de base:

  | Habilidade | Swing bruto | Aproveitamento | Porquê |
  |---|---|---|---|
  | intimidate | +0.583 | +0.583 | incondicional, se ele bater por Atk |
  | rock-head | +0.417 | +0.417 | incondicional, se eu tiver move de recuo |
  | guts | **+0.052** | **+0.013** | 1.5x de Atk menos 1/8 do HP por turno |
  | truant | −0.365 | −0.365 | metade dos turnos perdidos |

  **O Guts quase não vale nada, e é um resultado, não uma limitação do modelo.** O status
  que o liga custa 1/8 do HP por turno e não há cura dentro da dungeon: o 1.5x paga o
  próprio custo. A `GUTS_WINDOW_TURNS = 8` (não 16 — burn e poison são ambos 1/8 em Gen 3)
  e o `DUNGEON_SELF_STATUS = 0.25` descontam o resto, porque o status tem de ser *oferecido*
  pelo adversário: auto-inflingir exigiria itens ou um mon selvagem, os dois fora das regras.
- **16 dos 207 moves batem mais do que uma vez por turno** e estavam a ser pontuados pelo BP de
  um golpe só. Com a truncagem a acontecer golpe a golpe (§4), isto não é um detalhe de escala:

  | Move | BP nominal | Dano/turno real |
  |---|---|---|
  | bonemerang | 50 | **100** (2 golpes fixos) |
  | bone-rush, rock-blast | 25 | **75** (2-5 golpes) |
  | double-kick | 30 | **60** |
  | spike-cannon | 20 | 60 |
  | bullet-seed, icicle-spear | 10 | 30 |

  Em Gen 3 a contagem de 2-5 sorteia-se **em cada turno**, com 3/8, 3/8, 1/8, 1/8 — e por isso o
  total de golpes é uma soma aleatória, não a média vezes os turnos. Contra 120 de HP em 3 turnos,
  o `double-kick` passava de 0.000 (ingénuo) para **1.000** (real).
  O `triple-kick` é caso à parte: escala 10/20/30 e vale 60 no total, mas o veekun guarda 10, que
  é só o primeiro golpe. Entra como 20 de BP x 3 golpes.
- **`vector.py` é o caminho que faz a camada 0 correr.** Medido: 1.5x10^7 avaliações/s contra
  33 mil/s em Python puro. A tabela indexa `(dano antes do roll, turnos, hp)`, constrói-se em
  0.34 s e ocupa 18 MB, e **confere com o `damage.py`** — há teste, porque foi uma divergência
  entre dois caminhos que apanhou o bug do §4. Os moves multi-golpe entram como uma tabela
  própria por distribuição de golpes; só há 4 distribuições em todo o pool.

  O débito depende da forma do acesso, e isso decide como o batch é escrito:

  | Caminho | Débito | Camada 0 |
  |---|---|---|
  | `win_probabilities`, índices aleatórios | 7.1x10^6/s | 51 h |
  | **`win_block`, atacante fixo por bloco** | **1.5x10^7/s** | **24 h** |

  Com o atacante fixo a tabela colapsa numa fatia de 7x701 que cabe em cache. **O batch tem de
  iterar por atacante, não por célula** — é a diferença entre 51 h e 24 h, e sai de borla porque
  a partição do §3.7 já é por espécie.
- **`upside.py` mede o swing do efeito secundário**, com as chances do `move_meta` (58 dos 207
  moves têm efeito). A probabilidade usada é a de **ter disparado ao menos uma vez na troca**,
  `1-(1-p)^turnos`, e não `p`. Confirma o §3.5b, e em dois sentidos opostos:

  | Move | Efeito | Swing num mon lento | Swing num mon rápido |
  |---|---|---|---|
  | thunderbolt | paralisia 10% | **+0.175** | +0.011 |
  | thunder, body-slam | paralisia 30% | **+0.423** | +0.027 |
  | sacred-fire | burn 50% | **+0.590** | +0.062 |
  | headbutt, rock-slide | flinch 30% | **0.000** | **+0.047** |
  | extrasensory | flinch 10% | **0.000** | +0.019 |

  O status vale até **16x mais** a um mon lento. O flinch vale **exactamente zero** a um mon
  lento — quem ataca em segundo não tira turno a ninguém — e é o único upside que prefere o mon
  rápido. Era isto que a pergunta do serene grace levantava, agora com número.
- O chart de `typechart.py` foi **validado contra `veekun/pokedex`**, revertendo as
  mudanças da Gen 6. As 17 linhas batem certo.
- **O `base_experience` do veekun é moderno: 375 das 386 espécies diferem**, e os valores atuais
  rondam o dobro (Blissey 255 em Gen 3, 635 hoje). Usá-lo inflacionaria todo o EXP e com ele
  todos os níveis esperados. A fonte passou a ser a **disassembly `pret/pokefirered`**, que é o
  próprio jogo (`firered.py`). Sexta instância da armadilha, e a de maior impacto até agora.
  As curvas de crescimento, essas, estão certas no veekun — conferidas contra os totais
  canónicos ao nível 100 (1 000 000 / 800 000 / 1 250 000 / 1 059 860 / 600 000 / 1 640 000).
- **Fonte de dados: CSVs de `veekun/pokedex` via `raw.githubusercontent.com`**, e não a
  PokéAPI — a PokéAPI está bloqueada neste ambiente (403) e os CSVs são um ficheiro por
  tabela em vez de 386 chamadas. Substitui a decisão do §3.1.


## 3. Objetivo — especificação

### 3.1 Fontes de dados

| Dado | Fonte | Estado |
|---|---|---|
| Espécies, tipos, base stats, learnsets | **CSVs veekun/pokedex** | decidido (§2.1) |
| Moves (tipo, BP, efeito secundário) | **CSVs veekun/pokedex** | ver §3.5b |
| **Abilities** | **CSVs veekun/pokedex** | ver §3.5b |
| Type chart Gen 2-5 | `mon/typechart.py` | **feito e validado** |
| Níveis por checkpoint | **tabela manual** (§3.3) | estimativa feita, por calibrar |
| Regras Kaizo (boost, forced evo, BST) | ruleset IronMON | parcialmente levantado |

- **Pool: a dex de FRLG + a de Emerald**, ou seja Kanto + Hoenn = os **386 mons de Gen 3**.
- **TMs: compatibilidade 50/50 por mon**, medido no log real (49.9%). **Os HMs ficam fora
  do modelo.** Quais os TMs e onde se apanham não muda entre runs (só os moves que ensinam),
  logo o número disponível por checkpoint é invariante — tabela em `mon/tms.py`.
- **Cap de BST: 550 ou 551 é indiferente.** Nenhuma espécie de Gen 3 tem BST entre 541 e 554,
  por isso os dois valores dão exatamente o mesmo conjunto: **359 espécies, 307 chaves**.
- **Âmbito: Gen 2 para cima.** Gen 1 fica de fora (Special único quebra o modelo de skew).
- **Type chart é um dado do jogo:** Gen 2-5 (FRLG) sem FAIRY e com STEEL a resistir DARK/GHOST;
  Gen 6+ com FAIRY e sem essas resistências.

> **Lacuna 1:** a PokéAPI **não tem dados de treinadores nem de ginásios**. A tabela do §3.3 é
> mantida à mão. É a única parte do §3 sem fonte automática.

> **Lacuna 2 — armadilha de dados:** o campo `damage_class` da PokéAPI é a classificação
> **Gen 4+, por move**. Em Gen 3 o split físico/especial é **por tipo**, não por move. Usar
> `damage_class` diretamente dá a resposta errada para FRLG (ex.: classificaria um Hyper Beam
> como especial, quando em Gen 3 NORMAL é físico). O split tem de vir da lista de tipos físicos
> (`moves.PHYSICAL_TYPES`).

### 3.2 Modelo de skew — redistribuição soma-zero

Modela o **shuffle de base stats** do Kaizo. Transferência dentro de cada par, somando ao
maior metade do menor:

```
skew  = min(par) / 2
X     = max(par) + skew
resto = total - X   ( = min(par) / 2,  sempre >= 0 )

par defensivo (Def, SpD)          par ofensivo (Atk, SpA)
  físico    -> Def := X, SpD := resto     físico    -> Atk := Y, SpA := resto
  especial  -> SpD := X, Def := resto     especial  -> SpA := Y, Atk := resto
  híbrido   -> Def := SpD := total / 2    híbrido   -> Atk := SpA := total / 2
```

**Exemplo (Def 100, SpD 50):** skew = 25, X = 125, resto = 25 -> variantes **125/25**,
**25/125**, **75/75**.

**Snorlax** (Atk 110, Def 65, SpA 65, SpD 110): ambos os pares dão skew 32.5, X 142.5,
resto 32.5 -> `142.5/32.5`, `32.5/142.5`, `87.5/87.5`.

Verificado sobre Snorlax, Alakazam, Gengar, Onix e Shuckle: **o total é sempre preservado e o
residual nunca é negativo** (é `min/2` por construção). O problema de stats negativos da versão
anterior desapareceu.

#### O que a fórmula consome, e o problema que isso levanta

A fórmula precisa de um par `(Def, SpD)` para trabalhar. Nas camadas 2-4 (§1.2) isso é trivial:
lês os stats reais no tracker. Na **camada 0** não há stats reais — a distribuição foi sorteada.
**Que números se alimentam à fórmula?**

- **(a) Proxy vanilla** — usar os stats da espécie no jogo original. Snorlax: `Def 65 / SpD 110`.
- **(b) Neutro por BST** — se o roll redistribui o BST livremente pelos 6 slots, cada slot vale
  `BST/6` em esperança. Snorlax (BST 540): `Def 90 / SpD 90`.

| Base | Par defensivo | Variantes resultantes (fís. / resid. / híb.) |
|---|---|---|
| **Snorlax** (BST 540) | | |
| a. vanilla | 65 / 110 | 142.5 / 32.5 / 87.5 |
| b. BST/6 | 90 / 90 | 135.0 / 45.0 / 90.0 |
| **Alakazam** (BST 500) | | |
| a. vanilla | 45 / 95 | 117.5 / 22.5 / 70.0 |
| b. BST/6 | 83.3 / 83.3 | 125.0 / 41.7 / 83.3 |

**Decidido: (b).** O `Def 65 / SpD 110` do Snorlax **não existe na tua run** — foi substituído
por um sorteio. O que sobrevive é `BST = 540`, e daí a esperança de 90 por slot. Com (a)
estarias a sub-avaliar sistematicamente o Alakazam como defensor (bulk total 140 vs 166.7 — 19%
de diferença), quando em Kaizo um Alakazam tem exatamente a mesma probabilidade de rolar tanque
que qualquer outro mon de BST 500. (b) é também o que faz a chave `(tipos, BST)` do §1.2 fechar.

#### Forma fechada dos 3 ranges

Aplicando a fórmula a um par neutro `(BST/6, BST/6)`, tudo colapsa em frações do BST:

```
skew   = BST/12          def tank    ->  Def = BST/4  ,  SpD = BST/12
tank   = BST/4           híbrido     ->  Def = SpD    =  BST/6
resto  = BST/12          spdef tank  ->  Def = BST/12 ,  SpD = BST/4
                         (soma do par = BST/3, correto para 2 dos 6 slots)
```

| Mon | BST | def tank | híbrido | spdef tank |
|---|---|---|---|---|
| Onix | 385 | 96.2 / 32.1 | 64.2 / 64.2 | 32.1 / 96.2 |
| Alakazam | 500 | 125.0 / 41.7 | 83.3 / 83.3 | 41.7 / 125.0 |
| Snorlax | 540 | 135.0 / 45.0 | 90.0 / 90.0 | 45.0 / 135.0 |
| Dragonite | 600 | 150.0 / 50.0 | 100.0 / 100.0 | 50.0 / 150.0 |

Os 3 perfis são **ranges**, não estimativas pontuais: na camada 0 não se escolhe um, agrega-se
sobre os três. O mesmo se aplica ao par ofensivo `(Atk, SpA)`.

Consequência prática: **os ranges derivam-se só do BST**. Nenhum dado por espécie é preciso
além de `(tipos, BST)`, o que confirma a chave do §1.2. E como a redistribuição é livre, não há
um conjunto pequeno de rolls para enumerar exatamente — os 3 ranges são a aproximação.

#### Três pares, mesma fórmula

`(HP, Speed)` é tratado como **terceiro par**, com a mesma fórmula dos outros dois. O modelo
fica simétrico: nenhum stat fica de fora e o arquétipo "rápido" do §3.8 volta a funcionar na
camada 0.

| Par | Variante A | Híbrido | Variante B |
|---|---|---|---|
| `(Atk, SpA)` | Atk `BST/4`, SpA `BST/12` | ambos `BST/6` | SpA `BST/4`, Atk `BST/12` |
| `(Def, SpD)` | Def `BST/4`, SpD `BST/12` | ambos `BST/6` | SpD `BST/4`, Def `BST/12` |
| `(HP, Speed)` | HP `BST/4`, Speed `BST/12` | ambos `BST/6` | Speed `BST/4`, HP `BST/12` |

Cada par soma `BST/3` em todas as variantes, **logo os 27 perfis somam sempre exatamente o BST**.
O modelo é internamente consistente por construção.

Os três pares têm o **mesmo estatuto**: nenhum é "do atacante" ou "do defensor". Um mon é
descrito pelos três em conjunto, seja qual for o lado em que está (§3.5).

### 3.3 Níveis por checkpoint — MEDIDO

Fonte: **`kelseyyoung/FRLGIronmonMap`**, 345 treinadores com área e party. Os níveis do mapa
**já são os do Kaizo**, não os do vanilla — o Brock vem `18/18/18/18/21`, não `12/14`. Não se
aplica o `LEVEL_BOOST` por cima, seria contar o boost duas vezes.

Isso **valida a estimativa antiga** (`vanilla x 1.5`) para o adversário: Brock 18-21 e Giovanni
63-75 batem exactamente. O que faltava era o nível **do jogador**.

#### O nível do jogador — CALIBRADO contra runs reais

**O randomizer padroniza a curva de crescimento de todos os mons para FLUCTUATING.** A dimensão
das 6 curvas existia no modelo e não existe no jogo; saiu.

EXP de Gen 3, que **não escala com a diferença de níveis**: `exp = base x L / 7`, x1.5 em
treinador. O que conta é o nível de quem cai, e os adversários são randomizados, logo o exp yield
é um sorteio do pool. Daí sai a banda: **135.6** de média no pool todo, **172.5** se o treinador
traz mons já evoluídos.

Duas observações de runs reais do Gonçalo — "no Brock ronda 18-19" e "21 é o máximo com mons já
evoluídos" — saem do modelo **sem nada ajustado**:

| | Brock |
|---|---|
| yield médio do pool (135.6) | **19** |
| yield de espécies sem pré-evolução (172.5) | **21** |

Isso fixou também o conjunto de treinadores: as runs reais limpam as áreas da rota, não só os
inevitáveis. Há teste de calibração para as duas.

| Split | Adversário (o líder) | Jogador | Vantagem |
|---|---|---|---|
| Brock | 18 | 19 | **+1** |
| Misty | 27 | 36 | +9 |
| Surge | 27 | 46 | +19 |
| Erika | 36 | 58 | **+22** |
| Koga | 56 | 70 | +14 |
| Sabrina | 56 | 75 | +19 |
| Blaine | 63 | 82 | +19 |
| Giovanni | 68 | 83 | +15 |
| Elite 4 | 80 | 86 | **+6** |

**A vantagem sobe e depois fecha, e isso está confirmado em jogo.** É a forma que valida o
modelo, e diz onde a tabela tem de estar certa: chegas ao Brock em paridade, abres até +22 na
Erika e o Elite 4 volta a fechar para +6. **Os dois extremos são os pontos de perigo** — e são
precisamente o primeiro e o último checkpoint, onde a margem para um matchup mau é zero. Há teste
que falha se a forma deixar de subir-e-descer.

O nível do adversário é o do **líder**, não a mediana da rota: o que importa é a parede. O Brock
vem 18/18/18/18/21, e os bug catchers de nível 9 do caminho não baixam o que é preciso para o
vencer.

O `unavoidable()` fica no código — spinners e walkers do mapa, mais líderes e rival, 116 dos 345 —
porque é o conjunto que serve para perguntar "e se eu fugir a tudo". Dá o jogador 3 a 5 níveis
**abaixo** do adversário durante toda a run, e é por isso que não é o default: não é assim que a
run corre.

### 3.4 IVs — DECIDIDO

- **Defensor:** IV 31.
- **Atacante: três bandas**, com um valor representativo cada (`mon/ivs.py`):

  | Banda | Representativo |
  |---|---|
  | `sub-10` | 5 |
  | `sub-20` | 15 |
  | `20+` | 27 |

- EVs: 0. Nature: Serious (neutra).

A banda alta é **20+** e não 25+: com 25+ os IVs 20 a 24 não caíam em banda nenhuma, e um mon
real com IV 22 não tinha linha na tabela.

### 3.5 Matriz de variantes

Os três pares do §3.2 são simétricos — mesma fórmula, mesmo estatuto — e **os três juntos formam
o perfil de um mon**. Isto vale igualmente para o atacante e para o defensor: o perfil do teu mon
inclui o par `(HP, Speed)` e o par defensivo, não só o ofensivo.

```
perfil = (variante de Atk/SpA) x (variante de Def/SpD) x (variante de HP/Speed)
       =        3              x           3           x           3          = 27
```

O atacante precisa dos três pares porque os três entram no resultado: o ofensivo decide o dano
que dá, o defensivo e o HP decidem se sobrevive, o Speed decide se ataca primeiro.

| | Cardinalidade |
|---|---|
| perfis do atacante | 27 |
| bandas de IV do atacante | 3 |
| perfis do defensor | 27 |
| **células por par (atacante, defensor)** | **2 187** |

Multiplicado pelos 9 checkpoints do §3.3.

**Custo da camada 0** (agregado sobre o pool, ~386 chaves por lado):

```
linhas de atacante : 386 x 27 perfis x 3 IV  =  31 266
células de defensor: 386 x 27 perfis         =  10 422
avaliações totais  : 31 266 x 10 422         =  3.3 x 10^8
```

3.3x10^8 operações aritméticas triviais: **~30 s vetorizado (numpy), ~6 min em loops de Python**.
É um batch offline perfeitamente viável, mas **tem de ser vetorizado** — é a diferença entre
correr durante o pequeno-almoço e não correr de todo quando se lhe juntarem os movesets.

### 3.5b Moves e abilities

**Moves.** Importam-se todos, com dois filtros de exclusão:

- **Setup moves** (Swords Dance, Calm Mind, Dragon Dance, Agility, ...) — fora.
- **OHKO moves** (Fissure, Horn Drill, Guillotine, Sheer Cold) — fora.

Contagem real do pool de Gen 3 (moves 1-354, via veekun/pokedex):

| | Nº |
|---|---|
| Total de moves em Gen 3 | 354 |
| Status (sem dano) | 102 |
| Com dano | 252 |
| Com valor de `power` definido | **217** |

**O BP é O parâmetro de score. O efeito secundário conta como *upside*.**

O valor do upside **não é uma constante do move — depende do perfil**. É a mesma lógica dos 27
perfis: o mesmo efeito vale coisas diferentes em mons diferentes.

| Situação | Valor do upside |
|---|---|
| Thunderbolt num Snorlax special, bulky e lento | **alto** — a paralisia converte-o num bulky que passa a atacar primeiro |
| Flame Wheel num mon já rápido, a ganhar speed | **nulo** — não altera nada que já não tivesse |

Logo o upside avalia-se contra `(efeito, perfil do atacante, perfil do defensor)`, e entra
naturalmente na matriz do §3.5 em vez de ser uma tabela à parte.

**Quantificação: 3 cenários por moveset**, e aproximar a partir deles o valor esperado:

| Cenário | Efeito secundário |
|---|---|
| pior caso | **nunca** ativa |
| melhor caso | ativa **sempre** |
| esperado | ativa à **probabilidade real** do move |

Os dois extremos são as balizas, o terceiro é a estimativa. A saída é um *range*, não um número
— coerente com o modelo de solver do §1.2: um move de 30% de freeze lê-se de forma diferente de
um fiável, mesmo que o valor esperado calhe igual. Custo: **x3** sobre a avaliação de moveset.

**Abilities — entram na geração do perfil, não no fim.** Cada combinação de perfil e ability é
uma **entrada distinta** na tabela: `Snorlax / bulky physical / ability 1`, depois
`Snorlax / bulky physical / ability 2`, e assim por diante.

Não podem ser um modificador aplicado ao score no fim, porque muitas alteram o *input* do
cálculo:

| Ability | Onde entra |
|---|---|
| Truant | age em metade dos turnos — **obsoleta o mon por completo** |
| Wonder Guard | só leva dano super-efetivo — inverte a análise defensiva |
| Levitate | imunidade a GROUND — **altera o type chart daquele mon** |
| Huge Power | duplica o Atk — **altera o par ofensivo** |

**As abilities são totalmente randomizadas** — não são os 2 slots vanilla da espécie. O eixo é
portanto sobre **todas** as abilities de Gen 3.

**Banidas pelo ruleset: Huge Power, Pure Power e Wonder Guard.** Restam **73 de 76**. Isto é uma
simplificação real e não um detalhe: eram as três que obrigavam a casos especiais no motor —
Huge/Pure Power duplicavam o par ofensivo, Wonder Guard invertia toda a análise defensiva.
Nenhuma precisa de ser modelada.

**Agrupar por equivalência é obrigatório, não opcional:**

| Hipótese | Entradas/espécie | Camada 0 (x3 cenários) |
|---|---|---|
| as 73 disponíveis, individuais | 1 971 | **145 h** |
| ~30 individuais + 1 classe residual | 837 | 26 h |
| ~15 individuais + 1 classe residual | 432 | **7 h** |

Esboço de classes (**a verificar contra a lista real**, foi montado de memória):

| Classe | Onde entra no pipeline | Exemplos |
|---|---|---|
| altera o type chart | antes do cálculo de efetividade | Levitate, Flash Fire, Water/Volt Absorb, Lightning Rod, Thick Fat |
| altera stats efetivos | antes do cálculo de dano | Intimidate, Guts, Speed Boost, Marvel Scale, Overgrow/Blaze/Torrent/Swarm |
| **altera o upside** | dentro do modelo de efeito secundário | Serene Grace (dobra a probabilidade); Immunity, Limber, Insomnia, Water Veil, Own Tempo, Vital Spirit (anulam o efeito) |
| altera turnos | multiplica o output | Truant |
| meteorologia | condicional | Drizzle, Drought, Sand Stream, Chlorophyll, Swift Swim |
| contacto / passivo | dano residual | Static, Poison Point, Flame Body, Rough Skin, Effect Spore |
| sem efeito material | não entra | Illuminate, Run Away, Honey Gather, Pickup, ... |

Duas notas que caem deste esboço:

- **Sturdy torna-se no-op.** Em Gen 3 só bloqueia OHKO moves, e esses estão excluídos do pool
  (§3.5b). Vai para a classe residual.
- **A classe "altera o upside" não é independente do modelo de efeitos secundários.** Serene Grace
  dobra a probabilidade do cenário "esperado"; as abilities de imunidade a status anulam o upside
  de moves que dependem dele. Os dois sistemas têm de ser calculados juntos, não em sequência.

### 3.6 Score — desfecho da batalha, por distribuições

**A métrica não é "quanto dano dou", é "ganho a troca".** Percentagem de dano não chega: a
paralisia e o flinch não alteram o dano de um golpe nenhum, logo seriam invisíveis, e o upside
(§3.5b) deixaria de ser calculável.

```
turnos para eu derrubar o defensor  = HP_def / dano_meu_por_turno
turnos para ele me derrubar         = HP_meu / dano_dele_por_turno
quem ataca primeiro                 = comparacao de Speed
```

Os efeitos entram sozinhos: o flinch tira-lhe um turno, a paralisia corta-lhe a Speed a 1/4 e
falha 25% dos turnos, o burn corta-lhe o Atk a metade, o freeze tira-o do combate.

#### Resolução: analítica com distribuições, não valor esperado nem Monte Carlo

O dano em Gen 3 tem **16 rolls de 85% a 100%**, e o que interessa é um limiar ("mata em 2 ou em
3"), não uma média. O valor esperado erra grosseiramente nesse limiar:

| Dano médio | Valor esperado diz | P(2HKO) real |
|---|---|---|
| 50.0% do HP | 2HKO | **0.4%** |
| 53.0% | 2HKO | 30.5% |
| 55.0% | 2HKO | 69.5% |

Monte Carlo acertaria, mas o custo escala com N e o erro com `1/sqrt(N)`: N=25 dá ±10 pp (não
distingue um matchup de 45% de um de 55%), e N=1000 põe a camada 0 em 170 dias.

**Solução adotada:** a distribuição dos 16 rolls é sempre a mesma, e `P(KO em n golpes)` depende
de um único escalar, `HP / dano_médio`. Calcula-se **uma tabela, uma vez**, e depois é um lookup
— o mesmo custo do valor esperado, com a exatidão do Monte Carlo. Os efeitos de status são
cadeias de Markov pequenas, também com solução fechada.

Implementado em `mon/damage.py` e **medido**: a referência em Python puro faz 2.4x10^5/s, a forma
vetorizada em numpy faz **8.0x10^7/s**, com zero divergências entre as duas. Confirma o débito
assumido no §3.7.

Monte Carlo fica reservado para consultas pontuais das camadas 2-4, onde um matchup isolado
suporta 10 000 simulações em meio segundo.

> **O dano trunca-se golpe a golpe, não na soma.** Cada golpe causa `floor(base * roll / 100)`.
> Isto derruba a propriedade em que esta secção se apoiava: a distribuição do dano acumulado
> **não** depende só de `hp / base_damage`, depende do `base_damage`. A tabela única pré-calculada
> passa a ser uma tabela **por `base_damage`**, em cache (`_totals`). O custo continua baixo
> porque o número de valores distintos de `base_damage` numa run é pequeno, mas a afirmação
> "uma tabela serve tudo" era falsa. Ver §5.

> **O bug de arredondamento no limiar foi resolvido**: a referência conta em aritmética inteira
> sobre os rolls, sem `ceil`. A forma vetorizada usa `ceil` mas foi verificada contra a referência
> em 9 fronteiras exatas, sem divergências. Há um teste de regressão para o caso `hp=85, dano=100`.

Fórmula de stat (Gen 3+):

```
HP     = floor((2*Base + IV + floor(EV/4)) * Nivel / 100) + Nivel + 10
outros = floor((2*Base + IV + floor(EV/4)) * Nivel / 100) + 5      # nature neutra
```

### 3.6b Terceira escalada da métrica: sobreviver à dungeon

A métrica já escalou duas vezes: **% de dano → ganhar a troca**. A regra das dungeons
força a terceira: **sobreviver à sequência**.

Dentro de uma dungeon não há cura, não há recarga de PP, e lutar com mons selvagens é
contra as regras. HP e PP deixam de ser estado de uma batalha e passam a ser **orçamentos
que atravessam várias batalhas**. Isso muda o valor dos moves de forma que o motor da
troca não consegue ver:

- **O PP é dano total, não dano por golpe.** `BP × PP` é o teto de dano que um move entrega
  antes de secar. O extrasensory (80 BP × 30 PP = 2400) é o melhor move incondicional do
  pool acima de 80 BP, e é por causa do PP, não do BP.
- **O dreno é a única cura.** absorb, mega-drain, giga-drain, leech-life e dream-eater curam
  50% do dano feito. Um giga-drain a recuperar 40% do HP num mon tanky pode valer mais que
  um move de 120 BP, porque o que está em causa é chegar ao fim da dungeon, não ganhar
  aquela troca. (O leaf storm não entra na comparação — **é um move de Gen 4**, não existe
  no pool de Gen 3.)
- **O custo de um status aplicado a mim é permanente.** Fora da dungeon um burn passa; dentro,
  consome 1/8 do HP por turno de um orçamento que não se repõe. É o que mata o Guts.

- **A condição de um move é turnos, e não se desconta do BP** (`conditional.py`). Um BP por
  turno seria errado: no turno morto **o adversário ataca de graça**, e às vezes o dobro do BP
  corta um golpe ao número de golpes necessários e o turno morto sai grátis. Qual dos dois
  acontece depende do HP do alvo. Medido, com 150 de dano contra o mesmo adversário:

  | | Sobrevivência | HP médio no fim |
  |---|---|---|
  | bate todos os turnos | 1.000 | **98.9** |
  | um turno morto por golpe | 1.000 | **57.6** |

  Mesmo dano, mesma troca ganha, **41 HP a menos**. É isto que um BP/turno apagava. E no mesmo
  motor, 150 BP a cada dois turnos **bate** um move incondicional de 75: o dobro do BP corta um
  golpe. Não há métrica escalar que apanhe as duas coisas — só o turno a turno.
- O `focus-punch` tem prioridade −3 e quebra com qualquer dano, logo **só sai nos turnos em que
  o adversário não age**: `action_chance = 1 − them.action_chance`. Zero contra um adversário
  saudável; 0.214 contra um paralisado, onde um extrasensory dá 0.965.

#### O orçamento: só o caminho obrigatório

As secções grandes sem cura são a S.S. Anne, o Rocket Hideout, a Pokémon Tower, o Silph Co e
os ginásios. Conta-se **só os treinadores necessários para progredir** — todos os outros são
opcionais, e o trade-off de os evitar é chegar mais fraco. Logo **a tabela de níveis do §3.3 é
o teto, não o piso**: uma run que evita tudo chega a cada checkpoint abaixo dela.

| Secção | Obrigatórias | Caminho |
|---|---|---|
| S.S. Anne | 1 | o rival na passarela |
| Rocket Hideout | 3 | o grunt da Lift Key, 1 nos spinners, o Giovanni |
| Pokémon Tower | 4 | o rival no 2F e os 3 grunts do 7F |
| Silph Co | 4 | o rival e o Giovanni no 11F, mais 2 forçados pelos warps |
| ginásios | 1 | só o líder (exceto Saffron 3 e Viridian 2, pelos warps/spinners) |

Os números estão em `dungeons.py` e são **estimativa de FRLG por verificar em jogo**.

#### O motor: distribuição de estados, não valor esperado

`sequence.py`. Uma troca deixa de devolver um número e passa a devolver **a distribuição dos
estados em que o mon ficou**. O estado é o que atravessa os embates:

```
State(hp, pp, owed)      hp e pp nao se repoem; owed = turnos que devo antes de voltar a atacar
```

O `owed` é o que liga tudo: um mon que mata com um move de dois turnos entra no embate seguinte
a dever um turno, exatamente como o Truant. Um que mate com double-edge entra com o recuo já
descontado. O trainer de 6 mons é a mesma função aplicada seis vezes, com a distribuição de
saída de um embate a ser a de entrada do seguinte.

**Valor esperado não serve**: 50% de chegar inteiro e 50% de chegar morto não é "metade do HP".

O que impede a explosão combinatória é o **agrupamento**: no fim de cada troca o HP é
arredondado a uma grelha de `BUCKETS = 20` níveis, e dois caminhos que acabam quase no mesmo HP
colapsam num estado só. **Dentro da batalha a conta é exacta** — arredondar golpe a golpe
acumulava erro e falseava o resultado (§4). Medido, uma secção contra um adversário que
sobrevive a vários golpes:

| Mons | Estados | Tempo | Sobrevivência | HP médio |
|---|---|---|---|---|
| 1 | 4 | 77 ms | 1.000 | 329 |
| 2 | 9 | 0.3 s | 1.000 | 258 |
| 3 | 16 | 0.7 s | 1.000 | 187 |
| 4 | 25 | 1.3 s | 0.999 | 115 |
| 6 | 6 | 0.9 s | **0.200** | 28 |

**O número de estados fica na ordem das dezenas** e no fim desce, porque os ramos maus morrem e
saem da distribuição. É isto que torna uma batalha de 6 mons tratável. O tempo é dominado por
reavaliar a troca para cada estado de entrada; o `_rolls` em cache cortou-o para um terço
(medido), e é aqui que se mexe se a carga do §3.7 precisar.

Uma secção contra adversários do mesmo calibre e sem cura colapsa depressa: 3 mons ainda passam,
ao 5º a sobrevivência é 11%. **O modelo diz que a resposta não é o moveset, é o nível** — e é
exactamente o trade-off de evitar os treinadores opcionais.

### 3.6c O moveset não se escolhe: calha

A selecção gulosa respondia a "qual o melhor moveset que este mon poderia ter". O jogo nunca faz
essa pergunta: os moves são **aleatórios**, e o mon conhece N (9 no Brock, 23 no Elite 4, do
calendário mais os TMs a 50%). Pontuar o melhor de 194 era pontuar um moveset que nunca lhe sai.

O modelo é o **melhor de N aleatórios, por estatística de ordem** (`orderstat.py`): se os N são
um subconjunto uniforme dos M do pool, a probabilidade de o k-ésimo pior ser o melhor dos N é
`C(k, N-1) / C(M, N)`. O valor esperado do melhor é uma soma pesada dos scores **ordenados**, com
pesos que só dependem de (M, N). Sem amostragem e sem ruído.

O subconjunto é o mesmo para todos os defensores, mas isso **não altera o valor esperado do
agregado**: a média sobre defensores é linear, logo trocar a ordem das duas é exacto. Muda a
variância entre runs, não a média — e a variância é outra pergunta.

Sai mais barato e responde melhor: **21 h** contra as 232 h do guloso sobre o pool inteiro.
O HP restante viaja com o move escolhido pelo win, não com o seu próprio máximo — escolhe-se o
move pelo que ganha, não pelo que poupa.

### 3.7 As duas cargas de trabalho

**Camada 0 (batch, uma vez por ruleset)** — 24 867 linhas de atacante x 8 910 células de defensor
x 200 movesets (guloso) x 3 cenários de upside x 9 checkpoints = **1.3x10^12 avaliações**.

| Débito do numpy | Tempo |
|---|---|
| **10^7/s — MEDIDO** | **37 h** |
| 10^8/s (era o palpite otimista) | 3.7 h |

**Medido com protótipo, não estimado**: 1.0x10^7 avaliações/s, estável de 10^5 a 10^7 chamadas.
O palpite de 10^8 estava uma ordem de grandeza acima. A camada 0 é **37 h**, não 3.7 h.

Em Python puro o mesmo caminho dá 33 mil/s — 300x menos. **A vectorização não é otimização, é
a condição de isto correr**: sem ela a camada 0 leva 450 dias. A tabela de KO indexada por
`(base_damage, golpes, hp)` constrói-se em 0.1 s e ocupa 8 MB, e confere com o `damage.py` —
a "tabela por `base_damage`" do §5 não custa nada, ao contrário do que eu temia.

**Consulta (interativa)** — o custo depende do que já sabes do mon:

| O que sabes | Avaliações | Tempo |
|---|---|---|
| nada (pré-run: "se me sair um Snorlax...") | — | **0 s: é lookup na tabela core** |
| stats lidos no tracker | 4.8x10^7 | 0.5 s |
| stats + moveset | 2.4x10^5 | instantâneo |

A pergunta pré-run **não se calcula** — já está na tabela. É essa a razão de ser da camada 0: o
caso caro corre offline uma vez, e tudo o que é interativo colapsa para um lookup ou meio segundo.

#### A chave da partição é `(checkpoint,)`

9 checkpoints x 20 blocos de espécies = **180 partições**, ~9 min cada: **27 h**. A curva de
crescimento não entra, porque o randomizer a padroniza.

A chave do `Partition` é uma **tupla** e não um campo só. A curva entrou como segunda dimensão e
saiu na mensagem seguinte sem invalidar nada: é para isso que a chave é o caminho no disco.

A tabela continua a discriminar mesmo onde os números são todos baixos. No Brock, com o jogador
a nível 9 contra um pool a 18, o `win` vai de 0.013 a 0.120 — 10x entre o melhor e o pior perfil,
e a ordenação é a esperada: `def_tank` + `bulky` + IV alto no topo, `fast` + `spdef_tank` + IV
baixo no fundo. A nível 9 contra 18 a Speed não vale nada porque não se sobrevive ao primeiro
golpe; é o tipo de conclusão que a tabela existe para dar.

#### Requisito: a camada 0 corre aos pedaços

As 37 h não se correm de uma vez. **O batch tem de ser retomável**: 5 h hoje, nenhuma amanhã,
20 no dia seguinte. Isso não é uma opção de conveniência, é uma restrição de desenho:

- o espaço tem de estar **particionado** por uma chave estável e enumerável — o checkpoint é a
  partição natural (9 fatias), e dentro dele a espécie do atacante;
- cada partição **escreve o seu resultado ao acabar**, e um arranque novo salta as que já existem;
- nada de estado global entre partições — o que já está feito não pode mudar de valor por se
  retomar mais tarde, ou a tabela fica inconsistente consigo mesma.

Em compensação sai de graça o paralelismo por partição e a possibilidade de recalcular só um
checkpoint quando a tabela de níveis do §3.3 for calibrada em jogo.

### 3.8b O `win` satura no meio da run; o `hp_left` é que ordena

Medido numa partição real de cada ponta:

| Checkpoint | Jogador vs adversário | `win` (min–max, mediana) | `hp_left` (min–max) |
|---|---|---|---|
| Brock | 19 vs 18 | 0.782 – 0.991 (0.923) | 0.421 – 0.610 |
| Erika | 58 vs 36 | **1.000 – 1.000 (1.000)** | 0.752 – 0.903 |
| Elite 4 | 86 vs 80 | 0.929 – 1.000 (0.986) | 0.464 – 0.712 |

Com +22 níveis de vantagem **não se perde**, e o `win` deixa de distinguir: na Erika as 162
linhas dão todas 1.000. Não é um defeito do cálculo, é o modelo a dizer a verdade — a pergunta
deixa de ser "ganho?" e passa a ser "a que custo?". É o `hp_left` que carrega o sinal, e isso
justifica a posteriori ter pago as 3 h por ele.

Consequência para os tiers: **o critério tem de mudar com o checkpoint.** No Brock e no Elite 4
ordena-se por `win`; nos sete do meio, por `hp_left`. Uma tier-list única sobre o `win` dava
sete checkpoints em que todos os mons são S.

### 3.8 Arquétipos e tiers

Definidos por **percentis sobre o pool do jogo**, não por valores absolutos:

| Banda | Tier |
|---|---|
| >= ~90º percentil | S |
| >= ~65º percentil | A |
| abaixo | resto |

Tiers são **case-specific**: o percentil é calculado dentro do arquétipo, por isso há vários
caminhos para S (um glass cannon que OHKO 90% do pool e um bulky que faz 80-90% a 100% do pool
são ambos S, por critérios diferentes).

Arquétipos:

- **Rápido:** Speed no ~90º percentil do pool, o que cai perto de **base 100**.
  (A formulação anterior — "> 100 ao nível 100" — equivalia a base > 32, porque o stat ao nível
  100 com IV 31/EV 0/neutra é `2 x Base + 36`. Apanhava quase tudo. Substituída pelo percentil.)
  Funciona na camada 0 porque `(HP, Speed)` é um par com skew próprio (§3.2): o perfil
  Speed-heavy dá `Speed = BST/4`, distinguível do híbrido `BST/6` e do HP-heavy `BST/12`.
- **Glass cannon:** leva OHKO de um move neutro (não super-efetivo) de 80-90 BP.
  Falta definir o **atacante de referência** (nível e Atk/SpA) — sem isso o teste não é calculável.
- **Muito durável**, **dano alto mas lento**: por definir, mesma lógica de percentis.

### 3.9 Impacto de um move

```
impacto(M) = score(melhor moveset que inclui M) - score(melhor moveset sem M)
```

Reformulação, sobre movesets reais, do que `addition.py` e `substitution.py` fazem hoje sobre
tipos abstratos. Os dois módulos sobrevivem conceptualmente, não em código.

### Diagrama alvo

```
   PokéAPI  -----------> +----------------------------------+
   (espécies, tipos,     | mons (id, nome, tipos, base stats)|
    stats, learnsets)    | learnsets (mon x jogo x move)     |  camada de dados
                         | moves (tipo, BP, categoria, acc)  |
   tabelas manuais ----->| games (dex, chart, regra de split)|
   (chart Gen2-5,        | kaizo (checkpoints, boost,        |
    níveis, regras)      |        forced-evo, bans BST)      |
                         +----------------------------------+
                                        |
                                        v
                         +----------------------------------+
                         | domínio (puro, sem I/O):          |
                         |  stats @ nível (banda IV, EV0)    |
                         |  skew soma-zero (roll Kaizo)      |
                         |  dano em % de HP (chart + STAB)   |
                         |  seleção gulosa de moveset        |
                         +----------------------------------+
                                        |
                         +--------------+---------------+
                         v                              v
               +--------------------+        +----------------------+
               | arquétipo           |        | 27 células           |
               | (percentis do pool) |        | x 13 checkpoints     |
               +--------------------+        +----------------------+
                         +--------------+---------------+
                                        v
                         +----------------------------------+
                         | tier (P90 / P65) + impacto/move   |
                         +----------------------------------+
                                        |
                         +--------------+---------------+
                         v                              v
                lookup interativo               tier-list batch
                (1 mon, rápido)                 (pool todo, offline)
                         +--------------+---------------+
                                        v
                                   CLI  /  GUI
```

---

## 4. Bugs que apareceram e foram corrigidos


**`damage.probability_of_ko` somava os rolls antes de aplicar o dano.** Em Gen 3 cada golpe causa
`floor(base * roll / 100)` e trunca **sozinho**; o código somava os 16 rolls, aplicava
`base/100` uma vez e não truncava nada. Em 3 golpes de base 36 contra 100 de HP dava 0.500
onde o valor real é 0.367 — **13 pp** — e o erro propagava-se a tudo o que corre por cima:
`win_probability`, o swing das habilidades e a tabela de swing dos status (todos os valores
estavam 2 a 8 pp abaixo).

Só apareceu porque passou a haver **dois** motores: o `sequence.py`, que anda turno a turno,
discordava do `battle.py` em 9 pp no mesmo matchup. Uma terceira implementação independente
(convolução dos danos truncados) deu exactamente o valor do `sequence.py`. Nenhum teste
unitário o apanhava — os valores esperados tinham sido tirados do próprio código.

Consequência de desenho, não só de aritmética: a distribuição do dano acumulado **deixa de
depender só de `hp / base_damage`** e passa a depender do `base_damage`, o que mata a tabela
única pré-calculada do §3.6. Fica uma tabela por `base_damage`, em cache.

**O agrupamento de HP não pode acontecer dentro de uma batalha.** A grelha de 20 níveis era
aplicada golpe a golpe e o arredondamento acumulava: numa secção de 6 mons a sobrevivência
dava 0.0006 em vez de 0.1996. O agrupamento passou a ser aplicado **só no fim de cada troca**,
que é onde serve de facto para comprimir o estado. Dentro da batalha a conta é exacta.

---

## 5. Próximos passos

Nada aqui bloqueia o que está publicado: a camada 0 está calculada e a página serve-a. São os
pontos onde o modelo pode ficar melhor, e os sítios onde assumi um valor em vez de o medir.

**Precisam de dados ou de calibração em jogo:**

1. **As chances de efeito do `move_meta` são modernas** e não há `move_changelog` para elas, logo
   não há como as reverter para Gen 3 a partir dos dados. Ficam por verificar. Quinta instância
   da armadilha.
2. Calibração do `DUNGEON_SELF_STATUS = 0.25` e **verificação em jogo das contagens do
   `dungeons.py`** — são estimativa de FRLG, não dados medidos.
3. **Atacante de referência** para o teste de glass cannon (§3.8): nível e stats. Não bloqueia o
   cálculo, só a etiquetagem — decide-se melhor depois de ver a distribuição.
4. **Critério de S/A/B por arquétipo** além dos percentis (durável, dano alto e lento). Idem.
5. **Nível exato da forced-evo** (assumido ~30). Determina a partir de que checkpoint o pool
   encolhe para evoluções finais.

**Menores:**

6. **Limites por stat no randomizer** (mínimo/máximo por slot), se existirem. Afetariam a
   esperança de `BST/6` do §3.2.
7. Confirmar em jogo a tabela do §3.3, sobretudo o conjunto "obrigatório" — sai dos spinners e
   walkers do mapa, que é um sinal de movimento e não de obrigatoriedade.
8. Fonte dos dados da run nas camadas 2-4: input manual ou leitura do Ironmon Tracker. Não
   bloqueia — o modo por omissão é consulta sem input (§1.2).

**Resolvidas:**

- ~~Os tipos das espécies são randomizados?~~ **Não.** Mantêm-se. A análise de type chart é segura.
- ~~A fórmula do skew produz stats negativos?~~ **Não.** O residual é `min/2` por construção (§3.2).
- ~~Base do skew na camada 0?~~ **Neutro por `BST/6`** (§3.2).
- ~~Granularidade dos buckets de BST?~~ **Sem buckets** — o espaço ocupado é <= 386, indexa-se
  pelo BST exato (§1.2).
- ~~Bans de BST em Gen 3?~~ **551, verificado na aquisição**; evolução pode ultrapassar (§1).
- ~~HP e Speed ficam de fora do skew?~~ **Não.** `(HP, Speed)` é o terceiro par, mesma fórmula (§3.2).
- ~~Quantas batalhas por dungeon?~~ **Só o caminho obrigatório** (§3.6b). O resto é opcional e
  o trade-off é chegar a um nível mais baixo — a tabela do §3.3 é o teto, não o piso.
- ~~Os moves de cura pura voltam ao pool?~~ **Não.** Ficam fora (GRUPOS.md B2b). O leech-seed
  fica dentro pelo dano por turno, não pela cura.
- ~~Os moves condicionais saem do pool?~~ **Não** — entram com o custo da condição modelado como
  turnos perdidos (GRUPOS.md B4, §3.6b).
- ~~Níveis por checkpoint?~~ **Medidos** a partir do FRLGIronmonMap, por curva de crescimento
  (§3.3). Os níveis do mapa já são os do Kaizo; a estimativa `vanilla x 1.5` fica validada para
  o adversário.
- ~~`hidden-power`?~~ **Fora do pool.** O BP depende de IVs que não se leem antes da run.
- ~~Estratégia de selecção de moveset?~~ **Gulosa** (4 slots x N candidatos). É a única que torna
  o problema tratável; agrupar por cima corta mais.
- ~~Valor representativo de cada banda de IV e o intervalo 20-24?~~ **5 / 15 / 27**, com a banda
  alta redefinida como `20+` (§3.4). O buraco fecha-se.
- ~~Classes de equivalência das abilities?~~ **Não há lista para fixar.** A opção (c) colapsou-a:
  4 habilidades têm mecânica modelada, as outras valem zero por decisão (§2.1).
- ~~Mantêm-se os dois motores?~~ **Sim, os dois.** O `battle.py` é analítico e rápido e serve o
  `abilities.py` e as medições de swing; o `sequence.py` dá o estado e serve as secções. A
  condição para isto ser indiferente é concordarem, e **não concordavam** — havia 9 pp de erro
  no `battle.py` (§4). Há agora um teste de concordância sobre 16 matchups nos dois sentidos de
  Speed, a 1e-9.
- ~~Como atravessa o HP uma troca: valor esperado ou distribuição?~~ **Distribuição de estados
  agrupados** (§3.6b). O valor esperado dilui o que interessa; o agrupamento por grelha de HP
  mantém o número de estados em ~300 e torna um trainer de 6 mons tratável.
- ~~Um move de dois turnos vale metade do BP por turno?~~ **Não.** A condição é turnos, não BP,
  e resolve-se turno a turno (§3.6b, GRUPOS.md B4).
- ~~Introdução de dados é obrigatória?~~ **Não** — consulta é o modo por omissão (§1.2).

---

### Publicacao

A camada 0 sao 35 MB de JSON e 281 394 celulas. Para o browser empacota-se em **1.5 MB**: os dois
numeros de cada celula cabem em `uint16` com 4 casas decimais, e a chave nao viaja -- deriva-se da
posicao no array. A ordem do indice vai no proprio payload, para a pagina nao a adivinhar.

A pagina e **um ficheiro so**, com dados e motor la dentro: abre-se com duplo clique e nao precisa
de servidor. Vive em `docs/index.html`, que e de onde o **GitHub Pages** a serve em
<https://goncalofgoncalves.github.io/IronMon-Solver/>. O `data/` fica fora do git.

**O `engine.js` e um port de seis modulos para JavaScript**, para responder a pergunta que a
tabela nao responde: um moveset *concreto*, calculado na hora contra os mesmos 10 422 adversarios,
em menos de 20 ms. Ha teste que o corre em node e compara com o kernel Python a 1e-9 -- foi a
terceira vez neste projeto que dois caminhos para a mesma resposta apanharam bugs, e desta vez
logo dois: `2 * level // 5` nao e `2 * floor(level/5)`, e o Python arredonda meios para par
(`round(132.5) == 132`), o que divergia em todo o BST que caisse num `.5`.

## 6. Referências

- [FRLG IronMON Map](https://kelseyyoung.github.io/FRLGIronmonMap/) — mapa interativo com dados de treinadores
- [Official IronMon Randomizer Settings](https://gist.github.com/UTDZac/a147c497424dfbd537d8c4b0c22b5621) — settings strings oficiais
- [Kaizo IronMON+ rules](https://github.com/Corvimae/kaizo-ironmon-plus/blob/main/rules.md) — ruleset detalhado
- [FRLG Gym Leaders & Elite Four](https://pokemondb.net/firered-leafgreen/gymleaders-elitefour) — níveis vanilla, base da tabela §3.3
