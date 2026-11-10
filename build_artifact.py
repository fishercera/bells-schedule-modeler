"""Builds the starting models and the published (claude.ai artifact) version of the Bell Schedule Modeler.

    python build_artifact.py

Writes:
  starter-models.js                the models someone starts with when nothing is saved in their browser (STARTERS
                                   below). index.html loads it, so this computer starts with the same models as the
                                   published page. It's kept in git; run this script again after changing STARTERS
                                   or one of their files.
  dist/bell-schedule-modeler.html  the page to publish, with starter-models.js written into it. claude.ai wraps a
                                   published page in its own <!doctype html><html><head>...<body>, so those tags (and
                                   the charset and viewport meta tags it also supplies) are left out.
  dist/preview.html                the same page wrapped the way claude.ai wraps it, to try on this computer.
dist/ is not kept in git. People who have used the page before keep their own saved models.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DIST = ROOT / 'dist'

# The models someone starts with, in this order: (file, name of the model in that file). The first one opens first.
STARTERS = [
    ('Hotchkiss_Proposals/h-kiss-status-quo-model.json', "H'kiss Status Quo"),
    ('school-models/all-schools.json', 'Deerfield'),
    ('Hotchkiss_Proposals/h-kiss-block-waterfall-60-min--model.json', "H'kiss Block Waterfall (60-Min)"),
    ('Hotchkiss_Proposals/h-kiss-block-waterfall-morning-flex--model.json', "H'kiss Block Waterfall (Morning Flex)"),
]
STARTER_FILE = 'starter-models.js'
STARTER_TAG = f'<script src="{STARTER_FILE}"></script>'

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


def starters():
    out = []
    for path, name in STARTERS:
        found = [m for m in models_of(path) if m.get('name') == name]
        if len(found) != 1:
            sys.exit(f'Expected one model named "{name}" in {path}, found {len(found)}. Update STARTERS in build_artifact.py.')
        out.append(found[0])
    names = [m['name'].strip().lower() for m in out]
    if len(set(names)) != len(names):
        sys.exit('Two starting models have the same name. Give each one its own name.')
    return out


def starter_js(models):
    # Every "<" is written as "<" (the same string in JavaScript; in JSON it only occurs inside strings), so no
    # model text such as "</script>" or "<!--" can end or confuse the script element when this is written into the
    # published page. ASCII only, so the file reads the same in any encoding.
    payload = json.dumps({'models': models}, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    return ('// The models someone starts with when nothing is saved in their browser. Made by build_artifact.py from '
            'the files in its STARTERS list; edit those and run it again rather than editing this file.\n'
            f'window.STARTER_MODELS = {payload};\n')


def main():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    for tag in OUTER:
        found = len(re.findall(rf'^{re.escape(tag)}\s*$', html, flags=re.M | re.I))
        if found != 1:
            sys.exit(f'Expected one line "{tag}" in index.html, found {found}. Update OUTER in build_artifact.py.')
        html = re.sub(rf'^{re.escape(tag)}\s*\n?', '', html, count=1, flags=re.M | re.I)

    models = starters()
    js = starter_js(models)
    (ROOT / STARTER_FILE).write_text(js, encoding='utf-8', newline='\n')

    if html.count(STARTER_TAG) != 1:
        sys.exit(f'Expected exactly one {STARTER_TAG} in index.html.')
    html = html.replace(STARTER_TAG, f'<script>\n{js}</script>', 1)
    html = html.lstrip()

    DIST.mkdir(exist_ok=True)
    (DIST / 'bell-schedule-modeler.html').write_text(html, encoding='utf-8')
    skeleton = ('<!doctype html><html><head><meta charset=utf8>'
                '<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
                '</head><body>')
    (DIST / 'preview.html').write_text(skeleton + html + '</body></html>', encoding='utf-8')

    size = len(html.encode('utf-8'))
    print(f'{STARTER_FILE}: {len(js.encode("utf-8")) / 1024:.0f} KB. dist/bell-schedule-modeler.html: {size / 1024:.0f} KB. '
          'Starting models: ' + ', '.join(m['name'] for m in models))


if __name__ == '__main__':
    main()
