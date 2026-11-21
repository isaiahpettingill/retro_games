"""Compile the fixed 112-jump route. Each list contains a route across one face."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
routes=[
[50,78,120,101,65,36,54,87,112,136,100,66,38,66],
[103,126,106,69,34,61,99,133,103,73,41,66,100,122],
[92,54,27,64,103,135,106,76,41,68,108,135,102,70],
[33,64,106,135,101,59,25,65,106,135,92,51,27,66],
[108,139,96,56,39,72,115,90,51,26,70,115,89,53],
[93,128,87,47,32,72,114,130,87,45,76,121,86,53],
[92,124,88,50,36,74,112,78,40,80,124,82,42,73],
[114,81,41,85,123,84,48,84,123,81,40,84,123,79]]
kinds=[
'RRRRRRRRRRRRRC','RIIRRIRIIRIRRC','RMIRMMRIMRMIMC','RFIMFRIFMRFIRC',
'IMFRIMFIRMFIMC','IMFIRMFIMFRIMC','MFIMFRIMFIMFIC','MIFMIFMIFMIFMC']
heights=[
[23,25,24,28,25,26,29,26,24,28,29,24,28,28],
[27,26,24,31,27,31,30,28,32,29,30,29,32,30],
[31,33,29,34,30,33,32,34,29,32,34,33,30,33],
[33,35,34,31,35,34,35,32,36,34,35,33,36,34],
[33,35,32,30,27,33,32,36,32,34,33,32,35,34],
[32,35,33,34,35,32,34,47,32,33,34,32,34,35],
[34,35,32,33,36,32,34,35,31,48,35,33,32,36],
[33,35,33,32,36,33,32,33,49,32,33,32,35,36]]
widths=[
[7,7,6,5,6,5,6,5,6,5,5,6,5,6],
[5,6,6,5,5,4,5,5,4,5,4,5,4,6],
[5,4,5,4,4,4,4,5,4,4,4,4,4,6],
[4,4,4,4,4,3,4,4,3,4,4,3,4,6],
[4,4,3,6,6,4,3,4,3,4,4,4,4,6],
[3,4,3,4,3,4,3,4,3,3,4,4,3,6],
[4,4,3,3,3,4,4,3,3,3,4,3,3,6],
[3,4,3,3,3,4,4,3,3,3,4,3,4,6]]
ident={'R':0,'I':1,'F':2,'M':3,'C':4}
rows=[(0,0,20,4,0,0)]; camps=[0];alt=0
for z in range(8):
    for j,cx in enumerate(routes[z]):
        alt+=heights[z][j]; k=ident[kinds[z][j]]; w=widths[z][j]
        x=max(0,min(160-w*8,cx-4*w))
        if k==3:x=max(11,min(149-w*8,x))
        # Icicles guard one edge. The other edge remains available on every landing.
        spikes=(z>=4 and j in ((3,10) if z<6 else (1,5,10)))
        phase=(j*37+z*53)%256
        if z==4 and j==3:
            # The first falling icicle guards the right edge. The exit is to the left.
            phase &= ~1
        elif z==5 and j==3:
            # The next takeoff is on the left. Keep the falling ice on the right.
            phase&=~1
        elif spikes:
            # Leave a clear landing lane on the side the duck approaches from.
            prev=rows[-1]
            approach_x=prev[1]+prev[2]*4
            phase=(phase&~1) | int(approach_x>cx)
        rows.append((alt,x,w,k,phase,int(spikes)))
    camps.append(alt)
txt='/* Generated from the eight hand-set route sheets in tools/course.py. */\n'
txt+='const Ledge route[] = {\n'+''.join('  {'+','.join(map(str,row))+'},\n' for row in rows)+'};\n'
txt+='const int16_t camp_alt[] = {'+','.join(map(str,camps))+'};\n'
(ROOT/'art'/'course.inc').write_text(txt)
print(len(rows)-1,'jumps;',alt,'vertical pixels')

