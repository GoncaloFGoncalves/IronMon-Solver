/* Motor de cálculo ao vivo: o mesmo score do Python, no browser.
 *
 * A tabela da camada 0 responde "o que esperar de um moveset aleatório". Esta
 * pergunta é outra: "e se ele tiver giga-drain em vez de surf" — um moveset
 * concreto, que não está na tabela e tem de ser calculado na hora.
 *
 * É um port de mon/skew.py, stats.py, formula.py, damage.py, vector.py e
 * score.py. Dois caminhos a responder ao mesmo é como se apanhou o bug da
 * truncagem; por isso há um teste que corre este ficheiro em node e compara
 * com o Python célula a célula.
 */

const MAX_TURNS = 6;
const ROLLS = [];
for (let r = 85; r <= 100; r++) ROLLS.push(r);

/* O Python arredonda meios para par (round(132.5) === 132). Math.round
 * arredonda para cima e divergia em todo o BST divisível por 4 que caísse
 * num .5 — o base stat saía 1 acima e o dano com ele. */
function roundHalfEven(value) {
  const floor = Math.floor(value);
  const rest = value - floor;
  if (rest > 0.5) return floor + 1;
  if (rest < 0.5) return floor;
  return floor % 2 === 0 ? floor : floor + 1;
}

const HYBRID = "hybrid";
const PAIRS = [["physical", "special"], ["def_tank", "spdef_tank"], ["fast", "bulky"]];

function split(bst, variant, favoursFirst) {
  if (variant === HYBRID) return [bst / 6, bst / 6];
  return variant === favoursFirst ? [bst / 4, bst / 12] : [bst / 12, bst / 4];
}

/* Os seis base stats de um perfil. A ordem é a do StatProfile do Python:
 * hp, attack, defense, special_attack, special_defense, speed. */
export function baseStats(bst, profile) {
  const [offensive, defensive, tempo] = profile;
  const [attack, specialAttack] = split(bst, offensive, PAIRS[0][0]);
  const [defense, specialDefense] = split(bst, defensive, PAIRS[1][0]);
  const [speed, hp] = split(bst, tempo, PAIRS[2][0]);
  return [hp, attack, defense, specialAttack, specialDefense, speed];
}

export function statAtLevel(base, level, iv, isHp) {
  const common = Math.floor((2 * roundHalfEven(base) + iv) * level / 100);
  return isHp ? common + level + 10 : common + 5;
}

export function variantStats(bst, profile, level, iv) {
  const bases = baseStats(bst, profile);
  const [hp, attack, defense, specialAttack, specialDefense, speed] =
    bases.map((base, i) => statAtLevel(base, level, iv, i === 0));
  return { hp, attack, defense, specialAttack, specialDefense, speed, bases };
}

/* ---- dano ---- */

export function makeChart(chart) {
  return (attacking, defending) => {
    let out = 1;
    for (const type of defending) {
      const row = chart[attacking];
      out *= row && row[type] !== undefined ? row[type] : 1;
    }
    return out;
  };
}

export function damageBeforeRoll(level, power, attack, defense, stab, effectiveness) {
  const factor = Math.floor(2 * level / 5) + 2;   // (2*level)//5, nao 2*(level//5)
  let damage = Math.floor(Math.floor(factor * power * attack / defense) / 50) + 2;
  if (stab) damage = Math.floor(damage * 3 / 2);
  return Math.trunc(damage * effectiveness);
}

/* Distribuição acumulada do dano de n golpes, com cada golpe truncado
 * sozinho. É o `_totals` do damage.py, em cache por dano-base porque o mesmo
 * valor repete-se em centenas de defensores. */
const totalsCache = new Map();

function tailByTurn(baseDamage) {
  const cached = totalsCache.get(baseDamage);
  if (cached) return cached;
  const hits = ROLLS.map(roll => Math.floor(baseDamage * roll / 100));
  const span = Math.max(...hits);
  let dist = new Float64Array(1);
  dist[0] = 1;
  const perTurn = [];
  for (let turn = 1; turn <= MAX_TURNS; turn++) {
    const grown = new Float64Array(dist.length + span);
    for (let total = 0; total < dist.length; total++) {
      const weight = dist[total];
      if (!weight) continue;
      for (const hit of hits) grown[total + hit] += weight / 16;
    }
    dist = grown;
    // tail[hp] = P(dano acumulado >= hp)
    const tail = new Float64Array(dist.length + 1);
    let running = 0;
    for (let total = dist.length - 1; total >= 0; total--) {
      running += dist[total];
      tail[total] = running;
    }
    perTurn.push(tail);
  }
  totalsCache.set(baseDamage, perTurn);
  return perTurn;
}

export function koChance(baseDamage, hp, turn) {
  if (baseDamage <= 0 || turn <= 0) return 0;
  const tail = tailByTurn(baseDamage)[turn - 1];
  if (hp <= 0) return 1;
  return hp < tail.length ? tail[hp] : 0;
}

export function meanHit(baseDamage) {
  let total = 0;
  for (const roll of ROLLS) total += Math.floor(baseDamage * roll / 100);
  return total / ROLLS.length;
}

/* ---- a troca ---- */

/* (P(ganhar), E[HP restante | ganhar]) para um defensor. `first` é a
 * probabilidade de eu atacar primeiro: 1, 0 ou 0.5 no empate. */
export function trade(damage, hp, incoming, theirHp, first) {
  let won = 0;
  let hpLeft = 0;
  let before = 0;
  const mean = meanHit(incoming);
  for (let turn = 1; turn <= MAX_TURNS; turn++) {
    const now = koChance(damage, theirHp, turn);
    const landed = now - before;
    if (landed > 0) {
      const asFirst = landed * (1 - koChance(incoming, hp, turn - 1)) * first;
      const asSecond = landed * (1 - koChance(incoming, hp, turn)) * (1 - first);
      won += asFirst + asSecond;
      hpLeft += asFirst * Math.max(hp - (turn - 1) * mean, 0)
              + asSecond * Math.max(hp - turn * mean, 0);
    }
    before = now;
  }
  return [won, won > 0 ? hpLeft / won : 0];
}

/* ---- o pool de defensores ---- */

export function buildPool(species, profiles, level, effectiveness) {
  const rows = [];
  for (const [, , types, bst] of species) {
    for (const profile of profiles) {
      const s = variantStats(bst, profile, level, 31);
      const physical = s.attack >= s.specialAttack;
      rows.push({
        types, hp: s.hp, defense: s.defense, specialDefense: s.specialDefense,
        speed: s.speed, physical,
        // Os dois lados, nao so o mais forte: o 4b precisa de saber com que
        // stat ele bate em cada tipo de move, nao so com o melhor dele.
        attack: s.attack, specialAttack: s.specialAttack,
        best: physical ? s.attack : s.specialAttack,
      });
    }
  }
  const factor = Math.floor(2 * level / 5) + 2;
  return { rows, factor, level, effectiveness };
}

/* ---- 4b: o dano que levo, dos 4 moves sorteados dele ---- */

const MIN_ROLL = 85;
const SLOTS = 4;

export function lethalCap(hp) {
  let cap = Math.ceil(hp * 100 / MIN_ROLL);
  while (Math.floor(cap * MIN_ROLL / 100) < hp) cap += 1;
  return cap;
}

/* C(a, k) / C(b, k) sem binomiais: 3e30 nao cabe num double com exactidao. */
function ratioOfChoose(a, b, k) {
  if (a < k) return 0;
  let r = 1;
  for (let i = 0; i < k; i++) r *= (a - i) / (b - i);
  return r;
}

/* Peso de cada posicao do pool ordenado, do pior para o melhor -- a mesma
   estatistica de ordem do orderstat.py: w_r = C(r, k-1) / C(M, k).
   Por recorrencia, para nao precisar dos binomiais: w_{k-1} = 1/C(M,k) e
   w_r = w_{r-1} * r / (r-k+1). Nao se normaliza no fim, para nao divergir
   do lado do Python, que tambem nao normaliza. */
export function subsetWeights(poolSize, known) {
  const k = Math.max(1, Math.min(known, poolSize));
  const out = new Float64Array(poolSize);
  let cur = 1;
  for (let i = 0; i < k; i++) cur *= (k - i) / (poolSize - i);
  out[k - 1] = cur;
  for (let r = k; r < poolSize; r++) out[r] = out[r - 1] * r / (r - k + 1);
  return out;
}

/* `(share, safe)` por defensor: a hipotese de pelo menos um dos 4 moves dele
   me matar de um, e o que levo quando nenhum mata. */
export function incomingProfile(attacker, pool, threatMoves, physicalTypes) {
  const n = pool.rows.length;
  const total = threatMoves.length;
  const cap = lethalCap(attacker.hp);
  const share = new Float64Array(n);
  const safe = new Float64Array(n);
  const column = new Float64Array(total);

  for (let i = 0; i < n; i++) {
    const them = pool.rows[i];
    let lethal = 0;
    let kept = 0;
    for (let m = 0; m < total; m++) {
      const move = threatMoves[m];
      const physical = physicalTypes.has(move.type);
      const offence = physical ? them.attack : them.specialAttack;
      const defence = physical ? attacker.defense : attacker.specialDefense;
      const base = Math.floor(Math.floor(pool.factor * move.power * offence / defence) / 50) + 2;
      const stab = them.types.includes(move.type) ? 1.5 : 1;
      const damage = Math.floor(base * stab * pool.effectiveness(move.type, attacker.types));
      if (damage >= cap) lethal += 1; else column[kept++] = damage;
    }
    const left = total - lethal;
    if (left < SLOTS) { share[i] = 1; safe[i] = cap; continue; }
    share[i] = 1 - ratioOfChoose(left, total, SLOTS);
    const sorted = Array.prototype.slice.call(column, 0, kept).sort((a, b) => a - b);
    const weights = subsetWeights(left, SLOTS);
    let acc = 0;
    for (let r = 0; r < left; r++) acc += sorted[r] * weights[r];
    // Truncado, como do lado do Python: o dano e inteiro no jogo.
    safe[i] = Math.floor(acc);
  }
  return { share, safe, cap };
}

/* ---- score de um moveset concreto ---- */

/* `profile` e o `incomingProfile` ja calculado. Nao depende do meu moveset,
   e custa 194x10422: recalcula-lo por chamada punha o painel a 1.9 s, com
   seis chamadas a fazer a mesma conta. */
export function scoreMoveset(attacker, moves, pool, physicalTypes, threatMoves,
                             profile) {
  const n = pool.rows.length;
  if (!moves.length || !n) return { win: 0, hpLeft: 0, risk: 0 };
  const threat = threatMoves && threatMoves.length ? threatMoves : moves;
  const { share, safe, cap } = profile
    || incomingProfile(attacker, pool, threat, physicalTypes);

  let totalWin = 0;
  let totalHp = 0;
  for (let i = 0; i < n; i++) {
    const them = pool.rows[i];
    const first = attacker.speed > them.speed ? 1 : attacker.speed < them.speed ? 0 : 0.5;

    let bestWin = 0;
    let bestHp = 0;
    for (const move of moves) {
      const physical = physicalTypes.has(move.type);
      const damage = damageBeforeRoll(
        attacker.level, move.power,
        physical ? attacker.attack : attacker.specialAttack,
        physical ? them.defense : them.specialDefense,
        attacker.types.includes(move.type),
        pool.effectiveness(move.type, them.types));
      // 4b: a troca resolve-se duas vezes -- ele tirou um move que me mata,
      // ou nao tirou -- e pesa-se pela quota letal.
      const [winA, hpA] = trade(damage, attacker.hp, cap, them.hp, first);
      const [winB, hpB] = trade(damage, attacker.hp, safe[i], them.hp, first);
      const win = share[i] * winA + (1 - share[i]) * winB;
      const hpLeft = share[i] * hpA + (1 - share[i]) * hpB;
      // Empate na vitoria fica com o ultimo move da lista, que e o que o
      // argsort estavel do numpy faz do lado do Python. Divergir aqui dava
      // 10 pp de diferenca no HP quando varios moves ganham sempre.
      if (win >= bestWin) { bestWin = win; bestHp = hpLeft; }
    }
    totalWin += bestWin;
    totalHp += bestHp;
  }
  let totalRisk = 0;
  for (let i = 0; i < n; i++) totalRisk += share[i];
  return { win: totalWin / n, hpLeft: totalHp / n / attacker.hp,
           risk: totalRisk / n };
}

/* ---- a cadeia de breakpoint: o que me mata, por tipo ---- */

/* Os moves de um tipo contra mim, do que mais doi para o que menos, com
   P(morrer de 1) e P(morrer de 2). `hp` substitui o meu maximo, para
   perguntar ferido -- na Misty nada ELECTRIC me mata aos 88 de HP e aos 12
   que sobram de um thunderbolt mata-me um quarto do pool. */
export function chain(attacker, moves, moveType, threat, level, effectiveness,
                      physicalTypes, hp) {
  const alvo = hp == null ? attacker.hp : hp;
  const physical = physicalTypes.has(moveType);
  const offence = physical ? threat.attack : threat.specialAttack;
  const defence = physical ? attacker.defense : attacker.specialDefense;
  const factor = Math.floor(2 * level / 5) + 2;
  const eff = effectiveness(moveType, attacker.types);

  const rungs = [];
  for (const move of moves) {
    if (move.type !== moveType) continue;
    let damage = 0;
    if (eff !== 0) {
      const base = Math.floor(Math.floor(factor * move.power * offence / defence) / 50) + 2;
      damage = Math.floor(base * threat.stab * eff);
    }
    rungs.push({
      move: move.name, power: move.power, damage,
      ohko: koChance(damage, alvo, 1), two: koChance(damage, alvo, 2),
    });
  }
  rungs.sort((a, b) => b.damage - a.damage || (a.move < b.move ? -1 : 1));
  return { rungs, effectiveness: eff };
}

/* `[ultimo que mata sempre, primeiro que falha]`; qualquer um pode ser null. */
export function breakpointOf(rungs) {
  let last = null;
  for (const rung of rungs) {
    if (rung.ohko < 1) return [last, rung];
    last = rung;
  }
  return [last, null];
}

/* ---- o ranking por defensor ---- */

/* Os `limit` defensores onde este atacante se sai pior. O vector por
   defensor ja existe dentro do score; so se perde na media. */
export function worstMatchups(attacker, moves, pool, physicalTypes, threatMoves,
                              limit, profile) {
  const n = pool.rows.length;
  const threat = threatMoves && threatMoves.length ? threatMoves : moves;
  const { share, safe, cap } = profile
    || incomingProfile(attacker, pool, threat, physicalTypes);
  const out = [];
  for (let i = 0; i < n; i++) {
    const them = pool.rows[i];
    const first = attacker.speed > them.speed ? 1 : attacker.speed < them.speed ? 0 : 0.5;
    let bestWin = 0;
    let bestHp = 0;
    let dealt = 0;
    for (const move of moves) {
      const physical = physicalTypes.has(move.type);
      const damage = damageBeforeRoll(
        attacker.level, move.power,
        physical ? attacker.attack : attacker.specialAttack,
        physical ? them.defense : them.specialDefense,
        attacker.types.includes(move.type),
        pool.effectiveness(move.type, them.types));
      if (damage > dealt) dealt = damage;
      const [winA, hpA] = trade(damage, attacker.hp, cap, them.hp, first);
      const [winB, hpB] = trade(damage, attacker.hp, safe[i], them.hp, first);
      const win = share[i] * winA + (1 - share[i]) * winB;
      if (win >= bestWin) {
        bestWin = win;
        bestHp = share[i] * hpA + (1 - share[i]) * hpB;
      }
    }
    out.push({ index: i, win: bestWin, hpLeft: bestHp / attacker.hp,
               dealt, taken: safe[i], risk: share[i] });
  }
  // Desempate pelo HP: entre dois que se perdem na mesma medida, o pior e o
  // que custa mais caro ganhar.
  out.sort((a, b) => a.win - b.win || a.hpLeft - b.hpLeft);
  return out.slice(0, Math.max(0, Math.min(limit || 20, n)));
}

export function clearCache() { totalsCache.clear(); }
