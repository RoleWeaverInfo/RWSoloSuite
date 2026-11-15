import copy,json,tempfile,unittest
from pathlib import Path
from rwstudio.authoring import validate
from rwstudio.merchants import example,context,ground_quote,defaults
from rwstudio.builder import ROOT,build_project
from rwstudio.storage import Store
from rwstudio.nwn.module_copy import resources
from rwstudio.nwn.gff import read
GAME=Path('D:/SteamLibrary/steamapps/common/Neverwinter Nights')
COMPILER=ROOT/'vendor/nwnsc/nwnsc.exe'
class NativeStoreContextTests(unittest.TestCase):
 def test_older_explicit_price_projects_remain_list_shops(self):
  p=example();p['npcs'][-1]['merchant'].pop('interface');before=copy.deepcopy(p)
  self.assertEqual(validate(p)['npcs'][-1]['merchant']['interface'],'list');self.assertEqual(p,before)
  self.assertEqual(defaults()['interface'],'native')
 def test_native_prices_never_fabricated_and_buybacks_observed(self):
  n=example()['npcs'][-1];n['merchant']['interface']='native'
  snapshot=dict(merchant=dict(npc='bram',available=1,price_mode='native',items=[dict(name='Dagger',quantity=2),dict(name='Dagger',quantity=1),dict(name='Returned silver ring',quantity=1)]))
  shop=context(n,snapshot);self.assertEqual(shop['items'][0]['quantity'],3)
  self.assertNotIn('price',shop['items'][0]);answer=ground_quote('A dagger costs 999 gold','How much are daggers?',shop)
  self.assertNotIn('999',answer);self.assertIn('Returned silver ring',answer);self.assertIn('exact buying and selling prices',answer)
  self.assertNotIn('999',ground_quote('999 gold','Hello',shop))
 def test_no_shop_on_missing_native_observation(self):
  n=example()['npcs'][-1];n['merchant']['interface']='native'
  self.assertFalse(context(n,dict(merchant=dict(npc='bram',available=0,price_mode='native',items=[])))['available'])

@unittest.skipUnless(GAME.is_dir() and COMPILER.is_file(),'NWN/compiler required')
class NativeVisualStoreTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.p=example();cls.p['npcs'][-1]['merchant']['interface']='native'
  cls.m=build_project(cls.p,Store(Path(cls.temp.name)),GAME,COMPILER)
  cls.r={(n,k):v for n,k,v in resources(Path(cls.m['path']).read_bytes())}
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_stock_has_one_authoritative_store_and_no_npc_duplicate(self):
  self.assertEqual(read(self.r['bram',2027])[1][1]['ItemList'][1],[])
  store=read(self.r['aw_store_3',2051])[1][1]
  stock=[i for group in store['StoreList'][1] for i in group[1]['ItemList'][1]]
  self.assertEqual(len(stock),11);self.assertTrue(all(i[1]['Infinite'][1]==0 for i in stock))
  refs=[i[1]['InventoryRes'][1].decode() for i in stock]
  self.assertTrue(all((ref,2025) in self.r for ref in refs))
  git=read(self.r['abbey',2023])[1][1];stores=git['StoreList'][1]
  self.assertEqual(len(stores),1);self.assertEqual(stores[0][1]['Tag'][1],b'aw_store_3')
  self.assertIn('XPosition',stores[0][1]);self.assertEqual(store['MarkUp'][1],100);self.assertEqual(store['MarkDown'][1],35)
 def test_engine_handles_native_trade_and_custom_buy_path_is_blocked(self):
  source=self.r['aw_merchant',2009]
  self.assertIn(b'OpenStore(store,pc,-AWMDiscount(pc,actor),0)',source)
  self.assertIn(b'void AWMBuy(object pc,object actor,int index){if(AWMNative(actor))return;',source)
  native=source[source.index(b'if(AWMNative(actor)){object store='):source.index(b'SetLocalString(pc,"AWM_SESSION"')]
  for command in (b'CopyItem(',b'DestroyObject(',b'TakeGoldFromCreature(',b'CreateObject('):self.assertNotIn(command,native)
  self.assertIn(b'GetFirstItemInInventory(store)',source);self.assertIn(b'"price_mode",JsonString("native")',source)
  self.assertIn(b'!AWInt(shop,"store_missing")',self.r['aw_ct_request',2009])

 def test_native_visual_store_works_without_live_ai(self):
  p=copy.deepcopy(self.p);p['ai_conversations']=False
  m=build_project(p,Store(Path(self.temp.name)/'offline'),GAME,COMPILER)
  entries={(n,k):v for n,k,v in resources(Path(m['path']).read_bytes())}
  self.assertIn(('aw_store_3',2051),entries);self.assertIn(('aw_shop_3_0',2010),entries)
  self.assertNotIn(('sp_inc',2009),entries)
