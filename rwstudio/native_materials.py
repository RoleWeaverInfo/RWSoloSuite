"""Area-local native surface variations; no global stock texture overrides.

Recolour DXT endpoints, retaining original mipmaps, UV detail and alpha blocks.
Clone the native SET/palette and model resources, keeping all WOK geometry.
"""
import configparser
import copy
import hashlib
import re
import struct
from .area_presets import material,rgb

SURFACES={
 'castle':{'floor':['tic01_floor00','tic01_floor01','tic01_halflr','tic01_jailflr01','tic01_librflr02','tic01_librflrb2'],'wall':['tic01_stone20','tic01_richwall','tic01_librwall','tic01_jailwall']},
 'dungeon':{'floor':['tde01_floor1','tde01_floor2'],'wall':['tde01_wall6','tde01_wall8','tde01_wall9e','tde01_wall9h','tde01_wall9k','tde01_wall9f','tde01_wall9o','tde01_wall9l']},
 'cave':{'floor':['tdm01_floor01','tdm01_floor02','tdm01_dirt01'],'wall':['tdm01_rock01','tdm01_rock02','tdm01_rock03','tdm01_roof02']},
 'forest':{'floor':['ttf01_floor01','ttf01_grass01','ttf01_grassrim01','ttf01_grassrim02'],'wall':['ttf01_cliff01','ttf01_cliff02','ttf01_rock00','ttf01_rock02']},
 'desert':{'floor':['ttd01_floor01'],'wall':['ttd01_cliff01','ttd01_cliff02','ttd01_rock00','ttd01_rock04']},
 'winter':{'floor':['tts01_grass02','tts01_grassrim01'],'wall':['tts01_rock00','tts01_stone06b']},
}

def tint(color,target,strength=.72):
    # Retain most native shading and some original hue rather than painting flat RGB.
    luminance=sum(c*w for c,w in zip(color,(.2126,.7152,.0722)))
    target_luminance=sum(c*w for c,w in zip(target,(.2126,.7152,.0722)))
    return tuple(max(0,min(255,round(c*(1-strength)+luminance*t/max(1,target_luminance)*strength))) for c,t in zip(color,target))

def color565(value):return ((value>>11)*255//31,((value>>5)&63)*255//63,(value&31)*255//31)
def encode565(color):
    r,g,b=color;return (round(r*31/255)<<11)|(round(g*63/255)<<5)|round(b*31/255)

def tint_dds(raw,target):
    if raw[:4]==b'DDS ':
        if len(raw)<128:raise ValueError('Truncated DDS header')
        code=raw[84:88];offset=128
        if code not in (b'DXT1',b'DXT3',b'DXT5'):raise ValueError('Unsupported DDS compression; provide a DXT1/3/5 texture')
        stride=8 if code==b'DXT1' else 16;opaque=code!=b'DXT1'
    else:
        if len(raw)<20:raise ValueError('Truncated NWN DDS header')
        w,h,channels,size,alpha=struct.unpack_from('<4If',raw)
        if not 1<=w<=16384 or not 1<=h<=16384 or channels not in (3,4) or size>len(raw)-20:raise ValueError('Invalid NWN DDS header')
        stride=8 if channels==3 else 16;opaque=channels==4;offset=20
    if (len(raw)-offset)%stride:raise ValueError('Truncated DDS blocks')
    result=bytearray(raw);cache={}
    def convert(value):
        if value not in cache:cache[value]=encode565(tint(color565(value),target))
        return cache[value]
    for at in range(offset,len(raw),stride):
        pos=at+stride-8;c0,c1,bits=struct.unpack_from('<HHI',raw,pos);a,b=convert(c0),convert(c1);four=opaque or c0>c1
        if (four and a<b) or (not four and a>b):
            a,b=b,a;mapping=(1,0,3,2) if four else (1,0,2,3);bits=sum(mapping[(bits>>(2*i))&3]<<(2*i) for i in range(16))
        if four and a==b:
            if a<65535:a+=1
            else:b-=1
        struct.pack_into('<HHI',result,pos,a,b,bits)
    return bytes(result)

def tint_tga(raw,target):
    if len(raw)<18 or raw[1]!=0 or raw[2] not in (2,10) or raw[16] not in (24,32):raise ValueError('Unsupported surface TGA')
    w,h=struct.unpack_from('<HH',raw,12);step=raw[16]//8;offset=18+raw[0];count=w*h
    if not 1<=count<=16_777_216:raise ValueError('Invalid TGA dimensions')
    pixels=[]
    if raw[2]==2:
        if offset+count*step>len(raw):raise ValueError('Truncated TGA')
        pixels=[raw[i:i+step] for i in range(offset,offset+count*step,step)]
    else:
        while len(pixels)<count:
            if offset>=len(raw):raise ValueError('Truncated RLE TGA')
            run=raw[offset];offset+=1;n=(run&127)+1;size=step if run&128 else n*step
            if offset+size>len(raw) or len(pixels)+n>count:raise ValueError('Invalid RLE TGA run')
            pixels.extend([raw[offset:offset+step]]*n if run&128 else [raw[i:i+step] for i in range(offset,offset+size,step)]);offset+=size
    header=bytearray(raw[:18]);header[0]=0;header[2]=2;result=bytearray(header)
    for pixel in pixels:
        r,g,b=tint((pixel[2],pixel[1],pixel[0]),target);result.extend((b,g,r));result.extend(pixel[3:])
    return bytes(result)

def rewrite_model(raw,old,new,textures):
    """Only fixed-size name fields change in binary resources; offsets stay intact."""
    if raw[:4]!=b'\0'*4:
        text=raw.decode('latin1')
        mapping={**textures}
        def replace(match):
            value=match[0];low=value.lower()
            return new+value[len(old):] if low.startswith(old.lower()) else mapping.get(low,value)
        return re.sub(r'[A-Za-z][A-Za-z0-9_]*',replace,text).encode('latin1')
    result=bytearray(raw)
    def integer(at):
        if not 0<=at<=len(raw)-4:raise ValueError('Invalid native model offset')
        return struct.unpack_from('<I',raw,at)[0]
    def field(at,size,bitmap=False):
        if not 0<=at<=len(raw)-size:raise ValueError('Invalid native model string offset')
        name=raw[at:at+size].split(b'\0',1)[0].decode('latin1');low=name.lower()
        replacement=textures.get(low) if bitmap else new+name[len(old):] if low.startswith(old.lower()) else None
        if replacement is None:return
        if len(replacement)>=size:raise ValueError('Native model name is too long')
        # Stock fields can contain uninitialised bytes after NUL: use field
        # offsets, never a scan or assumptions about zero-filled padding.
        result[at:at+size]=replacement.encode().ljust(size,b'\0')
    seen=set()
    def walk(offset,depth=0):
        at=12+offset
        if offset in seen:return
        if depth>64 or len(seen)>8192:raise ValueError('Invalid native model tree')
        seen.add(offset);field(at+32,32);flags=integer(at+108)
        if flags&32:
            base=at+112+(92 if flags&2 else 0)+(216 if flags&4 else 0)+(68 if flags&16 else 0)
            for i in range(4):field(base+120+i*64,64,True)
        children,count=integer(at+72),integer(at+76)
        if count>8192:raise ValueError('Invalid native model child count')
        for i in range(count):walk(integer(12+children+i*4),depth+1)
    field(20,64);walk(integer(84))
    anims,count=integer(132),integer(136)
    if count>4096:raise ValueError('Invalid native model animation count')
    for i in range(count):
        at=12+integer(12+anims+i*4);field(at+120,64);walk(integer(at+72))
    return bytes(result)

def export(area,layout,game,namespace,archives=()):
    finish=material(area)
    if not finish or area.get('geometry'):return {},layout
    from .measured_geometry import serialize_set
    from .nwn.gff import read,write
    def get(name,kind):
        for archive in archives:
            if (name,kind) in archive:return archive[name,kind]
        return game.get(name,kind)
    setname='s'+hashlib.sha256((namespace+area['id']).encode()).hexdigest()[:8]
    cfg=configparser.ConfigParser(interpolation=None);cfg.optionxform=str;cfg.read_string(get(layout['tileset'],2013).decode('latin1'))
    # Retail desert bridge declares one door but supplies no hook. Keep the
    # bridge doorless in the copy rather than inventing a door position.
    if layout['tileset']=='ttd01' and cfg.get('TILE36','Model',fallback='').lower()=='ttd01_h07_01' and cfg.get('TILE36','Doors')=='1' and 'TILE36DOOR0' not in cfg:cfg['TILE36']['Doors']='0'
    resources={};replacements={}
    for role,names in SURFACES[area['type']].items():
        for old in names:
            new=setname+'s'+f'{len(replacements):02x}';found=False
            for kind,convert in ((2033,tint_dds),(3,tint_tga)):
                try:raw=get(old,kind)
                except KeyError:continue
                resources[new,kind]=convert(raw,rgb(finish[role]));found=True
            if not found:raise ValueError('The selected finish requires missing surface texture '+old)
            replacements[old]=new
            try:txi=get(old,2022)
            except KeyError:pass
            else:
                # Keep blending/bump metadata; an old materialname would reload the old albedo.
                resources[new,2022]=b'\r\n'.join(line for line in txi.splitlines() if not line.strip().lower().startswith(b'materialname'))+b'\r\n'
    models={}
    for i in range(int(cfg['TILES']['Count'])):
        section=cfg['TILE'+str(i)];old=section['Model'].lower()
        if old not in models:
            new=setname+'t'+f'{len(models):03x}';models[old]=new
            resources[new,2002]=rewrite_model(get(old,2002),old,new,replacements)
            # WOK name references do not affect geometry, material IDs or path nodes.
            resources[new,2016]=rewrite_model(get(old,2016),old,new,{})
        section['Model']=models[old]
    # Some retail SETs retain inactive door sections after Doors=0. They are
    # ignored by the original tile; do not turn them into new active doors.
    for section in list(cfg.sections()):
        match=re.fullmatch(r'TILE(\d+)(DOOR|SOUND)(\d+)',section)
        if match and int(match[3])>=int(cfg['TILE'+match[1]]['Doors' if match[2]=='DOOR' else 'Sounds']):cfg.remove_section(section)
    cfg['GENERAL']['Name']=setname;resources[setname,2013]=serialize_set(cfg)
    palette=read(get(layout['tileset']+'palstd',2030))[1]
    def remap(node):
        for key,(kind,value) in list(node[1].items()):
            if kind==15:
                for child in value:remap(child)
            elif kind==11 and value.decode().lower() in models:node[1][key]=(kind,models[value.decode().lower()].encode())
    remap(palette);resources[setname+'palstd',2030]=write(b'ITP V3.2',palette)
    return resources,dict(layout,tileset=setname,material_models=models,material_textures=replacements)
