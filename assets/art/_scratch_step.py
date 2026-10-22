from PIL import Image
import sys
sys.path.insert(0, 'assets/art')
from gen_chars import PALETTE, SCP173_IDLE

g = [list(r) for r in SCP173_IDLE]
for y in range(2, 19):
    g[y] = list(SCP173_IDLE[y][1:] + '0')

g[19] = list("01mm10mmmmmmmmnn01mm1000")
g[20] = list("0000001mnm0001mnm0000000")
g[21] = list("000001mnm00001mnm0000000")
g[22] = list("00001mm1000001mnm0000000")
g[23] = list("00000000000001mmmm100000")

for y in range(24):
    if len(g[y]) != 24:
        print('bad row', y, len(g[y]), ''.join(g[y]))

img=Image.new('RGBA',(24,24),(0,0,0,0)); px=img.load()
for y in range(24):
    for x in range(24):
        c=PALETTE[g[y][x]]
        if c: px[x,y]=(*c,255)
img.resize((240,240),Image.NEAREST).save('assets/art/_scratch_step.png')
for y in range(24): print('    "%s",'%''.join(g[y]))
