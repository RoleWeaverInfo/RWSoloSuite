import copy
import json
import subprocess
import unittest
from html.parser import HTMLParser

from rwstudio.authoring import blank,AREA_TYPES
from rwstudio.area_presets import catalog
from rwstudio.builder import ROOT


class Elements(HTMLParser):
    def __init__(self,html):
        super().__init__();self.elements=[];self.feed(html)

    def handle_starttag(self,tag,attrs):
        self.elements.append((tag,dict(attrs)))


class AreaNavigation(unittest.TestCase):
    def run_ui(self,script):
        project=blank('navigation_check');project['design_mode']='area'
        second=copy.deepcopy(project['areas'][0]);second['id']='second_area';second['rooms'][0]['id']='second_room';project['areas'].append(second)
        app=dict(projects=[],settings=dict(content_root=''),area_presets=catalog(),authoring_catalog=dict(area_types=AREA_TYPES))
        setup=r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert'),els={},groups={};
function element(dataset={}){return {dataset,hidden:false,attrs:{},classList:{toggle(){}},setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}};}
const ctx={console,window:{scrollTo(){}},document:{querySelector:s=>els[s]??=element(),querySelectorAll:s=>groups[s]||[]}};
vm.createContext(ctx);
for(const file of ['catalog','spatial','design','presets'])vm.runInContext(fs.readFileSync('web/'+file+'.js','utf8'),ctx);
const source=fs.readFileSync('web/editor.js','utf8');vm.runInContext(source.slice(0,source.indexOf("$('#saveProject').onclick")),ctx);
ctx.fixture=JSON.parse(process.argv[1]);ctx.appFixture=JSON.parse(process.argv[2]);
vm.runInContext("project=fixture;app=appFixture;page='world';areaIndex=1;",ctx);
"""
        result=subprocess.run(['node','-e',setup+script,json.dumps(project),json.dumps(app)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        return result.stdout

    def test_sections_keep_draft_context_and_render_one_visible_panel(self):
        result=self.run_ui(r"""
const keys=['overview','floorplans','materials','layout','assets'];
groups['[data-area-section]']=keys.map(k=>element({areaSection:k}));
groups['[data-area-panel]']=keys.map(k=>element({areaPanel:k}));
const fold=element({uiFold:'asset-catalog'});groups['[data-ui-fold]']=[fold];
ctx.bindAreaSections();const initial=vm.runInContext('JSON.stringify(project)',ctx);
const draft=els['#aiDirection']={value:'Keep this unfinished instruction'};
ctx.render=()=>assert.fail('Subsection navigation must retain existing form nodes');
const html=[];
for(const key of keys){ctx.showAreaSection(key);assert.equal(groups['[data-area-panel]'].filter(p=>!p.hidden).length,1);assert(!groups['[data-area-panel]'].find(p=>p.dataset.areaPanel===key).hidden);assert.equal(els['#aiDirection'],draft);assert.equal(draft.value,'Keep this unfinished instruction');assert.equal(vm.runInContext('areaIndex',ctx),1);html.push(ctx.world());}
assert.equal(vm.runInContext('JSON.stringify(project)',ctx),initial);
fold.open=true;fold.ontoggle();assert(ctx.foldAttributes('asset-catalog').includes('open'));
fold.open=false;fold.ontoggle();assert(!ctx.foldAttributes('asset-catalog').includes('open'));
vm.runInContext('generating=true',ctx);ctx.notify=()=>{};ctx.showAreaSection('overview');assert.equal(vm.runInContext('areaSection',ctx),'assets');
vm.runInContext("page='settings'",ctx);ctx.syncAreaSections();assert(els['#areaNavigation'].hidden);
console.log(JSON.stringify(html));
""")
        for selected,html in zip(('overview','floorplans','materials','layout','assets'),json.loads(result)):
            self.assertLess(html.index('<h3>Room design</h3>'),html.index('<h3>Visual area editor</h3>'))
            self.assertEqual(html.count('class="worldmap"'),1)
            nodes=Elements(html).elements
            panels=[attrs for _,attrs in nodes if 'data-area-panel' in attrs]
            self.assertEqual(len(panels),5)
            self.assertEqual([p['data-area-panel'] for p in panels if 'hidden' not in p],[selected])
            ids=[attrs['id'] for _,attrs in nodes if 'id' in attrs]
            self.assertEqual(len(ids),len(set(ids)),'Repeated control/result IDs')
            self.assertEqual(ids.count('designStatus'),1);self.assertEqual(ids.count('auroraResult'),1)
            for key in ('asset-catalog','content-sources','placed-furnishings','precise-placement'):
                fold=next(attrs for tag,attrs in nodes if tag=='details' and attrs.get('data-ui-fold')==key)
                self.assertNotIn('open',fold)

    def test_catalog_query_page_and_selection_survive_rebinding(self):
        self.run_ui(r"""
const assets=Array.from({length:30},(_,i)=>({id:'chair_'+i,name:'Chair '+i,model:'chair',pack:'builtin'}));ctx.assetsFixture=assets;vm.runInContext('assetLibrary.assets=assetsFixture',ctx);
function select(){let html='';return {value:'',set innerHTML(s){html=s;this.value=(s.match(/value="([^"]+)"/)||[])[1]||'';},get innerHTML(){return html;}};}
els['#customAsset']=select();els['#assetSearch']={value:''};ctx.bindAssetCatalog();
els['#assetSearch'].value='chair';els['#assetSearch'].oninput();els['#assetNext'].onclick();
els['#customAsset'].value='chair_18';els['#customAsset'].onchange();
els['#customAsset']=select();els['#assetSearch']={value:''};ctx.bindAssetCatalog();
assert.equal(els['#assetSearch'].value,'chair');assert.equal(els['#customAsset'].value,'chair_18');assert(els['#assetPageLabel'].textContent.includes('page 2 of 3'));
els['#assetSearch'].value='no match';els['#assetSearch'].oninput();assert.equal(els['#customAsset'].value,'');assert(els['#assetPageLabel'].textContent.includes('0 matches'));assert(els['#assetPrev'].disabled);assert(els['#assetNext'].disabled);
""")
