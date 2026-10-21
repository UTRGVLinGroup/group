"""Validate the generated upload with the Python standard library."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parent.parent
SITE=ROOT/'dist'
class Document(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.refs=[]; self.images=[]; self.h1=0; self.main=0; self.descriptions=0; self.problems=[]
    def handle_starttag(self,tag,attributes):
        attrs=dict(attributes)
        if attrs.get('id'): self.ids.append(attrs['id'])
        self.h1+=tag=='h1'; self.main+=tag=='main'
        if tag=='meta' and attrs.get('name')=='description': self.descriptions+=bool(attrs.get('content'))
        if tag=='img':
            self.images.append(attrs)
            if not attrs.get('alt') or attrs.get('alt')=='.': self.problems.append('Missing meaningful image alt')
            if not attrs.get('width') or not attrs.get('height'): self.problems.append('Missing image dimensions: '+attrs.get('src',''))
        if tag=='a' and attrs.get('target')=='_blank' and 'noopener' not in attrs.get('rel',''): self.problems.append('Unsafe new tab link')
        for key,value in attrs.items():
            if key.startswith('on'): self.problems.append('Inline event handler')
            if key in ['href','src','data-model'] and value: self.refs.append(value)

def validate():
    errors=[]; documents={}
    for file in SITE.glob('*.html'):
        parser=Document(); parser.feed(file.read_text(encoding='utf-8')); documents[file.name]=parser
        if parser.h1!=1 or parser.main!=1 or parser.descriptions!=1: errors.append(file.name+': heading/main/metadata issue')
        if len(parser.ids)!=len(set(parser.ids)): errors.append(file.name+': duplicate IDs')
        errors.extend(file.name+': '+issue for issue in parser.problems)
    for filename,parser in documents.items():
        for ref in parser.refs:
            if '\\' in ref: errors.append(filename+': Windows path '+ref)
            url=urlsplit(ref)
            if url.scheme in ['http','https','mailto','tel']: continue
            if url.scheme: errors.append(filename+': unsupported URL '+ref); continue
            target=unquote(url.path) or filename
            if target.startswith('/'): errors.append(filename+': root-dependent path '+ref); continue
            if not (SITE/target).is_file(): errors.append(filename+': missing asset '+target)
            if url.fragment and target in documents and unquote(url.fragment) not in documents[target].ids: errors.append(filename+': missing fragment '+ref)
    source=(SITE/'research.html').read_text(encoding='utf-8')
    for item in json.loads((SITE/'assets/models/sources.json').read_text()):
        assert (SITE/f'assets/models/{item["CID"]}.sdf').is_file()
        assert f'assets/models/{item["CID"]}.sdf' in source
    with zipfile.ZipFile(ROOT/'website-upload.zip') as archive:
        zipped=set(archive.namelist()); on_disk={p.relative_to(SITE).as_posix() for p in SITE.rglob('*') if p.is_file()}
        if zipped!=on_disk: errors.append('ZIP does not match dist')
        if any(name.startswith(('backups/','management/','scripts/','.venv/')) for name in zipped): errors.append('Private/development files in upload')
    if errors: print('\n'.join(errors)); return 1
    print(f'PASS: {len(documents)} HTML pages; local links, fragments, image dimensions, metadata, model files, and clean ZIP contents.'); return 0
if __name__=='__main__': sys.exit(validate())
