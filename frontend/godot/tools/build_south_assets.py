"""Original second-pass source-pixel art. Reference informs palette/composition only."""
from pathlib import Path
import random, math
namespace={'__file__':str(Path(__file__).with_name('build_pixel_art.py'))}
exec(Path(__file__).with_name('build_pixel_art.py').read_text().split("sample='--sample'")[0],namespace)
Pixel=namespace['Pixel']; folder='cutscene/opening'
# Rich, warm materials with subtle grit rather than high-contrast tile speckles.
for kind,base,colors in [('sand','#edd197',['#e4c68b','#f4dda9','#d8bc83']),('shallow','#62c9b4',['#74d7c0','#55bfae','#8cddc8']),('wet','#d8c18d',['#cfb686','#e0ca96','#c2b389'])]:
 for v in range(4):
  p=Pixel(16,16);p.rect(0,0,16,16,base);r=random.Random(701+v)
  for i in range(21):p.rect(r.randrange(16),r.randrange(16),r.choice([1,1,2]),1,r.choice(colors))
  p.save(folder,f'{kind}-{v}')
# Crown families: explicit pointed palm fronds and clustered broadleaf silhouettes.
leaf=['#203e32','#2c5035','#426b38','#5d873c','#7fa547','#a5c45e']
for variant in range(4):
 p=Pixel(96,112);r=random.Random(100+variant)
 p.oval(23,94,55,12,'#38573d');p.oval(34,99,35,7,'#314b37')
 p.line(47,101,51+variant,48,'#493f30',6);p.line(49,99,53+variant,49,'#8b6941',3)
 for y in range(62,99,6):p.line(48,y,52,y-2,'#bd9457')
 cx,cy=50+variant,43
 for i in range(7):
  a=i*math.tau/7+variant*.24;dx,dy=math.cos(a),math.sin(a);length=36+r.randrange(7)
  ex,ey=round(cx+dx*length),round(cy+dy*length*.76)
  mx,my=round(cx+dx*length*.53),round(cy+dy*length*.53*.76)
  pts=[(cx,cy),(round(mx-dy*9),round(my+dx*9)),(ex,ey),(round(mx+dy*9),round(my-dx*9))]
  p.poly(pts,leaf[0]);p.poly([(cx,cy),(round(mx-dy*7),round(my+dx*7)-1),(ex-1,ey-1),(mx,my)],leaf[3+i%2])
  p.line(cx,cy,ex,ey,leaf[5 if i%3 else 4])
  for j in range(3,9):
   t=j/10;x=round(cx+(ex-cx)*t);y=round(cy+(ey-cy)*t)
   p.line(x,y,round(x-dy*5),round(y+dx*5),leaf[2])
 for x,y in [(cx-2,cy+3),(cx+3,cy+5),(cx+4,cy)]:p.oval(x,y,4,4,'#775a37')
 p.save(folder,f'palm-{variant}')
for variant in range(4):
 p=Pixel(96,112);r=random.Random(220+variant)
 p.oval(15,94,72,13,'#35543b');p.line(47,101,49,49,'#493b2f',9);p.line(49,98,49,52,'#8a7047',3)
 p.line(50,80,29,48,'#685236',4);p.line(51,70,71,41,'#685236',4)
 for cx,cy,rr in [(47,27,24),(27,43,23),(69,41,22),(43,58,26),(68,65,19),(22,66,16)]:
  cx+=r.randrange(-4,5);cy+=r.randrange(-3,4)
  p.oval(cx-rr,cy-rr,rr*2,rr*2,leaf[0]);p.oval(cx-rr+2,cy-rr+1,rr*2-4,rr*2-6,leaf[1])
  p.oval(cx-rr+5,cy-rr+2,rr*2-10,rr*2-12,leaf[2+variant%2])
 for i in range(220):
  x,y=r.randrange(8,87),r.randrange(6,79)
  if p.p.get((x,y)) in leaf[1:4]:
   c=r.choice(leaf[2:5]);p.rect(x,y,3,2,c)
   if i%5==0:p.rect(x,y-1,2,1,leaf[5])
 p.save(folder,f'broadleaf-{variant}')
for kind in ['shrub','flowers','stones','shells','driftwood','trail-marker','outcrop','fallen-tree']:
 for v in range(3):
  p=Pixel(64,64);r=random.Random(kind+str(v));p.oval(8,51,49,8,'#607b43' if kind in ['shrub','flowers'] else '#a89a6e')
  if kind in ['shrub','flowers']:
   for i in range(9):
    x,y=r.randrange(10,46),r.randrange(30,50);rr=r.randrange(6,11)
    p.oval(x-rr,y-rr,rr*2,rr*2,leaf[1]);p.oval(x-rr+1,y-rr,rr*2-3,rr*2-5,leaf[3]);p.rect(x-3,y-rr+2,5,2,leaf[4])
   if kind=='flowers':
    for i in range(12):
     x,y=r.randrange(10,53),r.randrange(27,53);p.rect(x,y,3,2,r.choice(['#f3dc9b','#df9a76','#f3e7b9']));p.dot(x+1,y,'#cb854e')
  elif kind in ['stones','shells']:
   p=Pixel(32,32)
   for i in range(4):
    x,y=r.randrange(2,25),r.randrange(8,27)
    p.oval(x,y,5,4,'#a98c65');p.rect(x+1,y,3,2,'#f5dfb1' if kind=='shells' else '#cfb281');p.dot(x+2,y+1,'#e9cfa0')
  elif kind=='trail-marker':
   # North is up on the island: the arrow points inland toward Willowbrook.
   p.rect(29,32,5,25,'#594c35');p.rect(30,32,2,24,'#b89b64')
   p.poly([(31,15),(46,29),(38,29),(38,41),(24,41),(24,29),(16,29)],'#594c35')
   p.poly([(31,18),(41,27),(35,27),(35,38),(27,38),(27,27),(21,27)],'#bdab76')
   p.line(30,24,30,36,'#877346');p.line(33,29,33,36,'#d0b47d')
  elif kind in ['driftwood','fallen-tree']:
   if kind=='fallen-tree':
    # Level seat, short end stubs, bark grain; foliage stays behind the ends.
    p.oval(2,39,14,12,leaf[2]);p.oval(49,40,12,10,leaf[1])
    p.poly([(4,48),(12,46),(52,46),(61,49),(60,58),(53,61),(9,60),(3,56)],'#4d4432')
    p.rect(8,48,48,5,'#a68852');p.rect(12,48,40,2,'#d0b47d')
    p.rect(9,53,47,5,'#8b6d42');p.rect(17,54,13,2,'#594c35');p.rect(36,56,16,2,'#594c35')
    p.rect(4,49,6,9,'#d0b47d');p.rect(6,51,2,5,'#8b6d42')
    p.line(53,47,57,43,'#8b6d42',3);p.rect(56,42,3,2,'#d0b47d')
   else:
    p.line(7,49,55,39,'#4d4432',9);p.line(8,47,54,37,'#a68852',6);p.line(9,47,53,38,'#d0b47d',2);p.line(22,43,13,31,'#8b6d42',3);p.line(42,40,51,27,'#8b6d42',3)
  else:
   for x,y,rr in [(25,34,22),(43,43,15),(14,48,11)]:
    p.poly([(x-rr,y+rr//2),(x-rr+3,y-rr//2),(x-3,y-rr),(x+rr-3,y-rr//2),(x+rr,y+rr//2),(x+3,y+rr)],'#4b5544')
    p.poly([(x-rr+4,y-rr//2),(x-3,y-rr+2),(x+rr-5,y-rr//2),(x+4,y+3)],'#aaa280')
    p.poly([(x-rr+3,y+rr//2),(x-rr+5,y),(x+4,y+5),(x+rr-3,y),(x+2,y+rr-3)],'#7c8063')
    p.line(x-3,y-rr+5,x+4,y-4,'#c8bd95',2)
  p.save(folder,f'{kind}-{v}')
# Individual fog formations: overlapping irregular lobes, dithered highlights,
# opaque shaded undersides. No curves/gradients or alpha accumulation.
for v in range(7):
 w,h=[(192,112),(224,120),(160,96),(208,104),(184,128),(240,112),(176,104)][v]
 p=Pixel(w,h);r=random.Random(920+v);lobes=[]
 for i in range(14):
  x,y=r.randrange(26,w-26),r.randrange(30,h-25);rx,ry=r.randrange(19,34),r.randrange(14,25)
  pts=[]
  for j in range(16):
   a=j*math.tau/16;rr=r.uniform(.92,1.06)
   pts.append((round((x+math.cos(a)*rx*rr)/2)*2,round((y+math.sin(a)*ry*rr)/2)*2))
  lobes.append(pts)
 for pts in lobes:p.poly(pts,'#879fa3')
 for pts in lobes:p.poly([(x,y-5) for x,y in pts],'#a2b6b8')
 # Connected highlight masses sit within the bank, avoiding a dark ring per lobe.
 for pts in lobes[::3]:p.poly([(round(x*.9+w*.05),round(y*.67)+4) for x,y in pts],'#b4c6c5')
 for i in range(200):
  x,y=r.randrange(8,w-8),r.randrange(8,h-8)
  if p.p.get((x,y))=='#b4c6c5' and i%2:p.rect(x,y,3,1,'#c2d0cc')
 p.save(folder,f'fog-bank-{v}')
print('Original southern coast foliage, details and seven fog formations built')
