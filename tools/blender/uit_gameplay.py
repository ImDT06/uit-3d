"""
UIT 3D - Du lieu gameplay: ZONE_* (vung kich hoat) + ITEM_* (diem dat vat pham)
Chay lai duoc: tu xoa du lieu cu trong collection Gameplay roi tao lai.
- ZONE_<toa>: empty hinh hop, bao quanh BLD_<toa> + LE (m). Web: dung trong hop = dang o khu vuc BLD_<toa>.
  Co the keo/xoay/scale tay sau khi tao. Them vung moi (vd ZONE_SanBong) thi copy mot hop roi doi ten.
- ITEM_###: empty rai tren loi di, cach toa nha, cach nhau toi thieu MIN_GAP. Custom prop "quest".
"""
import bpy, random
from mathutils import Vector

LE = 6.0          # m, noi rong vung quanh toa
N_ITEMS = 12
MIN_GAP = 28.0
QUEST = "nhat_vat_pham"
SEED = 7
CAMPUS = (-80, 200, -150, 140)   # x0, x1, y0, y1 (Blender) - vung rai vat pham

def get_coll():
    c = bpy.data.collections.get("Gameplay")
    if not c:
        c = bpy.data.collections.new("Gameplay")
        bpy.context.scene.collection.children.link(c)
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    return c

def wbox(o):
    cs = [o.matrix_world @ Vector(b) for b in o.bound_box]
    for ch in o.children_recursive:
        cs += [ch.matrix_world @ Vector(b) for b in ch.bound_box]
    return Vector([min(c[i] for c in cs) for i in range(3)]), Vector([max(c[i] for c in cs) for i in range(3)])

def main():
    c = get_coll()
    blds = [o for o in bpy.data.objects if o.name.startswith("BLD_") and o.parent is None]
    boxes = []
    for b in blds:
        lo, hi = wbox(b)
        boxes.append((lo, hi))
        e = bpy.data.objects.new("ZONE_" + b.name[4:], None)
        e.empty_display_type = "CUBE"
        e.empty_display_size = 1.0
        e.location = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z / 2)
        e.scale = ((hi.x - lo.x) / 2 + LE, (hi.y - lo.y) / 2 + LE, hi.z / 2 + 3)
        e["zone"] = b.name
        c.objects.link(e)

    # diem ngau nhien nam TREN loi di (lay mau trong tam giac), chi trong pham vi truong
    fw = bpy.data.objects["PATH_Footway"]
    mw = fw.matrix_world
    me = fw.data
    me.calc_loop_triangles()
    rnd = random.Random(SEED)
    cands = []
    tris = []
    for tri in me.loop_triangles:
        p = [mw @ me.vertices[i].co for i in tri.vertices]
        tris.append((p, ((p[1] - p[0]).cross(p[2] - p[0])).length / 2))
    weights = [w for _, w in tris]
    for (a, b, cc), _ in rnd.choices(tris, weights=weights, k=3000):
            r1, r2 = rnd.random(), rnd.random()
            if r1 + r2 > 1: r1, r2 = 1 - r1, 1 - r2
            v = a + (b - a) * r1 + (cc - a) * r2
            if not (CAMPUS[0] < v.x < CAMPUS[1] and CAMPUS[2] < v.y < CAMPUS[3]): continue
            if any(lo.x - 4 < v.x < hi.x + 4 and lo.y - 4 < v.y < hi.y + 4 for lo, hi in boxes): continue
            cands.append(v)
    rnd.shuffle(cands)
    picked = []
    for v in cands:
        if all((v - q).length >= MIN_GAP for q in picked):
            picked.append(v)
        if len(picked) >= N_ITEMS: break
    for i, v in enumerate(picked):
        e = bpy.data.objects.new("ITEM_%03d" % i, None)
        e.empty_display_type = "SPHERE"
        e.empty_display_size = 0.6
        e.location = (v.x, v.y, 1.0)
        e["quest"] = QUEST
        c.objects.link(e)
    print("[UIT3D] ZONE:", len(blds), " ITEM:", len(picked), "/", len(cands), "ung vien")

main()
