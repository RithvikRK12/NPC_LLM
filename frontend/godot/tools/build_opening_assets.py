"""Original exact-grid opening art and deterministic synthesized audio. No external assets."""
from pathlib import Path
import math, random, struct, wave
# Reuse only the existing kit's definitions; do not regenerate unrelated files.
namespace={'__file__':str(Path(__file__).with_name('build_pixel_art.py'))}
exec(Path(__file__).with_name('build_pixel_art.py').read_text().split("sample='--sample'")[0],namespace)
Pixel=namespace['Pixel']; character=namespace['character']
folder='cutscene/opening'
INK='#392f36'; DARK='#533e36'; WOOD='#73503b'; LIGHT='#c89a60'
for damage in range(4):
 for turn in range(2):
    p=Pixel(160,192)
    bow=80-turn*8
    p.poly([(bow,14),(123,53),(132,132),(118,166),(42,166),(28,132),(37,53)],'#283e43')
    p.poly([(bow,10),(119,49),(128,128),(114,162),(46,162),(32,128),(41,49)],INK)
    p.poly([(bow,13),(116,51),(124,128),(111,158),(49,158),(36,128),(44,51)],DARK)
    p.poly([(bow,20),(109,52),(116,129),(106,149),(54,149),(44,129),(51,52)],'#ac8052')
    for y in range(52,146,6):
      p.line(47,y,112,y,WOOD);p.line(48,y+1,111,y+1,'#c39b64')
      for x in range(52,111,16):p.rect(x+(y%3),y+2,1,3,'#8f693f')
    for side in [-1,1]:
      for y in range(48,140,10):
        x=80+side*(32 if y<124 else 28)
        p.rect(x,y,3,5,LIGHT);p.rect(x,y+3,4,2,WOOD)
      p.line(80+side*35,52,80+side*39,124,'#b08957',2)
    p.rect(57,131,46,12,DARK);p.rect(59,132,42,8,LIGHT)
    p.rect(62,135,36,1,WOOD)
    p.rect(54,100,15,20,DARK);p.rect(56,101,11,17,'#8c693f')
    p.rect(55,106,13,2,INK);p.rect(55,115,13,2,INK)
    p.rect(96,114,11,10,DARK);p.rect(97,115,9,8,LIGHT);p.line(97,115,105,122,WOOD)
    if damage<2:
      p.rect(77,35,6,86,DARK);p.rect(78,35,2,85,LIGHT)
      p.line(43,54,80,116,'#bca77b');p.line(116,54,80,116,'#bca77b')
      p.rect(26,48,107,4,DARK);p.rect(27,48,105,1,LIGHT)
      p.poly([(30,51),(128,51),(123-turn*6,74),(109,88),(52,88),(35+turn*4,74)],'#bcb9a1')
      p.poly([(31,52),(124,52),(121-turn*6,72),(106,83),(53,83),(38+turn*4,72)],'#ded9b7')
      for x in [46,62,80,98,114]:p.line(x,53,x+2,80,'#c6c3a5')
      p.rect(77,33,12,4,'#a65742');p.rect(77,37,9,3,'#c88350')
    elif damage==3:
      p.line(24,83,137,95,DARK,5);p.line(24,83,135,95,LIGHT,2)
      p.poly([(36,80),(72,84),(65,102),(42,99)],'#c6c3a5');p.poly([(95,91),(122,94),(117,106),(100,104)],'#ded9b7')
      p.line(38,81,22,105,'#bca77b');p.line(130,95,145,122,'#bca77b')
    if damage:
      # Broken bow has a dark deck passage and splintered rails, not deep water.
      p.poly([(64,12),(96,12),(96,64),(91,69),(86,64),(80,72),(74,64),(64,70)],'#7c7054')
      for x in [64,92]:p.rect(x,34,3,25,LIGHT);p.line(x,34,x-4,22,WOOD,2)
      for y in [53,61]:p.rect(65,y,29,2,'#b29c6b')
      p.line(38,110,47,115,INK,2);p.line(114,99,123,113,INK,2)
      for i in range(9):p.rect(20+i*13,170+(i%3)*4,8,2,LIGHT)
    p.save(folder,f'ship-{damage}-{turn}')
# Discrete hand-authored mast fall poses, rasterized on the same integer grid.
for phase in range(5):
    p=Pixel(160,192)
    end=[(80,35),(94,42),(113,56),(132,76),(137,95)][phase]
    p.line(80,116,end[0],end[1],DARK,5);p.line(80,116,end[0],end[1],LIGHT,2)
    if phase<3:
      y=49+phase*13
      p.poly([(29+phase*12,y),(128,y+phase*8),(111,y+25),(52+phase*8,y+25)],'#c6c3a5')
      p.line(30+phase*12,y,128,y+phase*8,LIGHT)
    else:
      p.poly([(36,80),(72,84),(65,102),(42,99)],'#c6c3a5')
      p.poly([(95,91),(122,94),(117,106),(100,104)],'#ded9b7')
    p.save(folder,f'mast-fall-{phase}')
# Dedicated recovery poses use the player's palette and unchanged feet pivot (12,30).
sheet=Pixel(144,32)
for index,pose in enumerate(['recover','brace','stand','climb_out','fall','look']):
    if pose in ['stand','look']: c=character('player',3 if pose=='stand' else 1,0)
    else:
      c=Pixel(24,32)
      c.oval(3,27,19,3,'#405645')
      if pose in ['recover','fall']:
        c.rect(4,22,16,6,INK);c.rect(8,23,11,4,'#3c8592');c.rect(4,22,7,5,'#604133');c.rect(5,24,5,3,'#edbe89');c.rect(17,26,5,3,'#6d5041');c.rect(10,23,5,1,'#66b4bc');c.rect(12,27,6,1,'#d4ac66')
      else:
        c.rect(7,24,5,5,'#6d5041');c.rect(15,25,5,4,'#6d5041');c.rect(7,21,5,5,INK);c.rect(13,22,6,4,INK)
        c.rect(5,15,14,9,INK);c.rect(6,16,12,7,'#3c8592');c.rect(6,16,3,6,'#66b4bc');c.line(7,16,15,22,'#d4ac66')
        c.rect(8,8,9,9,'#604133');c.rect(8,11,9,5,'#edbe89');c.rect(7,8,10,4,'#604133');c.dot(15,13,INK)
        c.rect(17,18,4,7,'#3c8592');c.rect(19,24,3,3,'#d39b70');c.rect(3,18,4,8,'#3c8592');c.rect(3,25,3,2,'#d39b70')
        if pose=='climb_out':c.rect(3,17,3,8,'#66b4bc');c.rect(2,16,4,2,'#edbe89');c.rect(7,25,4,4,'#53616a')
    sheet.paste(c,index*24,0)
sheet.save(folder,'recovery')
# Coast materials, with clustered edges and source-scale grit.
rng=random.Random(71)
for kind,base,palette in [('sand','#d5bc83',['#bca576','#e1cc98','#cbb480']),('shallow','#4d8589',['#679c9b','#79ada8','#406f7d'])]:
 for variant in range(4):
    p=Pixel(16,16);p.rect(0,0,16,16,base)
    for i in range(15):p.rect(rng.randrange(16),rng.randrange(16),rng.choice([1,2,3]),1,rng.choice(palette))
    p.save(folder,f'{kind}-{variant}')
# Raised coastal rock clusters use the kit's stepped silhouettes and cool palette.
p=Pixel(48,48)
p.poly([(3,35),(5,14),(16,5),(34,7),(43,18),(46,40),(34,45),(12,43)],'#40545b')
p.poly([(5,30),(8,14),(17,8),(33,9),(41,19),(43,37),(32,42),(13,39)],'#667b77')
p.poly([(8,17),(17,7),(33,9),(40,17),(33,25),(16,24)],'#9da391')
p.poly([(8,19),(16,26),(33,27),(39,21),(37,33),(28,37),(14,32)],'#7d8f86')
for x,y,w in [(10,16,7),(20,10,10),(30,18,6),(12,29,8),(27,35,11)]:p.rect(x,y,w,1,'#b1b59c')
p.line(22,26,21,37,'#526a69');p.line(34,12,29,18,'#778a80')
p.save(folder,'coast-rock')
# Short neutral-pitch event samples. Capped source peaks allow overlapped crash layers.
assets=Path(__file__).parents[1]/'assets'/folder
rate=22050
for name,duration in [('surf',4),('wind',4),('impact',.65),('crack',.45),('mast',.75),('splash',.8),('cloth',.2),('creak',.6),('step',.12),('bird',.6)]:
    rng=random.Random(name);smooth=0; values=[]
    for i in range(int(rate*duration)):
      t=i/rate;n=rng.uniform(-1,1);smooth=.96*smooth+.04*n
      if name in ('wind','surf'):
        envelope=.6+.25*math.sin(t*math.tau/duration)
        value=(smooth*2.5 if name=='wind' else .14*n+smooth*2)*envelope*.33
      else:
        decay=math.exp(-t*(8 if name=='impact' else 6))*(min(t/.008,1))
        tone=math.sin(math.tau*(64*t-12*t*t)) if name=='impact' else math.sin(math.tau*(350*t+160*t*t))
        if name=='bird':value=math.sin(math.tau*(1600*t+700*t*t))*math.sin(t*27)**6*math.exp(-t*3)*.14
        elif name=='creak':value=tone*math.sin(t*14)*decay*.25
        elif name=='step':value=(n*.3+smooth)*decay*.28
        elif name=='impact':value=(tone*.65+n*.15)*decay*.5
        else:value=(n*.45+smooth*(2 if name=='splash' else 1))*decay*.5
      values.append(struct.pack('<h',int(max(-.85,min(.85,value))*32767)))
    with wave.open(str(assets/f'{name}.wav'),'wb') as wav:
      wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(b''.join(values))
print('Opening ship, recovery poses, shore tiles and audio built')

# The second visual pass owns the final coast palette and foliage family.
exec(Path(__file__).with_name("build_south_assets.py").read_text(), {"__file__": str(Path(__file__).with_name("build_south_assets.py"))})
