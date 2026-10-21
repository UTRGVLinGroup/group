"""One-time migration of the archived original. Do not rerun after manual edits."""
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from html import escape
import json
import zipfile

ROOT = Path(__file__).resolve().parent.parent
archive = zipfile.ZipFile(ROOT / "backups/original-site.zip")
PHYSICS = "https://www.utrgv.edu/cos/schools-and-departments/physics-and-astronomy/"
SCHOLAR = "https://scholar.google.com/citations?user=3SFNLZ4AAAAJ&amp;hl=en"
PAGES = [('index','Home'),('news','News'),('research','Research'),('courses','Courses'),('groups','Group'),('publications','Publications'),('links','Links')]

def fragment(html):
    return BeautifulSoup(html, "html.parser")

def original(name):
    soup = BeautifulSoup(archive.read(name + '.html').decode('utf-8'), 'html.parser')
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    for el in soup.select('[onclick], [style]'):
        el.attrs.pop('onclick', None)
        el.attrs.pop('style', None)
    for el in soup.select('img'):
        el['src'] = el['src'].replace('\\', '/')
        el['loading'] = 'lazy'
        el['decoding'] = 'async'
    for a in soup.select('a[target="_blank"]'):
        a['rel'] = 'noopener noreferrer'
    return soup

def shell(name, title, description, body, script=''):
    links = ''.join(f'<li><a href="{key}.html"' + (' aria-current="page"' if key == name else '') + f'>{label}</a></li>' for key,label in PAGES)
    nav = f'''<a class="skip-link" href="#main">Skip to content</a>
<div class="institution-bar"><div class="container"><span>The University of Texas Rio Grande Valley</span><span class="location-label">Brownsville, Texas</span></div></div>
<nav class="navbar" aria-label="Main navigation"><div class="nav-container">
<a class="logo" href="index.html"><span class="logo-mark" aria-hidden="true">W</span>Dr. Wei Lin</a>
<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-links">Menu +</button>
<ul class="nav-links" id="primary-links">{links}<li><details class="resource-menu"><summary>Resources</summary><ul>
<li><a href="https://my.utrgv.edu/">My UTRGV</a></li><li><a href="{PHYSICS}">Physics &amp; Astronomy</a></li>
<li><a href="{SCHOLAR}">Google Scholar profile</a></li></ul></details></li></ul></div></nav>'''
    footer = f'''<footer class="footer"><div class="container"><div class="footer-top"><div><span class="footer-name">Dr. Wei Lin</span>
<p>Department of Physics &amp; Astronomy<br>The University of Texas Rio Grande Valley</p></div>
<div class="footer-links"><a href="mailto:wei.lin@utrgv.edu">Email Dr. Lin</a><a href="{SCHOLAR}">Google Scholar ↗</a><a href="{PHYSICS}">Department ↗</a></div></div>
<div class="footer-bottom"><span>© <span data-year>2026</span> Dr. Wei Lin</span><span>Molecular spectroscopy · Physical chemistry</span><a href="#top">Back to top ↑</a></div></div></footer>'''
    html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | Dr. Wei Lin · UTRGV</title><meta name="description" content="{escape(description, quote=True)}"><meta name="theme-color" content="#192c32">
<meta property="og:title" content="{escape(title, quote=True)} | Dr. Wei Lin"><meta property="og:description" content="{escape(description, quote=True)}"><meta property="og:type" content="website"><meta property="og:site_name" content="Dr. Wei Lin · UTRGV">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/site.css">
<script src="site.js" defer></script>{f'<script src="{script}" defer></script>' if script else ''}</head>
<body id="top">{nav}{body}{footer}</body></html>'''
    (ROOT / (name + '.html')).write_text(BeautifulSoup(html,'html.parser').prettify(), encoding='utf-8')

def heading(eyebrow, title, desc):
    return f'<header class="page-header"><div class="container"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{desc}</p></div></header>'

def disclosure(soup, id, text):
    old = soup.find(id=id)
    old['class'] = ['archive-content']
    detail = soup.new_tag('details', attrs={'class':'archive-details'})
    summary = soup.new_tag('summary'); summary.string = text
    old.wrap(detail); detail.insert(0, summary)
    for button in soup.select('.archive-trigger-wrapper'):
        button.decompose()

s = original('index')
s.select_one('.title-tag').string = 'Professor · Department of Physics & Astronomy'
s.select_one('.faculty-name').insert_before(fragment('<span class="eyebrow">Molecular spectroscopy &amp; physical chemistry</span>'))
s.select_one('.title-tag').insert_after(fragment('<p class="hero-description">Exploring molecular structure and motion through high-resolution spectroscopy and quantum chemical calculations.</p><div class="actions"><a class="button" href="research.html">Explore the research <span aria-hidden="true">↗</span></a><a class="button secondary" href="publications.html">View publications</a></div>'))
s.select_one('.hero-image-wrapper').append(fragment('<p class="portrait-caption">Wei Lin, Ph.D. · UTRGV</p>'))
s.select_one('.profile-img')['loading'] = 'eager'
s.select_one('.profile-img')['fetchpriority'] = 'high'
contact = s.select_one('.contact-card').extract()
for p in contact.select('p'):
    if '956-882-5945' in p.get_text(): p.clear(); p.append(fragment('<a href="tel:+19568825945">956-882-5945</a>'))
s.select_one('.bio-text').insert(0, fragment('<p class="lead-text">Dr. Lin studies the structure, interactions, and dynamics of molecules. His research combines rotational spectroscopy with computational methods to investigate hydrogen bonding and molecular motion.</p>'))
for span in s.select('.edu-degree'):
    if 'Ph.D.' in span.text: span.string = 'Ph.D., Chemical Physics'
for item in s.select('.timeline-item'):
    if any(year in item.select_one('.year').text for year in ['2014 – 2015','2009 – 2014']):
        item.select_one('.org').string = 'Dept. of Chemistry and Environmental Sciences, University of Texas at Brownsville'
main = s.main; main['id']='main'; main['tabindex']='-1'
main.append(fragment('<section class="home-feature"><div><h2>Discover the Lin Research Group</h2><p>Research, mentorship, and opportunities in molecular science.</p></div><a class="button" href="groups.html">Meet the group <span aria-hidden="true">↗</span></a></section>'))
shell('index','Molecular Spectroscopy & Physical Chemistry','Wei Lin, professor at UTRGV. Explore molecular spectroscopy research, publications, teaching, and research opportunities.',str(s.select_one('.hero')) + f'<section class="contact-strip" aria-label="Contact information"><div class="container">{contact}</div></section>' + str(main))

for name, label, title, desc, archive_id, archive_text in [
    ('news','From the lab','News &amp; updates','Research milestones, student achievements, and group activities. Latest posted update: Spring 2026.','archive-section','Explore earlier news · 2020–2024'),
    ('courses','Teaching &amp; mentorship','Courses taught','A record of undergraduate and graduate teaching. For current course availability and materials, visit <a href="https://my.utrgv.edu/">My UTRGV</a>.','course-archive','View earlier teaching history · 2020–2024'),
    ('groups','People &amp; opportunities','Lin Research Group','Students and alumni exploring molecular science through spectroscopy and computation.','full-alumni-list','View more undergraduate alumni'),
]:
    s = original(name); main=s.main; main['id']='main'; main['tabindex']='-1'
    disclosure(s,archive_id,archive_text)
    if name == 'groups':
        main.insert(0, fragment('<p class="content-note">Roster information reflects Spring 2026. For current group meetings and research opportunities, <a href="mailto:wei.lin@utrgv.edu">contact Dr. Lin</a>.</p>'))
        s.select_one('.group-section h2').string='Graduate students · Spring 2026'
        graduate=s.select('.recruit-card')[2].p
        graduate.clear(); graduate.append(fragment('Interested in M.Sc. research? <a href="mailto:wei.lin@utrgv.edu?subject=Graduate%20research%20inquiry">Email Dr. Lin about available projects</a>.'))
        for th in s.select('th'): th['scope']='col'
        for table in s.select('table'):
            cap=s.new_tag('caption'); cap.string='Undergraduate alumni and recorded achievements'; table.insert(0,cap)
        for th in s.select('th'):
            if 'Current Position' in th.text: th.string='Recorded distinctions / position'
    if name == 'courses':
        main.insert(0,fragment('<p class="content-note">The most recent entry provided is Spring 2026. This page is a teaching archive; current registration details are available through My UTRGV.</p>'))
        for tag in s.select('.semester-tag'): tag.name='h2'
    text = str(main).replace('committee on ehics','committee on ethics').replace('development leave','developmental leave')
    shell(name,BeautifulSoup(title,'html.parser').text,BeautifulSoup(desc,'html.parser').text,heading(label,title,desc)+text)

s=original('research'); main=s.main; main['id']='main'; main['tabindex']='-1'; s.select_one('.research-header').decompose()
titles=['Chlorosulfonic acid: molecular motion','The structure of 3,4,5-trifluorobenzoic acid','Conformations of 3,5-difluorobenzoic acid','Nuclear coupling in 1,1-diiodoethane','Hydrogen bonding in an acid complex']
teasers=['Resolving tunneling states and large-amplitude OH motion with microwave spectroscopy.','Connecting quantum chemical calculations with measured rotational spectra.','Mapping molecular geometry and conformations through theory and experiment.','Investigating rotational spectra and iodine nuclear quadrupole interactions.','Exploring the structure and dynamics of a fluorinated acid–formic acid complex.']
for i, card in enumerate(s.select('.project-card')):
    card.name='article'; h=card.h3; h.name='h2'; h.string=titles[i]
    h.insert_before(fragment(f'<span class="project-index">PROJECT 0{i+1} / SPECTROSCOPY</span>'))
    card.select_one('.project-teaser').string=teasers[i]
    card.img['alt']='Molecular structure and spectrum for '+titles[i]
    a=card.select_one('.view-more'); a.name='a'; a['href']=f'#modal{i+1}'; a['data-project']=f'modal{i+1}'; a.string='Read project details ↗'; a['aria-label']='Read project details: '+titles[i]
models={24638:('Chlorosulfonic acid',24638),165184:('3,4,5-Trifluorobenzoic acid',853154),75037:('3,5-Difluorobenzoic acid',101265),73752:('1,1-Diiodoethane',68980),385606:('3,3,3-Trifluoro-2-(trifluoromethyl)propanoic acid',385606),284:('Formic acid',284)}
grid=s.select_one('.project-grid')
last=grid
for i, modal in enumerate(list(s.select('.modal'))):
    modal.extract(); modal.name='section'; modal['class']=['project-detail']; modal['aria-labelledby']=f'project-title-{i+1}'
    modal.select_one('.close').decompose(); modal.h2['id']=f'project-title-{i+1}'
    modal.select_one('.modal-main-img')['alt']='Research figure: '+titles[i]
    for viewer in modal.select('.mol-container'):
        name,cid=models[int(viewer['data-cid'])]; viewer.attrs={'id':viewer['id'],'class':['mol-container'],'data-model':f'assets/models/{cid}.sdf','data-name':name,'role':'img','aria-label':f'Interactive molecular structure of {name}'}
        viewer.append(fragment('<p class="model-status">The molecular viewer requires JavaScript and WebGL. The research figure above remains available.</p>'))
        caption=viewer.parent.select_one('.caption'); caption.clear(); caption.append(fragment(f'{escape(name)} · <a href="https://pubchem.ncbi.nlm.nih.gov/compound/{cid}">PubChem CID {cid}</a><br>Drag to rotate; scroll or pinch to zoom. Reference structure, not a fitted experimental geometry.'))
        viewer.parent.append(fragment(f'<div class="viewer-controls" hidden><button type="button" data-view="left" aria-label="Rotate {escape(name)} left">↶</button><button type="button" data-view="right" aria-label="Rotate {escape(name)} right">↷</button><button type="button" data-view="in" aria-label="Zoom in on {escape(name)}">+</button><button type="button" data-view="out" aria-label="Zoom out of {escape(name)}">−</button><button type="button" data-view="reset">Reset view</button></div><p class="caption"><a href="assets/models/{cid}.sdf" download>Download structure (SDF)</a></p>'))
    last.insert_after(modal); last=modal
maintext=str(main).replace('Clsingle bondSsingle bondOsingle bondH','Cl–S–O–H').replace('BrighSpec','BrightSpec').replace('instruemnt','instrument').replace('BLHSB2.918','BLHSB 2.918').replace('alt="Laser System"','alt="Stampede2 computing system at TACC"').replace('3D Model: $','3D Model: ').replace('Propanic Acid','Propanoic Acid')
shell('research','Research','Molecular spectroscopy and quantum chemistry research in the Lin Research Group at UTRGV.',heading('Structure, interactions &amp; dynamics','Research','Investigating molecular structure and motion with high-resolution spectroscopy and quantum chemical calculations.')+maintext,'research.js')

toolbar='''<div class="pub-toolbar"><div class="search-row"><div class="field"><label for="pubSearch">Search publications</label><input id="pubSearch" type="search" placeholder="Title, author, journal, or year" autocomplete="off"></div><div class="field"><label for="pubSort">Sort by</label><select id="pubSort"><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="title">Title A–Z</option></select></div></div><div class="filter-row"><div class="filter-group" role="group" aria-label="Publication type"><button type="button" class="filter-btn" data-filter="all" aria-pressed="true">All work</button><button type="button" class="filter-btn" data-filter="published" aria-pressed="false">Published</button><button type="button" class="filter-btn" data-filter="manuscript" aria-pressed="false">Manuscripts</button></div><button class="reset-btn" type="button" id="resetSearch">Reset filters</button></div></div>'''
shell('publications','Publications','Search publications and manuscripts by Wei Lin and collaborators in molecular spectroscopy and physical chemistry.',heading('Papers &amp; manuscripts','Publications',f'Research from the Lin group and collaborators. <a href="{SCHOLAR}">Visit Google Scholar ↗</a>')+f'<main class="container" id="main" tabindex="-1">{toolbar}<p class="pub-count" id="pubCount" role="status" aria-live="polite"></p><div id="publications-list"><!-- PUBLICATIONS:START --><!-- PUBLICATIONS:END --></div><div class="empty-state" id="noResults" hidden><h2>No matching publications</h2><p>Try another term or reset the filters.</p></div><p class="sr-only" id="citationStatus" role="status"></p></main>','publications.js')

linksrc=BeautifulSoup((ROOT/'backups/original-links.html').read_text(encoding='utf-8'),'html.parser')
alllinks=[(a.get_text(' ',strip=True),a.get('href','')) for a in linksrc.select('a[href]')]
def findurl(term,fallback):
    return next((url for label,url in alllinks if term.lower() in label.lower()),fallback)
sections=[('Conferences',[
('International Symposium on Molecular Spectroscopy',findurl('International Symposium','https://isms.illinois.edu/'),'Meeting information and the latest program.'),
('ACS meetings & events','https://www.acs.org/meetings.html','Conferences across the chemical sciences.'),
('ABRCMS','https://www.abrcms.org/','Research presentations and professional development for students.'),
('SACNAS','https://www.sacnas.org/','Events and resources supporting diversity in STEM.')]),
('Collaborators',[(label.replace('Univeristy','University').replace('Electric Engineering','Electrical Engineering'),url,'') for label,url in alllinks if label.strip().startswith('Professor')]),
('Research resources',[
('PGOPHER','https://pgopher.chm.bris.ac.uk/','Software for rotational, vibrational, and electronic spectra.'),
('PROSPE',findurl('PROSPE','https://info.ifpan.edu.pl/~kisiel/prospe.htm'),'Programs for rotational spectroscopy.'),
('PubChem','https://pubchem.ncbi.nlm.nih.gov/','Molecular structures and chemical information.'),
('Texas Advanced Computing Center','https://tacc.utexas.edu/','Advanced computing resources for research.'),
('Gaussian','https://gaussian.com/','Electronic structure and computational chemistry software.'),
('UTRGV Library','https://www.utrgv.edu/library/','Journal access, databases, and research support. Some services require a university login.')])]
directory=''
for title,items in sections:
    directory+=f'<details class="resource-section" open><summary>{title}</summary><div class="resource-grid">'
    for label,url,desc in items:
        if url.startswith('http://'): url='https://'+url[7:]
        directory+=f'<div class="resource-item"><a href="{escape(url,quote=True)}">{escape(label)} ↗</a>{f"<p>{escape(desc)}</p>" if desc else ""}</div>'
    directory+='</div></details>'
shell('links','Links & Resources','Conferences, collaborators, and molecular spectroscopy resources selected for the Lin Research Group.',heading('Connect &amp; explore','Links &amp; resources','A directory for our research community. Visit conference websites for current dates, locations, and registration.')+f'<main class="container" id="main" tabindex="-1">{directory}</main>')
shell('404','Page not found','The requested page could not be found.',heading('404 · Page not found','Let’s get you back.','The page may have moved, or the address may be incomplete.')+'<main class="container" id="main" tabindex="-1"><a class="button" href="index.html">Return to the homepage</a></main>')
print('Prepared eight pages from the original backup.')
