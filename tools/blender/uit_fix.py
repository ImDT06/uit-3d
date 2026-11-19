"""
UIT 3D - Buoc 3: Don dep, dat ten, chinh chieu cao
====================================================
Chay SAU uit_cleanup.py, trong cung file Blender.

  1. Xoa cac toa khong thuoc UIT (danh sach DELETE)
  2. Doi ten cho gon (D_2 -> D, E_2 -> E, khoi chua co ten -> X1, X2...)
  3. Chinh chieu cao theo so tang trong bang FLOORS
  4. In bang chieu cao ra System Console

SUA BANG FLOORS ben duoi khi biet so tang that cua tung toa
(None = giu chieu cao hien tai), roi chay lai script bao nhieu lan cung duoc.

Cach chay: tab Scripting > Text > Open > chon file nay > bam nut Run Script.
"""

import bpy

FLOOR_HEIGHT = 3.5      # m moi tang
ROOF_EXTRA = 1.0        # m cong them cho lan can / tum mai

DELETE = [
    "BLD_B3",
    "BLD_Nhà_thi_đấu_ĐH_KHXH_NV",   # khoi tron lon ben trai
    "BLD_X1",                       # KTX Dai hoc An ninh, ngoai truong
]

RENAME = {
    "BLD_D_2": "BLD_D",
    "BLD_E_2": "BLD_E",
    "BLD_Căn_tin_UIT": "BLD_CanTin",
    "BLD_X3": "BLD_CanTin2",
    "BLD_X4": "BLD_ChotBaoVe",
}

# So tang tung toa. None = giu nguyen chieu cao hien tai.
# Di quanh truong dem tang roi dien vao day.
FLOORS = {
    "BLD_A": 3,
    "BLD_B": 9,         # theo OSM
    "BLD_C": 3,
    "BLD_D": 1,
    "BLD_E": 12,        # theo OSM
    "BLD_CanTin": 2,    # theo OSM
    "BLD_CanTin2": 1,
    "BLD_ChotBaoVe": 1,
    "BLD_X2": 1,        # o nho tren bai co canh toa A
}

# Toa can tim: script se chon va zoom man hinh vao toa nay
FOCUS = None


# Do cao (m) cua cac lop mat dat, cach nhau vai cm de khong bi vet soc
LAYER_Z = {
    "GND_Base": 0.0,
    "GND_Green": 0.10,
    "GND_Parking": 0.10,
    "GND_Water": 0.10,
    "PATH_Footway": 0.13,
    "PATH_Road": 0.15,
    "GND_Pitch": 0.17,
}


def log(msg):
    print("[UIT3D] " + msg, flush=True)


def set_height(obj, height):
    me = obj.data
    if not me.vertices:
        return
    zmin = min(v.co.z for v in me.vertices)
    zmax = max(v.co.z for v in me.vertices)
    if zmax - zmin < 1e-4:
        return
    for v in me.vertices:
        if v.co.z > zmin + (zmax - zmin) * 0.5:
            v.co.z = zmin + height
    me.update()


def main():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    bld = bpy.data.collections.get("Buildings")
    if bld is None:
        raise RuntimeError("Khong thay collection 'Buildings'.")

    # 1. xoa
    for name in DELETE:
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
            log(f"Da xoa {name}")

    # 2. doi ten
    for old, new in RENAME.items():
        obj = bpy.data.objects.get(old)
        if obj and not bpy.data.objects.get(new):
            obj.name = new
            obj.data.name = new
            log(f"Doi ten {old} -> {new}")

    # khoi chua co ten (ten chi la so OSM) -> X1, X2... xep tu Bac xuong Nam, Tay sang Dong
    unnamed = [o for o in bld.objects if o.name[4:].isdigit()]
    unnamed.sort(key=lambda o: (-round(o.matrix_world.translation.y + sum(v.co.y for v in o.data.vertices) / max(len(o.data.vertices), 1)),
                                sum(v.co.x for v in o.data.vertices) / max(len(o.data.vertices), 1)))
    k = 1
    for o in unnamed:
        while bpy.data.objects.get(f"BLD_X{k}"):
            k += 1
        log(f"Doi ten {o.name} -> BLD_X{k}")
        o.name = f"BLD_X{k}"
        o.data.name = o.name
        k += 1

    # doi ten lan 2 (cho cac khoi X vua duoc dat ten)
    for old, new in RENAME.items():
        obj = bpy.data.objects.get(old)
        if obj and not bpy.data.objects.get(new):
            obj.name = new
            obj.data.name = new
            log(f"Doi ten {old} -> {new}")

    # 3. chieu cao
    for name, floors in FLOORS.items():
        obj = bpy.data.objects.get(name)
        if obj and floors:
            set_height(obj, floors * FLOOR_HEIGHT + ROOF_EXTRA)

    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)

    # 4. tach cac lop mat dat xa nhau hon de het vet soc (z-fighting)
    for o in bpy.data.objects:
        if o.name.startswith("REF_sat_"):
            o.location.z = 0.05
    for name, z in LAYER_Z.items():
        o = bpy.data.objects.get(name)
        if o:
            o.location.z = z
    try:
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.clip_start = 0.1
                space.clip_end = 3000
                space.shading.type = "MATERIAL"
    except Exception:  # noqa: BLE001
        pass

    # 5. bao cao + chon toa X de de nhan ra
    log("Bang toa nha hien tai:")
    for o in sorted(bld.objects, key=lambda o: o.name):
        h = max((v.co.z for v in o.data.vertices), default=0) - min((v.co.z for v in o.data.vertices), default=0)
        log(f"   {o.name:15s} cao {h:5.1f} m   so tang dat: {FLOORS.get(o.name)}")
    target = bpy.data.objects.get(FOCUS) if FOCUS else None
    for o in bpy.context.view_layer.objects:
        o.select_set(o == target)
    if target:
        bpy.context.view_layer.objects.active = target
        try:
            for area in bpy.context.screen.areas:
                if area.type == "VIEW_3D":
                    region = next(r for r in area.regions if r.type == "WINDOW")
                    with bpy.context.temp_override(area=area, region=region):
                        bpy.ops.view3d.view_selected()
                        bpy.ops.view3d.zoom(delta=-3)
        except Exception:  # noqa: BLE001
            pass
        log(f"Man hinh dang zoom vao {FOCUS} (vien cam). Nhan Home de xem lai toan canh.")
    log("HOAN TAT. Nho Ctrl + S.")


if __name__ == "__main__":
    main()
