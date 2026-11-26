"""
UIT 3D - Buoc 5: Lam chi tiet toa nha + trong cay
====================================================
Chay trong uit_blockout.blend (sau uit_fix.py). Chay lai bao nhieu lan cung duoc:
moi lan chay se xoa chi tiet cu va tao lai.

Script nay se:
  1. Them cua so theo tung tang, go ngang o moi san, lan can tren mai cho moi toa BLD_*
  2. Phoi mau: tuong kem, go trang, kinh xanh dam, mai xam
  3. Doi mau mat dat thanh co, loi di mau be tong
  4. Trong cay low-poly tren cac bai co (collection Deco), tranh loi di va toa nha
  5. In so tam giac ra System Console

Cach chay: tab Scripting > Text > Open > chon file nay > bam nut Run Script.
Xong thi chay lai uit_export.py de xuat ra web.
"""

import bpy
import bmesh
import math
import random
from mathutils import Matrix, Vector

# ---------------------------------------------------------------------------
# CAU HINH
# ---------------------------------------------------------------------------
FLOOR_HEIGHT = 3.5
WINDOW_W = 1.6          # m, be rong 1 o cua
WINDOW_GAP = 0.7        # m, khoang cach giua 2 o cua
WINDOW_BOTTOM = 0.9     # m, tinh tu san
WINDOW_H = 1.6
LEDGE_DEPTH = 0.30      # go ngang nho ra khoi tuong
LEDGE_THICK = 0.22
PARAPET_H = 0.9
PARAPET_T = 0.25

TREE_SPACING = 7.0      # m, cay cach nhau toi thieu
TREE_DENSITY = 1 / 90   # cay / m2 bai co
TREE_RADIUS_LIMIT = 300 # m, chi trong cay trong ban kinh nay quanh tam
TREE_SEED = 7

COLORS = {
    "wall":  (0.93, 0.90, 0.83, 1),
    "trim":  (0.98, 0.98, 0.97, 1),
    "glass": (0.20, 0.30, 0.40, 1),
    "roof":  (0.55, 0.55, 0.53, 1),
    "base":  (0.42, 0.58, 0.30, 1),   # co
    "green": (0.36, 0.55, 0.25, 1),
    "footway": (0.80, 0.78, 0.73, 1),
    "road":  (0.28, 0.28, 0.30, 1),
    "pitch": (0.22, 0.52, 0.28, 1),
    "trunk": (0.38, 0.27, 0.18, 1),
    "leaf1": (0.24, 0.50, 0.22, 1),
    "leaf2": (0.32, 0.58, 0.24, 1),
    "leaf3": (0.20, 0.42, 0.20, 1),
    # rieng tung toa (theo anh flycam)
    "a_wall":  (0.95, 0.95, 0.93, 1),   # A: tuong trang
    "a_roof":  (0.80, 0.40, 0.22, 1),   # A: mai cam dat nung
    "a_trim":  (0.30, 0.68, 0.68, 1),   # A: go xanh ngoc
    "a_glass": (0.35, 0.60, 0.75, 1),
    "dome":    (0.20, 0.58, 0.48, 1),   # A: mai vom xanh ngoc
    "e_wall":  (0.80, 0.70, 0.58, 1),   # E: tuong hong/be o hai dau
    "e_glass": (0.32, 0.68, 0.56, 1),   # E: kinh xanh la lien
    "sign":    (0.97, 0.97, 0.97, 1),
    "sign_text": (0.10, 0.20, 0.75, 1),
    "gate":    (0.95, 0.95, 0.92, 1),
    "fence":   (0.55, 0.57, 0.60, 1),
    "planter": (0.82, 0.80, 0.74, 1),
    "bush":    (0.25, 0.55, 0.22, 1),
    "asphalt": (0.30, 0.30, 0.32, 1),
    "b_wall":  (0.62, 0.78, 0.95, 1),   # B: tuong xanh da troi nhat
    "b_glass": (0.22, 0.55, 0.60, 1),   # B: kinh xanh ngoc
    "b_frame": (0.10, 0.33, 0.72, 1),   # B: vien xanh duong quanh dai kinh
    "b_base":  (0.30, 0.62, 0.22, 1),   # B: chan tuong xanh la
    "rail":    (0.42, 0.45, 0.50, 1),   # lan can sat
    "dark":    (0.10, 0.13, 0.17, 1),   # cua so / cua ra vao toi
    "c_wall":  (0.56, 0.78, 0.92, 1),   # C: tuong xanh nhat
    "c_glass": (0.17, 0.25, 0.31, 1),
    "c_brick": (0.70, 0.32, 0.22, 1),   # C: nen gach do sau hoa van sanh
    "c_text":  (0.82, 0.12, 0.14, 1),   # C: chu do ten truong
    "b_groove": (0.80, 0.83, 0.87, 1),  # B: ranh doc tuong hoi
    "b_hood":  (0.62, 0.66, 0.70, 1),   # B: mai che cua so
    "tank":    (0.86, 0.87, 0.89, 1),
    "stair":   (0.22, 0.24, 0.26, 1),   # B: bac cau thang toi o chan khe   # B: bon nuoc inox tren mai
    "plaza":   (0.78, 0.76, 0.72, 1),   # B: bac san be tong
    "plaza_c": (0.86, 0.80, 0.64, 1),   # B: vong tron giua san
    "c_roof":  (0.68, 0.78, 0.70, 1),   # C: mai ton xanh nhat
    "ct_roof": (0.16, 0.45, 0.85, 1),   # can tin: mai ton xanh duong
    "ct_wall": (0.92, 0.90, 0.84, 1),
    "c_court": (0.27, 0.42, 0.24, 1),   # C: san trong (cay)
    "pole":    (0.78, 0.79, 0.80, 1),
    "flag":    (0.86, 0.10, 0.10, 1),
    "star":    (1.00, 0.85, 0.10, 1),
}

# Kieu rieng tung toa. Khong co trong bang -> kieu mac dinh (tuong kem, cua so o vuong).
#   curtain: mat dai (song song truc chinh) la kinh lien thay cho cua so
#   domes:   [(x, y, ban kinh)] toa do the gioi Blender, vom dat tren mai
#   sign:    bang ten tren mai (chu 2 mat)
STYLE = {
    "BLD_A": {"wall": "a_wall", "roof": "a_roof", "trim": "a_trim", "glass": "a_glass",
              "domes": [(1.8, 73.0, 7.0), (-10.0, 26.0, 11.0)]},
    "BLD_B": {"wall": "b_wall", "glass": "b_glass"},
    "BLD_E": {"wall": "e_wall", "glass": "e_glass", "curtain": True,
              "sign": "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN"},
    # C (theo anh tour 360 "San bong"): 3 tang, tuong xanh nhat, khung lam trang chia o (vach dung + o vang
    # moi tang), moi o 2 cua so. Khoi sanh giua mat nam (huong san bong), nho cao hon mai: tang tret duoi
    # de trong co cot + ban cong; phan tren tang tret va tang 2: hang tam giac trang co lo tron tren nen
    # gach do; tang 3 lam dung; diem mai chu do ten truong; cot co truoc sanh.
    "BLD_C": {"wall": "c_wall", "glass": "c_glass", "fins": 3.8,
              "porch": {"at": (47.7, -74.5), "width": 16.0, "depth": 2.6,
                        "sign": "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN"},
              # mai (anh Google Maps): 2 day mai ton xanh nhat song song, san trong hep o giua,
              # khoi giua mai ngoi cam (4 mai), dau dong mai bang. Toa do the gioi, x0..x1 / y0..y1.
              "roofs": [
                  {"kind": "gable", "x": (-24.3, 35.7), "y": (-74.3, -64.0), "h": 2.0, "mat": "c_roof"},
                  {"kind": "gable", "x": (-24.3, 35.7), "y": (-55.0, -44.8), "h": 2.0, "mat": "c_roof"},
                  {"kind": "court", "x": (-24.3, 35.7), "y": (-64.0, -55.0)},
                  {"kind": "gable", "x": (-43.0, -24.3), "y": (-65.9, -53.5), "h": 2.0, "mat": "c_roof"},
                  {"kind": "hip", "x": (35.7, 59.7), "y": (-74.5, -49.0), "h": 4.5, "mat": "a_roof"},
              ]},
    # Can tin (ban banh, nuoc): mai ton xanh duong noi bat (anh Google Maps), 1 tang. Doan chinh mai doc
    # theo chieu dai, doan cuoi thap hon co noc vuong goc.
    "BLD_CanTin2": {"wall": "ct_wall", "roofs": [
        {"kind": "gable", "fit": True, "span": (0.0, 0.62), "h": 2.6, "mat": "ct_roof"},
        {"kind": "gable", "fit": True, "span": (0.62, 1.0), "h": 1.8, "mat": "ct_roof"},
    ]},
}
FIN_DEPTH = 0.7  # m, vach dung / o vang nho ra khoi tuong (kieu "fins")

# Toa nhieu cap mai: chia mat bang theo truc X (tay -> dong) thanh cac doan, moi doan mot so tang.
#   floors: so tang tung doan tu tay sang dong; cuts: vi tri cat theo ti le be ngang (0..1).
#   Ban goc cua toa luu o mesh "<ten>_goc" (fake user) nen chay lai / doi so tang thoai mai.
# B: theo anh flycam + tour 360, dau tay cao 9 tang, giua 7, dau dong 5 (vi tri cat uoc luong).
TIERS = {}

# Toa hinh vong cung dung lai hoan toan (mat bang OSM qua tho, lom lom loi khi cat tang).
# Goc tinh bang do, 0 = huong dong (+X Blender), tang nguoc chieu kim dong ho; a0 -> a1 di qua phia bac.
# floors: so tang tung khoi thap tu a0 (dau dong) sang a1 (dau tay), chia deu theo goc.
# Theo anh Google Maps nhin tu tren: cac khoi thap trang tach nhau boi "khe" lom (cau thang, hanh lang
# co lan can), hai mep khoi canh khe co dai kinh xanh vien xanh duong, chan tuong xanh la, tren mai co
# gian lam xanh duong. Tuong hoi dau tay (huong ve C): mot cot cua so co mai che, lo thong gio, ranh doc.
# San giua: bac ngoi vong cung thap dan ve vong tron o tam (object PLAZA_B, co va cham tren web).
ARC = {
    "BLD_B": {
        "center": (90.0, -12.0), "r_in": 20.0, "r_out": 42.0, "a0": -8.0, "a1": 188.0,
        # Cac doan tu dau dong (a0) sang dau tay (a1): deg = do rong goc, floors = so tang,
        # kind: "out" = khoi nho ra sat san (mat trang, cua so nho, chan xanh la),
        #       "in"  = phan lom vao (ban cong hanh lang chong tang, cot giua).
        # strip: dai kinh xanh o mep mat tien sat khe ("e" mep phia dong / "w" mep phia tay).
        # 6 mai cao thap 4 -> 9 tang (khe giua hep chung mai voi khoi ben canh).
        "segments": [
            # mat nho ra: strip / pairs / louver = vi tri (ti le 0 = mep dong .. 1 = mep tay) cua dai kinh xanh,
            # cot cap o vuong nho, cot cua so co mai che la sach; con lai la tuong tron (theo anh Google Maps)
            {"deg": 24, "floors": 4, "kind": "out", "strip": 0.88, "pairs": [0.62, 0.42], "pergola": True, "tank": True,
             "ac": True},
            {"deg": 11, "floors": 4, "kind": "in", "pillar": False},   # khe: nua dong 4 tang | nua tay 5 tang,
            {"deg": 11, "floors": 5, "kind": "in", "pillar": False},   #      chung 1 cot o ranh gioi
            {"deg": 24, "floors": 5, "kind": "out", "pairs": [0.5], "pergola": True, "tank": True},
            {"deg": 7, "floors": 6, "kind": "out", "strip": 0.5},     # khoi 6 tang: tru hep co dai kinh phia dong
            {"deg": 17, "floors": 6, "kind": "in", "pergola": True},  #            + khe co cot ghi chu "B" phia tay
            {"deg": 34, "floors": 7, "kind": "out", "strip": 0.61, "louver": [0.84], "pergola": True},
            {"deg": 12, "floors": 8, "kind": "out", "pairs": [0.5]},   # tru 8 tang nho ra canh khoi 7
            {"deg": 22, "floors": 8, "kind": "in", "pergola": True, "tank": True},
            {"deg": 34, "floors": 9, "kind": "out", "strip": 0.12, "pairs": [0.34], "tank": True},
        ],
        "recess": 7.0,       # m, do sau phan lom
        "plaza": {"circle_r": 5.5, "step_r0": 7.0, "step_w": 1.6, "steps": 5, "step_h": 0.12},
    },
}

# Cong chinh: pos = giua cong (x, y), dir = huong di vao truong, width = be rong duong vao.
# Doan duong vao co dai bon cay o giua dai median_len (m).
GATE = {"pos": (-71.2, 12.5), "dir": (20.0, -7.0), "width": 10.0, "median_len": 16.0, "fence_len": 3.0}

# Cong sau: duong noi bo di qua can tin (mai xanh) xuong phia nam, ra duong ven xa lo Ha Noi.
# pos = giua cong, dir = huong di vao truong, width = be rong loi di; bot bao ve ben phai khi di ra.
BACK_GATE = {"pos": (118.5, -132.5), "dir": (-0.64, 0.77), "width": 8.0, "fence_len": 10.0}


def log(msg):
    print("[UIT3D] " + msg, flush=True)


def mat(key, rough=0.85, metal=0.0):
    name = "MAT_" + key
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = COLORS[key]
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = COLORS[key]
    return m


def get_collection(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


# ---------------------------------------------------------------------------
# Hinh hoc phu tro
# ---------------------------------------------------------------------------
def add_box(bm, p0, p1, n, z0, z1, d0, d1):
    """Hop chay doc canh p0->p1, nho ra theo phap tuyen n tu d0 den d1, cao z0..z1."""
    a = Vector((p0.x, p0.y, 0))
    b = Vector((p1.x, p1.y, 0))
    nn = Vector((n.x, n.y, 0))
    pts = [a + nn * d0, b + nn * d0, b + nn * d1, a + nn * d1]
    bot = [bm.verts.new((p.x, p.y, z0)) for p in pts]
    top = [bm.verts.new((p.x, p.y, z1)) for p in pts]
    faces = [bot[::-1], top]
    for i in range(4):
        j = (i + 1) % 4
        faces.append((bot[i], bot[j], top[j], top[i]))
    for f in faces:
        try:
            bm.faces.new(f)
        except ValueError:
            pass


def add_quad(bm, p0, p1, n, z0, z1, d):
    """Tam phang dung (cua so) song song tuong, cach tuong d."""
    a = Vector((p0.x + n.x * d, p0.y + n.y * d))
    b = Vector((p1.x + n.x * d, p1.y + n.y * d))
    v = [bm.verts.new((a.x, a.y, z0)), bm.verts.new((b.x, b.y, z0)),
         bm.verts.new((b.x, b.y, z1)), bm.verts.new((a.x, a.y, z1))]
    try:
        bm.faces.new(v)
    except ValueError:
        pass


def footprint(obj):
    """Lay duong vien mai (nguoc chieu kim dong ho) va do cao day/mai."""
    me = obj.data
    zs = [v.co.z for v in me.vertices]
    zmin, zmax = min(zs), max(zs)
    tops = [p for p in me.polygons if p.normal.z > 0.9 and p.center.z > zmax - 0.01]
    if not tops:
        return None
    top = max(tops, key=lambda p: p.area)
    mw = obj.matrix_world
    pts = [(mw @ me.vertices[i].co) for i in top.vertices]
    ring = [Vector((p.x, p.y)) for p in pts]
    area = 0
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        area += a.x * b.y - b.x * a.y
    if area < 0:
        ring.reverse()
    return ring, zmin, zmax, top.index


# ---------------------------------------------------------------------------
# 1. Chi tiet toa nha
# ---------------------------------------------------------------------------
def clear_old():
    for o in list(bpy.data.objects):
        if o.name.startswith(("DET_", "TREE_", "GATE_", "PLAZA_")):
            bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def clip_x(ring, lo, hi):
    """Cat da giac (Sutherland-Hodgman) giu phan lo <= x <= hi."""
    def clip(pts, inside, cross):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(cross(a, b))
                out.append(b)
            elif ia:
                out.append(cross(a, b))
        return out

    def at_x(x):
        return lambda a, b: a.lerp(b, (x - a.x) / (b.x - a.x))

    pts = clip(ring, lambda v: v.x >= lo, at_x(lo))
    return clip(pts, lambda v: v.x <= hi, at_x(hi)) if pts else []


def apply_tiers(obj):
    """Dung lai khoi toa thanh nhieu khoi cao thap khac nhau theo TIERS (tu ban goc)."""
    cfg = TIERS.get(obj.name)
    if not cfg:
        return
    orig = bpy.data.meshes.get(obj.name + "_goc")
    if orig is None:
        orig = obj.data.copy()
        orig.name = obj.name + "_goc"
        orig.use_fake_user = True
    mw = obj.matrix_world
    zmin = min((mw @ v.co).z for v in orig.vertices)
    bottom = max((p for p in orig.polygons if p.normal.z < -0.9), key=lambda p: p.area)
    ring = [(mw @ orig.vertices[i].co).to_2d() for i in bottom.vertices]
    area = sum(ring[i - 1].x * ring[i].y - ring[i].x * ring[i - 1].y for i in range(len(ring)))
    if area < 0:
        ring.reverse()  # nguoc chieu kim dong ho -> mat tren huong len
    x0, x1 = min(p.x for p in ring), max(p.x for p in ring)
    xs = [x0 - 1] + [x0 + (x1 - x0) * c for c in cfg["cuts"]] + [x1 + 1]
    inv = mw.inverted()
    bm = bmesh.new()
    for i, floors in enumerate(cfg["floors"]):
        poly = clip_x(ring, xs[i], xs[i + 1])
        if len(poly) < 3:
            continue
        z1 = zmin + floors * FLOOR_HEIGHT + 1.0
        vb = [bm.verts.new(inv @ Vector((q.x, q.y, zmin))) for q in poly]
        vt = [bm.verts.new(inv @ Vector((q.x, q.y, z1))) for q in poly]
        bm.faces.new(vb[::-1])
        bm.faces.new(vt)
        for j in range(len(poly)):
            bm.faces.new((vb[j], vb[(j + 1) % len(poly)], vt[(j + 1) % len(poly)], vt[j]))
    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    log(f"   {obj.name}: {len(cfg['floors'])} cap mai {cfg['floors']} tang")


def roof_parts(obj):
    """Cac mat mai (huong len, cao hon day) -> [(ring CCW the gioi 2D, z mai, chi so mat, dien tich)]."""
    me = obj.data
    mw = obj.matrix_world
    zmin = min((mw @ v.co).z for v in me.vertices)
    parts = []
    for p in me.polygons:
        if p.normal.z > 0.9 and (mw @ p.center).z > zmin + 1.0:
            ring = [(mw @ me.vertices[i].co).to_2d() for i in p.vertices]
            area = sum(ring[i - 1].x * ring[i].y - ring[i].x * ring[i - 1].y for i in range(len(ring)))
            if area < 0:
                ring.reverse()
            parts.append((ring, (mw @ p.center).z, p.index, abs(area) / 2))
    return parts, zmin


def on_segment(m, a, b, tol=0.05):
    ab = b - a
    L2 = ab.length_squared
    if L2 < 1e-9:
        return False
    t = (m - a).dot(ab) / L2
    return -0.01 <= t <= 1.01 and (a + ab * t - m).length < tol


def arc_ring(c, r1, r2, a0, a1, seg):
    """Da giac vanh khan (nguoc chieu kim dong ho): cung ngoai a0->a1 roi cung trong a1->a0."""
    angs = [math.radians(a0 + (a1 - a0) * i / seg) for i in range(seg + 1)]
    outer = [Vector((c.x + r2 * math.cos(a), c.y + r2 * math.sin(a))) for a in angs]
    inner = [Vector((c.x + r1 * math.cos(a), c.y + r1 * math.sin(a))) for a in reversed(angs)]
    return outer + inner


def prism(bm, ring, z0, z1, mi=0, inv=None):
    """Lang tru dung tu da giac 2D (CCW). mi: chi so vat lieu; inv: doi toa do the gioi -> object."""
    T = (lambda v: inv @ v) if inv else (lambda v: v)
    vb = [bm.verts.new(T(Vector((q.x, q.y, z0)))) for q in ring]
    vt = [bm.verts.new(T(Vector((q.x, q.y, z1)))) for q in ring]
    fs = [bm.faces.new(vb[::-1]), bm.faces.new(vt)]
    n = len(ring)
    for j in range(n):
        fs.append(bm.faces.new((vb[j], vb[(j + 1) % n], vt[(j + 1) % n], vt[j])))
    for f in fs:
        f.material_index = mi
    fs[1].material_index = mi if mi else 1  # mat tren: mai (than toa) hoac cung vat lieu (chi tiet)
    return fs


def pergola(bm, c, r0, r1, g0, g1, z):
    """Gian lam tren mai: 4 cot goc, 2 dam cong, cac thanh huong tam cach ~1 m."""
    hp, t = 2.6, 0.18
    pt = lambda a, r: Vector((c.x + r * math.cos(math.radians(a)), c.y + r * math.sin(math.radians(a))))
    for a in (g0, g1):
        for r in (r0, r1):
            p = pt(a, r)
            prism(bm, [p + Vector((-t, -t)), p + Vector((t, -t)), p + Vector((t, t)), p + Vector((-t, t))], z, z + hp, 0)
    for r in (r0, r1):
        prism(bm, arc_ring(c, r - t, r + t, g0, g1, 4), z + hp - 0.3, z + hp, 0)
    cnt = max(2, int(math.radians(g1 - g0) * (r0 + r1) / 2 // 1.0))
    for j in range(cnt + 1):
        rad = math.radians(g0 + (g1 - g0) * j / cnt)
        d = Vector((math.cos(rad), math.sin(rad)))
        tg = Vector((-d.y, d.x)) * 0.08
        p0, p1 = c + d * (r0 - 0.5), c + d * (r1 + 0.5)
        prism(bm, [p0 - tg, p1 - tg, p1 + tg, p0 + tg], z + hp, z + hp + 0.22, 0)


def build_plaza(name, cfg):
    """San bac ngoi vong cung trong long toa, thap dan ve vong tron o tam. Object rieng (co va cham)."""
    p = cfg["plaza"]
    c = Vector(cfg["center"])
    zb = 0.2  # cao hon co / loi di mot chut
    bm = bmesh.new()
    ring = [c + Vector((math.cos(math.tau * i / 32), math.sin(math.tau * i / 32))) * p["circle_r"] for i in range(32)]
    for f in prism(bm, ring, 0.0, zb, 1):
        f.material_index = 1
    for k in range(p["steps"]):
        r0 = p["step_r0"] + k * p["step_w"]
        r1 = r0 + p["step_w"] if k < p["steps"] - 1 else cfg["r_in"] + cfg["recess"]  # bac tren cung lan toi chan toa
        for f in prism(bm, arc_ring(c, r0, r1, cfg["a0"], cfg["a1"], 48), 0.0, zb + p["step_h"] * (k + 1), 0):
            f.material_index = 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat("plaza", 0.9))
    me.materials.append(mat("plaza_c", 0.9))
    o = bpy.data.objects.new(name, me)
    get_collection("Props").objects.link(o)
    return sum(len(q.vertices) - 2 for q in me.polygons)


def arc_building(obj, coll):
    cfg = ARC[obj.name]
    if not bpy.data.meshes.get(obj.name + "_goc"):
        keep = obj.data.copy()
        keep.name = obj.name + "_goc"
        keep.use_fake_user = True  # giu mat bang OSM goc de tham chieu
    c = Vector(cfg["center"])
    r_in, r_out, rec = cfg["r_in"], cfg["r_out"], cfg["recess"]
    a0, a1 = cfg["a0"], cfg["a1"]
    mw = obj.matrix_world
    inv = mw.inverted()
    zmin = min((mw @ v.co).z for v in obj.data.vertices)
    FH = FLOOR_HEIGHT
    H = lambda f: f * FH + 1.0
    deg = lambda m, r: math.degrees(m / r)  # do dai cung -> goc
    scale = (a1 - a0) / sum(s["deg"] for s in cfg["segments"])
    segs, a = [], a0
    for s in cfg["segments"]:
        segs.append((a, a + s["deg"] * scale, s))
        a += s["deg"] * scale
    nseg = lambda lo, hi: max(3, int((hi - lo) / 4))
    front = lambda s: r_in if s["kind"] == "out" else r_in + rec
    top = lambda s: zmin + H(s["floors"])

    # --- than toa (co va cham tren web)
    bm = bmesh.new()
    for lo, hi, s in segs:
        prism(bm, arc_ring(c, front(s), r_out, lo, hi, nseg(lo, hi)), zmin, top(s), 0, inv)
    bm.normal_update()
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    style = STYLE.get(obj.name, {})
    me = obj.data
    me.materials.clear()
    me.materials.append(mat(style.get("wall", "wall"), 0.9))
    me.materials.append(mat(style.get("roof", "roof"), 0.95))

    # --- chi tiet: moi vat lieu mot bmesh
    parts = {}

    def B(key):
        if key not in parts:
            parts[key] = bmesh.new()
        return parts[key]

    radial = lambda a, r: Vector((c.x + r * math.cos(math.radians(a)), c.y + r * math.sin(math.radians(a))))

    def chord_quad(key, a, r, half_w, z0, z1):
        """Tam phang dung tiep tuyen voi cung tai goc a, ban kinh r, quay vao tam (mat trong)."""
        rad = math.radians(a)
        t = Vector((-math.sin(rad), math.cos(rad)))
        p = radial(a, r)
        add_quad(B(key), p + t * half_w, p - t * half_w, Vector((-math.cos(rad), -math.sin(rad))), z0, z1, 0.0)

    def wall_quad(key, a, r0, r1, nrm, z0, z1, d):
        """Tam phang tren tuong huong tam (tuong ben) tai goc a, tu ban kinh r0 den r1."""
        add_quad(B(key), radial(a, r0), radial(a, r1), nrm, z0, z1, d)

    for lo, hi, s in segs:
        T, f, r0 = top(s), s["floors"], front(s)
        mid = (lo + hi) / 2
        if s["kind"] == "out":
            # mat nho ra sat san: chan xanh la, dai kinh, cot cua so theo cau hinh
            prism(B("b_base"), arc_ring(c, r_in - 0.06, r_in + 0.01, lo, hi, nseg(lo, hi)), zmin, zmin + 1.6, 0)
            fw = lambda fr: lo + (hi - lo) * fr  # ti le -> goc
            if "strip" in s:
                sa = fw(s["strip"])
                prism(B("b_frame"), arc_ring(c, r_in - 0.12, r_in + 0.01, sa - deg(0.95, r_in), sa + deg(0.95, r_in), 2),
                      zmin + 1.6, T - 0.8, 0)
                chord_quad("b_glass", sa, r_in - 0.14, 0.7, zmin + 1.8, T - 1.0)
            for fr in s.get("pairs", []):          # cap o vuong nho moi tang
                ap = fw(fr)
                for k in range(1, f):
                    z = zmin + k * FH + 1.4
                    for dd in (-0.4, 0.4):
                        chord_quad("dark", ap + deg(dd, r_in), r_in - 0.03, 0.22, z, z + 0.45)
            for fr in s.get("louver", []):         # cua so co mai che la sach
                al, hw = fw(fr), deg(0.9, r_in)
                for k in range(1, f):
                    z = zmin + k * FH + 1.0
                    chord_quad("dark", al, r_in - 0.03, 0.75, z, z + 1.0)
                    prism(B("b_hood"), arc_ring(c, r_in - 0.35, r_in, al - hw, al + hw, 1), z + 1.05, z + 1.6, 0)
        else:
            # phan lom vao: ban cong hanh lang chong tang, cot giua, cua toi phia trong
            for k in range(1, f + 1):
                z = zmin + k * FH + (1.0 if k == f else 0)
                prism(B("trim"), arc_ring(c, r0 - 2.2, r0, lo, hi, nseg(lo, hi)), z - 0.3, z, 0)
                prism(B("rail"), arc_ring(c, r0 - 2.2, r0 - 2.12, lo, hi, nseg(lo, hi)), z, z + 1.0, 0)
            if s.get("pillar", True):
                prism(B("trim"), arc_ring(c, r0 - 2.3, r0 - 1.6, mid - deg(0.4, r0), mid + deg(0.4, r0), 1), zmin, T, 0)
            # cau thang toi o chan khe (soc bac tren mat san)
            zs = 0.2 + cfg["plaza"]["step_h"] * cfg["plaza"]["steps"] + 0.01 if cfg.get("plaza") else zmin + 0.01
            r = r_in + 0.3
            while r < r0 - 2.4:
                prism(B("stair"), arc_ring(c, r, r + 0.35, lo + deg(0.3, r), hi - deg(0.3, r), nseg(lo, hi)), zs, zs + 0.02, 0)
                r += 0.7
            for k in range(f):
                z = zmin + k * FH
                for q in (0.25, 0.75):
                    chord_quad("dark", lo + (hi - lo) * q, r0 - 0.03, math.radians(hi - lo) * r0 * 0.12, z + 0.3, z + 2.6)
            prism(B("b_base"), arc_ring(c, r0 - 0.06, r0 + 0.02, lo, hi, nseg(lo, hi)), zmin, zmin + 1.6, 0)
        # lan can mai + gian lam + bon nuoc
        prism(B("rail"), arc_ring(c, r0, r0 + 0.1, lo, hi, nseg(lo, hi)), T, T + 1.0, 0)
        prism(B("rail"), arc_ring(c, r_out - 0.1, r_out, lo, hi, nseg(lo, hi)), T, T + 1.0, 0)
        # gian lam: nua sau san thuong (phia mat ngoai), giua doan; bon nuoc + dan may lanh: nua truoc
        if s.get("pergola"):
            rp = r_out - 5.0
            hw = min(deg(5.0, rp), (hi - lo) / 2 - deg(1.2, rp))
            pergola(B("b_frame"), c, r_out - 8.0, r_out - 2.0, mid - hw, mid + hw, T)
        if s.get("tank"):
            at = mid + deg(2.0, r0 + 3.5) if s.get("ac") else mid  # co dan may lanh: bon nuoc lech sang tay
            p = radial(at, r0 + 3.5)
            ang = math.radians(at) + math.pi / 2
            bmesh.ops.create_cone(B("tank"), cap_ends=True, segments=12, radius1=0.7, radius2=0.7, depth=3.2,
                                  matrix=Matrix.Translation((p.x, p.y, T + 1.1)) @ Matrix.Rotation(ang, 4, "Z")
                                  @ Matrix.Rotation(math.pi / 2, 4, "Y"))
        if s.get("ac"):
            for j in range(5):
                ap = mid - deg(0.4 + j * 1.1, r0 + 3.5)  # hang may lanh phia dong bon nuoc
                prism(B("tank"), arc_ring(c, r0 + 3.0, r0 + 4.0, ap - deg(0.45, r0 + 3.5), ap + deg(0.45, r0 + 3.5), 1),
                      T, T + 0.9, 0)
        # mat ngoai: cua so theo tang, chan xanh la
        n_o = nseg(lo, hi)
        outer = arc_ring(c, r0, r_out, lo, hi, n_o)[: n_o + 1]
        for j in range(n_o):
            p0, p1 = outer[j], outer[j + 1]
            e = p1 - p0
            L = e.length
            t = e / L
            nn = Vector((t.y, -t.x))
            cnt = int((L - 0.8 + WINDOW_GAP) // (WINDOW_W + WINDOW_GAP))
            st = (L - (cnt * WINDOW_W + (cnt - 1) * WINDOW_GAP)) / 2
            for k in range(f):
                z0 = zmin + k * FH + WINDOW_BOTTOM
                for w in range(cnt):
                    sx = st + w * (WINDOW_W + WINDOW_GAP)
                    add_quad(B("dark"), p0 + t * sx, p0 + t * (sx + WINDOW_W), nn, z0, z0 + WINDOW_H, 0.04)
            prism(B("b_base"), [p0 + nn * 0.06 - t * 0.05, p1 + nn * 0.06 + t * 0.05, p1 - nn * 0.02 + t * 0.05,
                                p0 - nn * 0.02 - t * 0.05], zmin, zmin + 0.8, 0)

    def end_wall(a, nrm, f):
        """Tuong hoi dau vong cung (theo anh mat B huong ve C): cot cua so co mai che, lo thong gio, ranh doc."""
        p0, p1 = radial(a, r_in), radial(a, r_out)
        e = p1 - p0
        L = e.length
        t = e / L
        sw_ = L * 0.42
        for k in range(f):
            z = zmin + k * FH
            add_quad(B("dark"), p0 + t * (sw_ - 1.3), p0 + t * (sw_ + 1.3), nrm, z + 1.0, z + 2.4, 0.04)
            add_box(B("b_hood"), p0 + t * (sw_ - 1.45), p0 + t * (sw_ + 1.45), nrm, z + 2.45, z + 2.85, -0.01, 0.45)
            for off, dz in ((3.2, 1.0), (3.9, 1.0), (5.6, 2.1)):
                s_ = sw_ + off
                add_quad(B("dark"), p0 + t * (s_ - 0.2), p0 + t * (s_ + 0.2), nrm, z + dz, z + dz + 0.4, 0.04)
        for off in (3.55, 5.0):
            s_ = sw_ + off
            add_quad(B("b_groove"), p0 + t * (s_ - 0.25), p0 + t * (s_ + 0.25), nrm, zmin + FH, zmin + H(f) - 2.0, 0.02)

    # tuong ben o ranh gioi cac doan: phan khoi nay lo ra so voi khoi ben canh
    bounds = [segs[0][0]] + [hi for _, hi, _ in segs]
    for i, b in enumerate(bounds):
        rad = math.radians(b)
        tg = Vector((-math.sin(rad), math.cos(rad)))  # huong goc tang (sang tay)
        A = segs[i - 1][2] if i > 0 else None         # doan phia dong cua ranh gioi
        Bs = segs[i][2] if i < len(segs) else None    # doan phia tay
        if A is None or Bs is None:
            s = A or Bs
            end_wall(b, tg if Bs is None else -tg, s["floors"])
            continue
        if A["kind"] == "in" and Bs["kind"] == "in":
            # hai phan lom lien nhau: cot chung o ranh gioi, cao bang phan cao hon
            rp = r_in + rec
            prism(B("trim"), arc_ring(c, rp - 2.3, rp - 1.6, b - deg(0.4, rp), b + deg(0.4, rp), 1),
                  zmin, max(top(A), top(Bs)), 0)
        for S, O, nrm, side in ((A, Bs, tg, "w"), (Bs, A, -tg, "e")):
            fS, fO = front(S), front(O)
            if fS < fO - 0.1:
                # S nho ra hon O: tuong ben quay vao khe, lo ra tu chan len mai
                rm = (fS + fO) / 2
                for k in range(1, S["floors"]):
                    z = zmin + k * FH + 1.2
                    wall_quad("dark", b, rm - 0.35, rm + 0.35, nrm, z, z + 0.8, 0.03)
                wall_quad("b_base", b, fS, fO, nrm, zmin, zmin + 1.6, 0.02)
            if top(S) > top(O) + 0.1:
                # phan cao hon mai khoi ben canh: cua so theo tang + lan can mep mai thap
                rr = max(fS, fO)
                p0, p1 = radial(b, rr), radial(b, r_out)
                e = p1 - p0
                L = e.length
                t = e / L
                cnt = int((L - 0.8 + WINDOW_GAP) // (WINDOW_W + WINDOW_GAP))
                st = (L - (cnt * WINDOW_W + (cnt - 1) * WINDOW_GAP)) / 2
                for k in range(O["floors"], S["floors"]):
                    z0 = zmin + k * FH + WINDOW_BOTTOM
                    for w in range(cnt):
                        sx = st + w * (WINDOW_W + WINDOW_GAP)
                        add_quad(B("dark"), p0 + t * sx, p0 + t * (sx + WINDOW_W), nrm, z0, z0 + WINDOW_H, 0.04)
                d = nrm * 0.05
                zl = top(O)
                prism(B("rail"), [p0 + d, p1 + d, p1 + d * 3, p0 + d * 3], zl, zl + 1.0, 0)

    tris = 0
    names = {"b_glass": "glass", "dark": "win_glass", "b_groove": "groove_decal", "stair": "stair_decal"}  # *_glass/_decal: web khong do bong
    for key, bmx in parts.items():
        dme = bpy.data.meshes.new("DET_" + obj.name[4:] + "_" + names.get(key, key))
        bmesh.ops.recalc_face_normals(bmx, faces=bmx.faces)
        bmx.normal_update()
        bmx.to_mesh(dme)
        bmx.free()
        rough = 0.15 if key in ("b_glass", "dark") else (0.4 if key == "tank" else 0.8)
        dme.materials.append(mat(key, rough, 0.3 if key in ("b_glass", "tank") else 0.0))
        tris += attach(obj, coll, dme.name, dme)
    if cfg.get("plaza"):
        tris += build_plaza("PLAZA_" + obj.name[4:], cfg)
    log(f"   {obj.name}: vong cung {len(segs)} doan, so tang {[s['floors'] for _, _, s in segs]}")
    return tris


def detail_building(obj, coll):
    if obj.name in ARC:
        return arc_building(obj, coll)
    apply_tiers(obj)
    parts, zmin = roof_parts(obj)
    if not parts:
        return 0
    main = max(parts, key=lambda q: q[3])  # khoi lon nhat: dung cho vom, bang ten, truc chinh
    ring, zmax = main[0], main[1]

    style = STYLE.get(obj.name, {})
    k_wall, k_roof = style.get("wall", "wall"), style.get("roof", "roof")
    k_trim, k_glass = style.get("trim", "trim"), style.get("glass", "glass")
    curtain = style.get("curtain", False)
    # truc chinh = huong canh dai nhat
    axis = max(((ring[(i + 1) % len(ring)] - ring[i]) for i in range(len(ring))), key=lambda v: v.length).normalized()

    # tuong + mai cua khoi goc
    me = obj.data
    me.materials.clear()
    me.materials.append(mat(k_wall, 0.9))
    me.materials.append(mat(k_roof, 0.95))
    roofs = {q[2] for q in parts}
    for p in me.polygons:
        p.material_index = 1 if p.index in roofs else 0

    fins = style.get("fins")
    # khoi sanh: tim canh mai chinh gan diem "at" nhat, phan tuong sau sanh khong lam cua so / lam
    porch, pinfo = style.get("porch"), None
    if porch:
        at = Vector(porch["at"])
        j = min(range(len(ring)), key=lambda j: seg_dist(at, ring[j], ring[(j + 1) % len(ring)]))
        a = ring[j]
        tt = (ring[(j + 1) % len(ring)] - a).normalized()
        s = (at - a).dot(tt)
        pinfo = {"edge": j, "gap": (s - porch["width"] / 2, s + porch["width"] / 2),
                 "c": a + tt * s, "t": tt, "n": Vector((tt.y, -tt.x))}

    bm_trim, bm_glass = bmesh.new(), bmesh.new()
    for pring, ptop, _, _ in parts:
        height = ptop - zmin
        floors = max(1, int(round((height - 1.0) / FLOOR_HEIGHT)))
        fh = (height - 1.0) / floors if height > 2 else height
        n_edges = len(pring)
        for i in range(n_edges):
            p0, p1 = pring[i], pring[(i + 1) % n_edges]
            e = p1 - p0
            L = e.length
            if L < 0.5:
                continue
            t = e / L
            n = Vector((t.y, -t.x))  # phap tuyen huong ra ngoai (vong nguoc chieu kim dong ho)
            gap = pinfo["gap"] if pinfo and pring is ring and i == pinfo["edge"] else None
            runs = [(0.0, L)] if not gap else [r for r in ((0.0, gap[0]), (gap[1], L)) if r[1] - r[0] > 0.2]
            # canh tiep giap khoi khac: phan tuong thap hon mai khoi do bi che, chi lam tu do tro len
            mid = (p0 + p1) / 2
            covered = zmin
            for oring, otop, _, _ in parts:
                if oring is pring:
                    continue
                if any(on_segment(mid, oring[j], oring[(j + 1) % len(oring)]) for j in range(len(oring))):
                    covered = max(covered, otop)
            if covered >= ptop - 0.01:
                continue  # tuong nay nam han ben trong khoi cao hon

            # go ngang o moi san (kieu fins: o vang sau) + lan can mai
            use_fins = fins and L >= 3
            depth = FIN_DEPTH if use_fins else LEDGE_DEPTH
            for k in range(1, floors + 1):
                z = zmin + k * fh
                if k == floors:
                    z = ptop
                if z > covered + 0.3:
                    for u0, u1 in runs:
                        add_box(bm_trim, p0 + t * (u0 - (0.15 if u0 <= 0 else 0)), p0 + t * (u1 + (0.15 if u1 >= L else 0)),
                                n, z - LEDGE_THICK, z, -0.01, depth)
            add_box(bm_trim, p0, p1, n, ptop, ptop + PARAPET_H, -PARAPET_T, 0.02)

            # kinh lien (mat song song truc chinh)
            if curtain and abs(t.dot(axis)) > 0.9 and L > 3:
                add_quad(bm_glass, p0, p1, n, max(zmin + 0.6, covered), ptop - 0.25, 0.05)
                continue

            # khung lam: vach dung chia o deu ~fins m, moi o 2 cua so cao gan het tang
            if use_fins:
                nb = max(1, round(L / fins))
                bw = L / nb
                zf = max(zmin, covered)
                in_gap = lambda s0, s1: gap and s0 < gap[1] and s1 > gap[0]
                for j in range(nb + 1):
                    s = j * bw
                    if not in_gap(s - 0.15, s + 0.15):
                        add_box(bm_trim, p0 + t * (s - 0.15), p0 + t * (s + 0.15), n, zf, ptop, -0.01, depth)
                ww = (bw - 0.3 - 0.7 - 0.25) / 2
                for j in range(nb):
                    if ww < 0.5 or in_gap(j * bw, (j + 1) * bw):
                        continue
                    for k in range(floors):
                        z0 = zmin + k * fh + WINDOW_BOTTOM
                        z1 = zmin + (k + 1) * fh - LEDGE_THICK - 0.25
                        if z0 < covered:
                            continue
                        for s in (j * bw + 0.5, j * bw + 0.5 + ww + 0.25):
                            add_quad(bm_glass, p0 + t * s, p0 + t * (s + ww), n, z0, z1, 0.04)
                continue

            # cua so
            usable = L - 0.8
            count = int((usable + WINDOW_GAP) // (WINDOW_W + WINDOW_GAP))
            if count < 1:
                continue
            span = count * WINDOW_W + (count - 1) * WINDOW_GAP
            start = (L - span) / 2
            for k in range(floors):
                z0 = zmin + k * fh + WINDOW_BOTTOM
                z1 = min(z0 + WINDOW_H, zmin + (k + 1) * fh - LEDGE_THICK - 0.15)
                if z1 - z0 < 0.6 or z0 < covered:
                    continue
                for w in range(count):
                    s = start + w * (WINDOW_W + WINDOW_GAP)
                    add_quad(bm_glass, p0 + t * s, p0 + t * (s + WINDOW_W), n, z0, z1, 0.04)

    tris = 0
    for key, bm, rough, metal, mkey in (("trim", bm_trim, 0.8, 0.0, k_trim), ("glass", bm_glass, 0.15, 0.3, k_glass)):
        if not bm.faces:
            bm.free()
            continue
        name = f"DET_{obj.name[4:]}_{key}"
        dme = bpy.data.meshes.new(name)
        bm.to_mesh(dme)
        bm.free()
        dme.materials.append(mat(mkey, rough, metal))
        tris += attach(obj, coll, name, dme)

    for i, (x, y, r) in enumerate(style.get("domes", [])):
        tris += attach(obj, coll, f"DET_{obj.name[4:]}_dome{i}", dome_mesh(x, y, zmax, r))
    if style.get("sign"):
        tris += attach(obj, coll, f"DET_{obj.name[4:]}_sign", sign_mesh(ring, zmax, axis, style["sign"]))
    if pinfo:
        tris += build_porch(obj, coll, porch, pinfo, zmin, zmax)
    if style.get("roofs"):
        tris += build_roofs(obj, coll, style["roofs"], zmax, ring)
    return tris


def build_roofs(obj, coll, specs, ztop, ring=None):
    """Mai doc dat len mai bang (chi la hinh, khong va cham). gable: 2 mai, hip: 4 mai, court: san trong.
    Toa do x/y the gioi; hoac "fit": True -> theo khung chu nhat cua mat bang (truc = canh dai nhat),
    "span": (u0, u1) ti le doan theo chieu dai."""
    parts = {}
    o, b = 0.4, ztop + 0.5  # mai nho ra khoi tuong o (m), chan mai cao hon lan can mot chut
    for sp in specs:
        O, U, V = Vector((0, 0)), Vector((1, 0)), Vector((0, 1))
        if sp.get("fit") and ring:
            U = max(((ring[(i + 1) % len(ring)] - ring[i]) for i in range(len(ring))), key=lambda v: v.length).normalized()
            V = Vector((-U.y, U.x))
            us, vs_ = [q.dot(U) for q in ring], [q.dot(V) for q in ring]
            u0, u1 = sp.get("span", (0, 1))
            L = max(us) - min(us)
            x0, x1 = min(us) + L * u0, min(us) + L * u1
            y0, y1 = min(vs_), max(vs_)
        else:
            x0, x1 = sp["x"]
            y0, y1 = sp["y"]
        W = lambda x, y, z: (O + U * x + V * y).to_3d() + Vector((0, 0, z))
        if sp["kind"] == "court":
            bm = parts.setdefault("c_court", bmesh.new())
            vs = [bm.verts.new(W(x, y, ztop + 0.05)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
            bm.faces.new(vs)
            continue
        x0, x1, y0, y1 = x0 - o, x1 + o, y0 - o, y1 + o
        bm = parts.setdefault(sp["mat"], bmesh.new())
        A, B, C, D = (bm.verts.new(W(x, y, b)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))
        xm, ym, zr = (x0 + x1) / 2, (y0 + y1) / 2, b + sp["h"]
        along_x = x1 - x0 >= y1 - y0
        if sp["kind"] == "hip":
            e = min(x1 - x0, y1 - y0) / 2
        else:
            e = 0.0
        if along_x:
            R0, R1 = bm.verts.new(W(x0 + e, ym, zr)), bm.verts.new(W(x1 - e, ym, zr))
            faces = [(A, B, R1, R0), (C, D, R0, R1), (D, A, R0), (B, C, R1)]
        else:
            R0, R1 = bm.verts.new(W(xm, y0 + e, zr)), bm.verts.new(W(xm, y1 - e, zr))
            faces = [(B, C, R1, R0), (D, A, R0, R1), (A, B, R0), (C, D, R1)]
        for f in faces + [(D, C, B, A)]:
            if len(set(f)) == len(f):
                bm.faces.new(f)
    tris = 0
    for key, bm in parts.items():
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        name = f"DET_{obj.name[4:]}_roof_{key}" + ("_decal" if key == "c_court" else "")
        dme = bpy.data.meshes.new(name)
        bm.to_mesh(dme)
        bm.free()
        dme.materials.append(mat(key, 0.7))
        tris += attach(obj, coll, name, dme)
    return tris


def seg_dist(p, a, b):
    ab = b - a
    u = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (a + ab * u - p).length


def build_porch(obj, coll, cfg, pinfo, zmin, ztop):
    """Khoi sanh nho ra truoc mat tuong (toa C). Khong co va cham: tang tret de trong nen di vao duoi duoc."""
    c, t, n = pinfo["c"], pinfo["t"], pinfo["n"]
    W, D = cfg["width"], cfg["depth"]
    w2 = W / 2
    floors = max(1, int(round((ztop - zmin - 1.0) / FLOOR_HEIGHT)))
    fh = (ztop - zmin - 1.0) / floors
    top = ztop + 1.6           # diem mai sanh cao hon lan can khoi chinh
    pil = zmin + fh - 1.0      # tang tret: phan duoi de trong (cot), phan tren la dai hoa van
    parts = {}

    def B(key):
        if key not in parts:
            parts[key] = bmesh.new()
        return parts[key]

    P = lambda s, d: c + t * s + n * d

    def box(key, s0, s1, d0, d1, z0, z1):
        add_box(B(key), P(s0, 0), P(s1, 0), n, z0, z1, d0, d1)

    def quad(key, s0, s1, d, z0, z1):
        add_quad(B(key), P(s0, 0), P(s1, 0), n, z0, z1, d)

    def V(bm, s, d, z):
        p = P(s, d)
        return bm.verts.new((p.x, p.y, z))

    def vtri(key, s0, s1, d0, d1, zt, za):
        """Tam giac dung chuc xuong (day tren o zt, dinh o za), day d0..d1."""
        bm = B(key)
        sm = (s0 + s1) / 2
        f = [V(bm, s0, d1, zt), V(bm, sm, d1, za), V(bm, s1, d1, zt)]
        b = [V(bm, s0, d0, zt), V(bm, sm, d0, za), V(bm, s1, d0, zt)]
        for vs in (f[::-1], b, (b[0], b[1], f[1], f[0]), (b[1], b[2], f[2], f[1]), (b[2], b[0], f[0], f[2])):
            bm.faces.new(vs)

    def disc(key, s, d, zc, r, seg=10, rin=None):
        """Hinh tron (hoac sao neu co rin) dung, quay ra ngoai: quat tam giac tu tam."""
        bm = B(key)
        k = seg * (2 if rin else 1)
        ctr = V(bm, s, d, zc)
        ring = []
        for i in range(k):
            a = math.tau * i / k + math.pi / 2
            rr = rin if rin and i % 2 else r
            ring.append(V(bm, s + rr * math.cos(a), d, zc + rr * math.sin(a)))
        for i in range(k):
            bm.faces.new((ctr, ring[i], ring[(i + 1) % k]))

    # than sanh (trang): tu dinh tang tret de trong len diem mai, lung tua vao tuong khoi chinh
    box("trim", -w2, w2, -0.05, D, pil, top)
    box("trim", -w2 - 0.2, w2 + 0.2, D - 0.1, D + 0.3, top - 0.3, top + 0.4)  # go diem mai
    # tang tret: hang cot + mang tuong toi (sanh) phia sau, bac tam cap
    for i in range(6):
        s = -w2 + 0.45 + (W - 0.9) * i / 5
        box("trim", s - 0.25, s + 0.25, D - 0.65, D - 0.15, zmin, pil)
    quad("dark", -w2 + 0.3, w2 - 0.3, 0.03, zmin + 0.25, pil - 0.1)
    box("footway", -w2 - 0.6, w2 + 0.6, -0.1, D + 1.4, zmin, zmin + 0.25)
    # dai hoa van: phan tren tang tret va tang 2 -- go san trang, hang tam giac co lo tron, nen gach do
    for k in range(min(2, floors)):
        zt = zmin + (k + 1) * fh
        zlo = pil if k == 0 else zmin + k * fh
        quad("c_brick", -w2 + 0.3, w2 - 0.3, D + 0.01, zlo + 0.1, zt - 0.3)
        box("trim", -w2, w2, D - 0.05, D + 0.35, zt - 0.3, zt)
        tri_h = min(1.4, zt - 0.3 - zlo - 0.1)
        m = max(3, round((W - 0.6) / 1.45))
        tw = (W - 0.6) / m
        for j in range(m):
            s0 = -w2 + 0.3 + j * tw
            vtri("trim", s0 + 0.04, s0 + tw - 0.04, D + 0.05, D + 0.2, zt - 0.3, zt - 0.3 - tri_h)
            disc("dark", s0 + tw / 2, D + 0.21, zt - 0.3 - tri_h * 0.33, min(0.28, tw * 0.22))
        # vach dung trang chia o gach
        for j in range(m + 1):
            s = -w2 + 0.3 + j * tw
            box("trim", s - 0.08, s + 0.08, D, D + 0.12, zlo, zt - 0.3)
    # tang tren cung: lam dung trang truoc nen toi
    for k in range(2, floors):
        z0 = zmin + k * fh
        quad("dark", -w2 + 0.3, w2 - 0.3, D + 0.01, z0 + 0.3, ztop - 0.2)
        cnt = max(2, round(W / 1.6))
        for j in range(cnt + 1):
            s = -w2 + 0.3 + (W - 0.6) * j / cnt
            box("trim", s - 0.12, s + 0.12, D, D + 0.45, z0, ztop)
    # ban cong giua o san tang 2, hai cot do ben duoi
    bw2 = min(3.6, w2 - 1)
    zb = zmin + fh
    box("trim", -bw2, bw2, D, D + 1.9, zb - 0.3, zb)
    box("trim", -bw2, bw2, D + 1.75, D + 1.9, zb, zb + 1.0)
    for s in (-bw2, bw2 - 0.15):
        box("trim", s, s + 0.15, D, D + 1.9, zb, zb + 1.0)
    for s in (-bw2 + 0.3, bw2 - 0.3):
        box("trim", s - 0.2, s + 0.2, D + 1.4, D + 1.8, zmin, zb - 0.3)
    # chu do ten truong tren diem mai
    if cfg.get("sign"):
        tme = font_mesh(cfg["sign"])
        xs = [v.co.x for v in tme.vertices]
        ys = [v.co.y for v in tme.vertices]
        band = top - 0.3 - (ztop - 0.1)
        k = min((W - 1.0) / (max(xs) - min(xs)), band * 0.75 / (max(ys) - min(ys)))
        p = P(-(max(xs) + min(xs)) / 2 * k, D + 0.03)
        ang = math.atan2(n.x, -n.y)  # chu nam XY doc tu -Y -> quay de doc tu phia n
        M = (Matrix.Translation((p.x, p.y, ztop - 0.1 + band / 2 - (max(ys) + min(ys)) / 2 * k))
             @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Scale(k, 4))
        bm = B("c_text")
        vs = [bm.verts.new(M @ v.co) for v in tme.vertices]
        for poly in tme.polygons:
            try:
                bm.faces.new([vs[i] for i in poly.vertices])
            except ValueError:
                pass
        bpy.data.meshes.remove(tme)
    # cot co truoc sanh (ben trai khi nhin tu san bong), co do sao vang
    sf, df, hp = -w2 * 0.4, D + 3.2, ztop - 1.3  # dinh co thap hon chu ten truong (theo anh)
    pp = P(sf, df)
    bmesh.ops.create_cone(B("pole"), cap_ends=True, segments=8, radius1=0.08, radius2=0.05, depth=hp,
                          matrix=Matrix.Translation((pp.x, pp.y, zmin + hp / 2)))
    fz0, fz1, fl = zmin + hp - 1.5, zmin + hp - 0.1, 2.1
    quad("flag", sf + 0.08, sf + 0.08 + fl, df, fz0, fz1)
    for d in (df + 0.02, df - 0.02):
        disc("star", sf + 0.08 + fl / 2, d, (fz0 + fz1) / 2, 0.42, 5, 0.17)

    tris = 0
    names = {"dark": "porch_win_glass", "c_brick": "porch_brick_decal", "c_text": "porch_text_decal"}
    for key, bmx in parts.items():
        dme = bpy.data.meshes.new("DET_" + obj.name[4:] + "_" + names.get(key, "porch_" + key))
        bmx.normal_update()
        bmx.to_mesh(dme)
        bmx.free()
        dme.materials.append(mat(key, 0.2 if key == "dark" else 0.8))
        tris += attach(obj, coll, dme.name, dme)
    return tris


def attach(obj, coll, name, dme):
    """Gan mesh chi tiet (toa do the gioi) lam con cua toa."""
    d = bpy.data.objects.new(name, dme)
    coll.objects.link(d)
    d.parent = obj
    d.matrix_parent_inverse = obj.matrix_world.inverted()
    return sum(len(p.vertices) - 2 for p in dme.polygons)


def dome_mesh(x, y, z, r):
    """Vom ban cau det tren mot vanh tru, mau xanh ngoc."""
    bm = bmesh.new()
    drum_h = 1.0
    bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=r * 1.04, radius2=r * 1.04, depth=drum_h,
                          matrix=Matrix.Translation((x, y, z + drum_h / 2)))
    sph = bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)["verts"]
    bmesh.ops.delete(bm, geom=[v for v in sph if v.co.z < -1e-4], context="VERTS")
    for v in sph:
        if v.is_valid:  # nua tren con lai: det xuong 1/2 roi dat len vanh
            v.co = Vector((x + v.co.x, y + v.co.y, z + drum_h + v.co.z * 0.5))
    me = bpy.data.meshes.new("dome")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat("dome", 0.35, 0.2))
    return me


def font_mesh(text):
    """Chu phang (mat phang XY, can giua, cao ~1) -> mesh tam. Nho xoa sau khi dung."""
    cu = bpy.data.curves.new("tmp_sign", "FONT")
    cu.body = text
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.size = 1.0
    tmp = bpy.data.objects.new("tmp_sign", cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    tme = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.curves.remove(cu)
    return tme


def sign_mesh(ring, zmax, axis, text):
    """Bang ten tren mai: tam bang trang dat doc theo truc chinh, chu xanh ca hai mat."""
    cx = sum(p.x for p in ring) / len(ring)
    cy = sum(p.y for p in ring) / len(ring)
    along = [p.dot(axis) for p in ring]
    length = (max(along) - min(along)) * 0.7
    H, T, LIFT = 2.4, 0.3, 1.2
    ang = math.atan2(axis.y, axis.x)
    M = Matrix.Translation((cx, cy, zmax + LIFT + H / 2)) @ Matrix.Rotation(ang, 4, "Z")

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=M @ Matrix.Diagonal((length, T, H, 1)))
    for f in bm.faces:
        f.material_index = 0
    tme = font_mesh(text)
    xs = [v.co.x for v in tme.vertices]
    ys = [v.co.y for v in tme.vertices]
    k = min(length * 0.92 / (max(xs) - min(xs)), H * 0.6 / (max(ys) - min(ys)))
    # chu nam mat phang XY -> xoay dung len, mat doc duoc huong -Y, ap vao mat -Y cua bang
    front = (Matrix.Translation((0, -(T / 2 + 0.02), 0))
             @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Scale(k, 4))
    for side in (1, -1):
        # mat sau = mat truoc xoay 180 do quanh truc dung (khong bi nguoc chu)
        Mt = M @ (front if side == 1 else Matrix.Rotation(math.pi, 4, "Z") @ front)
        tb = bmesh.new()
        tb.from_mesh(tme)
        bmesh.ops.transform(tb, matrix=Mt, verts=tb.verts)
        tmp_me = bpy.data.meshes.new("tmp")
        tb.to_mesh(tmp_me)
        tb.free()
        off = len(bm.verts)
        vs = [bm.verts.new(v.co) for v in tmp_me.vertices]
        for p in tmp_me.polygons:
            try:
                f = bm.faces.new([vs[i] for i in p.vertices])
                f.material_index = 1
            except ValueError:
                pass
        bpy.data.meshes.remove(tmp_me)
    bpy.data.meshes.remove(tme)
    me = bpy.data.meshes.new("sign")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat("sign", 0.6))
    me.materials.append(mat("sign_text", 0.5))
    return me


# ---------------------------------------------------------------------------
# 1b. Cong chinh (theo anh flycam: duong vao co dai bon cay o giua, hai tru cong, hang rao thap)
# ---------------------------------------------------------------------------
def build_gate(coll):
    # cong A lay tu ban MyUIT (PROP_congA / GND_congA, dung chu UIT, hang co, san hoa van): khong dung cong cu
    if bpy.data.objects.get("PROP_congA"):
        log("   Da co cong A cua MyUIT (PROP_congA), bo qua cong cu")
        return 0
    pos = Vector(GATE["pos"])
    d = Vector(GATE["dir"]).normalized()
    side = Vector((-d.y, d.x))
    W, ML = GATE["width"], GATE["median_len"]
    ang = math.atan2(d.y, d.x)

    def box(bm, center2d, z0, z1, length, width, mi=0):
        M = Matrix.Translation((center2d.x, center2d.y, (z0 + z1) / 2)) @ Matrix.Rotation(ang, 4, "Z")
        r = bmesh.ops.create_cube(bm, size=1.0, matrix=M @ Matrix.Diagonal((length, width, z1 - z0, 1)))
        for v in r["verts"]:
            for f in v.link_faces:
                f.material_index = mi

    made = 0
    # mat duong rong (de len duong OSM hep)
    road_len = ML + 6
    bm = bmesh.new()
    box(bm, pos + d * (road_len / 2 - 1), 0.0, 0.16, road_len, W)
    made += gate_obj(coll, "GATE_road", bm, ["asphalt"])

    # tru cong + hang rao thap hai ben
    bm = bmesh.new()
    for sgn in (1, -1):
        p = pos + side * sgn * (W / 2 + 0.7)
        box(bm, p, 0, 3.4, 1.4, 1.4, 0)
        FL = GATE.get("fence_len", 3.0)
        box(bm, pos + side * sgn * (W / 2 + 1.4 + FL / 2), 0, 1.3, 0.3, FL, 1)
    made += gate_obj(coll, "GATE_pillars", bm, ["gate", "fence"])

    # dai bon cay o giua duong vao
    bm = bmesh.new()
    n_pl = max(1, round(ML / 5))
    for i in range(n_pl):
        c = pos + d * (3 + i * (ML - 3) / max(1, n_pl - 1)) if n_pl > 1 else pos + d * (ML / 2)
        box(bm, c, 0, 0.55, 3.2, 1.4, 0)
        r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.9,
                                       matrix=Matrix.Translation((c.x, c.y, 1.15)) @ Matrix.Diagonal((1.55, 0.7, 0.8, 1)))
        for v in r["verts"]:
            for f in v.link_faces:
                f.material_index = 1
    made += gate_obj(coll, "GATE_median", bm, ["planter", "bush"])
    return made


def build_back_gate(coll):
    """Cong sau: 2 tru, hang rao sat hai ben, canh cong truot dang mo, bot bao ve nho."""
    pos = Vector(BACK_GATE["pos"])
    d = Vector(BACK_GATE["dir"]).normalized()
    side = Vector((-d.y, d.x))
    W, FL = BACK_GATE["width"], BACK_GATE["fence_len"]
    ang = math.atan2(d.y, d.x)

    def box(bm, c2, z0, z1, along, across, mi):
        M = Matrix.Translation((c2.x, c2.y, (z0 + z1) / 2)) @ Matrix.Rotation(ang, 4, "Z")
        r = bmesh.ops.create_cube(bm, size=1.0, matrix=M @ Matrix.Diagonal((along, across, z1 - z0, 1)))
        for f in {f for v in r["verts"] for f in v.link_faces}:
            f.material_index = mi

    bm = bmesh.new()
    for sgn in (1, -1):
        box(bm, pos + side * sgn * (W / 2 + 0.4), 0, 3.0, 0.8, 0.8, 0)              # tru cong
        box(bm, pos + side * sgn * (W / 2 + 0.8 + FL / 2), 0, 1.8, 0.15, FL, 1)    # hang rao
    box(bm, pos + d * 0.5 + side * (W / 2 + 0.8 + W * 0.3), 0.1, 1.7, 0.1, W * 0.6, 1)  # canh cong da keo sang
    # bot bao ve phia trong cong
    bc = pos + side * (W / 2 + 2.2) + d * 3.5
    box(bm, bc, 0, 2.6, 2.6, 2.6, 0)
    box(bm, bc, 2.6, 2.8, 3.3, 3.3, 2)
    box(bm, bc - side * 1.3, 1.0, 2.0, 1.6, 0.06, 3)  # cua so nhin ra loi di
    return gate_obj(coll, "GATE_back", bm, ["gate", "fence", "ct_roof", "dark"])


def gate_obj(coll, name, bm, keys):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for k in keys:
        me.materials.append(mat(k, 0.9))
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return sum(len(p.vertices) - 2 for p in me.polygons)


# ---------------------------------------------------------------------------
# 2. Mau mat dat
# ---------------------------------------------------------------------------
def recolor_ground():
    for oname, key in (("GND_Base", "base"), ("GND_Green", "green"), ("PATH_Footway", "footway"),
                       ("PATH_Road", "road"), ("GND_Pitch", "pitch")):
        o = bpy.data.objects.get(oname)
        if o and o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(mat(key, 0.95))


# ---------------------------------------------------------------------------
# 3. Cay
# ---------------------------------------------------------------------------
def tree_meshes():
    meshes = []
    # cay tan tron
    for idx, leaf in enumerate(("leaf1", "leaf2", "leaf3")):
        name = f"TREEMESH_round_{idx}"
        me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
        bm = bmesh.new()
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.28, radius2=0.2, depth=2.6,
                                    matrix=Matrix.Translation((0, 0, 1.3)))
        trunk_verts = set(res["verts"])
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=2.3,
                                   matrix=Matrix.Translation((0, 0, 3.9)))
        for v in bm.verts:
            if v.co.z > 2.0:
                v.co.z = 3.9 + (v.co.z - 3.9) * 0.85
        for f in bm.faces:
            f.material_index = 0 if all(v in trunk_verts for v in f.verts) else 1
        me.materials.clear()
        me.materials.append(mat("trunk", 0.9))
        me.materials.append(mat(leaf, 0.9))
        bm.to_mesh(me)  # sau khi gan vat lieu, vi materials.clear() dat lai chi so vat lieu ve 0
        bm.free()
        meshes.append(me)
    # cay dang non (thong)
    name = "TREEMESH_pine"
    me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    bm = bmesh.new()
    M = Matrix
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.25, radius2=0.18, depth=1.6,
                                matrix=M.Translation((0, 0, 0.8)))
    trunk_verts = set(res["verts"])
    for lvl, (r, z) in enumerate(((2.0, 2.6), (1.6, 3.9), (1.1, 5.1))):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=r, radius2=0.05, depth=2.2,
                              matrix=M.Translation((0, 0, z)))
    for f in bm.faces:
        f.material_index = 0 if all(v in trunk_verts for v in f.verts) else 1
    me.materials.clear()
    me.materials.append(mat("trunk", 0.9))
    me.materials.append(mat("leaf3", 0.9))
    bm.to_mesh(me)
    bm.free()
    meshes.append(me)
    return meshes


def tris_2d(obj):
    """Tam giac 2D (the gioi) cua mot mesh phang."""
    out = []
    if not obj or obj.type != "MESH":
        return out
    mw = obj.matrix_world
    me = obj.data
    me.calc_loop_triangles()
    for lt in me.loop_triangles:
        out.append(tuple((mw @ me.vertices[i].co).to_2d() for i in lt.vertices))
    return out


def in_tri(p, a, b, c):
    d1 = (p.x - b.x) * (a.y - b.y) - (a.x - b.x) * (p.y - b.y)
    d2 = (p.x - c.x) * (b.y - c.y) - (b.x - c.x) * (p.y - c.y)
    d3 = (p.x - a.x) * (c.y - a.y) - (c.x - a.x) * (p.y - a.y)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


class Grid:
    """Luoi tra cuu nhanh tam giac theo o 10 m."""

    def __init__(self, tris, cell=10.0):
        self.cell = cell
        self.g = {}
        for t in tris:
            xs = [p.x for p in t]
            ys = [p.y for p in t]
            for gx in range(int(math.floor(min(xs) / cell)), int(math.floor(max(xs) / cell)) + 1):
                for gy in range(int(math.floor(min(ys) / cell)), int(math.floor(max(ys) / cell)) + 1):
                    self.g.setdefault((gx, gy), []).append(t)

    def hit(self, p):
        for t in self.g.get((int(math.floor(p.x / self.cell)), int(math.floor(p.y / self.cell))), ()):
            if in_tri(p, *t):
                return True
        return False


def plant_trees(coll):
    # da co cay lay tu ban MyUIT (CAY_*): khong trong them cay tu dong
    if any(o.name.startswith("CAY_") for o in bpy.data.objects):
        log("Da co cay CAY_* (MyUIT), bo qua trong cay tu dong")
        return 0
    green = bpy.data.objects.get("GND_Green")
    if not green:
        log("Khong co GND_Green, bo qua trong cay")
        return 0
    rnd = random.Random(TREE_SEED)
    green_tris = tris_2d(green)
    block = Grid(tris_2d(bpy.data.objects.get("PATH_Footway")) + tris_2d(bpy.data.objects.get("PATH_Road"))
                 + tris_2d(bpy.data.objects.get("GND_Pitch"))
                 + tris_2d(bpy.data.objects.get("GATE_road")))
    blds = []
    bcol = bpy.data.collections.get("Buildings")
    for o in (bcol.objects if bcol else []):
        if o.name.startswith("BLD_") and o.type == "MESH":
            ws = [o.matrix_world @ v.co for v in o.data.vertices]
            blds.append((min(v.x for v in ws) - 3, max(v.x for v in ws) + 3,
                         min(v.y for v in ws) - 3, max(v.y for v in ws) + 3))

    meshes = tree_meshes()
    placed = []
    for a, b, c in green_tris:
        area = abs((b - a).cross(c - a)) / 2
        n = area * TREE_DENSITY
        count = int(n) + (1 if rnd.random() < n - int(n) else 0)
        for _ in range(count):
            r1, r2 = rnd.random(), rnd.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            p = a + (b - a) * r1 + (c - a) * r2
            if p.length > TREE_RADIUS_LIMIT:
                continue
            if any(x0 < p.x < x1 and y0 < p.y < y1 for x0, x1, y0, y1 in blds):
                continue
            if any(block.hit(p + Vector(off)) for off in ((0, 0), (1.8, 0), (-1.8, 0), (0, 1.8), (0, -1.8))):
                continue
            if any((p - q).length < TREE_SPACING for q in placed):
                continue
            placed.append(p)

    for i, p in enumerate(placed):
        me = meshes[3] if rnd.random() < 0.2 else meshes[rnd.randrange(3)]
        o = bpy.data.objects.new(f"TREE_{i:03d}", me)
        o.location = (p.x, p.y, 0.1)
        s = rnd.uniform(0.8, 1.3)
        o.scale = (s, s, s * rnd.uniform(0.9, 1.15))
        o.rotation_euler = (0, 0, rnd.uniform(0, math.tau))
        coll.objects.link(o)
    return len(placed)


# ---------------------------------------------------------------------------
def main():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    clear_old()

    bcol = bpy.data.collections.get("Buildings")
    if not bcol:
        raise RuntimeError("Khong thay collection 'Buildings'.")
    total = 0
    for o in list(bcol.objects):
        if o.name.startswith("BLD_") and o.type == "MESH":
            # toa da co mo hinh hien thi rieng (VIS_*, vd lay tu ban MyUIT): khong dung chi tiet de len
            if any(c.name.startswith("VIS_") for c in o.children):
                log(f"   {o.name:15s} bo qua (da co {', '.join(c.name for c in o.children if c.name.startswith('VIS_'))})")
                continue
            t = detail_building(o, bcol)
            total += t
            log(f"   {o.name:15s} +{t} tam giac chi tiet")
    recolor_ground()
    log(f"   Cong chinh +{build_gate(get_collection('Props'))} tam giac")
    log(f"   Cong sau +{build_back_gate(get_collection('Props'))} tam giac")
    trees = plant_trees(get_collection("Deco"))
    log(f"Da them chi tiet ({total} tam giac) va trong {trees} cay.")

    try:
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.shading.type = "MATERIAL"
        ref = bpy.context.view_layer.layer_collection.children.get("Reference")
        if ref:
            ref.hide_viewport = True   # an anh ve tinh de xem mau moi
    except Exception:  # noqa: BLE001
        pass
    log("HOAN TAT. Ctrl + S de luu, roi chay uit_export.py de xuat ra web.")


if __name__ == "__main__":
    main()
