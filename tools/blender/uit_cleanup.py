"""
UIT 3D - Buoc 2: Loc bo cac toa nha ngoai truong UIT
======================================================
Chay SAU uit_import.py, trong cung file Blender.

Script nay se:
  1. Tai ranh gioi khuon vien UIT tu OpenStreetMap
  2. Xoa cac toa nha nam ngoai ranh gioi (KHXH&NV, ky tuc xa, nha dan...)
  3. Ve duong ranh gioi truong (REF_CampusBoundary) de tham khao
  4. Chuyen goc nhin: nhin tu tren xuong, hien mau + anh ve tinh, zoom vao truong
  5. In danh sach toa nha giu lai ra System Console

Cach chay: tab Scripting > Text > Open > chon file nay > bam nut Run Script.
"""

import bpy
import bmesh
import json
import math
import urllib.parse
import urllib.request

# Phai trung voi uit_import.py
CENTER_LAT = 10.8700
CENTER_LON = 106.8030
HALF_SIZE_M = 450

NAME_KEYWORDS = ["công nghệ thông tin", "cong nghe thong tin", "information technology", "uit"]
FALLBACK_RADIUS_M = 220      # dung neu khong tim thay ranh gioi truong tren OSM
MARGIN_M = 3.0               # giu ca toa nam sat mep ranh gioi

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
USER_AGENT = "UIT3D-student-project/1.0 (Blender script)"

M_PER_DEG_LAT = 110574.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(CENTER_LAT))


def log(msg):
    print("[UIT3D] " + msg, flush=True)


def to_xy(lat, lon):
    return ((lon - CENTER_LON) * M_PER_DEG_LON, (lat - CENTER_LAT) * M_PER_DEG_LAT)


def bbox():
    dlat = HALF_SIZE_M / M_PER_DEG_LAT
    dlon = HALF_SIZE_M / M_PER_DEG_LON
    return (CENTER_LAT - dlat, CENTER_LON - dlon, CENTER_LAT + dlat, CENTER_LON + dlon)


def fetch_campus_areas():
    s, w, n, e = bbox()
    b = f"{s:.6f},{w:.6f},{n:.6f},{e:.6f}"
    query = f"""
[out:json][timeout:60];
(
  way["amenity"~"university|college"]({b});
  relation["amenity"~"university|college"]({b});
);
(._;>;);
out body;
"""
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    for server in OVERPASS_SERVERS:
        try:
            log(f"Dang tai ranh gioi truong tu {server}...")
            req = urllib.request.Request(server, data=data, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as ex:  # noqa: BLE001
            log(f"  Loi: {ex}")
    return None


def ring(node_ids, nodes):
    pts = [to_xy(*nodes[i]) for i in node_ids if i in nodes]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    return pts if len(pts) >= 3 else None


def join_ways(way_list):
    """Noi cac doan way (outer cua relation) thanh cac vong kin."""
    segs = [list(w) for w in way_list if len(w) >= 2]
    rings = []
    while segs:
        cur = segs.pop(0)
        changed = True
        while cur[0] != cur[-1] and changed:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == cur[-1]:
                    cur += s[1:]
                elif s[-1] == cur[-1]:
                    cur += list(reversed(s))[1:]
                elif s[-1] == cur[0]:
                    cur = s[:-1] + cur
                elif s[0] == cur[0]:
                    cur = list(reversed(s))[:-1] + cur
                else:
                    continue
                segs.pop(i)
                changed = True
                break
        if cur[0] == cur[-1]:
            rings.append(cur)
    return rings


def find_campus_polygons(osm):
    if not osm:
        return [], None
    nodes, ways, rels = {}, {}, []
    for el in osm.get("elements", []):
        if el["type"] == "node":
            nodes[el["id"]] = (el["lat"], el["lon"])
        elif el["type"] == "way":
            ways[el["id"]] = el
        elif el["type"] == "relation":
            rels.append(el)

    def matches(tags):
        text = " ".join(str(tags.get(k, "")) for k in ("name", "name:vi", "name:en", "short_name", "alt_name")).lower()
        return any(k in text for k in NAME_KEYWORDS)

    polys, label = [], None
    for w in ways.values():
        tags = w.get("tags", {})
        if tags and matches(tags):
            p = ring(w.get("nodes", []), nodes)
            if p:
                polys.append(p)
                label = tags.get("name")
    for r in rels:
        tags = r.get("tags", {})
        if matches(tags):
            outer = [ways[m["ref"]]["nodes"] for m in r.get("members", [])
                     if m["type"] == "way" and m.get("role") in ("outer", "") and m["ref"] in ways]
            for rr in join_ways(outer):
                p = ring(rr, nodes)
                if p:
                    polys.append(p)
                    label = tags.get("name")
    return polys, label


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def dist_to_poly(x, y, poly):
    best = float("inf")
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / L))
        best = min(best, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return best


def footprint_center(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    if not vs:
        return None
    return (sum(v.x for v in vs) / len(vs), sum(v.y for v in vs) / len(vs))


def keep_building(c, polys):
    if polys:
        return any(point_in_poly(c[0], c[1], p) or dist_to_poly(c[0], c[1], p) <= MARGIN_M for p in polys)
    return math.hypot(c[0], c[1]) <= FALLBACK_RADIUS_M


def draw_boundary(polys):
    coll = bpy.data.collections.get("Reference")
    if coll is None:
        coll = bpy.data.collections.new("Reference")
        bpy.context.scene.collection.children.link(coll)
    old = bpy.data.objects.get("REF_CampusBoundary")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    bm = bmesh.new()
    for p in polys:
        vs = [bm.verts.new((x, y, 0.3)) for x, y in p]
        for i in range(len(vs)):
            bm.edges.new((vs[i], vs[(i + 1) % len(vs)]))
    me = bpy.data.meshes.new("REF_CampusBoundary")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("REF_CampusBoundary", me)
    coll.objects.link(obj)
    obj.show_in_front = True
    obj.color = (1.0, 0.2, 0.2, 1.0)
    return obj


def setup_view(kept):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in kept:
        o.select_set(True)
    if kept:
        bpy.context.view_layer.objects.active = kept[0]
    screen = bpy.context.screen
    if not screen:
        return
    for area in screen.areas:
        if area.type != "VIEW_3D":
            continue
        space = area.spaces.active
        space.shading.type = "MATERIAL"
        space.clip_end = 5000
        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        if region is None:
            continue
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.view3d.view_axis(type="TOP")
            if kept:
                bpy.ops.view3d.view_selected()


def main():
    bld = bpy.data.collections.get("Buildings")
    if bld is None or len(bld.objects) == 0:
        raise RuntimeError("Khong thay collection 'Buildings'. Hay chay uit_import.py truoc.")

    polys, label = find_campus_polygons(fetch_campus_areas())
    if polys:
        log(f"Tim thay ranh gioi truong: {label} ({len(polys)} vung)")
        draw_boundary(polys)
    else:
        log(f"KHONG tim thay ranh gioi truong tren OSM. Giu cac toa trong ban kinh {FALLBACK_RADIUS_M} m quanh tam.")

    kept, removed = [], 0
    for obj in list(bld.objects):
        if obj.type != "MESH":
            continue
        c = footprint_center(obj)
        if c and keep_building(c, polys):
            kept.append(obj)
        else:
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1

    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)

    log(f"Da xoa {removed} toa ngoai truong, giu lai {len(kept)} toa:")
    for o in sorted(kept, key=lambda o: o.name):
        levels = o.get("osm_building_levels", "?")
        log(f"   {o.name:30s} cao {o.dimensions.z:5.1f} m  (so tang tren OSM: {levels})")

    try:
        setup_view(kept)
    except Exception as ex:  # noqa: BLE001
        log(f"(Khong chinh duoc goc nhin: {ex})")
    log("HOAN TAT. Nho Ctrl + S de luu file.")


if __name__ == "__main__":
    main()
