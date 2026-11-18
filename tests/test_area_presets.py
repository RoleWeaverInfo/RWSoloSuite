import copy,json,math,re,struct,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from rwstudio.area_presets import MATERIALS,LIGHTING,catalog,default_look,apply_lighting,packed,rgb,stone_texture
from rwstudio.native_materials import export as export_native,tint_dds,tint_tga,rewrite_model,SURFACES
from rwstudio.measured_geometry import export as export_measured,validate_set
from rwstudio.authoring import blank,validate
from rwstudio.authoring_ai import finish_proposal
from rwstudio.design_extensions import base_project
from rwstudio.design_tools import area_test_project,attach_area,apply_interpretation
from rwstudio.layout import plan,TILESETS
from rwstudio.asset_catalog import installed
from rwstudio.model_preview import geometry
from rwstudio.builder import ROOT,build_project
from rwstudio.storage import Store
from rwstudio.nwn.area_tools import node
from rwstudio.nwn.gff import read,write
from rwstudio.nwn.module_copy import resources
from rwstudio.custom_assets import FileArchive
from tests.test_spatial_geometry import GAME,COMPILER
from tests.test_doorways import connected_project

def native_project(kind='forest'):
    p=blank('look_test','Material test');p['design_mode']='area';a=p['areas'][0];a['type']=kind;a['look']=default_look(kind);return p

def numbers(raw):
    out=[]
    for line in raw.decode('latin1').splitlines():
        try:out.append(tuple(map(float,line.split())))
        except ValueError:pass
    return out

class AreaPresets(unittest.TestCase):
    def test_all_families_and_invalid_settings(self):
        for kind in TILESETS:validate(native_project(kind))
        for look in (dict(material='cave_basalt'),dict(lighting='winter_day'),dict(brightness=float('nan')),dict(fog=81),dict(weather='storm'),dict(brightness=0)):
            p=native_project();p['areas'][0]['look'].update(look)
            with self.subTest(look=look),self.assertRaises(ValueError):validate(p)
        p=native_project('castle');p['areas'][0]['look']['weather']='snow'
        with self.assertRaisesRegex(ValueError,'outdoor'):validate(p)

    def test_old_projects_do_not_change_without_a_preset(self):
        p=blank();a=p['areas'][0];native=node(0,SunAmbientColor=(4,123),Tile_List=(15,[]));before=copy.deepcopy(native)
        apply_lighting(a,native);self.assertEqual(native,before)
        self.assertEqual(export_native(a,{'tileset':'tic01'},Mock(),'legacy'),({}, {'tileset':'tic01'}))
        a['look']=dict(material='original',lighting='legacy',brightness=1,fog=0,weather='preset');apply_lighting(a,native);self.assertEqual(native,before)

    def test_native_lighting_fields_and_color_byte_order(self):
        self.assertEqual(packed('#123456'),0x563412)
        for ident,spec in LIGHTING.items():
            p=native_project(spec['types'][0]);a=p['areas'][0];a['look'].update(lighting=ident,brightness=.75,fog=17)
            native=node(0,Tile_List=(15,[node(1)]));apply_lighting(a,native);out=read(write(b'ARE V3.2',native))[1][1]
            self.assertEqual(out['SunAmbientColor'],(4,packed(spec['ambient'],.75)));self.assertEqual(out['MoonFogAmount'],(0,17))
            self.assertEqual(out['DayNightCycle'][1],0);self.assertEqual(out['IsNight'][1],int(spec['night']))
            self.assertEqual(out['Tile_List'][1][0][1]['Tile_SrcLight1'][1],spec['source'])
            self.assertEqual(out['ChanceSnow'][1],65 if ident=='winter_flurry' else 0)
        a=native_project('desert')['areas'][0];a['look']['weather']='rain';n=node(0,Tile_List=(15,[]));apply_lighting(a,n)
        self.assertEqual(n[1]['ChanceRain'][1],65);self.assertEqual(n[1]['SkyBox'][1],2)

    def test_dds_retains_mipmaps_alpha_and_transparent_mode(self):
        # BioWare DXT5: header + two blocks (mip levels); alpha bytes are untouched.
        header=struct.pack('<4If',4,4,4,16,1.);block=b'\x90\x20\x02\x03\x04\x05\x06\x07'+struct.pack('<HHI',0xf800,0x07e0,0xe4e4e4e4)
        raw=header+block*2;out=tint_dds(raw,(100,160,210));self.assertEqual(out[:20],header);self.assertEqual(len(out),len(raw));self.assertNotEqual(out,raw)
        for at in (20,36):self.assertEqual(raw[at:at+8],out[at:at+8])
        raw=struct.pack('<4If',4,4,3,8,1.)+struct.pack('<HHI',0x001f,0x07e0,0xffffffff);out=tint_dds(raw,(170,90,40));a,b,bits=struct.unpack_from('<HHI',out,20)
        self.assertLessEqual(a,b);self.assertEqual(bits,0xffffffff)
        with self.assertRaises(ValueError):tint_dds(raw[:-1],(100,100,100))

    def test_tga_alpha_dimensions_and_detail_survive_tint(self):
        head=bytes([0,0,2,0,0,0,0,0,0,0,0,0,2,0,1,0,32,40]);raw=head+bytes([20,40,60,0,80,100,120,180]);out=tint_tga(raw,(50,100,160))
        self.assertEqual(out[:18],head);self.assertEqual(out[21::4],raw[21::4]);self.assertNotEqual(out[18:21],out[22:25])
        rle=bytearray(head);rle[2]=10;out=tint_tga(bytes(rle)+b'\x81'+raw[18:22],(50,100,160));self.assertEqual(len(out),26);self.assertEqual(out[18:22],out[22:26])

    @unittest.skipUnless(GAME.exists(),'NWN assets required')
    def test_native_finishes_clone_all_tiles_without_changing_shapes_or_collision(self):
        g=installed(str(GAME))
        for kind in ('castle','cave','forest','desert','winter'):
            with self.subTest(kind=kind):
                p=native_project(kind);a=p['areas'][0];res,layout=export_native(a,plan(p)[a['id']],g,'preset_'+kind);cfg=validate_set(res[layout['tileset'],2013])
                self.assertNotEqual(layout['tileset'],TILESETS[kind]);self.assertEqual(len(layout['material_models']),int(cfg['TILES']['Count']))
                for old,new in list(layout['material_models'].items())[:3]:
                    raw=g.get(old,2002);self.assertEqual(geometry(raw),geometry(res[new,2002]));self.assertEqual(numbers(g.get(old,2016)),numbers(res[new,2016]))
                    if raw[:4]==b'\0'*4:self.assertEqual(len(raw),len(res[new,2002]));self.assertEqual(res[new,2002][20:84].split(b'\0')[0],new.encode())
                for old,new in layout['material_textures'].items():
                    self.assertNotIn((old,2033),res);self.assertNotIn((old,3),res)
                    self.assertEqual(len(res[new,2033]),len(g.get(old,2033)));self.assertNotEqual(res[new,2033],g.get(old,2033))
                if kind=='desert':self.assertEqual(cfg['TILE36']['Doors'],'0')

    @unittest.skipUnless(GAME.exists(),'NWN assets required')
    def test_two_areas_using_different_finishes_cannot_override_each_other(self):
        g=installed(str(GAME));p=native_project('forest');a=p['areas'][0];b=copy.deepcopy(a);b['id']='other';b['look']['material']='forest_dry'
        layout=plan(p)[a['id']];ra,la=export_native(a,layout,g,'isolation');rb,lb=export_native(b,layout,g,'isolation')
        self.assertFalse(set(ra)&set(rb));self.assertNotEqual(la['tileset'],lb['tileset'])
        sa=la['material_textures']['ttf01_floor01'];sb=lb['material_textures']['ttf01_floor01'];self.assertNotEqual(ra[sa,2033],rb[sb,2033])

    @unittest.skipUnless(GAME.exists(),'NWN assets required')
    def test_measured_finish_preserves_carpet_platform_wok_and_fitted_doors(self):
        p=connected_project();a=p['areas'][0];g=installed(str(GAME));l=plan(p)[a['id']];old,_=export_measured(a,l,g,'same')
        a['look']=default_look('castle');a['look']['material']='castle_limestone';new,result=export_measured(a,l,g,'same');ts=result['tileset']
        self.assertEqual(new[ts+'f',3],stone_texture(MATERIALS['castle_limestone']));self.assertNotEqual(new[ts+'f',3],old[ts+'f',3])
        self.assertEqual({k:v for k,v in old.items() if k[1]==2016},{k:v for k,v in new.items() if k[1]==2016})
        self.assertEqual(old[ts+'c0',3],new[ts+'c0',3]);self.assertEqual(len(result['doorways']),4)
        for d in result['doorways']:self.assertEqual(d['wood'],MATERIALS['castle_limestone']['wood'])

    def test_presets_survive_ai_proposals_floorplan_rebuild_attachment_and_playtests(self):
        p=native_project();a=p['areas'][0];look=copy.deepcopy(a['look']);raw=base_project(p);self.assertNotIn('look',raw['areas'][0])
        result=finish_proposal(Mock(),p,p,raw,'area',a['id'],{})['proposal'];self.assertEqual(result['areas'][0]['look'],look)
        proposal=apply_interpretation(p,a['id'],dict(area=raw['areas'][0],connections=[]))['proposal'];self.assertEqual(proposal['areas'][0]['look'],look)
        self.assertEqual(area_test_project(p,a['id'])['areas'][0]['look'],look)
        target=blank('dest','Destination');attached=attach_area(p,a['id'],target)['proposal'];self.assertEqual(attached['areas'][-1]['look'],look)

    def test_creator_controls_recommend_edit_reset_and_filter_by_area_type(self):
        script=r"""
const vm=require('vm'),fs=require('fs'),assert=require('assert');const elements={},p=JSON.parse(process.argv[1]),notices=[];delete p.areas[0].look;let saved,reviewErrors=[];const ctx={project:p,app:{area_presets:JSON.parse(process.argv[2])},E:String,clone:o=>JSON.parse(JSON.stringify(o)),area:()=>ctx.project.areas[0],report:null,previousDraft:null,dirty:false,$:s=>elements[s]??={},render:()=>{},renderHeader:()=>{},projectList:()=>{},notify:(...args)=>notices.push(args),api:async(path,body)=>{if(path==='/api/project/save'){saved=ctx.clone(body.project);return {project:ctx.clone(saved)};}if(path==='/api/state')return {projects:[]};assert.equal(path,'/api/author/review');return {errors:reviewErrors};},task:async(b,f)=>await f(),document:{querySelectorAll:s=>elements[s]||[]}};
vm.createContext(ctx);const editor=fs.readFileSync('web/editor.js','utf8');vm.runInContext(editor.slice(editor.indexOf('function change()'),editor.indexOf('function roomOptions()')),ctx);vm.runInContext(editor.slice(editor.indexOf('async function save()'),editor.indexOf('function assistant(')),ctx);vm.runInContext(fs.readFileSync('web/presets.js','utf8'),ctx);let h=ctx.presetPanel(ctx.area());assert(h.includes('Mossy forest floor'));assert(!h.includes('Golden sand and sandstone'));
const choose={dataset:{lookAction:'recommended'}},reset={dataset:{lookAction:'reset'}},fog={dataset:{look:'fog'},value:'24'};elements['[data-look-action]']=[choose,reset];elements['[data-look]']=[fog];ctx.bindPresets();(async()=>{
 await choose.onclick();assert.equal(ctx.area().look.material,'forest_moss');assert(ctx.dirty);assert.equal(elements['#saveState'].textContent,'Unsaved draft');assert.deepEqual(ctx.report.errors,[]);
 await ctx.save();assert(!ctx.dirty);assert.equal(saved.areas[0].look.material,'forest_moss');ctx.project=ctx.clone(saved);
 await fog.onchange();assert.equal(ctx.area().look.fog,24);assert.equal(ctx.previousDraft.areas[0].look.fog,12);assert.deepEqual(ctx.report.errors,[]);
 reviewErrors=['Another room still needs a connection'];await choose.onclick();assert.equal(ctx.area().look.fog,12);assert.equal(ctx.report.errors,reviewErrors);assert.equal(notices.at(-1)[0],reviewErrors[0]);
 ctx.area().type='winter';ctx.reconcileAreaLook(ctx.area());assert.equal(ctx.area().look.material,'original');await reset.onclick();assert(!ctx.area().look);assert(ctx.report);assert(ctx.dirty);
 reviewErrors=[];for(const type of ['castle','cave','forest','desert','winter']){ctx.area().type=type;await choose.onclick();assert.equal(ctx.area().look.material,ctx.app.area_presets.defaults[type][0]);assert(ctx.report);}
 const before=ctx.clone(ctx.project);ctx.api=async()=>{throw Error('Review unavailable');};await assert.rejects(choose.onclick(),/Review unavailable/);assert.deepEqual(ctx.project,before);
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        r=subprocess.run(['node','-e',script,json.dumps(native_project()),json.dumps(catalog())],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)

    def test_dropdown_changes_keep_options_and_submit_valid_presets_with_real_task(self):
        script=r"""
const vm=require('vm'),fs=require('fs'),assert=require('assert'),elements={},submitted=[],notices=[];
const initial=JSON.parse(process.argv[1]),catalog=JSON.parse(process.argv[2]);
const ctx={project:initial,app:{area_presets:catalog},clone:o=>JSON.parse(JSON.stringify(o)),area:()=>ctx.project.areas[0],previousDraft:null,report:null,dirty:false,$:s=>elements[s]??={},render:()=>{},notify:(...args)=>notices.push(args),api:async(path,body)=>{assert.equal(path,'/api/author/review');submitted.push(ctx.clone(body.project));return {errors:[]};},document:{querySelectorAll:s=>elements[s]||[]}};
vm.createContext(ctx);const editor=fs.readFileSync('web/editor.js','utf8');
vm.runInContext(editor.slice(editor.indexOf('async function task('),editor.indexOf('function value(')),ctx);
vm.runInContext(editor.slice(editor.indexOf('function change()'),editor.indexOf('function roomOptions()')),ctx);
vm.runInContext(fs.readFileSync('web/presets.js','utf8'),ctx);
function control(tagName,key,value){
 const el={tagName,dataset:{look:key},value,disabled:false,options:tagName==='SELECT'?[{value}]:[]};let text='Original label';
 // A real select loses its option nodes and selected value on textContent assignment.
 Object.defineProperty(el,'textContent',{get:()=>text,set:v=>{text=v;if(tagName==='SELECT'){el.options=[];el.value='';}}});return el;
}
(async()=>{
 for(const type of Object.keys(catalog.defaults)){
  ctx.project=ctx.clone(initial);ctx.area().type=type;delete ctx.area().look;
  const material=Object.keys(catalog.materials).filter(id=>catalog.materials[id].types.includes(type)).at(-1);
  const lighting=Object.keys(catalog.lighting).filter(id=>catalog.lighting[id].types.includes(type)).at(-1);
  const weather=['forest','desert','winter'].includes(type)?'snow':'clear';
  for(const [key,value] of [['material',material],['lighting',lighting],['weather',weather],['fog','24'],['brightness','1.25'],['lighting','legacy'],['material','original']]){
   const input=control(['fog','brightness'].includes(key)?'INPUT':'SELECT',key,value),options=input.options;
   elements['[data-look]']=[input];ctx.bindPresets();await input.onchange();
   assert.equal(ctx.area().look[key],['fog','brightness'].includes(key)?Number(value):value,type+' / '+key);
   assert.equal(input.value,value);assert.strictEqual(input.options,options);assert.equal(input.disabled,false);assert.equal(input.textContent,'Original label');
  }
 }
 assert.deepEqual(notices,[]);
 const select=control('SELECT','lighting','castle_warm'),options=select.options;
 await ctx.task(select,async()=>{assert(select.disabled);throw Error('Review unavailable');});
 assert.equal(select.value,'castle_warm');assert.strictEqual(select.options,options);assert.equal(select.disabled,false);assert.equal(notices.at(-1)[0],'Review unavailable');
 const button=control('BUTTON','',null);await ctx.task(button,async()=>{assert(button.disabled);assert.equal(button.textContent,'Working…');});
 assert.equal(button.textContent,'Original label');assert.equal(button.disabled,false);
 button.disabled=true;await ctx.task(button,async()=>{});assert.equal(button.disabled,true);
 await ctx.task(null,async()=>{});console.log(JSON.stringify(submitted));
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        result=subprocess.run(['node','-e',script,json.dumps(native_project()),json.dumps(catalog())],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        projects=json.loads(result.stdout);self.assertEqual(len(projects),len(TILESETS)*7)
        for project in projects:validate(project)

    @unittest.skipUnless(GAME.exists() and COMPILER.exists(),'NWN/compiler required')
    def test_real_native_build_packages_terrain_materials_and_light_fields(self):
        p=native_project('winter');p['areas'][0]['look'].update(material='winter_blue',lighting='winter_flurry',fog=30)
        q=area_test_project(p,p['areas'][0]['id']);q['module_name']='preset_test'
        with tempfile.TemporaryDirectory() as tmp:
            manifest=build_project(q,Store(Path(tmp)),GAME,COMPILER);folder=Path(manifest['path']).parent;mod={(n,k):b for n,k,b in resources(Path(manifest['path']).read_bytes())}
            ar=read(mod[p['areas'][0]['id'],2012])[1][1];self.assertEqual(ar['ChanceSnow'][1],65);self.assertEqual(ar['SunFogAmount'][1],30);self.assertEqual(ar['SkyBox'][1],4)
            module=read(mod['module',2014])[1][1];hakname=module['Mod_HakList'][1][0][1]['Mod_Hak'][1].decode();hak=FileArchive(folder/'hak'/(hakname+'.hak'));ts=ar['Tileset'][1].decode();validate_set(hak[ts,2013])
            self.assertTrue(any(k==2033 for n,k in hak));self.assertTrue(list((folder/'geometry-source').glob('*.dds')))
