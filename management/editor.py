"""Private local maintenance app. Run with Python 3.10+; never upload this folder."""
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote
import argparse, hashlib, html, json, mimetypes, os, re, secrets, shutil, subprocess, sys, threading, webbrowser, zipfile
from bs4 import BeautifulSoup, NavigableString, Comment

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'management'
sys.path.insert(0, str(ROOT))
PAGES = ['index', 'news', 'courses', 'groups', 'research', 'links', 'publications', '404']
EDITABLE = [p+'.html' for p in PAGES]+['publications.json','manuscripts.json','management/review-queue.json','management/editor-settings.json']
MUTEX = threading.RLock()
TOKEN = secrets.token_urlsafe(32)

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def read(name, default=None):
    p=ROOT/name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def write(name, value):
    p=ROOT/name; p.parent.mkdir(parents=True,exist_ok=True)
    content=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    tmp=p.with_name(p.name+'.tmp-'+secrets.token_hex(4))
    tmp.write_text(content,encoding='utf-8',newline=''); os.replace(tmp,p)

@contextmanager
def locked():
    with MUTEX:
        with (HERE/'editor.lock').open('a+b') as f:
            f.seek(0); f.write(b'0'); f.flush(); f.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(f.fileno(),msvcrt.LK_LOCK,1)
            else:
                import fcntl
                fcntl.flock(f,fcntl.LOCK_EX)
            try: yield
            finally:
                f.seek(0)
                if os.name=='nt': msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
                else: fcntl.flock(f,fcntl.LOCK_UN)

def revision(content_only=False):
    h=hashlib.sha256()
    for name in EDITABLE:
        if content_only and name=='management/review-queue.json': continue
        if (ROOT/name).exists(): h.update(name.encode()); h.update((ROOT/name).read_bytes())
    return h.hexdigest()

def backup(label):
    folder=ROOT/'backups/editor'; folder.mkdir(parents=True,exist_ok=True)
    name=datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(3)+'.zip'
    with zipfile.ZipFile(folder/name,'w',zipfile.ZIP_DEFLATED) as z:
        for file in EDITABLE:
            if (ROOT/file).exists(): z.write(ROOT/file,file)
        z.writestr('backup-info.json',json.dumps({'label':label,'time':now()}))
    return name

def queue(): return read('management/review-queue.json',{'pending':[], 'ignored':[], 'last_check':None,'last_success':None,'message':'No check has run yet.'})
def key(row): return re.sub(r'\W','',row.get('title','').casefold())
def identity(row):
    for field in ['scholar_record','link']:
        match=re.search(r'citation_for_view=3SFNLZ4AAAAJ:([\w-]+)',row.get(field,''))
        if match: return match[1]
    return row.get('scholar_id','')

def ingest(rows):
    """Stage candidates only. No existing citation can be changed by an import."""
    if not rows: raise ValueError('The source returned no records. Existing publications are unchanged.')
    with locked():
        q=queue(); known_ids=set(); known_titles=set()
        sources=read('publications.json',[])+read('manuscripts.json',[])+q['pending']+q['ignored']
        for entry in read('management/publication-audit-2026-09-12.json',{}).get('records',[]):
            sources.append({**entry.get('record',{}),'scholar_record':entry.get('scholar_record','')})
        for r in sources:
            if identity(r): known_ids.add(identity(r))
            known_titles.add(key(r))
        added=0
        for r in rows:
            if not identity(r): raise ValueError('A source record is missing its exact profile citation ID; import stopped.')
            if identity(r) in known_ids or key(r) in known_titles: continue
            item=validate_work({**r,'type':'manuscript'})
            item.update(queue_id=secrets.token_hex(12),discovered_on=now(),scholar_record=r.get('link',''))
            q['pending'].append(item); known_ids.add(identity(r)); known_titles.add(key(r)); added+=1
        q.update(last_check=now(),last_success=now(),ok=True,message=f'Check complete: {added} new candidate(s). {len(q["pending"])} awaiting review.')
        write('management/review-queue.json',q)
        return q

def check_publications():
    try:
        from scraper import scrape_scholar
        return ingest(scrape_scholar())
    except Exception as exc:
        with locked():
            q=queue(); q.update(last_check=now(),ok=False,message='Publication check could not complete. Existing publications and pending reviews are unchanged. '+str(exc)[:450])
            write('management/review-queue.json',q)
        return q

def safe_url(value, local=False):
    value=str(value).strip()
    if not value: return ''
    u=urlsplit(value)
    if u.scheme in ['https','http'] and u.netloc and not u.username: return value
    if local and u.scheme in ['mailto','tel']: return value
    if local and not u.scheme and not u.netloc and not value.startswith(('/', '\\')) and '..' not in Path(u.path).parts: return value
    raise ValueError('Use a complete https:// link'+(' or an existing relative website link.' if local else '.'))

def text(value, limit=20000):
    if not isinstance(value,str) or len(value)>limit: raise ValueError('Text is missing or too long.')
    return value.strip()

def validate_work(row):
    result={k:v for k,v in row.items() if k in ['title','authors','year','journal','link','type','status','source_profile','verified_on','scholar_record','source','queue_id','discovered_on','scholar_id']}
    for field in ['title','authors']:
        result[field]=text(row.get(field,''))
        if not result[field]: raise ValueError('A publication needs a title and authors.')
    year=str(row.get('year','')).strip()
    if year in ['N/A','Undated']: year=''
    if year and (not year.isdigit() or not 1800<=int(year)<=datetime.now().year+2): raise ValueError('Enter a four-digit publication year or leave it blank.')
    result['year']=year; result['journal']=text(row.get('journal',''))
    result['link']=safe_url(row.get('link',''))
    result['type']=row.get('type','published')
    if result['type'] not in ['published','manuscript']: raise ValueError('Choose a publication type.')
    if result.get('status')!='Preprint': result.pop('status',None)
    citation=f'{result["authors"]}. {result["title"]}. '
    citation+=(result['journal']+'. ' if result['journal'] else '')+(f'({year}).' if year else 'Undated.')
    result['citation']=citation
    return result

def semesters(name):
    s=BeautifulSoup((ROOT/(name+'.html')).read_text(encoding='utf-8'),'html.parser')
    selector='.timeline-block' if name=='news' else '.course-card'
    return [{'semester':c.h2.get_text(' ',strip=True),'items':[li.get_text(' ',strip=True) for li in c.select('li')],
             'links':[[{'text':a.get_text(' ',strip=True),'url':a.get('href','')} for a in li.select('a')] for li in c.select('li')]} for c in s.select(selector)]

def save_semesters(name, rows):
    if not isinstance(rows,list) or not rows: raise ValueError('Keep at least one semester.')
    blocks=[]
    for row in rows:
        title=text(row['semester'],100)
        if not re.fullmatch(r'(Spring|Summer|Fall|Winter) 20\d{2}',title): raise ValueError('Use a semester such as Fall 2026.')
        items=[]
        for i,item in enumerate(row['items']):
            val=text(item)
            if not val: continue
            links=row.get('links',[]); markup=html.escape(val)
            if name=='news':
                # Keep existing named links when their label remains in the edited text.
                for link in (links[i] if i<len(links) else []):
                    label=html.escape(text(link['text'])); url=safe_url(link['url'])
                    if label and label in markup: markup=markup.replace(label,f'<a href="{html.escape(url,quote=True)}" target="_blank" rel="noopener noreferrer">{label}</a>',1)
                # Linkify bare URLs only in text nodes (never inside an existing link).
                fragment=BeautifulSoup(markup,'html.parser')
                for node in list(fragment.find_all(string=True)):
                    if node.parent.name=='a': continue
                    parts=re.split(r'(https?://[^\s<>]+)',str(node))
                    if len(parts)>1:
                        for part in parts:
                            if part.startswith(('http://','https://')):
                                a=fragment.new_tag('a',href=safe_url(html.unescape(part)),target='_blank',rel='noopener noreferrer'); a.string=part; node.insert_before(a)
                            else: node.insert_before(NavigableString(part))
                        node.extract()
                markup=str(fragment)
            else:
                m=re.match(r'([A-Z]+\s*\d{4})\s*(?:-\s*)?(.*)',val)
                if m: markup=f'<strong>{html.escape(m[1])}</strong> '+html.escape(m[2])
            items.append('<li>'+markup+'</li>')
        if not items: raise ValueError('Each semester needs at least one entry.')
        cls,head,ul=('timeline-block','semester-title','news-list') if name=='news' else ('course-card','semester-tag','course-list')
        blocks.append(f'<div class="{cls}"><h2 class="{head}">{html.escape(title)}</h2><ul class="{ul}">'+''.join(items)+'</ul></div>')
    source=(ROOT/(name+'.html')).read_text(encoding='utf-8')
    wrap='timeline-wrapper' if name=='news' else 'courses-grid'
    note=('Latest posted update: '+html.escape(rows[0]['semester'])+'.' if name=='news' else 'Teaching schedule and history. Confirm upcoming course availability and registration through My UTRGV.')
    body=f'<p class="content-note">{note} Last edited {datetime.now():%B %d, %Y}.</p><div class="{wrap}">'+''.join(blocks[:6])+'</div>'
    body+=f'<details class="archive-details"><summary>View earlier {"news" if name=="news" else "teaching history"}</summary><div class="archive-content"><div class="{wrap}">'+''.join(blocks[6:])+'</div></div></details>'
    source=re.sub(r'(<main\b[^>]*>).*?(</main>)',lambda m:m[1]+body+m[2],source,flags=re.S)
    if name=='news': source=re.sub(r'Latest posted update: (?:Spring|Summer|Fall|Winter) 20\d{2}\.',lambda m:'Latest posted update: '+rows[0]['semester']+'.',source)
    write(name+'.html',source)

def page_fields(name):
    if name not in PAGES or name in ['news','courses','publications']: raise ValueError('Choose a supported page.')
    s=BeautifulSoup((ROOT/(name+'.html')).read_text(encoding='utf-8'),'html.parser'); fields=[]; refs=[]
    for node in s.body.descendants:
        if not isinstance(node,NavigableString) or isinstance(node,Comment) or not str(node).strip(): continue
        if node.find_parent(['script','style','nav','footer','button']) or node.find_parent(class_='institution-bar'): continue
        if node.parent.get('aria-hidden')=='true' or node.find_parent(attrs={'aria-hidden':'true'}): continue
        fields.append({'label':node.parent.name.upper(), 'value':str(node).strip(),'kind':'text'}); refs.append((node,None))
    for a in s.select('main a[href], header a[href], .contact-strip a[href]'):
        fields.append({'label':'Link: '+a.get_text(' ',strip=True),'value':a['href'],'kind':'link'}); refs.append((a,'href'))
    for img in s.select('img'):
        fields.append({'label':'Image description','value':img.get('alt',''),'kind':'text'}); refs.append((img,'alt'))
    return s,fields,refs

def build():
    backup('Before preview/export build')
    write('management/last-build.json',{'time':now(),'revision':None})
    result=[]
    args=[sys.executable,str(ROOT/'scripts/build.py')]
    base=read('management/editor-settings.json',{}).get('base_url','')
    if base: args+=['--base-url',base]
    for cmd in [args,[sys.executable,str(ROOT/'scripts/validate.py')]]:
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
        result.append(p.stdout+p.stderr)
        if p.returncode: raise ValueError('Build/check failed. Your saved content is backed up. '+''.join(result))
    write('management/last-build.json',{'time':now(),'revision':revision(content_only=True)})
    return {'message':'Preview and upload ZIP are ready. The live website has not changed.','details':''.join(result)}

def status():
    q=queue(); saved=read('management/last-build.json',{})
    return {'revision':revision(),'queue':q,'settings':read('management/editor-settings.json',{}),'schedule':read('management/weekly-schedule.json',{}),
            'needs_build':saved.get('revision')!=revision(content_only=True), 'last_build':saved.get('time'),
            'backups':[p.name for p in sorted((ROOT/'backups/editor').glob('*.zip'),reverse=True)][:30]}

def action(path,data):
    if path=='check': return {'message':check_publications()['message']}
    with locked():
        if data.get('revision')!=revision(): raise ValueError('The content changed in another window or a weekly check. Reload this section before saving.')
        if path=='build': return build()
        if path=='save-semesters':
            name=data['page']
            if name not in ['news','courses']: raise ValueError('Unknown page.')
            backup('Edit '+name); save_semesters(name,data['rows'])
        elif path=='save-page':
            s,fields,refs=page_fields(data['page'])
            if len(data['fields'])!=len(refs): raise ValueError('Page structure changed. Reload the page editor.')
            values=[]
            for field,original in zip(data['fields'],fields): values.append(safe_url(field['value'],local=True) if original['kind']=='link' else text(field['value']))
            backup('Edit '+data['page'])
            for value,(node,attr) in zip(values,refs):
                if attr: node[attr]=value
                else:
                    original=str(node)
                    prefix=re.match(r'^\s*',original)[0]; suffix=re.search(r'\s*$',original)[0]
                    node.replace_with(NavigableString(prefix+value+suffix))
            write(data['page']+'.html',str(s))
        elif path in ['save-work','delete-work','review']:
            pubs=read('publications.json',[]); manuscripts=read('manuscripts.json',[]); q=queue()
            if path=='review':
                candidate=next((r for r in q['pending'] if r['queue_id']==data['id']),None)
                if candidate is None: raise ValueError('This candidate has already been reviewed.')
                if data['decision']=='approve':
                    item=validate_work({**candidate,**data['work']}); item['verified_on']=datetime.now().date().isoformat()
                    item.pop('queue_id',None)
                    if any(key(r)==key(item) for r in pubs+manuscripts): raise ValueError('This title is already in the bibliography.')
                    (pubs if item['type']=='published' else manuscripts).append(item)
                elif data['decision']=='ignore': q['ignored'].append(candidate)
                else: raise ValueError('Choose Approve or Ignore.')
                q['pending']=[r for r in q['pending'] if r['queue_id']!=data['id']]
            else:
                collection=pubs if data.get('collection')=='published' else manuscripts
                idx=data.get('index')
                if idx is not None and (not isinstance(idx,int) or not 0<=idx<len(collection)): raise ValueError('Publication no longer exists.')
                if path=='delete-work':
                    if idx is None: raise ValueError('Choose an existing publication.')
                    q['ignored'].append(collection.pop(idx))
                else:
                    item=validate_work(data['work'])
                    if idx is not None: collection.pop(idx)
                    if any(key(r)==key(item) for r in pubs+manuscripts): raise ValueError('This title already exists.')
                    (pubs if item['type']=='published' else manuscripts).append(item)
            if not pubs: raise ValueError('Keep at least one research output.')
            backup('Publication '+path)
            write('publications.json',pubs); write('manuscripts.json',manuscripts); write('management/review-queue.json',q)
        elif path=='settings':
            value=safe_url(data.get('base_url',''))
            if value and (not value.startswith('https://') or urlsplit(value).query or urlsplit(value).fragment): raise ValueError('Use the final HTTPS directory address without a query or fragment.')
            backup('Website address'); write('management/editor-settings.json',{'base_url':value})
        elif path=='restore':
            name=data['name']
            if not re.fullmatch(r'\d{8}-\d{6}-[a-f0-9]{6}\.zip',name): raise ValueError('Invalid backup.')
            with zipfile.ZipFile(ROOT/'backups/editor'/name) as z:
                recovered={n:z.read(n).decode('utf-8') for n in z.namelist() if n in EDITABLE}
            backup('Before restoring '+name)
            for n in EDITABLE:
                if n in recovered: write(n,recovered[n])
                elif n=='management/editor-settings.json': write(n,{})
                elif n=='management/review-queue.json': write(n,{'pending':[],'ignored':[],'last_check':None,'last_success':None,'message':'Restored backup predates the first publication check.'})
            return {'message':'Backup restored. Build a preview before uploading.'}
        else: raise ValueError('Unknown action.')
        return {'message':'Saved on this computer. Preview or export when ready.'}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def reply(self,code,body,kind='application/json'):
        payload=json.dumps(body).encode() if kind=='application/json' else (body.encode() if isinstance(body,str) else body)
        self.send_response(code); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(payload)))
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer'); self.end_headers(); self.wfile.write(payload)
    def valid_host(self): return self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}'
    def do_GET(self):
        if not self.valid_host(): return self.reply(403,{'error':'This editor is available only through its local shortcut.'})
        path=unquote(urlsplit(self.path).path)
        try:
            if path=='/':
                content=(HERE/'editor.html').read_text(encoding='utf-8').replace('__TOKEN__',TOKEN)
                return self.reply(200,content,'text/html; charset=utf-8')
            if path=='/api/status':
                with locked(): return self.reply(200,status())
            if path.startswith('/api/page/'):
                name=path.rsplit('/',1)[1]
                with locked():
                    data={'revision':revision()}
                    if name in ['news','courses']: data['rows']=semesters(name)
                    elif name=='publications': data.update(published=read('publications.json',[]),manuscript=read('manuscripts.json',[]))
                    else: data['fields']=page_fields(name)[1]
                    return self.reply(200,data)
            if path in ['/editor.js','/editor.css']: p=HERE/path[1:]
            elif path=='/download':
                if read('management/last-build.json',{}).get('revision')!=revision(content_only=True): raise ValueError('Content has changed. Create a new upload ZIP first.')
                p=ROOT/'website-upload.zip'
            elif path.startswith('/preview/'):
                p=(ROOT/'dist'/path[len('/preview/'):]).resolve()
                if not p.is_relative_to((ROOT/'dist').resolve()): return self.reply(403,{'error':'Invalid path.'})
            else: return self.reply(404,{'error':'Not found.'})
            if not p.is_file(): return self.reply(404,{'error':'File not found. Build a preview first.'})
            return self.reply(200,p.read_bytes(),mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
        except Exception as e: self.reply(400,{'error':str(e)})
    def do_POST(self):
        origin=f'http://127.0.0.1:{self.server.server_port}'
        if not self.valid_host() or self.headers.get('Origin') not in [None,origin] or self.headers.get('X-Editor-Token')!=TOKEN:
            return self.reply(403,{'error':'Open the editor from its local shortcut.'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<2_000_000: raise ValueError('Request too large or empty.')
            if self.headers.get('Content-Type')!='application/json': raise ValueError('Expected JSON.')
            data=json.loads(self.rfile.read(length))
            path=urlsplit(self.path).path
            if not path.startswith('/api/'): raise ValueError('Unknown action.')
            result=action(path[5:],data)
            with locked(): result['state']=status()
            self.reply(200,result)
        except Exception as e: self.reply(400,{'error':str(e)})

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); parser.add_argument('--stage-candidates',type=Path); parser.add_argument('--no-browser',action='store_true'); parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    if args.stage_candidates:
        rows=json.loads(args.stage_candidates.read_text(encoding='utf-8'))
        if not isinstance(rows,list): raise SystemExit('Expected an array of exact-profile citation records.')
        print(ingest(rows)['message']); return 0
    if args.check:
        q=check_publications(); print(q['message']); return 0 if q.get('ok') else 1
    try: server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError:
        # Reuse only a verified instance of this app.
        import urllib.request
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/api/status',timeout=2) as r: existing=json.load(r)
            if 'needs_build' not in existing or 'queue' not in existing: raise ValueError()
            if not args.no_browser: webbrowser.open(f'http://127.0.0.1:{args.port}/')
            return 0
        except Exception: raise SystemExit('The editor port is in use. Close the other program or run with --port 8766.')
    if not args.no_browser: webbrowser.open(f'http://127.0.0.1:{args.port}/')
    print(f'Website editor: http://127.0.0.1:{args.port}/',flush=True)
    server.serve_forever()

if __name__=='__main__': sys.exit(main())
