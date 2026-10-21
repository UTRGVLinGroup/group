/* Browser integration checks. Requires Playwright and Microsoft Edge (or PLAYWRIGHT_CHANNEL). */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.SITE_TEST_URL || 'http://127.0.0.1:8080/dist/';
const output = path.resolve(__dirname, '../management/qa');
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge', headless: true, args: ['--enable-unsafe-swiftshader'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  // The entire visitor experience must function without third-party requests.
  const externalRequests = [];
  await context.route('**/*', route => {
    if (new URL(route.request().url()).origin === new URL(base).origin) return route.continue();
    externalRequests.push(route.request().url()); return route.abort();
  });
  const page = await context.newPage();
  const errors = [], failed = [];
  page.on('pageerror', error => { errors.push(error.message); console.error('Browser error:',error.message); });
  page.on('response', response => { if (response.status() >= 400) failed.push(response.url()); });
  const pages = ['index','news','research','courses','groups','publications','links','404'];
  for (const width of [1440, 768, 375, 320]) {
    await page.setViewportSize({width,height:1000});
    for (const name of pages) {
      await page.goto(base + name + '.html');
      await page.evaluate(async () => { await Promise.all([...document.images].map(img => { img.loading='eager'; return img.decode().catch(() => {}); })); });
      assert.deepEqual(errors,[],name+': no JavaScript errors');
      assert.equal(await page.locator('h1').count(), 1, name + ': one h1');
      assert.equal(await page.locator('main').count(), 1, name + ': one main');
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), name + ': no overflow at ' + width);
      assert.deepEqual(await page.locator('img').evaluateAll(images => images.filter(img => !img.naturalWidth).map(img => img.src)), [], name + ': images loaded');
      if (width === 1440 && ['index','research','publications','groups'].includes(name)) await page.screenshot({path:path.join(output,name+'-desktop.png'),fullPage: name !== 'publications'});
      if (width === 375 && name === 'index') await page.screenshot({path:path.join(output,'index-mobile.png'),fullPage:true});
    }
  }
  console.log('PASS: 8 pages at desktop, tablet, 375px, and 320px; no overflow or missing images.');

  await page.goto(base+'index.html');
  await page.getByRole('button',{name:'Menu +',exact:true}).click();
  assert.equal(await page.locator('.nav-toggle').getAttribute('aria-expanded'),'true');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('.nav-toggle').getAttribute('aria-expanded'),'false');
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('.resource-menu summary').focus(); await page.keyboard.press('Enter');
  assert.equal(await page.locator('.resource-menu').getAttribute('open'),'');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('.resource-menu').getAttribute('open'),null);
  console.log('PASS: Mobile menu, keyboard resource menu, Escape, and expanded states.');

  await page.goto(base+'publications.html');
  const visible = () => page.locator('.pub-card:visible').count();
  assert.equal(await visible(),60);
  await page.locator('[data-filter="manuscript"]').click(); assert.equal(await visible(),4);
  await page.locator('#pubSearch').fill('radical'); assert.equal(await visible(),2);
  await page.locator('#pubSearch').fill('iodopropyl'); assert.equal(await visible(),1);
  assert(!(await page.locator('.pub-card:visible').innerText()).includes('undefined'));
  await page.locator('[data-filter="published"]').click(); assert.equal(await visible(),0);
  assert(await page.locator('#noResults').isVisible());
  await page.locator('#resetSearch').click(); assert.equal(await visible(),60);
  await page.locator('#pubSearch').fill('Journal of Molecular Spectroscopy'); assert((await visible())>0);
  await page.locator('#resetSearch').click();
  await page.locator('#pubSort').selectOption('oldest');
  const years = await page.locator('.pub-card').evaluateAll(cards => cards.map(c=>Number(c.dataset.year)).filter(Boolean));
  assert.deepEqual(years,[...years].sort((a,b)=>a-b));
  // Exercise success and denied-permission paths without modifying the system clipboard.
  await page.evaluate(() => Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.testCitation=text;}}}));
  await page.locator('.cite-btn').first().click();
  assert((await page.locator('.cite-btn').first().textContent()).includes('copied'));
  assert((await page.evaluate(()=>window.testCitation)).length>20);
  await page.evaluate(() => Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('Permission denied');}}}));
  await page.locator('.cite-btn').nth(1).click();
  assert(await page.locator('.citation-panel textarea').isVisible());
  assert((await page.locator('.citation-panel textarea').inputValue()).length>20);
  await page.getByRole('button',{name:'Close citation',exact:true}).click();
  console.log('PASS: Combined manuscript/search filters, missing metadata, sorting, empty state, reset, and both citation paths.');

  await page.goto(base+'research.html');
  for(let i=1;i<=5;i++) {
    const trigger=page.locator('[data-project="modal'+i+'"]');
    await trigger.focus(); await page.keyboard.press('Enter');
    assert(await page.locator('dialog').isVisible());
    await page.waitForFunction(() => [...document.querySelectorAll('dialog .viewer-controls')].every(el=>!el.hidden),null,{timeout:20000});
    const expected=i===5?2:1;
    assert.equal(await page.locator('dialog canvas').count(),expected);
    await page.locator('dialog [data-view="left"]').first().click();
    await page.locator('dialog [data-view="in"]').first().click();
    await page.locator('dialog [data-view="reset"]').first().click();
    if(i===1) await page.screenshot({path:path.join(output,'research-dialog.png')});
    await page.keyboard.press('Escape'); assert(!(await page.locator('dialog').isVisible()));
    assert.equal(await page.evaluate(()=>document.activeElement.dataset.project),'modal'+i);
  }
  await page.locator('[data-project="modal1"]').click();
  await page.getByRole('button',{name:'Close project details',exact:true}).click();
  await page.setViewportSize({width:375,height:812});
  await page.locator('[data-project="modal5"]').click();
  assert(await page.evaluate(()=>document.querySelector('dialog').scrollWidth<=document.querySelector('dialog').clientWidth+1));
  await page.screenshot({path:path.join(output,'research-dialog-mobile.png')});
  await page.keyboard.press('Escape');
  console.log('PASS: All 5 project dialogs, all 6 WebGL models, rotation/zoom/reset, reopen, mobile dialog, and focus restoration.');
  assert.deepEqual(errors,[],'No uncaught JavaScript errors'); assert.deepEqual(failed,[],'No failed page assets'); assert.deepEqual(externalRequests,[],'No third-party asset dependency');

  const noJS=await browser.newContext({javaScriptEnabled:false,viewport:{width:375,height:812}});
  const simple=await noJS.newPage();
  await simple.goto(base+'publications.html'); assert.equal(await simple.locator('.pub-card:visible').count(),60);
  await simple.goto(base+'research.html'); assert.equal(await simple.locator('.project-detail:visible').count(),5);
  for(const name of ['news','courses','groups']) {
    await simple.goto(base+name+'.html');
    const details=simple.locator('.archive-details'); await details.locator('summary').click();
    assert.equal(await details.getAttribute('open'),'');
  }
  console.log('PASS: Publications, project details, and all 3 archives work with JavaScript disabled.');
  const failure=await browser.newContext();
  await failure.route('**/3Dmol-2.0.4.min.js',route=>route.abort());
  const fallback=await failure.newPage(); await fallback.goto(base+'research.html'); await fallback.locator('[data-project="modal1"]').click();
  await fallback.getByText('The interactive viewer is unavailable in this browser.',{exact:false}).waitFor();
  assert(await fallback.locator('dialog a[download]').isVisible());
  console.log('PASS: Missing viewer library displays a usable fallback and structure download.');
  await browser.close();
  fs.writeFileSync(path.join(output,'browser-results.txt'),'All browser integration checks passed.\nTested '+base+' at 1440, 768, 375, 320px; JS disabled; clipboard denied; viewer unavailable.\n');
})().catch(error=>{console.error(error);process.exit(1);});
