"""Measured textile floor coverings, exported without changing the walkmesh."""
import math
import re
from .content import _obj,array,S,enum,schema_check
from .platforms import platform_rect,stair_rect,intersects,inside,ground

COLORS={'red':(142,22,30),'blue':(30,56,113),'green':(35,86,54),'purple':(83,35,99),'brown':(94,60,37),'cream':(195,178,137),'gold':(180,139,55)}
CARPET=_obj({'id':S,'name':S,**{k:{'type':'number'} for k in ('x','y','width','depth')},'color':enum(*COLORS),'border':enum('none','gold','cream'),'requirements':array(S)})
LIFT=.012

def rect(c):return c['x'],c['y'],c['x']+c['width'],c['y']+c['depth']

def validate(room,geometry):
    from .spatial import dimensions
    carpets=room.get('carpets',[])
    if not isinstance(carpets,list) or len(carpets)>12:raise ValueError('Use at most 12 measured carpets per room')
    if carpets and not geometry:raise ValueError('Measured carpets require measured interior geometry')
    w,h=dimensions(room);seen=set();placed=[]
    for c in carpets:
        schema_check(c,CARPET,'Carpet')
        if not re.fullmatch('[a-z][a-z0-9_]{0,15}',c['id']) or c['id'] in seen:raise ValueError('Carpets need unique short IDs within their room')
        seen.add(c['id'])
        if any(type(c[k]) not in (int,float) or not math.isfinite(c[k]) for k in ('x','y','width','depth')):raise ValueError('Carpet measurements must be finite')
        if min(c['width'],c['depth'])<.3:raise ValueError('Carpet width and depth must be at least 0.30 m')
        a,b,d,e=rect(c)
        if a<0 or b<0 or d>w+1e-6 or e>h+1e-6:raise ValueError('Carpet must fit inside the clear room dimensions')
        if len(set(c['requirements']))!=len(c['requirements']):raise ValueError('Duplicate carpet checklist requirements')
        if any(intersects(rect(c),other) for other in placed):raise ValueError('Measured carpets must not overlap')
        placed.append(rect(c))
        for p in room.get('platforms',[]):
            if intersects(rect(c),stair_rect(p)):raise ValueError('Carpet must stop at the stairs; draped stair runners are not supported yet')
            pr=platform_rect(p)
            if intersects(rect(c),pr) and not all(inside(pr,x,y) for x,y in ((a,b),(d,b),(d,e),(a,e))):raise ValueError('Carpet must stay on one flat floor or platform surface')

def texture(color):
    """Original seamless woven texture; metre-based UVs avoid stretching."""
    rgb=COLORS[color];size=64;raw=bytearray()
    for y in range(size):
        for x in range(size):
            grain=((x*13+y*7)%7)-3
            weave=(3 if x%4<2 else -3)+(2 if y%4<2 else -2)
            r,g,b=[max(0,min(255,c+grain+weave)) for c in rgb]
            raw.extend((b,g,r,255))
    return bytes([0,0,2,0,0,0,0,0,0,0,0,0,size,0,size,0,32,40])+raw

def tile_meshes(area):
    from .measured_geometry import mesh,quad
    result={}
    for room in area['rooms']:
        for c in room.get('carpets',[]):
            x,y,x2,y2=rect(c);z=ground(room,(x+x2)/2,(y+y2)/2)+LIFT
            edge=min(.08,min(c['width'],c['depth'])/10) if c['border']!='none' else 0
            # Border is physical geometry around the perimeter, never repeated
            # down the middle by wrapping a complete rug image along its length.
            patches=[(x+edge,y+edge,x2-edge,y2-edge,c['color'])]
            if edge:patches.extend([(x,y,x2,y+edge,c['border']),(x,y2-edge,x2,y2,c['border']),(x,y+edge,x+edge,y2-edge,c['border']),(x2-edge,y+edge,x2,y2-edge,c['border'])])
            for left,bottom,right,top,color in patches:
                left+=room['x']*10;right+=room['x']*10;bottom+=room['y']*10;top+=room['y']*10
                for tx in range(math.floor(left/10),math.ceil((right-1e-7)/10)):
                    for ty in range(math.floor(bottom/10),math.ceil((top-1e-7)/10)):
                        l,b=max(left,tx*10),max(bottom,ty*10);r,t=min(right,tx*10+10),min(top,ty*10+10)
                        if r-l<1e-7 or t-b<1e-7:continue
                        m=result.setdefault((tx,ty),{}).setdefault(color,mesh());xy=[(l,b),(r,b),(r,t),(l,t)]
                        quad(m,[(px-tx*10-5,py-ty*10-5,z) for px,py in xy],0,[(px*4,py*4,0) for px,py in xy])
    return result
