# Nuong anh sang (ban thu) cho mot so toa cua mo hinh MyUIT tach toa.
# Chay ngam: blender -b --factory-startup -P tools/blender/uit_nuong_myuit.py -- [ten_ra] [obj1,obj2,...]
# Vi du: ... -- uit_myuit_nuongB BLD_B,PODIUM_B  ->  public/models/uit_myuit_nuongB.glb (xem bang ?model=uit_myuit_nuongB)
# Doc public/models/uit_myuit_tach.glb (khong sua file goc). Anh sang khop preset "thap" trong src/world/lighting.js,
# mau khop src/world/palette.js: sua hai file do thi phai sua o day va nuong lai.
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector

THU_MUC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "public", "models")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEN_RA = args[0] if args else "uit_myuit_nuongB"
DOI_TUONG = (args[1] if len(args) > 1 else "BLD_B,PODIUM_B").split(",")

# preset "thap": huong mat troi three (x, y, z) -> Blender (x, -z, y)
SUN_DIR = (140.0, -85.0, 78.0)
SUN_COLOR, SUN_STRENGTH = "ffd9a0", 2.6
SKY, GROUND, HEMI = "bcd6ff", "d9b890", 2.6  # ram sang hon ban thoi gian thuc (thay cho tu sang SANG cua toa B)
SUN_ANGLE = 1.5     # do: mep bong hoi mem
HE_SO = 0.75        # anh 8 bit luu gia tri x HE_SO (cho sang khong bi cat); web nhan nguoc lai
PX_M = 12           # diem anh moi met (bi chan boi MAX)
MAX = {"BLD_B": 2048, "PODIUM_B": 1024}
SAMPLES = 640       # nhieu mau cho mang toi bot loang
BU_SANG = 0.14      # cong them (mau x BU_SANG): hanh lang, goc khuat khong toi om
MAT_NGUOC = 0.012   # diem toi hon muc nay: coi nhu mat bi lat (phap tuyen quay vao trong), lay ket qua phia ben kia

MAU = {  # CHUNG + TUOI trong palette.js
    "Color_E08": "93cb6c", "G02_Spring_Lime": "b4eaa6", "M00_Soft_Cloud": "f6ead2", "M03_Pewter_Shine": "e3d9c6",
    "M05_Graphite_Haze": "c6c5c4", "M06_Steel_Smoke": "9298a8", "M07_Charcoal_Gleam": "939aa6",
    "UIT_main_blue": "2fc4f0", "UIT_glasswindow_main": "74b9c9", "UIT_glasswindow_supporting": "bfe8f0",
    "B03_Apricot_Glow": "ffb48c", "Color_C08": "cfa67e",
}
RIENG = {"BLD_B": {"UIT_suporting_blue": "c4e4ff", "FrontColor": "eef7fd", "UIT_main_blue": "6aaae6",
                   "UIT_glasswindow_main": "7cc3d6"}}


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def bsdf(m):
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def chuan_vat_lieu(m, mau):
    b = bsdf(m)
    if not b:
        return
    if mau:
        for l in list(b.inputs["Base Color"].links):
            m.node_tree.links.remove(l)
        b.inputs["Base Color"].default_value = lin(mau)
    b.inputs["Metallic"].default_value = 0  # kim loai khong co thanh phan khuech tan -> nuong ra den
    b.inputs["Roughness"].default_value = 1
    for l in list(b.inputs["Alpha"].links):
        m.node_tree.links.remove(l)
    b.inputs["Alpha"].default_value = 1


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(THU_MUC, "uit_myuit_tach.glb"))
sc = bpy.context.scene

# mau nhu tren web (anh huong anh sang doi). Toa co mau rieng dung ban sao vat lieu.
for m in list(bpy.data.materials):
    chuan_vat_lieu(m, MAU.get(m.name))
goi = {}
for o in [o for o in sc.objects if o.type == "MESH" and o.name in DOI_TUONG]:
    rieng = RIENG.get(o.name, {})
    for i, m in enumerate(o.data.materials):
        if m.name in rieng:
            if (o.name, m.name) not in goi:
                c = m.copy()
                chuan_vat_lieu(c, rieng[m.name])
                goi[(o.name, m.name)] = c
            o.data.materials[i] = goi[(o.name, m.name)]
# khoi chi de va cham khong duoc che nang
for o in sc.objects:
    if o.name.startswith("COL_"):
        o.hide_render = True

# mat troi + bau troi: tren la mau troi, duoi la mau dat (giong hemisphereLight cua three)
den = bpy.data.lights.new("sun", "SUN")
den.energy, den.color, den.angle = SUN_STRENGTH, lin(SUN_COLOR)[:3], math.radians(SUN_ANGLE)
sun = bpy.data.objects.new("sun", den)
sc.collection.objects.link(sun)
sun.rotation_euler = Vector(SUN_DIR).normalized().to_track_quat("Z", "Y").to_euler()
w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
nt = w.node_tree
bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
tc = nt.nodes.new("ShaderNodeTexCoord")
tach = nt.nodes.new("ShaderNodeSeparateXYZ")
tren = nt.nodes.new("ShaderNodeMath")
tren.operation = "GREATER_THAN"
tren.inputs[1].default_value = 0.0
tron = nt.nodes.new("ShaderNodeMix")
tron.data_type = "RGBA"
mau_vao = [s for s in tron.inputs if s.type == "RGBA"]
mau_vao[0].default_value, mau_vao[1].default_value = lin(GROUND), lin(SKY)
nt.links.new(tc.outputs["Generated"], tach.inputs[0])
nt.links.new(tach.outputs["Z"], tren.inputs[0])
nt.links.new(tren.outputs[0], tron.inputs[0])
nt.links.new(next(s for s in tron.outputs if s.type == "RGBA"), bg.inputs["Color"])
bg.inputs["Strength"].default_value = HEMI / math.pi

sc.render.engine = "CYCLES"
sc.cycles.samples = SAMPLES
sc.cycles.max_bounces = 5
sc.cycles.diffuse_bounces = 3
prefs = bpy.context.preferences.addons["cycles"].preferences
for kieu in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = kieu
        prefs.get_devices()
        if any(d.type == kieu for d in prefs.devices):
            for d in prefs.devices:
                d.use = d.type == kieu
            sc.cycles.device = "GPU"
            print("NUONG bang", kieu)
            break
    except Exception:
        pass

xong = []
for ten in DOI_TUONG:
    o = sc.objects[ten]
    me = o.data
    if me.users > 1:
        o.data = me = me.copy()
    area = sum(p.area for p in me.polygons) * o.matrix_world.median_scale ** 2  # object co scale (~28)
    size = min(MAX.get(ten, 1024), max(256, int(math.ceil(math.sqrt(area) * PX_M / 0.7 / 64)) * 64))
    lay = me.uv_layers.new(name="LM")
    me.uv_layers.active = lay
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=3.0 / size, margin_method="FRACTION")
    bpy.ops.object.mode_set(mode="OBJECT")
    img = bpy.data.images.new("raw_" + ten, size, size, alpha=False, float_buffer=True)
    for m in set(me.materials):
        n = m.node_tree.nodes.new("ShaderNodeTexImage")
        n.name, n.image = "nuong", img
        for x in m.node_tree.nodes:
            x.select = x == n
        m.node_tree.nodes.active = n
    def nuong(loc):
        bpy.ops.object.bake(type="DIFFUSE", pass_filter=loc, margin=8, margin_type="EXTEND", use_clear=True)
        return np.array(img.pixels[:], np.float32).reshape(size, size, 4)[..., :3].copy()

    def lat_mat():
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(me)
        bm.free()

    mau_goc = nuong({"COLOR"})
    rgb = nuong({"DIRECT", "INDIRECT", "COLOR"})
    lat_mat()
    nguoc = nuong({"DIRECT", "INDIRECT", "COLOR"})
    lat_mat()
    for m in set(me.materials):
        m.node_tree.nodes.remove(m.node_tree.nodes["nuong"])
    do_sang = np.array([0.2126, 0.7152, 0.0722], np.float32)
    den_ = (rgb @ do_sang < MAT_NGUOC) & (nguoc @ do_sang > rgb @ do_sang)
    rgb[den_] = nguoc[den_]
    print("NUONG", ten, "diem lay tu mat lat:", int(den_.sum()))
    rgb = rgb + mau_goc * BU_SANG
    img8 = bpy.data.images.new("LM_" + ten, size, size, alpha=False)
    img8.pixels.foreach_set(np.dstack([to_srgb(rgb * HE_SO), np.ones((size, size), np.float32)]).astype(np.float32).ravel())
    img8.pack()
    xong.append((o, img8))
    print("NUONG", ten, size, "px, dien tich", round(area), "m2, max", round(float(rgb.max()), 2), "trung binh", round(float(rgb.mean()), 3))

# thay vat lieu sau khi nuong het (toa nuong sau van thay mau goc cua toa truoc khi tinh anh sang doi)
for o, img8 in xong:
    me = o.data
    m = bpy.data.materials.new("LM_" + o.name)
    m.use_nodes = True
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img8
    m.node_tree.links.new(t.outputs["Color"], bsdf(m).inputs["Base Color"])
    bsdf(m).inputs["Roughness"].default_value = 1
    m.use_backface_culling = False
    me.materials.clear()
    me.materials.append(m)
    me.polygons.foreach_set("material_index", [0] * len(me.polygons))
    for ten_uv in [l.name for l in me.uv_layers if l.name != "LM"]:
        me.uv_layers.remove(me.uv_layers[ten_uv])
    o["baked"] = 1
    o["lm"] = 1 / HE_SO

bpy.data.objects.remove(sun)
ra = os.path.join(THU_MUC, TEN_RA + ".glb")
bpy.ops.export_scene.gltf(filepath=ra, export_format="GLB", export_extras=True, export_image_format="WEBP",
                          export_image_quality=88, export_draco_mesh_compression_enable=True,
                          export_draco_mesh_compression_level=6, export_draco_position_quantization=18)
print("XUAT", ra, os.path.getsize(ra))
