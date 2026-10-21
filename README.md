# Dr. Wei Lin — website ready for static hosting

The site runs as ordinary HTML, CSS, and JavaScript. The hosting server does not need Python, Node.js, a database, or an API key.

## Upload the site

1. Open `website-upload.zip`, or use the `dist` folder.
2. Upload **the contents** to the hosting account's public web directory. `index.html` must sit directly inside that directory. Keep the `assets` and `images` folders and their filenames intact.
3. Enable HTTPS using your hosting provider's controls, then open the site's public address.
4. Check the homepage, navigation, Publications search, and a Research project after uploading. Your provider must serve `.html`, `.css`, `.js`, `.svg`, `.jpg`, `.jpeg`, `.png`, `.json`, and `.sdf` files without rewriting asset requests to the homepage.

For a university account, the destination may be a faculty directory such as `/wei.lin/`. All site links and assets are relative, so the same package works at a domain root or in a subdirectory. Preserve filename capitalization on Linux servers.

The package is prepared locally; it has **not been published**. Back up any existing live site before replacing it. Upload only the package contents, not the entire development folder. Backups, original files, Python environments, scripts, and QA screenshots are intentionally excluded.

## Optional setup for the final web address

Once the final address is known, rebuild with that address to add canonical URLs, social-sharing image URLs, a sitemap, and robots.txt:

```powershell
python scripts/build.py --base-url https://faculty.utrgv.edu/wei.lin/
python scripts/validate.py
```

Replace the example address with the real one. Upload the regenerated package. Use `robots.txt` at the domain root only if you control that domain's crawler configuration; a university server may manage it centrally. Submit the generated sitemap separately if appropriate.

`404.html` is included. If the host supports a custom error document, configure it to use this file **after rebuilding with the final base URL**. That allows its links and styles to work even for missing addresses several folders deep. Without a known base URL, keep the host's default 404 handling. The optional `_headers` file is applied by hosts that support this format; other hosts may ignore it. `.nojekyll` allows the package to be used on GitHub Pages.

## Easy editor (recommended)

Double-click **Wei Lin Website Editor** on the desktop, or **Open Website Editor.cmd** in this folder. Use forms to edit News, Courses, publication records, and existing text/links on other pages. Save, preview, and export from the Overview screen. See [management/START-HERE.md](management/START-HERE.md) for illustrated-by-the-interface steps, backups, and recovery. The editor is private to this computer; it is not included in the public upload.

A Codex weekly task checks the exact Scholar profile on Mondays at 9 AM America/New_York and stages new candidates for approval. Keep Codex running on an awake, connected computer. Review in the editor; nothing is approved or uploaded automatically. The latest check status and any failures appear on Overview. Manage the schedule in Codex.

## Update content manually

- Edit the root HTML files for the biography, news, courses, group, research descriptions, and links.
- Edit `publications.json` and `manuscripts.json` for publication data, then rebuild. Keep full author lists and direct DOI/publisher URLs when available. Retained Scholar links point to exact records on the intended profile.
- Use `assets/site.css` for the shared design, `site.js` for the navigation, and `assets/publications.js` / `assets/research.js` for page interactions.
- Put new research images in `images`, include descriptive `alt` text and the image's width and height in the HTML, and reference paths with `/` rather than Windows backslashes.
- Navigation and footer markup are present in every HTML file so browsing works without JavaScript. Update these consistently across all eight pages when changing shared links.

After changes, run:

```powershell
python scripts/build.py
python scripts/validate.py
python -m http.server 8080 --bind 127.0.0.1
```

Preview at `http://127.0.0.1:8080/dist/`, then upload the regenerated ZIP. Use `--base-url` again on every build if you want the site-specific metadata. Python 3.10 or newer is needed **only on the editing computer**. Never edit `dist` directly; it is generated and stale files are pruned during rebuilding.

The bibliography is a maintained snapshot, not a live Scholar feed. `scraper.py` is an optional local tool that saves a review candidate; it never changes the live publication file. Scholar may limit or block automated access. Review the candidate for completeness and accuracy before replacing `publications.json`. No scraper runs on the web server. The editor and weekly Codex task use `management/editor.py --check` to merge only unseen candidates into the review queue.

## Content dates and research assets

- News was refreshed from the live faculty website through Fall 2026; teaching includes the posted Spring 2027 schedule. Both were checked September 12, 2026. Group records remain as supplied, through Spring 2026.
- The bibliography now contains 56 research outputs and 4 manuscripts/preprints. All 63 entries on the intended Scholar profile (`3SFNLZ4AAAAJ`) were reviewed: two pharmaceutical entries were excluded because their author is identified at Merck, and three duplicate/malformed records were consolidated. Two new spectroscopy preprints were added; two existing manuscripts were confirmed on the faculty page. Record-level decisions and source links are in `management/publication-audit-2026-09-12.json`. Some source metadata remains abbreviated or undated; this is not an independent publisher-level verification of every paper. Review new Scholar imports for namesake errors before accepting them.
- The current department, Ph.D. discipline, and historical University of Texas at Brownsville affiliation were checked against [the existing faculty page](https://faculty.utrgv.edu/wei.lin/index.html).
- Six PubChem reference structures and the pinned 3Dmol.js viewer are bundled locally. Three incorrect compound IDs from the original site were corrected. Model provenance is recorded in `assets/models/sources.json`; the 3Dmol license is included under `assets/vendor`.
- Models are illustrative PubChem geometries, not experimentally fitted structures. Research figures, PubChem links, and SDF downloads remain available if WebGL is unavailable. Publication citations have a manual-copy fallback when clipboard permissions are denied.

## Verification and recovery

`scripts/validate.py` checks generated pages, links, fragments, metadata, image dimensions, model files, and ZIP contents. `scripts/smoke-test.cjs` runs browser integration checks using Playwright and Microsoft Edge. If Playwright is installed in a separate runtime, set `NODE_PATH` to that runtime's `node_modules` directory before running `node scripts/smoke-test.cjs`. Set `PLAYWRIGHT_CHANNEL` to another installed Chromium channel if needed.

Browser tests exercise desktop and mobile layouts, publication filters and sorting, clipboard success and denial, six molecular models, dialog keyboard behavior, disabled JavaScript, missing viewer assets, and operation without external asset requests. Results and preview screenshots are in `management/qa`.

`backups/original-site.zip` preserves the original site and images. The original CSS and JavaScript files at the project root are retained for reference but are not referenced by the new pages or included in the upload. `backups/prepare_site.py` records the one-time migration; do not rerun it after editing the finished pages.
