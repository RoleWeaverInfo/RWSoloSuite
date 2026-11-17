"""Native tile groups are indivisible stamps with their authored access ports."""
import configparser
import copy
import hashlib
import math
from functools import lru_cache
from .asset_catalog import installed

def turn(x,y,width,height,rotation):
    for _ in range(rotation):x,y,width,height=height-y,x,height,width
    return x,y

def rotated(record):
    d=record['definition'];rot=record['rotation'];w,h=d['width'],d['height']
    tiles=[]
    for i,ident in enumerate(d['tiles']):
        x,y=turn(i%w+.5,i//w+.5,w,h,rot);tiles.append(dict(x=int(x),y=int(y),id=ident,rotation=rot))
    ports=[];sides=['east','north','west','south']
    for p in d['ports']:
        x,y=turn(p['x']/10,p['y']/10,w,h,rot)
        ports.append(dict(x=x*10,y=y*10,side=sides[(sides.index(p['side'])+rot)%4]))
    return dict(width=h if rot%2 else w,height=w if rot%2 else h,tiles=tiles,ports=ports)

@lru_cache(maxsize=8)
def catalog(game_root,tileset):
    game=installed(game_root);raw=game.get(tileset,2013);cfg=configparser.ConfigParser(strict=False);cfg.read_string(raw.decode('latin1'));digest=hashlib.sha256(raw).hexdigest();result=[]
    from .layout import TILESETS,TILES
    kind=next(k for k,v in TILESETS.items() if v==tileset)
    default=cfg['TILE'+str(TILES[kind][1])].get('topleft','').lower();interior=cfg['GENERAL'].get('interior')=='1'
    for section in cfg.sections():
        if not section.startswith('GROUP') or not section[5:].isdigit():continue
        group=cfg[section];w=int(group['columns']);h=int(group['rows']);ids=[int(group['tile'+str(i)]) for i in range(w*h)]
        ports=[];all_wall=True;plain_boundary=True
        for i,ident in enumerate(ids):
            if ident<0 or 'TILE'+str(ident) not in cfg:
                all_wall=False;plain_boundary=False;continue
            t=cfg['TILE'+str(ident)];x,y=i%w,i//w
            all_wall &= all(t.get(k,'').lower()=='wall' for k in ('topleft','topright','bottomleft','bottomright'))
            for key,cx,cy in [('bottomleft',x,y),('bottomright',x+1,y),('topleft',x,y+1),('topright',x+1,y+1)]:
                if cx in (0,w) or cy in (0,h):plain_boundary &= t.get(key,'').lower()==default and int(t.get(key+'height','0'))==0
            for edge,side,px,py,boundary in [('top','north',x+.5,y+1,y==h-1),('bottom','south',x+.5,y,y==0),('right','east',x+1,y+.5,x==w-1),('left','west',x,y+.5,x==0)]:
                if boundary and t.get(edge,'').lower()=='doorway':ports.append(dict(x=px*10,y=py*10,side=side))
                if boundary and t.get(edge,''):plain_boundary=False
        mode='enclosed' if interior and all_wall and ports and 'room' in group['name'].lower() else ('floor_feature' if interior else 'outdoor_feature') if plain_boundary else 'unsupported'
        result.append(dict(id=tileset+'_'+section.lower(),tileset=tileset,name=group['name'],width=w,height=h,tiles=ids,ports=ports,mode=mode,source_hash=digest))
    return result

def validate_record(record,area,room):
    if not isinstance(record,dict) or set(record)!={'definition','rotation'} or type(record['rotation']) is not int or record['rotation'] not in range(4):raise ValueError('Invalid native room group')
    d=record['definition'];keys={'id','tileset','name','width','height','tiles','ports','mode','source_hash'}
    if not isinstance(d,dict) or set(d)!=keys or d['mode'] not in ('enclosed','floor_feature','outdoor_feature'):raise ValueError('This group needs terrain support that is not yet available')
    if any(not isinstance(d[k],str) or not d[k] or len(d[k])>150 for k in ('id','tileset','name','source_hash')):raise ValueError('Invalid group identity')
    if not isinstance(d['tiles'],list) or not isinstance(d['ports'],list) or len(d['ports'])>64:raise ValueError('Invalid group tile matrix or ports')
    if any(type(d[k]) is not int or not 1<=d[k]<=16 for k in ('width','height')) or len(d['tiles'])!=d['width']*d['height'] or any(type(t) is not int or not 0<=t<=65535 for t in d['tiles']):raise ValueError('Invalid native group tile matrix')
    from .layout import TILESETS
    if d['tileset']!=TILESETS[area['type']]:raise ValueError('Native group belongs to a different tileset')
    for p in d['ports']:
        if not isinstance(p,dict) or set(p)!={'x','y','side'} or p['side'] not in ('north','east','south','west') or not all(type(p[k]) in (int,float) and math.isfinite(p[k]) for k in ('x','y')):raise ValueError('Invalid group access port')
        if not (0<=p['x']<=d['width']*10 and 0<=p['y']<=d['height']*10):raise ValueError('Group access port is outside its footprint')
    layout=rotated(record)
    if (room['width'],room['height'])!=(layout['width'],layout['height']):raise ValueError('Native room groups cannot be stretched; remove the group to resize freely')

def verify_installed(project,game_root):
    for a in project['areas']:
        for r in a['rooms']:
            if not r.get('native_group'):continue
            record=r['native_group'];validate_record(record,a,r);d=record['definition']
            actual=next((g for g in catalog(str(game_root),d['tileset']) if g['id']==d['id']),None)
            if actual!=d:raise ValueError('Native group definition differs from the installed tileset; reselect '+d['name'])

def apply(project,room_id,definition,rotation=0):
    from .authoring import validate,review
    p=validate(project)
    if room_id in p.get('locked_rooms',[]):raise ValueError('Unlock this room before changing its group')
    found=next(((a,r) for a in p['areas'] for r in a['rooms'] if r['id']==room_id),None)
    if found is None:raise ValueError('Choose an existing room or zone')
    a,r=found
    if type(rotation) is not int or rotation not in range(4):raise ValueError('Choose a quarter-turn rotation')
    if definition is None:r.pop('native_group',None)
    else:
        record=dict(definition=copy.deepcopy(definition),rotation=rotation);shape=rotated(record)
        r.update(width=shape['width'],height=shape['height'],native_group=record)
    validate(p);check=review(p)
    return dict(project=p,review=check)

@lru_cache(maxsize=256)
def walk_triangles(game_root,model):
    game=installed(game_root)
    rows=[s.split() for s in game.get('surfacemat',2017).decode('latin1').splitlines()]
    allowed={int(r[0]) for r in rows if r and r[0].isdigit() and r[2]=='1'}
    lines=[line.split() for line in game.get(model,2016).decode('latin1').splitlines() if line.strip()]
    offset=(0,0,0);vertices=[];triangles=[]
    for i,t in enumerate(lines):
        if t[0]=='position':offset=tuple(map(float,t[1:4]))
        elif t[0]=='verts':vertices=[tuple(float(v)+offset[j] for j,v in enumerate(row[:3])) for row in lines[i+1:i+1+int(t[1])]]
        elif t[0]=='faces':
            for row in lines[i+1:i+1+int(t[1])]:
                if int(row[-1]) in allowed:triangles.append(tuple(vertices[int(n)] for n in row[:3]))
    return triangles

def contains(triangle,x,y):
    a,b,c=triangle;cross=lambda x,y,u,v:x*v-y*u
    det=cross(b[0]-a[0],b[1]-a[1],c[0]-a[0],c[1]-a[1])
    if abs(det)<1e-8:return False
    u=cross(x-a[0],y-a[1],c[0]-a[0],c[1]-a[1])/det
    v=cross(b[0]-a[0],b[1]-a[1],x-a[0],y-a[1])/det
    return u>=-1e-4 and v>=-1e-4 and u+v<=1.0001

def point_test(record,game_root):
    d=record['definition'];cfg=configparser.ConfigParser(strict=False);cfg.read_string(installed(game_root).get(d['tileset'],2013).decode('latin1'))
    tiles={(t['x'],t['y']):t for t in rotated(record)['tiles']}
    def test(x,y):
        t=tiles.get((int(x//10),int(y//10)))
        if t is None:return False
        angle=-t['rotation']*math.pi/2;lx=x-t['x']*10-5;ly=y-t['y']*10-5
        mx=lx*math.cos(angle)-ly*math.sin(angle);my=lx*math.sin(angle)+ly*math.cos(angle)
        return any(contains(tri,mx,my) for tri in walk_triangles(game_root,cfg['TILE'+str(t['id'])]['model']))
    return test

def prepare_navigation(project,game_root):
    """Choose a walkable arrival in native groups and return placement predicates."""
    result={}
    for a in project['areas']:
        for r in a['rooms']:
            if not r.get('native_group'):continue
            test=point_test(r['native_group'],str(game_root));cx,cy=r['width']*5,r['height']*5
            candidates=sorted(((x/2,y/2) for x in range(2,r['width']*20-1) for y in range(2,r['height']*20-1)),key=lambda p:(p[0]-cx)**2+(p[1]-cy)**2)
            entry=next((p for p in candidates if all(test(p[0]+dx,p[1]+dy) for dx,dy in ((0,0),(.5,0),(-.5,0),(0,.5),(0,-.5)))),None)
            if entry is None:raise ValueError(r['name']+': native group has no verified arrival space')
            r['_entry_point']=entry
            from .layout import exit_point
            for c in project['connections']:
                for rid,side in ((c['from_room'],c['from_side']),(c['to_room'],c['to_side'])):
                    if rid!=r['id']:continue
                    x,y=exit_point(r,side,.2);x-=r['x']*10;y-=r['y']*10
                    dx,dy=(.4,0) if side in ('north','south') else (0,.4)
                    if not all(test(x+dx*n,y+dy*n) for n in (-1,0,1)):raise ValueError(r['name']+': native feature obstructs this connection; rotate the group or choose another side')
            result[r['id']]=lambda x,y,t=test,r=r:t(x-r['x']*10,y-r['y']*10)
    return result

@lru_cache(maxsize=16)
def preview(game_root,tileset,ident,rotation=0):
    from .model_preview import svg,geometry
    d=next((g for g in catalog(game_root,tileset) if g['id']==ident),None)
    if d is None or rotation not in range(4):raise ValueError('Unknown native group')
    game=installed(game_root);cfg=configparser.ConfigParser(strict=False);cfg.read_string(game.get(tileset,2013).decode('latin1'))
    vertices=[];faces=[]
    for t in rotated(dict(definition=d,rotation=rotation))['tiles']:
        if t['id']<0:continue
        mesh=geometry(game.get(cfg['TILE'+str(t['id'])]['model'],2002));base=len(vertices);angle=rotation*math.pi/2
        vertices.extend((x*math.cos(angle)-y*math.sin(angle)+t['x']*10+5,x*math.sin(angle)+y*math.cos(angle)+t['y']*10+5,z) for x,y,z in mesh['vertices'])
        faces.extend(tuple(i+base for i in f) for f in mesh['faces'])
    return svg(dict(vertices=vertices,faces=faces),d['name'])
