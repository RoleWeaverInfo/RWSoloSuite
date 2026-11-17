"""Fitted native doors for measured interiors (original meshes and textures).

Doors use doortypes.2da Appearance rows, ordinary Door GIT objects, native
animations and closed/open DWK states. No NWNX or runtime visual scaling.
"""
import hashlib
import math
from .custom_assets import table
from .nwn.area_tools import door
from .nwn.gff import write

DEFAULT = dict(style='wood', height=2.4, leaves='auto')
BEARING = dict(north=0, east=270, south=180, west=90)

def settings(connection):
    return {**DEFAULT, **connection.get('doorway', {})}

def validate(project):
    rooms={r['id']:(a,r) for a in project['areas'] for r in a['rooms']}
    for c in project['connections']:
        d=c.get('doorway')
        if d is None:continue
        if not isinstance(d,dict) or set(d)-set(DEFAULT):raise ValueError('Invalid doorway settings')
        d=settings(c)
        if d['style'] not in ('wood','open','none') or d['leaves'] not in ('auto','single','double'):raise ValueError('Choose a wooden door, framed opening or open passage')
        if type(d['height']) not in (int,float) or not math.isfinite(d['height']) or not 1.8<=d['height']<=4:raise ValueError('Door height must be from 1.8 to 4 metres')
        if c['from_room'] not in rooms or c['to_room'] not in rooms:continue
        a,r=rooms[c['from_room']];b,_=rooms[c['to_room']]
        if c['kind']!='corridor' or a['id']!=b['id'] or not a.get('geometry'):raise ValueError('Fitted door settings require a corridor in one measured area')
        if d['height']+.2>a['geometry']['wall_height']:raise ValueError('The doorway lintel must fit below the wall top')

def box(mesh,lo,hi,material=0):
    from .measured_geometry import quad
    x,y,z=lo;X,Y,Z=hi
    for pts in ([(x,y,z),(X,y,z),(X,y,Z),(x,y,Z)],[(X,y,z),(X,Y,z),(X,Y,Z),(X,y,Z)],[(X,Y,z),(x,Y,z),(x,Y,Z),(X,Y,Z)],[(x,Y,z),(x,y,z),(x,y,Z),(x,Y,Z)],[(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]):quad(mesh,pts,material)

def leaf_specs(width,leaves):
    double=leaves=='double' or (leaves=='auto' and width>=1.8)
    return [(-width/2,0,width/2,1),(width/2,-width/2,0,-1)] if double else [(-width/2,0,width,1)]

def collision(width,height,leaves,state):
    from .measured_geometry import mesh
    result=mesh();angle={'closed':0,'open1':-math.pi/2,'open2':math.pi/2}[state]
    for hinge,lo,hi,direction in leaf_specs(width,leaves):
        part=mesh();box(part,(lo,-.055,0),(hi,.055,height),7)
        theta=angle*direction;ct,st=math.cos(theta),math.sin(theta);base=len(result['vertices'])
        result['vertices'] += [(hinge+x*ct-y*st,x*st+y*ct,z) for x,y,z in part['vertices']]
        result['uv']+=part['uv'];result['faces'] += [(a+base,b+base,c+base,m) for a,b,c,m in part['faces']]
    return result

def dummy(name,parent,position=(0,0,0)):
    return f'node dummy {name}\n parent {parent}\n position '+ ' '.join(map(str,position))+'\n orientation 0 0 1 0\nendnode\n'

def door_resources(name,width,height,leaves,wood=None):
    from .measured_geometry import mesh,node_text,quad
    tex=name+'t';root=name+'_DWK';dwk='';body=dummy(name,'NULL')
    for suffix,z in [('grnd',0),('impc',height/2),('hhit',height*.8),('head',height)]:body+=dummy(name+suffix,name,(0,0,z))
    for i,(hinge,lo,hi,direction) in enumerate(leaf_specs(width,leaves)):
        parent='hinge'+str(i);body+=dummy(parent,name,(hinge,0,0))
        m=mesh();box(m,(lo+.012,-.045,.015),(hi-.012,.045,height-.015))
        body+=node_text(m,'leaf'+str(i),parent,bitmap=tex)
        metal=mesh()
        for z in (height*.22,height*.78):box(metal,(lo+.03,-.058,z-.035),(hi-.03,.058,z+.035))
        hx=hi-.13 if direction==1 else lo+.13
        box(metal,(hx-.035,-.10,height*.48),(hx+.035,.10,height*.48+.15))
        body+=node_text(metal,'iron'+str(i),parent).replace('ambient 1 1 1','ambient 0.18 0.18 0.18').replace('diffuse 1 1 1','diffuse 0.18 0.18 0.18')
    sam=mesh();points=[(-width/2,0,0),(width/2,0,0),(width/2,0,height),(-width/2,0,height)]
    quad(sam,points);quad(sam,list(reversed(points)))
    body+=node_text(sam,'sam',name,shadow=False).replace(' render 1',' render 1\n alpha 0\n selfillumcolor 0.2 0.1 1')
    for state in ('closed','open1','open2'):
        for index,y in enumerate((-.9,.9) if state=='closed' else ((-1.2,) if state=='open1' else (1.2,))):
            dwk+=dummy(name+'_DWK_dp_'+state+'_'+str(index+1),root,(0,y,0))
        dwk+=node_text(collision(width,height,leaves,state),name+'_DWK_wg_'+state,root,shadow=False).replace('render 1','render 0')
    body+=dummy(root,name)+dwk
    mdl=f'newmodel {name}\nsetsupermodel {name} NULL\nclassification Door\nsetanimationscale 1\nbeginmodelgeom {name}\n'+body+f'endmodelgeom {name}\n'
    states={'closed':(0,0),'opening1':(0,-math.pi/2),'opened1':(-math.pi/2,-math.pi/2),'closing1':(-math.pi/2,0),'opening2':(0,math.pi/2),'opened2':(math.pi/2,math.pi/2),'closing2':(math.pi/2,0),'die':(0,0),'dead':(0,0),'trans':(0,0)}
    for anim,(start,end) in states.items():
        length=1 if start!=end else .1
        mdl+=f'newanim {anim} {name}\n length {length}\n transtime 0.1\n animroot {name}\n'+dummy(name,'NULL')
        if anim!='trans':
            for i,(hinge,_,_,direction) in enumerate(leaf_specs(width,leaves)):
                mdl+=f'node dummy hinge{i}\n parent {name}\n orientationkey\n  0 0 0 1 {start*direction:.7f}\n  {length} 0 0 1 {end*direction:.7f}\n endlist\n'
                z1=-(height+.2) if anim=='dead' else 0;z2=-(height+.2) if anim in ('die','dead') else 0
                mdl+=f' positionkey\n  0 {hinge} 0 {z1}\n  {length} {hinge} 0 {z2}\n endlist\nendnode\n'
        alpha=.25 if anim=='trans' else 0
        mdl+=f'node trimesh sam\n parent {name}\n alphakey\n  0 {alpha}\n  {length} {alpha}\n endlist\nendnode\n'
        mdl+=f'doneanim {anim} {name}\n'
    mdl+=f'donemodel {name}\n'
    from .area_presets import rgb
    base=rgb(wood) if wood else (99,62,30);raw=bytearray()
    for y in range(64):
        for x in range(64):
            shade=-25 if x%16<1 else (x*7+y*3)%11
            raw.extend((*[max(0,min(255,c+shade)) for c in reversed(base)],255))
    tga=bytes([0,0,2,0,0,0,0,0,0,0,0,0,64,0,64,0,32,40])+raw
    # NWN resource type 2052 is DWK (2053 is PWK).
    return {(name,2002):mdl.encode(),(name,2052):('#NWmax DWKMESH ASCII\n'+dwk).encode(),(tex,3):tga}

class Registry:
    def __init__(self,game,archives=()):
        raw=next((a['doortypes',2017] for a in archives if ('doortypes',2017) in a),None)
        self.raw=raw if raw is not None else game.get('doortypes',2017)
        self.rows=table(self.raw);self.columns=list(next(iter(self.rows.values())))
        required={'Label','Model','TileSet','TemplateResRef','StringRefGame','BlockSight','VisibleModel','SoundAppType'}
        if not required<=set(self.columns):raise ValueError('The selected doortypes.2da is missing native door columns')
        self.resources={};self.additions=[];self.cache={}

    def register(self,d,setname):
        if d['style']!='wood':return
        key=(setname,round(d['width'],4),d['height'],d['leaves'],d.get('wood'))
        if key not in self.cache:
            name='rd'+hashlib.sha256(repr(key).encode()).hexdigest()[:10]
            index=max(self.rows,default=-1)+1+len(self.additions)
            values=dict(Label=name,Model=name,TileSet=setname,TemplateResRef=name,StringRefGame='5350',BlockSight='1',VisibleModel='1',SoundAppType='0')
            self.additions.append(str(index)+' '+' '.join(values.get(c,'****') for c in self.columns))
            self.resources.update(door_resources(name,d['width'],d['height'],d['leaves'],d.get('wood')))
            blueprint=door(name,'Wooden door','',0.,0.,0,appearance=index)
            blueprint[1].update(GenericType=(0,0),TemplateResRef=(11,name.encode()),LinkedToFlags=(0,0))
            self.resources[name,2042]=write(b'UTD V3.2',(0xffffffff,blueprint[1]))
            self.cache[key]=(index,name)
        d['appearance'],d['model']=self.cache[key]

    def export(self):
        if self.additions:
            # Retain every original/custom row and extra column, with highest HAK priority.
            self.resources['doortypes',2017]=self.raw.rstrip(b'\r\n')+b'\r\n'+('\r\n'.join(self.additions)+'\r\n').encode()
        return self.resources

def frame_boxes(d,thickness,wall_height=None):
    if d['style']=='none':return []
    x,y,w,h=d['x'],d['y'],d['width'],d['height'];trim=.16
    # Jambs stay outside the clear aperture; lintel remains above head height.
    boxes=[(-w/2-trim,0,0,-w/2,thickness,h+.2),(w/2,0,0,w/2+trim,thickness,h+.2),(-w/2,0,h,w/2,thickness,wall_height or h+.2)]
    theta=math.radians(BEARING[d['side']]);ct,st=math.cos(theta),math.sin(theta)
    result=[]
    for x1,y1,z1,x2,y2,z2 in boxes:
        pts=[(x+xx*ct-yy*st,y+xx*st+yy*ct) for xx in (x1,x2) for yy in (y1,y2)]
        result.append((min(p[0] for p in pts),min(p[1] for p in pts),z1,max(p[0] for p in pts),max(p[1] for p in pts),z2))
    return result
