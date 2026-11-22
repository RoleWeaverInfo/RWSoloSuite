"""Bounded, read-only readers for untrusted community module resources.

Format reference: BioWare Aurora ERF/GFF/TLK specifications. These readers do
not unpack resources to executable files or rewrite the input archive.
"""
from pathlib import Path
import math
import struct

TYPES={2012:'are',2023:'git',2014:'ifo',2027:'utc',2029:'dlg',2056:'jrl',2040:'ute',2025:'uti',2044:'utp',2032:'utt',2051:'utm',2042:'utd',2009:'nss',2010:'ncs',2064:'ndb'}

def decode(raw,language=0):
    codecs={5:'cp1250',128:'cp949',129:'big5',130:'gbk',131:'shift_jis'}
    return raw.decode(codecs.get(language,'cp1252'),errors='replace').replace('\x00','')

class Archive:
    def __init__(self,path,allow_duplicates=False):
        self.path=Path(path);self.index={};self.duplicates=[];length=self.path.stat().st_size
        with self.path.open('rb') as f:
            h=f.read(160)
            if len(h)!=160 or h[:8] not in (b'MOD V1.0',b'HAK V1.0',b'ERF V1.0'):raise ValueError('Select a standard NWN .mod archive (ERF V1.0).')
            self.signature=h[:8].decode('ascii')
            count,ko,ro=struct.unpack_from('<I4xII',h,16)
            if count>300000 or ko<160 or ro<160 or ko+24*count>length or ro+8*count>length:raise ValueError('Invalid module resource index.')
            f.seek(ko);keys=f.read(count*24);f.seek(ro);entries=f.read(count*8)
            for i in range(count):
                name,rid,kind,_=struct.unpack_from('<16sIHH',keys,i*24)
                name=name.split(b'\0')[0].decode('ascii',errors='strict').lower()
                if not name or any(ord(c)<32 or ord(c)>126 for c in name) or rid>=count:raise ValueError('Invalid module resource name or index.')
                offset,size=struct.unpack_from('<II',entries,rid*8)
                if offset+size>length:raise ValueError('Invalid module resource bounds.')
                if (name,kind) in self.index:
                    if not allow_duplicates:raise ValueError('Duplicate module resource.')
                    self.duplicates.append((name,kind));continue
                self.index[name,kind]=(offset,size)
    def get(self,name,kind,limit=32_000_000):
        offset,size=self.index[name.lower(),kind]
        if size>limit:raise ValueError('Resource exceeds the 32 MB analysis budget; it was not inspected.')
        with self.path.open('rb') as f:f.seek(offset);raw=f.read(size)
        if len(raw)!=size:raise ValueError('Resource changed during analysis.')
        return raw

class TalkTable:
    def __init__(self,path):
        self.path=Path(path);self.length=self.path.stat().st_size
        with self.path.open('rb') as f:h=f.read(20)
        if len(h)!=20 or h[:8]!=b'TLK V3.0':raise ValueError('Unsupported talk table.')
        self.language,self.count,self.offset=struct.unpack_from('<III',h,8)
        if 20+self.count*40>self.length or self.offset>self.length:raise ValueError('Invalid talk table index.')
    def get(self,index):
        if not 0<=index<self.count:raise KeyError(index)
        with self.path.open('rb') as f:
            f.seek(20+40*index);entry=f.read(40)
            flags=struct.unpack_from('<I',entry)[0];offset,size=struct.unpack_from('<II',entry,28)
            if not flags&1:return ''
            if self.offset+offset+size>self.length or size>1_000_000:raise ValueError('Invalid talk table text.')
            f.seek(self.offset+offset);return decode(f.read(size),self.language)

def gff(raw):
    """Read selected standard GFF types with bounds, cycle and depth checks."""
    if len(raw)<56 or raw[4:8] not in (b'V3.2',b'V3.3'):raise ValueError('Unsupported or truncated GFF resource.')
    so,sc,fo,fc,lo,lc,do,dc,io,ic,lso,lsc=struct.unpack_from('<12I',raw,8)
    if sc>200000 or fc>500000 or lc>500000:raise ValueError('GFF exceeds the analysis structure budget.')
    for offset,size in ((so,12*sc),(fo,12*fc),(lo,16*lc),(do,dc),(io,ic),(lso,lsc)):
        if (size and offset<56) or offset+size>len(raw):raise ValueError('Invalid GFF table bounds.')
    def chunk(offset,size,start,end):
        if size<0 or offset<start or offset+size>end:raise ValueError('Invalid GFF field bounds.')
        return raw[offset:offset+size]
    def unpack(fmt,offset,start,end):return struct.unpack(fmt,chunk(offset,struct.calcsize(fmt),start,end))
    visits=0
    def node(index,trail=()):
        nonlocal visits
        visits+=1
        if index>=sc or index in trail or len(trail)>64 or visits>200000:raise ValueError('Cyclic or excessively nested GFF structure.')
        _,off,count=struct.unpack_from('<III',raw,so+12*index)
        if count>fc:raise ValueError('Invalid GFF field count.')
        ids=[] if not count else [off] if count==1 else unpack('<'+'I'*count,io+off,io,io+ic)
        result={}
        for fi in ids:
            if fi>=fc:raise ValueError('Invalid GFF field index.')
            kind,li,value=struct.unpack_from('<III',raw,fo+12*fi)
            if li>=lc:raise ValueError('Invalid GFF label.')
            label=raw[lo+li*16:lo+(li+1)*16].split(b'\0')[0].decode('ascii',errors='replace')
            if label in result:raise ValueError('Duplicate GFF field.')
            if kind in (0,2,4):v=value
            elif kind in (1,3,5):
                bits={1:8,3:16,5:32}[kind];v=value&((1<<bits)-1);v=v-(1<<bits) if v&(1<<(bits-1)) else v
            elif kind==8:v=struct.unpack('<f',struct.pack('<I',value))[0]
            elif kind in (6,7,9):v=unpack({6:'<Q',7:'<q',9:'<d'}[kind],do+value,do,do+dc)[0]
            elif kind in (10,12,13):
                size=unpack('<I',do+value,do,do+dc)[0];data=chunk(do+value+4,size,do,do+dc)
                if kind==10:v=decode(data)
                elif kind==13:v=None
                else:
                    if len(data)<8:raise ValueError('Invalid localized string.')
                    ref,n=struct.unpack_from('<II',data);p=8;texts=[]
                    if n>1000:raise ValueError('Invalid localized string count.')
                    for _ in range(n):
                        if p+8>len(data):raise ValueError('Invalid localized string entry.')
                        lang,size=struct.unpack_from('<II',data,p);p+=8
                        if p+size>len(data):raise ValueError('Truncated localized text.')
                        texts.append((lang,decode(data[p:p+size],lang//2)));p+=size
                    v={'strref':ref,'text':next((s for lang,s in texts if lang==0),texts[0][1] if texts else '')}
            elif kind==11:
                size=chunk(do+value,1,do,do+dc)[0];v=decode(chunk(do+value+1,size,do,do+dc))
            elif kind==14:v=node(value,trail+(index,))
            elif kind==15:
                n=unpack('<I',lso+value,lso,lso+lsc)[0]
                if n>200000:raise ValueError('Excessive GFF list.')
                v=[node(j,trail+(index,)) for j in unpack('<'+'I'*n,lso+value+4,lso,lso+lsc)]
            elif kind in (16,17):v=list(unpack('<'+'f'*(4 if kind==16 else 3),do+value,do,do+dc))
            else:raise ValueError('Unsupported GFF field type '+str(kind))
            if isinstance(v,float) and not math.isfinite(v):v=str(v)
            if kind in (16,17):v=[x if math.isfinite(x) else str(x) for x in v]
            result[label]=v
        return result
    return node(0)
