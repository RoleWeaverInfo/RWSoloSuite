import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from test_module_analyser import fixture,ACTIONS,archive
from rwstudio.module_analysis import build_report
from rwstudio.imported_module import plan,npc_reply,validate
from rwstudio.conversion_profiles import refresh
from rwstudio.conversion_merchants import add_store_metadata,binding,adapt_runtime
from rwstudio.nwn.analysis_formats import Archive
from rwstudio.nwn.gff import read,write
from rwstudio.nwn.area_tools import set_value,node
from rwstudio.builder import ROOT,literal
from rwstudio.conversion_runtime import replace


class ImportedMerchants(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'shop.mod';self.path.write_bytes(fixture())
        original=Archive(self.path);entries=[]
        for key in original.index:
            raw=original.get(*key)
            if key==('keep',2023):
                kind,d=read(raw);c=d[1]['Creature List'][1][0]
                set_value(c,'VarTable',[node(0,Name=(10,b'MYSTORE'),Type=(4,3),Value=(10,b'original_shop'))],15)
                set_value(d,'StoreList',[node(0,Tag=(10,b'original_shop'),ResRef=(11,b'different_ref'),StoreGold=(5,321),MarkUp=(5,175))],15)
                raw=write(kind,d)
            entries.append((*key,raw))
        self.path.write_bytes(archive(entries))
        self.report,_=build_report(self.path,{},actions=ACTIONS)
        self.report['scripts'].append(dict(id='native_trade',functions={'OpenStore':1,'GetLocalString':1,'GetNearestObjectByTag':1},calls=[dict(name='GetLocalString',arguments=[0,'MYSTORE'])],literals=[]))
        for c in self.report['characters']:c['script_refs'].append('native_trade')
        self.p=plan(self.report);self.n=self.p['npcs'][0]

    def test_detection_defaults_and_creator_opt_out(self):
        self.assertTrue(self.n['merchant']['enabled']);self.assertTrue(self.n['merchant']['haggle_enabled'])
        self.assertEqual(self.n['merchant']['stock'],[])
        self.assertEqual(self.n['native_store']['tags'],['original_shop'])
        self.assertEqual(self.n['native_store']['variables'],['MYSTORE'])
        self.n['merchant']['enabled']=False
        self.assertFalse(refresh(self.p,self.report)['npcs'][0]['merchant']['enabled'])
        self.assertFalse(binding(dict(self.report,scripts=[]),self.report['characters'][0])['detected'])
        self.n['merchant']['stock']=[dict(item='dagger',quantity=1,price=1)]
        with self.assertRaisesRegex(ValueError,'original native stock'):validate(self.p)

    def test_old_analysis_upgrade_and_transitive_opener(self):
        old=copy.deepcopy(self.report);old.pop('native_stores');old.pop('merchant_metadata_version')
        for c in old['characters']:c.pop('native_store_variables')
        upgraded=add_store_metadata(old,self.path)
        self.assertEqual(binding(upgraded,upgraded['characters'][0])['tags'],['original_shop'])
        c=copy.deepcopy(upgraded['characters'][0]);c['script_refs']=['dispatch']
        upgraded['scripts'].append(dict(id='dispatch',functions={},calls=[dict(name='ExecuteScript',arguments=['native_trade'])]))
        self.assertTrue(binding(upgraded,c)['detected'])

    def test_ai_stock_grounding_and_trade_actions_use_original_menu(self):
        provider=Mock();provider.request.return_value=dict(reply='A mythical sword costs 999 gold.',action='turn_in',merchant_action='',companion_action='',task_target='',task_question='',task_item='',task_quantity='')
        snap=dict(merchant=dict(npc=self.n['id'],available=1,price_mode='native',items=[dict(name='Longsword',quantity=2)]))
        result=npc_reply(provider,self.p,self.n['id'],'What do you sell?',snap)
        self.assertIn('Longsword',result['reply']);self.assertNotIn('999',result['reply']);self.assertNotIn('mythical',result['reply'])
        ctx=provider.request.call_args.args[1];schema=provider.request.call_args.args[2]
        self.assertTrue(ctx['is_merchant']);self.assertEqual(ctx['merchant_stock']['price_mode'],'native')
        self.assertEqual(schema['properties']['merchant_action']['enum'],['','browse','haggle'])
        self.assertNotIn('native_store',ctx['npc'])
        for verb in ('browse','haggle'):
            provider.request.return_value['merchant_action']=verb
            result=npc_reply(provider,self.p,self.n['id'],'Let us trade',snap)
            self.assertEqual(result['merchant_action'],verb);self.assertEqual(result['action'],'none')
        self.n['merchant']['enabled']=False
        self.assertEqual(npc_reply(provider,self.p,self.n['id'],'Trade',snap)['merchant_action'],'')

    def test_native_store_adapter_never_changes_stock_economy_or_bypasses_dialogue(self):
        scripts={'aw_merchant':(ROOT/'authoring_scripts/aw_merchant.nss').read_text(encoding='utf-8')}
        adapt_runtime(scripts,self.p,literal,replace);s=scripts['aw_merchant']
        self.assertIn('AWFind(AWShops(),RWProfile(actor))',s)
        self.assertIn('GetLastOpenedBy(store)==pc',s)
        self.assertIn('GetLastOpenedBy(store)!=pc',s)
        self.assertIn('GetLocalString(actor,JsonGetString(JsonArrayGet(vars,i)))',s)
        self.assertNotIn('GetResRef(store)!=ref',s)
        opening=s[s.index('void AWMOpen('):]
        self.assertIn('ActionStartConversation(pc,dlg,TRUE,FALSE)',opening)
        for mutation in ('OpenStore(', 'SetStoreGold(', 'SetStoreMaxBuyPrice(', 'CreateObject(', 'CopyItem(', 'TakeGoldFromCreature(', 'AWMHaggle('):self.assertNotIn(mutation,opening)


if __name__=='__main__':unittest.main()
