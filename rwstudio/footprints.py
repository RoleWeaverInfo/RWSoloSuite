"""Oriented model-bound rectangles for explicit asset placement."""
import math

def box(bounds,x,y,degrees):
    a=math.radians(degrees);c,s=math.cos(a),math.sin(a);lo,hi=bounds
    return [(x+c*u-s*v,y+s*u+c*v) for u,v in ((lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1]))]

def distance(poly,x,y):
    inside=True;signs=[];best=float('inf')
    for a,b in zip(poly,poly[1:]+poly[:1]):
        vx,vy=b[0]-a[0],b[1]-a[1];length=vx*vx+vy*vy
        signs.append(vx*(y-a[1])-vy*(x-a[0]));t=max(0,min(1,((x-a[0])*vx+(y-a[1])*vy)/length)) if length else 0
        best=min(best,math.hypot(x-a[0]-t*vx,y-a[1]-t*vy))
    return 0 if all(v>=-1e-8 for v in signs) or all(v<=1e-8 for v in signs) else best

def overlap(a,b,margin=.15):
    for poly in (a,b):
        for p,q in zip(poly,poly[1:]+poly[:1]):
            nx,ny=q[1]-p[1],p[0]-q[0];length=math.hypot(nx,ny)
            if length<1e-9:continue
            aa=[(x*nx+y*ny)/length for x,y in a];bb=[(x*nx+y*ny)/length for x,y in b]
            if max(aa)+margin<=min(bb) or max(bb)+margin<=min(aa):return False
    return True
