"""Author-owned surface finishes and native area lighting, independent of story AI."""
import copy
import math
from .nwn.area_tools import set_value

MATERIALS={
 'castle_grey':dict(name='Grey stone and oak',types=['castle','dungeon'],floor='#8a8a83',wall='#81857f',wood='#80542f',pattern='stone'),
 'castle_limestone':dict(name='Pale limestone and dark oak',types=['castle','dungeon'],floor='#c0b799',wall='#b1a889',wood='#523524',pattern='stone'),
 'castle_slate':dict(name='Dark slate and walnut',types=['castle','dungeon'],floor='#626e77',wall='#747e87',wood='#533b31',pattern='stone'),
 'cave_earth':dict(name='Earth and weathered rock',types=['cave'],floor='#80705c',wall='#786955',wood='#71523c',pattern='rough'),
 'cave_basalt':dict(name='Cool basalt',types=['cave'],floor='#626b76',wall='#57616d',wood='#574b40',pattern='rough'),
 'forest_moss':dict(name='Mossy forest floor',types=['forest'],floor='#65734b',wall='#727966',wood='#6b4e33',pattern='rough'),
 'forest_dry':dict(name='Dry woodland floor',types=['forest'],floor='#9b895e',wall='#8a806a',wood='#77553c',pattern='rough'),
 'desert_gold':dict(name='Golden sand and sandstone',types=['desert'],floor='#c9a96e',wall='#b9996c',wood='#7c5c40',pattern='rough'),
 'desert_red':dict(name='Red sand and rust sandstone',types=['desert'],floor='#b98158',wall='#a36d4f',wood='#72523b',pattern='rough'),
 'winter_fresh':dict(name='Fresh snow and grey rock',types=['winter'],floor='#dce5e9',wall='#919da4',wood='#65564a',pattern='rough'),
 'winter_blue':dict(name='Blue frost and dark rock',types=['winter'],floor='#abbfd2',wall='#727e8e',wood='#514b47',pattern='rough'),
}

def light(name,types,ambient,diffuse,fog_color,fog=0,night=False,weather='clear',main=2,source=1):
    return dict(name=name,types=types,ambient=ambient,diffuse=diffuse,fog_color=fog_color,fog=fog,night=night,weather=weather,main=main,source=source)

LIGHTING={
 'castle_warm':light('Warm torchlit hall',['castle','dungeon'],'#92806a','#ead8b8','#82705f',4,main=6,source=3),
 'castle_cool':light('Cool stone hall',['castle','dungeon'],'#7f8b99','#c6d5e6','#738391',3,main=2,source=1),
 'cave_dim':light('Dim amber cavern',['cave','dungeon'],'#544d43','#a58c66','#403b35',18,main=1,source=3),
 'cave_blue':light('Blue cavern haze',['cave','dungeon'],'#465768','#8aa3c2','#40596d',25,main=1,source=9),
 'forest_day':light('Soft woodland daylight',['forest'],'#87917f','#d4dec3','#899b88',12,main=2,source=3),
 'forest_moon':light('Moonlit woodland',['forest'],'#455369','#8c9fbc','#40536a',28,True,main=1,source=3),
 'desert_sun':light('Clear desert sun',['desert'],'#b5a48a','#fff0d0','#d1ba8e',5,main=2),
 'desert_dusk':light('Desert dusk',['desert'],'#a08179','#efb482','#a58683',18,main=1,source=3),
 'winter_day':light('Clear winter daylight',['winter'],'#9baebb','#edf4ff','#c4d2df',10,main=2),
 'winter_flurry':light('Overcast snow flurries',['winter'],'#83939f','#bccbd5','#b6c8d5',35,weather='snow',main=1),
}
DEFAULTS={'castle':('castle_grey','castle_warm'),'dungeon':('castle_slate','cave_dim'),'cave':('cave_earth','cave_dim'),'forest':('forest_moss','forest_day'),'desert':('desert_gold','desert_sun'),'winter':('winter_fresh','winter_day')}
OUTDOOR={'forest','desert','winter'}

def catalog():return copy.deepcopy(dict(materials=MATERIALS,lighting=LIGHTING,defaults=DEFAULTS))

def default_look(kind):
    material,lighting=DEFAULTS[kind]
    return dict(material=material,lighting=lighting,brightness=1.,fog=LIGHTING[lighting]['fog'],weather='preset')

def validate(area):
    look=area.get('look')
    if 'look' not in area:return
    if not isinstance(look,dict) or set(look)!={'material','lighting','brightness','fog','weather'}:raise ValueError('Invalid material and lighting settings')
    for key,values,original in (('material',MATERIALS,'original'),('lighting',LIGHTING,'legacy')):
        value=look[key]
        if not isinstance(value,str) or value!=original and (value not in values or area['type'] not in values[value]['types']):raise ValueError('Choose a '+key+' preset for this area type')
    for key,lo,hi in (('brightness',.35,1.6),('fog',0,80)):
        if type(look[key]) not in (int,float) or not math.isfinite(look[key]) or not lo<=look[key]<=hi:raise ValueError('Invalid '+key+' setting')
    if look['weather'] not in ('preset','clear','rain','snow'):raise ValueError('Choose a supported weather option')
    if area['type'] not in OUTDOOR and look['weather'] in ('rain','snow'):raise ValueError('Rain and snow require an outdoor area')

def preserve(source,target):
    if source.get('outdoor_layout') and 'outdoor_layout' not in target and target['type'] in OUTDOOR:
        selected=set(source['outdoor_layout']['courtyard_rooms'])&{r['id'] for r in target['rooms']}
        if selected and not any(r.get('native_group') for r in target['rooms']):target['outdoor_layout']=dict(copy.deepcopy(source['outdoor_layout']),courtyard_rooms=sorted(selected))
    if source.get('geometry',{}).get('solid_exterior') and target.get('geometry'):target['geometry']['solid_exterior']=True
    if 'look' in target or 'look' not in source:return
    proposed=copy.deepcopy(source['look']);candidate=dict(target,look=proposed)
    try:validate(candidate)
    except ValueError:return
    target['look']=proposed

def material(area):return MATERIALS.get(area.get('look',{}).get('material'))

def rgb(color):return tuple(int(color[i:i+2],16) for i in (1,3,5))

def packed(color,brightness=1):
    r,g,b=(max(0,min(255,round(v*brightness))) for v in rgb(color))
    return r|(g<<8)|(b<<16)

def apply_lighting(area,native):
    look=area.get('look',{});spec=LIGHTING.get(look.get('lighting'))
    if not spec:return
    outdoor=area['type'] in OUTDOOR
    for prefix in ('Sun','Moon'):
        set_value(native,prefix+'AmbientColor',packed(spec['ambient'],look['brightness']),4)
        set_value(native,prefix+'DiffuseColor',packed(spec['diffuse'],look['brightness']),4)
        set_value(native,prefix+'FogColor',packed(spec['fog_color']),4)
        set_value(native,prefix+'FogAmount',round(look['fog']),0)
        set_value(native,prefix+'Shadows',int(outdoor),0)
    weather=spec['weather'] if look['weather']=='preset' else look['weather']
    values=dict(DayNightCycle=(0,0),IsNight=(0,int(spec['night'])),LightingScheme=(0,13),
                SkyBox=(0,({'forest':1,'desert':3,'winter':4}[area['type']] if outdoor else 0)),
                ChanceRain=(5,65 if outdoor and weather=='rain' else 0),ChanceSnow=(5,65 if outdoor and weather=='snow' else 0),
                WindPower=(5,1 if outdoor else 0),FogClipDist=(8,80. if outdoor else 60.))
    if outdoor and weather=='rain':values['SkyBox']=(0,2)
    for key,(kind,value) in values.items():set_value(native,key,value,kind)
    for _,tile in native[1]['Tile_List'][1]:
        for key in ('Tile_MainLight1','Tile_MainLight2'):tile[key]=(0,spec['main'])
        for key in ('Tile_SrcLight1','Tile_SrcLight2'):tile[key]=(0,spec['source'])

def stone_texture(finish,wall=False):
    """Original tileable stone/rough-rock texture; repeat stays in world metres."""
    base=rgb(finish['wall' if wall else 'floor']);size=128;pixels=bytearray()
    for y in range(size):
        for x in range(size):
            noise=((x*73856093 ^ y*19349663 ^ (x*y)*83492791)&255)/255-.5
            if finish['pattern']=='stone':
                xx=(x+(16 if wall and (y//32)%2 else 0))%size
                joint=xx%32<2 or y%32<2;variation=((xx//32*17+y//32*11)%19)-9
                scale=.50 if joint else 1+variation/145+noise*.10
            else:
                scale=.92+noise*.22+.08*math.sin(x*math.tau/32)*math.sin(y*math.tau/64)
            r,g,b=(max(0,min(255,round(c*scale))) for c in base);pixels.extend((b,g,r,255))
    return bytes([0,0,2,0,0,0,0,0,0,0,0,0,size,0,size,0,32,40])+pixels
