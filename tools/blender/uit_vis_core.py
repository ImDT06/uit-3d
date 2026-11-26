"""
UIT 3D - Lop loi dac cho toa VIS_* (mo hinh lay tu ban MyUIT)
================================================================
Toa VIS_* chi la vo mong (san la tam phang, tuong tung mang roi, tang tret rong) nen nhin nhu giay.
Script nay dung them VIS_<toa>_core: khoi dac ngay sau mat tuong (~0,3 m), cao toi ngay duoi tung muc mai.
Web hien lop loi nay (bit tang tret trong, khe cua) va dung no lam khoi va cham.

Cach lam (moi toa):
  1. Ban do do cao nhin tu tren xuong (o 0,25 m) tu cac mat ngang cao > 2 m cua VIS_.
  2. Gom cac muc mai (dien tich >= 25 m2).
  3. Moi muc: vung mai (bo dai mong < 2 m) GIAO vung tuong bao: ve cac mat dung trong khoang cao do xuong
     mat bang, bit khe < ~3 m (cua, tang tret trong), lay phan ben trong. San/mai hien nho ra ngoai tuong
     nen khong lay theo mep san (se che mat cua so). Roi thu vao INSET.
  4. Do duong vien, lam tron (sai lech < 0,3 m), dun len thanh khoi bac thang.
Chay lai duoc: tu xoa VIS_*_core cu. Vat lieu tuong = vat lieu mat dung nhieu nhat cua toa.
Web (campusModel.js): co VIS_*_core thi dung no lam khoi va cham + chan camera thay cho than BLD_.
"""
import time
from collections import Counter

import bmesh
import bpy
import mathutils
import numpy as np

R = 0.25           # m, kich thuoc o ban do do cao
THIN = 1.0         # m, bo dai mong hon 2*THIN (ban cong, mai hat)
INSET = 0.3        # m, lui vao sau mat tuong
GAP = 1.5          # m, bit khe tuong rong toi 2*GAP (cua, tang tret trong) truoc khi lay phan ben trong
# rieng tung toa: bit ca cho lom sau (B: hanh lang ban cong giua cac khoi nho, mat truoc ho -> nhin tu tren thanh ho sau)
CLOSE = {"VIS_B": 4.0}
# rieng tung toa: bo cac muc mai thap hon (m) - B: muc 2,0/2,7/3,4 xep thanh bac, nhan vat leo len mai duoc
MIN_LEVEL = {"VIS_B": 4.0}
SIMPLIFY = 0.3     # m, sai lech toi da khi lam tron duong vien
MIN_LEVEL_AREA = 25.0


def log(msg):
    print("[UIT3D] " + msg, flush=True)


def erode(m, k):
    for _ in range(k):
        n = m.copy(); n[1:] &= m[:-1]; n[:-1] &= m[1:]; n[:, 1:] &= m[:, :-1]; n[:, :-1] &= m[:, 1:]; m = n
    return m


def dilate(m, k):
    for _ in range(k):
        n = m.copy(); n[1:] |= m[:-1]; n[:-1] |= m[1:]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]; m = n
    return m


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    d = b - a
    L = np.linalg.norm(d)
    dist = np.abs(np.cross(d, pts - a)) / L if L > 1e-9 else np.linalg.norm(pts - a, axis=1)
    i = int(dist.argmax())
    if dist[i] > eps:
        return np.vstack([rdp(pts[:i + 1], eps)[:-1], rdp(pts[i:], eps)])
    return np.array([a, b])


def loops_of(mask):
    """Duong vien vung o (toa do goc o), moi vong la mot mang diem."""
    m = np.pad(mask, 1)
    nxt = {}
    for j, i in zip(*np.nonzero(mask)):
        J, I = j + 1, i + 1
        if not m[J - 1, I]: nxt[(i + 1, j)] = (i, j)
        if not m[J + 1, I]: nxt[(i, j + 1)] = (i + 1, j + 1)
        if not m[J, I - 1]: nxt[(i, j)] = (i, j + 1)
        if not m[J, I + 1]: nxt[(i + 1, j + 1)] = (i + 1, j)
    loops, seen = [], set()
    for s in list(nxt):
        if s in seen:
            continue
        lp = [s]; seen.add(s); c = nxt.get(s)
        while c is not None and c != s and c not in seen:
            lp.append(c); seen.add(c); c = nxt.get(c)
        if len(lp) >= 4:
            loops.append(np.array(lp, float))
    return loops


def heightmap(V):
    me = V.data
    M = np.array(V.matrix_world)
    me.calc_loop_triangles()
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    nt = len(me.loop_triangles)
    tv = np.zeros(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get("vertices", tv); tv = tv.reshape(-1, 3)
    mi = np.zeros(nt, dtype=int); me.loop_triangles.foreach_get("material_index", mi)
    a, b, c = co[tv[:, 0]], co[tv[:, 1]], co[tv[:, 2]]
    n = np.cross(b - a, c - a); ln = np.linalg.norm(n, axis=1) + 1e-12
    ar = ln / 2; nz = np.abs(n[:, 2]) / ln; zc = (a[:, 2] + b[:, 2] + c[:, 2]) / 3
    wall = Counter()
    for k, x in zip(mi[nz < 0.2], ar[nz < 0.2]):
        wall[k] += x
    wall_mat = me.materials[wall.most_common(1)[0][0]] if wall else None
    lo = co[:, :2].min(0) - 2; hi = co[:, :2].max(0) + 2
    nx, ny = np.ceil((hi - lo) / R).astype(int)
    H = np.full((ny, nx), -1.0)
    for i in np.where((nz > 0.9) & (ar > 0.05) & (zc > 2.0))[0]:
        T = np.array([a[i], b[i], c[i]])
        x0, y0 = ((T[:, :2].min(0) - lo) / R).astype(int)
        x1, y1 = ((T[:, :2].max(0) - lo) / R).astype(int) + 1
        gx, gy = np.meshgrid(lo[0] + (np.arange(x0, x1) + .5) * R, lo[1] + (np.arange(y0, y1) + .5) * R)
        p, q, r = T
        d1 = (gx - q[0]) * (p[1] - q[1]) - (p[0] - q[0]) * (gy - q[1])
        d2 = (gx - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (gy - r[1])
        d3 = (gx - p[0]) * (r[1] - p[1]) - (r[0] - p[0]) * (gy - p[1])
        ins = ~(((d1 < 0) | (d2 < 0) | (d3 < 0)) & ((d1 > 0) | (d2 > 0) | (d3 > 0)))
        sub = H[y0:y1, x0:x1]; sub[ins] = np.maximum(sub[ins], zc[i])
    w = (nz < 0.2) & (ar > 0.05)
    walls = np.stack([a[w], b[w], c[w]], 1)  # (n, 3 dinh, xyz)
    return H, lo, float(co[:, 2].min()), wall_mat, walls


def wall_inside(walls, zlo, zhi, shape, lo, GAP=GAP):
    """Vung nam trong tuong bao (cac mat dung cat qua khoang cao zlo..zhi), da bit khe < 2*GAP."""
    zmin, zmax = walls[:, :, 2].min(1), walls[:, :, 2].max(1)
    sel = walls[(zmin < zhi) & (zmax > zlo)]
    Wm = np.zeros(shape, bool)
    for T in sel:
        for p, q in ((T[0], T[1]), (T[1], T[2]), (T[2], T[0])):
            k = int(np.hypot(*(q[:2] - p[:2])) / (R / 2)) + 2
            t = np.linspace(0, 1, k)[:, None]
            ij = ((p[:2] + (q[:2] - p[:2]) * t - lo) / R).astype(int)
            Wm[ij[:, 1].clip(0, shape[0] - 1), ij[:, 0].clip(0, shape[1] - 1)] = True
    G = int(GAP / R)
    free = ~dilate(Wm, G)
    out = np.zeros(shape, bool); out[0, :] = out[-1, :] = out[:, 0] = out[:, -1] = True; out &= free
    while True:
        n = dilate(out, 1) & free
        if n.sum() == out.sum():
            break
        out = n
    return erode(~out, G)


def cap_tris(polys):
    """Tam giac phu vung gioi han boi cac vong (vong ngoai + lo), tra ve chi so dinh theo thu tu noi cac vong."""
    tb = bmesh.new()
    vs = [tb.verts.new(p) for poly in polys for p in poly]
    off = 0
    for poly in polys:
        k = len(poly)
        for s in range(k):
            try:
                tb.edges.new((vs[off + s], vs[off + (s + 1) % k]))
            except ValueError:
                pass
        off += k
    tb.verts.index_update()
    res = bmesh.ops.triangle_fill(tb, use_beauty=True, use_dissolve=False, edges=tb.edges[:], normal=(0, 0, 1))
    tris = [[v.index for v in f.verts] for f in res["geom"] if isinstance(f, bmesh.types.BMFace)]
    tb.free()
    return tris


def build_core(V):
    t0 = time.time()
    H, lo, base, wall_mat, walls = heightmap(V)
    vals = np.sort(H[H > 0])[::-1]
    levels = []
    for v in vals:
        if not levels or abs(levels[-1][0] - v) > 0.6:
            levels.append([v, 0])
        levels[-1][1] += 1
    levels = sorted(l[0] for l in levels if l[1] * R * R >= MIN_LEVEL_AREA and l[0] >= MIN_LEVEL.get(V.name, 0))
    K, INS = int(THIN / R), int(INSET / R)
    masks = []
    for L in levels:
        z0 = masks[-1][0] if masks else base
        roof = erode(dilate(erode(H >= L - 0.4, K), K), 1)
        cl = CLOSE.get(V.name, 0)
        if cl:
            c = int(cl / R); roof = erode(dilate(roof, c), c)
        m = erode(roof & wall_inside(walls, z0 + 0.3, L - 0.7, H.shape, lo, max(GAP, cl)), INS)
        if m.sum() * R * R >= 15:
            masks.append((L - 0.4, m))
    bm = bmesh.new()
    for idx, (top, m) in enumerate(masks):
        z0 = base if idx == 0 else masks[idx - 1][0]
        if top <= z0 + 0.2:
            continue
        polys = []
        for lp in loops_of(m):
            pts = rdp(np.vstack([lp, lp[:1]]), SIMPLIFY / R)[:-1]
            if len(pts) >= 3:
                polys.append([mathutils.Vector((lo[0] + x * R, lo[1] + y * R, 0)) for x, y in pts])
        if not polys:
            continue
        # nap tren/duoi: triangle_fill hieu duoc lo (san trong); tessellate_polygon thi lap kin lo
        tris = cap_tris(polys)
        flat = [p for poly in polys for p in poly]
        vb = [bm.verts.new((p.x, p.y, z0)) for p in flat]
        vt = [bm.verts.new((p.x, p.y, top)) for p in flat]
        for t in tris:
            try:
                bm.faces.new([vt[t[0]], vt[t[1]], vt[t[2]]]); bm.faces.new([vb[t[2]], vb[t[1]], vb[t[0]]])
            except ValueError:
                pass
        off = 0
        for poly in polys:
            k = len(poly)
            for s in range(k):
                i0, i1 = off + s, off + (s + 1) % k
                try:
                    bm.faces.new([vb[i0], vb[i1], vt[i1], vt[i0]])
                except ValueError:
                    pass
            off += k
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    name = V.name + "_core"
    old = bpy.data.objects.get(name)
    if old:
        me_old = old.data; bpy.data.objects.remove(old, do_unlink=True); bpy.data.meshes.remove(me_old)
    cm = bpy.data.meshes.new(name); bm.to_mesh(cm); bm.free()
    if wall_mat:
        cm.materials.append(wall_mat)
    B = V.parent
    ob = bpy.data.objects.new(name, cm)
    for col in V.users_collection:
        col.objects.link(ob)
    if B:
        ob.parent = B; ob.matrix_parent_inverse = B.matrix_world.inverted()
    log(f"{name}: {len(masks)} muc ({', '.join(f'{t:.1f}' for t, _ in masks)} m), {len(cm.polygons)} mat, "
        f"tuong {wall_mat.name if wall_mat else '-'}, {time.time() - t0:.1f}s")


def main():
    for V in [o for o in bpy.data.objects if o.name.startswith("VIS_") and not o.name.endswith("_core") and o.type == "MESH"]:
        build_core(V)
    log("HOAN TAT. Chay uit_export.py de xuat ra web.")


if __name__ == "__main__":
    main()
