import copy
import re
from .content import _obj,array,S,enum,schema_check
from .reference_images import validate_references

PLACEMENT=_obj({**{k:S for k in ('id','name','room','asset_id','description')},'placement':enum('north','east','south','west','center')})
REFERENCE=_obj({'name':{'type':'string','maxLength':120},'notes':{'type':'string','maxLength':3000},'data_url':{'type':'string','maxLength':3_000_000}})
ASSET=_obj({**{k:S for k in ('id','name','pack','sha256','resref','model')},'appearance':{'type':'integer'}})

def base_project(p):
    q=copy.deepcopy(p);q.pop('custom_assets',None);q.pop('custom_placements',None);q.pop('custom_packs',None);q.pop('locked_rooms',None);q.pop('design_mode',None)
    q.pop('object_positions',None);q.pop('asset_geometry',None)
    for c in q.get('connections',[]):c.pop('doorway',None)
    for a in q.get('areas',[]):
        a.pop('references',None);a.pop('design_plan',None);a.pop('geometry',None);a.pop('look',None);a.pop('outdoor_layout',None)
        for r in a['rooms']:r.pop('native_group',None);r.pop('interior',None);r.pop('openings',None);r.pop('platforms',None);r.pop('carpets',None)
    return q

def validate_extensions(p):
    from .doorways import validate as validate_doorways
    validate_doorways(p)
    from .floorplan_design import POSITION,validate_plan
    from .spatial import validate_positions_shape,validate_area
    positions=p.get('object_positions',[]);validate_positions_shape(positions)
    objects={f['id']:f for k in ('furnishings','custom_placements') for f in p.get(k,[])}
    seen=set()
    for pos in positions:
        if pos['id'] not in objects or pos['id'] in seen or not 0<=pos['facing']<360:raise ValueError('Object positions need unique existing furnishing IDs and facing from 0 to less than 360')
        seen.add(pos['id'])
    for a in p['areas']:
        validate_area(a)
        if 'design_plan' in a:validate_plan(a['design_plan'])
        for r in a['rooms']:
            if r.get('native_group'):
                from .native_groups import validate_record
                validate_record(r['native_group'],a,r)
    if p.get('design_mode','adventure') not in ('area','adventure'):raise ValueError('Unknown design mode')
    locked=p.get('locked_rooms',[])
    rooms={r['id'] for a in p['areas'] for r in a['rooms']}
    if not isinstance(locked,list) or any(not isinstance(r,str) or r not in rooms for r in locked) or len(locked)!=len(set(locked)):raise ValueError('Room locks must reference unique existing rooms')
    for i,a in enumerate(p['areas']):
        for j,ref in enumerate(a.get('references',[])):schema_check(ref,REFERENCE,f'Area {i+1} floor plan {j+1}')
    validate_references(p)
    assets=p.get('custom_assets',[]);placed=p.get('custom_placements',[])
    geometries=p.get('asset_geometry',{})
    if not isinstance(geometries,dict) or len(geometries)>300:raise ValueError('Invalid asset geometry catalog')
    import math
    for ident,bounds in geometries.items():
        if ident not in {a['id'] for a in assets} or not isinstance(bounds,list) or len(bounds)!=2 or any(not isinstance(row,list) or len(row)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>10000 for v in row) for row in bounds) or any(bounds[0][i]>bounds[1][i] for i in range(3)):raise ValueError('Invalid asset model bounds')
    if len(assets)>300 or len(placed)>100:raise ValueError('Use at most 300 custom assets and 100 custom placements per project.')
    packs=p.get('custom_packs',[])
    if len(packs)>40:raise ValueError('Use at most 40 custom packs.')
    for pack in packs:
        if set(pack)!={'pack','sha256'} or not re.fullmatch(r'rw[a-f0-9]{14}',pack['pack']) or not re.fullmatch('[a-f0-9]{64}',pack['sha256']):raise ValueError('Invalid custom dependency')
    ids=set();rooms={r['id'] for a in p['areas'] for r in a['rooms']}
    for a in assets:
        schema_check(a,ASSET)
        if not re.fullmatch(r'[a-z0-9_]{1,64}',a['id']) or a['id'] in ids:raise ValueError('Invalid or duplicate custom asset ID')
        ids.add(a['id'])
        if not re.fullmatch(r'[a-z0-9_]{1,16}',a['pack']) or not re.fullmatch('[a-f0-9]{64}',a['sha256']) or not 0<=a['appearance']<=65535:raise ValueError('Invalid custom pack identity')
    existing={o['id'] for key in ('npcs','items','furnishings','encounters','areas','connections','quests') for o in p[key]}|rooms
    for obj in placed:
        schema_check(obj,PLACEMENT)
        if not re.fullmatch('[a-z][a-z0-9_]{0,15}',obj['id']) or obj['id'].startswith(('aw_','aq_','spx_')) or obj['id'] in existing:raise ValueError('Custom placement needs a unique native object ID')
        existing.add(obj['id'])
        if obj['asset_id'] not in ids or obj['room'] not in rooms:raise ValueError('Custom placement references an unavailable asset or room')

def generation_schema(schema):
    result=copy.deepcopy(schema);result['properties']['custom_placements']=array(PLACEMENT);result['required'].append('custom_placements');return result
