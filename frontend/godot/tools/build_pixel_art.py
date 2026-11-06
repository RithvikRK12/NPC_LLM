"""Original Willowbrook pixel sources. stdlib only; integer pixels, no resampling.
Run with --sample for the scale gate, or without arguments for the full kit.
SVG stores horizontal runs of exact pixel colors and is rasterized 1:1 by Godot.
"""
from pathlib import Path
import math
import random
import sys

ROOT = Path(__file__).resolve().parents[1] / 'assets'
INK='#392f36'; WOOD='#73503b'; LIGHT='#c89a60'; DARK='#533e36'
LEAF=['#294e42','#356348','#4b8050','#68a253','#91bd62']
class Pixel:
    def __init__(self,w,h): self.w=w; self.h=h; self.p={}
    def dot(self,x,y,c):
        if 0<=int(x)<self.w and 0<=int(y)<self.h: self.p[int(x),int(y)]=c
    def rect(self,x,y,w,h,c):
        for yy in range(int(y),int(y+h)):
            for xx in range(int(x),int(x+w)): self.dot(xx,yy,c)
    def line(self,x,y,X,Y,c,width=1):
        n=max(abs(X-x),abs(Y-y),1)
        for i in range(n+1): self.rect(round(x+(X-x)*i/n),round(y+(Y-y)*i/n),width,width,c)
    def oval(self,x,y,w,h,c):
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                if ((xx+.5-x)/w*2-1)**2+((yy+.5-y)/h*2-1)**2<=1: self.dot(xx,yy,c)
    def poly(self,pts,c):
        for y in range(min(p[1] for p in pts),max(p[1] for p in pts)+1):
            for x in range(min(p[0] for p in pts),max(p[0] for p in pts)+1):
                inside=False; j=len(pts)-1
                for i in range(len(pts)):
                    a,b=pts[i],pts[j]
                    if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: inside=not inside
                    j=i
                if inside:self.dot(x,y,c)
    def paste(self,other,x,y):
        for (xx,yy),c in other.p.items():self.dot(xx+x,yy+y,c)
    def save(self,folder,name):
        out=ROOT/folder; out.mkdir(parents=True,exist_ok=True)
        runs=[]
        for y in range(self.h):
            x=0
            while x<self.w:
                c=self.p.get((x,y)); end=x+1
                while end<self.w and self.p.get((end,y))==c:end+=1
                if c:runs.append(f'<path fill="{c}" d="M{x} {y}h{end-x}v1H{x}z"/>')
                x=end
        (out/(name+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" shape-rendering="crispEdges">'+''.join(runs)+'</svg>\n')

def shadow(p,x,y,w):
    p.oval(x,y,w,6,'#405645');p.rect(x+4,y+1,w-8,3,'#394c40')

def window(p,x,y):
    p.rect(x-2,y-2,16,20,DARK);p.rect(x-1,y-1,14,18,LIGHT)
    p.rect(x,y,12,15,'#283e43');p.rect(x+1,y+1,4,6,'#e9bf71');p.rect(x+7,y+1,4,6,'#f4d68c')
    p.rect(x+1,y+9,4,5,'#b99060');p.rect(x+7,y+9,4,5,'#d2aa66')
    p.rect(x+5,y,2,16,WOOD);p.rect(x,y+7,12,2,WOOD);p.rect(x-3,y+16,18,3,WOOD)
    p.rect(x-3,y+19,18,3,'#496b43')
    for dx in [0,4,8,12]:p.rect(x-2+dx,y+18,2,2,'#f5e5ac');p.dot(x-1+dx,y+18,'#c96f61')

def building(workshop=False,blue=False):
    w,h=(128,120) if workshop else (80,96);p=Pixel(w,h); b=h-5
    shadow(p,4,b-1,w-8)
    left,right=8,w-9; top=49 if workshop else 40
    p.rect(left,top,right-left,b-top,DARK);p.rect(left+2,top+2,right-left-4,b-top-5,'#d4b77e' if workshop else '#c8cd98')
    rng=random.Random(24+blue)
    for _ in range(w*2):
        x=rng.randrange(left+3,right-2); y=rng.randrange(top+3,b-5);p.rect(x,y,2,1,rng.choice(['#ba9c6c','#ded0a0','#b4b886'] if not workshop else ['#c5a476','#e3c38c','#b18a60']))
    for yy in range(b-10,b,4):
        for xx in range(left,right,9):
            p.rect(xx,yy,8,3,rng.choice(['#7e8074','#a8a58c','#b7ad8d']));p.rect(xx,yy,8,1,'#cac0a0')
    for x in [left,left+5,(w//2),right-5]:p.rect(x,top,3,b-top-10,WOOD);p.rect(x,top,1,b-top-10,LIGHT)
    p.rect(left,top+20,right-left,3,WOOD)
    # Chimney, behind the roof.
    p.rect(w-29,9,12,28,DARK)
    for y in range(10,36,4):
        for x in range(w-28,w-18,5):p.rect(x,y,4,3,'#a19a81');p.dot(x,y,'#c8b998')
    p.rect(w-31,7,16,4,'#b4a585')
    # Roof scanlines form exact stair-step silhouettes, then individual shingles.
    peak=5; roof_bottom=top+6
    p.poly([(2,roof_bottom),(w//2,peak),(w-2,roof_bottom+1)],DARK)
    for y in range(peak+3,roof_bottom-1):
        half=int((y-peak)*(w//2-4)/(roof_bottom-peak));x0=w//2-half;x1=w//2+half
        for x in range(x0,x1):
            row=(y-peak)//5; seam=(x+row%2*5)%10
            palette=['#6a5661','#81717a','#9c8b87','#b29a8c'] if blue else ['#813f38','#a9503c','#c36a45','#df8d58']
            c=palette[0] if y%5==0 or seam==0 else palette[2 if y%5==1 else 1]
            if seam in (2,3) and y%5==2:c=palette[3]
            p.dot(x,y,c)
    p.line(2,roof_bottom,w//2,peak,'#d19b60',2);p.line(w//2,peak,w-3,roof_bottom,'#9c6744',2)
    p.rect(3,roof_bottom,w-6,3,DARK);p.rect(5,roof_bottom,w-10,1,LIGHT)
    # Recessed plank door, hinges, handle and worn doorstep.
    dx=w//2-7;p.rect(dx-2,b-32,18,26,DARK);p.rect(dx,b-30,14,24,'#735b42' if workshop else '#4f7464')
    for x in range(dx+2,dx+14,4):p.rect(x,b-29,1,21,'#aa8150' if workshop else '#77927a')
    p.rect(dx,b-28,14,2,DARK);p.rect(dx,b-12,14,2,DARK);p.dot(dx+11,b-19,'#f3cf71')
    p.rect(dx-4,b-6,22,3,'#bdb598');p.rect(dx-6,b-3,26,2,'#d3c6a5')
    window(p,left+11,b-36);window(p,right-24,b-36)
    if workshop:
        p.rect(w//2-18,top+8,36,12,WOOD);p.rect(w//2-17,top+9,34,9,'#d4af70')
        # Anvil emblem, rather than unreadable baked text.
        p.rect(w//2-8,top+11,16,2,INK);p.rect(w//2-3,top+13,6,3,INK);p.rect(w//2-6,top+16,12,1,INK)
    else:
        p.rect(left+3,b-22,2,12,'#466a4b')
        for y in range(b-28,b-10,4):p.rect(left+2,y,4,2,'#648846');p.dot(left+4,y-1,'#e1b76b')
    for x in range(left+4,right-2,8):p.rect(x,roof_bottom+3,2,3,LIGHT)
    for x,sign in [(left+6,1),(right-6,-1)]:
        p.line(x,top+22,x+sign*9,top+31,WOOD,2);p.line(x,top+24,x+sign*7,top+31,LIGHT)
    lx=w//2+13
    p.line(lx,b-32,lx+5,b-32,DARK);p.rect(lx+4,b-32,1,4,DARK)
    p.rect(lx+2,b-28,5,8,DARK);p.rect(lx+3,b-27,3,5,'#f1ca71');p.dot(lx+3,b-27,'#fff1ab')
    # Wood grain and door pegs stay within their structural surfaces.
    for y in range(b-27,b-11,4):p.dot(dx+4,y,'#b18b55');p.dot(dx+9,y+1,DARK)
    return p

def tree(variant=0,phase=0):
    p=Pixel(48,72);shadow(p,8,65,35);p.poly([(19,68),(21,35),(28,35),(29,67),(25,65)],DARK)
    p.rect(23,36,3,30,'#94663e');p.rect(23,43,1,18,'#bf9250');p.line(24,55,14,41,WOOD,2);p.line(25,49,34,34,WOOD,2)
    rng=random.Random(98+variant)
    clusters=[[(24,15,15),(13,27,12),(33,28,13),(24,38,14),(10,40,9),(37,42,9)],[(24,20,18),(14,31,13),(34,31,13),(24,42,13)],[(24,12,11),(23,24,14),(24,37,17),(24,45,18)]][variant]
    for x,y,r in clusters:
        p.oval(x-r,y-r,r*2,r*2,LEAF[0]);p.oval(x-r+1,y-r,r*2-3,r*2-4,LEAF[1])
    for _ in range(170):
        x=rng.randrange(4,44);y=rng.randrange(3,51)
        if p.p.get((x,y)) in LEAF:
            c=LEAF[rng.choices(range(1,5),[2,4,4,1])[0]];p.rect(x,y,3,2,c);p.dot(x,y-1,c)
    for x,y in [(13,11),(26,7),(7,29),(32,24)]:p.rect(x+phase,y,3,1,LEAF[4])
    return p

def bench():
    p=Pixel(48,32);shadow(p,4,26,40)
    for x in [7,36]:p.rect(x,17,4,11,DARK);p.rect(x,18,1,9,LIGHT)
    p.rect(3,14,42,8,WOOD);p.rect(2,12,44,5,LIGHT);p.rect(4,13,40,1,'#e3bb7a')
    for x in range(7,42,8):p.dot(x,15,DARK)
    p.poly([(19,4),(37,4),(33,7),(28,8),(28,11),(22,11),(22,7)],'#414a53');p.rect(20,4,16,1,'#9babb0')
    p.line(7,6,13,12,WOOD,2);p.rect(5,5,6,3,'#87979d');p.rect(5,5,5,1,'#ced2b8')
    return p

def stall(cloth=False,phase=0):
    p=Pixel(48,48);shadow(p,2,41,44)
    for x in [5,40]:p.rect(x,12,3,31,DARK);p.rect(x,13,1,29,LIGHT)
    p.rect(5,29,38,13,WOOD)
    for x in range(7,42,6):p.rect(x,31,4,10,'#ad7a49');p.rect(x,32,1,8,LIGHT)
    p.rect(3,28,42,3,'#d2a76c')
    for i in range(3):
        x=8+i*11;p.rect(x,21,10,7,DARK);p.rect(x,22,10,6,'#9c7643')
        if cloth:
            for j,c in enumerate(['#668b99','#bc7e92','#e3c07a']):p.rect(x+1,22+j,8,2,c);p.dot(x+1,22+j,'#e9d1a0')
        else:
            for xx,yy in [(x+2,23),(x+6,23),(x+4,25)]:
                p.oval(xx,yy,4,3,['#c45b43','#dca34e','#64934c'][i]);p.dot(xx+1,yy,'#f0bd6c');p.dot(xx+1,yy-1,LEAF[1])
    for y in range(4,17):
        left=max(1,7-(y-4)//2);right=48-left
        for x in range(left,right):p.dot(x,y,'#ead9a4' if (x//6)%2 else ('#c7994d' if cloth else '#be6050'))
    p.rect(1,16+phase,46,4,DARK)
    for x in range(2,46,6):p.rect(x,16+phase,5,4,'#f3dfb0' if x%12==8 else ('#c7994d' if cloth else '#cb7158'))
    return p

def character(role='player',direction=0,frame=0):
    p=Pixel(24,32);shadow(p,5,27,14)
    coat={'player':'#3c8592','craftsman':'#c38a45','gatherer':'#648954'}[role]
    hi={'player':'#66b4bc','craftsman':'#e4b867','gatherer':'#99b76a'}[role]
    hair={'player':'#604133','craftsman':'#6b4636','gatherer':'#753e37'}[role]
    # Fixed contact row 29; walk frames move one boot, never the whole body.
    stride=[0,-1,0,1,0][frame]
    p.rect(8,22,3,6,INK);p.rect(13,22,3,6,INK)
    p.rect(7,27+min(stride,0),5,2,'#6d5041');p.rect(13,27-min(stride,0),5,2,'#6d5041')
    p.rect(8,23,2,3,'#53616a');p.rect(14,23,2,3,'#53616a')
    p.rect(6,13,12,11,INK);p.rect(7,14,10,9,coat);p.rect(7,14,3,8,hi)
    p.rect(4,15+stride,3,7,coat);p.rect(17,15-stride,3,7,coat)
    p.rect(4,21+stride,3,2,'#d9a374');p.rect(17,21-stride,3,2,'#d9a374')
    p.rect(8,21,9,2,'#73523a');p.dot(12,21,'#e4bd77')
    if role=='craftsman':p.rect(9,16,7,7,'#78513d');p.rect(10,17,1,5,'#b27a4b');p.rect(11,20,4,2,DARK)
    if role=='player':p.line(8,14,16,21,'#d4ac66');p.rect(15,20,4,4,'#956344');p.rect(16,21,2,1,LIGHT)
    if role=='gatherer':p.rect(16,16,4,8,'#9d764a');p.rect(17,17,2,6,'#c6a26b')
    p.rect(8,5,9,10,INK);p.rect(7,7,11,6,INK);p.rect(8,7,9,7,'#d39b70');p.rect(9,7,6,6,'#edbe89')
    p.rect(7,4,10,4,hair);p.rect(9,3,6,1,hair);p.rect(6,6,3,5,hair);p.rect(16,6,2,5,hair)
    p.rect(8,4,6,1,'#956342');p.rect(8,6,3,2,hair)
    if direction==3:
        p.rect(8,7,9,7,hair);p.rect(9,8,3,4,'#805339')
    else:
        eyes=[(10,10),(15,10)] if direction==0 else ([(9,10)] if direction==1 else [(16,10)])
        for x,y in eyes:p.dot(x,y,INK)
        p.rect(12,13,2,1,'#a15e4d')
        if role=='craftsman':p.rect(9,12,7,3,hair);p.rect(11,13,3,1,'#dcaa79')
    if role=='gatherer':p.rect(7,4,11,2,'#496c49');p.rect(9,3,8,1,'#7d9d59');p.dot(17,3,'#e5bd68')
    return p

def portrait(role):
    p=Pixel(48,48);p.rect(0,0,48,48,DARK);p.rect(1,1,46,46,LIGHT);p.rect(3,3,42,42,'#ceb58a')
    for y in range(4,44):p.rect(4,y,40,1,'#d8c69a' if y<24 else '#bca57d')
    coat={'player':'#3c8592','craftsman':'#c38a45','gatherer':'#648954'}[role]
    p.poly([(7,44),(10,34),(20,30),(31,30),(40,36),(43,44)],INK);p.poly([(9,44),(12,35),(21,31),(30,31),(39,36),(41,44)],coat)
    p.rect(21,28,9,7,'#c28864');p.rect(20,11,14,20,'#e6b786');p.rect(16,14,20,12,'#e6b786');p.rect(17,17,4,10,'#c88f67')
    p.rect(21,14,10,11,'#f2cd9b');p.rect(17,10,18,5,'#684333');p.rect(15,13,6,9,'#684333');p.rect(33,13,4,9,'#684333')
    p.poly([(15,13),(17,7),(27,5),(36,9),(36,14),(28,11),(24,16),(20,12)],'#684333');p.rect(20,8,10,2,'#956244')
    for x in [22,30]:p.rect(x,20,3,3,'#faf0d0');p.rect(x+1,20,2,3,'#3c5148');p.dot(x+1,20,INK);p.rect(x-1,18,4,1,DARK)
    p.rect(27,23,2,3,'#c88f67');p.rect(24,28,6,1,'#9d5d4e');p.rect(25,28,4,1,'#bd7962');p.dot(20,25,'#dc9e79')
    if role=='craftsman':
        p.rect(18,25,16,6,'#78503b');p.rect(22,26,9,3,'#e6b786');p.rect(24,29,5,1,'#a66e4b');p.rect(16,35,3,9,DARK);p.rect(16,39,20,5,'#79533e')
    elif role=='gatherer':
        p.poly([(14,14),(15,7),(24,4),(35,7),(39,14)],'#446748');p.rect(15,12,24,3,'#729358');p.rect(18,8,12,2,'#8fa65e');p.rect(32,34,3,10,LIGHT)
    else:p.poly([(13,34),(20,32),(29,34),(34,38),(28,40),(18,36)],'#66b4bc');p.line(14,38,18,44,LIGHT,2)
    return p

def terrain(kind='grass',variant=0):
    p=Pixel(16,16);rng=random.Random(42+variant)
    base={'grass':'#72934f','path':'#c8ac72','soil':'#806348','shade':'#57794a','edge':'#a6a06a','moss':'#64884c'}[kind];p.rect(0,0,16,16,base)
    pal={'grass':['#799c53','#85a45a','#698b4e'],'path':['#d6ba80','#c0a16b','#b99b69'],'soil':['#9d7c50','#715a44','#b38a54'],'shade':['#60834d','#688b50','#4f7148'],'edge':['#b4ab70','#90965e','#b5a673'],'moss':['#6b8e50','#729653','#5e814b']}[kind]
    for _ in range(14):
        x=rng.randrange(16);y=rng.randrange(16);p.rect(x,y,2,1,rng.choice(pal))
    return p

def prop(kind):
    p=Pixel(48,56)
    if kind=='well':
        shadow(p,4,49,40);p.oval(6,34,36,17,DARK);p.oval(7,33,34,13,'#a4a18c');p.oval(12,34,24,8,'#344c51')
        for y in [41,45]:
            for x in range(9,40,7):p.rect(x,y,6,3,'#b9b49a');p.dot(x,y,'#d9cfac')
        for x in [8,37]:p.rect(x,18,3,26,WOOD);p.rect(x,18,1,26,LIGHT)
        p.line(8,28,39,28,DARK,2);p.rect(23,26,1,13,LIGHT);p.rect(21,37,6,4,'#b58a54')
        p.poly([(2,22),(24,7),(46,22)],DARK)
        for y in range(10,22):
            half=(y-7)*22//15
            for x in range(24-half,24+half):p.dot(x,y,'#bd7449' if y%4==0 else '#99573e')
        p.rect(3,22,42,2,LIGHT)
    elif kind=='board':
        shadow(p,7,49,34)
        for x in [12,34]:p.rect(x,19,3,31,WOOD)
        p.rect(7,14,34,25,DARK);p.rect(9,16,30,21,'#9f784d');p.rect(8,12,32,3,LIGHT)
        for x,y in [(12,19),(23,18),(19,28),(30,27)]:
            p.rect(x,y,6,7,'#ead8aa');p.rect(x+1,y+2,4,1,'#a28b67');p.dot(x+3,y,'#ba6955')
    elif kind=='logs':
        shadow(p,3,48,42)
        for y in [36,41,46]:
            for x in [6,22]:p.rect(x,y,18,5,WOOD);p.oval(x-2,y,6,5,LIGHT);p.oval(x-1,y+1,4,3,'#9b6d40');p.dot(x,y+2,'#d8ad6e');p.rect(x+4,y,11,1,'#a67e4d')
    elif kind=='fence':
        for x in [4,20,36]:p.rect(x,28,4,23,WOOD);p.rect(x,27,4,3,LIGHT);p.rect(x,30,1,19,'#bd8e57')
        for y in [34,43]:p.rect(4,y,36,3,'#a17448');p.rect(4,y,36,1,LIGHT)
    elif kind=='flowers':
        rng=random.Random(43)
        for _ in range(24):
            x=rng.randrange(8,40);y=rng.randrange(35,52);p.rect(x,y,1,3,'#4d7747');p.rect(x-1,y-1,3,2,rng.choice(['#dd956f','#e8d493','#bfa1bc']));p.dot(x,y,'#f1d883')
    elif kind=='bush':
        shadow(p,5,48,39)
        for x,y in [(13,43),(24,39),(34,44)]:
            p.oval(x-10,y-10,20,16,LEAF[1]);p.oval(x-8,y-9,15,10,LEAF[2]);p.rect(x-4,y-7,5,2,LEAF[3]);p.dot(x+1,y-2,'#d9a95c')
    elif kind=='barrel':
        shadow(p,12,48,26);p.rect(14,29,21,20,DARK);p.oval(13,27,23,8,LIGHT)
        p.rect(15,31,19,15,'#b18450');p.oval(15,28,19,5,'#86613e')
        for x in range(17,34,4):p.rect(x,33,1,14,'#d0a166')
        for y in [33,44]:p.rect(14,y,21,2,'#58615e');p.rect(15,y,19,1,'#899484')
    elif kind=='crate':
        shadow(p,10,48,30);p.rect(11,32,26,18,DARK);p.rect(12,33,24,15,'#ae8150')
        for y in [34,40,46]:p.rect(13,y,22,2,'#d1a76a')
        for x in [13,32]:p.rect(x,33,3,15,'#caa06a');p.dot(x+1,34,DARK);p.dot(x+1,46,DARK)
        p.line(16,34,31,46,WOOD,2)
    elif kind=='garden':
        p.rect(4,15,40,37,WOOD);p.rect(5,16,38,35,'#876545')
        for y in [18,28,38,48]:p.rect(6,y,36,2,'#ad8650')
        for y in [23,33,43]:
            for x in [11,22,33]:
                p.rect(x,y,2,4,LEAF[0]);p.rect(x-3,y-2,3,3,LEAF[2]);p.rect(x+2,y-3,3,3,LEAF[3]);p.dot(x,y,'#d4aa5e')
        p.rect(4,15,40,2,LIGHT);p.rect(4,16,2,35,LIGHT)
    elif kind=='smoke':
        for x,y,r in [(24,45,4),(22,36,5),(27,25,6),(23,12,7)]:p.oval(x-r,y-r,r*2,r*2,'#c4c5ab');p.oval(x-r,y-r,r*2-2,r*2-2,'#ddd6b8')
    return p

def item(kind):
    p=Pixel(24,24)
    if kind in ['wood','axe','hammer','saw']:
        if kind=='wood':
            for x,y in [(4,11),(8,7),(9,14)]:p.line(x,y,x+10,y-5,WOOD,5);p.line(x+1,y-1,x+10,y-6,LIGHT,2);p.oval(x-2,y-1,5,5,'#dbb677');p.dot(x,y+1,WOOD)
        else:
            p.line(6,20,16,5,DARK,3);p.line(6,19,16,4,LIGHT,1)
            if kind=='axe':p.poly([(12,4),(20,3),(21,10),(15,9)],'#526371');p.rect(19,4,2,6,'#c7d0bc')
            elif kind=='hammer':p.rect(9,3,12,5,INK);p.rect(10,3,10,3,'#91a5a7');p.rect(10,3,10,1,'#d1d3b8')
            else:p.poly([(5,15),(17,3),(21,7),(9,19)],'#a9b7af');p.line(8,17,19,6,'#e4dfc5');p.rect(4,15,4,6,WOOD)
    elif kind in ['string','rope']:
        c='#e8d6a2' if kind=='string' else '#c6a16b'
        for y in [7,10,13,16]:p.oval(5,y,14,6,DARK);p.oval(6,y,12,4,c);p.rect(9,y+1,6,2,'#a78c61')
        p.line(17,18,21,21,c,2)
    elif kind=='bow':
        p.line(6,3,16,8,DARK,3);p.line(16,8,17,15,DARK,3);p.line(17,15,8,22,DARK,3)
        p.line(7,3,16,8,LIGHT,2);p.line(16,8,17,15,LIGHT,2);p.line(17,15,8,22,LIGHT,2);p.line(6,3,8,22,'#ead7a6')
    elif kind=='water':
        p.rect(8,3,8,3,WOOD);p.rect(9,6,6,2,'#b9d6c2');p.rect(6,8,12,13,INK);p.rect(7,9,10,11,'#548d9d');p.rect(8,11,8,7,'#79b4bd');p.rect(8,10,2,6,'#c0dbcb')
    elif kind=='food':
        p.oval(3,7,19,14,WOOD);p.oval(4,6,17,13,'#dca565');p.oval(5,6,15,9,'#edc581')
        for x in [8,13,17]:p.line(x,8,x-2,13,'#aa7447',2)
    elif kind=='fruits':
        for x,y in [(5,11),(12,12),(9,6)]:p.oval(x,y,8,8,'#a8463c');p.oval(x+1,y,6,6,'#d87950');p.dot(x+2,y+1,'#edb66c');p.line(x+4,y,x+5,y-3,LEAF[1],2)
    return p

sample='--sample' in sys.argv
building(True).save('world','workshop');building().save('world','cottage-a');tree().save('world','tree-0');bench().save('world','bench');stall().save('world','produce-0');character().save('characters','sample');portrait('player').save('portraits','player')
for k in ['grass','path','soil','shade','edge','moss']:
    for v in range(4):terrain(k,v).save('world',f'{k}-{v}')
if not sample:
    building(blue=True).save('world','cottage-b')
    for role in ['player','craftsman','gatherer']:
        sheet=Pixel(120,128)
        for d in range(4):
            for f in range(5):sheet.paste(character(role,d,f),f*24,d*32)
        sheet.save('characters',role);portrait(role).save('portraits',role)
    for v in range(3):
        for phase in range(2):tree(v,phase).save('world',f'tree-{v}-{phase}')
    for phase in range(2):
        stall(False,phase).save('world',f'produce-{phase}');stall(True,phase).save('world',f'cloth-{phase}')
    for k in ['well','board','logs','fence','flowers','bush','smoke','barrel','crate','garden']:prop(k).save('world',k)
    for k in ['wood','string','bow','food','water','axe','hammer','saw','rope','fruits']:item(k).save('items/pixel',k)
print('Built exact-grid sample' if sample else 'Built full original pixel kit')
