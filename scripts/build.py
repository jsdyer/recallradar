"""Build the search snapshot from Health Canada and Transport Canada."""
import argparse
from collections import defaultdict
import csv
from datetime import date, datetime, timezone
import gzip
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from product_topics import publish_topics
from public_pages import publish_pages

ROOT = Path(__file__).resolve().parents[1]
HEALTH = 'https://recalls-rappels.canada.ca/sites/default/files/opendata-donneesouvertes/HCRSAMOpenData.json'
TRANSPORT = 'https://opendatatc.tc.canada.ca/vrdb_60days_daily.csv'
HEALTH_FIELDS = ('NID', 'Title', 'URL', 'Organization', 'Product', 'Issue', 'Category', 'Last updated', 'Archived')
TRANSPORT_FIELDS = ('RECALL_NUMBER_NUM', 'MAKE_NAME_NM', 'MODEL_NAME_NM', 'YEAR', 'RECALL_DATE_DTE',
                    'LAST_UPDATE_DATE', 'NOTIFICATION_TYPE_ETXT', 'CATEGORY_ETXT')


def download(url, limit):
    for attempt in range(3):
        try:
            request = Request(url, headers={'User-Agent': 'CoolCode/1.0'})
            with urlopen(request, timeout=35) as response:
                data = response.read(limit + 1)
            if not 0 < len(data) <= limit:
                raise ValueError('Unexpected download size')
            return data
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def clean(value):
    return ' '.join(str(value or '').split())


def iso(value):
    try:
        return date.fromisoformat(clean(value)).isoformat()
    except ValueError:
        return ''


def transport_details(data):
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig'), newline=''))
    if not set(TRANSPORT_FIELDS).issubset(reader.fieldnames or []):
        raise ValueError('Missing fields in Transport Canada CSV.')
    recalls = defaultdict(lambda: {'vehicles': set(), 'types': set(), 'categories': set(), 'date': '', 'updated': ''})
    for row in reader:
        number = clean(row[TRANSPORT_FIELDS[0]])
        if not re.fullmatch(r'[0-9]{7}', number):
            continue
        entry = recalls[number]
        make, model, year = (clean(row[key]) for key in TRANSPORT_FIELDS[1:4])
        if make or model or year:
            entry['vehicles'].add((make, model, year.removesuffix('.0')))
        entry['date'] = max(entry['date'], iso(row[TRANSPORT_FIELDS[4]]))
        entry['updated'] = max(entry['updated'], iso(row[TRANSPORT_FIELDS[5]]))
        for key, field in zip(('types', 'categories'), TRANSPORT_FIELDS[6:]):
            if value := clean(row[field]):
                entry[key].add(value)
    if not recalls:
        raise ValueError('No Transport Canada vehicle notices found.')
    return {number: {key: sorted(value) if isinstance(value, set) else value for key, value in entry.items()}
            for number, entry in recalls.items()}


def merged_snapshot(health, transport):
    incoming = json.loads(health)
    if not isinstance(incoming, list) or len(incoming) < 500 or not set(HEALTH_FIELDS).issubset(incoming[0]):
        raise ValueError('Unexpected Health Canada JSON.')
    items = {}
    matched = set()
    for row in incoming:
        identity, title, url, org, product, issue, category, updated, archived = (
            clean(row.get(key)) for key in HEALTH_FIELDS)
        parsed = urlsplit(url)
        if not identity or not title or parsed.scheme != 'https' or parsed.netloc != 'recalls-rappels.canada.ca':
            continue
        item = {'id': identity, 'title': title, 'url': url, 'org': org, 'product': product, 'issue': issue,
                'category': category, 'updated': iso(updated), 'archived': archived == '1'}
        if org == 'TC' and (match := re.fullmatch(r'Transport Canada Recall - (\d{7}) - .+', title)):
            number = match.group(1)
            item['number'] = number
            if number in transport:
                item['transport'] = transport[number]
                matched.add(number)
        if identity not in items or items[identity]['updated'] < item['updated']:
            items[identity] = item
    if len(items) < 500:
        raise ValueError('Too few valid Health Canada notices.')
    for number, details in transport.items():
        if number not in matched:
            items[f'TC-{number}'] = {'id': f'TC-{number}', 'title': f'Transport Canada recall {number}', 'org': 'TC',
                                     'number': number, 'updated': details['updated'], 'transport': details}
    rows = sorted(items.values(), key=lambda item: (item['updated'], item['id']), reverse=True)
    return {'built': date.today().isoformat(), 'matched': len(matched),
            'transportUpdated': max(row['updated'] for row in transport.values()), 'rows': rows}


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--health-file', type=Path)
    args.add_argument('--transport-file', type=Path)
    sources = args.parse_args()
    health = sources.health_file.read_bytes() if sources.health_file else download(HEALTH, 64 * 1024 ** 2)
    transport_input = sources.transport_file.read_bytes() if sources.transport_file else download(TRANSPORT, 8 * 1024 ** 2)
    retrieved = None
    if not (sources.health_file or sources.transport_file):
        retrieved = datetime.now(timezone.utc).isoformat(timespec='seconds')
    snapshot = merged_snapshot(health, transport_details(transport_input))
    snapshot['retrievedAt'] = retrieved
    output = ROOT / 'dist'
    with tempfile.TemporaryDirectory(dir=ROOT) as work:
        stage = Path(work) / 'site'
        shutil.copytree(ROOT / 'web', stage)
        page = (stage / 'index.html').read_text(encoding='utf-8')
        page = page.replace("<!-- product-categories -->", publish_topics(stage, snapshot))
        publish_pages(stage, page, json.loads((ROOT / 'tool.json').read_text(encoding='utf-8')), snapshot)
        payload = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':')).encode()
        (stage / 'notices.json').write_bytes(payload)
        (stage / 'notices.json.gz').write_bytes(gzip.compress(payload, compresslevel=6, mtime=0))
        status = {key: snapshot[key] for key in ('retrievedAt', 'built', 'transportUpdated', 'matched')}
        status['records'] = len(snapshot['rows'])
        (stage / 'data-status.json').write_text(json.dumps(status) + '\n', encoding='utf-8')
        if output.exists():
            shutil.rmtree(output)
        stage.rename(output)
    print(f"{len(snapshot['rows']):,} notices, with vehicle model details joined to {snapshot['matched']:,} official identifiers")


if __name__ == '__main__':
    main()
