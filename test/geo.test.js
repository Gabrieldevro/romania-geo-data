import { test } from 'node:test';
import assert from 'node:assert/strict';
import geo, { counties, county, localities, locality, search, byPostalCode, normalize } from '../index.js';

test('42 counties with plate codes and diacritics', () => {
  assert.equal(counties().length, 42);
  assert.equal(county('is').name, 'Iași');
  assert.equal(county('Bistrita-Nasaud').code, 'BN');
  assert.equal(county('B').seat, 'București');
  assert.equal(county('CJ').region, 'Nord-Vest');
  assert.equal(county('XX'), null);
});

test('every county has its localities, Bucharest has 6 sectors', () => {
  for (const c of counties()) assert.equal(localities(c.code).length, c.localities, c.code);
  assert.deepEqual(localities('B').map((l) => l.name), ['Sectorul 1', 'Sectorul 2', 'Sectorul 3', 'Sectorul 4', 'Sectorul 5', 'Sectorul 6']);
  assert.ok(localities().length > 13000);
});

test('names use comma-below ș/ț and modern â', () => {
  const bad = localities().filter((l) => /[şţŞŢ]/.test(l.label) || /\Bî\B/.test(l.label));
  assert.deepEqual(bad, []);
});

test('search is diacritic-insensitive and ranks cities first', () => {
  const [first] = search('iasi');
  assert.equal(first.name, 'Iași');
  assert.equal(first.type, 'municipiu');
  assert.ok(search('valea mare').length > 10);
  assert.ok(search('valea mare', { county: 'AG' }).every((l) => l.county === 'AG'));
  assert.equal(search('cluj', { limit: 1 })[0].name, 'Cluj-Napoca');
});

test('labels disambiguate villages with the same name', () => {
  const labels = search('valea mare', { county: 'AG', limit: 50 }).map((l) => l.label);
  assert.equal(new Set(labels).size, labels.length);
  assert.match(labels[0], /\((com\.|oraș|mun\.) /);
});

test('postal codes and SIRUTA lookups', () => {
  const voluntari = search('voluntari', { county: 'IF' })[0];
  assert.equal(voluntari.postal_code, '077190');
  assert.equal(byPostalCode('77190')[0].name, 'Voluntari');
  assert.equal(locality(voluntari.siruta).name, 'Voluntari');
  assert.deepEqual(search('bucuresti').map((l) => l.label).slice(0, 2), ['București, Sectorul 1', 'București, Sectorul 2']);
  assert.equal(search('Iasi', { county: 'IS' })[0].street_level_postal_codes, true);
});

test('normalize and default export', () => {
  assert.equal(normalize('  Bistrița-Năsăud  '), 'bistrita-nasaud');
  assert.equal(normalize('Ţăndărei'), 'tandarei');
  assert.equal(typeof geo.search, 'function');
});
