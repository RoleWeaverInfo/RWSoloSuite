import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from rwstudio.authoring import blank,npc,review,validate
from rwstudio.authoring_ai import generate
from rwstudio.design_tools import attach_area,area_test_project
from rwstudio.storage import Store

class AreaWorkspaceTests(unittest.TestCase):
 def test_fresh_store_is_empty_workspace_without_examples(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp));rows=store.list()
   self.assertEqual(len(rows),1);self.assertEqual(rows[0]['design_mode'],'area')
   self.assertEqual(store.get(rows[0]['id'])['npcs'],[])
   self.assertEqual(len(Store(Path(tmp)).list()),1)
 def test_no_story_or_quest_required_for_area(self):
  p=blank();p['design_mode']='area'
  self.assertTrue(review(p)['ready']);validate(p,complete=True)
  p['design_mode']='adventure';self.assertFalse(review(p)['ready'])
 def test_generated_area_stays_in_workspace(self):
  p=blank();p['design_mode']='area';provider=Mock();provider.request.return_value=blank()
  result=generate(provider,p,'Populate the room','area','starting_area')['proposal']
  self.assertEqual(result['design_mode'],'area');self.assertEqual(result['quests'],[])
  self.assertEqual(result['story'],'');self.assertTrue(review(result)['ready'])
 def test_attach_copies_and_remaps_collisions_without_changing_source(self):
  p=blank('source_area');p['design_mode']='area';p['npcs']=[npc('guard','Guard','arrival')];p['npcs'][0]['secret']='A hidden identity'
  target=blank('adventure');target['npcs']=[npc('guard','Existing guard','arrival')]
  before=copy.deepcopy(p);original=copy.deepcopy(target)
  result=attach_area(p,'starting_area',target)['proposal']
  self.assertEqual(p,before);self.assertEqual(target,original)
  self.assertEqual(len(result['areas']),2);self.assertNotEqual(result['areas'][0]['id'],result['areas'][1]['id'])
  self.assertNotEqual(result['npcs'][0]['alias'],result['npcs'][1]['alias'])
  self.assertEqual(result['npcs'][1]['room'],result['areas'][1]['rooms'][0]['id'])
  self.assertEqual(result['npcs'][1]['secret'],'A hidden identity');self.assertEqual(result['quests'],target['quests'])
 def test_workspace_target_rejected_and_test_build_is_adventure(self):
  p=blank();p['design_mode']='area'
  with self.assertRaises(ValueError):attach_area(p,'starting_area',p)
  test=area_test_project(p,'starting_area');self.assertEqual(test['design_mode'],'adventure');self.assertTrue(review(test)['ready'])
