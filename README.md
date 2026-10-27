<h1 align="center">🗺️ romania-geo-data</h1>

<p align="center"><b>All 42 Romanian counties and 13,755 localities</b> — with SIRUTA codes, postal codes, proper diacritics and disambiguated labels — as <b>JSON, CSV, SQL</b>, plus a tiny search API for <b>JavaScript</b> and <b>PHP</b>.<br>
<i>Toate județele și localitățile din România, cu coduri SIRUTA, coduri poștale și diacritice corecte. Gata pentru formularele de checkout.</i></p>

<p align="center">
<img alt="tests" src="https://github.com/Gabrieldevro/romania-geo-data/actions/workflows/tests.yml/badge.svg">
<img alt="counties" src="https://img.shields.io/badge/counties-42-0b5fff?style=flat-square">
<img alt="localities" src="https://img.shields.io/badge/localities-13%2C755-0b5fff?style=flat-square">
<img alt="data" src="https://img.shields.io/badge/data-INS%20SIRUTA%20%2B%20Po%C8%99ta%20Rom%C3%A2n%C4%83-555?style=flat-square">
<img alt="License" src="https://img.shields.io/badge/license-MIT%20%2B%20OGL--ROU-blue?style=flat-square">
</p>

---

Every Romanian shop needs a **county → city** dropdown. Most copies floating around have no diacritics, broken `ş/ș` characters, no way to tell apart the 11 villages called *Valea Mare*, and no postal codes. This one is built from the **official open data** with a reproducible script.

```js
import { county, localities, search } from 'romania-geo-data';

county('IS');                 // { code: 'IS', name: 'Iași', region: 'Nord-Est', seat: 'Iași', ... }
localities('CJ').length;      // 434
search('valea mare', { county: 'AG' })[0].label;  // "Valea Mare (com. Priboieni)"
search('bucuresti')[0].label; // "București, Sectorul 1"
```

## What you get

| | |
|---|---|
| `data/counties.json` | 42 counties: plate code (`AB`…`VN`, `B`), name, SIRUTA, development region, county seat, number of localities |
| `data/localities.json` | 13,755 localities: SIRUTA, name, **label**, county, type, urban/rural, parent commune/town/municipality, **postal code** |
| `data/localities.min.json` | compact `[siruta, name, county, label, postal_code]` arrays (850 KB) for the browser |
| `data/*.csv` | the same as CSV (UTF-8) |
| `data/romania.sql` | `CREATE TABLE` + `INSERT`s for MySQL, MariaDB, PostgreSQL and SQLite |

A locality looks like this:

```json
{
  "siruta": 179560,
  "name": "Voluntari",
  "label": "Voluntari",
  "county": "IF",
  "type": "oraș",
  "urban": true,
  "uat_siruta": 179551,
  "uat_name": "Voluntari",
  "uat_type": "oraș",
  "postal_code": "077190",
  "street_level_postal_codes": false
}
```

- **`label`** is ready for dropdowns: villages that share a name get their commune in brackets — `Fetești (com. Scobinți)`.
- **`type`**: `municipiu`, `oraș`, `sector`, `localitate componentă` or `sat`.
- **`postal_code`** is filled for 13,688 localities. Big cities (Iași, Cluj-Napoca, Bucharest sectors…) have one code per street, so it is `null` there and `street_level_postal_codes` is `true`.
- Names use the correct **comma-below `ș` `ț`** and modern **`â`** spelling (`Câmpuri`, not `Cîmpuri`).

## JavaScript / TypeScript

```bash
npm install romania-geo-data
```

```js
import { counties, county, localities, locality, search, byPostalCode, normalize } from 'romania-geo-data';

counties();                         // all 42, sorted by name
county('Bistrita-Nasaud');          // by code or name, diacritics optional
localities('B');                    // the 6 Bucharest sectors
locality(179560);                   // by SIRUTA
search('chis', { limit: 5 });       // exact > prefix > substring, cities before villages
byPostalCode('077190');             // [Voluntari]
normalize('Bistrița-Năsăud');       // "bistrita-nasaud"
```

Works in Node 18+. In the browser, import the JSON directly: `import data from 'romania-geo-data/data/localities.min.json'`. Types are included.

## PHP / Laravel

```bash
composer require gabrieldevro/romania-geo-data
```

```php
use Gabrieldev\RomaniaGeo\RomaniaGeo;

RomaniaGeo::counties();
RomaniaGeo::county('IS')['name'];          // "Iași"
RomaniaGeo::localities('CJ');
RomaniaGeo::search('valea mare', 'AB');
RomaniaGeo::byPostalCode('077190');
```

Laravel seeder in three lines:

```php
foreach (array_chunk(RomaniaGeo::localities(), 1000) as $chunk) {
    DB::table('localities')->insert(array_map(fn ($l) => Arr::only($l, ['siruta', 'name', 'label', 'county', 'postal_code']), $chunk));
}
```

Or import `RomaniaGeo::path('romania.sql')` directly into your database.

## Dependent dropdown example

```html
<select id="county"></select>
<select id="city"></select>
<script type="module">
  import { counties, localities } from 'https://cdn.jsdelivr.net/npm/romania-geo-data/+esm';
  const c = document.querySelector('#county'), l = document.querySelector('#city');
  c.innerHTML = counties().map((x) => `<option value="${x.code}">${x.name}</option>`).join('');
  const fill = () => (l.innerHTML = localities(c.value).map((x) => `<option value="${x.siruta}">${x.label}</option>`).join(''));
  c.onchange = fill; fill();
</script>
```

## Sources and rebuilding

| Source | Publisher | Licence |
|---|---|---|
| [SIRUTA](https://data.gov.ro/dataset/siruta) – administrative units and localities | Institutul Național de Statistică | OGL-ROU-1.0 |
| [Coduri poștale cu SIRUTA](https://data.gov.ro/dataset/coduri-postale-romania) – postal codes (Infocod) | Poșta Română | OGL-ROU-1.0 |

```bash
pip install xlrd
python tools/build.py   # downloads the sources and regenerates data/
```

These are the latest editions published on data.gov.ro. Administrative changes since then are rare; if you spot one, open an issue or a PR against `tools/build.py`.

---

## 🇷🇴 Pe scurt, în română

Lista completă cu **cele 42 de județe și 13.755 de localități** din România, din datele oficiale INS (SIRUTA) și Poșta Română (coduri poștale), în JSON, CSV și SQL:

- diacritice corecte (`ș`, `ț` cu virgulă, `â` modern);
- etichete clare pentru satele cu același nume: `Valea Mare (com. Priboieni)`;
- cod poștal pentru 13.688 de localități; orașele mari au cod pe stradă;
- căutare fără diacritice (`iasi` → Iași), pentru JavaScript și PHP/Laravel.

Perfect pentru selectorul județ → localitate din checkout.

## License

Code: MIT © [Gabriel Dev](https://gabrieldev.eu). Data: © INS and Poșta Română, published under the [Open Government Licence Romania 1.0](https://data.gov.ro/base/images/logoinst/OGL-ROU-1.0.pdf); attribution is kept above.

If it saved you an afternoon of data cleaning, a ⭐ helps other developers find it.
