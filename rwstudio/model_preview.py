"""Bounded, read-only static MDL geometry previews (not an in-game renderer).

Binary field layout: Tim Smith's NWN Binary Model Files Basics:
https://raw.githubusercontent.com/xoreos/xoreos-docs/master/specs/torlack/binmdl.html
Parses the default geometry only; animations, particles and textures are omitted.
"""
import html
import math
import struct
import zlib

IDENTITY=((1,0,0),(0,1,0),(0,0,1))

def rotate(q):
    x,y,z,w=q;length=math.sqrt(sum(v*v for v in q))
    if length<1e-9:return IDENTITY
    x,y,z,w=(v/length for v in q)
    return ((1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w),
            (2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w),
            (2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y))

def mv(m,v):return tuple(sum(m[i][j]*v[j] for j in range(3)) for i in range(3))
def mm(a,b):return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def add(a,b):return tuple(a[i]+b[i] for i in range(3))

def geometry(raw):
    if len(raw)>32_000_000:raise ValueError('Model too large for an interactive preview')
    nodes=[]
    if raw[:4]==b'\0'*4:
        def unpack(fmt,off):
            size=struct.calcsize('<'+fmt)
            if off<0 or off+size>len(raw):raise ValueError('Invalid model offsets')
            return struct.unpack_from('<'+fmt,raw,off)
        u=lambda off:unpack('I',off)[0]
        data=12+u(4);visited=set()
        def walk(off,parent=-1,depth=0):
            if depth>64 or off in visited or len(visited)>4096:raise ValueError('Invalid model hierarchy')
            visited.add(off);n=12+off;flags=u(n+108)
            co,cn=unpack('II',n+72);ko,kn=unpack('II',n+84);fo,fn=unpack('II',n+96)
            if max(cn,kn)>4096 or fn>1000000:raise ValueError('Invalid model arrays')
            pos=(0,0,0);rot=IDENTITY;scale=1
            for i in range(kn):
                kind,rows,time,value,cols,_=unpack('Ihhhbb',12+ko+i*12)
                if rows<1 or value<0:continue
                if kind in (8,20,36):
                    count={8:3,20:4,36:1}[kind]
                    if value+count>fn:raise ValueError('Invalid model controller')
                    val=unpack(str(count)+'f',12+fo+value*4)
                    if kind==8:pos=val
                    elif kind==20:rot=rotate(val)
                    else:scale=val[0]
            node=dict(parent=parent,pos=pos,rot=rot,scale=scale,vertices=[],faces=[])
            index=len(nodes);nodes.append(node)
            m=n+112+(92 if flags&2 else 0)+(216 if flags&4 else 0)+(68 if flags&16 else 0)
            if flags&32 and not flags&512:
                face_off,face_count=unpack('II',m+8)
                vertex_off,vertex_count=unpack('IH',m+444)
                render=u(m+108)
                if face_count>200000:raise ValueError('Too many model faces')
                if render and vertex_count and vertex_off!=0xffffffff:
                    node['vertices']=[unpack('3f',data+vertex_off+i*12) for i in range(vertex_count)]
                    node['faces']=[unpack('3H',12+face_off+i*32+26) for i in range(face_count)]
            for i in range(cn):walk(u(12+co+4*i),index,depth+1)
        walk(u(84))
    else:
        lines=[line.split('#',1)[0].strip().split() for line in raw.decode('latin1').splitlines()]
        names={};node=None;i=0
        while i<len(lines):
            t=lines[i];i+=1
            if not t:continue
            if t[0].lower()=='beginmodelgeom':continue
            if t[0].lower()=='endmodelgeom':break
            if t[0].lower()=='newanim':break
            if t[0].lower()=='node':
                node=dict(parent=-1,pos=(0,0,0),rot=IDENTITY,scale=1,vertices=[],faces=[],render=True,kind=t[1]);names[t[2]]=len(nodes);nodes.append(node)
            elif node:
                key=t[0].lower()
                if key=='parent':node['parent']=names.get(t[1],-1)
                elif key=='position':node['pos']=tuple(map(float,t[1:4]))
                elif key=='orientation':
                    x,y,z,angle=map(float,t[1:5]);s=math.sin(angle/2);node['rot']=rotate((x*s,y*s,z*s,math.cos(angle/2)))
                elif key=='scale':node['scale']=float(t[1])
                elif key=='render':node['render']=t[1]!='0'
                elif key in ('verts','faces'):
                    count=int(t[1])
                    if not 0<=count<=200000 or i+count>len(lines):raise ValueError('Invalid ASCII model array')
                    node['vertices' if key=='verts' else 'faces']=[tuple((float if key=='verts' else int)(v) for v in row[:3]) for row in lines[i:i+count]];i+=count
                elif key=='endnode':node=None
    vertices=[];faces=[];transforms=[]
    for index,n in enumerate(nodes):
        rot=tuple(tuple(v*n['scale'] for v in row) for row in n['rot']);pos=n['pos']
        if n['parent']>=0:
            if n['parent']>=index:raise ValueError('Invalid parent order')
            pr,pp=transforms[n['parent']];pos=add(mv(pr,pos),pp);rot=mm(pr,rot)
        transforms.append((rot,pos))
        if not n.get('render',True) or n.get('kind')=='aabb':continue
        base=len(vertices)
        vertices.extend(add(mv(rot,v),pos) for v in n['vertices'])
        for face in n['faces']:
            if any(v<0 or v>=len(n['vertices']) for v in face):raise ValueError('Invalid model face')
            faces.append(tuple(base+v for v in face))
    if not vertices or not faces:raise ValueError('No visible static mesh in this model')
    if len(vertices)>400000 or any(not math.isfinite(v) or abs(v)>10000 for point in vertices for v in point):raise ValueError('Invalid model dimensions')
    low=[min(p[i] for p in vertices) for i in range(3)];high=[max(p[i] for p in vertices) for i in range(3)]
    return dict(vertices=vertices,faces=faces,bounds=[low,high],dimensions=[round(high[i]-low[i],3) for i in range(3)])

def svg(mesh,title='',angle=35):
    """Actual model geometry, shaded in neutral colours; no fabricated asset art."""
    rad=math.radians(angle);s,c=math.sin(rad),math.cos(rad)
    points=[(c*x-s*y,.48*(s*x+c*y)-.88*z,.88*(s*x+c*y)+.48*z) for x,y,z in mesh['vertices']]
    lo=[min(p[i] for p in points) for i in (0,1)];hi=[max(p[i] for p in points) for i in (0,1)];scale=190/max(hi[0]-lo[0],hi[1]-lo[1],.01)
    project=lambda p:((p[0]-(lo[0]+hi[0])/2)*scale+120,(p[1]-(lo[1]+hi[1])/2)*scale+114)
    polys=[]
    for face in mesh['faces'][::max(1,len(mesh['faces'])//12000)]:
        ps=[points[i] for i in face];a,b,c0=ps
        cross=(b[0]-a[0])*(c0[1]-a[1])-(b[1]-a[1])*(c0[0]-a[0])
        shade=int(135+55*math.tanh(cross));coords=' '.join('%.2f,%.2f'%project(p) for p in ps)
        polys.append((sum(p[2] for p in ps),f'<polygon points="{coords}" fill="rgb({shade},{shade+12},{shade+17})" stroke="#18252b" stroke-width=".12"/>'))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"><title>'+html.escape(title)+' — untextured model preview</title><rect width="240" height="240" fill="#132125"/>'+''.join(p for _,p in sorted(polys))+ '<text x="120" y="231" text-anchor="middle" fill="#bfccd2" font-size="10">Actual mesh · textures/animations omitted</text></svg>').encode()

def raster(mesh,size=200,angle=35):
    """Small software-rendered shape thumbnail, for multimodal asset selection."""
    pixels=bytearray(bytes((19,33,37))*size*size)
    rad=math.radians(angle);s,c=math.sin(rad),math.cos(rad)
    points=[(c*x-s*y,.48*(s*x+c*y)-.88*z,.88*(s*x+c*y)+.48*z) for x,y,z in mesh['vertices']]
    lo=[min(p[i] for p in points) for i in (0,1)];hi=[max(p[i] for p in points) for i in (0,1)]
    scale=(size-30)/max(hi[0]-lo[0],hi[1]-lo[1],.01)
    def project(p):return ((p[0]-(lo[0]+hi[0])/2)*scale+size/2,(p[1]-(lo[1]+hi[1])/2)*scale+size/2)
    faces=sorted(mesh['faces'][::max(1,len(mesh['faces'])//12000)],key=lambda f:sum(points[i][2] for i in f))
    for face in faces:
        a,b,c0=[points[i] for i in face];shade=int(135+55*math.tanh((b[0]-a[0])*(c0[1]-a[1])-(b[1]-a[1])*(c0[0]-a[0])))
        colour=bytes((shade,shade+12,shade+17));ps=[project(points[i]) for i in face]
        for y in range(max(0,math.ceil(min(p[1] for p in ps)-.5)),min(size,math.ceil(max(p[1] for p in ps)-.5))):
            hits=[]
            for j in range(3):
                x1,y1=ps[j];x2,y2=ps[(j+1)%3]
                if min(y1,y2)<=y+.5<max(y1,y2):hits.append(x1+(x2-x1)*(y+.5-y1)/(y2-y1))
            if len(hits)<2:continue
            left=max(0,math.ceil(min(hits)-.5));right=min(size,math.ceil(max(hits)-.5))
            if right>left:pixels[(y*size+left)*3:(y*size+right)*3]=colour*(right-left)
    # Reference axes share the exact camera projection used for the model.
    # Red = local +X, green = local +Y, blue = local +Z.
    for dx,dy,colour in [(c,.48*s,(255,112,112)),(-s,.48*c,(105,238,134)),(0,-1,(117,171,255))]:
        for step in range(24):
            x=round(28+dx*step);y=round(size-30+dy*step)
            for offset in (0,1):
                at=((y+offset)*size+x)*3
                if 0<=x<size and 0<=y+offset<size:pixels[at:at+3]=bytes(colour)
    return pixels

def png(pixels,width,height):
    def chunk(kind,body):return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
    rows=b''.join(b'\0'+pixels[y*width*3:(y+1)*width*3] for y in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')

def contact_sheet(meshes):
    """Up to sixteen numbered actual-shape previews; metadata supplies names."""
    size=200;width=800;height=math.ceil(len(meshes)/4)*220
    pixels=bytearray(bytes((19,33,37))*width*height)
    digits=['111101101101111','010110010010111','111001111100111','111001111001111','101101111001001','111100111001111','111100111101111','111001001001001','111101111101111','111101111001111']
    for index,mesh in enumerate(meshes):
        ox=(index%4)*size;oy=(index//4)*220;thumb=raster(mesh)
        for y in range(size):pixels[((oy+y)*width+ox)*3:((oy+y)*width+ox+size)*3]=thumb[y*size*3:(y+1)*size*3]
        for k,digit in enumerate(str(index+1)):
            for i,bit in enumerate(digits[int(digit)]):
                if bit!='1':continue
                for dy in range(2):
                    for dx in range(2):
                        at=((oy+202+(i//3)*2+dy)*width+ox+8+k*9+(i%3)*2+dx)*3;pixels[at:at+3]=bytes((240,225,178))
    return png(pixels,width,height)
