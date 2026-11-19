"""
UIT 3D - Tu dong lam Phan 2 (thay cho BlenderGIS)
====================================================
Script nay se:
  1. Xoa scene hien tai, dat don vi met
  2. Tai du lieu OpenStreetMap quanh truong UIT (toa nha, san, co, loi di)
  3. Dung khoi toa nha (cao theo so tang neu OSM co, khong thi 10 m)
  4. Tao san bong, mang co, bai xe, loi di (da co be rong)
  5. Ghep anh ve tinh ESRI lam nen tham chieu (collection Reference)
  6. Chia vao cac collection: Buildings, Ground, Paths, Reference

Cach chay:
  - Mo file Blender MOI (File > New > General) vi script se xoa het scene.
  - Window > Toggle System Console (de xem tien trinh).
  - Workspace "Scripting" > Text > Open > chon file nay > bam nut Run Script (hoac Alt + P).
  - Blender co the dung 1-3 phut khi tai du lieu. Dung tat.
"""

import bpy
import bmesh
import json
import math
import os
import time
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# CAU HINH - sua o day neu can
# ---------------------------------------------------------------------------
CENTER_LAT = 10.8700        # tam khuon vien UIT
CENTER_LON = 106.8030
HALF_SIZE_M = 450           # lay du lieu trong o vuong +-450 m quanh tam

DEFAULT_HEIGHT = 10.0       # m, toa nha khong co du lieu so tang
FLOOR_HEIGHT = 3.5          # m moi tang

LOAD_SATELLITE = True       # tai anh ve tinh lam nen
SATELLITE_ZOOM = 18         # 18 = vua du ro; 19 = net hon nhung tai lau gap 4 lan
CACHE_DIR = r"D:\uit3d\gis_cache"   # thu muc luu anh ve tinh; khong co o D thi tu dung thu muc tam

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
ESRI_TILE_URL = ("https://server.arcgisonline.com/ArcGIS/rest/services/"
                 "World_Imagery/MapServer/tile/{z}/{y}/{x}")
USER_AGENT = "UIT3D-student-project/1.0 (Blender script)"

# be rong loi di theo loai highway (m)
PATH_WIDTH = {
    "footway": 2.0, "path": 2.0, "pedestrian": 3.0, "steps": 2.0, "cycleway": 2.0,
    "service": 4.0, "living_street": 5.0, "residential": 6.0, "unclassified": 6.0,
    "tertiary": 8.0, "secondary": 10.0, "primary": 12.0, "trunk": 16.0,
    "trunk_link": 8.0, "primary_link": 8.0, "secondary_link": 7.0,
}

# do cao cac lop mat dat (tranh nhap nhay)
Z_SATELLITE = 0.005         # nam tren GND_Base de nhin thay, duoi co/loi di
Z_BASE = 0.0
Z_GREEN = 0.01
Z_PATH_MINOR = 0.02
Z_PATH_ROAD = 0.025
Z_PITCH = 0.03

COLORS = {
    "building": (0.92, 0.89, 0.82, 1),
    "base": (0.55, 0.55, 0.50, 1),
    "green": (0.45, 0.68, 0.35, 1),
    "pitch": (0.20, 0.55, 0.30, 1),
    "parking": (0.60, 0.60, 0.60, 1),
    "water": (0.30, 0.55, 0.80, 1),
    "footway": (0.85, 0.83, 0.78, 1),
    "road": (0.30, 0.30, 0.32, 1),
}

# ---------------------------------------------------------------------------
# Toa do: lat/lon -> met (phep chieu phang cuc bo quanh tam)
# ---------------------------------------------------------------------------
M_PER_DEG_LAT = 110574.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(CENTER_LAT))


def to_xy(lat, lon):
    return ((lon - CENTER_LON) * M_PER_DEG_LON, (lat - CENTER_LAT) * M_PER_DEG_LAT)


def bbox():
    dlat = HALF_SIZE_M / M_PER_DEG_LAT
    dlon = HALF_SIZE_M / M_PER_DEG_LON
    return (CENTER_LAT - dlat, CENTER_LON - dlon, CENTER_LAT + dlat, CENTER_LON + dlon)


def log(msg):
    print("[UIT3D] " + msg, flush=True)


# ---------------------------------------------------------------------------
# Mang
# ---------------------------------------------------------------------------
def http_get(url, data=None, timeout=90):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_osm():
    s, w, n, e = bbox()
    b = f"{s:.6f},{w:.6f},{n:.6f},{e:.6f}"
    query = f"""
[out:json][timeout:90];
(
  way["building"]({b});
  relation["building"]({b});
  way["highway"]({b});
  way["leisure"]({b});
  way["landuse"]({b});
  way["natural"]({b});
  way["amenity"="parking"]({b});
);
(._;>;);
out body;
"""
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    last_err = None
    for server in OVERPASS_SERVERS:
        for attempt in range(2):
            try:
                log(f"Dang tai OSM tu {server} (lan {attempt + 1})...")
                raw = http_get(server, data=data, timeout=120)
                result = json.loads(raw.decode("utf-8"))
                log(f"Tai xong: {len(result.get('elements', []))} phan tu")
                return result
            except Exception as ex:  # noqa: BLE001
                last_err = ex
                log(f"  Loi: {ex}. Thu lai sau 5 giay...")
                time.sleep(5)
    raise RuntimeError(f"Khong tai duoc du lieu OSM: {last_err}")


# ---------------------------------------------------------------------------
# Tien ich Blender
# ---------------------------------------------------------------------------
def clear_scene():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for item in list(block):
            if item.users == 0:
                block.remove(item)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    sc.unit_settings.length_unit = "METERS"


def get_collection(name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


_materials = {}


def material(key):
    if key in _materials:
        return _materials[key]
    mat = bpy.data.materials.new("MAT_" + key)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = COLORS[key]
        bsdf.inputs["Roughness"].default_value = 0.9
    mat.diffuse_color = COLORS[key]
    _materials[key] = mat
    return mat


def new_object(name, bm, coll, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    coll.objects.link(obj)
    if mat is not None:
        me.materials.append(mat)
    return obj


def safe_name(text):
    keep = []
    for ch in text.strip():
        keep.append(ch if (ch.isalnum() or ch in "-_") else "_")
    return "".join(keep)[:40] or "noname"


# ---------------------------------------------------------------------------
# Hinh hoc
# ---------------------------------------------------------------------------
def ring_xy(node_ids, nodes):
    pts = []
    for nid in node_ids:
        nd = nodes.get(nid)
        if nd is None:
            return None
        pts.append(to_xy(nd[0], nd[1]))
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    # bo diem trung lien tiep
    clean = []
    for p in pts:
        if not clean or (abs(p[0] - clean[-1][0]) > 1e-4 or abs(p[1] - clean[-1][1]) > 1e-4):
            clean.append(p)
    return clean if len(clean) >= 3 else None


def signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def add_prism(bm, pts, z0, z1):
    """Them khoi lang tru (day pts, tu z0 den z1) vao bm."""
    if signed_area(pts) < 0:
        pts = list(reversed(pts))  # dua ve nguoc chieu kim dong ho
    bottom = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    try:
        bm.faces.new(list(reversed(bottom)))  # mat day huong xuong
        bm.faces.new(top)                      # mat mai huong len
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((bottom[i], bottom[j], top[j], top[i]))
    except ValueError:
        pass


def add_flat(bm, pts, z):
    if signed_area(pts) < 0:
        pts = list(reversed(pts))
    verts = [bm.verts.new((x, y, z)) for x, y in pts]
    try:
        bm.faces.new(verts)
    except ValueError:
        pass


def add_ribbon(bm, pts, width, z):
    """Bien duong ke thanh dai phang co be rong."""
    if len(pts) < 2:
        return
    half = width / 2.0
    left, right = [], []
    n = len(pts)
    for i in range(n):
        if i == 0:
            dx, dy = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == n - 1:
            dx, dy = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
        else:
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            bx, by = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            la, lb = math.hypot(ax, ay) or 1, math.hypot(bx, by) or 1
            dx, dy = ax / la + bx / lb, ay / la + by / lb
        l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l, dx / l
        scale = 1.0
        if 0 < i < n - 1:
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            la = math.hypot(ax, ay) or 1
            cos_half = abs(nx * (-ay / la) + ny * (ax / la))
            scale = 1.0 / max(cos_half, 0.5)  # gioi han goc nhon
        x, y = pts[i]
        left.append(bm.verts.new((x + nx * half * scale, y + ny * half * scale, z)))
        right.append(bm.verts.new((x - nx * half * scale, y - ny * half * scale, z)))
    for i in range(n - 1):
        try:
            bm.faces.new((right[i], right[i + 1], left[i + 1], left[i]))
        except ValueError:
            pass


def building_height(tags):
    h = tags.get("height")
    if h:
        try:
            return float(h.replace("m", "").strip())
        except ValueError:
            pass
    lv = tags.get("building:levels")
    if lv:
        try:
            return float(lv) * FLOOR_HEIGHT
        except ValueError:
            pass
    return DEFAULT_HEIGHT


def building_name(tags, osm_id, used):
    label = tags.get("name") or tags.get("ref") or tags.get("addr:housename")
    base = "BLD_" + (safe_name(label) if label else str(osm_id))
    name, k = base, 2
    while name in used:
        name, k = f"{base}_{k}", k + 1
    used.add(name)
    return name


# ---------------------------------------------------------------------------
# Dung tu du lieu OSM
# ---------------------------------------------------------------------------
GREEN_LANDUSE = {"grass", "meadow", "recreation_ground", "village_green", "forest"}
GREEN_NATURAL = {"grassland", "scrub", "wood", "tree_row", "heath"}
GREEN_LEISURE = {"park", "garden"}


def build_from_osm(osm):
    nodes, ways, relations = {}, {}, []
    for el in osm.get("elements", []):
        t = el.get("type")
        if t == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
        elif t == "way":
            ways[el["id"]] = el
        elif t == "relation":
            relations.append(el)

    c_bld = get_collection("Buildings")
    c_gnd = get_collection("Ground")
    c_path = get_collection("Paths")

    used_names = set()
    stats = {"buildings": 0, "green": 0, "pitch": 0, "parking": 0, "paths": 0}

    bm_green, bm_pitch, bm_parking, bm_water = (bmesh.new() for _ in range(4))
    bm_foot, bm_road = bmesh.new(), bmesh.new()

    def make_building(pts, tags, osm_id):
        bm = bmesh.new()
        h = building_height(tags)
        min_h = 0.0
        try:
            min_h = float(tags.get("min_height", 0) or 0)
        except ValueError:
            pass
        add_prism(bm, pts, min_h, max(h, min_h + 1))
        obj = new_object(building_name(tags, osm_id, used_names), bm, c_bld, material("building"))
        obj["osm_id"] = str(osm_id)
        for key in ("name", "ref", "building", "building:levels"):
            if key in tags:
                obj["osm_" + key.replace(":", "_")] = tags[key]
        stats["buildings"] += 1

    member_ways = set()
    for rel in relations:
        tags = rel.get("tags", {})
        if "building" not in tags:
            continue
        for m in rel.get("members", []):
            if m.get("type") == "way" and m.get("role") in ("outer", ""):
                w = ways.get(m["ref"])
                if not w:
                    continue
                member_ways.add(w["id"])
                nds = w.get("nodes", [])
                if len(nds) > 3 and nds[0] == nds[-1]:
                    pts = ring_xy(nds, nodes)
                    if pts:
                        make_building(pts, {**w.get("tags", {}), **tags}, rel["id"])

    for wid, w in ways.items():
        tags = w.get("tags", {})
        if not tags:
            continue
        nds = w.get("nodes", [])
        closed = len(nds) > 3 and nds[0] == nds[-1]

        if "building" in tags and wid not in member_ways:
            if closed:
                pts = ring_xy(nds, nodes)
                if pts:
                    make_building(pts, tags, wid)
            continue

        hw = tags.get("highway")
        if hw and tags.get("area") != "yes":
            line = []
            for nid in nds:
                nd = nodes.get(nid)
                if nd:
                    line.append(to_xy(nd[0], nd[1]))
            width = PATH_WIDTH.get(hw)
            if width is None or len(line) < 2:
                continue
            if width <= 3.0:
                add_ribbon(bm_foot, line, width, Z_PATH_MINOR)
            else:
                add_ribbon(bm_road, line, width, Z_PATH_ROAD)
            stats["paths"] += 1
            continue

        if not closed:
            continue
        pts = ring_xy(nds, nodes)
        if not pts:
            continue
        leisure, landuse, natural = tags.get("leisure"), tags.get("landuse"), tags.get("natural")
        if leisure in ("pitch", "track", "sports_centre"):
            add_flat(bm_pitch, pts, Z_PITCH)
            stats["pitch"] += 1
        elif leisure in GREEN_LEISURE or landuse in GREEN_LANDUSE or natural in GREEN_NATURAL:
            add_flat(bm_green, pts, Z_GREEN)
            stats["green"] += 1
        elif tags.get("amenity") == "parking":
            add_flat(bm_parking, pts, Z_GREEN)
            stats["parking"] += 1
        elif natural == "water" or landuse in ("basin", "reservoir"):
            add_flat(bm_water, pts, Z_GREEN)

    new_object("GND_Green", bm_green, c_gnd, material("green"))
    new_object("GND_Pitch", bm_pitch, c_gnd, material("pitch"))
    new_object("GND_Parking", bm_parking, c_gnd, material("parking"))
    new_object("GND_Water", bm_water, c_gnd, material("water"))
    new_object("PATH_Footway", bm_foot, c_path, material("footway"))
    new_object("PATH_Road", bm_road, c_path, material("road"))

    # mat dat nen phu het vung
    bm = bmesh.new()
    r = HALF_SIZE_M
    add_flat(bm, [(-r, -r), (r, -r), (r, r), (-r, r)], Z_BASE)
    new_object("GND_Base", bm, c_gnd, material("base"))

    # xoa object rong
    for obj in list(c_gnd.objects) + list(c_path.objects):
        if obj.type == "MESH" and len(obj.data.polygons) == 0:
            bpy.data.objects.remove(obj, do_unlink=True)
    return stats


# ---------------------------------------------------------------------------
# Anh ve tinh
# ---------------------------------------------------------------------------
def tile_xy(lat, lon, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    lat_r = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n)
    return x, y


def tile_corner(x, y, z):
    n = 2 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


def resolve_cache_dir():
    d = CACHE_DIR
    try:
        os.makedirs(d, exist_ok=True)
        return d
    except OSError:
        d = os.path.join(bpy.app.tempdir or os.path.expanduser("~"), "uit3d_tiles")
        os.makedirs(d, exist_ok=True)
        return d


def load_satellite():
    z = SATELLITE_ZOOM
    s, w, n, e = bbox()
    x0, y0 = tile_xy(n, w, z)
    x1, y1 = tile_xy(s, e, z)
    total = (x1 - x0 + 1) * (y1 - y0 + 1)
    log(f"Tai anh ve tinh: {total} manh (zoom {z})")
    cache = resolve_cache_dir()
    coll = get_collection("Reference")
    done = 0
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            path = os.path.join(cache, f"esri_{z}_{tx}_{ty}.jpg")
            if not os.path.exists(path):
                try:
                    raw = http_get(ESRI_TILE_URL.format(z=z, x=tx, y=ty), timeout=30)
                    with open(path, "wb") as f:
                        f.write(raw)
                except Exception as ex:  # noqa: BLE001
                    log(f"  Bo qua manh {tx},{ty}: {ex}")
                    continue
            lat_top, lon_left = tile_corner(tx, ty, z)
            lat_bot, lon_right = tile_corner(tx + 1, ty + 1, z)
            xl, yt = to_xy(lat_top, lon_left)
            xr, yb = to_xy(lat_bot, lon_right)

            bm = bmesh.new()
            uv = bm.loops.layers.uv.new("UVMap")
            v = [bm.verts.new(p) for p in ((xl, yb, Z_SATELLITE), (xr, yb, Z_SATELLITE),
                                           (xr, yt, Z_SATELLITE), (xl, yt, Z_SATELLITE))]
            face = bm.faces.new(v)
            for loop, co in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                loop[uv].uv = co

            mat = bpy.data.materials.new(f"MAT_sat_{tx}_{ty}")
            mat.use_nodes = True
            nt = mat.node_tree
            bsdf = nt.nodes.get("Principled BSDF")
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = bpy.data.images.load(path, check_existing=True)
            tex.extension = "EXTEND"
            if bsdf:
                nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
                bsdf.inputs["Roughness"].default_value = 1.0
            new_object(f"REF_sat_{tx}_{ty}", bm, coll, mat)
            done += 1
            if done % 10 == 0:
                log(f"  {done}/{total}")
    log(f"Xong anh ve tinh: {done}/{total} manh")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def setup_view():
    for area in bpy.context.screen.areas if bpy.context.screen else []:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.clip_end = 5000
                    space.shading.type = "MATERIAL" if LOAD_SATELLITE else "SOLID"
            region = next((r for r in area.regions if r.type == "WINDOW"), None)
            if region:
                with bpy.context.temp_override(area=area, region=region):
                    bpy.ops.view3d.view_all()


def main():
    if hasattr(bpy.app, "online_access") and not bpy.app.online_access:
        log("Canh bao: 'Allow Online Access' dang tat (Edit > Preferences > System > Network). "
            "Script van thu tai; neu loi mang thi bat muc nay roi chay lai.")
    t0 = time.time()
    clear_scene()
    osm = fetch_osm()
    stats = build_from_osm(osm)
    log(f"Da dung: {stats}")
    if LOAD_SATELLITE:
        try:
            load_satellite()
        except Exception as ex:  # noqa: BLE001
            log(f"Khong tai duoc anh ve tinh ({ex}). Bo qua, phan con lai van dung.")
    try:
        setup_view()
    except Exception:  # noqa: BLE001
        pass
    log(f"HOAN TAT sau {time.time() - t0:.0f} giay. Nho Ctrl + S de luu file.")


if __name__ == "__main__":
    main()
