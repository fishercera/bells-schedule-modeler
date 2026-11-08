"""Builds the published (claude.ai artifact) version of the Bell Schedule Modeler from index.html.

    python build_artifact.py

Writes two files to dist/ (not kept in git):
  dist/bell-schedule-modeler.html  the page to publish. claude.ai wraps a published page in its own
                                   <!doctype html><html><head>...<body>, so those tags (and the charset and
                                   viewport meta tags it also supplies) are left out.
  dist/preview.html                the same page wrapped the way claude.ai wraps it, to try on this computer.

The page also gets the models a new visitor starts with, as JSON in <script id="starter-models">: the Hotchkiss
models listed below and Deerfield, then the app's two built-in samples. People who have used the page before keep
their own saved models.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DIST = ROOT / 'dist'

# The models a new visitor starts with, in this order; the two samples follow them.
HOTCHKISS = [
    'Hotchkiss_Proposals/h-kiss-status-quo-model.json',
    'Hotchkiss_Proposals/h-kiss-block-waterfall-model.json',
    'Hotchkiss_Proposals/h-kiss-block-waterfall-morning-flex--model.json',
    'Hotchkiss_Proposals/h-kiss-block-waterfall-minimize-back-to-back-class--model.json',
]
PEER_FILE, PEERS = 'school-models/all-schools.json', ['Deerfield']

# Lines claude.ai supplies itself. Each must appear exactly once, so a change to index.html's outer tags stops the
# build instead of slipping through.
OUTER = [
    r'<!doctype html>', r'<html lang="en">', r'<head>', r'<meta charset="utf-8">',
    r'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
    r'</head>', r'<body>', r'</body>', r'</html>',
]


def models_of(path):
    data = json.loads((ROOT / path).read_text(encoding='utf-8'))
    return data['models'] if isinstance(data, dict) and 'models' in data else [data]


def main():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    for tag in OUTER:
        found = len(re.findall(rf'^{re.escape(tag)}\s*$', html, flags=re.M | re.I))
        if found != 1:
            sys.exit(f'Expected one line "{tag}" in index.html, found {found}. Update OUTER in build_artifact.py.')
        html = re.sub(rf'^{re.escape(tag)}\s*\n?', '', html, count=1, flags=re.M | re.I)

    starters = [m for p in HOTCHKISS for m in models_of(p)]
    peers = {m['name']: m for m in models_of(PEER_FILE)}
    missing = [n for n in PEERS if n not in peers]
    if missing:
        sys.exit(f'Not found in {PEER_FILE}: {", ".join(missing)}')
    starters += [peers[n] for n in PEERS]
    # "</" is written as "<\/" (still valid JSON) so no model text can end the script element early.
    payload = json.dumps({'models': starters, 'samples': True}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

    marker = '\n<script>\n'
    if html.count(marker) != 1:
        sys.exit('Expected exactly one "<script>" line (the app script) in index.html.')
    html = html.replace(marker, f'\n<script type="application/json" id="starter-models">{payload}</script>{marker}', 1)
    html = html.lstrip()

    DIST.mkdir(exist_ok=True)
    (DIST / 'bell-schedule-modeler.html').write_text(html, encoding='utf-8')
    skeleton = ('<!doctype html><html><head><meta charset=utf8>'
                '<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
                '</head><body>')
    (DIST / 'preview.html').write_text(skeleton + html + '</body></html>', encoding='utf-8')

    size = len(html.encode('utf-8'))
    print(f'dist/bell-schedule-modeler.html: {size / 1024:.0f} KB, starting models: '
          + ', '.join(m['name'] for m in starters) + ', then the 2 samples')


if __name__ == '__main__':
    main()
