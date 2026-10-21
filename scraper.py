"""Optional local Scholar import: produces a candidate for human review.

Never overwrites publications.json. Not required to build or host the website.
Install optional dependencies with: python -m pip install requests beautifulsoup4
"""
import argparse
import json
from pathlib import Path
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
AUTHOR_ID = '3SFNLZ4AAAAJ'

def parse_page(text):
    soup = BeautifulSoup(text, 'html.parser')
    records = []
    for row in soup.select('tr.gsc_a_tr'):
        title_link = row.select_one('a.gsc_a_at')
        details = row.select('div.gs_gray')
        year_tag = row.select_one('.gsc_a_y span')
        if not title_link or len(details) < 1:
            raise ValueError('Scholar markup changed; review the response before importing.')
        title = title_link.get_text(' ', strip=True)
        authors = details[0].get_text(' ', strip=True)
        journal = details[1].get_text(' ', strip=True) if len(details) > 1 else ''
        year = year_tag.get_text(strip=True) if year_tag else ''
        if not title or not authors: raise ValueError('Incomplete Scholar record; import stopped.')
        link=urljoin('https://scholar.google.com',title_link.get('href',''))
        if 'citation_for_view=3SFNLZ4AAAAJ:' not in link:
            raise ValueError('Missing exact citation ID for the intended professor; import stopped.')
        records.append({'title':title, 'authors':authors, 'year':year, 'journal':journal,
                        'type':'published', 'link':link,
                        'citation':f'{authors}. '+(f'({year}). ' if year else '')+f'{title}. {journal}.'})
    return records

def scrape_scholar():
    results = []; seen = set(); page_size = 100
    for page in range(20):
        response = requests.get('https://scholar.google.com/citations',
            params={'user':AUTHOR_ID,'hl':'en','cstart':page*page_size,'pagesize':page_size},
            timeout=30, headers={'User-Agent':'FacultyWebsiteMaintenance/1.0'})
        response.raise_for_status()
        rows = parse_page(response.text)
        if not rows:
            raise ValueError('No publications returned (possibly a block or changed markup). Existing data is untouched.')
        new = 0
        for row in rows:
            key = (row['title'],row['authors'],row['year'])
            if key not in seen: seen.add(key); results.append(row); new += 1
        if not new: raise ValueError('Repeated page detected; refusing a potentially incomplete import.')
        if len(rows) < page_size: return results
        time.sleep(2)
    raise ValueError('Pagination limit reached; refusing a potentially incomplete import.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overwrite-candidate',action='store_true',help='Replace an earlier review candidate (never the live JSON).')
    args = parser.parse_args()
    target = ROOT/'management/publications-candidate.json'
    if target.exists() and not args.overwrite_candidate:
        raise SystemExit('A review candidate already exists. Review it first, or use --overwrite-candidate.')
    try:
        records = scrape_scholar()
    except (requests.RequestException, ValueError) as error:
        raise SystemExit(f'Import stopped: {error}') from error
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Saved {len(records)} records to {target}.')
    print('Review titles, authors, years, links, and completeness before replacing publications.json and rebuilding.')
