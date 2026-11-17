"""Measured native tile geometry: visible walls and an independently exported WOK.

Uses the installed SET/palette as the base; generated meshes/textures are our own.
All coordinates are metres. No visual-only barriers or runtime scale tricks.
"""
import configparser
import copy
import hashlib
import io
import math
import re
from .spatial import dimensions
from .nwn.gff import read,write
from .nwn.area_tools import node

def rect_contains(r,x,y):return r[0]-1e-6<=x<=r[2]+1e-6 and r[1]-1e-6<=y<=r[3]+1e-6

def plan(area,connections):
    from .layout import cells,route,port,exit_point,TILESETS
    from .doorways import settings
    rooms={r['id']:r for r in area['rooms']};rects=[];corridors=[];openings=[];doorways=[]
    for r in rooms.values():
        w,h=dimensions(r);rects.append([r['x']*10,r['y']*10,r['x']*10+w,r['y']*10+h])
    half=area['geometry']['corridor_width']/2
    def segment(a,b,halfwidth=None):
        width=half if halfwidth is None else halfwidth
        if a==b:return
        if abs(a[0]-b[0])>.001 and abs(a[1]-b[1])>.001:raise ValueError('Measured corridors must be orthogonal')
        rects.append([min(a[0],b[0])-width,min(a[1],b[1])-width,max(a[0],b[0])+width,max(a[1],b[1])+width])
    thickness=area['geometry']['wall_thickness']
    for i,a in enumerate(rects):
        for b in rects[i+1:]:
            if a[0]<b[2]+2*thickness and a[2]+2*thickness>b[0] and a[1]<b[3]+2*thickness and a[3]+2*thickness>b[1]:
                raise ValueError('Measured rooms need space for their exterior walls; separate them and connect their doorways')
    room_rects=list(zip(rooms,rects));occupied=set().union(*(cells(r) for r in rooms.values())) if rooms else set()
    for c in connections:
        endpoints=[(rooms[rid],c[side]) for rid,side in ((c['from_room'],'from_side'),(c['to_room'],'to_side')) if rid in rooms]
        if c['kind']=='corridor' and len(endpoints)==2:
            r1,s1=endpoints[0];r2,s2=endpoints[1];start=port(r1,s1);end=port(r2,s2)
            p1,p2=exit_point(r1,s1,0),exit_point(r2,s2,0)
            widths=[next((o['width'] for o in r.get('openings',[]) if o['side']==s),half*2) for r,s in endpoints]
            dx,dy={'north':(0,1),'south':(0,-1),'east':(1,0),'west':(-1,0)}[s1]
            opposite={'north':'south','south':'north','east':'west','west':'east'}
            direct=s2==opposite[s1] and abs((p2[0]-p1[0])*dy-(p2[1]-p1[1])*dx)<1e-6 and (p2[0]-p1[0])*dx+(p2[1]-p1[1])*dy>0
            if direct:
                # Follow actual apertures, including sub-tile gaps, not room-envelope centres.
                hw=min(widths)/2
                rr=[min(p1[0],p2[0])-(hw if dy else 0),min(p1[1],p2[1])-(hw if dx else 0),max(p1[0],p2[0])+(hw if dy else 0),max(p1[1],p2[1])+(hw if dx else 0)]
                for rid,other in room_rects:
                    if rid not in (r1['id'],r2['id']) and rr[0]<other[2]+thickness and rr[2]>other[0]-thickness and rr[1]<other[3]+thickness and rr[3]>other[1]-thickness:raise ValueError('A measured passage crosses another room; move its endpoints')
                if abs(widths[0]-widths[1])>1e-6:raise ValueError('Facing connected openings need matching widths')
                rects.append(rr);line=[p1,p2];path=[]
            else:
                blocked=occupied-{start,end};path=route(start,end,blocked,area['width'],area['height'])
                line=[(x*10+5,y*10+5) for x,y in path]
                if any(rect_contains(rr,*point) for rid,rr in room_rects for point in line):raise ValueError('The passage would cut through a room. Align facing openings or leave more space for a bend.')
                for r,side,at in ((r1,s1,line[0]),(r2,s2,line[-1])):
                    p=exit_point(r,side,0);elbow=(p[0],at[1]) if side in ('north','south') else (at[0],p[1])
                    width=widths[0] if r is r1 else widths[1]
                    segment(p,elbow,width/2);segment(elbow,at,width/2)
                for a,b in zip(line,line[1:]):segment(a,b)
            for (r,side),width in zip(endpoints,widths):
                p=exit_point(r,side,0);opening=dict(room=r['id'],side=side,x=p[0],y=p[1],width=width)
                rw,rh=dimensions(r);offset=p[0]-r['x']*10 if side in ('north','south') else p[1]-r['y']*10;length=rw if side in ('north','south') else rh
                if offset-width/2<.1-1e-6 or offset+width/2>length-.1+1e-6:raise ValueError('The connected opening must fit its wall with space for jambs. Add or resize its wall opening.')
                # Implicit centered doorways need the same flat approach as drawn openings.
                from .platforms import validate as validate_platforms
                projected=copy.deepcopy(r);projected.setdefault('openings',[])
                if not any(o['side']==side for o in projected['openings']):projected['openings'].append(dict(side=side,offset=offset,width=width))
                validate_platforms(projected,area['geometry'])
                openings.append(opening);d=dict(opening,**settings(c),connection=c['id'],name=c['name'],measured=True)
                if d['height']+.2>area['geometry']['wall_height']:raise ValueError('The doorway lintel must fit below the wall top')
                doorways.append(d)
            corridors.append(dict(id=c['id'],from_room=r1['id'],to_room=r2['id'],cells=path,points=line,width=min(widths)))
    # Unconnected drawn openings remain doorway recesses, never invented exits.
    linked={(o['room'],o['side']) for o in openings}
    for r in rooms.values():
        sides={o['side']:o['width'] for o in r.get('openings',[])}
        for c in connections:
            if c['kind']=='exit':
                for key,side in (('from_room','from_side'),('to_room','to_side')):
                    if c[key]==r['id']:sides.setdefault(c[side],half*2)
        for side,width in sides.items():
            if (r['id'],side) in linked:continue
            x,y=exit_point(r,side,0);dx,dy={'north':(0,1),'south':(0,-1),'east':(1,0),'west':(-1,0)}[side];hw=width/2
            if dx:rects.append([x-.6 if dx<0 else x-.1,y-hw,x+.6 if dx>0 else x+.1,y+hw])
            else:rects.append([x-hw,y-.6 if dy<0 else y-.1,x+hw,y+.6 if dy>0 else y+.1])
            openings.append(dict(room=r['id'],side=side,x=x,y=y,width=width))
    return dict(measured=True,rectangles=rects,groups=[],doorways=doorways,openings=openings,width=area['width'],height=area['height'],floor=sorted(occupied),vertices=[],corridors=corridors,tileset=TILESETS[area['type']])

def texture(wall=False):
    """Small original stone texture, stored as ordinary uncompressed NWN TGA."""
    size=128;raw=bytearray()
    for y in range(size):
        for x in range(size):
            row=y//32;xx=(x+(16 if wall and row%2 else 0))%size
            mortar=xx%32<2 or y%32<2
            shade=64 if mortar else 133+((xx//32*17+row*11)%19)+(x*13+y*7)%7
            raw.extend((shade,shade,shade,255))
    return bytes([0,0,2,0,0,0,0,0,0,0,0,0,128,0,128,0,32,40])+raw

def mesh():return dict(vertices=[],faces=[],uv=[])

def quad(m,points,material=0,uv=None):
    base=len(m['vertices']);m['vertices'].extend(points)
    m['uv'].extend(uv or [(p[0]/2,p[1]/2,0) for p in points])
    for a,b,c in ((0,1,2),(0,2,3)):
        u=[points[b][i]-points[a][i] for i in range(3)];v=[points[c][i]-points[a][i] for i in range(3)]
        if sum((u[i]*v[(i+1)%3]-u[(i+1)%3]*v[i])**2 for i in range(3))>1e-16:m['faces'].append((base+a,base+b,base+c,material))

def aabb_lines(m):
    def recurse(ids,depth=0):
        pts=[m['vertices'][v] for i in ids for v in m['faces'][i][:3]]
        lo=[min(p[j] for p in pts) for j in range(3)];hi=[max(p[j] for p in pts) for j in range(3)]
        lines=[' '*depth+' '.join(f'{n:.6f}' for n in lo+hi)+' '+str(ids[0] if len(ids)==1 else -1)]
        if len(ids)>1:
            axis=max(range(3),key=lambda j:hi[j]-lo[j]);ids=sorted(ids,key=lambda i:sum(m['vertices'][v][axis] for v in m['faces'][i][:3]));mid=len(ids)//2
            lines+=recurse(ids[:mid],depth+1)+recurse(ids[mid:],depth+1)
        return lines
    return recurse(list(range(len(m['faces']))))

def node_text(m,name,parent,kind='trimesh',bitmap='NULL',shadow=True):
    lines=[f'node {kind} {name}',f' parent {parent}',' position 0 0 0',' orientation 0 0 0 0',' wirecolor 0.6 0.6 0.6']
    if kind=='trimesh':lines+=[' ambient 1 1 1',' diffuse 1 1 1',' specular 0 0 0',' shininess 0',f' shadow {int(shadow)}',' render 1',f' bitmap {bitmap}',' tilefade '+('1' if name=='walls' else '0')]
    lines+=[' verts '+str(len(m['vertices']))]+['  '+' '.join(f'{v:.6f}' for v in p) for p in m['vertices']]
    if kind=='trimesh':lines+=[' tverts '+str(len(m['uv']))]+['  '+' '.join(f'{v:.6f}' for v in p) for p in m['uv']]
    lines+=[' faces '+str(len(m['faces']))]+[f'  {a} {b} {c} 1 {a if kind=="trimesh" else 0} {b if kind=="trimesh" else 0} {c if kind=="trimesh" else 0} {mat}' for a,b,c,mat in m['faces']]
    if kind=='aabb':
        tree=aabb_lines(m);lines+=[' aabb '+tree[0]]+tree[1:]
    return '\n'.join(lines+['endnode'])+'\n'

def tile_meshes(area,layout):
    """Coordinate-compressed union, split on tile edges so adjacent WOKs agree."""
    rects=layout['rectangles'];w,h=area['width']*10,area['height']*10;t=area['geometry']['wall_thickness'];height=area['geometry']['wall_height']
    xs=sorted({float(i) for i in range(0,w+1,10)}|{r[i] for r in rects for i in (0,2)})
    ys=sorted({float(i) for i in range(0,h+1,10)}|{r[i] for r in rects for i in (1,3)})
    from .platforms import platform_rect,stair_rect,inside,elevation
    structures=[];xx=set(xs);yy=set(ys)
    for room in area['rooms']:
        for original in room.get('platforms',[]):
            p=dict(original,x=original['x']+room['x']*10,y=original['y']+room['y']*10);structures.append(p)
            for r in (platform_rect(p),stair_rect(p)):xx.update((r[0],r[2]));yy.update((r[1],r[3]))
            sr=stair_rect(p);vertical=p['stair_side'] in ('north','south');lo,hi=(sr[1],sr[3]) if vertical else (sr[0],sr[2])
            (yy if vertical else xx).update(lo+(hi-lo)*i/p['steps'] for i in range(1,p['steps']))
    xs=sorted(xx);ys=sorted(yy)
    if len(xs)*len(ys)>100000:raise ValueError('Measured layout is too complex; simplify the corridor graph')
    occupied={(i,j) for i in range(len(xs)-1) for j in range(len(ys)-1) if any(rect_contains(r,(xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2) for r in rects)}
    regions={};visible={}
    for i,j in occupied:
        x,y=(xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2
        region=next(((p,kind) for p in structures for kind,r in (('platform',platform_rect(p)),('stairs',stair_rect(p))) if inside(r,x,y)),(None,'floor'))
        regions[i,j]=region;visible[i,j]=elevation(region,x,y,True)
    result={}
    def get(tx,ty):
        if not 0<=tx<area['width'] or not 0<=ty<area['height']:raise ValueError('Measured walls extend outside the area boundary')
        key=(tx,ty)
        if key not in result:result[key]=(mesh(),mesh(),mesh())
        return result[key]
    # Walkable and nonwalkable ground cover every used tile; no unclassified gaps.
    used={(int((xs[i]+xs[i+1])/20),int((ys[j]+ys[j+1])/20)) for i,j in occupied}
    walls=[]
    for i,j in occupied:
        x1,x2,y1,y2=xs[i],xs[i+1],ys[j],ys[j+1]
        for di,dj,rect in [(-1,0,[x1-t,y1,x1,y2]),(1,0,[x2,y1,x2+t,y2]),(0,-1,[x1,y1-t,x2,y1]),(0,1,[x1,y2,x2,y2+t])]:
            if (i+di,j+dj) not in occupied:walls.append(rect)
    # Close the outside corner squares as well as the straight wall strips.
    corners=set()
    for i,j in occupied:
        for di,dj,x,y in [(-1,-1,xs[i],ys[j]),(-1,1,xs[i],ys[j+1]),(1,-1,xs[i+1],ys[j]),(1,1,xs[i+1],ys[j+1])]:
            if (i+di,j) not in occupied and (i,j+dj) not in occupied and (i+di,j+dj) not in occupied:
                corners.add((min(x,x+di*t),min(y,y+dj*t),max(x,x+di*t),max(y,y+dj*t)))
    walls.extend(sorted(corners))
    for r in walls:
        for tx in range(int(r[0]//10),int((r[2]-1e-7)//10)+1):
            for ty in range(int(r[1]//10),int((r[3]-1e-7)//10)+1):used.add((tx,ty))
    for i in range(len(xs)-1):
        for j in range(len(ys)-1):
            tx,ty=int((xs[i]+xs[i+1])/20),int((ys[j]+ys[j+1])/20)
            if (tx,ty) not in used:continue
            floor,wall,walk=get(tx,ty);ox,oy=tx*10+5,ty*10+5;x1,x2,y1,y2=xs[i]-ox,xs[i+1]-ox,ys[j]-oy,ys[j+1]-oy
            region=regions.get((i,j),(None,'floor'))
            points=[(x,y,elevation(region,x+ox,y+oy)) for x,y in ((x1,y1),(x2,y1),(x2,y2),(x1,y2))];quad(walk,points,4 if (i,j) in occupied else 7)
            if (i,j) in occupied:quad(floor,[(x,y,visible[i,j]) for x,y,z in points],0,[( (x+ox)/2,(y+oy)/2,0) for x,y,z in points])
    # Render each riser and platform side. Only true height discontinuities
    # block walking; the ramp is continuous across the visible step risers.
    for i,j in occupied:
        tx,ty=int((xs[i]+xs[i+1])/20),int((ys[j]+ys[j+1])/20);floor,wall,walk=get(tx,ty);ox,oy=tx*10+5,ty*10+5
        x1,x2,y1,y2=xs[i],xs[i+1],ys[j],ys[j+1]
        for di,dj,a,b in ((0,-1,(x1,y1),(x2,y1)),(1,0,(x2,y1),(x2,y2)),(0,1,(x2,y2),(x1,y2)),(-1,0,(x1,y2),(x1,y1))):
            other=(i+di,j+dj)
            if other not in occupied:continue
            hi,lo=visible[i,j],visible[other]
            if hi>lo+1e-7:
                points=[(a[0]-ox,a[1]-oy,lo),(b[0]-ox,b[1]-oy,lo),(b[0]-ox,b[1]-oy,hi),(a[0]-ox,a[1]-oy,hi)]
                quad(floor,points,0,[( (x+ox+y+oy)/2,z/2,0) for x,y,z in points])
            upper=[elevation(regions[i,j],*pt) for pt in (a,b)];lower=[elevation(regions[other],*pt) for pt in (a,b)]
            if sum(upper)>sum(lower)+1e-7:
                quad(walk,[(a[0]-ox,a[1]-oy,lower[0]),(b[0]-ox,b[1]-oy,lower[1]),(b[0]-ox,b[1]-oy,upper[1]),(a[0]-ox,a[1]-oy,upper[0])],2)
    for r in walls:
        for tx in range(int(r[0]//10),int((r[2]-1e-7)//10)+1):
            for ty in range(int(r[1]//10),int((r[3]-1e-7)//10)+1):
                floor,wall,walk=get(tx,ty);ox,oy=tx*10+5,ty*10+5
                x1,x2=max(r[0],tx*10)-ox,min(r[2],tx*10+10)-ox;y1,y2=max(r[1],ty*10)-oy,min(r[3],ty*10+10)-oy
                bottom=[(x1,y1,0),(x2,y1,0),(x2,y2,0),(x1,y2,0)];top=[(x,y,height) for x,y,z in bottom]
                quad(wall,top)
                for i in range(4):
                    a,b=bottom[i],bottom[(i+1)%4];points=[a,b,top[(i+1)%4],top[i]]
                    uv=[((x+ox+y+oy)/2,z/2,0) for x,y,z in points];quad(wall,points,0,uv);quad(walk,points,2)
    # Lintels are overhead visual geometry; do not lay an impassable WOK face
    # across the floor beneath them. Jambs occupy the already blocked wall edge.
    from .doorways import frame_boxes,box
    for d in layout.get('doorways',[]):
        for x1,y1,z1,x2,y2,z2 in frame_boxes(d,t,height):
            for tx in range(math.floor(x1/10),math.floor((x2-1e-7)/10)+1):
                for ty in range(math.floor(y1/10),math.floor((y2-1e-7)/10)+1):
                    floor,wall,walk=get(tx,ty);ox,oy=tx*10+5,ty*10+5
                    box(wall,(max(x1,tx*10)-ox,max(y1,ty*10)-oy,z1),(min(x2,tx*10+10)-ox,min(y2,ty*10+10)-oy,z2))
    for x in range(area['width']):
        for y in range(area['height']):
            if (x,y) not in result:
                floor,wall,walk=get(x,y);quad(walk,[(-5,-5,0),(5,-5,0),(5,5,0),(-5,5,0)],7)
    # Shared vertex indices are required for adjoining walkable triangles.
    for floor,wall,walk in result.values():
        vertices=[];lookup={};remap={}
        for index,p in enumerate(walk['vertices']):
            key=tuple(round(v,6) for v in p)
            if key not in lookup:lookup[key]=len(vertices);vertices.append(key)
            remap[index]=lookup[key]
        walk['vertices']=vertices
        walk['faces']=[(remap[a],remap[b],remap[c],mat) for a,b,c,mat in walk['faces']]
    return result

def minimap(layout,tx,ty):
    size=32;raw=bytearray()
    for row in range(size):
        for col in range(size):
            x=tx*10+(col+.5)*10/size;y=ty*10+(size-row-.5)*10/size
            inside=any(rect_contains(r,x,y) for r in layout['rectangles'])
            shade=165 if inside else 18
            raw.extend((shade,shade,shade,255))
    return bytes([0,0,2,0,0,0,0,0,0,0,0,0,size,0,size,0,32,40])+raw

def path_nodes(meshes):
    """Coarse edge connectivity; the WOK remains the final collision authority.

    PathNode N is a north-only dead end, not a generic walkable floor. Match
    shared boundary edges at their actual height, including raised tile seams.
    https://nwn.wiki/spaces/NWN1/pages/139689996/Tile+Path+Nodes
    """
    edges={};ports={key:set() for key in meshes}
    for key,(_,_,walk) in meshes.items():
        tx,ty=key
        for face in walk['faces']:
            if face[3]!=4:continue
            vs=[walk['vertices'][i] for i in face[:3]]
            for a,b in zip(vs,vs[1:]+vs[:1]):
                side=next((side for side,axis,value in ((0,1,5),(1,0,-5),(2,1,-5),(3,0,5)) if abs(a[axis]-value)<1e-6 and abs(b[axis]-value)<1e-6),None)
                if side is None:continue
                edge=tuple(sorted(tuple(round(v,6) for v in (p[0]+tx*10+5,p[1]+ty*10+5,p[2])) for p in (a,b)))
                edges.setdefault(edge,set()).add((key,side))
    for links in edges.values():
        if len({key for key,side in links})==2:
            for key,side in links:ports[key].add(side)
    patterns={'T':set(),'N':{0},'L':{0,2},'H':{1,2},'I':{0,1,2},'A':{0,1,2,3}}
    return {key:next((letter,str(rotation*90)) for letter,sides in patterns.items() for rotation in range(4) if {(s+rotation)%4 for s in sides}==present) for key,present in ports.items()}

def set_sections(cfg):
    """Aurora reads SET sections sequentially, unlike ConfigParser.

    New TILE sections must precede GROUPS, even when appended to a cloned
    config. Each tile's door/sound sections immediately follow that tile.
    https://nwn.wiki/spaces/NWN1/pages/38175567/SET
    """
    def count(section,key='Count'):
        try:n=int(cfg[section][key])
        except (KeyError,ValueError):raise ValueError('Tileset is missing a valid '+section+'.'+key) from None
        if not 0<=n<=8192:raise ValueError('Invalid tileset count: '+section+'.'+key)
        return n
    names=['GENERAL']
    if 'GRASS' in cfg:names.append('GRASS')
    for section,child in [('TERRAIN TYPES','TERRAIN'),('CROSSER TYPES','CROSSER'),('PRIMARY RULES','PRIMARY RULE'),('SECONDARY RULES','SECONDARY RULE'),('TILES','TILE'),('GROUPS','GROUP')]:
        # Vanilla cave tiles omit SECONDARY RULES entirely.
        if section in ('CROSSER TYPES','PRIMARY RULES','SECONDARY RULES') and section not in cfg:continue
        names.append(section)
        for i in range(count(section)):
            name=child+str(i);names.append(name)
            if name not in cfg:raise ValueError('Tileset section counts do not match definitions: missing '+name)
            if section=='TILES':
                for key,suffix in [('Doors','DOOR'),('Sounds','SOUND')]:
                    names.extend(name+suffix+str(j) for j in range(count(name,key)))
    missing=set(names)-set(cfg.sections());extra=set(cfg.sections())-set(names)
    if missing or extra:raise ValueError('Tileset section counts do not match definitions: '+', '.join(sorted(missing|extra)[:8]))
    return names

def validate_set(raw):
    """Reject files that a dictionary-style INI parser silently accepts."""
    if not raw.endswith(b'\r\n') or re.search(rb'(?<!\r)\n|\r(?!\n)',raw):
        raise ValueError('Aurora tilesets require Windows CRLF line endings and a final newline')
    cfg=configparser.ConfigParser(interpolation=None);cfg.optionxform=str
    cfg.read_string(raw.decode('latin1'))
    if cfg.sections()!=set_sections(cfg):raise ValueError('Aurora tileset sections are out of order; all tiles must precede groups')
    return cfg

def serialize_set(cfg):
    ordered=configparser.ConfigParser(interpolation=None);ordered.optionxform=str
    for name in set_sections(cfg):ordered[name]=dict(cfg[name])
    out=io.StringIO();ordered.write(out,space_around_delimiters=False)
    raw=out.getvalue().replace('\n','\r\n').encode('latin1')
    validate_set(raw)
    return raw

def export(area,layout,game,namespace,door_registry=None):
    """Return generated HAK resources and the actual area tile IDs."""
    from .layout import TILES
    setname='r'+hashlib.sha256((namespace+area['id']).encode()).hexdigest()[:8]
    from .doorways import Registry,BEARING
    from .area_presets import material,stone_texture
    finish=material(area)
    own_registry=door_registry is None
    if own_registry:door_registry=Registry(game) if layout.get('doorways') else None
    layout=copy.deepcopy(layout)
    for d in layout.get('doorways',[]):
        if finish:d['wood']=finish['wood']
        door_registry.register(d,setname)
    cfg=configparser.ConfigParser(strict=False);cfg.optionxform=str;cfg.read_string(game.get(layout['tileset'],2013).decode('latin1'))
    palette=copy.deepcopy(read(game.get(layout['tileset']+'palstd',2030))[1]);resources={};tiles={};start=int(cfg['TILES']['Count']);count=start
    floor_tex=setname+'f';wall_tex=setname+'w';resources[floor_tex,3]=stone_texture(finish) if finish else texture();resources[wall_tex,3]=stone_texture(finish,True) if finish else texture(True)
    from .carpets import tile_meshes as carpet_meshes,texture as carpet_texture
    carpets=carpet_meshes(area);colors=sorted({color for tile in carpets.values() for color in tile});carpet_textures={color:setname+'c'+str(i) for i,color in enumerate(colors)}
    for color,resref in carpet_textures.items():resources[resref,3]=carpet_texture(color)
    meshes=tile_meshes(area,layout);paths=path_nodes(meshes)
    for (x,y),(floor,wall,walk) in sorted(meshes.items()):
        name=setname+f'{x:02x}{y:02x}';root=f'node dummy {name}\n parent NULL\nendnode\n'
        body=f'newmodel {name}\nsetsupermodel {name} NULL\nclassification TILE\nsetanimationscale 1\nbeginmodelgeom {name}\n'+root
        if floor['faces']:body+=node_text(floor,'floor',name,bitmap=floor_tex)
        if wall['faces']:body+=node_text(wall,'walls',name,bitmap=wall_tex)
        for color,m in carpets.get((x,y),{}).items():body+=node_text(m,'carpet_'+color,name,bitmap=carpet_textures[color],shadow=False)
        body+=node_text(walk,'walk',name,'aabb')+f'endmodelgeom {name}\ndonemodel {name}\n'
        resources[name,2002]=body.encode();resources[name,2016]=(f'#MAXWALKMESH ASCII\nbeginwalkmeshgeom {name}\n'+node_text(walk,'walk',name,'aabb')+f'endwalkmeshgeom {name}\n').encode()
        template=dict(cfg['TILE'+str(TILES[area['type']][0])]);template.update(Model=name,Doors='0',Sounds='0',ImageMap2D=name+'m',PathNode=paths[x,y][0],Orientation=paths[x,y][1])
        template.pop('VisibilityNode',None);template.pop('VisibilityOrientation',None)
        resources[name+'m',3]=minimap(layout,x,y)
        hooks=[]
        for d in layout.get('doorways',[]):
            if 'appearance' not in d:continue
            # Boundary hooks belong to the tile on the room's inside edge.
            ix=d['x']+(.001 if d['side']=='west' else -.001 if d['side']=='east' else 0)
            iy=d['y']+(.001 if d['side']=='south' else -.001 if d['side']=='north' else 0)
            if (int(ix//10),int(iy//10))==(x,y):hooks.append(d)
        template['Doors']=str(len(hooks));cfg['TILE'+str(count)]=template
        from .doorways import dummy
        door_nodes=''
        for i,d in enumerate(hooks):
            local=(d['x']-x*10-5,d['y']-y*10-5,0)
            cfg[f'TILE{count}DOOR{i}']={'Type':str(d['appearance']),'X':str(local[0]),'Y':str(local[1]),'Z':'0.0','Orientation':str(BEARING[d['side']])}
            door_nodes+=dummy(name+f'_D{i+1:02d}',name,local)
        resources[name,2002]=resources[name,2002].replace(f'endmodelgeom {name}'.encode(),(door_nodes+f'endmodelgeom {name}').encode())
        tiles[x,y]=count;count+=1
    cfg['GENERAL']['Name']=setname;cfg['TILES']['Count']=str(count)
    # One authored group lets Aurora repaint the whole measured layout intact.
    group=int(cfg['GROUPS']['Count']);cfg['GROUPS']['Count']=str(group+1)
    blank=TILES[area['type']][0];ids=[tiles.get((x,y),blank) for y in range(area['height']) for x in range(area['width'])]
    cfg['GROUP'+str(group)]={'Name':'RoleWeaverMeasured','StrRef':'-1','Rows':str(area['height']),'Columns':str(area['width']),**{'Tile'+str(i):str(v) for i,v in enumerate(ids)}}
    # Aurora identifies the group by its first tile model resource.
    main=palette[1]['MAIN'][1];category=max((n[1].get('ID',(0,0))[1] for n in main),default=0)+1
    main.append(node(0,NAME=(10,b'Role Weaver measured layout'),ID=(0,category),LIST=(15,[node(0,NAME=(10,area['name'].encode('utf-8')),RESREF=(11,(setname+'0000').encode()))])))
    resources[setname+'palstd',2030]=write(b'ITP V3.2',palette)
    resources[setname,2013]=serialize_set(cfg)
    if own_registry and door_registry:resources.update(door_registry.export())
    return resources,dict(layout,tileset=setname,measured_tiles=ids)
