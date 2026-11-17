"""Tile-sized room plans and routed corridors; the same plan drives preview/export."""
import heapq
import math
from .spatial import dimensions
from .nwn.area_tools import tile, rotate_corners

TILESETS={'castle':'tic01','dungeon':'tde01','cave':'tdm01','forest':'ttf01','desert':'ttd01','winter':'tts01'}
# Native terrain corner patterns verified against the installed .set resources.
# 109 is the plain rich floor (floor textures only). 175 is the Bath feature:
# walkability alone is not a sufficient test for selecting generic floor tiles.
TILES={'castle':(116,109,28,29,30,31),'dungeon':(5,4,0,1,2,3),'cave':(5,103,0,1,2,3),'forest':(6,5,0,1,2,3),'desert':(6,5,0,1,2,3),'winter':(0,0,0,0,0,0)}

def cells(r):return {(x,y) for x in range(r['x'],r['x']+r['width']) for y in range(r['y'],r['y']+r['height'])}
def center(r):
    from .platforms import entry
    x,y=r['_entry_point'] if '_entry_point' in r else entry(r) if r.get('platforms') else (dimensions(r)[0]/2,dimensions(r)[1]/2)
    return r['x']*10+x,r['y']*10+y
def port(r,side):
    x=r['x']+r['width']//2;y=r['y']+r['height']//2
    return {'north':(x,r['y']+r['height']),'south':(x,r['y']-1),'east':(r['x']+r['width'],y),'west':(r['x']-1,y)}[side]
def exit_point(r,side,inside=2):
    x,y=center(r)
    port=next((p for p in r.get('openings',[]) if p['side']==side),None)
    if port:
        if side in ('north','south'):x=r['x']*10+port['offset']
        else:y=r['y']*10+port['offset']
    if r.get('native_group',{}).get('definition',{}).get('mode')=='enclosed':
        from .native_groups import rotated
        matches=[p for p in rotated(r['native_group'])['ports'] if p['side']==side]
        if len(matches)!=1:raise ValueError(r['name']+': choose the native group’s authored doorway side')
        if inside>=8:return x,y
        p=matches[0];vx,vy={'east':(1,0),'west':(-1,0),'north':(0,1),'south':(0,-1)}[side]
        return r['x']*10+p['x']-vx*inside,r['y']*10+p['y']-vy*inside
    # Arrival points in narrow rooms must not reach the opposite exit trigger.
    w,h=dimensions(r);inside=min(inside,(w if side in ('east','west') else h)/2)
    return {'north':(x,r['y']*10+h-inside),'south':(x,r['y']*10+inside),'east':(r['x']*10+w-inside,y),'west':(r['x']*10+inside,y)}[side]

def access_points(project,layouts):
    points=[d for layout in layouts.values() for d in layout.get('doorways',[])+layout.get('openings',[])]
    rooms={r['id']:r for a in project['areas'] for r in a['rooms']}
    for c in project['connections']:
        if c['kind']!='exit':continue
        for rid,side in ((c['from_room'],c['from_side']),(c['to_room'],c['to_side'])):
            r=rooms[rid]
            if min(r['width'],r['height'])!=1:continue
            x,y=exit_point(r,side,0);points.append(dict(room=rid,side=side,x=x,y=y))
    return points

def arrange(area):
    a=dict(area);count=a['room_count'];w=a['width'];h=a['height']
    options=[]
    for cols in range(1,count+1):
        rows=math.ceil(count/cols);rw=min(3,(w-2-(cols-1)*3)//cols);rh=min(3,(h-2-(rows-1)*3)//rows)
        if rw>=1 and rh>=1:options.append((abs(cols/rows-w/h),-rw*rh,cols,rows,rw,rh))
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
    if area['type'] in ('forest','desert','winter'):return {}
    rooms={r['id']:r for r in area['rooms']};slots=[]
    for c in connections:
        if c['kind']!='corridor' or c['from_room'] not in rooms or c['to_room'] not in rooms:continue
        for rid,side in ((c['from_room'],c['from_side']),(c['to_room'],c['to_side'])):
            r=rooms[rid];candidates=[];vertical=side in ('east','west');length=r['height'] if vertical else r['width']
            if r.get('native_group'):continue
            # A stock framed doorway replaces a full tile. Opposing/corner
            # frames cannot share a narrow room's tile; keep its passage open.
            if min(r['width'],r['height'])==1:continue
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
        if a.get('geometry',{}).get('mode')=='measured':
            from .measured_geometry import plan as measured_plan
            result[a['id']]=measured_plan(a,p['connections']);continue
        rooms={r['id']:r for r in a['rooms']};floor=set();paths=[];doorways=doorway_plan(a,p['connections']);openings=[]
        from .native_groups import rotated
        groups={r['id']:rotated(r['native_group']) for r in a['rooms'] if r.get('native_group')}
        for c in p['connections']:
            for rid,side in ((c['from_room'],c['from_side']),(c['to_room'],c['to_side'])):
                if rid in rooms and rooms[rid].get('native_group',{}).get('definition',{}).get('mode')=='enclosed':exit_point(rooms[rid],side,0)
        for c in p['connections']:
            if c['kind']!='corridor' or c['from_room'] not in rooms or c['to_room'] not in rooms:continue
            for rid,side in ((c['from_room'],c['from_side']),(c['to_room'],c['to_side'])):
                r=rooms[rid]
                if r.get('native_group',{}).get('definition',{}).get('mode')!='enclosed':continue
                matches=[p for p in groups[rid]['ports'] if p['side']==side]
                if len(matches)!=1:raise ValueError(r['name']+': choose a connection on the native group’s authored doorway side')
                p0=matches[0];x=r['x']*10+p0['x'];y=r['y']*10+p0['y'];vx,vy={'east':(1,0),'west':(-1,0),'north':(0,1),'south':(0,-1)}[side]
                inside=(int((x-vx*.1)//10),int((y-vy*.1)//10));outside=(inside[0]+vx,inside[1]+vy)
                doorways[rid,side]=dict(room=rid,side=side,inside=inside,outside=outside,x=x,y=y,native_group=True)
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
            for r,side in ((r1,c['from_side']),(r2,c['to_side'])):
                if (r['id'],side) in doorways:continue
                px,py=port(r,side);vx,vy={'east':(1,0),'west':(-1,0),'north':(0,1),'south':(0,-1)}[side]
                openings.append(dict(room=r['id'],side=side,x=(2*px-vx+1)*5,y=(2*py-vy+1)*5))
            paths.append(dict(id=c['id'],from_room=r1['id'],to_room=r2['id'],cells=path))
        vertices={(x+dx,y+dy) for x,y in floor for dx,dy in ((0,0),(1,0),(0,1),(1,1))}
        for r in a['rooms']:
            if r.get('native_group',{}).get('definition',{}).get('mode')=='enclosed':
                vertices-={(x,y) for x in range(r['x'],r['x']+r['width']+1) for y in range(r['y'],r['y']+r['height']+1)}
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
        stamps=[dict(t,x=t['x']+rooms[rid]['x'],y=t['y']+rooms[rid]['y']) for rid,g in groups.items() for t in g['tiles']]
        result[a['id']]={'groups':stamps,'doorways':list(doorways.values()),'openings':openings,'width':a['width'],'height':a['height'],'floor':sorted(floor),'vertices':sorted(vertices),'corridors':paths,'tileset':TILESETS[a['type']]}
    return result

def native_tiles(template,area,layout):
    if 'measured_tiles' in layout:return [tile(template,i,0) for i in layout['measured_tiles']]
    blank,full,corner,side,diagonal,inverse=TILES[area['type']]
    candidates=[((False,False,False,False),blank),((True,True,True,True),full),((False,False,True,False),corner),((True,False,True,False),side),((True,False,False,True),diagonal),((False,True,True,True),inverse)]
    vertices={tuple(v) for v in layout['vertices']};result=[]
    for y in range(area['height']):
        for x in range(area['width']):
            wanted=tuple(pos in vertices for pos in ((x,y+1),(x+1,y+1),(x,y),(x+1,y)));found=None
            if area['type'] in ('desert','winter'):
                result.append(tile(template,full,0));continue
            for pattern,ident in candidates:
                for rotation in range(4):
                    if pattern==wanted:found=tile(template,ident,rotation);break
                    pattern=rotate_corners(pattern)
                if found is not None:break
            if found is None:raise ValueError('No stock terrain tile matches the requested room edge')
            result.append(found)
    for g in layout.get('groups',[]):result[g['y']*area['width']+g['x']]=tile(template,g['id'],g['rotation'])
    for d in layout.get('doorways',[]):
        rotation={'east':0,'north':1,'west':2,'south':3}[d['side']]
        for cell,ori in ((d['inside'],rotation),(d['outside'],(rotation+2)%4)):
            if d.get('native_group') and cell==d['inside']:continue
            x,y=cell;index=y*area['width']+x;old=result[index]
            expected=29 if area['type']=='castle' else 1
            if old[1]['Tile_ID'][1]!=expected or old[1]['Tile_Orientation'][1]!=ori:
                raise ValueError(area['name']+': doorway overlaps another opening; move the rooms or select a different exit side')
            result[index]=tile(old,37 if area['type']=='castle' else 6,ori)
    return result
