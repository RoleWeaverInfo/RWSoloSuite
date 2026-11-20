"""Flat outdoor landscapes with continuous stone courtyards and native gates.

The same coordinate partition drives visible ground, walls and collision. Country
paths stay connected through zone interiors; only selected zones become courtyards.
"""
import copy
import math
from .spatial import dimensions
from .measured_geometry import mesh,quad,rect_contains


def validate(area):
    spec=area.get('outdoor_layout')
    if spec is None:return
    if area['type'] not in ('forest','desert','winter') or area.get('geometry'):
        raise ValueError('Courtyards require an outdoor area without measured interior geometry')
    if not isinstance(spec,dict) or set(spec)!={'courtyard_rooms','wall_height','wall_thickness','road_width'}:
        raise ValueError('Invalid outdoor courtyard settings')
    ids=spec['courtyard_rooms'];rooms={r['id'] for r in area['rooms']}
    if not isinstance(ids,list) or not ids or any(not isinstance(v,str) or v not in rooms for v in ids) or len(ids)!=len(set(ids)):
        raise ValueError('Select existing outdoor zones for the courtyard walls and paving')
    if any(r.get('native_group') for r in area['rooms']):raise ValueError('Remove native groups before generating a flat courtyard landscape')
    for key,lo,hi in [('wall_height',2,8),('wall_thickness',.2,1),('road_width',2,6)]:
        if type(spec[key]) not in (int,float) or not math.isfinite(spec[key]) or not lo<=spec[key]<=hi:
            raise ValueError('Invalid courtyard '+key)


def ribbon(points,width):
    half=width/2
    for a,b in zip(points,points[1:]):
        if a==b:continue
        if a[0]!=b[0] and a[1]!=b[1]:raise ValueError('Outdoor paths must be orthogonal')
        yield [min(a[0],b[0])-half,min(a[1],b[1])-half,max(a[0],b[0])+half,max(a[1],b[1])+half]


def cut(rect,hole):
    x,y,X,Y=rect;a,b,A,B=hole
    if a>=X or A<=x or b>=Y or B<=y:return [rect]
    result=[]
    for part in ([x,y,min(a,X),Y],[max(A,x),y,X,Y],[max(x,a),y,min(X,A),min(b,Y)],[max(x,a),max(B,y),min(X,A),Y]):
        if part[2]-part[0]>1e-7 and part[3]-part[1]>1e-7:result.append(part)
    return result


def boundaries(rects,t):
    xs=sorted({r[k] for r in rects for k in (0,2)});ys=sorted({r[k] for r in rects for k in (1,3)})
    occupied={(i,j) for i in range(len(xs)-1) for j in range(len(ys)-1) if any(rect_contains(r,(xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2) for r in rects)}
    walls=[]
    for i,j in occupied:
        x,X,y,Y=xs[i],xs[i+1],ys[j],ys[j+1]
        for di,dj,r in [(-1,0,[x-t,y-t,x,Y+t]),(1,0,[X,y-t,X+t,Y+t]),(0,-1,[x,y-t,X,y]),(0,1,[x,Y,X,Y+t])]:
            if (i+di,j+dj) not in occupied:walls.append(r)
    return walls


def plan(area,connections):
    from .layout import center,exit_point,TILESETS,cells
    validate(area);spec=area['outdoor_layout'];width=spec['road_width'];enclosed=set(spec['courtyard_rooms'])
    rooms={r['id']:r for r in area['rooms']};paving=[];roads=[];corridors=[];openings=[];gates=[];holes=[]
    for rid in enclosed:
        r=rooms[rid];w,h=dimensions(r);paving.append([r['x']*10,r['y']*10,r['x']*10+w,r['y']*10+h])
    for c in connections:
        local=[(rid,c[side]) for rid,side in ((c['from_room'],'from_side'),(c['to_room'],'to_side')) if rid in rooms]
        if c['kind']=='corridor' and len(local)==2:
            (rid,s1),(oid,s2)=local;r1,r2=rooms[rid],rooms[oid];a,b=exit_point(r1,s1,0),exit_point(r2,s2,0)
            path=[a]
            if a[0]!=b[0] and a[1]!=b[1]:
                if s1 in ('north','south'):mid=(a[1]+b[1])/2;path += [(a[0],mid),(b[0],mid)]
                else:mid=(a[0]+b[0])/2;path += [(mid,a[1]),(mid,b[1])]
            path.append(b);roads.extend(ribbon([center(r1),*path,center(r2)],width))
            corridors.append(dict(id=c['id'],from_room=rid,to_room=oid,cells=[],points=path,width=width))
            if rid in enclosed and oid in enclosed:paving.extend(ribbon(path,width))
        for rid,side in local:
            x,y=exit_point(rooms[rid],side,0);opening=dict(room=rid,side=side,x=x,y=y,width=width);openings.append(opening)
            other=c['to_room'] if c['from_room']==rid else c['from_room']
            if rid not in enclosed or other in enclosed:continue
            d=spec['wall_thickness']+.1;half=width/2
            holes.append([x-half,y-d,x+half,y+d] if side in ('north','south') else [x-d,y-half,x+d,y+half])
            if c['kind']=='corridor':
                gates.append(dict(opening,style='wood',height=min(3.,spec['wall_height']-.2),leaves='double',connection=c['id'],name=c['name'],measured=True))
    walls=boundaries(paving,spec['wall_thickness'])
    for hole in holes:walls=[part for wall in walls for part in cut(wall,hole)]
    w,h=area['width']*10,area['height']*10
    if any(r[0]<0 or r[1]<0 or r[2]>w or r[3]>h for r in walls+roads+paving):raise ValueError('Courtyard walls and roads must fit inside the area')
    return dict(outdoor=True,rectangles=[[0,0,w,h]],paving=paving,roads=roads,walls=walls,groups=[],doorways=gates,openings=openings,width=area['width'],height=area['height'],floor=sorted(set().union(*(cells(r) for r in rooms.values()))),vertices=[],corridors=corridors,tileset=TILESETS[area['type']])


def tile_meshes(area,layout):
    w,h=area['width']*10,area['height']*10;rects=layout['paving']+layout['roads']+layout['walls']
    xs=sorted({float(x) for x in range(0,w+1,10)}|{r[k] for r in rects for k in (0,2)})
    ys=sorted({float(y) for y in range(0,h+1,10)}|{r[k] for r in rects for k in (1,3)})
    if len(xs)*len(ys)>100000:raise ValueError('Courtyard is too complex; simplify the paths')
    tiles={(x,y):(mesh(),mesh(),mesh()) for x in range(area['width']) for y in range(area['height'])}
    for i in range(len(xs)-1):
        for j in range(len(ys)-1):
            x,X,y,Y=xs[i],xs[i+1],ys[j],ys[j+1];cx,cy=(x+X)/2,(y+Y)/2;tx,ty=int(cx//10),int(cy//10)
            floor,wall,walk=tiles[tx,ty];ox,oy=tx*10+5,ty*10+5
            points=[(xx-ox,yy-oy,0) for xx,yy in ((x,y),(X,y),(X,Y),(x,Y))]
            blocked=any(rect_contains(r,cx,cy) for r in layout['walls'])
            material=0 if any(rect_contains(r,cx,cy) for r in layout['paving']) else 2 if any(rect_contains(r,cx,cy) for r in layout['roads']) else 1
            quad(floor,points,material,[(xx/2,yy/2,0) for xx,yy in ((x,y),(X,y),(X,Y),(x,Y))]);quad(walk,points,7 if blocked else 4)
    from .doorways import box,frame_boxes
    wall_height=area['outdoor_layout']['wall_height']
    boxes=[(*r[:2],0,*r[2:],wall_height) for r in layout['walls']]
    for d in layout['doorways']:boxes+=frame_boxes(d,area['outdoor_layout']['wall_thickness'],wall_height)
    for x,y,z,X,Y,Z in boxes:
        for tx in range(math.floor(x/10),math.floor((X-1e-7)/10)+1):
            for ty in range(math.floor(y/10),math.floor((Y-1e-7)/10)+1):
                floor,wall,walk=tiles[tx,ty];ox,oy=tx*10+5,ty*10+5
                lo=(max(x,tx*10)-ox,max(y,ty*10)-oy,z);hi=(min(X,tx*10+10)-ox,min(Y,ty*10+10)-oy,Z)
                box(wall,lo,hi)
                if z==0:box(walk,lo,hi,2)
    # Weld WOK vertices: separate coincident triangles can break NWN pathfinding.
    for _,_,walk in tiles.values():
        vertices=[];lookup={};remap={}
        for i,p in enumerate(walk['vertices']):
            key=tuple(round(v,6) for v in p)
            if key not in lookup:lookup[key]=len(vertices);vertices.append(key)
            remap[i]=lookup[key]
        walk['vertices']=vertices;walk['faces']=[(remap[a],remap[b],remap[c],m) for a,b,c,m in walk['faces']]
    return tiles


def export(area,layout,game,namespace,registry=None):
    from .measured_geometry import export as export_tiles
    ground={'forest':'ttf01_grass01','desert':'ttd01_floor01','winter':'tts01_grass02'}[area['type']]
    modified=copy.deepcopy(area);modified['look']=dict(area.get('look',{}),material='castle_grey')
    return export_tiles(modified,layout,game,namespace,registry,meshes=tile_meshes(area,layout),floor_surfaces={1:ground,2:'tdm01_dirt01'})
