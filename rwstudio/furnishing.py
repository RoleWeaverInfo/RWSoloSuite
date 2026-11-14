"""Conservative stock-prop footprints and reviewable interior-design guidance."""
from collections import Counter

# Clearance radii in metres, including a small walking/use margin. Never scale
# stock models merely to fill a room. Chairs may sit closer to their table.
RADII = {'table': 1.8, 'chair': .7, 'barrel': .9, 'bookshelf': 1.5,
         'crate': 1., 'chest': 1.1, 'sign': .8, 'candle': .4, 'bed': 1.8}
DESIGN_GUIDE = {
    'scale': 'One tile is 10 metres. Prefer 2x2 rooms; 3x3 for halls/combat. Larger rooms need an explicit purpose. Preserve author dimensions.',
    'composition': 'Give each room one purpose and one focal point. Use 3-7 purposeful props, not a repeated prop in every corner. Empty space is intentional.',
    'groups': {
        'dining': 'one table, one or two chairs; place the chairs on the same side as the table to group them',
        'bedroom': 'one bed against a wall, one chest; optional candle',
        'archive': 'one or two bookshelves against a wall, a table and chair for reading',
        'store': 'one table as counter, one shelf and a small crate/barrel cluster',
        'ruin': 'one story focal point, sparse storage only when justified; no domestic furniture by default',
        'wilderness': 'leave wild rooms largely unfurnished; crates/beds/tables only in a described occupied camp',
    },
    'placement': 'Use wall sides for beds, shelves and storage. Reserve center for a focal group. Keep exits and central walking lanes clear. Describe why each prop belongs here.',
    'limits': 'Stock objects only, fixed scale, floor-level candles; no tabletop stacking or arbitrary 3D meshes. Do not describe unsupported visual detail as already built.',
}


def warnings(project):
    result=[]
    for area in project['areas']:
        for room in area['rooms']:
            props=[p for p in project['furnishings'] if p['room']==room['id']]
            counts=Counter(p['kind'] for p in props)
            if room['width']*room['height']>9:
                result.append(f"{room['name']}: {room['width']*10} x {room['height']*10} metres is a large room; consider a smaller footprint or distinct activity zones.")
            for kind,count in counts.items():
                if count>3:result.append(f"{room['name']}: {count} repeated {kind} props; review whether each serves the room's purpose.")
            if counts['chair'] and not counts['table']:
                result.append(room['name']+': chairs have no table; check that their placement has a purpose.')
            if len(props)>8:result.append(room['name']+': many furnishings; review clutter and keep travel lanes open.')
    return result
