"""Build a portable static upload. Python 3.10+, standard library only.

Usage: python scripts/build.py [--base-url https://example.edu/wei.lin/]
"""
import argparse
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit, urljoin, quote
import zipfile

ROOT = Path(__file__).resolve().parent.parent
PAGES = ['index.html','news.html','research.html','courses.html','groups.html','publications.html','links.html','404.html']
ESC = lambda value: html.escape(str(value), quote=True)

def publication_records():
    result = []
    for filename, kind in [('publications.json','published'),('manuscripts.json','manuscript')]:
        data = json.loads((ROOT / filename).read_text(encoding='utf-8'))
        if not isinstance(data, list): raise ValueError(f'{filename} must contain an array')
        if kind == 'published' and not data: raise ValueError('Refusing to build an empty publication list')
        for item in data:
            for field in ['title','authors']:
                if not isinstance(item.get(field), str) or not item[field].strip(): raise ValueError(f'Missing {field}: {item}')
            for field in ['year','journal','citation','link']:
                if field in item and not isinstance(item[field], (str, int)): raise ValueError(f'Invalid {field}: {item}')
            record = {**item, 'type':kind}
            link = str(record.get('link',''))
            if link and (urlsplit(link).scheme not in ['https','http'] or not urlsplit(link).netloc): raise ValueError(f'Unsafe publication URL: {link}')
            result.append(record)
    result.sort(key=lambda row: -(int(row.get('year',0)) if str(row.get('year','')).isdigit() else 0))
    return result

def render_publications(records):
    cards=[]
    for index, item in enumerate(records):
        kind=item['type']; dated=str(item.get('year','')); year=dated if dated.isdigit() else ''
        title=item['title']; authors=item['authors']; journal=item.get('journal','')
        citation=item.get('citation') or f"{authors}. {title}. " + (f"{journal}. " if journal else '') + (f"({year})." if year else 'Unpublished manuscript.')
        link=item.get('link','')
        actions=''
        if link:
            label='View Scholar record' if 'scholar.google.com' in urlsplit(link).netloc else ('View preprint' if item.get('status')=='Preprint' else 'View publication')
            actions=f'<a href="{ESC(link)}" target="_blank" rel="noopener noreferrer">{label} ↗</a>'
        badge=('<span class="pub-kind">Preprint · not peer reviewed</span>' if item.get('status')=='Preprint' else '<span class="pub-kind">Manuscript · unpublished</span>') if kind=='manuscript' else ''
        journalhtml=f'<p class="journal-info"><em>{ESC(journal)}</em></p>' if journal else ''
        cards.append(f'''<article class="pub-card" id="paper-{index+1}" data-kind="{kind}" data-year="{year}" data-citation="{ESC(citation)}">
<div class="pub-year-badge">{year or 'Undated'}</div><div class="pub-body">{badge}<h2>{ESC(title)}</h2><p class="authors">{ESC(authors)}</p>{journalhtml}<div class="pub-actions">{actions}<button class="cite-btn" type="button" aria-label="Copy citation: {ESC(title)}">Copy citation</button></div></div></article>''')
    return '\n'.join(cards)

def replace_block(text, name, replacement):
    start, end = f'<!-- {name}:START -->', f'<!-- {name}:END -->'
    if start not in text or end not in text: raise ValueError(f'Missing {name} build markers')
    return text.split(start)[0] + start + '\n' + replacement + '\n' + end + text.split(end)[1]

def build(base_url=''):
    if base_url:
        parsed=urlsplit(base_url)
        if parsed.scheme != 'https' or not parsed.netloc or parsed.query or parsed.fragment: raise ValueError('Base URL must be a full HTTPS directory URL without a query or fragment')
        base_url=base_url.rstrip('/')+'/'
    records=publication_records()
    page=ROOT/'publications.html'
    source=page.read_text(encoding='utf-8')
    source=replace_block(source,'PUBLICATIONS',render_publications(records))
    page.write_text(source,encoding='utf-8')
    research=ROOT/'research.html'
    source=research.read_text(encoding='utf-8')
    models={path:(ROOT/path).read_text(encoding='utf-8') for path in re.findall(r'data-model="([^"]+)"',source)}
    serialized=json.dumps(models,ensure_ascii=True).replace('<','\\u003c')
    block=f'<script id="molecule-data" type="application/json">{serialized}</script>'
    if '<!-- MODELS:START -->' not in source: source=source.replace('</body>','<!-- MODELS:START --><!-- MODELS:END -->\n</body>')
    research.write_text(replace_block(source,'MODELS',block),encoding='utf-8')
    # Resolve the generated output before writing or pruning files.
    output=(ROOT/'dist').resolve()
    if output.parent != ROOT.resolve() or output.name != 'dist' or output.is_symlink(): raise ValueError('Unsafe output directory')
    output.mkdir(exist_ok=True)
    files = PAGES + ['site.js','assets/site.css','assets/publications.js','assets/research.js','assets/favicon.svg','assets/vendor/3Dmol-2.0.4.min.js','assets/vendor/3Dmol-LICENSE.txt','assets/models/sources.json','publications.json','manuscripts.json']
    files += list(models)
    image_paths=set()
    for filename in PAGES:
        source=(ROOT/filename).read_text(encoding='utf-8')
        image_paths.update(re.findall(r'<img[^>]*src="([^"]+)"',source))
    files += sorted(image_paths)
    for filename in files:
        target=output/filename; target.parent.mkdir(parents=True,exist_ok=True)
        if filename.endswith('.html'):
            source=(ROOT/filename).read_text(encoding='utf-8')
            if base_url:
                canonical=urljoin(base_url,filename)
                metadata=f'<link rel="canonical" href="{ESC(canonical)}"><meta property="og:url" content="{ESC(canonical)}"><meta property="og:image" content="{ESC(urljoin(base_url,"images/weilin.jpg"))}">'
                source=source.replace('</head>',metadata+'\n</head>')
                # A host's 404 document can be served at arbitrary nested paths.
                if filename=='404.html': source=source.replace('<head>','<head><base href="'+ESC(base_url)+'">')
            if filename=='404.html': source=source.replace('</head>','<meta name="robots" content="noindex">\n</head>')
            target.write_text(source,encoding='utf-8')
        else: shutil.copy2(ROOT/filename,target)
    (output/'.nojekyll').write_text('',encoding='utf-8')
    # Hosting providers that support this file apply these optional headers.
    (output/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: SAMEORIGIN\n',encoding='utf-8')
    if base_url:
        urls=''.join('<url><loc>'+html.escape(urljoin(base_url,p))+'</loc></url>' for p in PAGES if p!='404.html')
        (output/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls+'</urlset>',encoding='utf-8')
        (output/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+urljoin(base_url,'sitemap.xml')+'\n',encoding='utf-8')
    allowed=set(files+['.nojekyll','_headers']+(['sitemap.xml','robots.txt'] if base_url else []))
    # Reuse directories: OneDrive can prevent removing synced directories even
    # while ordinary file replacement is allowed. Prune only stale build files.
    for old in output.rglob('*'):
        if old.is_file() and old.relative_to(output).as_posix() not in allowed:
            if not old.resolve().is_relative_to(output): raise ValueError('Unsafe generated file')
            old.unlink()
    with zipfile.ZipFile(ROOT/'website-upload.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(output.rglob('*')):
            if file.is_file(): archive.write(file,file.relative_to(output).as_posix())
    print(f'Built {len(PAGES)} pages, {len(records)} works, and {len(models)} verified molecular structures.')
    print('Upload the CONTENTS of dist/ or extract website-upload.zip into the web directory.')
    if not base_url: print('Optional: supply --base-url to include canonical URLs and sitemap.xml for the final address.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--base-url',default=''); args=parser.parse_args(); build(args.base_url)
