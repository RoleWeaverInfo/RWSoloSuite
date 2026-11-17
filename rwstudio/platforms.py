"""Rectangular, room-local platforms with cardinal stairs, measured in metres.

Rendered treads are discrete. The walking surface is a continuous ramp, as in
NWN's native stair tiles. No second ground surface is retained under a platform.
"""
import math
import re
from .content import _obj, array, S, I, enum, schema_check

NUMBER={'type':'number'}
PLATFORM=_obj({'id':S,'name':S,**{k:NUMBER for k in ('x','y','width','depth','height','stair_width','stair_run','stair_offset')},'steps':I,'stair_side':enum('north','east','south','west'),'requirements':array(S)})

def platform_rect(p):return (p['x'],p['y'],p['x']+p['width'],p['y']+p['depth'])

def stair_rect(p):
    x,y,x2,y2=platform_rect(p);o=p['stair_offset'];w=p['stair_width']/2;run=p['stair_run']
    return {'south':(x+o-w,y-run,x+o+w,y),'north':(x+o-w,y2,x+o+w,y2+run),'west':(x-run,y+o-w,x,y+o+w),'east':(x2,y+o-w,x2+run,y+o+w)}[p['stair_side']]

def inside(rect,x,y):return rect[0]-1e-7<=x<=rect[2]+1e-7 and rect[1]-1e-7<=y<=rect[3]+1e-7

def intersects(a,b,pad=0):return a[0]<b[2]+pad-1e-7 and b[0]<a[2]+pad-1e-7 and a[1]<b[3]+pad-1e-7 and b[1]<a[3]+pad-1e-7

def progress(p,x,y):
    a,b,c,d=stair_rect(p)
    v={'south':y-b,'north':d-y,'west':x-a,'east':c-x}[p['stair_side']]
    return max(0.,min(1.,v/p['stair_run']))

def landing_rect(p):
    a,b,c,d=stair_rect(p)
    return {'south':(a,b-1,c,b),'north':(a,d,c,d+1),'west':(a-1,b,a,d),'east':(c,b,c+1,d)}[p['stair_side']]

def surface(room,x,y):
    for p in room.get('platforms',[]):
        if inside(platform_rect(p),x,y):return p,'platform'
        if inside(stair_rect(p),x,y):return p,'stairs'
    return None,'floor'

def elevation(region,x,y,visual=False):
    p,kind=region
    if kind=='floor':return 0.
    if kind=='platform':return float(p['height'])
    t=progress(p,x,y)
    return p['height']*(math.ceil(t*p['steps']-1e-7)/p['steps'] if visual else t)

def ground(room,x,y):return elevation(surface(room,x,y),x,y)

def flat(room,x,y,radius=.5):
    points=[(x,y),*( (x+dx,y+dy) for dx,dy in ((radius,0),(-radius,0),(0,radius),(0,-radius)))]
    return all(surface(room,px,py)[1]!='stairs' and abs(ground(room,px,py)-ground(room,x,y))<1e-6 for px,py in points)

def entry(room):
    """Keep arrival points off stair runs and platform edges."""
    from .spatial import dimensions
    w,h=dimensions(room);cx,cy=w/2,h/2
    if flat(room,cx,cy,1):return cx,cy
    points=((x/2,y/2) for x in range(2,int(w*2)-1) for y in range(2,int(h*2)-1))
    for x,y in sorted(points,key=lambda p:math.hypot(p[0]-cx,p[1]-cy)):
        if flat(room,x,y,1):return x,y
    raise ValueError(room['name']+': no flat arrival space remains around the platforms')

def validate(room,geometry):
    from .spatial import dimensions
    platforms=room.get('platforms',[])
    if not isinstance(platforms,list) or len(platforms)>12:raise ValueError('Use at most 12 platforms per room')
    if platforms and not geometry:raise ValueError('Raised platforms require measured interior geometry')
    w,h=dimensions(room);seen=set();occupied=[]
    for p in platforms:
        schema_check(p,PLATFORM,'Raised platform')
        if not re.fullmatch('[a-z][a-z0-9_]{0,15}',p['id']) or p['id'] in seen:raise ValueError('Platforms need unique short IDs within their room')
        seen.add(p['id'])
        if len(p['requirements'])!=len(set(p['requirements'])):raise ValueError('Duplicate platform checklist requirements')
        if any(type(p[k]) not in (int,float) or not math.isfinite(p[k]) for k in ('x','y','width','depth','height','stair_width','stair_run','stair_offset')):raise ValueError('Platform measurements must be finite')
        if min(p['width'],p['depth'])<1 or not .05<=p['height']<=min(3,geometry['wall_height']-2):raise ValueError('Platforms need a footprint of at least 1 m and 2 m headroom')
        if type(p['steps']) is not int or not 1<=p['steps']<=24 or p['stair_run']<=0:raise ValueError('Stairs need 1–24 steps and a positive run')
        if p['height']/p['steps']>.30+1e-7 or p['stair_run']/p['steps']<.15-1e-7 or p['height']/p['stair_run']>1:raise ValueError('Stairs need rises up to 0.30 m, treads at least 0.15 m and a slope no steeper than 45 degrees')
        length=p['width'] if p['stair_side'] in ('north','south') else p['depth']
        if not 1<=p['stair_width']<=length or not p['stair_width']/2<=p['stair_offset']<=length-p['stair_width']/2:raise ValueError('The stair width and offset must fit the platform edge')
        rects=[platform_rect(p),stair_rect(p)]
        if any(a<-.000001 or b<-.000001 or c>w+.000001 or d>h+.000001 for a,b,c,d in rects):raise ValueError('The platform and stairs must fit inside the clear room dimensions')
        # Leave a flat landing in front of the bottom tread.
        landing=landing_rect(p)
        if not (landing[0]>=0 and landing[1]>=0 and landing[2]<=w and landing[3]<=h):raise ValueError('Leave a 1 m flat landing below the stairs')
        for other in occupied:
            if any(intersects(r,s,.1) for r in rects+[landing] for s in other):raise ValueError('Platforms and stair runs must not overlap')
        occupied.append(rects+[landing])
        for o in room.get('openings',[]):
            offset,half=o['offset'],o['width']/2
            door={'south':(offset-half,0,offset+half,1),'north':(offset-half,h-1,offset+half,h),'west':(0,offset-half,1,offset+half),'east':(w-1,offset-half,w,offset+half)}[o['side']]
            if any(intersects(r,door) for r in rects):raise ValueError('Keep raised platforms and stairs clear of doorway approaches')
    if platforms:entry(room)

def check_footprint(room,polygon,z0,z1,ident):
    """Reject furniture buried in a dais, hanging over its edge, or blocking steps."""
    from .footprints import overlap
    def poly(r):return [(r[0],r[1]),(r[2],r[1]),(r[2],r[3]),(r[0],r[3])]
    for p in room.get('platforms',[]):
        r=platform_rect(p)
        if overlap(polygon,poly(r),0) and z0<p['height']-.05:raise ValueError(ident+': object intersects the raised platform')
        on_top=abs(z0-p['height'])<.06
        if on_top and overlap(polygon,poly(r),0) and not all(inside(r,x,y) for x,y in polygon):raise ValueError(ident+': object straddles a platform edge')
        if overlap(polygon,poly(stair_rect(p)),0 if z1<.05 else .1) and z0<p['height']+2.2 and z1>0:raise ValueError(ident+': keep the stairs clear of furniture')
        if overlap(polygon,poly(landing_rect(p)),.1) and z0<2.2 and z1>.05:raise ValueError(ident+': keep the stair landing clear of furniture')
