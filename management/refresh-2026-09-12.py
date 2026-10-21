"""One-time refresh from saved faculty pages and manually checked Scholar records."""
from pathlib import Path
from bs4 import BeautifulSoup
import html, json, re, shutil

ROOT = Path(__file__).resolve().parent.parent
backup = ROOT / 'backups' / 'before-author-audit-2026-09-12'
backup.mkdir(exist_ok=True)
for name in ['publications.json', 'manuscripts.json', 'news.html', 'courses.html']:
    if not (backup / name).exists(): shutil.copy2(ROOT / name, backup / name)

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

ids = '''u5HHmVD_uO8C d1gkVwhDpl0C u-x6o8ySG0sC IjCSPb-OGe4C RHpTSmoSYBkC IWHjjKOFINEC qxL8FJ1GzNcC 2osOgNQ5qMEC 9yKSN-GCB0IC zYLM7Y9cAGgC 4JMBOYKVnBMC roLk4NBRz8UC qjMakFHDy7sC W7OEmFMy1HYC WF5omc3nYNoC Tyk-4Ss8FVUC UeHWp8X0CEIC eQOLeE2rZwMC TFP_iSt0sucC YsMSGLbcyi4C hC7cP41nSMkC Y0pCki6q_DkC k_IJM867U9cC TQgYirikUcIC 3fE2CSJIrl8C JV2RwH3_ST0C 70eg2SAEIzsC r0BpntZqJG4C j3f4tGmQtD8C _Qo2XoVZTnwC hFOr9nPyWt4C ZHo1McVdvXMC maZDTaKrznsC isC4tDSrTZIC R3hNpaxXUhUC QIV2ME_5wuYC YFjsv_pBGBYC lSLTfruPkqcC M05iB0D1s5AC NaGl4SEjCO4C zA6iFVUQeVQC g5m5HwL7SMYC GnPB-g6toBAC blknAaTinKkC vV6vV6tmYwMC ldfaerwXgEUC BqipwSGYUEgC O3NaXMp0MMsC RGFaLdJalmkC J_g5lzvAfSwC hMod-77fHWUC ns9cj8rnVeAC 35N4QoGY0k4C RYcK_YlVTxYC 3s1wT3WcHBgC SeFeTyx0c_EC 2P1L_qKh6hAC HoB7MX3m0LUC NMxIlDl6LWMC pqnbT2bcN3wC'''.split()
def scholar(sid):
    return 'https://scholar.google.com/citations?view_op=view_citation&hl=en&user=3SFNLZ4AAAAJ&citation_for_view=3SFNLZ4AAAAJ:'+sid

old = json.loads((backup/'publications.json').read_text(encoding='utf-8'))
assert len(old)==len(ids)==60
excluded = {
    31: ('Excluded: author identified at Merck, with Merck email; not verified as the UTRGV professor.', 'https://www.mdpi.com/2813-9380/2/1/2'),
    51: ('Consolidated truncated duplicate into the complete propane-water dimer record.', scholar(ids[30])),
    54: ('Consolidated malformed duplicate into the complete tropolone journal record.', scholar(ids[1])),
    58: ('Consolidated incomplete title and erroneous 1971 date: Scholar description identifies the tropolone conference abstract.', scholar(ids[56])),
}
audit=[]; retained=[]
for i,(row,sid) in enumerate(zip(old,ids)):
    entry={'original_index':i,'record':row,'scholar_record':scholar(sid),'decision':'Retained: listed on intended Scholar profile.'}
    if i in excluded:
        entry['decision'],entry['evidence']=excluded[i]
    else:
        row={**row,'link':scholar(sid),'source_profile':'3SFNLZ4AAAAJ','verified_on':'2026-09-12'}
        if i==59:
            row['authors']='Karla Salazar, Li Zhang, Jinfei Chen, Haoyu Chen, Arnulfo Mar, Wei Lin'
            row['citation']=row['authors']+'. '+row['title']+'. Undated research output; venue not listed in Scholar.'
        retained.append(row)
    audit.append(entry)

new = [
 {'title':'Conformational Structure and Nuclear Quadrupole Interactions of 3-Chloropropionitrile: A Combined Rotational Spectroscopic and Quantum Chemical Study','authors':'Thomas Izo, Yasuki Endo, Wei Lin','year':'2026','journal':'SSRN preprint 7240411 (posted August 5, 2026)','link':'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7240411','scholar_record':scholar('fPk4N6BV_jEC'),'status':'Preprint'},
 {'title':'Rotational Spectroscopy of Pentafluorobenzoic Acid, Pentafluorobenzoic Acid Methyl Ester, and Tetrafluorobenzoic Acid Methyl Ester: Conformational and Structural Insights','authors':'Michael J. Carrillo, Francisco Jimenez, Alitza Gracia, Elizabeth Soehnlen, Zoe Deems, Nicholas Kamuti, Jeffrey Mighion, Michael J. Tubergen, Wei Lin','journal':'SSRN preprint 7286470; date not listed in Scholar','link':'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7286470','scholar_record':scholar('4OULZ7Gr8RgC'),'status':'Preprint'},
]
manuscripts=json.loads((backup/'manuscripts.json').read_text(encoding='utf-8'))
for row in manuscripts: row.update(source='https://faculty.utrgv.edu/wei.lin/publications.html',verified_on='2026-09-12')
for row in new:
    row.update(type='manuscript',source_profile='3SFNLZ4AAAAJ',verified_on='2026-09-12')
    row['citation']=row['authors']+'. '+row['title']+'. '+row['journal']+'.'
    manuscripts.append(row)
    audit.append({'record':row,'scholar_record':row['scholar_record'],'decision':'Added as preprint; full author list checked in Scholar citation detail.'})
audit.append({'record':{'title':'Development of a High-Throughput Size-Exclusion Chromatography–Mass Spectrometry Workflow for Real-Time Monitoring of Bioconjugation of Cysteine-Based Antibody–Drug Conjugates','year':'2026'},'scholar_record':scholar('u_35RYKgDlwC'),'decision':'Excluded new candidate: Wei Lin affiliation is Analytical Research & Development, Merck & Co., Inc., Rahway, NJ. Not verified as the UTRGV professor.','evidence':'https://pubmed.ncbi.nlm.nih.gov/42312960/'})
dump(ROOT/'publications.json',retained)
dump(ROOT/'manuscripts.json',manuscripts)
dump(ROOT/'management/publication-audit-2026-09-12.json',{'profile':'https://scholar.google.com/citations?user=3SFNLZ4AAAAJ&hl=en','reviewed_on':'2026-09-12','profile_identity':'Wei Lin, UTRGV, verified utrgv.edu email, faculty.utrgv.edu/wei.lin homepage','scope':'All 63 expanded profile entries matched; individual publisher affiliation checks for the two pharmaceutical records. Other records checked against profile/coauthor context, not independently publisher-verified. Two existing manuscripts confirmed on faculty publications page.','records':audit})

esc=html.escape
for name in ['news','courses']:
    live=BeautifulSoup((ROOT/f'management/live-{name}-source.html').read_text(encoding='utf-8'),'html.parser')
    source=(ROOT/f'{name}.html').read_text(encoding='utf-8')
    cards=[]
    for card in live.select('.row .column .card'):
        heading=card.h2.get_text(' ',strip=True)
        items=[]
        for li in card.select('ul li'):
            text=' '.join(li.get_text(' ',strip=True).split()).replace('ehics','ethics')
            if name=='news':
                text=esc(text)
                text=re.sub(r'https://authors\.elsevier\.com/\S+',lambda m:f'<a href="{m[0]}" target="_blank" rel="noopener noreferrer">Read the article ↗</a>',text)
                items.append('<li>'+text+'</li>')
            else:
                match=re.match(r'([A-Z]+\s*\d{4})\s*-\s*(.*)',text)
                if match:
                    grad=' class="grad-course"' if 'Graduate Course' in text else ''
                    items.append(f'<li{grad}><strong>{esc(match[1])}</strong> {esc(match[2])}</li>')
                else: items.append('<li>'+esc(text)+'</li>')
        if name=='news':
            cards.append(f'<div class="timeline-block"><h2 class="semester-title">{esc(heading)}</h2><ul class="news-list">'+''.join(items)+'</ul></div>')
        else:
            cards.append(f'<div class="course-card"><h2 class="semester-tag">{esc(heading)}</h2><ul class="course-list">'+''.join(items)+'</ul></div>')
    wrapper='timeline-wrapper' if name=='news' else 'courses-grid'
    note=('Latest posted update: Fall 2026.' if name=='news' else 'The posted schedule includes Spring 2027 (upcoming). Confirm registration details and course availability through My UTRGV.')
    body=f'<p class="content-note">{note} Updated from the <a href="https://faculty.utrgv.edu/wei.lin/{name}.html" target="_blank" rel="noopener noreferrer">faculty website</a> on September 12, 2026.</p>'
    body+=f'<div class="{wrapper}">'+''.join(cards[:6])+'</div>'
    body+=f'<details class="archive-details"><summary>View earlier {"news" if name=="news" else "teaching history"}</summary><div class="archive-content"><div class="{wrapper}">'+''.join(cards[6:])+'</div></div></details>'
    source=re.sub(r'(<main\b[^>]*>).*?(</main>)',lambda m:m[1]+body+m[2],source,flags=re.S)
    if name=='news': source=source.replace('Latest posted update: Spring 2026.','Latest posted update: Fall 2026.')
    else: source=source.replace('Courses taught','Courses &amp; teaching')
    (ROOT/f'{name}.html').write_text(source,encoding='utf-8')
    print(name, len(cards),'semesters')
print('Publication audit:',len(audit),'Scholar records;',len(retained),'research outputs;',len(manuscripts),'manuscripts/preprints')
