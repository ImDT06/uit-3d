"""
UIT 3D - Buoc 5b: Nuong bong mem (AO) + texture lap cho toa nha
=================================================================
Chay SAU uit_detail.py va uit_gameplay.py, TRUOC uit_export.py (chay lai bao nhieu lan cung duoc).

Script nay se, cho tung toa trong BAKE (va cac chi tiet DET_ con cua no):
  1. Trai UV "UVMap" kieu chieu hop theo toa do the gioi (1 o texture = TILE m) de dan texture lap
  2. Tao texture lap bang code (vua tuong, mai ton song, gach, ngoi...) da to mau san, khong dinh ban quyen
  3. Trai UV thu hai "ao" (smart project), nuong AO bang Cycles vao anh rieng tung object
  4. Gan anh AO vao node "glTF Material Output" -> Occlusion: file glb co occlusionTexture (texCoord 1),
     three.js tu doc thanh aoMap
Vat lieu duoc nhan ban rieng tung object ("MAT_x@BLD_C") vi moi object co anh AO rieng.

Cach chay: tab Scripting > mo file nay > Run Script (mat vai phut: Cycles nuong tren CPU).
"""

import bpy
import bmesh
import math
import numpy as np

BAKE = ["BLD_C"]          # toa can nuong (them dan khi thu nghiem on)
AO_SAMPLES = 48
AO_DISTANCE = 4.0         # m, tam xa toi da cua bong mem
TEX_SIZE = 256

# texture lap theo vat lieu: (kieu, kich thuoc 1 o texture tinh bang m)
TEXTURES = {
    "c_wall": ("plaster", 3.0),
    "trim": ("plaster", 3.0),
    "roof": ("slab", 4.0),
    "c_roof": ("corrugated", 3.0),
    "a_roof": ("tiles", 2.0),
    "c_brick": ("brick", 1.6),
    "footway": ("slab", 2.0),
}


def log(msg):
    print("[UIT3D] " + msg, flush=True)


# ---------------------------------------------------------------------------
# Texture lap sinh bang code (tuan hoan -> ghep khong lo duong noi)
# ---------------------------------------------------------------------------
def periodic_noise(n, octaves, rng, amp=1.0):
    y, x = np.mgrid[0:n, 0:n] / n
    out = np.zeros((n, n))
    for o in range(octaves):
        f = 2 ** o
        for _ in range(4):
            fx, fy = rng.integers(-f * 2, f * 2 + 1, size=2)
            out += amp / (o + 1) * np.sin(2 * math.pi * (fx * x + fy * y) + rng.uniform(0, 2 * math.pi))
    out /= max(np.abs(out).max(), 1e-6)
    return out


def pattern(kind, n=TEX_SIZE):
    """Do sang (0..1) cua mau, se nhan voi mau vat lieu."""
    rng = np.random.default_rng(abs(hash(kind)) % 2 ** 32)
    y, x = np.mgrid[0:n, 0:n] / n
    grain = rng.normal(0, 1, (n, n))
    if kind == "plaster":
        v = 0.95 + 0.03 * periodic_noise(n, 4, rng) + 0.015 * grain
    elif kind == "slab":            # be tong / gach lat o vuong
        v = 0.93 + 0.04 * periodic_noise(n, 3, rng) + 0.02 * grain
        line = (np.minimum(x % 0.25, 0.25 - x % 0.25) < 0.006) | (np.minimum(y % 0.25, 0.25 - y % 0.25) < 0.006)
        v = np.where(line, v * 0.82, v)
    elif kind == "corrugated":      # mai ton song
        v = 0.88 + 0.10 * np.sin(2 * math.pi * 12 * x) + 0.01 * grain
    elif kind == "tiles":           # ngoi
        row = np.floor(y * 8)
        xx = (x * 8 + (row % 2) * 0.5) % 1
        yy = (y * 8) % 1
        v = 0.80 + 0.18 * yy + 0.03 * periodic_noise(n, 3, rng)
        v = np.where(np.minimum(xx, 1 - xx) < 0.04, v * 0.8, v)
    elif kind == "brick":
        row = np.floor(y * 8)
        xx = (x * 4 + (row % 2) * 0.5) % 1
        yy = (y * 8) % 1
        tone = 0.9 + 0.1 * np.sin(row * 12.9898 + np.floor(x * 4 + (row % 2) * 0.5) * 78.233)
        v = tone + 0.02 * grain
        mortar = (np.minimum(xx, 1 - xx) < 0.03) | (np.minimum(yy, 1 - yy) < 0.06)
        v = np.where(mortar, 1.35, v)
    else:
        v = np.ones((n, n))
    return np.clip(v, 0, 1.5)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def color_texture(key, base_rgb):
    """Anh texture da to mau (sRGB) cho vat lieu key."""
    kind, _ = TEXTURES[key]
    name = f"TX_{key}"
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.new(name, TEX_SIZE, TEX_SIZE, alpha=False)
    v = pattern(kind)
    rgb = np.stack([to_srgb(np.clip(base_rgb[i] * v, 0, 1)) for i in range(3)], axis=-1)
    rgba = np.concatenate([rgb, np.ones((TEX_SIZE, TEX_SIZE, 1))], axis=-1)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.file_format = "JPEG"
    img.pack()
    return img


# ---------------------------------------------------------------------------
# UV
# ---------------------------------------------------------------------------
def box_uv(obj, tile_of_mat):
    """UV 'UVMap' (kenh 0): chieu theo truc phap tuyen troi nhat, toa do the gioi / kich thuoc o."""
    me = obj.data
    while len(me.uv_layers) and me.uv_layers[0].name != "UVMap":
        me.uv_layers.remove(me.uv_layers[0])
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")
    mw = obj.matrix_world
    nmat = mw.to_3x3().inverted().transposed()
    for f in bm.faces:
        n = (nmat @ f.normal).normalized()
        s = tile_of_mat.get(f.material_index, 3.0)
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in f.loops:
            p = mw @ lp.vert.co
            if ax == 2:
                lp[uv].uv = (p.x / s, p.y / s)
            elif ax == 0:
                lp[uv].uv = (p.y / s, p.z / s)
            else:
                lp[uv].uv = (p.x / s, p.z / s)
    bm.to_mesh(me)
    bm.free()


def fix_normals(obj):
    """Phap tuyen huong ra ngoai (hop go tao bang add_box co mat quay vao trong -> AO den kit)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def ao_uv(obj):
    me = obj.data
    lay = me.uv_layers.get("ao") or me.uv_layers.new(name="ao")
    me.uv_layers.active = lay
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    me.uv_layers.active = me.uv_layers["UVMap"]


# ---------------------------------------------------------------------------
# Vat lieu
# ---------------------------------------------------------------------------
def gltf_output_group():
    g = bpy.data.node_groups.get("glTF Material Output")
    if g is None:
        g = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return g


def setup_material(obj, idx, ao_img):
    """Nhan ban vat lieu cho rieng object, gan texture lap (neu co) va anh AO. Tra ve node anh AO."""
    me = obj.data
    src = me.materials[idx]
    base = src.name.split("@")[0]
    name = f"{base}@{obj.name}"
    m = bpy.data.materials.get(name)
    if m is not None:
        bpy.data.materials.remove(m)
    m = src.copy()
    m.name = name
    me.materials[idx] = m
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    key = base[4:] if base.startswith("MAT_") else base
    if key in TEXTURES:
        col = list(bsdf.inputs["Base Color"].default_value)[:3]
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = color_texture(key, col)
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = "UVMap"
        nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if ao_img is None:
        return None
    aon = nt.nodes.new("ShaderNodeTexImage")
    aon.image = ao_img
    uva = nt.nodes.new("ShaderNodeUVMap")
    uva.uv_map = "ao"
    nt.links.new(uva.outputs["UV"], aon.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(aon.outputs["Color"], sep.inputs["Color"])
    grp = nt.nodes.new("ShaderNodeGroup")
    grp.node_tree = gltf_output_group()
    nt.links.new(sep.outputs[0], grp.inputs["Occlusion"])
    return aon


def smooth(img, r=2):
    """Lam min nhieu hat cua AO (it mau) -> JPEG nen nho hon nhieu, bong van mem."""
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    g = a[..., 0]
    for _ in range(2):  # 2 lan loc hop ~ loc Gauss
        acc = np.zeros_like(g)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                acc += np.roll(np.roll(g, dy, 0), dx, 1)
        g = acc / (2 * r + 1) ** 2
    g = np.round(g * 32) / 32  # bot muc xam -> nen tot hon
    a[..., 0] = a[..., 1] = a[..., 2] = g
    img.pixels.foreach_set(a.ravel())


def ao_size(obj):
    area = sum(p.area for p in obj.data.polygons)
    n = len(obj.data.polygons)
    if n > 600:
        return 1024  # nhieu manh nho (go, vach)
    return 512 if area > 300 else 256


# ---------------------------------------------------------------------------
def main():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scn = bpy.context.scene
    old_engine = scn.render.engine
    scn.render.engine = "CYCLES"
    scn.cycles.samples = AO_SAMPLES
    scn.cycles.device = "CPU"
    if scn.world:
        scn.world.light_settings.distance = AO_DISTANCE

    for bname in BAKE:
        bld = bpy.data.objects.get(bname)
        if not bld:
            log(f"Khong thay {bname}")
            continue
        objs = [bld] + [c for c in bld.children if c.type == "MESH"]
        for o in objs:
            flat = o.name.endswith(("_glass", "_decal"))
            tiles = {}
            for i, m in enumerate(o.data.materials):
                key = m.name.split("@")[0][4:]
                if key in TEXTURES:
                    tiles[i] = TEXTURES[key][1]
            fix_normals(o)
            box_uv(o, tiles)
            ao_img = None
            if not flat:
                ao_uv(o)
                iname = f"AO_{o.name}"
                old = bpy.data.images.get(iname)
                if old:
                    bpy.data.images.remove(old)
                sz = ao_size(o)
                ao_img = bpy.data.images.new(iname, sz, sz, alpha=False)
            nodes = [setup_material(o, i, ao_img) for i in range(len(o.data.materials))]
            if ao_img is None:
                continue
            for m, n in zip(o.data.materials, nodes):
                m.node_tree.nodes.active = n
                for x in m.node_tree.nodes:
                    x.select = x == n
            for x in bpy.context.view_layer.objects:
                x.select_set(False)
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            o.data.uv_layers.active = o.data.uv_layers["ao"]  # Cycles nuong vao lop UV dang chon
            bpy.ops.object.bake(type="AO", margin=48, margin_type="EXTEND", use_clear=True)  # lan mau ra ngoai manh UV: tranh nen den khi thu nho (mipmap)
            o.data.uv_layers.active = o.data.uv_layers["UVMap"]
            smooth(ao_img)
            ao_img.file_format = "JPEG"
            ao_img.pack()
            log(f"   {o.name}: AO {ao_img.size[0]}px")
    scn.render.engine = old_engine
    log("HOAN TAT nuong AO + texture. Chay uit_export.py de xuat.")


if __name__ == "__main__":
    main()
