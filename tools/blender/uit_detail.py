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
}

# Kieu rieng tung toa. Khong co trong bang -> kieu mac dinh (tuong kem, cua so o vuong).
#   curtain: mat dai (song song truc chinh) la kinh lien thay cho cua so
#   domes:   [(x, y, ban kinh)] toa do the gioi Blender, vom dat tren mai
#   sign:    bang ten tren mai (chu 2 mat)
STYLE = {
    "BLD_A": {"wall": "a_wall", "roof": "a_roof", "trim": "a_trim", "glass": "a_glass",
              "domes": [(1.8, 73.0, 7.0), (-10.0, 26.0, 11.0)]},
    "BLD_E": {"wall": "e_wall", "glass": "e_glass", "curtain": True,
              "sign": "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN"},
}

# Cong chinh: pos = giua cong (x, y), dir = huong di vao truong, width = be rong duong vao.
# Doan duong vao co dai bon cay o giua dai median_len (m).
GATE = {"pos": (-71.2, 12.5), "dir": (20.0, -7.0), "width": 10.0, "median_len": 16.0, "fence_len": 3.0}


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
        if o.name.startswith(("DET_", "TREE_", "GATE_")):
            bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def detail_building(obj, coll):
    fp = footprint(obj)
    if not fp:
        return 0
    ring, zmin, zmax, top_idx = fp
    height = zmax - zmin
    floors = max(1, int(round((height - 1.0) / FLOOR_HEIGHT)))
    fh = (height - 1.0) / floors if height > 2 else height

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
    for p in me.polygons:
        p.material_index = 1 if p.index == top_idx else 0

    bm_trim, bm_glass = bmesh.new(), bmesh.new()
    n_edges = len(ring)
    for i in range(n_edges):
        p0, p1 = ring[i], ring[(i + 1) % n_edges]
        e = p1 - p0
        L = e.length
        if L < 0.5:
            continue
        t = e / L
        n = Vector((t.y, -t.x))  # phap tuyen huong ra ngoai (vong nguoc chieu kim dong ho)

        # go ngang o moi san + lan can mai
        ext = t * 0.15
        for k in range(1, floors + 1):
            z = zmin + k * fh
            if k == floors:
                z = zmax
            add_box(bm_trim, p0 - ext, p1 + ext, n, z - LEDGE_THICK, z, -0.01, LEDGE_DEPTH)
        add_box(bm_trim, p0, p1, n, zmax, zmax + PARAPET_H, -PARAPET_T, 0.02)

        # kinh lien (mat song song truc chinh)
        if curtain and abs(t.dot(axis)) > 0.9 and L > 3:
            add_quad(bm_glass, p0, p1, n, zmin + 0.6, zmax - 0.25, 0.05)
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
            if z1 - z0 < 0.6:
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
    # chu: dung text object cua Blender roi chuyen thanh mesh
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
            t = detail_building(o, bcol)
            total += t
            log(f"   {o.name:15s} +{t} tam giac chi tiet")
    recolor_ground()
    log(f"   Cong chinh +{build_gate(get_collection('Props'))} tam giac")
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
