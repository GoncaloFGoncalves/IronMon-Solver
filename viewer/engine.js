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
        attack: physical ? s.attack : s.specialAttack,
      });
    }
  }
  const factor = Math.floor(2 * level / 5) + 2;
  return { rows, factor, level, effectiveness };
}

/* ---- score de um moveset concreto ---- */

export function scoreMoveset(attacker, moves, pool, physicalTypes) {
  const n = pool.rows.length;
  if (!moves.length || !n) return { win: 0, hpLeft: 0 };

  let totalWin = 0;
  let totalHp = 0;
  for (let i = 0; i < n; i++) {
    const them = pool.rows[i];
    const theirDefense = them.physical ? attacker.defense : attacker.specialDefense;
    const incoming = Math.floor(Math.floor(pool.factor * 80 * them.attack / theirDefense) / 50) + 2;
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
      const [win, hpLeft] = trade(damage, attacker.hp, incoming, them.hp, first);
      // Empate na vitoria fica com o ultimo move da lista, que e o que o
      // argsort estavel do numpy faz do lado do Python. Divergir aqui dava
      // 10 pp de diferenca no HP quando varios moves ganham sempre.
      if (win >= bestWin) { bestWin = win; bestHp = hpLeft; }
    }
    totalWin += bestWin;
    totalHp += bestHp;
  }
  return { win: totalWin / n, hpLeft: totalHp / n / attacker.hp };
}

export function clearCache() { totalsCache.clear(); }
