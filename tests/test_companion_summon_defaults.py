"""Exercise the save-local SQL used when a new companion body is observed."""
import re
import sqlite3
import unittest
from pathlib import Path


class SummonDefaultsTests(unittest.TestCase):
    def setUp(self):
        source = (Path(__file__).resolve().parents[1] / 'authoring_scripts/aw_companion.nss').read_text()
        statements = re.findall(r'SqlPrepareQueryObject\(GetModule\(\),"([^"\n]+)"\)', source)
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.row_factory = sqlite3.Row
        schema = next(q for q in statements if q.startswith('CREATE TABLE IF NOT EXISTS awc_memory'))
        # Explicit initialization must also work in an older save with another default.
        self.db.execute(schema.replace('ai INTEGER NOT NULL DEFAULT 1', 'ai INTEGER NOT NULL DEFAULT 0'))
        self.insert = next(q for q in statements if q.startswith('INSERT OR IGNORE INTO awc_memory'))
        self.change = next(q for q in statements if q.startswith('UPDATE awc_memory SET instance='))
        self.params = dict(id='bond', owner='player', profile='familiar', kind='familiar', instance='first', time=1)
        self.db.execute(self.insert, self.params)

    def record(self):
        return dict(self.db.execute('SELECT * FROM awc_memory').fetchone())

    def test_new_companion_starts_enabled_and_duplicate_insert_preserves_current_choice(self):
        self.assertEqual(self.record()['ai'], 1)
        self.db.execute('UPDATE awc_memory SET ai=0')
        self.db.execute(self.insert, self.params)
        self.assertEqual(self.record()['ai'], 0)

    def test_new_summoned_body_enables_conversation_and_retains_other_preferences(self):
        for kind in ('familiar', 'summon', 'party'):
            with self.subTest(kind=kind):
                self.db.execute("UPDATE awc_memory SET kind=?,ai=0,epoch=4,history='Remember me',movement=0,inventory=0,reply=2,tone=3,receipt='Potion taken'", (kind,))
                self.db.execute(self.change, self.params | dict(instance='second', time=10))
                r = self.record()
                self.assertEqual(r['ai'], 0 if kind == 'party' else 1)
                self.assertEqual((r['instance'], r['epoch'], r['touched']), ('second', 5, 10))
                self.assertEqual((r['history'], r['movement'], r['inventory'], r['reply'], r['tone'], r['receipt']), ('Remember me', 0, 0, 2, 3, 'Potion taken'))

    def test_another_owner_cannot_reset_companion(self):
        before = self.record()
        self.db.execute(self.change, self.params | dict(owner='stranger', instance='other'))
        self.assertEqual(self.record(), before)


if __name__ == '__main__':
    unittest.main()
