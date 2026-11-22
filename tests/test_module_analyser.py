import io
import json
import struct
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from unittest.mock import Mock,patch
from rwstudio.nwn.analysis_formats import Archive,TalkTable,gff
from rwstudio.nwn.gff import write,text
from rwstudio.nwn.script_analysis import analyse,prototypes
from rwstudio.module_analysis import build_report,sha256
from rwstudio.module_analyser import ModuleAnalyser,explain_report
from rwstudio.server import Application,Server,defaults

ROOT=Path(__file__).resolve().parents[1]
ACTIONS={0:{'name':'AddJournalQuestEntry','return':'void','types':['string','int'],'params':['szPlotID','nState']},1:{'name':'OpenStore','return':'void','types':['object','object'],'params':['oStore','oPC']}}
def ncs(code):return b'NCS V1.0\x42'+struct.pack('>I',13+len(code))+code
def integer(n):return b'\x04\x03'+struct.pack('>i',n)
def string(s):
    raw=s.encode('cp1252');return b'\x04\x05'+struct.pack('>H',len(raw))+raw
def action(n,argc):return b'\x05\x00'+struct.pack('>HB',n,argc)
def node(**fields):return (0,fields)
def doc(kind,**fields):return write(kind.encode().ljust(4,b' ')+b'V3.2',node(**fields))
def archive(entries,signature=b'MOD V1.0'):
    count=len(entries);head=bytearray(160);head[:8]=signature
    struct.pack_into('<7I',head,8,0,0,count,160,160,160+24*count,0)
    keys=[];index=[];body=[];offset=160+32*count
    for i,(name,kind,data) in enumerate(entries):
        keys.append(struct.pack('<16sIHH',name.encode(),i,kind,0));index.append(struct.pack('<II',offset,len(data)));body.append(data);offset+=len(data)
    return bytes(head)+b''.join(keys+index+body)
def fixture():
    creature=node(FirstName=(12,text('Mara')),Tag=(10,b'mara'),Conversation=(11,b'mara_talk'),ScriptDialogue=(11,b'quest_start'),Description=(12,text('A cautious keeper who knows the lost seal.')))
    encounter=node(LocalizedName=(12,text('Cave sentries')),Tag=(10,b'sentries'),MaxCreatures=(5,3),RecCreatures=(5,2),CreatureList=(15,[node(ResRef=(11,b'goblin'),CR=(8,1.0))]))
    return archive([
        ('module',2014,doc('IFO',Mod_Name=(12,text('The Lost Seal')),Mod_Description=(12,text('Recover the seal for the queen.')),Mod_OnModLoad=(11,b'quest_start'))),
        ('keep',2012,doc('ARE',Name=(12,text('Old Keep')),Tileset=(11,b'tin01'),Width=(5,4),Height=(5,3))),
        ('keep',2023,write(b'GIT V3.2',(0,{'Creature List':(15,[creature]),'Encounter List':(15,[encounter])}))),
        ('mara',2027,write(b'UTC V3.2',creature)),
        ('module',2056,doc('JRL',Categories=(15,[node(Name=(12,text('Lost Seal')),Tag=(10,b'seal'),EntryList=(15,[node(ID=(4,10),Text=(12,text('Find the seal.')),End=(0,0)),node(ID=(4,20),Text=(12,text('The seal is returned.')),End=(0,1))]))]))),
        ('mara_talk',2029,doc('DLG',StartingList=(15,[node(Index=(4,0),Active=(11,b'check_quest'))]),EntryList=(15,[node(Text=(12,text('The queen needs you to recover our missing seal from the cave.')),Script=(11,b'quest_start'),RepliesList=(15,[node(Index=(4,0))]))]),ReplyList=(15,[node(Text=(12,text('I will help.')))]))),
        ('quest_start',2010,ncs(integer(10)+string('seal')+action(0,2)+b'\x20\x00')),
        ('maybe_quest',2010,ncs(string('seal')+b'\x20\x00')),
    ])
def wait_job(manager,ident):
    end=time.monotonic()+15
    while time.monotonic()<end:
        status=manager.status(ident)
        if status['status'] not in ('copying','analysing','explaining'):return status
        time.sleep(.02)
    raise AssertionError('Job did not finish')

class FormatTests(unittest.TestCase):
    def test_gff_localized_text_and_bad_bounds_cycles(self):
        raw=doc('UTC',FirstName=(12,text('Mara')),Description=(12,struct.pack('<II',12,0)))
        parsed=gff(raw);self.assertEqual(parsed['FirstName']['text'],'Mara');self.assertEqual(parsed['Description']['strref'],12)
        corrupt=bytearray(raw);struct.pack_into('<I',corrupt,8,len(raw)+1)
        with self.assertRaises(ValueError):gff(corrupt)
        cyclic=bytearray(doc('UTC',Self=(14,node())))
        field_offset=struct.unpack_from('<I',cyclic,16)[0];struct.pack_into('<I',cyclic,field_offset+8,0)
        with self.assertRaisesRegex(ValueError,'Cyclic'):gff(cyclic)
        raw=doc('ARE',Height=(8,float('nan')));json.dumps(gff(raw),allow_nan=False)
    def test_archive_index_bounds_and_duplicate_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.mod';path.write_bytes(fixture());a=Archive(path);self.assertEqual(a.get('quest_start',2010)[:8],b'NCS V1.0')
            for raw in (b'garbage',archive([('same',2010,b'a'),('same',2010,b'b')]),fixture()[:-1]):
                path.write_bytes(raw)
                with self.assertRaises(ValueError):Archive(path)
            path.write_bytes(archive([('same',2010,b'a'),('same',2010,b'b')],b'HAK V1.0'));a=Archive(path,allow_duplicates=True)
            self.assertEqual(a.get('same',2010),b'a');self.assertEqual(len(a.duplicates),1)
    def test_talk_table_and_custom_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'tlk').mkdir();entry=bytearray(40);struct.pack_into('<I',entry,0,1);struct.pack_into('<II',entry,28,0,5)
            (root/'tlk/story.tlk').write_bytes(b'TLK V3.0'+struct.pack('<III',0,1,60)+entry+b'Queen')
            self.assertEqual(TalkTable(root/'tlk/story.tlk').get(0),'Queen')
            path=root/'story.mod';path.write_bytes(archive([('module',2014,doc('IFO',Mod_Name=(12,struct.pack('<II',0x01000000,0)),Mod_CustomTlk=(11,b'story'),Mod_HakList=(15,[node(Mod_Hak=(10,b'absent'))])))]))
            report,_=build_report(path,{'user_dir':str(root)},actions=ACTIONS)
            self.assertEqual(report['module']['name'],'Queen');self.assertFalse(report['dependencies'][0]['found']);self.assertTrue(report['dependencies'][1]['found'])

class ScriptTests(unittest.TestCase):
    def test_compiled_only_journal_arguments_and_relative_branch(self):
        body=integer(10)+string('seal')+action(0,2)+b'\x20\x00'
        r=analyse(ncs(body),ACTIONS);self.assertEqual(r['status'],'decoded');self.assertEqual(r['calls'][0]['arguments'],['seal',10]);self.assertIn('AddJournalQuestEntry',r['disassembly'])
        branch=analyse(ncs(b'\x1d\x00'+struct.pack('>i',6)+b'\x20\x00'),ACTIONS)
        self.assertEqual(branch['branches'][0]['target'],19);self.assertEqual(branch['status'],'decoded')
    def test_unknown_calls_do_not_invent_names_and_jumps_clear_argument_values(self):
        r=analyse(ncs(string('seal')+action(55,1)));self.assertEqual(r['calls'][0]['name'],'ACTION_55')
        r=analyse(ncs(integer(10)+string('seal')+b'\x1d\x00'+struct.pack('>i',6)+action(0,2)),ACTIONS)
        self.assertEqual(r['calls'][0]['arguments'],[None,None])
    def test_malformed_and_unsupported_scripts_are_explicit(self):
        with self.assertRaises(ValueError):analyse(b'bad')
        r=analyse(ncs(b'\xff\x00'));self.assertEqual(r['status'],'partial');self.assertIn('Stopped',r['warnings'][0])
        r=analyse(ncs(b'\x04\x05\x00\x12short'));self.assertEqual(r['instructions'],0)
        r=analyse(ncs(b'\x1d\x00'+struct.pack('>i',999)));self.assertIn('not a decoded instruction',r['warnings'][0])

class ReportTests(unittest.TestCase):
    def test_normal_module_is_preserved_and_quest_evidence_is_qualified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'story.mod';path.write_bytes(fixture());before=sha256(path)
            r,details=build_report(path,{},actions=ACTIONS)
            self.assertEqual(sha256(path),before);self.assertEqual(r['counts']['placed_characters'],1);self.assertEqual(r['counts']['encounters'],1);self.assertEqual(r['counts']['dialogues'],1)
            q=r['quests'][0];self.assertEqual(len(q['entries']),2)
            self.assertTrue(any(e.get('journal_entry')==10 for e in q['script_evidence']));self.assertTrue(any('string literal only' in e['finding'] for e in q['script_evidence']))
            self.assertFalse(next(s for s in r['scripts'] if s['id']=='quest_start')['source_available']);self.assertIn('check_quest',r['missing_scripts']);self.assertIn('quest_start',r['characters'][0]['script_refs'])
            self.assertEqual(r['dialogues'][0]['lines'][0]['links'][0]['index'],0);json.dumps(r,allow_nan=False)
    def test_async_import_delete_and_restore_never_touch_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'story.mod';path.write_bytes(fixture());original=path.read_bytes();m=ModuleAnalyser(root/'reports')
            job=m.start(str(path),{});ident=job['id'];self.assertEqual(wait_job(m,ident)['status'],'complete')
            self.assertEqual(path.read_bytes(),original);self.assertEqual(m.report(ident)['module']['filename'],'story.mod')
            self.assertIn('ACTION_',m.script(ident,'quest_start')['disassembly']);self.assertEqual(ModuleAnalyser(root/'reports').list()['analyses'][0]['id'],ident)
            with self.assertRaises(ValueError):m.delete(ident)
            with self.assertRaises(ValueError):m.delete('../story.mod',True)
            with self.assertRaises(ValueError):m.script(ident,'../../story.mod')
            m.delete(ident,True);self.assertEqual(path.read_bytes(),original);self.assertFalse(m.folder(ident).exists())
    def test_dependency_subfolders_and_punctuation_are_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'pack/subfolder').mkdir(parents=True)
            (root/'pack/subfolder/~winter.hak').write_bytes(archive([('mara',2027,doc('UTC',FirstName=(12,text('Mara'))))],b'HAK V1.0'))
            path=root/'story.mod';path.write_bytes(archive([('module',2014,doc('IFO',Mod_Name=(12,text('Winter')),Mod_HakList=(15,[node(Mod_Hak=(10,b'~winter'))])))]))
            m=ModuleAnalyser(root/'reports');j=m.start(str(path),{});self.assertEqual(wait_job(m,j['id'])['status'],'complete')
            self.assertTrue(m.report(j['id'])['dependencies'][0]['found'])
    def test_bad_uploads_and_concurrency(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=ModuleAnalyser(tmp)
            with self.assertRaises(ValueError):m.upload('../evil.mod',io.BytesIO(fixture()),len(fixture()),{})
            with self.assertRaises(ValueError):m.upload('bad.mod',io.BytesIO(b'x'*160),160,{})
            with self.assertRaises(ValueError):m.upload('short.mod',io.BytesIO(b'MOD '),200,{})
            ident=m.begin('one.mod')
            with self.assertRaisesRegex(ValueError,'already running'):m.begin('two.mod')
            with self.assertRaises(ValueError):m.delete(ident,True)
            restored=ModuleAnalyser(tmp);self.assertEqual(restored.status(ident)['status'],'failed')
    def test_ai_is_optional_and_requires_valid_evidence_citations(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.mod';path.write_bytes(fixture());r,_=build_report(path,{},actions=ACTIONS)
            provider=Mock(model='test-model',provider='test');provider.request.return_value={'claims':[{'topic':'Story','text':'The queen requests the seal.','evidence_ids':['E1']}],'uncertainties':['Conditional branches need review.']}
            result=explain_report(r,provider);self.assertEqual(result['claims'][0]['evidence_ids'],['E1']);self.assertIn('untrusted',provider.request.call_args.args[0])
            provider.request.return_value['claims'][0]['evidence_ids']=['invented']
            with self.assertRaisesRegex(ValueError,'unavailable evidence'):explain_report(r,provider)
    def test_installed_engine_ids_and_bundled_compiled_only_evidence(self):
        config=defaults()
        if not config['game_root']:self.skipTest('NWN installation unavailable')
        path=ROOT/'bundled/emberseal/rw_ember_v3.mod';before=sha256(path);r,d=build_report(path,config)
        self.assertEqual(sha256(path),before);self.assertEqual(r['counts']['areas'],3);self.assertEqual(d['aw_acquire']['status'],'decoded')
        self.assertIn('GetModuleItemAcquiredBy',d['aw_acquire']['functions']);self.assertIn('AddJournalQuestEntry',d['aw_acquire']['functions']);self.assertIn('GiveGoldToCreature',d['aw_acquire']['functions'])

class HttpTests(unittest.TestCase):
    def test_upload_session_report_and_read_only_routes(self):
        with tempfile.TemporaryDirectory() as tmp,patch('rwstudio.server.Bridge'):
            app=Application(tmp);app.config={'game_root':'','user_dir':tmp};server=Server(('127.0.0.1',0),app);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();url='http://127.0.0.1:'+str(server.server_port)
            def request(route,body,token=True,content='application/json',origin=None):
                headers={'Content-Type':content}
                if token:headers['X-Studio-Token']=app.token
                if origin:headers['Origin']=origin
                return urllib.request.urlopen(urllib.request.Request(url+route,data=body,headers=headers))
            try:
                for route in ('/?view=analyser','/analyser.js','/analyser.css'):
                    with urllib.request.urlopen(url+route) as response:self.assertEqual(response.status,200)
                for token,origin in ((False,None),(True,'https://elsewhere.example')):
                    with self.assertRaises(urllib.error.HTTPError) as error:request('/api/analyser/upload?filename=test.mod',fixture(),token,'application/octet-stream',origin)
                    self.assertEqual(error.exception.code,403)
                with request('/api/analyser/upload?filename=test.mod',fixture(),content='application/octet-stream') as response:j=json.load(response)
                self.assertEqual(wait_job(app.analyser,j['id'])['status'],'complete')
                with request('/api/analyser/report',json.dumps({'id':j['id']}).encode()) as response:r=json.load(response)
                self.assertEqual(r['module']['name'],'The Lost Seal')
                with urllib.request.urlopen(url+'/api/analyser/disassembly?id='+j['id']+'&script=quest_start') as response:self.assertIn(b'ACTION_0',response.read())
                with self.assertRaises(urllib.error.HTTPError):request('/api/analyser/delete',json.dumps({'id':j['id']}).encode())
                with patch.object(app.authoring_provider,'request') as paid:app.analyser.report(j['id']);paid.assert_not_called()
            finally:server.shutdown();server.server_close();worker.join()

if __name__=='__main__':unittest.main()
