import importlib.util, json, tempfile, shutil, unittest, sys, threading, urllib.request, urllib.error
from pathlib import Path
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('editor',SOURCE/'management/editor.py')
editor=importlib.util.module_from_spec(spec); spec.loader.exec_module(editor)
from scraper import parse_page

class EditorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        (self.root/'management').mkdir()
        for name in editor.EDITABLE+['management/publication-audit-2026-09-12.json']:
            if (SOURCE/name).exists(): shutil.copy2(SOURCE/name,self.root/name)
        self.patches=[patch.object(editor,'ROOT',self.root),patch.object(editor,'HERE',self.root/'management')]
        for p in self.patches:p.start()
        editor.write('management/review-queue.json',{'pending':[],'ignored':[],'last_check':None,'last_success':None,'message':'No check yet'})
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        assert self.root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
        self.temp.cleanup()
    def call(self,path,**kwargs): return editor.action(path,{'revision':editor.revision(),**kwargs})
    def candidate(self,ident='new_test_1',title='New spectroscopy test'):
        return {'title':title,'authors':'Wei Lin, Test Author','year':'2026','link':'https://scholar.google.com/citations?view_op=view_citation&citation_for_view=3SFNLZ4AAAAJ:'+ident}
    def test_import_deduplicates_and_preserves_audit_exclusions(self):
        rows=editor.read('publications.json')+[self.candidate(),self.candidate()]
        excluded=self.candidate('ZHo1McVdvXMC','Namesake paper with changed title')
        before=(self.root/'publications.json').read_bytes()
        q=editor.ingest(rows+[excluded]); self.assertEqual(len(q['pending']),1)
        self.assertEqual(before,(self.root/'publications.json').read_bytes())
        self.assertEqual(len(editor.ingest(rows)['pending']),1)
    def test_ignore_survives_future_checks(self):
        row=self.candidate();q=editor.ingest([row]);self.call('review',id=q['pending'][0]['queue_id'],decision='ignore')
        self.assertEqual(editor.ingest([row])['pending'],[])
    def test_approve_and_edit_regenerates_citation(self):
        q=editor.ingest([self.candidate()]);work=q['pending'][0]
        self.call('review',id=work['queue_id'],decision='approve',work={**work,'type':'published'})
        self.assertEqual(editor.queue()['pending'],[])
        pubs=editor.read('publications.json');self.assertEqual(pubs[-1]['title'],work['title'])
        self.call('save-work',collection='published',index=len(pubs)-1,work={**pubs[-1],'title':'Corrected title','type':'manuscript','status':'Preprint'})
        self.assertIn('Corrected title',editor.read('manuscripts.json')[-1]['citation'])
        self.assertNotIn(work['title'],[r['title'] for r in editor.read('publications.json')])
    def test_failed_check_preserves_queue_and_last_success(self):
        editor.ingest([self.candidate()]);before=editor.queue()
        with patch('scraper.scrape_scholar',side_effect=ValueError('Scholar blocked')): result=editor.check_publications()
        self.assertFalse(result['ok']);self.assertEqual(before['pending'],result['pending']);self.assertEqual(before['last_success'],result['last_success'])
    def test_invalid_candidate_is_not_partially_written(self):
        before=editor.queue()
        with self.assertRaises(ValueError):editor.ingest([self.candidate(),{'title':'Invalid'}])
        self.assertEqual(before,editor.queue())
    def test_save_semesters_preserves_entries_and_named_links(self):
        for name in ['news','courses']:
            rows=editor.semesters(name);self.call('save-semesters',page=name,rows=rows)
            actual=editor.semesters(name)
            self.assertEqual([r['semester'] for r in actual],[r['semester'] for r in rows])
            self.assertEqual([len(r['items']) for r in actual],[len(r['items']) for r in rows])
            if name=='news':self.assertEqual(actual[0]['links'],rows[0]['links'])
    def test_new_semester_and_plain_text_escape(self):
        rows=editor.semesters('news');rows.insert(0,{'semester':'Spring 2027','items':['<script>alert(1)</script> https://example.org/paper'],'links':[[]]})
        self.call('save-semesters',page='news',rows=rows)
        source=(self.root/'news.html').read_text(encoding='utf-8')
        self.assertIn('&lt;script&gt;',source);self.assertIn('href="https://example.org/paper"',source)
    def test_stale_save_refused(self):
        before=editor.revision();editor.ingest([self.candidate()])
        with self.assertRaisesRegex(ValueError,'another window'):editor.action('settings',{'revision':before,'base_url':''})
    def test_backup_restore(self):
        original=(self.root/'news.html').read_bytes();name=editor.backup('Test')
        rows=editor.semesters('news');rows[0]['items'][0]='Temporary news';self.call('save-semesters',page='news',rows=rows)
        self.call('restore',name=name)
        self.assertEqual(original,(self.root/'news.html').read_bytes())
    def test_unsafe_link_rejected_without_write(self):
        before=(self.root/'publications.json').read_bytes()
        with self.assertRaises(ValueError):self.call('save-work',collection='published',index=None,work={**self.candidate(),'link':'javascript:alert(1)'})
        self.assertEqual(before,(self.root/'publications.json').read_bytes())
    def test_page_form_preserves_markup_and_link_spacing(self):
        s,fields,refs=editor.page_fields('index')
        before_links=[a.get('href') for a in s.select('a')]
        fields[0]['value']='Edited text'
        self.call('save-page',page='index',fields=fields)
        after,_,_=editor.page_fields('index')
        self.assertEqual(before_links,[a.get('href') for a in after.select('a')]);self.assertIn('Edited text',after.get_text())
    def test_parser_exact_profile(self):
        source='<table><tr class="gsc_a_tr"><td><a class="gsc_a_at" href="/citations?citation_for_view=3SFNLZ4AAAAJ:abc">Title</a><div class="gs_gray">Wei Lin</div><div class="gs_gray">Journal</div></td><td class="gsc_a_y"><span>2026</span></td></tr></table>'
        self.assertIn('citation_for_view=3SFNLZ4AAAAJ:abc',parse_page(source)[0]['link'])
        with self.assertRaises(ValueError):parse_page(source.replace('3SFNLZ4AAAAJ','WRONG_AUTHOR'))
    def test_queue_updates_do_not_mark_public_site_dirty(self):
        before=editor.revision(content_only=True);editor.ingest([self.candidate()])
        self.assertEqual(before,editor.revision(content_only=True))
    def test_http_rejects_cross_origin_and_unauthorized_saves(self):
        server=editor.ThreadingHTTPServer(('127.0.0.1',0),editor.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base='http://127.0.0.1:'+str(server.server_port)
        def request(headers):
            body=json.dumps({'revision':editor.revision(),'base_url':''}).encode()
            req=urllib.request.Request(base+'/api/settings',body,headers={'Content-Type':'application/json',**headers})
            try:
                with urllib.request.urlopen(req) as r:return r.status
            except urllib.error.HTTPError as e:return e.code
        try:
            self.assertEqual(request({}),403)
            self.assertEqual(request({'X-Editor-Token':editor.TOKEN,'Origin':'https://unrelated.example'}),403)
            self.assertEqual(request({'X-Editor-Token':editor.TOKEN,'Origin':base,'Host':'unrelated.example'}),403)
            self.assertEqual(request({'X-Editor-Token':editor.TOKEN,'Origin':base}),200)
        finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
