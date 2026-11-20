"""Build the original tile art for the Everest cartridge. Requires Pillow and NumPy."""
from pathlib import Path
import math
import random
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art'
OUT.mkdir(exist_ok=True)

# A five-by-seven bitmap alphabet, used for all cartridge lettering.
GLYPHS = {
',':[0,0,0,0,0,4,8],
'A':[14,17,17,31,17,17,17],'B':[30,17,17,30,17,17,30],'C':[14,17,16,16,16,17,14],
'D':[28,18,17,17,17,18,28],'E':[31,16,16,30,16,16,31],'F':[31,16,16,30,16,16,16],
'G':[14,17,16,23,17,17,15],'H':[17,17,17,31,17,17,17],'I':[14,4,4,4,4,4,14],
'J':[7,2,2,2,2,18,12],'K':[17,18,20,24,20,18,17],'L':[16,16,16,16,16,16,31],
'M':[17,27,21,21,17,17,17],'N':[17,25,21,21,19,17,17],'O':[14,17,17,17,17,17,14],
'P':[30,17,17,30,16,16,16],'Q':[14,17,17,17,21,18,13],'R':[30,17,17,30,20,18,17],
'S':[15,16,16,14,1,1,30],'T':[31,4,4,4,4,4,4],'U':[17,17,17,17,17,17,14],
'V':[17,17,17,17,17,10,4],'W':[17,17,17,21,21,27,17],'X':[17,17,10,4,10,17,17],
'Y':[17,17,10,4,4,4,4],'Z':[31,1,2,4,8,16,31],
'0':[14,17,19,21,25,17,14],'1':[4,12,4,4,4,4,14],'2':[14,17,1,2,4,8,31],
'3':[30,1,1,14,1,1,30],'4':[2,6,10,18,31,2,2],'5':[31,16,16,30,1,1,30],
'6':[14,16,16,30,17,17,14],'7':[31,1,2,4,8,8,8],'8':[14,17,17,14,17,17,14],
'9':[14,17,17,15,1,1,14],'+':[0,4,4,31,4,4,0],'-':[0,0,0,31,0,0,0],
'.':[0,0,0,0,0,0,4],'/':[1,1,2,4,8,16,16],'>':[16,8,4,2,4,8,16],' ':[0]*7,
'!':[4,4,4,4,4,0,4],':':[0,4,4,0,4,4,0]}
def label(d, xy, s, fill, scale=1, tracking=1):
    x,y=xy
    for char in s:
        for iy,row in enumerate(GLYPHS[char]):
            for ix in range(5):
                if row & (16>>ix):
                    d.rectangle((x+ix*scale,y+iy*scale,x+(ix+1)*scale-1,y+(iy+1)*scale-1), fill)
        x+=5*scale+tracking

def rgb(col): return tuple(bytes.fromhex(col.lstrip('#')))
def cgb(col):
    r,g,b=rgb(col)
    return (r>>3)|((g>>3)<<5)|((b>>3)<<10)
def emit(name, data, typ='unsigned char'):
    return f'const {typ} {name}[] = {{\n'+''.join('  '+','.join(str(int(v)) for v in data[i:i+20])+',\n' for i in range(0,len(data),20))+'};\n'
def bits(a):
    out=[]
    for row in a:
        for bit in (0,1):
            out.append(sum(((int(p)>>bit)&1)<<(7-i) for i,p in enumerate(row)))
    return bytes(out)
# Colors run from near-black through the lit snow. Two warm colors paint the expedition gear.
# Base at dawn, then morning, noon, afternoon, sunset, twilight and moonlight.
THEMES=[
 ['212741','493e59','77576b','aa6a71','d59588','e8bba7','ffe1bb','fff4bd','d8816d','ffba86'],
 ['183748','2f5164','4b7385','6e9aaf','9ec3c9','c1d8d4','ebe8d1','fff1ba','d99372','f6c28a'],
 ['133245','255169','3c738d','5e9ab8','8ac5d9','b4dbe3','e2eff0','fff4c6','ce906c','efb976'],
 ['19374e','335574','547a9b','78a3bf','a4cad9','c4dbe3','ebf1ef','fff8dc','d18b76','f4b784'],
 ['243450','43536d','696983','928394','b2a6a9','d2c0bb','f1ddd0','ffeead','c57d70','e8a478'],
 ['252340','493552','714761','985b70','bd777d','dda198','f2c4ac','ffe0a0','d37668','efa27c'],
 ['1b203b','2e3455','4a4d75','555a86','736e97','9889a7','bbb9ce','eae4d4','ba7d85','dfa28c'],
 ['11182f','202c4a','334565','475c82','5b7493','8c9db8','c0d1de','edf4df','bb8378','dca389']]
TITLE=['102c38','1c414a','315c61','507c7b','7fa5a0','a9c6af','dce2bb','ffe7a4','d77f59','f5ad63']
def ridge(points, rng, rough):
    line=[]
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        for x in range(x0,x1):
            v=(x-x0)/(x1-x0)
            y=round(y0+(y1-y0)*v+rough*(math.sin(x*.76)*.36+math.sin(x*.39+.5)*.45))
            line.append((x,y))
    return line+[points[-1]]
def landscape(zone, title=False, end=False):
    W=160; H=144 if title else 176
    cols=(THEMES[7] if end else TITLE) if title else THEMES[zone]
    cs=['#'+v for v in cols]
    rng=random.Random(7281+zone*139+(170 if title else 0))
    im=Image.new('RGB',(W,H),cs[4]); d=ImageDraw.Draw(im)
    # Broad bands preserve the print-like color steps of a real four-color tile.
    d.rectangle((0,0,159,H//3),fill=cs[3])
    sky=H//3
    for x in range(0,160,2):
        d.point((x,sky),cs[4])
    sx=(37 if end else 128) if title else [25,42,64,86,108,136,121,94][zone]
    sy=59 if title else [68,49,34,29,43,66,44,33][zone]
    r=13 if title else 11
    d.ellipse((sx-r,sy-r,sx+r,sy+r),cs[7])
    if zone>=6 and not title:
        d.ellipse((sx-r+5,sy-r-2,sx+r+5,sy+r-2),cs[3])
        for _ in range(21):
            x,y=rng.randrange(3,157),rng.randrange(16,53)
            if abs(x-sx)>15:d.point((x,y),cs[7 if rng.randrange(4)==0 else 5])
    else:
        for strip in (6,10):
            d.line((sx-r,sy+strip,sx+r,sy+strip),cs[4])
    for j in range(6):
        x=rng.randrange(-15,153); y=rng.randrange(38,78)
        d.line((x,y,x+rng.randrange(7,29),y),cs[5])
        d.line((x+5,y-1,x+13,y-1),cs[5])
    # Distant silhouettes and individual sunlit snow faces.
    shift=0 if title else (zone*13)%33-16
    base=94 if title else 102+zone*5
    for li,(dy,peak_col,dark_col) in enumerate([(-15,5,4),(0,6,3),(25,4,2)]):
        start=-45; pts=[(start,base+dy)]
        while start<180:
            mid=start+rng.randint(12,25); peak=base+dy-rng.randrange(9,27)
            edge=mid+rng.randint(12,29); pts.extend([(mid,peak),(edge,base+dy+rng.randrange(-7,5))]);start=edge
        profile=ridge(pts,rng,2)
        d.polygon(profile+[(230,H),(-55,H)],fill=cs[dark_col])
        for k in range(1,len(pts)-1,2):
            left,tip,right=pts[k-1:k+2]; x,y=tip; lx,ly=left
            face=ridge([left,tip],rng,2)+[(x-2,y+6),(x+1,y+9),(x-4,y+9),(x-7,y+15),(x-7,y+11),(x-13,y+16),(lx+3,ly)]
            d.polygon(face,fill=cs[peak_col])
    # The massive asymmetric summit has a broken light face and two shadow spurs.
    px=(88 if title else 73+shift); py=(46 if title else [71,58,68,52,64,55,47,43][zone])
    by=(113 if title else 143+zone*3)
    outline=[(px-71,by),(px-51,by-13),(px-43,by-15),(px-31,py+29),(px-23,py+25),(px-15,py+14),(px-10,py+13),(px,py),(px+6,py+7),(px+11,py+9),(px+19,py+22),(px+24,py+23),(px+41,py+45),(px+48,py+44),(px+67,by)]
    d.polygon(ridge(outline,rng,1.5)+[(px+69,H),(px-71,H)],fill=cs[3])
    lit=ridge(outline[:8],rng,1.4)+[(px-2,py+5),(px+1,py+9),(px-5,py+9),(px-3,py+13),(px-7,py+17),(px-7,py+23),(px-13,py+22),(px-20,py+34),(px-22,py+31),(px-32,py+44),(px-36,py+43),(px-54,by-2),(px-68,by)]
    d.polygon(lit,fill=cs[6])
    for dx,dy,ln in [(1,5,15),(9,14,11),(20,27,12),(-12,23,6),(-24,35,6),(34,42,7)]:
        x=px+dx;y=py+dy
        d.polygon([(x,y),(x+3,y+3),(x+ln,y+ln+4),(x+6,y+10),(x+7,y+13),(x+2,y+6)],fill=cs[2 if dx>0 else 4])
    d.polygon([(px,py),(px+2,py+3),(px-6,py+9),(px-4,py+5)],fill=cs[7])
    # A foreground ridge anchors the far peak without creating false flat ledges.
    fy=122 if title else 160
    front=ridge([(-1,fy-9),(22,fy-19),(33,fy-13),(48,fy-10),(65,fy+1),(92,fy+5),(110,fy-2),(129,fy-9),(150,fy-16),(162,fy-13)],rng,2)
    d.polygon(front+[(160,H),(0,H)],fill=cs[1])
    # Landmark silhouettes give each section its own horizon.
    if not title and zone==1:
        for x,y,w in [(0,107,16),(15,118,15),(135,114,14),(149,100,12)]:
            d.polygon([(x-6,H),(x,y+9),(x+4,y),(x+w,y+4),(x+w-1,y+18),(x+w+4,H)],fill=cs[3])
            d.polygon([(x,y+9),(x+4,y),(x+w,y+4),(x+w-5,y+6),(x+1,y+5)],fill=cs[6])
            d.line([(x+4,y+7),(x+3,y+16),(x+6,y+25)],fill=cs[4])
    if not title and zone==2:
        d.polygon([(64,141),(91,135),(81,141),(111,144),(76,151),(108,161),(85,176),(50,176),(76,161),(51,151),(83,146)],fill=cs[4])
        d.line([(80,139),(88,139),(78,142),(101,145),(67,150)],fill=cs[5])
    if not title and zone in (3,4):
        wall=[(126,176),(123,152),(131,138),(129,129),(140,109),(143,95),(153,83),(160,70),(160,176)]
        d.polygon(wall,fill=cs[2])
        for dx,dy in [(134,146),(147,113),(154,95)]:
            d.line([(dx,dy),(dx+4,dy-10),(dx+9,dy-15)],fill=cs[4])
        if zone==4:
            d.polygon([(128,139),(140,132),(146,119),(159,113),(159,119),(148,125),(142,137),(125,147)],fill=cs[8])
            d.line([(136,137),(143,133),(148,123),(157,120)],fill=cs[9])
    if not title and zone==5:
        d.line([(0,123),(21,132),(43,136),(59,138)],fill=cs[1])
        for j,(x,y) in enumerate([(3,125),(13,129),(24,133),(35,135),(46,137)]):
            d.polygon([(x,y),(x+6,y+2),(x+4,y+7),(x,y+5)],fill=cs[[8,5,3,9,4][j]])
    if not title and zone in (6,7):
        for j in range(2 if zone==6 else 4):
            yy=132+j*7
            pts=[(x,yy+int(3*math.sin(x*0.08+j)+2*math.cos(x*.18))) for x in range(-2,164,2)]
            d.polygon(pts+[(162,H),(-2,H)],fill=cs[3 if j%2==0 else 4])
        for j in range(4):
            x=px+4+j*3;y=py-1-j//2
            d.line((x,y,x+9-j,y),fill=cs[5])
    if not title and zone==0:
        # The full-width base is the only unbroken floor on the route.
        d.rectangle((0,152,159,175),cs[1]);d.rectangle((0,152,159,154),cs[6]);d.line((0,155,159,155),cs[3])
        for x in range(1,160,7):
            y=rng.randrange(157,174);d.line((x,y,x+2,y-1),cs[2])
        d.polygon([(6,151),(15,138),(25,151)],fill=cs[8]);d.polygon([(15,139),(16,151),(25,151)],fill=cs[9])
        d.polygon([(14,146),(11,151),(16,151)],fill=cs[0]);d.line((28,150,28,137),cs[1]);d.polygon([(29,137),(37,138),(29,141)],fill=cs[8])
    if title:
        # Original large, scarf-wearing duck on the overlook.
        lay=duck_pixels(0)
        palette={1:cs[0],2:cs[7],3:cs[9],4:cs[8],5:cs[2]}
        left,top=(8,82) if not end else (82,71)
        if end:
            d.polygon([(35,144),(60,119),(69,116),(83,103),(102,101),(116,107),(140,133),(160,144)],fill=cs[1])
            d.polygon([(62,119),(83,102),(101,100),(115,106),(107,107),(101,104),(92,106),(87,105),(76,112)],fill=cs[6])
            d.line((116,107,116,74),fill=cs[0])
            d.polygon([(117,74),(134,76),(138,74),(138,82),(132,84),(117,81)],fill=cs[8])
            d.line([(117,75),(132,77),(136,76)],fill=cs[9])
        else:
            d.polygon([(0,115),(10,110),(35,110),(43,115),(67,120),(0,120)],fill=cs[0])
            d.line([(0,114),(10,109),(34,109),(40,112)],fill=cs[5])
        for y,row in enumerate(lay):
            for x,c in enumerate(row):
                if end and c:d.rectangle((left+2*x,top+2*y,left+2*x+1,top+2*y+1),palette[int(c)])
        d.rectangle((0,0,159,40),cs[0])
        if end:
            label(d,(9,6),'EVEREST EXPEDITION',cs[5])
            label(d,(8,17),'SUMMIT',cs[7],3,2)
        else:
            label(d,(8,5),'CLIMB, DUCKY,',cs[7],2)
            label(d,(47,22),'CLIMB!',cs[9],2)
        # A compact mountain survey mark.
        if end:
            d.line([(139,11),(144,4),(151,12),(139,12)],fill=cs[5])
            d.line([(143,7),(145,8),(146,7)],fill=cs[5])
        d.rectangle((0,120,159,143),cs[0])
    return im,cols
def palettes(cols):
    combos=[[0,1,2,3],[2,3,4,5],[3,4,5,7],[2,3,6,7],[0,2,5,7],[0,2,8,9],[1,3,5,6],[5,0,7,9]]
    return [[cols[i] for i in c] for c in combos]

def compile_scene(name, im, cols, bank):
    pals=palettes(cols); pix=np.array(im).astype('int32')
    pal=np.array([[rgb(c) for c in p] for p in pals],dtype='int32')
    choices={};patterns=[];indices=[];attrs=[]
    for y in range(0,im.height,8):
        for x in range(0,im.width,8):
            a=pix[y:y+8,x:x+8]
            dist=((a[None,:,:,None,:]-pal[:,None,None,:,:])**2).sum(axis=4)
            which=int(dist.min(axis=3).sum(axis=(1,2)).argmin()); packed=bits(dist[which].argmin(axis=2))
            if packed not in choices: choices[packed]=len(patterns);patterns.append(packed)
            idx=choices[packed]
            assert idx<256,(name,idx)
            indices.append(idx if idx<256 else idx-256+128)
            attrs.append(which|(8 if idx<256 else 0))
    def decl(n,vs,t='unsigned char'):return emit(name+n,vs,t)
    code=f'#pragma bank {bank}\n'+decl('_tiles',b''.join(patterns))+decl('_map',indices)+decl('_attr',attrs)+decl('_altmap',[v&127 for v in indices])+decl('_altattr',[a if t<128 else a&7 for t,a in zip(indices,attrs)])+decl('_pals',[cgb(c) for p in pals for c in p],'unsigned short')
    (OUT/(name+'.c')).write_text(code)
    return name,len(patterns),im.height//8,bank
# The scarf overlay has an independent palette. Rotate the head and feet around the body for tumbles.
# Outline refinements from the edited Aseprite tumble frames, in (x, y) order.
TUMBLE_OUTLINE = {
    6: ((2, 6), (14, 6), (13, 8)),
    8: ((9, 2), (2, 6), (4, 8), (7, 13), (9, 14)),
    10: ((9, 2), (7, 4), (2, 7), (1, 9), (13, 9), (3, 11)),
    12: ((6, 0), (8, 2), (6, 13)),
}

def duck_pixels(pose):
    pattern=[
    '................','........0000....','.......0cccc0...','......0cccccc0..',
    '......0cccc0c0..','......0cccccaaa.','.......0cc0aaa..','......rrr0......',
    '..00.0ccrrr.....','.0cc0ccccc0.....','..0ccc00ccc0....','...0ccccc0c0....',
    '....000cccc0....','......00000.....','......a..a......','.....aaa.aaa....']
    a=np.array([[{'.':0,'0':1,'c':2,'a':3,'r':4}[v] for v in row] for row in pattern],dtype='uint8')
    if pose in (1,2):
        a[14:,:]=0
        if pose==1:a[14,5:7]=3;a[15,4:7]=3;a[13,9:11]=3;a[14,10:13]=3
        else:a[14,8:10]=3;a[15,8:11]=3;a[13,4:6]=3;a[14,3:6]=3
    if pose in (3,4):
        a[14:,:]=0;a[13,4:6]=3;a[14,9:12]=3
        img=Image.fromarray(a); dr=ImageDraw.Draw(img)
        if pose==4:
            dr.polygon([(6,10),(3,3),(1,3),(1,7),(4,11)],fill=1);dr.polygon([(5,9),(3,5),(2,4),(2,7)],fill=2)
        else:
            dr.line([(3,8),(6,10),(9,9)],fill=1)
        a=np.array(img)
    if pose>=5:
        a=duck_pixels(4 if pose%2 else 3)
        a=np.array(Image.fromarray(a).rotate(-45*(pose-5),resample=Image.Resampling.NEAREST,center=(8,8)))
    for x, y in TUMBLE_OUTLINE.get(pose, ()):
        a[y, x] = 1
    return a

def title_duck_tiles():
    """Scale the idle body and scarf exactly, preserving the gameplay palette indices."""
    idle = duck_pixels(0)
    body = np.where(idle == 4, 1, idle)
    scarf = np.where(idle[:, 4:12] == 4, 1, 0)
    tiles = []
    for layer in (body, scarf):
        scaled = layer.repeat(2, axis=0).repeat(2, axis=1)
        for y in range(0, 32, 16):
            for x in range(0, scaled.shape[1], 8):
                tiles.extend((bits(scaled[y:y+8, x:x+8]),
                              bits(scaled[y+8:y+16, x:x+8])))
    return tiles

def sprites():
    art=[]; desc={}
    def col(name,a):
        desc[name]=len(art)
        for i in range(0,a.shape[1],8):
            art.append(bits(a[:8,i:i+8]));art.append(bits(a[8:,i:i+8]))
    for i in range(13):
        a=duck_pixels(i)
        # The body gets a solid outline under the scarf. Accessory tile only needs 8x16 twice.
        col('du'+str(i),np.where(a==4,1,a))
        col('sc'+str(i),np.where(a[:,4:12]==4,1,0))
    # Ledge edges use separate tiles so moving ledges have capped ends.
    for kind in ['rock','ice','crack','move','camp','gone']:
        for part in ['l','m','r','alt']:
            p=Image.new('L',(8,16));d=ImageDraw.Draw(p)
            if kind=='gone':
                d.point((1,1),2);d.point((6,1),2)
            else:
                d.polygon([(0,0),(7,0),(7,6),(5,7),(4,10),(2,8),(0,8)],fill=1)
                d.polygon([(0,1),(7,1),(7,4),(4,5),(2,4),(0,5)],fill=2)
                d.line((0,0,7,0),fill=3)
                if part=='l':d.line((0,0,0,1),fill=0);d.line((0,7,0,10),fill=0)
                if part=='r':d.point((7,0),0);d.line((7,6,7,11),fill=0)
                if part=='alt':
                    d.polygon([(0,5),(2,5),(3,7),(6,6),(7,5),(7,9),(5,9),(3,12),(0,10)],fill=1)
                    d.line((1,5,3,6),fill=2)
                if kind=='rock' and part in ('l','r'):
                    d.line((2,3,4,3),fill=3);d.point((5,5),fill=1)
                if kind=='ice':d.polygon([(2,3),(5,3),(3,11)],fill=2);d.line((3,3,3,7),fill=3)
                if kind=='crack':d.line([(4,0),(3,2),(5,3),(3,6)],fill=1)
                if kind=='move':d.line((1,3,6,3),fill=1);d.point((4,5),3)
                if kind=='camp':d.line((0,4,7,4),fill=1);d.point((3,3),3)
            col(kind+part,np.array(p))
    def sym(name,lines):
        a=np.zeros((16,8),dtype='uint8')
        for y,line in enumerate(lines):
            for x,c in enumerate(line):a[y,x]=int(c)
        col(name,a)
    sym('flag',['01111100','01333331','01333210','01332100','01111000','01200000','01200000','01200000','01200000','01200000','01200000','01200000'])
    sym('icicle',['00111100','01233210','01232210','00132100','00132100','00031000','00031000','00010000'])
    sym('warn',['00010000','00030000','00030000','00000000','00030000'])
    sym('gust',['00000000','00000000','00222200','00000320','03333300','00000000','00222000'])
    return art,desc

def main():
    scene_info=[compile_scene('scene'+str(i),*landscape(i),i+1) for i in range(8)]
    scene_info += [compile_scene('cover',*landscape(0,True),9),compile_scene('ending',*landscape(7,True,True),10)]
    hdr='/* Cartridge assets generated by tools/art.py. */\n'
    for name,n,h,b in scene_info:
        hdr+=f'extern const unsigned char {name}_tiles[], {name}_map[], {name}_attr[], {name}_altmap[], {name}_altattr[];\nextern const unsigned short {name}_pals[];\n'
    hdr+='#define SCENE_TABLE { '+', '.join('{%d,%d,%d,%s_tiles,%s_map,%s_attr,%s_altmap,%s_altattr,%s_pals}'%(b,n,h,nm,nm,nm,nm,nm,nm) for nm,n,h,b in scene_info)+' }\n'
    atlas,symbols=sprites()
    # The title duck uses high tiles in bank one, above the backdrop.
    (OUT/'sprites.c').write_text('#pragma bank 11\n'+emit('sprite_tiles',b''.join(atlas)) + emit('title_duck_tiles', b''.join(title_duck_tiles())))
    hdr+='extern const unsigned char title_duck_tiles[];\nextern const unsigned char sprite_tiles[];\n#define SPRITE_COUNT %d\n'%len(atlas)
    for k,v in symbols.items():hdr+='#define TILE_'+k+' '+str(v)+'\n'
    font_order=' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-./>!:'
    ft=[]
    for char in font_order:
        mat=np.ones((8,8),dtype=int)
        for iy,row in enumerate(GLYPHS[char]):
            for ix in range(5):
                if row&(16>>ix):mat[iy,ix+1]=2
        ft.append(bits(mat))
    amber=[]
    for tile in ft:
        buf=bytearray(tile)
        for y in range(8):buf[y*2]=255
        amber.append(bytes(buf))
    (OUT/'font.c').write_text('#pragma bank 11\n'+emit('font_tiles',b''.join(ft+amber)))
    hdr+='extern const unsigned char font_tiles[];\n#define FONT_COUNT '+str(len(ft))+'\n'
    (OUT/'assets.h').write_text(hdr)
    print('scene tiles:',[(nm,n) for nm,n,_,_ in scene_info],'sprite tiles:',len(atlas))
if __name__=='__main__':main()
