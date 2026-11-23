import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from test_module_analyser import fixture,ACTIONS,archive
from rwstudio.module_analysis import build_report
from rwstudio.imported_module import plan,npc_reply,validate
from rwstudio.conversion_profiles import refresh
from rwstudio.conversion_merchants import add_store_metadata,binding,adapt_runtime,trade_intent,add_trade_dialogues
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
        self.assertEqual(schema['properties']['merchant_action']['enum'],[''])
        self.assertNotIn('native_store',ctx['npc'])
        for verb,message in [('browse','Let us trade'),('haggle','Can we negotiate?')]:
            provider.request.return_value['merchant_action']=verb
            result=npc_reply(provider,self.p,self.n['id'],message,snap)
            self.assertEqual(result['merchant_action'],verb);self.assertEqual(result['action'],'none')
        self.n['merchant']['enabled']=False
        self.assertEqual(npc_reply(provider,self.p,self.n['id'],'Trade',snap)['merchant_action'],'')

    def test_stock_questions_and_backstory_cannot_trigger_shop_actions(self):
        provider=Mock();provider.request.return_value=dict(reply='I grew up trading hides.',merchant_action='browse',companion_action='',task_target='')
        items=[dict(name='Padded armor',quantity=1)]*32+[dict(name='Longsword +2',quantity=1)]
        snap=dict(merchant=dict(npc=self.n['id'],available=1,price_mode='native',items=items))
        for question in ('Tell me your story.','How did you start selling hides?','What is your name?'):
            result=npc_reply(provider,self.p,self.n['id'],question,snap)
            self.assertEqual(result['merchant_action'],'');self.assertEqual(result['reply'],'I grew up trading hides.')
        for question in ('What do you sell in your store?','What have you in stack?','Do you have swords?'):
            result=npc_reply(provider,self.p,self.n['id'],question,snap)
            self.assertEqual(result['merchant_action'],'');self.assertIn('On my shelves:',result['reply'])
        self.assertIn('Longsword +2',result['reply']);self.assertNotIn('Padded armor',result['reply'])
        for message in ("Don't open your store",'If I wanted to buy something','Tell me about your shop','I used to sell hides','How do you haggle?','Can you show me the history of your store?'):
            self.assertEqual(trade_intent(message),'',message)
        for message in ('Show me your inventory','Shoe me your wares.','Let me see your store','Can I buy a sword?','Open your store','Let us trade','Could I see what you have for sale?','Would you mind showing me your merchandise?'):
            self.assertEqual(trade_intent(message),'browse',message)

    def test_trade_shortcut_retains_native_starts_actions_and_gated_paths(self):
        from rwstudio.builder import conversation
        dlg=conversation([('Introduction',[0]),('Quest step',[1]),('Trade?',[1]),('Gated shop',[2])],
                         [('Continue',[1],'quest_update'),('Show your goods',[],'native_trade'),('Secret shop',[],'native_trade')],[(3,'special_gate'),(2,'met_before'),(0,'')])
        set_value(dlg[1]['EntryList'][1][1],'Script',b'quest_update',11)
        set_value(dlg[1]['EntryList'][1][3][1]['RepliesList'][1][0],'Active',b'shop_gate',11)
        raw=write(b'DLG V3.2',dlg);name=self.n['native_store']['conversation']
        d=next(d for d in self.report['dialogues'] if d['id']==name)
        d['lines']=[dict(id=f'{col}:{i}',action=row[1].get('Script',(11,b''))[1].decode(),text='') for col in ('EntryList','ReplyList') for i,row in enumerate(dlg[1][col][1])]
        entries={(name,2029):raw};extras={};scripts={'aw_merchant':'string RWMTradeDialogue(object actor){return "";}'}
        records=add_trade_dialogues(entries,extras,self.report,self.p,scripts,literal,replace)
        self.assertEqual(entries[name,2029],raw)
        self.assertEqual(records[0]['shortcuts'],[dict(entry=2,reply=1,action='native_trade')])
        clone=read(extras[records[0]['dialogue'],2029])[1]
        self.assertEqual(clone[1]['StartingList'],dlg[1]['StartingList'])
        self.assertEqual(clone[1]['ReplyList'],dlg[1]['ReplyList'])
        for i in (0,1,3):self.assertEqual(clone[1]['EntryList'][1][i],dlg[1]['EntryList'][1][i])
        direct=clone[1]['EntryList'][1][2][1]
        self.assertEqual(direct['Script'][1],b'native_trade');self.assertEqual(direct['RepliesList'][1],[])
        self.assertIn(records[0]['dialogue'],scripts['aw_merchant'])

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
        self.assertIn('RWMTradeDialogue(actor)',opening)
        self.assertIn('count<256',s)
        for mutation in ('OpenStore(', 'SetStoreGold(', 'SetStoreMaxBuyPrice(', 'CreateObject(', 'CopyItem(', 'TakeGoldFromCreature(', 'AWMHaggle('):self.assertNotIn(mutation,opening)


if __name__=='__main__':unittest.main()
