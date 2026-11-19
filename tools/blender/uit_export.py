"""
UIT 3D - Buoc 4: Xuat file .glb cho web
=========================================
Chay trong file uit_blockout.blend (sau khi da chay uit_fix.py).

Script nay se:
  1. Dua cac lop mat dat ve dung do cao (sua neu lo keo nham)
  2. Xuat ca ZONE_* / ITEM_* (empty, collection Gameplay) cho web doc vi tri
     Bo qua anh ve tinh (collection Reference) - chi dung de tham chieu
  3. Xuat .glb co nen Draco vao thu muc web/public/models
  4. In dung luong file ra System Console

Cach chay: tab Scripting > Text > Open > chon file nay > bam nut Run Script.
"""

import bpy
import os

EXPORT_PATH = r"D:\uit3d\web\public\models\uit_campus.glb"

LAYER_Z = {
    "GND_Base": 0.0,
    "GND_Green": 0.10,
    "GND_Parking": 0.10,
    "GND_Water": 0.10,
    "PATH_Footway": 0.13,
    "PATH_Road": 0.15,
    "GND_Pitch": 0.17,
}
EXPORT_COLLECTIONS = ["Buildings", "Ground", "Paths", "Deco", "Gameplay", "Props"]


def log(msg):
    print("[UIT3D] " + msg, flush=True)


def main():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # 1. dua mat dat ve dung cho
    for name, z in LAYER_Z.items():
        o = bpy.data.objects.get(name)
        if o:
            o.location = (0.0, 0.0, z)
            o.rotation_euler = (0.0, 0.0, 0.0)
            o.scale = (1.0, 1.0, 1.0)

    # 2. chon dung cac object can xuat
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    count = 0
    for cname in EXPORT_COLLECTIONS:
        coll = bpy.data.collections.get(cname)
        if not coll:
            continue
        for o in coll.all_objects:
            if o.type in ("MESH", "EMPTY") and o.name in bpy.context.view_layer.objects:
                o.hide_set(False)
                o.select_set(True)
                count += 1
    log(f"Xuat {count} object (bo qua anh ve tinh)")

    folder = os.path.dirname(EXPORT_PATH)
    try:
        os.makedirs(folder, exist_ok=True)
        path = EXPORT_PATH
    except OSError:
        path = os.path.join(os.path.dirname(bpy.data.filepath) or os.path.expanduser("~"), "uit_campus.glb")
        log(f"Khong tao duoc {folder}, xuat vao {path}")

    common = dict(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_extras=True,       # giu ten va thong tin OSM
        export_materials="EXPORT",
    )
    try:
        bpy.ops.export_scene.gltf(**common,
                                  export_draco_mesh_compression_enable=True,
                                  export_draco_mesh_compression_level=6)
        log("Da nen Draco")
    except Exception as ex:  # noqa: BLE001
        log(f"Khong nen Draco duoc ({ex}), xuat ban khong nen")
        bpy.ops.export_scene.gltf(**common)

    size_mb = os.path.getsize(path) / 1024 / 1024
    log(f"HOAN TAT: {path} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
