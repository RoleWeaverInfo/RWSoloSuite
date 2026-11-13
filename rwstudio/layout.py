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
        rows=math.ceil(count/cols);rw=min(5,(w-2-(cols-1)*3)//cols);rh=min(5,(h-2-(rows-1)*3)//rows)
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

def plan(p):
    result={}
    for a in p['areas']:
        rooms={r['id']:r for r in a['rooms']};floor=set();paths=[]
        for r in a['rooms']:
            for other in a['rooms']:
                if r['id']>=other['id']:continue
                if not (r['x']+r['width']+2<=other['x'] or other['x']+other['width']+2<=r['x'] or r['y']+r['height']+2<=other['y'] or other['y']+other['height']+2<=r['y']):
                    raise ValueError(a['name']+': leave at least two tiles between '+r['name']+' and '+other['name'])
            floor|=cells(r)
        room_floor=set(floor)
        for c in p['connections']:
            if c['kind']!='corridor' or c['from_room'] not in rooms or c['to_room'] not in rooms:continue
            r1=rooms[c['from_room']];r2=rooms[c['to_room']];start=port(r1,c['from_side']);end=port(r2,c['to_side']);blocked=set(room_floor)
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
        result[a['id']]={'width':a['width'],'height':a['height'],'floor':sorted(floor),'vertices':sorted(vertices),'corridors':paths,'tileset':TILESETS[a['type']]}
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
    return result
