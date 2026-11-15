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

class NativeUpgradeTests(unittest.TestCase):
 setUpClass=classmethod(native_tasks.NativeCompanionTaskTests.setUpClass.__func__)
 tearDownClass=classmethod(native_tasks.NativeCompanionTaskTests.tearDownClass.__func__)
 def test_real_companion_dialogue_and_native_inventory_compile(self):
  for name in ('aw_cp_talk','aw_cp_orig','aw_cp_visual','aw_ct_transfer'):self.assertIn((name,2010),self.r)
  dlg=read(self.r['aw_cp_native',2029])[1]
  self.assertIn(b'aw_cp_talk',[r[1]['Script'][1] for r in dlg[1]['ReplyList'][1]])
  self.assertIn(b'BeginConversation("aw_cp_native",owner)',self.r['aw_cp_dialog',2009])
  self.assertIn(b'OpenInventory(body,pc)',self.r['aw_cp_ui',2009])
 def test_inspect_and_transfer_use_native_contents_not_ui_open_or_cloning(self):
  self.assertNotIn(b'GetIsOpen(target)',self.r['aw_cp_tasks',2009])
  transfer=self.r['aw_ct_transfer',2009]
  for text in (b'GetDistanceBetween(pc,chest)>3.0',b'matches!=1',b'GetItemStackSize(chosen)!=1',b'GetItemPossessor(item,TRUE)==dest',b'ActionTakeItem(chosen,chest)',b'ActionGiveItem(chosen,chest)'):self.assertIn(text,transfer)
  self.assertNotIn(b'CopyItem(',transfer);self.assertNotIn(b'DestroyObject(',transfer)
 def test_native_door_points_to_real_waypoint(self):
  doors=[];tags=set()
  for a in self.p['areas']:
   git=read(self.r[a['id'],2023])[1]
   doors+=git[1]['Door List'][1]
   tags|={w[1]['Tag'][1] for w in git[1]['WaypointList'][1]}
  self.assertGreaterEqual(len(doors),1)
  for door in doors:self.assertIn(door[1]['LinkedTo'][1],tags)
