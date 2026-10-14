"""Collision footprints matching Godot south_scenery.gd's deterministic placements."""
import math
from functools import lru_cache
from app.services.island import LAYOUT, BEACH, exterior_walkable

def segment_distance(x,y,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0.,min(1.,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)

def route_distance(x,y):
    route=LAYOUT['routes'][0]
    return min(segment_distance(x,y,a,b) for a,b in zip(route,route[1:]))

def safe(x,y,clearance):
    if not exterior_walkable(x,y) or y<780 or abs(x)>2200 or route_distance(x,y)<clearance: return False
    for at in [(-250,2900),(-340,2830),(250,2250),(150,940)]:
        if math.hypot(x-at[0],y-at[1])<200: return False
    for at in BEACH['markers'].values():
        if math.hypot(x-at[0],y-at[1])<(clearance+90 if clearance>=100 else 70): return False
    for a,b,w,h in BEACH['solids']:
        if a-clearance<=x<a+w+clearance and b-clearance<=y<b+h+clearance: return False
    return True

@lru_cache(maxsize=128)
def footprints(cx,cy):
    result=[]
    for iy in range(9):
        for ix in range(9):
            seed=(((cx*9+ix)*73856093)^((cy*9+iy)*19349663))%2147483647
            # GDScript snaps positive/negative world coordinates to the same 2-unit grid.
            x=math.floor((cx*1024+ix*112+16+seed%71)/2+.5)*2
            y=math.floor((cy*1024+iy*112+16+(seed//71)%71)/2+.5)*2
            if (math.floor(x/1024),math.floor(y/1024))!=(cx,cy): continue
            beach=y>BEACH['coast_origin'][1]-320
            clearing=math.hypot(x,y-1580)<330
            tree=not beach and not clearing and seed%7<4
            clearance=140 if tree else 76
            if not safe(x,y,clearance) or (route_distance(x,y)>1500 and seed%2): continue
            if tree: result.append((x-11,y-9,22,18))
    for x,y,w,h in [(-250,2900,72,36),(-340,2830,72,36),(250,2250,116,28),(150,940,10,12)]:
        if (math.floor(x/1024),math.floor(y/1024))==(cx,cy): result.append((x-w/2,y-h/2,w,h))
    return result

def blocked(x,y):
    cx,cy=math.floor(x/1024),math.floor(y/1024)
    for dy in range(-1,2):
        for dx in range(-1,2):
            for a,b,w,h in footprints(cx+dx,cy+dy):
                if a-12<=x<a+w+12 and b-8<=y<b+h+8: return True
    return False
