"""Tile-sized room plans and routed corridors; the same plan drives preview/export."""
import heapq
import math
from .nwn.area_tools import tile, rotate_corners

TILESETS={'castle':'tic01','dungeon':'tde01','cave':'tdm01','forest':'ttf01'}
# Native terrain corner patterns verified against the installed .set resources.
TILES={'castle':(116,36,28,29,30,31),'dungeon':(5,4,0,1,2,3),'cave':(5,103,0,1,2,3),'forest':(6,5,0,1,2,3)}

def cells(r):return {(x,y) for x in range(r['x'],r['x']+r['width']) for y in range(r['y'],r['y']+r['height'])}
def center(r):return ((r['x']+r['width']/2)*10,(r['y']+r['height']/2)*10)
def port(r,side):
    x=r['x']+r['width']//2;y=r['y']+r['height']//2
    return {'north':(x,r['y']+r['height']),'south':(x,r['y']-1),'east':(r['x']+r['width'],y),'west':(r['x']-1,y)}[side]
def exit_point(r,side,inside=2):
    x,y=center(r)
    return {'north':(x,(r['y']+r['height'])*10-inside),'south':(x,r['y']*10+inside),'east':((r['x']+r['width'])*10-inside,y),'west':(r['x']*10+inside,y)}[side]

def arrange(area):
    a=dict(area);count=a['room_count'];w=a['width'];h=a['height']
    options=[]
    for cols in range(1,count+1):
        rows=math.ceil(count/cols);rw=min(3,(w-2-(cols-1)*3)//cols);rh=min(3,(h-2-(rows-1)*3)//rows)
        if rw>=2 and rh>=2:options.append((abs(cols/rows-w/h),-rw*rh,cols,rows,rw,rh))
    if not options:raise ValueError('The requested rooms do not fit. Increase the area size or reduce the room count.')
    _,_,cols,rows,rw,rh=min(options);old=a['rooms'];result=[]
    for i in range(count):
        r=dict(old[i]) if i<len(old) else dict(id=f"r_{a['id'][:9]}_{i+1}",name='Room '+str(i+1),description='',purpose='Exploration')
        r.update(x=1+(i%cols)*(rw+3),y=1+(i//cols)*(rh+3),width=rw,height=rh);result.append(r)
    a['rooms']=result;return a

def route(start,end,blocked,w,h):
    queue=[(0,0,start)];came={};cost={start:0}
    while queue:
        _,g,cur=heapq.heappop(queue)
        if cur==end:
            result=[cur]
            while cur in came:cur=came[cur];result.append(cur)
            return list(reversed(result))
        if g!=cost[cur]:continue
        for dx,dy in ((1,0),(0,1),(-1,0),(0,-1)):
            nxt=(cur[0]+dx,cur[1]+dy)
            if not (1<=nxt[0]<w-1 and 1<=nxt[1]<h-1) or nxt in blocked:continue
            ng=g+1
            if ng<cost.get(nxt,10**9):cost[nxt]=ng;came[nxt]=cur;heapq.heappush(queue,(ng+abs(nxt[0]-end[0])+abs(nxt[1]-end[1]),ng,nxt))
    raise ValueError('No corridor fits between the chosen exits. Move the rooms, change exit sides, or use an exit transition.')

def doorway_plan(area,connections):
    """Choose stock doorway slots without letting adjacent frames overlap."""
    if area['type']=='forest':return {}
    rooms={r['id']:r for r in area['rooms']};slots=[]
    for c in connections:
        if c['kind']!='corridor' or c['from_room'] not in rooms or c['to_room'] not in rooms:continue
        for rid,side in ((c['from_room'],c['from_side']),(c['to_room'],c['to_side'])):
            r=rooms[rid];candidates=[];vertical=side in ('east','west');length=r['height'] if vertical else r['width']
            for offset in sorted(range(length),key=lambda n:abs(n-length//2)):
                px,py=port(r,side)
                if vertical:py=r['y']+offset
                else:px=r['x']+offset
                vx,vy={'east':(1,0),'west':(-1,0),'north':(0,1),'south':(0,-1)}[side];ix,iy=px-vx,py-vy
                plane=px if side=='east' else px+1 if side=='west' else py if side=='north' else py+1
                removed={(plane,py),(plane,py+1)} if vertical else {(px,plane),(px+1,plane)}
                required={(x+dx,y+dy) for x,y in ((ix,iy),(px,py)) for dx,dy in ((0,0),(0,1),(1,0),(1,1))}-removed
                d=dict(room=rid,side=side,inside=(ix,iy),outside=(px,py),x=(ix+px+1)*5,y=(iy+py+1)*5)
                candidates.append((d,removed,required))
            slots.append(((rid,side),candidates))
    attempts=0
    def choose(index,removed,required,chosen):
        nonlocal attempts
        attempts+=1
        if attempts>10000:return None
        if index==len(slots):return chosen
        key,candidates=slots[index]
        for door,cut,keep in candidates:
            if cut&required or keep&removed:continue
            found=choose(index+1,removed|cut,required|keep,chosen|{key:door})
            if found is not None:return found
        return None
    result=choose(0,set(),set(),{})
    if result is None:raise ValueError(area['name']+': not enough wall space for these doorways; enlarge a room or change exit sides')
    return result

def plan(p):
    result={}
    for a in p['areas']:
        rooms={r['id']:r for r in a['rooms']};floor=set();paths=[];doorways=doorway_plan(a,p['connections'])
        for r in a['rooms']:
            for other in a['rooms']:
                if r['id']>=other['id']:continue
                if not (r['x']+r['width']+2<=other['x'] or other['x']+other['width']+2<=r['x'] or r['y']+r['height']+2<=other['y'] or other['y']+other['height']+2<=r['y']):
                    raise ValueError(a['name']+': leave at least two tiles between '+r['name']+' and '+other['name'])
            floor|=cells(r)
        room_floor=set(floor)
        for c in p['connections']:
            if c['kind']!='corridor' or c['from_room'] not in rooms or c['to_room'] not in rooms:continue
            r1=rooms[c['from_room']];r2=rooms[c['to_room']];start=doorways.get((r1['id'],c['from_side']),{}).get('outside',port(r1,c['from_side']));end=doorways.get((r2['id'],c['to_side']),{}).get('outside',port(r2,c['to_side']));blocked=set(room_floor)
            for r in a['rooms']:
                if r['id'] not in (r1['id'],r2['id']):
                    blocked|={(x,y) for x in range(r['x']-1,r['x']+r['width']+1) for y in range(r['y']-1,r['y']+r['height']+1)}
            for prev in paths:
                if not {prev['from_room'],prev['to_room']} & {r1['id'],r2['id']}:
                    blocked|={(x+dx,y+dy) for x,y in prev['cells'] for dx,dy in ((0,0),(1,0),(-1,0),(0,1),(0,-1))}
            blocked.discard(start);blocked.discard(end)
            path=route(start,end,blocked,a['width'],a['height']);floor.update(path)
            paths.append(dict(id=c['id'],from_room=r1['id'],to_room=r2['id'],cells=path))
        vertices={(x+dx,y+dy) for x,y in floor for dx,dy in ((0,0),(1,0),(0,1),(1,1))}
        # Two compatible stock doorway tiles face each other across the room
        # boundary. Removing their shared terrain vertices creates the wall;
        # the doorway models then supply its actual walkable opening.
        for d in doorways.values():
            x,y=d['outside']
            if d['side'] in ('east','west'):
                plane=x if d['side']=='east' else x+1
                vertices.discard((plane,y));vertices.discard((plane,y+1))
            else:
                plane=y if d['side']=='north' else y+1
                vertices.discard((x,plane));vertices.discard((x+1,plane))
        result[a['id']]={'doorways':list(doorways.values()),'width':a['width'],'height':a['height'],'floor':sorted(floor),'vertices':sorted(vertices),'corridors':paths,'tileset':TILESETS[a['type']]}
    return result

def native_tiles(template,area,layout):
    blank,full,corner,side,diagonal,inverse=TILES[area['type']]
    candidates=[((False,False,False,False),blank),((True,True,True,True),full),((False,False,True,False),corner),((True,False,True,False),side),((True,False,False,True),diagonal),((False,True,True,True),inverse)]
    vertices={tuple(v) for v in layout['vertices']};result=[]
    for y in range(area['height']):
        for x in range(area['width']):
            wanted=tuple(pos in vertices for pos in ((x,y+1),(x+1,y+1),(x,y),(x+1,y)));found=None
            for pattern,ident in candidates:
                for rotation in range(4):
                    if pattern==wanted:found=tile(template,ident,rotation);break
                    pattern=rotate_corners(pattern)
                if found is not None:break
            if found is None:raise ValueError('No stock terrain tile matches the requested room edge')
            result.append(found)
    for d in layout.get('doorways',[]):
        rotation={'east':0,'north':1,'west':2,'south':3}[d['side']]
        for cell,ori in ((d['inside'],rotation),(d['outside'],(rotation+2)%4)):
            x,y=cell;index=y*area['width']+x;old=result[index]
            expected=29 if area['type']=='castle' else 1
            if old[1]['Tile_ID'][1]!=expected or old[1]['Tile_Orientation'][1]!=ori:
                raise ValueError(area['name']+': doorway overlaps another opening; move the rooms or select a different exit side')
            result[index]=tile(old,37 if area['type']=='castle' else 6,ori)
    return result
