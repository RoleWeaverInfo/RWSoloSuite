import unittest
from rwstudio.authoring import blank, npc, validate
from rwstudio.ambient import permitted
from rwstudio.companions import template


class GameplayDefaultTests(unittest.TestCase):
    def test_new_profiles_allow_social_conversations_and_storage(self):
        project = blank();a = npc('anna','Anna','arrival');b = npc('bert','Bert','arrival');project['npcs'] = [a,b]
        self.assertTrue(project['ai_conversations']);self.assertTrue(project['companions']['enabled'])
        self.assertTrue(permitted(project,a,b))
        for n in project['npcs']:
            self.assertTrue(n['ai_enabled']);self.assertTrue(n['behavior']['accept_visits']);self.assertEqual(n['behavior']['partners'],[])
        for profile in [a['companion'],b['companion'],template('new','New'),*project['companions']['templates']]:
            for permission in ('movement','inventory','inspect_containers','social_visits'):self.assertTrue(profile[permission])

    def test_explicit_optouts_and_animal_communication_are_preserved(self):
        project = blank();n = npc('anna','Anna','arrival');project['npcs'] = [n]
        n['ai_enabled'] = False;n['behavior'].update(social_enabled=False,accept_visits=False)
        n['companion'].update(inspect_containers=False,social_visits=False,inventory=False)
        project['ambient']['social'] = False
        for t in project['companions']['templates']:t.update(inspect_containers=False,social_visits=False)
        result = validate(project)
        self.assertFalse(result['ambient']['social']);self.assertFalse(result['npcs'][0]['ai_enabled'])
        self.assertFalse(result['npcs'][0]['behavior']['accept_visits'])
        self.assertFalse(result['npcs'][0]['companion']['inventory'])
        for t in result['companions']['templates']:self.assertFalse(t['social_visits'])
        cat = next(t for t in result['companions']['templates'] if t['familiar_type']==1)
        self.assertEqual(cat['communication'],'nonverbal')
