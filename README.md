# IronMon Solver

Uma tabela de referência para jogar **Kaizo IronMON em Pokémon FireRed**: para cada espécie, com
cada distribuição de stats que o randomizer lhe pode dar, diz quão bem se sai em cada um dos nove
checkpoints da run.

**[Abrir a página →](https://goncalofgoncalves.github.io/IronMon-Solver/)**

Não é uma tier-list de espécies. Em Kaizo os base stats são redistribuídos ao acaso preservando o
BST, por isso "Snorlax" não é uma linha — são 27, uma por perfil de stats, vezes três bandas de IV.
A tabela tem 281 394 células e levou 40 h a calcular.

---

## O que a página mostra

**Ranking** — os melhores mons num checkpoint, com filtros de BST (550 é o limite do ruleset),
banda de IV e perfil de stats.

**O teu mon** — escolhes espécie, perfil e IV e vês a linha nos nove checkpoints.

**Moveset concreto** — a tabela assume moves aleatórios, que é o que o Kaizo dá. Este painel
calcula um moveset específico na hora, contra os mesmos 10 422 adversários: ~74 ms a trocar um
slot, ~395 ms a trocar de mon. Serve para perguntar "e se ele tiver giga-drain em vez de surf".

**Testar um mon** — escolhes a espécie, distribuis o BST pelos seis stats com sliders, pões uma
ability, e carregas em **Calcular**. O randomizer não dá 27 distribuições: dá uma qualquer que
preserva o BST, e os 27 perfis são a grelha do modelo, não o que sai no jogo. ~450 ms para os
nove checkpoints, e nada corre até pedires.

A coluna **Mons** é o tamanho da fila sem cura de cada secção — 7 no Brock, 30 no Elite 4 — e é
o que decide se uma ability como o Guts vale algo: o burn tira 1/8 do HP por turno, logo numa
fila de 30 o status é uma sentença e não uma vantagem.

**O que me mata** — por tipo, os moves ordenados por dano até ao degrau onde a morte deixa de
ser certa, com um cursor para perguntar a HP ferido em vez de a HP cheio.

**Piores matchups** — os 15 adversários onde o teu moveset se sai pior, de 10 422. A média da
célula não distingue um mon sólido de um mon com um buraco.

As três colunas:

- **Vitória** — probabilidade de ganhar a troca, em média sobre os 386 adversários ao nível daquele
  checkpoint.
- **HP que sobra** — a fracção do máximo com que ficas quando ganhas. Numa dungeon não há cura nem
  recarga de PP, por isso o custo de ganhar importa tanto como ganhar.
- **Risco** — a quota de sorteios em que o adversário tem, nos seus 4 slots, um move que te mata de
  um golpe. É o número que o HP não vê: o HP é condicional a ganhares, por isso *sobe* quando o
  risco passa a ser binário — as vitórias que te restam são as folgadas.

O risco faz pico nos dois sítios onde a vantagem de nível é menor: 0,107 no Brock e 0,113 no
Elite 4, contra 0,010 no Surge.

---

## Como o modelo funciona

| | |
|---|---|
| **O que sobrevive à randomização** | tipos, BST e o calendário de aprendizagem. Os stats não. |
| **Perfis de stats** | três pares simétricos — (Atk, SpA), (Def, SpD), (HP, Speed) — cada um híbrido ou inclinado para um lado. 27 combinações, todas a somar exactamente o BST. |
| **Níveis** | simulados a partir dos 345 treinadores do mapa de FRLG, com a fórmula de EXP de Gen 3 e os exp yields da disassembly do jogo. Calibrados contra runs reais. |
| **Dano** | distribuição exacta dos 16 rolls de Gen 3, com cada golpe truncado sozinho. Nada de valores esperados: a média diz "2HKO" onde a probabilidade real é 0.4%. |
| **Dano recebido** | o adversário tem 4 moves sorteados dos mesmos 194 e escolhe à sorte entre os que matam de um; o excesso é desperdiçado. Daí duas situações distinguíveis, e a troca resolve-se duas vezes. |
| **Moveset** | não se escolhe, calha. O valor é o esperado do melhor de N moves aleatórios, por estatística de ordem. |
| **Habilidades** | só as que têm mecânica modelada produzem swing; as outras valem zero em vez de valerem um palpite. |

O [CONTEXT.md](CONTEXT.md) tem a especificação completa, as decisões tomadas e os bugs que
apareceram pelo caminho. O [GRUPOS.md](GRUPOS.md) tem a composição dos grupos de moves e
habilidades.

---

## Correr

Precisa de Python 3.12 e numpy.

```bash
python -m mon.run --status      # quanto falta calcular
python -m mon.run               # a camada 0; Ctrl+C a qualquer momento
python -m mon.viewer            # reconstrói docs/index.html
python -m pytest tests/         # 293 testes
```

O batch leva cerca de 27 h e corre aos pedaços: cada partição escreve ao acabar e uma corrida nova
salta as que já estão no disco. O `Ctrl+C` nunca perde mais do que os ~9 minutos da partição a meio.

Os resultados ficam em `data/camada0/`, que está fora do git — são 35 MB. O que entra é a página
construída, em `docs/`.

---

## Estrutura

```
mon/             o solver
viewer/          a página: template + motor de cálculo ao vivo
docs/            a página construída, de onde o GitHub Pages a serve
tests/           293 testes
CONTEXT.md       especificação, decisões e bugs encontrados
GRUPOS.md        composição dos grupos de moves e habilidades
```

Dentro do `mon/`:

```
  skew.py        27 perfis de stats a partir do BST
  stats.py       fórmula de stat de Gen 3
  typechart.py   chart de Gen 2-5, validado contra dados independentes
  damage.py      distribuição exacta dos rolls de dano
  vector.py      o mesmo cálculo vectorizado: 1.5x10^7 avaliações/s
  battle.py      desfecho de uma troca, analítico
  sequence.py    estados encadeados: HP e PP a atravessar vários embates
  moves.py       194 moves utilizáveis, com os valores de Gen 3
  abilities.py   aproveitamento de uma habilidade, como swing na troca
  upside.py      valor do efeito secundário, que depende do mon
  trainers.py    os 345 treinadores do mapa, por split
  levels.py      nível esperado em cada checkpoint
  score.py       o kernel
  breakpoints.py o que me mata, por tipo
  matchups.py    o ranking por defensor
  gauntlet.py    a sala inteira antes do lider
  stall.py       a parede do Shedinja, que se resolve a PP
  run.py         a camada 0, retomável
  viewer.py      constrói docs/index.html
```

O `engine.js` é um port para JavaScript de seis módulos Python. Há um teste que o corre em node e
compara com o kernel, porque dois caminhos a responder à mesma pergunta é como se apanharam dois
bugs neste projeto.

**Fontes de dados**: [veekun/pokedex](https://github.com/veekun/pokedex) para moves, tipos e curvas
de EXP; [pret/pokefirered](https://github.com/pret/pokefirered) para os exp yields de Gen 3, que o
veekun guarda com os valores modernos; [kelseyyoung/FRLGIronmonMap](https://github.com/kelseyyoung/FRLGIronmonMap)
para os treinadores.

---

## Licença

[MIT](LICENSE) — copyright (c) 2026 Gonçalo Faria Gonçalves.

Cobre o código deste repositório. Os dados do jogo que a página contém — nomes de espécies,
tipos, BSTs, nomes de moves, exp yields — são da Nintendo e da Game Freak, e a licença não os
abrange.
