import copy
import json
import math
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from rwstudio.conversion_performance import configuration, json_expression, record_tree


def evaluate_tree(source, ident):
    """Evaluate generated dispatch branches, counting only the taken path."""
    branches=0
    while source.startswith('if(index<'):
        match=re.match(r'if\(index<(\d+)\)\{',source)
        start=match.end();depth=1;end=start
        # JSON/string literals occur only at leaves. Skip quoted strings so
        # braces inside a character description cannot affect branch parsing.
        quoted=False;escaped=False
        while depth:
            char=source[end]
            if quoted:
                if escaped:escaped=False
                elif char=='\\':escaped=True
                elif char=='"':quoted=False
            elif char=='"':quoted=True
            elif char=='{':depth+=1
            elif char=='}':depth-=1
            end+=1
        branches+=1
        source=(source[start:end-1] if int(ident[4:])<int(match[1]) else source[end+5:-1]).strip()
    match=re.fullmatch(r'if\(id==("(?:\\.|[^"\\])*")\)return JsonParse\((.*)\);return JsonNull\(\);',source,re.S)
    if not match:return None,branches
    if json.loads(match[1])!=ident:return None,branches+1
    # Adjacent string constants are joined by + in the generated NSS.
    parts=re.findall(r'"(?:\\.|[^"\\])*"',match[2])
    return json.loads(''.join(json.loads(part) for part in parts)),branches+1


class PerformanceTests(unittest.TestCase):
    def test_thousand_profiles_require_at_most_eleven_dispatch_checks(self):
        rows=[(f'cv_n{i:04}',dict(id=f'cv_n{i:04}',label='A {name} "quoted"',enabled=i%2==0)) for i in range(1000)]
        tree=record_tree(rows)
        for ident,expected in rows:
            actual,checks=evaluate_tree(tree,ident)
            self.assertEqual(actual,expected)
            self.assertLessEqual(checks,math.ceil(math.log2(len(rows)))+1)
        self.assertIsNone(evaluate_tree(tree,'cv_n9999')[0])
        # Edited/filtered profiles need not have contiguous numeric IDs.
        sparse=record_tree([rows[3],rows[800],rows[999]])
        self.assertIsNone(evaluate_tree(sparse,'cv_n0004')[0])
        self.assertEqual(evaluate_tree(sparse,'cv_n0800')[0],rows[800][1])

    def test_large_unicode_constants_are_chunked_losslessly(self):
        value={'description':'雪🌲 {"room"} \\ '+('x'*90000)}
        expression=json_expression(value)
        parts=[json.loads(part) for part in re.findall(r'"(?:\\.|[^"\\])*"',expression)]
        self.assertGreater(len(parts),1)
        self.assertTrue(all(len(part.encode('utf-8'))<=4000 for part in parts))
        self.assertEqual(json.loads(''.join(parts)),value)

    def test_runtime_has_no_full_cast_scans_on_chat_or_heartbeat(self):
        from test_module_analyser import fixture,ACTIONS
        from rwstudio.module_analysis import build_report
        from rwstudio.imported_module import plan
        from rwstudio.conversion_runtime import runtime
        from rwstudio.server import defaults
        from rwstudio.nwn.game_assets import GameAssets
        cfg=defaults()
        if not cfg['game_root']:self.skipTest('Installed NWN assets required')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'original.mod';path.write_bytes(fixture())
            report,_=build_report(path,{},actions=ACTIONS);p=plan(report)
        game=GameAssets(cfg['game_root']);scripts,_=runtime(p,'a'*20,game,{})
        for name in ('aw_companion','aw_cp_ui','aw_cp_tasks','aw_ct_poll','aw_merchant','sp_inc','sp_chat'):
            for full_table in ('AWCompanionNPCs()','AWABehaviors()','AWShops()'):
                self.assertNotIn(full_table,scripts[name],name)
        self.assertEqual(scripts['rwc_beat'].count('AWCActors(pc)'),1)
        self.assertIn('RWTaskTick(pc,actors)',scripts['rwc_beat'])
        self.assertIn('if(body!=ticked)AWTBodyTick',scripts['aw_cp_tasks'])
        self.assertIn('JsonDump(SPSnapshot(pc,FALSE))',scripts['sp_inc'])
        self.assertIn('json observed=SPSnapshot(pc);',scripts['sp_inc'])
        self.assertIn('GetLastOpenedBy(store)==pc',scripts['aw_merchant'])
        self.assertIn('AWCOwner(body)==pc && AWCLinked(body)',scripts['aw_companion'])
        # Cache revision follows profile changes, not a fixed install/session ID.
        old=re.search(r'RWConfigVersion\(\)\{return "([^"]+)"',scripts['aw_config'])[1]
        changed=copy.deepcopy(p);changed['npcs'][0]['behavior']['accept_visits']=False
        new_scripts,_=runtime(changed,'b'*20,game,{})
        new=re.search(r'RWConfigVersion\(\)\{return "([^"]+)"',new_scripts['aw_config'])[1]
        self.assertNotEqual(old,new)

    def test_actual_compiler_accepts_thousand_profile_lookup_and_native_caches(self):
        from rwstudio.server import defaults
        cfg=defaults()
        if not Path(cfg['compiler']).is_file() or not cfg['game_root']:self.skipTest('Installed NWN compiler required')
        npcs=[dict(id=f'cv_n{i:04}',native_tag=f'tag{i}',native_resref=f'ref{i}',alias=f'person{i}',name=f'Person {i}',ai_enabled=i%2==0) for i in range(1000)]
        arrays={name:[dict(id=n['id'],name=n['name']) for n in npcs] for name in ('AWCompanionNPCs','AWABehaviors','AWShops')}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'rwc_perf.nss').write_text(configuration(dict(npcs=npcs),arrays)+'\nvoid main(){RWIsNPC("cv_n0999");RWProfile(OBJECT_SELF);RWAddress("person0");RWAlias("person1");}',encoding='utf-8')
            result=subprocess.run([cfg['compiler'],'-n',cfg['game_root'],'-b',str(root),'rwc_perf.nss'],cwd=root,capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue((root/'rwc_perf.ncs').is_file())


if __name__=='__main__':unittest.main()
