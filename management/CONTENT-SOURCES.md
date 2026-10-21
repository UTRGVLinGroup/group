# Content and asset checks

Checked during launch preparation on September 12, 2026.

Links page follow-up: fetched the live faculty Links page directly (search results contained an older version). All 7 conferences, 6 collaborators, 9 research resources, and 3 university navigation links are included. The source snapshot and destination mapping are in `management/live-links-source.html` and `management/live-links-mapping.json`. Existing PubChem and UTRGV Library entries are retained. Conference details reflect the freshly fetched page. Obsolete collaborator/CDMS addresses use their verified successor pages. The session-specific SciFinder address uses the stable login documented at https://www.cas.org/academic-key-contact-resource-center/faq, with an institutional-access note. All Resources dropdown links use `target="_blank"` and `rel="noopener noreferrer"` across the eight pages.

- Primary faculty information: https://faculty.utrgv.edu/wei.lin/index.html
- Original resource directory: https://faculty.utrgv.edu/wei.lin/links.html (a local copy is preserved in backups/original-links.html).
- Department URL: https://www.utrgv.edu/cos/schools-and-departments/physics-and-astronomy/
- PubChem compound structures: exact names, CIDs, molecular formulas, and source URLs are recorded in assets/models/sources.json. The original IDs 165184, 75037, and 73752 referred to unrelated compounds; they were replaced by 853154, 101265, and 68980 respectively.
- 3Dmol.js 2.0.4: https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.0.4/3Dmol-min.js
- 3Dmol license: https://raw.githubusercontent.com/3dmol/3Dmol.js/2.0.4/LICENSE
- Viewer API documentation: https://3dmol.org/doc/index.html
- Updated collaborator profile addresses: https://scholar.nycu.edu.tw/en/persons/yasuki-endo/ and https://sites.mst.edu/grubbsg/grubbs-bio/

All project descriptions, archived news, course entries, student names, and bibliography records originate from the supplied site. No new news, appointment, student outcome, publication, or meeting schedule was invented. The old Spring 2026 meeting notice has been replaced by a contact link for current arrangements. Current affiliation and two historical institution names were corrected using the faculty page. External website availability is controlled by those providers and can change after these checks.


## September 12 publication, news, and teaching refresh

News and courses were fetched directly from https://faculty.utrgv.edu/wei.lin/news.html and https://faculty.utrgv.edu/wei.lin/courses.html. All 19 semester sections on each live page are included, with the six newest visible and older sections expandable. News extends through Fall 2026; teaching includes Spring 2027, labeled upcoming. Raw snapshots are saved here as live-news-source.html and live-courses-source.html. Only minor spelling/formatting corrections were made. The latest news describes a 3-bromopropionitrile paper; the new Scholar preprint concerns 3-chloropropionitrile. These were kept distinct.

The exact Scholar profile 3SFNLZ4AAAAJ was opened in the browser and expanded to all 63 records. It identifies Wei Lin at UTRGV, with a verified utrgv.edu email and the matching faculty homepage. Every retained research output now links to its exact profile citation instead of a broad title search. All decisions are preserved in publication-audit-2026-09-12.json, including excluded records. The 2025 antibody formulation paper identifies Wei Lin with wei.lin3@merck.com, ORCID 0000-0002-1953-9765, and Merck affiliation: https://www.mdpi.com/2813-9380/2/1/2. The 2026 antibody-drug conjugation paper also identifies Wei Lin at Merck: https://pubmed.ncbi.nlm.nih.gov/42312960/. Both are excluded pending evidence tying them to this professor. Three malformed duplicates were consolidated, including the erroneous 1971 tropolone entry whose Scholar description identifies the 2005 conference abstract. Two SSRN preprints were added with full authors read from Scholar detail pages (7240411 and 7286470). Existing manuscripts were checked against live-publications-source.html. Other entries were matched to the intended profile and coauthor context, not individually verified with every publisher.
