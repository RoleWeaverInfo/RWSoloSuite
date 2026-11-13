import unittest
from unittest.mock import patch
from rwstudio.authoring import seed
from rwstudio.authoring_ai import npc_reply
from rwstudio.provider import Provider
from rwstudio.story_actions import actions,native
from rwstudio.builder import literal


class StoryActionTests(unittest.TestCase):
    def test_only_current_npc_objective_is_offered(self):
        p=seed()
        self.assertEqual([a['id'] for a in actions(p,'ilyra',{'road_safe':1})],['talk:road_safe:1'])
        self.assertEqual(actions(p,'rowan',{'road_safe':1}),[])
        self.assertEqual(actions(p,'ilyra',{'road_safe':3}),[])

    def test_choices_require_exact_active_state_and_actor(self):
        p=seed();states={'road_safe':-1,'bell_fate':3}
        self.assertEqual([a['id'] for a in actions(p,'ilyra',states)],['choice:bell_fate:3:0','choice:bell_fate:3:1'])
        self.assertEqual(actions(p,'cael',states),[])
        self.assertEqual(actions(p,'ilyra',{'bell_fate':-1}),[])
        self.assertEqual(actions(p,'ilyra',{'bell_fate':True}),[])

    def test_start_respects_prerequisite_and_named_starter(self):
        p=seed();p['quests'][1]['start_npc']='cael'
        self.assertEqual(actions(p,'cael',{}),[])
        self.assertEqual(actions(p,'cael',{'road_safe':-1}),[dict(id='start:bell_fate',description='Offer and start The fate of the Silent Bell')])

    def test_model_cannot_invent_or_use_another_npcs_action(self):
        p=seed();provider=Provider('unused')
        with patch.object(provider,'request',return_value=dict(reply='Hello',action='turn_in',story_action='choice:bell_fate:3:0')):
            reply=npc_reply(provider,p,'rowan','Return the bell',{'quests':{'road_safe':1}})
        self.assertEqual(reply['story_action'],'');self.assertEqual(reply['action'],'none')

    def test_valid_choice_is_returned_with_strict_allowlist(self):
        p=seed();provider=Provider('unused');selected='choice:bell_fate:3:1'
        with patch.object(provider,'request',return_value=dict(reply='We can seal it.',action='none',story_action=selected)) as request:
            reply=npc_reply(provider,p,'ilyra','I choose to seal the clapper.',{'quests':{'road_safe':-1,'bell_fate':3}})
        self.assertEqual(reply['story_action'],selected)
        self.assertEqual(set(request.call_args.args[2]['properties']['story_action']['enum']),{'','choice:bell_fate:3:0',selected})

    def test_native_action_rechecks_state_and_uses_shared_quest_engine(self):
        code=native(seed(),literal)
        self.assertIn('npc=="ilyra" && AQState("bell_fate")==3',code)
        self.assertIn('AQAdvance(pc,"bell_fate",3,"seal_bell")',code)
        self.assertIn('GetDistanceBetween(pc,actor)>12.0',code)
        self.assertIn('GetIsDMPossessed(actor)',code)
        self.assertNotIn('GiveGoldToCreature',code)


if __name__=='__main__':unittest.main()
