import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

let countiesCache;
let localitiesCache;

/** Lowercase, no diacritics (both ş/ș forms), single spaces: "Bistrița-Năsăud" -> "bistrita-nasaud". */
export function normalize(text) {
  return String(text ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
}

/** All 42 counties (41 + București), sorted by name. */
export function counties() {
  return (countiesCache ??= require('./data/counties.json'));
}

/** A county by auto code ("IS", "b") or name ("Iasi", "Iași"). */
export function county(codeOrName) {
  const key = normalize(codeOrName);
  return counties().find((c) => c.code.toLowerCase() === key || normalize(c.name) === key) ?? null;
}

/** All localities, or only those of one county (code or name). */
export function localities(countyCodeOrName) {
  const all = (localitiesCache ??= require('./data/localities.json'));
  if (countyCodeOrName === undefined) return all;
  const c = county(countyCodeOrName);
  return c ? all.filter((l) => l.county === c.code) : [];
}

/** A locality by its SIRUTA code. */
export function locality(siruta) {
  const id = Number(siruta);
  return localities().find((l) => l.siruta === id) ?? null;
}

/**
 * Diacritic- and case-insensitive search: exact names first, then prefixes, then substrings; towns before villages.
 * search('iasi'), search('valea mare', { county: 'AB' }), search('chis', { limit: 5 })
 */
export function search(query, { county: countyFilter, limit = 20 } = {}) {
  const q = normalize(query);
  if (!q) return [];
  const pool = countyFilter ? localities(countyFilter) : localities();
  const rank = { municipiu: 0, oraș: 1, sector: 1, 'localitate componentă': 3, sat: 4 };

  return pool
    .map((l) => {
      const name = normalize(l.name);
      const label = normalize(l.label);
      const score = name === q ? 0 : name.startsWith(q) || label.startsWith(q) ? 1 : label.includes(q) ? 2 : -1;
      return { l, score };
    })
    .filter((x) => x.score >= 0)
    .sort((a, b) => a.score - b.score || rank[a.l.type] - rank[b.l.type] || a.l.name.localeCompare(b.l.name, 'ro'))
    .slice(0, limit)
    .map((x) => x.l);
}

/** Localities with this exact postal code (small localities have one code; big cities have one per street). */
export function byPostalCode(code) {
  const c = String(code).trim().padStart(6, '0');
  return localities().filter((l) => l.postal_code === c);
}

export default { normalize, counties, county, localities, locality, search, byPostalCode };
