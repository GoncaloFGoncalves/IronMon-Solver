# GRUPOS — proposta para aprovação

Composição completa de todos os agrupamentos do §6 do CONTEXT.md. Tudo extraído dos dados reais
do `veekun/pokedex` (Gen 3, moves 1-354, abilities de generation_id <= 3), não de memória.

Marca cada grupo com OK ou NÃO.

---

## A. Moves excluídos

### A1 — OHKO — 4 moves · `[ ]`

```
fissure   guillotine   horn-drill   sheer-cold
```

### A2 — Setup (status que sobe stats do próprio) — 21 moves · `[ ]`

```
acid-armor    agility       amnesia       barrier       bulk-up
calm-mind     charge        cosmic-power  defense-curl  double-team
dragon-dance  growth        harden        howl          iron-defense
meditate      minimize      sharpen       swords-dance  tail-glow
withdraw
```

Critério usado: move sem dano, alvo = próprio, com pelo menos uma subida de stat.

---

## B. Moves sem BP — DECIDIDO

### B1 — Causam dano sem BP fixo — 19 moves

| Decisão | Moves | Tratamento |
|---|---|---|
| **fora** | `counter`, `mirror-coat`, `reversal` | dependem de levar dano / estar com HP baixo |
| **BP médio** | `low-kick` **56.3**, `magnitude` **71.0** | low-kick: média sobre os 386 mons (mais pesados = mais BP, logo escala no late game); magnitude: valor esperado das 7 magnitudes |
| **dano fixo** | `dragon-rage` (40), `sonic-boom` (20) | o falloff sai sozinho da dimensão de checkpoint |
| **dano = nível** | `seismic-toss`, `night-shade` | escalam com o nível |

O falloff verificado sobre um defensor de BST 500, perfil híbrido:

| Move | Brock (lv20) | Erika (lv43) | Giovanni (lv75) | Blue (lv94) |
|---|---|---|---|---|
| dragon-rage | 58% | 29% | 17% | 14% |
| sonic-boom | 29% | 15% | 9% | 7% |
| seismic-toss / night-shade | 29% | 31% | 32% | 33% |

Confirma o modelo: o dano fixo cai de 58% para 14% do HP ao longo da run, e o dano-igual-ao-nível
mantém-se plano. **Nenhum dos dois precisa de tratamento especial** — a dimensão de checkpoint
já captura isto.

### B1b — DECIDIDO

**Dentro:** `super-fang` (50% do HP atual, escala sempre).
**Fora:** `beat-up`, `bide`, `endeavor`, `flail`, `present`, `psywave`, `spit-up`.

### B2 — Status puro — DECIDIDO

**Fora, exceto os que causam dano.** Razão: podem resolver um moveset que não tinha resposta
contra certos mons — pouco dano, mas deixa de ser zero.

**Dentro:** `will-o-wisp`, `toxic`, `poison-powder`

### B2b — DECIDIDO

**Dentro**, pelo mesmo critério (status que causa dano):

```
poison-gas   leech-seed   nightmare   curse   spikes
```

`leech-seed` é caso à parte: além do dano por turno, **cura**. Num formato de permadeath isso vale
mais do que o dano em si.

> **RESOLVIDO: não.** Os moves de cura pura (`recover`, `soft-boiled`, `moonlight`,
> `morning-sun`, `synthesis`, `milk-drink`, `rest`, `wish`) **ficam fora**. Já estavam fora
> pelo filtro de BP e continuam fora por decisão. O `leech-seed` fica dentro porque o dano
> por turno é o que o põe lá; a cura é bónus, não o critério.

### B4 — Moves com condição: entram, com o custo da condição · `[x]`

Não se excluem nem se tomam pelo BP nominal. A condição é modelada como **turnos perdidos**,
a mesma classe de problema que o Truant (`mon/conditional.py`, CONTEXT.md 3.6b):

| Família | Moves | Modelo |
|---|---|---|
| dois turnos por golpe | `hyper-beam` `blast-burn` `frenzy-plant` `hydro-cannon` `solar-beam` `razor-wind` `skull-bash` `sky-attack` `fly` `dig` `dive` `bounce` | um turno morto por golpe, resolvido turno a turno — **o BP não se desconta** |
| prioridade -3, quebra com dano | `focus-punch` | ataca sempre último e só sai nos turnos em que o adversário não age |

### B3 — Suicidio: em IronMON acaba a run — DECIDIDO, saem

O criterio do perish-song aplica-se a mais dois moves, e esses **tem BP**, por isso estao neste
momento dentro do grupo dos 193:

| Move | Tipo | BP |
|---|---|---|
| `self-destruct` | NORMAL | 200 |
| `explosion` | NORMAL | **250** |

Numa run normal seriam moves fortes. Em IronMON, **se o teu mon desmaia a run acaba** — logo o
valor real e negativo, nao 250. Devem sair pela mesma razao que o perish-song.

`memento` e `destiny-bond` ja estao fora por serem status.

## C. Upside — DECIDIDO: não há fórmula por família

O valor de um efeito secundário **é o swing que provoca na batalha** — a diferença entre o
desfecho com o efeito ativado e sem ele. Não é uma constante por família, e depende dos **dois**
mons.

O exemplo que fixa a regra, com Serene Grace:

| Atacante | Move | Valor do upside | Porquê |
|---|---|---|---|
| Snorlax físico, **rápido** | headbutt (flinch) | **alto** | flinch só funciona se atacares primeiro; Serene Grace leva os 30% a 60% |
| Snorlax special, ou **lento** | headbutt | **baixo** | o flinch quase nunca chega a contar |
| Snorlax **lento** | thunderbolt (paralisia) | **alto** | a paralisia converte-o em mais rápido — exatamente o que lhe faltava |
| Snorlax **rápido** | thunderbolt | **baixo** | já atacava primeiro; a paralisia não acrescenta |

Repara que o flinch e a paralisia têm valor **inverso** em relação à mesma variável (a tua Speed).
Nenhuma tabela de "paralisia vale X" apanharia isto.

**Consequência:** os 3 cenários do §3.5b já dão a resposta sem tabela nenhuma —
`upside = score(efeito sempre) - score(efeito nunca)`, ponderado pela probabilidade real. A
fórmula por família deixa de ser precisa.

### C1 — O score muda — DECIDIDO

O §3.6 define o score como **% de HP causada por dano**. Com essa métrica, **a paralisia e o
flinch são literalmente invisíveis**: nenhum dos dois altera o dano de um golpe. O swing acima
não é calculável.

Para o upside funcionar, o score tem de passar a modelar **a batalha ao longo de turnos**:

```
turnos para eu derrubar o defensor   = HP_def / dano_meu_por_turno
turnos para ele me derrubar          = HP_meu / dano_dele_por_turno
quem ataca primeiro                  = comparacao de Speed
```

Com isto, os efeitos entram naturalmente: o flinch tira-lhe um turno, a paralisia corta-lhe a
Speed a 1/4 e falha 25% dos turnos, o burn corta-lhe o Atk a metade, o freeze tira-o do combate.
Tudo sai do mesmo motor.

É a escalada de "quanto dano dou" para "ganho a troca". Mais fiel ao problema real — em IronMON o
que interessa é não morrer — mas é uma mudança ao §3.6, que está marcado como decidido.

## D. Abilities — a ordem de cálculo mudou

**Decidido: primeiro o mon com o moveset, só depois a ability.** A ability não entra na geração
do perfil — entra como **grau de aproveitamento** que aquele mon, com aquele moveset, consegue
tirar dela. Guts é trunfo num mon físico e vale zero num special sem moves físicos.

### Consequência: o custo cai 65x

| Ordem | Cálculo | Custo |
|---|---|---|
| A. ability antes (multiplica a seleção de moveset) | 24 867 linhas x 73 abilities x 8 910 células x 200 movesets x 3 cenários | **270 h** |
| **B. moveset primeiro, ability depois** | seleção 1.3x10^11 + aproveitamento 1.6x10^10 | **4.1 h** |

A seleção de moveset deixa de ser repetida por ability: corre uma vez por `(mon, perfil)` e a
ability aplica-se por cima. **Isto torna as classes de equivalência desnecessárias para efeito de
custo** — dá para manter as 73 individuais. Continuam úteis só como vocabulário.

> **Aproximação assumida:** a ability não influencia *que* moveset é escolhido. Na margem isso é
> falso — Guts pode tornar o único move físico melhor que um special que de outra forma ganhava.
> Aceite em troca do fator 65x.

### D7 — Independentes do moveset — 2

```
battle-armor   shell-armor
```

**S tier incondicional.** São as únicas que valem sempre o mesmo, independentemente do mon e do
moveset: nunca há um mon que não beneficie de não levar críticos. Não precisam do cálculo de
aproveitamento.

### As restantes 71 — aproveitamento dependente do moveset

Classificadas abaixo. As classes dizem **onde entram no pipeline**, não quanto valem — o quanto
sai do cálculo de aproveitamento.

### D0 — Banidas pelo ruleset — 3 · `[ ]`

```
huge-power   pure-power   wonder-guard
```

### D1 — Altera o type chart — 5 · `[ ]`

```
levitate       evita GROUND
flash-fire     imune a FIRE
volt-absorb    absorve ELECTRIC
water-absorb   absorve WATER
thick-fat      metade de FIRE e ICE
```

### D2b — Aproveitamento condicional — 2 · `[ ]`

```
rock-head    vale se o moveset tiver recuo (double-edge, volt-tackle, take-down, submission)
damp         vale contra Explosion adversario; ZERO se o teu mon for GHOST
```

Saíram de D8. São o exemplo mais limpo do modelo de aproveitamento: uma depende do **moveset**,
a outra dos **tipos** do mon.

### D2 — Altera stats efetivos — 9 · `[ ]`

```
guts           Atk x1.5 com status
marvel-scale   Def x1.5 com status
intimidate     baixa o Atk do adversario
speed-boost    Speed +1 por turno
hustle         fisico x1.5, precisao a descer
compound-eyes  precisao x1.3
overgrow       GRASS x1.5 abaixo de 1/3 HP
blaze          FIRE x1.5 abaixo de 1/3 HP
torrent        WATER x1.5 abaixo de 1/3 HP
swarm          BUG x1.5 abaixo de 1/3 HP
```

### D3 — Altera o upside — 19 · `[ ]`

Não são independentes do grupo C: têm de ser calculadas em conjunto (§3.5b).

```
serene-grace   DOBRA a probabilidade dos efeitos secundarios
shield-dust    ANULA os efeitos secundarios recebidos
immunity       imune a poison         limber         imune a paralysis
insomnia       imune a sleep          vital-spirit   imune a sleep
water-veil     imune a burn           magma-armor    imune a freeze
own-tempo      imune a confusion      oblivious      imune a infatuation
inner-focus    imune a flinch         keen-eye       imune a queda de precisao
clear-body     imune a queda de stats white-smoke    imune a queda de stats
hyper-cutter   imune a queda de Atk   early-bird     sleep passa a dobrar
shed-skin      33%/turno de curar status
synchronize    devolve burn/paralysis/poison ao atacante
natural-cure   cura ao trocar
```

### D4 — Altera turnos — 1 · `[ ]`

```
truant         salta um turno em cada dois
```

### D5 — Meteorologia — 10 · `[ ]`

```
drizzle  drought  sand-stream          invocam
chlorophyll  swift-swim               Speed x2 na meteorologia certa
rain-dish    sand-veil                cura / evasao
air-lock     cloud-nine               anulam meteorologia
forecast                              so o Castform
```

### D6 — Contacto / passivo — 6 · `[ ]`

```
static  poison-point  flame-body  effect-spore    30% de status ao ser tocado
rough-skin                                        1/8 HP ao ser tocado
cute-charm                                        30% de infatuation ao ser tocado
```

### D8 — Sem efeito material — 19 · `[ ]`

```
illuminate  run-away  pickup  stench  sticky-hold  suction-cups
soundproof  liquid-ooze  magnet-pull  arena-trap  shadow-tag
color-change  sturdy  trace  pressure  plus  minus  lightning-rod
```

---

## E. Casos duvidosos — decidir um a um

Estes foram para D8 mas têm argumento para sair de lá.

| Ability | Porque está em D8 | Argumento contra |
|---|---|---|
| **sturdy** | em **Gen 3** só bloqueia OHKO moves, e esses estão excluídos em A1 | a descrição do veekun é a moderna ("evita KO desde HP máximo"), que só vale da Gen 5 em diante |
| **lightning-rod** | em **Gen 3** só redireciona em combates duplos | a descrição do veekun diz "absorve", que é Gen 5+. Em single battle é no-op |
| **plus / minus** | precisam de um aliado com a outra | em IronMON só se usa um mon: nunca ativam |
| **natural-cure** | cura ao trocar, e trocas quase não há | posta em D3 por consistência, mas na prática é no-op |
| ~~**rock-head**~~ | — | **RESOLVIDO**: sai de D8. Vale so se o moveset tiver recuo — `double-edge` (120 BP, 33%), `volt-tackle` (120, 33%), `take-down` (90, 25%), `submission` (80, 25%). Aproveitamento dependente do *moveset*. |
| ~~**damp**~~ | — | **RESOLVIDO**: sai de D8. Vale contra Explosion/Self-Destruct do adversario, mas **zero se o teu mon for GHOST** — os dois moves sao NORMAL e os Ghost ja sao imunes. Aproveitamento dependente dos *tipos* do mon. |
| **color-change** | muda de tipo ao ser atingido | altera o type chart em pleno combate — complexo de modelar |
| **trace** | copia a ability do adversario | obrigaria a resolver abilities em cadeia |
| **arena-trap / shadow-tag / magnet-pull** | impedem fuga | irrelevante contra treinadores (não podes fugir de qualquer forma) |

---

## Armadilha de dados

As descrições de abilities do veekun são o comportamento **moderno**, não o de Gen 3. Pelo menos
`sturdy` e `lightning-rod` mudaram de comportamento depois da Gen 3. Qualquer classificação feita
a partir do texto tem de ser confirmada contra o comportamento de Gen 3.
