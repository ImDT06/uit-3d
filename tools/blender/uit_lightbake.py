"""
UIT 3D - Buoc 5c: Nuong TOAN BO anh sang (nang, bong mem, anh sang doi, bo canh) vao texture
==============================================================================================
Chay SAU uit_detail.py / uit_bake.py, TRUOC uit_export.py. Chay lai duoc tren file da nuong: vat lieu goc
cua object da nuong luu trong Text "LB_store", script tu lay lai truoc khi nuong.

Cho tung muc trong LIGHTBAKE (toa + DET_ con tru kinh *_glass, mat dat, loi di...):
  1. Dat tam mat troi + mau troi theo PRESETS[LIGHT] ("trua" / "chieu"; khop src/world/lighting.js)
  2. Chen node Bevel vao phap tuyen vat lieu: canh duoc bo tron khi nuong ma khong them da giac
  3. Trai UV "LM" (smart project), nuong DIFFUSE (truc tiep + gian tiep + mau) bang Cycles (GPU neu co),
     nuong het tren vat lieu goc roi moi thay (tranh tinh anh sang doi 2 lan)
  4. Chinh do sang chung theo muc dau tien, ghi anh 8-bit sRGB, thay vat lieu bang 1 vat lieu "LM_<obj>"
     (Base Color = anh nuong), danh dau custom prop "baked". Web (campusModel.js) thay bang
     MeshBasicMaterial: hien dung mau da nuong, khong tinh den lai.
  5. Tra lai den/world nhu cu.
"""

import bpy
import math
import numpy as np
from mathutils import Vector

# (ten object, hoac tien to ket thuc bang "_" = moi object goc co ten bat dau nhu vay; px/m; ban kinh bo canh m)
# Object con (DET_) dung ban kinh nho hon (chi tiet mong, bo canh lon bi meo).
# Muc dau tien la "chuan do sang": do sang chung tinh theo no de moi phan khop mau nhau.
# Cay (TREE_) va kinh (*_glass) khong nuong: van chieu sang thoi gian thuc.
LIGHTBAKE = [
    ("BLD_B", 10, 0.15),
    ("PLAZA_B", 10, 0.05),
    ("GND_", 4.6, 0),
    ("PATH_", 4.6, 0),
]
DETAIL_BEVEL = 0.04
MAX_SIZE = 2048
SAMPLES = 256
SKIP_SUFFIX = ("_glass",)

# Kieu anh sang. sun_dir: huong toi mat troi (Blender); phai khop src/world/lighting.js (three x,y,z = Blender x,z,-y)
LIGHT = "sang"   # chu du an chon 19/11
PRESETS = {
    "trua": dict(sun_dir=(120.0, -80.0, 160.0), sun_color=(1.0, 0.90, 0.76), sun_strength=4.0,
                 sky_color=(0.50, 0.66, 0.95), sky_strength=0.45, white=0.80),
    # buoi sang: nang thap (~26 do) phia dong, trang am; bong kha dai, troi xanh trong
    "sang": dict(sun_dir=(150.0, -60.0, 80.0), sun_color=(1.0, 0.85, 0.66), sun_strength=4.5,
                 sky_color=(0.48, 0.64, 1.0), sky_strength=0.55, white=0.82),
    # chieu vang: nang thap phia tay nam, mau cam; bong dai nga xanh (anh sang troi)
    "chieu": dict(sun_dir=(-150.0, -50.0, 50.0), sun_color=(1.0, 0.60, 0.32), sun_strength=5.0,
                  sky_color=(0.42, 0.52, 0.95), sky_strength=0.55, white=0.85),
}
SUN_ANGLE = 4.0                   # do: mat troi rong hon -> mep bong mem
EXPORT_COLLECTIONS = ["Buildings", "Ground", "Paths", "Deco", "Gameplay", "Props"]


def log(msg):
    print("[UIT3D] " + msg, flush=True)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def round64(n):
    """Lam tron len boi so 64 (WebGL2 dung duoc anh khong phai luy thua 2, khong phi cho nhu ep len 2^n)."""
    return int(math.ceil(max(n, 1) / 64)) * 64


def setup_device(scn):
    scn.render.engine = "CYCLES"
    scn.cycles.samples = SAMPLES
    scn.cycles.use_denoising = False
    scn.cycles.max_bounces = 6
    scn.cycles.diffuse_bounces = 4
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for t in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = t
            prefs.get_devices()
            devs = [d for d in prefs.devices if d.type == t]
            if devs:
                for d in prefs.devices:
                    d.use = d.type == t
                scn.cycles.device = "GPU"
                log(f"Nuong bang GPU {t}: {devs[0].name}")
                return
        except Exception:  # noqa: BLE001
            pass
    scn.cycles.device = "CPU"
    log("Nuong bang CPU")


def setup_light(scn):
    """Dat mat troi + mau troi tam thoi. Tra ve ham tra lai nhu cu."""
    P = PRESETS[LIGHT]
    data = bpy.data.lights.new("LB_Sun", "SUN")
    data.energy = P["sun_strength"]
    data.color = P["sun_color"]
    data.angle = math.radians(SUN_ANGLE)
    sun = bpy.data.objects.new("LB_Sun", data)
    scn.collection.objects.link(sun)
    sun.rotation_euler = Vector(P["sun_dir"]).normalized().to_track_quat("Z", "Y").to_euler()
    # den co san trong file (neu co) tat khi nuong
    lights = [(o, o.hide_render) for o in scn.objects if o.type == "LIGHT" and o is not sun]
    for o, _ in lights:
        o.hide_render = True
    # world
    w = scn.world
    bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None) if w else None
    old_bg = (tuple(bg.inputs["Color"].default_value), bg.inputs["Strength"].default_value) if bg else None
    if bg:
        bg.inputs["Color"].default_value = (*P["sky_color"], 1.0)
        bg.inputs["Strength"].default_value = P["sky_strength"]
    # an object khong xuat ra web (anh ve tinh REF_ ...) de khong che nang / doi sang sai
    keep = set()
    for cname in EXPORT_COLLECTIONS:
        c = bpy.data.collections.get(cname)
        if c:
            keep.update(o.name for o in c.all_objects)
    hidden = [(o, o.hide_render) for o in scn.objects if o.type == "MESH" and o.name not in keep]
    for o, _ in hidden:
        o.hide_render = True

    def restore():
        bpy.data.objects.remove(sun)
        bpy.data.lights.remove(data)
        for o, h in lights + hidden:
            o.hide_render = h
        if bg:
            bg.inputs["Color"].default_value = old_bg[0]
            bg.inputs["Strength"].default_value = old_bg[1]

    return restore


# Vat lieu goc + chi so vat lieu tung mat luu trong Text "LB_store" (JSON), khong luu o custom prop
# vi custom prop bi xuat ra glb (extras) lam nang file.
def store():
    import json
    t = bpy.data.texts.get("LB_store") or bpy.data.texts.new("LB_store")
    try:
        return t, json.loads(t.as_string() or "{}")
    except ValueError:
        return t, {}


def save_store(t, data):
    import json
    t.from_string(json.dumps(data))


def original_materials(o, data):
    """Chay lai tren object da nuong: lay lai vat lieu goc da luu."""
    rec = data.get(o.name)
    if not rec:
        return
    me = o.data
    me.materials.clear()
    for n in rec["mats"]:
        me.materials.append(bpy.data.materials.get(n))
    me.polygons.foreach_set("material_index", rec["index"])
    if "LM" in me.uv_layers:
        me.uv_layers.remove(me.uv_layers["LM"])


def lightmap_uv(o, size):
    me = o.data
    lay = me.uv_layers.get("LM") or me.uv_layers.new(name="LM")
    me.uv_layers.active = lay
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=6.0 / size, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_materials(o, img, bevel):
    """Ban sao vat lieu de nuong: chen Bevel + node anh dang chon. Tra ve danh sach ban sao."""
    temp = []
    for i, src in enumerate(o.data.materials):
        m = src.copy()
        m.name = f"LBTMP_{src.name}@{o.name}"
        o.data.materials[i] = m
        temp.append(m)
        nt = m.node_tree
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bevel > 0 and bsdf and not bsdf.inputs["Normal"].is_linked:
            bev = nt.nodes.new("ShaderNodeBevel")
            bev.samples = 8
            bev.inputs["Radius"].default_value = bevel
            nt.links.new(bev.outputs["Normal"], bsdf.inputs["Normal"])
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        for x in nt.nodes:
            x.select = x == tex
        nt.nodes.active = tex
    return temp


def final_material(o, img8):
    name = f"LM_{o.name}"
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 1.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img8
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "LM"
    nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def main():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scn = bpy.context.scene
    old_engine = scn.render.engine
    setup_device(scn)
    restore = setup_light(scn)
    log(f"Anh sang: {LIGHT}")
    try:
        # danh sach (object, px/m, ban kinh bo canh)
        # chi object duoc xuat ra web (bo BLD_B_goc, REF_...); moi object chi lay 1 lan (BLD_B khop ca "BLD_")
        export = set()
        for cname in EXPORT_COLLECTIONS:
            c = bpy.data.collections.get(cname)
            if c:
                export.update(o.name for o in c.all_objects)
        objs, seen = [], set()
        for key, density, bevel in LIGHTBAKE:
            roots = ([o for o in scn.objects if o.name.startswith(key) and o.parent is None] if key.endswith("_")
                     else [o for o in [bpy.data.objects.get(key)] if o])
            roots = [r for r in roots if r.name in export]
            if not roots:
                log(f"Khong thay {key}")
            for r in roots:
                for o in [r] + list(r.children_recursive):
                    if o.type == "MESH" and not o.name.endswith(SKIP_SUFFIX) and o.name not in seen:
                        seen.add(o.name)
                        objs.append((o, density, bevel if o is r else min(bevel, DETAIL_BEVEL)))
        log(f"Nuong {len(objs)} object")

        # 1. nuong het tren vat lieu GOC (chua thay vat lieu nuong: tranh object nuong sau "thay" anh
        #    da nuong cua object truoc -> anh sang doi bi tinh 2 lan)
        raw = {}
        text, data = store()
        for o, density, bevel in objs:
            original_materials(o, data)
            me = o.data
            idx = [0] * len(me.polygons)
            me.polygons.foreach_get("material_index", idx)
            data[o.name] = {"mats": [m.name for m in me.materials], "index": idx}
            for m in me.materials:
                m.use_fake_user = True  # khong bi xoa khi luu file du khong con object nao dung
            save_store(text, data)
            area = sum(p.area for p in me.polygons)
            size = min(MAX_SIZE, max(128, round64(math.sqrt(area) * density / 0.7)))
            lightmap_uv(o, size)
            iname = f"LMraw_{o.name}"
            old = bpy.data.images.get(iname)
            if old:
                bpy.data.images.remove(old)
            img = bpy.data.images.new(iname, size, size, alpha=False, float_buffer=True)
            temp = bake_materials(o, img, bevel)
            for x in bpy.context.view_layer.objects:
                x.select_set(False)
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            me.uv_layers.active = me.uv_layers["LM"]
            bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT", "COLOR"},
                                margin=16, margin_type="EXTEND", use_clear=True)
            # tra vat lieu goc ngay (object nuong sau thay dung mau goc)
            for i, n in enumerate(data[o.name]["mats"]):
                me.materials[i] = bpy.data.materials.get(n)
            for m in temp:
                bpy.data.materials.remove(m)
            raw[o.name] = img
            log(f"   {o.name}: nuong {size}px")

        # 2. do sang chung (theo muc dau tien), de cac phan khop mau nhau
        ref = np.array(raw[objs[0][0].name].pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
        lum = ref @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        scale = PRESETS[LIGHT]["white"] / max(float(np.percentile(lum, 99.5)), 1e-4)
        log(f"   do sang x{scale:.2f}")

        # 3. ghi anh 8-bit + thay vat lieu
        for o, _, _ in objs:
            img = raw[o.name]
            w, h = img.size
            px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
            rgb = to_srgb(px[..., :3] * scale)
            name8 = f"LM_{o.name}"
            old = bpy.data.images.get(name8)
            if old:
                bpy.data.images.remove(old)
            img8 = bpy.data.images.new(name8, w, h, alpha=False)
            out = np.concatenate([rgb, np.ones((h, w, 1), np.float32)], axis=-1)
            img8.pixels.foreach_set(out.astype(np.float32).ravel())
            img8.pack()
            # thay vat lieu: 1 vat lieu duy nhat, UV LM lam kenh 0
            me = o.data
            me.materials.clear()
            me.materials.append(final_material(o, img8))
            me.polygons.foreach_set("material_index", [0] * len(me.polygons))
            bpy.data.images.remove(img)
            for lay in [l for l in me.uv_layers if l.name != "LM"]:
                me.uv_layers.remove(lay)
            o["baked"] = 1
    finally:
        restore()
        scn.render.engine = old_engine
    log("HOAN TAT nuong anh sang. Chay uit_export.py de xuat.")


if __name__ == "__main__":
    main()
