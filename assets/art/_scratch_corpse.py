from PIL import Image
import sys
sys.path.insert(0, 'assets/art')
from gen_chars import PALETTE

W,H=24,16
g=[['0']*W for _ in range(H)]

def run(y,x1,x2,ch):
    for x in range(x1,x2+1):
        g[y][x]=ch

# blood pool
for y,x1,x2 in [(12,2,13),(13,1,15),(14,3,14),(15,4,12)]:
    run(y,x1,x2,'b')
run(13,4,10,'c')
# head: hair cap + broad face
run(3,3,6,'2'); run(4,2,7,'2'); run(4,3,5,'3')
run(5,1,3,'2'); run(5,4,8,'j')
run(6,1,3,'2'); run(6,4,8,'j'); run(6,6,7,'1')
run(7,1,3,'2'); run(7,4,8,'j'); run(7,7,8,'d')
run(8,1,3,'d'); run(8,4,8,'d')
run(9,4,6,'d')
# torso
run(5,8,12,'g'); run(6,8,14,'g'); run(7,8,15,'g'); run(8,8,15,'g')
run(9,9,16,'g'); run(10,11,17,'g'); run(11,13,18,'g')
run(6,10,12,'h'); run(7,11,13,'h'); run(8,12,14,'h')
# bent leg: knee raised above the body, shin down, boot
run(7,15,18,'g'); run(8,15,19,'g'); run(9,15,19,'h')
run(5,18,20,'g'); run(6,18,21,'g'); run(7,18,21,'h')
run(8,20,21,'g'); run(9,20,21,'g'); run(10,20,21,'i')
run(10,20,22,'2'); run(11,20,22,'4')
# second leg behind (darker), boot
run(10,15,19,'i'); run(11,16,20,'g'); run(12,18,21,'i')
run(12,20,22,'2'); run(13,19,22,'4')
# second lower leg
run(12,16,18,'g'); run(13,17,19,'g'); run(14,17,19,'g')
run(14,18,20,'2'); run(15,18,20,'4')
# arm across torso / floor
run(9,9,13,'g'); run(10,11,14,'g'); run(11,13,16,'g'); run(12,15,17,'k')
# upper arm near head
run(8,7,9,'g'); run(7,7,9,'g')

# outline
for y in range(H):
    for x in range(W):
        if g[y][x]!='0':
            continue
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<W and 0<=ny<H and g[ny][nx] not in '01':
                g[y][x]='1'
                break

for y in range(H):
    row=''.join(g[y])
    for ch in row:
        if ch not in PALETTE: print('bad char',ch)
img=Image.new('RGBA',(W,H),(0,0,0,0)); px=img.load()
for y in range(H):
    for x in range(W):
        c=PALETTE[g[y][x]]
        if c: px[x,y]=(*c,255)
img.resize((W*10,H*10),Image.NEAREST).save('assets/art/_scratch_corpse.png')
img.resize((W*4,H*4),Image.NEAREST).save('assets/art/_scratch_corpse_4x.png')
for y in range(H): print('    "%s",'%''.join(g[y]))
