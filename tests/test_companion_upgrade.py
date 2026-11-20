import copy
import unittest
from pathlib import Path
from rwstudio.furnishing import room_proposal,ROOM_STYLES
from rwstudio.game_text import response_text
from rwstudio.companion_tasks import example
from rwstudio.companions import context
from rwstudio.task_intent import finish
from test_task_intent import scene
import test_companion_tasks as native_tasks
from rwstudio.nwn.gff import read

class CompanionUpgradeTests(unittest.TestCase):
 def test_take_put_require_native_offer_inventory_permission_and_quantity(self):
  p=example();s=scene()
  for kind in ('take','put'):s['task_targets'].append(dict(s['task_targets'][1],kind=kind))
  ctx=context(p,s)
  self.assertIn('take:chest-instance',[t['id'] for t in ctx['task_targets']])
  for quantity in ('','two',None):
   self.assertEqual(finish(dict(reply='',task_target='take:chest-instance',task_item='potion',task_quantity=quantity),ctx)['task_target'],'')
  result=finish(dict(reply='Already done',task_target='take:chest-instance',task_item='potion',task_quantity='one'),ctx)
  self.assertIn('try',result['reply']);self.assertEqual(result['task_item'],'potion')
  s['companion']['allowed_actions']=[x for x in s['companion']['allowed_actions'] if x!='inventory']
  self.assertNotIn('take',[t['kind'] for t in context(p,s)['task_targets']])
 def test_world_safe_response_preserves_innocent_game_and_identifiers(self):
  text='The game failed to open the Healing supplies cache.'
  self.assertNotIn('game failed',response_text(dict(reply=text))['reply'])
  self.assertEqual(response_text(dict(reply='Fancy a game of cards?',id=text))['id'],text)
  self.assertEqual(response_text(dict(reply='Fancy a game of cards?'))['reply'],'Fancy a game of cards?')
 def test_design_proposals_preserve_story_and_unselected_rooms(self):
  p=example();old=copy.deepcopy(p)
  for style in ROOM_STYLES:
   proposal=room_proposal(p,'guest_hall',style)['proposal']
   for key in ('npcs','items','quests','encounters','connections'):self.assertEqual(proposal[key],p[key])
   self.assertEqual([f for f in proposal['furnishings'] if f['room']!='guest_hall'],[f for f in p['furnishings'] if f['room']!='guest_hall'])
   self.assertLessEqual(len([f for f in proposal['furnishings'] if f['room']=='guest_hall']),4)
  self.assertEqual(p,old)

@unittest.skipUnless(native_tasks.GAME.is_dir() and native_tasks.COMPILER.is_file(),'NWN/compiler required')
class NativeUpgradeTests(unittest.TestCase):
 setUpClass=classmethod(native_tasks.NativeCompanionTaskTests.setUpClass.__func__)
 tearDownClass=classmethod(native_tasks.NativeCompanionTaskTests.tearDownClass.__func__)
 def test_real_companion_dialogue_and_native_inventory_compile(self):
  for name in ('aw_cp_talk','aw_cp_orig','aw_cp_visual','aw_ct_transfer'):self.assertIn((name,2010),self.r)
  dlg=read(self.r['aw_cp_native',2029])[1]
  self.assertIn(b'aw_cp_talk',[r[1]['Script'][1] for r in dlg[1]['ReplyList'][1]])
  self.assertIn(b'BeginConversation("aw_cp_native",owner)',self.r['aw_cp_dialog',2009])
  ui=self.r['aw_cp_ui',2009]
  self.assertIn(b'AWCGridOpen(pc,pack)',ui)
  self.assertIn(b'void AWCInventory(object pc,object body){AWCVisualInventory(pc,body);}',ui)
  self.assertIn(b'Inventory - text list (fallback)',ui)
  visual=ui[ui.index(b'void AWCVisualInventory('):ui.index(b'void AWCInventory(object')]
  self.assertIn(b'AWC_TRANSFER_PENDING',visual);self.assertIn(b'AWT_TRANSFER_PENDING',visual)
  primary=visual[:visual.index(b'void AWCSatchelGrid(')]
  self.assertIn(b'AWCPersistentPack(pc,AWCIdentity(pc,body)',primary)
  self.assertNotIn(b'OpenInventory(pc,pc)',primary);self.assertIn(b'AWCGridOpen(pc,pack)',primary)
  self.assertIn(b'OpenInventory(pc,pc)',visual);self.assertIn(b'AWCSatchel(',visual)
  self.assertIn(b'AWCSatchelGrid(pc,body)',self.r['aw_cp_ui_evt',2009])
  self.assertIn(b'AWCInventoryList(pc,body)',self.r['aw_cp_ui_evt',2009])
 def test_inspect_and_transfer_validate_native_contents_and_split_stacks(self):
  self.assertNotIn(b'GetIsOpen(target)',self.r['aw_cp_tasks',2009])
  transfer=self.r['aw_ct_transfer',2009]
  for text in (b'matches!=1',b'AWCPersistentPack(',b'AWXBegin('):self.assertIn(text,transfer)
  self.assertNotIn(b'GetDistanceBetween(pc,chest)',transfer)
  cargo=self.r['aw_cp_cargo',2009]
  for guard in (b'GetItemPossessor(staged,TRUE)!=escrow',b'after==before+amount',b'GetItemStackSize(original)==remaining',b'if(GetIsObjectValid(staged))',b'SetLocalInt(pc,"AWX_PHASE",-1)'):self.assertIn(guard,cargo)
  self.assertIn(('aw_cp_storage',2051),self.r)
  self.assertNotIn(('aw_cp_pack',2044),self.r)
  self.assertNotIn(b'ActionInteractObject(',self.r['aw_cp_pack',2009])
  self.assertIn(b'OBJECT_TYPE_STORE',self.r['aw_cp_pack',2009])
  self.assertIn(b'GetObjectType(holder)==OBJECT_TYPE_CREATURE && !GetDroppableFlag(item)',self.r['aw_cp_ui',2009])
  self.assertIn(b'SetItemStackSize(item,originalCount-amount)',cargo)
  self.assertIn(b'AWXTick(pc);AWCTransferTick(pc);AWTTick(pc)',self.r['aw_beat',2009])
 def test_visual_grid_uses_owned_items_and_revalidates_drag_transfers(self):
  grid=self.r['aw_cp_grid',2009];give=self.r['aw_cp_give',2009]
  for guard in (b'AWCVisibleItems(pc)',b'AWCVisibleItems(storage)',b'AWCVisibleItems(body)',b'AWG_DRAG_EXP',b'kind!="mousedown" && kind!="mouseup"',b'side!=GetLocalInt(pc,"AWG_DRAG_SIDE")'):self.assertIn(guard,grid)
  for guard in (b'GetItemPossessor(item,TRUE)',b'AWCOwner(body)!=pc',b'AWCItemSafe(item,src)',b'AWXBegin(pc,OBJECT_INVALID'):self.assertIn(guard,give)
  self.assertNotIn(b'OpenInventory(',grid);self.assertNotIn(b'ActionInteractObject(',grid)
 def test_grid_click_keeps_selection_and_excludes_creature_abilities(self):
  grid=self.r['aw_cp_grid',2009]
  self.assertIn(b'if(id=="aw_grid_canvas")return;',grid)
  self.assertIn(b'AWGSelect(pc,selected,selectedSide)',grid)
  self.assertIn(b'GetBaseItemType(item)==BASE_ITEM_CREATUREITEM',grid)
  self.assertIn(b'slot<=INVENTORY_SLOT_CARMOUR',grid)
  self.assertIn(b'AWGIsBelonging(GetObjectByUUID(id),body)',grid)
  self.assertNotIn(b'NuiImage(JsonString("")',grid)
  self.assertIn(b'if(icon!="")draw=',grid)
  texture=self.r['aw_grid_blank',3]
  self.assertEqual(texture[2],2);self.assertEqual(texture[12:18],bytes([1,0,1,0,32,40]))
  self.assertEqual(texture[18:],bytes(4))
 def test_native_door_points_to_real_waypoint(self):
  doors=[];tags=set()
  for a in self.p['areas']:
   git=read(self.r[a['id'],2023])[1]
   doors+=git[1]['Door List'][1]
   tags|={w[1]['Tag'][1] for w in git[1]['WaypointList'][1]}
  self.assertGreaterEqual(len(doors),1)
  for door in doors:
   if door[1]['LinkedToFlags'][1]:self.assertIn(door[1]['LinkedTo'][1],tags)
   else:self.assertEqual(door[1]['LinkedTo'][1],b'')
