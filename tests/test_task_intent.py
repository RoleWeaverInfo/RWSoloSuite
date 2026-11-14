import copy
import unittest
from unittest.mock import patch
from rwstudio.companion_tasks import example
from rwstudio.companions import context,reply
from rwstudio.authoring_ai import npc_reply
from rwstudio.provider import Provider
from rwstudio.task_intent import finish
from test_companions import snapshot


def scene(kind='familiar'):
    s=snapshot('party' if kind=='party' else 'familiar','seren' if kind=='party' else 'fam_eyeball')
    s['companion'].update(familiar_type=10,animal=0,intelligence=12,name='Seren' if kind=='party' else 'Agathos')
    s['task_targets']=[dict(kind='visit',uuid='bram-instance',tag='bram',name='Bram Ironstock',distance=7),
                       dict(kind='inspect',uuid='chest-instance',tag='supplies',name='Healing supplies cache',distance=5)]
    return s


class TaskIntentTests(unittest.TestCase):
    def test_natural_request_offers_current_merchant_identity_and_role(self):
        p=example();s=scene();provider=Provider('unused')
        result=dict(reply='I did it.',action='none',companion_action='follow',task_target='visit:bram-instance',task_question='What swords do you have for sale?')
        with patch.object(provider,'request',return_value=result) as request:
            answer=reply(provider,p,'Go ask the Merchant what swords he has for sale',s)
        ctx=request.call_args.args[1]['companion'];schema=request.call_args.args[2]
        merchant=ctx['task_targets'][0];self.assertTrue(merchant['merchant']);self.assertEqual(merchant['name'],'Bram Ironstock')
        self.assertEqual(schema['properties']['task_target']['enum'],['','visit:bram-instance','inspect:chest-instance'])
        self.assertEqual(answer['task_target'],'visit:bram-instance');self.assertEqual(answer['companion_action'],'')
        self.assertNotIn('I did it',answer['reply']);self.assertIn('try',answer['reply'])
        self.assertNotIn('secret',merchant);self.assertNotIn('knowledge',merchant)

    def test_party_companions_share_the_same_task_interpreter(self):
        p=example();provider=Provider('unused')
        result=dict(reply='Done',action='none',story_action='invent',merchant_action='',companion_action='follow',task_target='inspect:chest-instance',task_question='')
        with patch.object(provider,'request',return_value=result):answer=npc_reply(provider,p,'seren','Can you find out what is inside that chest?',scene('party'))
        self.assertEqual(answer['task_target'],'inspect:chest-instance');self.assertEqual(answer['story_action'],'');self.assertEqual(answer['companion_action'],'')

    def test_creator_player_and_recipient_permissions_filter_offers(self):
        p=example();s=scene();self.assertEqual(len(context(p,s)['task_targets']),2)
        t=next(t for t in p['companions']['templates'] if t['id']=='fam_eyeball')
        t['social_visits']=False;self.assertEqual([t['kind'] for t in context(p,s)['task_targets']],['inspect'])
        t['inspect_containers']=False;self.assertEqual(context(p,s)['task_targets'],[])
        p=example();s['companion']['allowed_actions']=[];self.assertEqual(context(p,s)['task_targets'],[])
        s=scene();next(n for n in p['npcs'] if n['id']=='bram')['behavior']['accept_visits']=False
        self.assertEqual([t['kind'] for t in context(p,s)['task_targets']],['inspect'])

    def test_invalid_stale_or_invented_targets_cannot_become_actions(self):
        ctx=context(example(),scene())
        for target in ('visit:invented','inspect:bram-instance','execute_script:anything'):
            r=finish(dict(reply='Hello',task_target=target,task_question='Question?'),ctx)
            self.assertEqual(r['task_target'],'');self.assertEqual(r['task_question'],'')
        self.assertEqual(finish(dict(reply='Hello',task_target='visit:bram-instance',task_question=''),ctx)['task_target'],'')
        self.assertEqual(finish(dict(reply='Hello',task_target='visit:bram-instance',task_question='Question?'),{})['task_target'],'')

    def test_ambiguous_target_can_clarify_without_dispatch(self):
        p=example();s=scene();s['task_targets'].append(dict(kind='inspect',uuid='second-chest',tag='other',name='Old lockbox',distance=6))
        provider=Provider('unused')
        with patch.object(provider,'request',return_value=dict(reply='The supplies cache or the old lockbox?',action='none',companion_action='',task_target='',task_question='')):
            answer=reply(provider,p,'Look in the chest',s)
        self.assertEqual(answer['task_target'],'');self.assertIn('lockbox',answer['reply'])

    def test_nonverbal_creatures_may_inspect_but_cannot_conduct_verbal_visits(self):
        p=example();s=scene();s['companion'].update(profile='fam_cat',familiar_type=1,animal=1,intelligence=2)
        ctx=context(p,s);self.assertEqual([t['kind'] for t in ctx['task_targets']],['inspect'])
        r=finish(dict(reply='I will tell you.',task_target='inspect:chest-instance',task_question=''),ctx)
        self.assertNotIn('I will',r['reply'])

    def test_missing_old_snapshot_and_bad_candidates_are_safe(self):
        p=example();s=scene();s.pop('task_targets');self.assertEqual(context(p,s)['task_targets'],[])
        s['task_targets']=[None,{},dict(kind='visit',uuid='x',tag='missing',name='Missing',distance=2),dict(kind='inspect',uuid='x',name='Distant',distance=46)]
        self.assertEqual(context(p,s)['task_targets'],[])


if __name__=='__main__':unittest.main()
