# IronMon Solver

Uma tabela de referência para jogar **Kaizo IronMON em Pokémon FireRed**: para cada espécie, com
cada distribuição de stats que o randomizer lhe pode dar, diz quão bem se sai em cada um dos nove
checkpoints da run.

**[Abrir a página →](https://goncalofgoncalves.github.io/IronMon-Solver/)**

Não é uma tier-list de espécies. Em Kaizo os base stats são redistribuídos ao acaso preservando o
BST, por isso "Snorlax" não é uma linha — são 27, uma por perfil de stats, vezes três bandas de IV.
A tabela tem 281 394 células e levou 27 h a calcular.

---

## O que a página mostra

**Ranking** — os melhores mons num checkpoint, com filtros de BST (550 é o limite do ruleset),
banda de IV e perfil de stats.

**O teu mon** — escolhes espécie, perfil e IV e vês a linha nos nove checkpoints.

**Moveset concreto** — a tabela assume moves aleatórios, que é o que o Kaizo dá. Este painel
calcula um moveset específico na hora, contra os mesmos 10 422 adversários, em menos de 20 ms.
Serve para perguntar "e se ele tiver giga-drain em vez de surf".

As duas colunas:

- **Vitória** — probabilidade de ganhar a troca, em média sobre os 386 adversários ao nível daquele
  checkpoint.
- **HP que sobra** — a fracção do máximo com que ficas quando ganhas. Numa dungeon não há cura nem
  recarga de PP, por isso o custo de ganhar importa tanto como ganhar.

Com vantagem de nível a vitória satura — na Erika quase tudo dá 1.000 — e só o HP ordena. A página
ordena por vitória no Brock e no Elite 4, que são os dois checkpoints onde se perde, e por HP nos
outros sete.

---

## Como o modelo funciona

| | |
|---|---|
| **O que sobrevive à randomização** | tipos, BST e o calendário de aprendizagem. Os stats não. |
| **Perfis de stats** | três pares simétricos — (Atk, SpA), (Def, SpD), (HP, Speed) — cada um híbrido ou inclinado para um lado. 27 combinações, todas a somar exactamente o BST. |
| **Níveis** | simulados a partir dos 345 treinadores do mapa de FRLG, com a fórmula de EXP de Gen 3 e os exp yields da disassembly do jogo. Calibrados contra runs reais. |
| **Dano** | distribuição exacta dos 16 rolls de Gen 3, com cada golpe truncado sozinho. Nada de valores esperados: a média diz "2HKO" onde a probabilidade real é 0.4%. |
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
python -m pytest tests/         # 196 testes
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
tests/           196 testes
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
