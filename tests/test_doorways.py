import copy,json,math,subprocess,tempfile,unittest
from collections import defaultdict,deque
from pathlib import Path
from tests.test_carpets import carpet_project
from tests.test_spatial_geometry import GAME,COMPILER,triangles
from tests.test_platforms import height_at
from rwstudio.authoring import room,validate,review
from rwstudio.layout import plan
from rwstudio.measured_geometry import tile_meshes,export,validate_set
from rwstudio.doorways import Registry,collision,door_resources,leaf_specs
from rwstudio.asset_catalog import installed
from rwstudio.custom_assets import FileArchive,table
from rwstudio.builder import build_project,ROOT
from rwstudio.storage import Store
from rwstudio.design_tools import area_test_project,attach_area
from rwstudio.nwn.gff import read
from rwstudio.nwn.module_copy import resources

def connect(ident,source,side,destination,arrival):
    return dict(id=ident,name=ident.replace('_',' ').title(),from_room=source,from_side=side,to_room=destination,to_side=arrival,kind='corridor',two_way=True,requires_quest='')

def connected_project():
    p=carpet_project();a=p['areas'][0];r=a['rooms'][0]
    r['openings']=[dict(side='south',offset=5,width=2),dict(side='east',offset=15.6,width=1.2)]
    foyer=room('foyer','Entrance hall',2,1,1,1);foyer.update(interior=dict(width_m=10,depth_m=8),openings=[dict(side='north',offset=5,width=2)])
    chamber=room('chamber','Side chamber',4,3,1,1);chamber.update(interior=dict(width_m=6,depth_m=8),openings=[dict(side='west',offset=5.6,width=1.2)])
    a['rooms'] += [foyer,chamber];a['room_count']=3;p['start_room']='foyer'
    p['connections']=[connect('entrance','foyer','north','arrival','south'),connect('side_door','arrival','east','chamber','west')]
    return p

def reachable(walk,start,ends):
    edges=defaultdict(list)
    for i,t in enumerate(walk):
        vs=[tuple(round(n,6) for n in v) for v in t]
        for a,b in zip(vs,vs[1:]+vs[:1]):edges[tuple(sorted((a,b)))].append(i)
    neighbors=defaultdict(set)
    for indices in edges.values():
        for i in indices:neighbors[i].update(set(indices)-{i})
    first=next(i for i,t in enumerate(walk) if height_at(t,*start) is not None);todo=deque([first]);seen={first}
    while todo:
        for i in neighbors[todo.popleft()]-seen:seen.add(i);todo.append(i)
    return all(any(height_at(walk[i],*end) is not None for i in seen) for end in ends)

class Doorways(unittest.TestCase):
    def test_exact_small_gaps_and_side_aperture_connect_without_wall_leaks(self):
        p=connected_project();validate(p);self.assertFalse(review(p)['errors']);a=p['areas'][0];layout=plan(p)[a['id']]
        self.assertEqual(layout['rectangles'][3],[24,18,26,20]);self.assertEqual(layout['rectangles'][4],[30,35,40,36.2])
        self.assertEqual(len(layout['doorways']),4)
        walk=triangles(tile_meshes(a,layout));self.assertTrue(reachable(walk,(25,14),[(25,25),(25,38.8),(43,35.6)]))
        for x,y in ((25,19),(30,35.6),(35,35.6),(40,35.6)):self.assertTrue(any(height_at(t,x,y)==0 for t in walk))
        for x,y in ((23.8,19),(26.2,19),(30.2,34.8),(30.2,36.4),(35,34.8),(35,36.4)):
            self.assertFalse(any(height_at(t,x,y) is not None for t in walk),(x,y))

    def test_door_open_states_clear_center_and_follow_hinge_geometry(self):
        for width,leaves in ((1.2,'auto'),(2,'auto'),(2,'single'),(1.2,'double')):
            with self.subTest(width=width,leaves=leaves):
                closed=collision(width,2.4,leaves,'closed');self.assertAlmostEqual(min(v[0] for v in closed['vertices']),-width/2)
                self.assertAlmostEqual(max(v[0] for v in closed['vertices']),width/2)
                for state,sign in (('open1',-1),('open2',1)):
                    m=collision(width,2.4,leaves,state)
                    self.assertTrue(all(abs(v[0])>=width/2-.056 for v in m['vertices']))
                    self.assertGreater(max(sign*v[1] for v in m['vertices']),width/(2 if len(leaf_specs(width,leaves))==2 else 1)-.01)
                    self.assertTrue(all(f[3]==7 for f in m['faces']))

    def test_model_has_native_animations_interaction_points_and_dwks(self):
        r=door_resources('rd_test',2,2.4,'double');mdl=r['rd_test',2002].decode();dwk=r['rd_test',2052].decode()
        for anim in ('closed','opening1','opened1','closing1','opening2','opened2','closing2','die','dead','trans'):self.assertIn('newanim '+anim+' rd_test',mdl)
        for state in ('closed','open1','open2'):
            self.assertIn('rd_test_DWK_wg_'+state,dwk);self.assertIn('rd_test_DWK_dp_'+state+'_1',dwk)
        self.assertIn('node dummy hinge1',mdl);self.assertIn('classification Door',mdl);self.assertIn('render 0',dwk)
        self.assertEqual(len(r['rd_testt',3]),18+64*64*4)

    @unittest.skipUnless(GAME.exists(),'NWN assets required')
    def test_hooks_blueprints_and_merged_table_have_consistent_identity(self):
        p=connected_project();a=p['areas'][0];game=installed(str(GAME));original=game.get('doortypes',2017)
        # A custom pack can define rows/extra columns; preserve it exactly.
        custom=b'2DA V2.0\r\n\r\nLabel Model TileSet TemplateResRef StringRefGame BlockSight VisibleModel SoundAppType Extra\r\n0 Generic **** **** **** 66717 **** **** **** custom\r\n6000 Existing old_model oldset olddoor 5350 1 1 0 keep\r\n'
        registry=Registry(game,[{('doortypes',2017):custom}]);r,l=export(a,plan(p)[a['id']],game,'test_doors',registry);r.update(registry.export())
        merged=table(r['doortypes',2017]);self.assertEqual(merged[6000],table(custom)[6000]);self.assertEqual(merged[0],table(custom)[0])
        cfg=validate_set(r[l['tileset'],2013]);hooks=[dict(cfg[s]) for s in cfg.sections() if 'DOOR' in s and int(cfg[s]['Type'])>=6001]
        self.assertEqual(len(hooks),4);self.assertEqual(len(registry.cache),2)
        for tile in l['measured_tiles']:
            name=cfg['TILE'+str(tile)]['Model']
            for i in range(int(cfg['TILE'+str(tile)]['Doors'])):self.assertIn('node dummy '+name+f'_D{i+1:02d}',r[name,2002].decode())
        for d in l['doorways']:
            row=merged[d['appearance']];self.assertEqual(row['Model'],d['model']);self.assertEqual(row['Extra'],'****')
            self.assertIn((d['model'],2052),r);bp=read(r[d['model'],2042])[1][1];self.assertEqual(bp['Appearance'][1],d['appearance']);self.assertEqual(bp['GenericType'][1],0)
            self.assertTrue(any(int(h['Type'])==d['appearance'] and abs(float(h['X']))<=5 and abs(float(h['Y']))<=5 for h in hooks))
        self.assertEqual(game.get('doortypes',2017),original)

    @unittest.skipUnless(GAME.exists(),'NWN assets required')
    def test_open_frame_and_plain_passage_do_not_export_door_objects(self):
        p=connected_project()
        for c,style in zip(p['connections'],('open','none')):c['doorway']=dict(style=style,height=2.4,leaves='auto')
        validate(p);a=p['areas'][0];r,l=export(a,plan(p)[a['id']],installed(str(GAME)),'open_test')
        self.assertFalse(any(k in (2052,2042,2017) for n,k in r));self.assertTrue(reachable(triangles(tile_meshes(a,l)),(25,14),[(43,35.6)]))

    def test_invalid_door_height_type_and_connection_are_rejected(self):
        for d in (dict(height=float('nan')),dict(height=6),dict(style='portcullis'),dict(leaves='triple'),dict(height=2.4,unexpected=True)):
            p=connected_project();p['connections'][0]['doorway']=d
            with self.subTest(d=d),self.assertRaises(ValueError):validate(p)
        p=connected_project();p['connections'][0].update(kind='exit',doorway=dict(style='wood'))
        with self.assertRaisesRegex(ValueError,'corridor'):validate(p)
        p=connected_project();p['areas'][0]['rooms'][1]['openings'][0]['width']=1.2
        with self.assertRaisesRegex(ValueError,'matching widths'):plan(p)

    def test_offset_short_gap_does_not_silently_cut_through_throne_wall(self):
        p=connected_project();p['areas'][0]['rooms'][1]['openings'][0]['offset']=4
        with self.assertRaisesRegex(ValueError,'Align facing openings'):plan(p)

    def test_implicit_doorway_cannot_cut_a_platform_or_exceed_wall_width(self):
        p=connected_project();r=p['areas'][0]['rooms'][0];r['openings']=[o for o in r['openings'] if o['side']!='east']
        p['connections'][1]['from_side']='north';p['connections'][1]['to_side']='south'
        p['areas'][0]['height']=9;p['areas'][0]['rooms'][2].update(x=2,y=6)
        p['areas'][0]['rooms'][2]['openings']=[dict(side='south',offset=5,width=2)]
        with self.assertRaisesRegex(ValueError,'platforms and stairs clear'):plan(p)
        p=connected_project();p['areas'][0]['geometry']['corridor_width']=6;r=p['areas'][0]['rooms'][2];r['interior']['depth_m']=2;r.pop('openings')
        with self.assertRaises(ValueError):plan(p)

    def test_attachment_and_area_test_preserve_door_controls(self):
        p=connected_project();p['connections'][0]['doorway']=dict(style='wood',leaves='double',height=2.6)
        q=area_test_project(p,p['areas'][0]['id']);validate(q)
        self.assertEqual(q['start_room'],'foyer')
        self.assertEqual(q['connections'][0]['doorway'],p['connections'][0]['doorway']);self.assertEqual(len(q['areas'][0]['rooms']),3)
        from rwstudio.authoring import blank
        target=blank('destination','Destination');q=attach_area(p,p['areas'][0]['id'],target)['proposal'];validate(q)
        self.assertTrue(any(c.get('doorway',{}).get('height')==2.6 for c in q['connections']))

    def test_editor_destination_and_door_style_controls(self):
        code=r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');const ctx={E:String,project:JSON.parse(process.argv[1])};vm.createContext(ctx);vm.runInContext(fs.readFileSync('web/spatial.js','utf8'),ctx);const a=ctx.project.areas[0],r=a.rooms[0];let html=ctx.openingPanel(r,'areas.0.rooms.0');assert(html.includes('Connected to Entrance hall'));assert(html.includes('Connected to Side chamber'));html=ctx.doorwayFields(ctx.project.connections[0],0,a);assert(html.includes('data-doorway="0.height"'));assert(html.includes('Working wooden door'));assert(html.includes('Framed opening'));ctx.project.connections=[];assert(ctx.openingPanel(r,'areas.0.rooms.0').includes('connectOpening_south'));
"""
        result=subprocess.run(['node','-e',code,json.dumps(connected_project())],cwd=ROOT,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)

    def test_editor_connects_rooms_incrementally_without_losing_the_first_link(self):
        code=r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');const buttons={},p=JSON.parse(process.argv[1]);p.connections=[];let closed=false;const ctx={E:String,project:p,report:null,previousDraft:null,clone:o=>JSON.parse(JSON.stringify(o)),area:()=>ctx.project.areas[0],selectedRoom:()=>ctx.project.areas[0].rooms[0],modal:()=>{},$:s=>buttons[s]??={},task:async(b,fn)=>await fn(),render:()=>{},notify:()=>{},api:async()=>({errors:ctx.project.connections.length<2?['Room is unreachable from the start: Side chamber']:[]})};buttons['#modal']={close:()=>closed=true};vm.createContext(ctx);const editor=fs.readFileSync('web/editor.js','utf8');vm.runInContext(editor.slice(editor.indexOf('function change()'),editor.indexOf('function roomOptions()')),ctx);vm.runInContext(fs.readFileSync('web/spatial.js','utf8'),ctx);
(async()=>{await ctx.spatialAction('connectOpening_south');buttons['#openingRoom']={value:'foyer'};buttons['#openingSide']={value:'north'};await buttons['#connectOpeningNow'].onclick({target:{}});assert.equal(ctx.project.connections.length,1);assert(closed);await ctx.spatialAction('connectOpening_east');buttons['#openingRoom'].value='chamber';buttons['#openingSide'].value='west';await buttons['#connectOpeningNow'].onclick({target:{}});assert.equal(ctx.project.connections.length,2);assert.equal(ctx.report.errors.length,0);assert.equal(ctx.previousDraft.connections.length,1);
 const count=ctx.selectedRoom().carpets.length;await ctx.spatialAction('addCarpet');assert.equal(ctx.selectedRoom().carpets.length,count+1);assert(ctx.report);await ctx.spatialAction('removeCarpet_'+count);assert.equal(ctx.selectedRoom().carpets.length,count);assert(ctx.report);
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        result=subprocess.run(['node','-e',code,json.dumps(connected_project())],cwd=ROOT,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)

    @unittest.skipUnless(GAME.exists() and COMPILER.exists(),'NWN/compiler required')
    def test_native_build_has_four_doors_and_no_corridor_teleport_signs(self):
        p=connected_project();q=area_test_project(p,p['areas'][0]['id']);q['module_name']='door_test'
        with tempfile.TemporaryDirectory() as tmp:
            m=build_project(q,Store(Path(tmp)),GAME,COMPILER);folder=Path(m['path']).parent;mod={(n,k):b for n,k,b in resources(Path(m['path']).read_bytes())}
            module=read(mod['module',2014])[1][1];hakname=module['Mod_HakList'][1][0][1]['Mod_Hak'][1].decode();hak=FileArchive(folder/'hak'/(hakname+'.hak'))
            git=read(mod[p['areas'][0]['id'],2023])[1][1];doors=git['Door List'][1];self.assertEqual(len(doors),4)
            rows=table(hak['doortypes',2017]);self.assertEqual(len(git['TriggerList'][1]),0)
            for _,d in doors:
                self.assertEqual(d['LinkedToFlags'][1],0);self.assertFalse(d['LinkedTo'][1]);self.assertEqual(d['Locked'][1],0);self.assertEqual(d['GenericType'][1],0)
                model=rows[d['Appearance'][1]]['Model'];self.assertIn((model,2052),hak);self.assertTrue((folder/'geometry-source'/(model+'.dwk')).exists())
            self.assertEqual({(round(d['X'][1],2),round(d['Y'][1],2)) for _,d in doors},{(25,18),(25,20),(30,35.6),(40,35.6)})
            self.assertFalse(any(o[1]['Tag'][1].decode().startswith('aw_sign') for o in git['Placeable List'][1]))
