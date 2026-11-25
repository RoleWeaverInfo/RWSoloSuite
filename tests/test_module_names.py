import copy
import re
import unittest

from rwstudio import authoring, content
from rwstudio.imported_module import plan
from rwstudio.module_names import module_tag, validate_module_name
from rwstudio.module_analysis import build_report
from test_module_analyser import fixture, ACTIONS
from pathlib import Path
import tempfile


class ModuleNameTests(unittest.TestCase):
    def test_long_names_roundtrip_all_project_formats(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'original.mod'
            path.write_bytes(fixture())
            report, _ = build_report(path, {}, actions=ACTIONS)
            report['module']['name'] = 'A Much Longer Adventure Name for Conversion'
            converted = plan(report)
        self.assertEqual(converted['module_name'], 'rw_a_much_longer_adventure_name_for_conversion')
        for project in (content.seed(), authoring.seed(), converted):
            for name in ('a', 'pools_of_radiance_ai_edition', 'a'*64):
                with self.subTest(schema=project['schema_version'], name=name):
                    draft = copy.deepcopy(project)
                    draft['module_name'] = name
                    self.assertEqual(content.validate_project(draft)['module_name'], name)
            for name in ('a'*65, '../outside', 'folder/file', 'bad name', 'bad.mod', 'name;cmd', 'a\n'):
                with self.subTest(schema=project['schema_version'], invalid=name):
                    draft = copy.deepcopy(project)
                    draft['module_name'] = name
                    with self.assertRaises(ValueError):
                        content.validate_project(draft)

    def test_ai_schema_uses_file_limit_but_internal_resources_stay_short(self):
        pattern = authoring.SCHEMA['properties']['module_name']['pattern']
        self.assertIsNotNone(re.fullmatch(pattern, 'a'*64))
        self.assertIsNone(re.fullmatch(pattern, 'a'*65))
        draft = authoring.seed()
        draft['areas'][0]['id'] = 'a'*17
        with self.assertRaises(ValueError):
            authoring.validate(draft)
        self.assertEqual(authoring.blank('a_longer_project_identifier')['module_name'], 'a_longer_project_identifier')

    def test_tags_remain_short_and_distinguish_shared_prefixes(self):
        self.assertEqual(module_tag('rw_ember_v3'), 'rw_ember_v3')
        self.assertEqual(module_tag('a'*32), 'a'*32)
        self.assertEqual(len(module_tag('a'*64)), 32)
        self.assertNotEqual(module_tag('a'*63+'b'), module_tag('a'*63+'c'))
        for value in (None, 42, '', 'Upper', 'a'*65, 'a\\b', 'a\x00b'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_module_name(value)
