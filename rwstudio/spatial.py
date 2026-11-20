"""Metre-based room extents and backward-compatible placement records."""
import math
from .content import _obj,array,S,schema_check

NUMBER={'type':'number'}
POSITION=_obj({'id':S,'x':NUMBER,'y':NUMBER,'facing':NUMBER})
POSITION_3D=_obj({**POSITION['properties'],'z':NUMBER,'support':S})

def dimensions(room):
    interior=room.get('interior',{})
    return interior.get('width_m',room['width']*10),interior.get('depth_m',room['height']*10)

def validate_positions_shape(positions):
    if not isinstance(positions,list):raise ValueError('Object positions must be a list')
    for p in positions:
        schema_check(p,POSITION_3D if 'z' in p or 'support' in p else POSITION,'Object position')
        if any(not math.isfinite(p[k]) for k in ('x','y','facing')) or not -1<=p.get('z',0)<=30:raise ValueError('Position or height is outside the supported range')

def validate_area(area):
    from .outdoor_geometry import validate as validate_outdoor
    validate_outdoor(area)
    from .area_presets import validate as validate_look
    validate_look(area)
    spec=area.get('geometry')
    if spec is not None:
        required={'mode','wall_height','wall_thickness','corridor_width'}
        if not isinstance(spec,dict) or not required<=set(spec) or set(spec)-required-{'solid_exterior'} or spec['mode']!='measured':raise ValueError('Invalid measured geometry settings')
        if 'solid_exterior' in spec and type(spec['solid_exterior']) is not bool:raise ValueError('Choose whether to fill the exterior mass')
        if area['type'] not in ('castle','dungeon','cave'):raise ValueError('Measured walls are for interiors; outdoor areas use native terrain')
        for key,lo,hi in [('wall_height',2,10),('wall_thickness',.1,1),('corridor_width',1.5,6)]:
            if type(spec[key]) not in (int,float) or not math.isfinite(spec[key]) or not lo<=spec[key]<=hi:raise ValueError('Invalid '+key)
    for r in area['rooms']:
        ports=r.get('openings',[])
        if not isinstance(ports,list) or len(ports)>4:raise ValueError('Use at most one opening on each room wall')
        sides=set()
        for port in ports:
            if not spec or not isinstance(port,dict) or set(port)!={'side','offset','width'}:raise ValueError('Measured openings need a side, offset and width')
            side=port['side']
            if side not in ('north','south','east','west') or side in sides:raise ValueError('Use at most one opening on each room wall')
            sides.add(side)
            if any(type(port[k]) not in (float,int) or not math.isfinite(port[k]) for k in ('offset','width')):raise ValueError('Opening measurements must be finite')
            length=dimensions(r)[0 if side in ('north','south') else 1]
            if not 1<=port['width']<=6 or not port['width']/2+.1<=port['offset']<=length-port['width']/2-.1:raise ValueError('Opening must fit its wall and keep clear of the corners')
        from .platforms import validate as validate_platforms
        validate_platforms(r,spec)
        from .carpets import validate as validate_carpets
        validate_carpets(r,spec)
        if 'interior' not in r:continue
        d=r['interior']
        if not spec or r.get('native_group'):raise ValueError('Measured room dimensions require measured walls and cannot stretch a native group')
        if set(d)!={'width_m','depth_m'} or any(type(v) not in (int,float) or not math.isfinite(v) or v<2 for v in d.values()):raise ValueError('Interior dimensions must be finite and at least 2 m')
        if d['width_m']>r['width']*10 or d['depth_m']>r['height']*10:raise ValueError('Increase the room tile envelope to fit its measured interior')
    if spec and any(r.get('native_group') for r in area['rooms']):raise ValueError('Use either native groups or measured walls in this area')

def enable(area,measurements=()):
    if any(r.get('native_group') for r in area['rooms']):raise ValueError('Remove native groups before switching to measured walls')
    area['geometry']=dict(mode='measured',wall_height=5.,wall_thickness=.3,corridor_width=2.)
    measured={m['room']:m for m in measurements}
    for r in area['rooms']:
        m=measured.get(r['id'],{});w=m.get('width_m',dimensions(r)[0]);h=m.get('height_m',dimensions(r)[1])
        r['interior']=dict(width_m=w,depth_m=h);r['width']=math.ceil(w/10);r['height']=math.ceil(h/10)
    validate_area(area)

def stripped(area):
    import copy
    a=copy.deepcopy(area);a.pop('geometry',None);a.pop('look',None);a.pop('outdoor_layout',None)
    for r in a['rooms']:r.pop('interior',None);r.pop('native_group',None);r.pop('openings',None);r.pop('platforms',None);r.pop('carpets',None)
    return a

def resolve_heights(project):
    """Resolve support chains, preserving authored offsets and rejecting cycles."""
    from .footprints import box,distance
    objects={f['id']:f for key in ('furnishings','custom_placements') for f in project.get(key,[])}
    positions={p['id']:p for p in project.get('object_positions',[])};done={};visiting=set()
    rooms={r['id']:r for a in project['areas'] for r in a['rooms']}
    from .platforms import ground
    def bounds(ident):return project.get('asset_geometry',{}).get(objects[ident].get('asset_id'))
    def resolve(ident):
        if ident in done:return done[ident]
        if ident in visiting:raise ValueError('Cyclic item support relationship')
        visiting.add(ident);p=positions[ident];support=p.get('support','');z=p.get('z',0)
        if support:
            if support not in positions or objects[support]['room']!=objects[ident]['room']:raise ValueError(ident+': choose a positioned support object in the same room')
            parent=resolve(support);pb=bounds(support);child=bounds(ident)
            if pb is None or child is None:raise ValueError(ident+': support placement requires measured model bounds for both objects')
            polygon=box(pb,parent['x'],parent['y'],parent['facing']);footprint=box(child,p['x'],p['y'],p['facing'])
            if not all(distance(polygon,x,y)<.001 for x,y in footprint):raise ValueError(ident+': item extends beyond its supporting surface')
            z=parent['z']+pb[1][2]-child[0][2]+z
        else:z+=ground(rooms[objects[ident]['room']],p['x'],p['y'])
        if not -1<=z<=30:raise ValueError(ident+': resolved elevation is outside the supported range')
        done[ident]=dict(p,z=z,support=support);visiting.remove(ident);return done[ident]
    for ident in positions:resolve(ident)
    return done
