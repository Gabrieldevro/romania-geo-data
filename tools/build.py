"""
Builds data/*.json, data/*.csv and data/*.sql from the official open datasets on data.gov.ro:

  * SIRUTA nomenclature (INS) .................. https://data.gov.ro/dataset/siruta
  * Postal codes "Infocod cu SIRUTA" (Poșta Română) https://data.gov.ro/dataset/coduri-postale-romania

Both are published under the Open Government Licence Romania 1.0 (OGL-ROU-1.0).

    pip install xlrd
    python tools/build.py          # downloads the sources into sources/ on first run
"""

import csv
import json
import re
import sys
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / 'sources'
DATA = ROOT / 'data'

URLS = {
    'siruta.csv': 'http://data.gov.ro/storage/f/2013-11-01T11%3A49%3A59.808Z/siruta.csv',
    'infocod-siruta-2016.xls': 'https://data.gov.ro/dataset/3eb7dc31-e53e-4c09-b2e2-87c909e68fb6/resource/29a5c89e-0f23-4a42-aa05-765ef04177b6/download/infocod-cu-siruta-mai-2016.xls',
}

# SIRUTA county number (JUD) -> (auto code, official name with diacritics)
COUNTIES = {
    1: ('AB', 'Alba'), 2: ('AR', 'Arad'), 3: ('AG', 'Argeș'), 4: ('BC', 'Bacău'), 5: ('BH', 'Bihor'),
    6: ('BN', 'Bistrița-Năsăud'), 7: ('BT', 'Botoșani'), 8: ('BV', 'Brașov'), 9: ('BR', 'Brăila'),
    10: ('BZ', 'Buzău'), 11: ('CS', 'Caraș-Severin'), 12: ('CJ', 'Cluj'), 13: ('CT', 'Constanța'),
    14: ('CV', 'Covasna'), 15: ('DB', 'Dâmbovița'), 16: ('DJ', 'Dolj'), 17: ('GL', 'Galați'),
    18: ('GJ', 'Gorj'), 19: ('HR', 'Harghita'), 20: ('HD', 'Hunedoara'), 21: ('IL', 'Ialomița'),
    22: ('IS', 'Iași'), 23: ('IF', 'Ilfov'), 24: ('MM', 'Maramureș'), 25: ('MH', 'Mehedinți'),
    26: ('MS', 'Mureș'), 27: ('NT', 'Neamț'), 28: ('OT', 'Olt'), 29: ('PH', 'Prahova'),
    30: ('SM', 'Satu Mare'), 31: ('SJ', 'Sălaj'), 32: ('SB', 'Sibiu'), 33: ('SV', 'Suceava'),
    34: ('TR', 'Teleorman'), 35: ('TM', 'Timiș'), 36: ('TL', 'Tulcea'), 37: ('VS', 'Vaslui'),
    38: ('VL', 'Vâlcea'), 39: ('VN', 'Vrancea'), 40: ('B', 'București'), 51: ('CL', 'Călărași'),
    52: ('GR', 'Giurgiu'),
}

REGIONS = {1: 'Nord-Est', 2: 'Sud-Est', 3: 'Sud-Muntenia', 4: 'Sud-Vest Oltenia', 5: 'Vest',
           6: 'Nord-Vest', 7: 'Centru', 8: 'București-Ilfov'}

# SIRUTA TIP codes
UAT_TYPES = {1: 'municipiu', 4: 'municipiu', 2: 'oraș', 5: 'oraș', 3: 'comună', 9: 'municipiu'}
LOCALITY_TYPES = {6: 'sector', 9: 'municipiu', 10: 'localitate componentă', 11: 'sat', 17: 'oraș',
                  18: 'localitate componentă', 19: 'sat', 22: 'sat', 23: 'sat'}
SEAT_TYPES = {9, 17, 22}  # the locality that is the seat of its municipality / town / commune

SMALL_WORDS = {'de', 'din', 'pe', 'la', 'lui', 'cu', 'sub', 'peste', 'și', 'în', 'cel', 'mare', 'mic'} - {'mare', 'mic'}


def fix_diacritics(text: str) -> str:
    """Cedilla ş/ţ (legacy encodings) -> comma-below ș/ț (correct Romanian)."""
    text = text.translate(str.maketrans('şŞţŢ', 'șȘțȚ'))
    # Pre-1993 spelling in some SIRUTA names: "Cîmpuri" -> "Câmpuri" (î stays only at the start or end of a word).
    return re.sub(r'(?<=\w)î(?=\w)', 'â', re.sub(r'(?<=\w)Î(?=\w)', 'Â', text))


def title_case(name: str) -> str:
    words = re.split(r'(\s+|-)', name.lower())
    out = []
    for i, w in enumerate(words):
        out.append(w if (i and w in SMALL_WORDS) else w[:1].upper() + w[1:])
    return ''.join(out)


def ascii_slug(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def number(value) -> int:
    return int(float(str(value).replace(',', '.'))) if str(value).strip() else 0


def download():
    SOURCES.mkdir(exist_ok=True)
    for name, url in URLS.items():
        target = SOURCES / name
        if not target.exists():
            print('downloading', name)
            urllib.request.urlretrieve(url, target)


def load_postal():
    import xlrd

    book = xlrd.open_workbook(str(SOURCES / 'infocod-siruta-2016.xls'))
    names, codes, street_level = {}, defaultdict(set), set()

    small = book.sheet_by_index(2)  # localities under 50,000: one code per locality
    for i in range(1, small.nrows):
        _, county, locality, code, siruta = small.row_values(i)[:5]
        if siruta:
            names[int(siruta)] = locality.strip()
            codes[int(siruta)].add(str(code).strip().zfill(6))

    big = book.sheet_by_index(1)  # localities over 50,000: one code per street segment
    for i in range(1, big.nrows):
        row = big.row_values(i)
        if row[6]:
            names.setdefault(int(row[6]), row[1].strip())
            street_level.add(int(row[6]))
            codes[int(row[6])].add(str(row[5]).strip().zfill(6))

    bucharest = book.sheet_by_index(0)
    for i in range(1, bucharest.nrows):
        row = bucharest.row_values(i)
        if row[6]:
            street_level.add(int(row[6]))
            codes[int(row[6])].add(str(row[3]).strip().zfill(6))

    return names, codes, street_level


def main():
    download()
    names, codes, street_level = load_postal()
    rows = list(csv.DictReader(open(SOURCES / 'siruta.csv', encoding='cp1250'), delimiter=';'))

    def proper(row):
        siruta = number(row['SIRUTA'])
        name = names.get(siruta)
        if not name:
            raw = re.sub(r'^(MUNICIPIUL|ORAŞ|ORAS|COMUNA|JUDEŢUL|JUDETUL)\s+', '', row['DENLOC'].strip())
            name = title_case(raw)
        return fix_diacritics(name)

    by_siruta = {number(r['SIRUTA']): r for r in rows}

    uats = {}
    for r in rows:
        if r['NIV'] == '2':
            siruta = number(r['SIRUTA'])
            raw = r['DENLOC'].strip()
            name = fix_diacritics(title_case(re.sub(r'^(MUNICIPIUL|ORAŞ|ORAS|COMUNA)\s+', '', raw)))
            uats[siruta] = {'siruta': siruta, 'name': name, 'type': UAT_TYPES.get(number(r['TIP']), 'comună'),
                            'county': COUNTIES[number(r['JUD'])][0]}

    localities = []
    for r in rows:
        if r['NIV'] != '3':
            continue
        siruta, tip, parent = number(r['SIRUTA']), number(r['TIP']), number(r['SIRSUP'])
        county_code = COUNTIES[number(r['JUD'])][0]
        uat = uats.get(parent)
        name = proper(r)
        if tip == 6:
            name = 'Sectorul ' + name.rsplit(' ', 1)[-1]
            uat = {'siruta': parent, 'name': 'București', 'type': 'municipiu'}
        if uat and tip in SEAT_TYPES and uat['name'].lower() != name.lower():
            uat['name'] = name if uat['type'] != 'comună' else uat['name']
        loc_codes = sorted(codes.get(siruta, []))
        localities.append({
            'siruta': siruta,
            'name': name,
            'county': county_code,
            'type': LOCALITY_TYPES.get(tip, 'sat'),
            'urban': r['MED'].strip() == '1',
            'uat_siruta': parent,
            'uat_name': uat['name'] if uat else None,
            'uat_type': uat['type'] if uat else None,
            'postal_code': loc_codes[0] if len(loc_codes) == 1 and siruta not in street_level else None,
            'street_level_postal_codes': siruta in street_level,
        })

    # Use the seat locality's spelling (with diacritics) for each municipality / town name.
    seats = {l['uat_siruta']: l['name'] for l in localities if by_siruta[l['siruta']]['TIP'].strip() in ('9', '17')}
    for l in localities:
        if l['uat_type'] in ('municipiu', 'oraș') and l['uat_siruta'] in seats:
            l['uat_name'] = seats[l['uat_siruta']]
    commune_names = {}
    for u in uats.values():
        if u['type'] == 'comună':
            # Commune names in SIRUTA have no ă/â/î; the seat village often has the same name with diacritics.
            seat = next((l['name'] for l in localities if l['uat_siruta'] == u['siruta']
                         and by_siruta[l['siruta']]['TIP'].strip() == '22'), None)
            commune_names[u['siruta']] = seat if seat and ascii_slug(seat) == ascii_slug(u['name']) else u['name']
    for l in localities:
        if l['uat_type'] == 'comună':
            l['uat_name'] = commune_names[l['uat_siruta']]

    for l in localities:
        same_name = l['uat_name'] and ascii_slug(l['uat_name']) == ascii_slug(l['name'])
        l['label'] = f"București, {l['name']}" if l['type'] == 'sector' else l['name'] if same_name or not l['uat_name'] else \
            f"{l['name']} ({ {'comună': 'com.', 'oraș': 'oraș', 'municipiu': 'mun.'}[l['uat_type']] } {l['uat_name']})"

    localities.sort(key=lambda l: (l['county'], ascii_slug(l['name']), l['siruta']))

    counties = []
    for jud, (code, name) in sorted(COUNTIES.items(), key=lambda kv: ascii_slug(kv[1][1])):
        county_row = next(r for r in rows if r['NIV'] == '1' and number(r['JUD']) == jud)
        seat = next((u for u in uats.values() if u['county'] == code and number(by_siruta[u['siruta']]['TIP']) in (1, 5)), None)
        if code == 'B':
            seat = {'siruta': 179132, 'name': 'București'}
        counties.append({
            'code': code,
            'name': name,
            'siruta': number(county_row['SIRUTA']),
            'region': REGIONS[number(county_row['REGIUNE'])],
            'seat': next((l['uat_name'] for l in localities if l['uat_siruta'] == seat['siruta']), seat['name']) if seat else None,
            'localities': sum(1 for l in localities if l['county'] == code),
        })

    DATA.mkdir(exist_ok=True)
    dump = lambda name, obj: (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    dump('counties.json', counties)
    dump('localities.json', localities)
    (DATA / 'localities.min.json').write_text(json.dumps(
        [[l['siruta'], l['name'], l['county'], l['label'], l['postal_code']] for l in localities],
        ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

    for name, items in (('counties.csv', counties), ('localities.csv', localities)):
        with open(DATA / name, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=list(items[0].keys()))
            writer.writeheader()
            writer.writerows(items)

    sql = ['-- Romania counties and localities. Source: INS SIRUTA + Posta Romana Infocod (data.gov.ro, OGL-ROU-1.0).',
           'CREATE TABLE ro_counties (code VARCHAR(2) PRIMARY KEY, name VARCHAR(40) NOT NULL, siruta INT NOT NULL, region VARCHAR(30) NOT NULL, seat VARCHAR(60));',
           'CREATE TABLE ro_localities (siruta INT PRIMARY KEY, name VARCHAR(80) NOT NULL, label VARCHAR(160) NOT NULL, county VARCHAR(2) NOT NULL, type VARCHAR(30) NOT NULL, urban SMALLINT NOT NULL, uat_siruta INT NOT NULL, uat_name VARCHAR(80), uat_type VARCHAR(20), postal_code CHAR(6));',
           'CREATE INDEX ro_localities_county ON ro_localities (county);']
    q = lambda v: 'NULL' if v is None else str(int(v)) if isinstance(v, bool) else str(v) if isinstance(v, int) else "'" + str(v).replace("'", "''") + "'"
    for c in counties:
        sql.append(f"INSERT INTO ro_counties VALUES ({q(c['code'])}, {q(c['name'])}, {c['siruta']}, {q(c['region'])}, {q(c['seat'])});")
    for i in range(0, len(localities), 500):
        values = ',\n'.join(f"({l['siruta']}, {q(l['name'])}, {q(l['label'])}, {q(l['county'])}, {q(l['type'])}, {q(l['urban'])}, {l['uat_siruta']}, {q(l['uat_name'])}, {q(l['uat_type'])}, {q(l['postal_code'])})"
                           for l in localities[i:i + 500])
        sql.append(f"INSERT INTO ro_localities VALUES\n{values};")
    (DATA / 'romania.sql').write_text('\n'.join(sql) + '\n', encoding='utf-8')

    print(f'{len(counties)} counties, {len(localities)} localities, '
          f"{sum(1 for l in localities if l['postal_code'])} with a single postal code")


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
