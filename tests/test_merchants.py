import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rwstudio.authoring import seed,validate,blank
from rwstudio.merchants import CATALOG,defaults,example,context,ground_quote
from rwstudio.authoring_ai import npc_reply
from rwstudio.provider import Provider
from rwstudio.builder import ROOT,build_project
from rwstudio.storage import Store
from rwstudio.nwn.gff import read
from rwstudio.nwn.module_copy import resources
from rwstudio.nwn.game_assets import GameAssets

GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'

class MerchantTests(unittest.TestCase):
    def test_old_projects_upgrade_without_mutating_input(self):
        p=seed()
        for n in p['npcs']:n.pop('merchant')
        upgraded=validate(p)
        self.assertEqual(upgraded['npcs'][0]['merchant'],defaults())
        self.assertNotIn('merchant',p['npcs'][0])
        upgraded['npcs'][0]['merchant']['stock'].append(dict(item='dagger',quantity=1,price=2))
        self.assertEqual(upgraded['npcs'][1]['merchant']['stock'],[])
    def test_new_adventures_enable_ai_but_example_remains_native(self):
        self.assertTrue(blank()['ai_conversations']);self.assertFalse(seed()['ai_conversations'])
    def test_merchant_limits_and_duplicates(self):
        for field,value in [('haggle_chance',101),('discount_percent',11),('offer_seconds',0)]:
            p=example();p['npcs'][-1]['merchant'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate(p)
        for field,value in [('quantity',0),('quantity',21),('price',0),('price',100001)]:
            p=example();p['npcs'][-1]['merchant']['stock'][0][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):validate(p)
        p=example();p['npcs'][-1]['merchant']['stock'].append(copy.deepcopy(p['npcs'][-1]['merchant']['stock'][0]))
        with self.assertRaisesRegex(ValueError,'only once'):validate(p)
    def test_stock_quotes_require_matching_live_observation(self):
        npc=example()['npcs'][-1]
        self.assertFalse(context(npc,{})['available'])
        self.assertFalse(context(npc,{'merchant':{'npc':'ilyra','available':1}})['available'])
        observed={'merchant':{'npc':'bram','available':1,'haggle_available':1,'items':[{'item':'dagger','quantity':1,'price':7}]}}
        shop=context(npc,observed)
        self.assertEqual(shop['items'][0]['price'],7)
        reply=ground_quote('A thousand gold!','What does a dagger cost?',shop)
        self.assertIn('7 gold each (1 available)',reply);self.assertNotIn('thousand',reply)
        self.assertIn('check my current',ground_quote('I have everything','What do you sell?',context(npc,{})))
    def test_sold_out_and_invalid_stock_are_not_invented(self):
        npc=example()['npcs'][-1]
        shop=context(npc,{'merchant':{'npc':'bram','available':1,'items':[dict(item='dagger',quantity=0,price=2),dict(item='unknown_magic_sword',quantity=99,price=1),dict(item='shortbow',quantity=True,price=30)]}})
        self.assertEqual(len(shop['items']),1)
        self.assertIn('sold out',ground_quote('Have a bow','What is in stock?',shop))
    def test_ai_can_open_shop_but_cannot_pay_or_transfer(self):
        p=example();provider=Provider('unused')
        with patch.object(provider,'request',return_value=dict(reply='I sold it to you.',action='none',story_action='',merchant_action='browse')) as request:
            reply=npc_reply(provider,p,'bram','I would like to buy a dagger.',{'quests':{}})
        self.assertEqual(reply['merchant_action'],'browse');self.assertIn('confirm',reply['reply'])
        self.assertEqual(set(request.call_args.args[2]['properties']['merchant_action']['enum']),{'','browse','haggle'})
        self.assertNotIn('stock',request.call_args.args[1]['npc'].get('merchant',{}))
        with patch.object(provider,'request',return_value=dict(reply='Paid',action='buy',story_action='',merchant_action='buy:dagger')):
            reply=npc_reply(provider,p,'bram','Buy a dagger',{'quests':{}})
        self.assertEqual(reply['merchant_action'],'');self.assertEqual(reply['action'],'none')
    def test_other_npcs_and_disabled_haggling_have_no_capability(self):
        p=example();provider=Provider('unused')
        with patch.object(provider,'request',return_value=dict(reply='Hello',action='none',merchant_action='haggle')) as request:
            reply=npc_reply(provider,p,'ilyra','Haggle',{'quests':{}})
        self.assertEqual(request.call_args.args[2]['properties']['merchant_action']['enum'],['']);self.assertEqual(reply['merchant_action'],'')
        p['npcs'][-1]['merchant']['haggle_enabled']=False
        with patch.object(provider,'request',return_value=dict(reply='No',action='none',merchant_action='haggle')) as request:
            reply=npc_reply(provider,p,'bram','Haggle',{'quests':{}})
        self.assertNotIn('haggle',request.call_args.args[2]['properties']['merchant_action']['enum']);self.assertEqual(reply['merchant_action'],'')

@unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'NWN/compiler required')
class NativeMerchantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.store=Store(Path(cls.temp.name));cls.p=example()
        cls.p['npcs'][0]['dialogue'].append(dict(topic='The final outcome',text='This is only known once the bell quest is complete.',after_quest='bell_fate'))
        cls.manifest=build_project(cls.p,cls.store,GAME,COMPILER)
        cls.res={(n,k):b for n,k,b in resources(Path(cls.manifest['path']).read_bytes())}
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_real_stock_and_both_menu_actions_are_exported(self):
        npc=read(self.res['bram',2027])[1];stock=npc[1]['ItemList'][1]
        self.assertEqual(len(stock),11)
        rows=GameAssets(GAME).get('baseitems',2017).decode('latin1').splitlines()
        columns=next(r.split() for r in rows if 'InvSlotWidth' in r and 'InvSlotHeight' in r)
        sizes={int(r.split()[0]):dict(zip(columns,r.split()[1:])) for r in rows if r.split() and r.split()[0].isdigit()}
        occupied=set()
        for item in stock:
            ref=item[1]['InventoryRes'][1].decode();uti=read(self.res[ref,2025])[1]
            self.assertEqual(uti[1]['StackSize'][1],1);self.assertFalse(uti[1]['Plot'][1])
            size=sizes[uti[1]['BaseItem'][1]];x=item[1]['Repos_PosX'][1];y=item[1]['Repos_Posy'][1]
            cells={(x+dx,y+dy) for dx in range(int(size['InvSlotWidth'])) for dy in range(int(size['InvSlotHeight']))}
            self.assertFalse(cells&occupied);occupied.update(cells)
        dlg=read(self.res['bram',2029])[1];scripts={r[1]['Script'][1] for r in dlg[1]['ReplyList'][1]}
        self.assertIn(b'aw_shop_3_0',scripts);self.assertIn(b'aw_shop_3_1',scripts)
        for script in ('aw_shop_evt','aw_shop_3_0','aw_shop_3_1','sp_chat','sp_select'):self.assertIn((script,2010),self.res)
    def test_shop_is_native_even_with_live_ai_disabled(self):
        p=copy.deepcopy(self.p);p['ai_conversations']=False;m=build_project(p,self.store,GAME,COMPILER)
        res={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
        self.assertIn(('aw_shop_evt',2010),res);self.assertNotIn(('sp_inc',2009),res)
        for (name,kind),raw in res.items():
            if kind==2009:self.assertNotIn(b'NWNX_',raw);self.assertNotIn(b'SqlPrepareQueryCampaign',raw)
    def test_chat_and_shop_state_checks_are_wired_into_runtime(self):
        self.assertIn(b'AWMContext(pc,GetLocalObject(pc,"SP_FOCUS"))',self.res['sp_inc',2009])
        self.assertIn(b'AWM_REQUEST',self.res['sp_inc',2009]);self.assertIn(b'AWMVersion(pc,npc)',self.res['sp_inc',2009])
        self.assertIn(b'shopVerb=="browse" || shopVerb=="haggle"',self.res['sp_inc',2009])
        self.assertIn(b'normal',self.res['sp_select',2009]);self.assertIn(b'SPAddress',self.res['sp_chat',2009])
        self.assertIn(b"state='expired'",self.res['sp_inc',2009])
    def test_active_quest_choice_keeps_menu_and_ai_options(self):
        dlg=read(self.res['ilyra',2029])[1]
        first=dlg[1]['EntryList'][1][0];edges=first[1]['RepliesList'][1]
        self.assertGreater(len(edges),2)
        scripts={dlg[1]['ReplyList'][1][e[1]['Index'][1]][1]['Script'][1] for e in edges}
        self.assertIn(b'sp_select',scripts)
        gated_index=next(i for i,r in enumerate(dlg[1]['ReplyList'][1]) if b'The final outcome' in r[1]['Text'][1])
        links=[e for entry in dlg[1]['EntryList'][1] for e in entry[1]['RepliesList'][1] if e[1]['Index'][1]==gated_index]
        self.assertGreaterEqual(len(links),2)
        self.assertTrue(all(e[1]['Active'][1]==b'awd_0_2' for e in links))
        self.assertIn(b'AQDone("bell_fate")',self.res['awd_0_2',2009])
    def test_delivery_reservation_and_quote_checks_precede_payment(self):
        body=self.res['aw_merchant',2009].decode()
        buy=body[body.index('void AWMBuy('):]
        self.assertLess(buy.index('GetGold(pc)<price'),buy.index('CopyItem('))
        self.assertLess(buy.index('SetLocalInt(item,"AWM_SOLD",TRUE)'),buy.index('CopyItem('))
        self.assertLess(buy.index('if(!GetIsObjectValid(delivered))'),buy.index('TakeGoldFromCreature('))
        self.assertIn('GetLocalInt(pc,"AWM_QUOTE_"',buy);self.assertIn('SetItemStackSize(unit,1)',buy)
        self.assertNotIn('SetItemStackSize(delivered',buy)
        self.assertIn(('aw_escrow',2051),self.res)
        self.assertLess(buy.index('SetItemStackSize(unit,1)'),buy.index('CopyItem(unit,pc,FALSE)'))
        self.assertIn('AWM_SESSION',self.res['aw_shop_evt',2009].decode())

if __name__=='__main__':unittest.main()
