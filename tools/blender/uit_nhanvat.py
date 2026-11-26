# Dung nhan vat sinh vien UIT tu bo Ultimate Modular Men / Women cua Quaternius.
# Chay ngam: blender -b --factory-startup -P tools/blender/uit_nhanvat.py -- [anh_xem_thu.png | xuat]
# xuat: ghi public/models/nv_nam.glb, nv_nu.glb (Walk, Run cua bo goc; Idle, Jump, Fall, Hover, Fly, Dive tu lam trong dong_tac)
# Nguon (D:/uit3d/nhanvat_goc): nam.glb, nu.glb, logo_ao.png, balo.png (hai anh nay cat tu anh chup ao va balo that)
# Them: ao polo trang vien xanh + logo, quan kaki, that lung, balo UIT, toc dai cho nu (object ToDai).
import bpy, bmesh, os, sys, math
from mathutils import Vector as V, Matrix
from mathutils.bvhtree import BVHTree

GOC = "D:/uit3d/nhanvat_goc"


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1,)


def bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def mau(ten, h=None, anh=None):
    m = bpy.data.materials.get(ten)
    if m:
        return m
    m = bpy.data.materials.new(ten)
    m.use_nodes = True
    b = bsdf(m)
    b.inputs["Roughness"].default_value = 0.85
    if h:
        b.inputs["Base Color"].default_value = lin(h)
    if anh:
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(f"{GOC}/{anh}")
        m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
        m.node_tree.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    return m


def to_mau(o, ten, h):
    for m in o.data.materials:
        if m.name.split(".")[0] == ten:
            b = bsdf(m)
            for l in list(b.inputs["Base Color"].links):
                m.node_tree.links.remove(l)
            b.inputs["Base Color"].default_value = lin(h)


def cat(o, ten, truc, gia_tri):
    """cat cac mat cua vat lieu `ten` tai mat phang truc = gia_tri (de to vien cho thang)"""
    M = o.matrix_world
    co = M.inverted() @ V([gia_tri if i == truc else 0 for i in range(3)])
    no = (M.to_3x3().transposed() @ V([1 if i == truc else 0 for i in range(3)])).normalized()
    mi = [i for i, m in enumerate(o.data.materials) if m.name.split(".")[0] == ten][0]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    fs = [f for f in bm.faces if f.material_index == mi]
    geom = fs + list({e for f in fs for e in f.edges}) + list({v for f in fs for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
    bm.to_mesh(o.data)
    bm.free()


def gan(o, ten, moi, dk):
    """doi vat lieu cac mat cua `ten` thoa dk(tam mat, toa do the gioi)"""
    mi = [i for i, m in enumerate(o.data.materials) if m.name.split(".")[0] == ten][0]
    o.data.materials.append(moi)
    k = len(o.data.materials) - 1
    for p in o.data.polygons:
        if p.material_index == mi and dk(o.matrix_world @ p.center):
            p.material_index = k


class Than:
    """be mat than de dat phu kien + chep trong so xuong"""

    def __init__(self, arm, meshes):
        self.arm = arm
        vs, fs, self.w = [], [], []
        for o in meshes:
            n = len(vs)
            names = [g.name for g in o.vertex_groups]
            for v in o.data.vertices:
                vs.append(o.matrix_world @ v.co)
                self.w.append({names[g.group]: g.weight for g in v.groups if g.weight > 0.001})
            fs += [[n + i for i in p.vertices] for p in o.data.polygons]
        self.vs = vs
        self.bvh = BVHTree.FromPolygons(vs, fs)

    def tia(self, x, z, huong):
        """diem tren be mat khi ban tia tu truoc (huong=1) hoac tu sau (huong=-1)"""
        for dx, dz in ((0, 0), (0.002, 0.002), (-0.002, -0.002), (-0.008, 0), (0, -0.008)):
            h = self.bvh.ray_cast(V((x + dx, -1.0 * huong, z + dz)), V((0, huong, 0)))
            if h[0]:
                return h[0]
        return self.bvh.find_nearest(V((x, -0.2 * huong, z)))[0]

    def gan_nhat(self, p, d):
        q, n, *_ = self.bvh.find_nearest(p)
        return q + n * d

    def vat(self, ten, verts, faces, mat, xuong=None, uv=None, day=0.0):
        """tao mesh phu kien gan vao xuong; xuong=None: chep trong so cua dinh than gan nhat"""
        me = bpy.data.meshes.new(ten)
        me.from_pydata([tuple(v) for v in verts], [], faces)
        me.materials.append(mat)
        if uv:
            lay = me.uv_layers.new(name="UVMap")
            for p in me.polygons:
                for li in p.loop_indices:
                    lay.data[li].uv = uv[me.loops[li].vertex_index]
        o = bpy.data.objects.new(ten, me)
        bpy.context.scene.collection.objects.link(o)
        if day:
            md = o.modifiers.new("day", "SOLIDIFY")
            md.thickness = day
            md.offset = 0
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=md.name)
        for v in o.data.vertices:
            if callable(xuong):
                w = xuong(v.co)
            elif xuong:
                w = {xuong: 1}
            else:
                i = min(range(len(self.vs)), key=lambda i: (self.vs[i] - v.co).length_squared)
                w = self.w[i]
            for g, k in w.items():
                vg = o.vertex_groups.get(g) or o.vertex_groups.new(name=g)
                vg.add([v.index], k, "REPLACE")
        mw = o.matrix_world.copy()
        o.parent = self.arm
        o.matrix_parent_inverse = self.arm.matrix_world.inverted()
        o.matrix_world = mw
        md = o.modifiers.new("xuong", "ARMATURE")
        md.object = self.arm
        return o


def dai(pts_a, pts_b, kin=False):
    """dai mat noi 2 hang diem"""
    n = len(pts_a)
    verts = list(pts_a) + list(pts_b)
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n if kin else n - 1)]
    return verts, faces


def hop(cx, cy, cz, sx, sy, sz, bo):
    """hop bo goc -> (verts, faces)"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co = V((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bo, segments=3, affect="EDGES", profile=0.6)
    bm.verts.index_update()
    r = [v.co + V((cx, cy, cz)) for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces]
    bm.free()
    return r


def luoi(t, x0, x1, z0, z1, huong, d, n=8):
    """tam phang uon theo be mat than (logo)"""
    verts, uv, faces = [], [], []
    for j in range(n + 1):
        for i in range(n + 1):
            u, v = i / n, j / n
            x, z = x0 + (x1 - x0) * u, z0 + (z1 - z0) * v
            p = t.tia(x, z, huong)
            verts.append(V((x, p.y - d * huong, z)))
            uv.append((u, v))
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i
            faces.append((a, a + 1, a + n + 2, a + n + 1))
    return verts, faces, uv


def dung(gioi):
    truoc = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f"{GOC}/{gioi}.glb")
    moi = [o for o in bpy.data.objects if o not in truoc]
    arm = next(o for o in moi if o.type == "ARMATURE")
    for o in list(moi):
        if o.type == "MESH" and not o.find_armature():
            moi.remove(o)
            bpy.data.objects.remove(o)
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    bo = {o.name.split("_")[1].split(".")[0]: o for o in moi if o.type == "MESH"}
    than, quan, giay, dau = bo["Body"], bo["Legs"], bo["Feet"], bo["Head"]
    nam = gioi == "nam"
    ao_cu = "LightBrown" if nam else "White"
    quan_cu = "LightBlue" if nam else "Orange"

    for o in bo.values():
        for m in o.data.materials:
            bsdf(m).inputs["Metallic"].default_value = 0
            bsdf(m).inputs["Roughness"].default_value = 0.85

    xanh = mau("UIT_xanh", "1553c8")
    xanh_nhat = mau("UIT_xanh_nhat", "2f86e0")
    trang = mau("UIT_trang", "f2f4f8")
    den = mau("UIT_den", "1c1c20")

    to_mau(than, ao_cu, "f2f4f8")
    to_mau(quan, quan_cu, "b9ab8b")
    for ten in ("Hair", "Hair_Blond", "Hair_Brown", "Eyebrows"):
        to_mau(dau, ten, "17120f")
    if nam:
        to_mau(giay, "Red_Dark", "2a2a30")

    def toa_do(o, ten):
        mi = [i for i, m in enumerate(o.data.materials) if m.name.split(".")[0] == ten][0]
        return [o.matrix_world @ o.data.vertices[v].co for p in o.data.polygons if p.material_index == mi for v in p.vertices]

    # nam: cat bo chom toc buoc sau gay -> toc ngan
    if nam:
        mi = [i for i, m in enumerate(dau.data.materials) if m.name.split(".")[0] == "Hair"][0]
        bm = bmesh.new()
        bm.from_mesh(dau.data)
        M = dau.matrix_world
        bo_di = [f for f in bm.faces if f.material_index == mi and (M @ f.calc_center_median()).y > 0.082
                 and (M @ f.calc_center_median()).z < 1.74]
        bmesh.ops.delete(bm, geom=bo_di, context="FACES")
        bm.to_mesh(dau.data)
        bm.free()

    # vien tay ao
    xm = max(abs(p.x) for p in toa_do(than, ao_cu))
    for s in (1, -1):
        cat(than, ao_cu, 0, s * (xm - 0.04))
    gan(than, ao_cu, xanh, lambda c: abs(c.x) > xm - 0.04)
    # that lung: dai tren cung cua quan, ngay duoi gau ao
    gau = min(p.z for p in toa_do(than, ao_cu))
    z1, z0 = gau + 0.008, gau - 0.042
    cat(quan, quan_cu, 2, z0)
    cat(quan, quan_cu, 2, z1)
    gan(quan, quan_cu, den, lambda c: c.z > z0)

    t = Than(arm, [than, quan])
    f = t.tia(0, z0 + 0.025, 1)
    t.vat("KhoaThatLung", *hop(0, f.y - 0.006, (z0 + gau) / 2, 0.045, 0.012, 0.032, 0.004), mau("UIT_bac", "b8bcc4"), "Hips")

    # co ao polo: 2 ve co om quanh co, ho o giua nguc
    co = V((0, -0.045, 0))
    for s in (1, -1):
        trong, ngoai = [], []
        for k in range(13):
            u = k / 12
            a = math.radians(-90 + s * (9 + u * 171))  # -90 do = phia truoc
            huong = V((math.cos(a), math.sin(a), 0))
            mui = max(0, 1 - u * 4)  # dau ve co nhon xuong
            z_in = 1.535 - 0.03 * mui
            h = t.bvh.ray_cast(co + huong * 0.4 + V((0, 0, z_in)), -huong)[0]
            r_in = min((h - co - V((0, 0, z_in))).length, 0.075) if h else 0.06
            trong.append(co + huong * (r_in + 0.006) + V((0, 0, z_in)))
            ngoai.append(t.gan_nhat(co + huong * (r_in + 0.028) + V((0, 0, 1.51 - 0.035 * mui)), 0.01))
        t.vat(f"CoAo{s}", *dai(trong, ngoai), xanh, None, day=0.006)
    # nep ao + 2 cuc
    zs = [1.50 - i * 0.015 for i in range(8)]
    trai = [V((-0.011, t.tia(-0.011, z, 1).y - 0.004, z)) for z in zs]
    phai = [V((0.011, t.tia(0.011, z, 1).y - 0.004, z)) for z in zs]
    t.vat("NepAo", *dai(trai, phai), xanh, None)
    for z in (1.47, 1.42):
        p = t.tia(0, z, 1)
        t.vat("Cuc", *hop(0, p.y - 0.007, z, 0.011, 0.005, 0.011, 0.002), trang, "Chest")
    # logo nguc trai (ben trai cua nguoi mac = +X)
    verts, faces, uv = luoi(t, 0.018, 0.088, 1.31 if nam else 1.325, 1.394 if nam else 1.409, 1, 0.014, 16)
    t.vat("Logo", verts, faces, mau("UIT_logo", anh="logo_ao.png"), None, uv)

    # balo
    lung = max(t.tia(x, z, -1).y for x in (-0.08, 0, 0.08) for z in (1.15, 1.25, 1.35) if t.tia(x, z, -1))
    day, rong, cao = 0.12, 0.28, 0.35
    cy, cz = lung + day / 2 - 0.012, 1.22
    # mau than balo lay theo anh that (diem giua phia tren logo cua mat sau)
    hinh = mau("UIT_balo", anh="balo.png")
    img = next(n for n in hinh.node_tree.nodes if n.type == "TEX_IMAGE").image
    w_, h_ = img.size
    i_ = (int(h_ * 0.62) * w_ + int(w_ * 0.5)) * 4
    r_ = "".join(f"{round(c * 255):02x}" for c in img.pixels[i_:i_ + 3])
    t.vat("Balo", *hop(0, cy, cz, rong, day, cao, 0.04), mau("UIT_balo_than", r_), "Chest")
    t.vat("BaloHong", *hop(0, cy - 0.008, cz - 0.005, rong + 0.018, day * 0.55, cao * 0.93, 0.025), xanh_nhat, "Chest")
    yb = cy + day / 2 + 0.002
    x, za, zb = rong / 2 - 0.028, cz - cao / 2 + 0.025, cz + cao / 2 - 0.025
    t.vat("BaloHinh", [V((x, yb, za)), V((-x, yb, za)), V((-x, yb, zb)), V((x, yb, zb))], [(0, 1, 2, 3)],
          hinh, "Chest", [(0, 0), (1, 0), (1, 1), (0, 1)])
    quai = [V((x, cy, cz + cao / 2 + h)) for x, h in ((-0.055, -0.005), (-0.035, 0.032), (0.035, 0.032), (0.055, -0.005))]
    t.vat("BaloQuai", *dai(quai, [p + V((0, 0.022, 0)) for p in quai]), trang, "Chest", day=0.01)
    # day deo: tu lung balo qua vai xuong truoc nguc, om sat than
    for s in (1, -1):
        duong = []
        for z in (1.38, 1.43):
            duong.append(V((0.085, t.tia(0.085, z, -1).y + 0.01, z)))
        for y in (0.0, -0.05, -0.09):
            h = t.bvh.ray_cast(V((0.1, y, 2.0)), V((0, 0, -1)))[0]
            duong.append(V((0.105, y, min(h.z, 1.52) + 0.012)))
        zs_ = (1.45, 1.40, 1.35, 1.30, 1.25, 1.20, 1.15)
        ys = [min(t.tia(x, z, 1).y for x in (0.09, 0.11, 0.13)) for z in zs_]
        ys = [min(ys[max(i - 1, 0):i + 2]) * 0.5 + (ys[max(i - 1, 0)] + ys[i] + ys[min(i + 1, 6)]) / 6 for i in range(7)]
        for z, y in zip(zs_, ys):
            duong.append(V((0.115 if nam else 0.108, y - 0.012, z)))
        duong.append(V((rong / 2 - 0.01, cy - 0.04, 1.09)))
        a = [V((s * (p.x - 0.018), p.y, p.z)) for p in duong]
        b = [V((s * (p.x + 0.018), p.y, p.z)) for p in duong]
        t.vat(f"DayBalo{s}", *dai(a, b), xanh_nhat, None, day=0.008)

    # toc dai cho nu (bat/tat tren web): mang toc phu sau dau xuong ngang vai
    if not nam:
        hang = [  # z, ban kinh ngang, ban kinh sau, tam y, nua goc (do) tinh tu sau gay
            (1.79, 0.095, 0.095, -0.045, 112), (1.72, 0.125, 0.130, -0.045, 112), (1.64, 0.128, 0.135, -0.040, 108),
            (1.56, 0.125, 0.130, -0.025, 100), (1.50, 0.135, 0.125, -0.005, 92), (1.44, 0.140, 0.120, 0.015, 84),
            (1.40, 0.120, 0.105, 0.025, 76), (1.375, 0.070, 0.085, 0.030, 60)]
        n = 16
        verts, faces = [], []
        for z, rx, ry, y, g in hang:
            for i in range(n + 1):
                a = math.radians(-g + 2 * g * i / n)
                song = 1 + 0.05 * (i % 2)  # lon toc
                verts.append(V((math.sin(a) * rx * song, y + math.cos(a) * ry * song, z)))
        for j in range(len(hang) - 1):
            for i in range(n):
                k = j * (n + 1) + i
                faces.append((k, k + n + 1, k + n + 2, k + 1))
        toc = next(m for m in dau.data.materials if m.name.split(".")[0] == "Hair_Blond")

        def w(co_):
            k = min(max((co_.z - 1.42) / 0.18, 0), 1)
            return {"Head": k, "Chest": 1 - k} if 0 < k < 1 else {"Head" if k else "Chest": 1}

        t.vat("ToDai", verts, faces, toc, w, day=0.016)

    arm.data.pose_position = "POSE"
    arm.name = "NV_" + gioi
    return arm, [o for o in arm.children]


def xem_thu(out):
    """anh duyet: nu toc ngan, nu toc dai, nam x truoc, nghieng, sau"""
    sc = bpy.context.scene
    cot = [("nam", False, "Nam"), ("nu", False, "Nữ tóc ngắn"), ("nu", True, "Nữ tóc dài")]
    for c, (gioi, dai_toc, nhan) in enumerate(cot):
        for r, goc in enumerate((0, 50, 180)):
            before = set(bpy.data.actions)
            arm, con = dung(gioi)
            acts = [a for a in bpy.data.actions if a not in before]
            idle = next(a for a in acts if a.name.split("|")[-1].split(".")[0] == "Idle")
            ad = arm.animation_data
            for tr in list(ad.nla_tracks):
                ad.nla_tracks.remove(tr)
            ad.action = idle
            if len(idle.slots):
                ad.action_slot = idle.slots[0]
            for o in con:
                if o.name.startswith("ToDai") and not dai_toc:
                    o.hide_render = True
            e = bpy.data.objects.new("goc", None)
            sc.collection.objects.link(e)
            arm.parent = e
            e.location = ((c * 3 + r) * 0.82 + c * 0.35, 0, 0)
            e.rotation_euler.z = math.radians(goc)
        t = bpy.data.curves.new(nhan, "FONT")
        t.body, t.align_x, t.size = nhan, "CENTER", 0.15
        t.materials.append(mau("chu", "10204a"))
        to = bpy.data.objects.new(nhan, t)
        sc.collection.objects.link(to)
        to.location = ((c * 3 + 1) * 0.82 + c * 0.35, 0, -0.25)
        to.rotation_euler.x = math.pi / 2
    sc.frame_set(10)
    cam = bpy.data.cameras.new("c")
    cam.type, cam.ortho_scale = "ORTHO", 8.2
    co = bpy.data.objects.new("c", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    co.location = (3.63, -10, 0.82)
    co.rotation_euler.x = math.pi / 2
    sc.render.engine = "BLENDER_EEVEE"
    for en, rx, rz in ((1.8, 50, -30), (0.7, 65, 140)):
        l = bpy.data.lights.new("s", "SUN")
        l.energy = en
        lo = bpy.data.objects.new("s", l)
        sc.collection.objects.link(lo)
        lo.rotation_euler = (math.radians(rx), 0, math.radians(rz))
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    bg = next(x for x in sc.world.node_tree.nodes if x.type == "BACKGROUND")
    bg.inputs["Color"].default_value = lin("c9d3e0")
    bg.inputs["Strength"].default_value = 0.9
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = 2000, 640
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    # can canh than tren
    cam.ortho_scale = 3.3
    co.location = (1.55, -10, 1.38)
    sc.render.resolution_x, sc.render.resolution_y = 1800, 560
    sc.render.filepath = out.replace(".png", "_gan.png")
    bpy.ops.render.render(write_still=True)


def dong_tac(arm, idle_goc):
    """tu lam Idle (dung thang), Jump (bay len), Fall (roi) tu tu the goc; tra ve {ten: action}"""
    sc = bpy.context.scene
    ad = arm.animation_data
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    pbs = arm.pose.bones
    # ban tay tha long: lay dang cac ngon tu dong tac dung cu
    ad.action = idle_goc
    if len(idle_goc.slots):
        ad.action_slot = idle_goc.slots[0]
    sc.frame_set(0)
    bpy.context.view_layer.update()
    ngon = {b.name: b.matrix_basis.copy() for b in pbs if b.name.startswith(("Index", "Middle", "Ring", "Pinky", "Thumb"))}
    ad.action = None
    Mi = arm.matrix_world.to_3x3().inverted()
    truc = {k: (Mi @ V(v)).normalized() for k, v in (("x", (1, 0, 0)), ("y", (0, 1, 0)))}

    def xoay(ten, ax, do):
        """xoay xuong quanh goc cua no theo truc the gioi (x: do am = ve phia truoc; y: ha / nang tay)"""
        b = pbs[ten]
        h = b.matrix.translation.copy()
        b.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(do), 4, truc[ax]) @ Matrix.Translation(-h) @ b.matrix
        bpy.context.view_layer.update()

    def tu_the(tay, khuyu, chan, than, co=0):
        for b in pbs:
            b.matrix_basis = ngon.get(b.name, Matrix()).copy()
        bpy.context.view_layer.update()
        if than:
            xoay("Torso", "x", than)
        if co:
            xoay("Neck", "x", co)
        for s, ben in ((1, "L"), (-1, "R")):
            ha, truoc = tay[ben]
            xoay("UpperArm." + ben, "y", s * ha)
            xoay("UpperArm." + ben, "x", truoc)
            xoay("LowerArm." + ben, "x", khuyu[ben])
            dui, goi = chan[ben]
            if dui or goi:
                xoay("UpperLeg." + ben, "x", dui)
                xoay("LowerLeg." + ben, "x", goi)
                # ban chan khong la con cua ong chan trong bo xuong nay -> tu cho di theo
                ong, ban = pbs["LowerLeg." + ben], pbs["Foot." + ben]
                ban.matrix = ong.matrix @ ong.bone.matrix_local.inverted() @ ban.bone.matrix_local
                bpy.context.view_layer.update()

    def ghi(ten, khung):
        a = bpy.data.actions.new("moi_" + ten)
        ad.action = a
        for f, args in khung:
            tu_the(*args)
            for b in pbs:
                for k in ("location", "rotation_quaternion", "scale"):
                    b.keyframe_insert(k, frame=f)
        ad.action = None
        return a

    thang = {"L": (0, 0), "R": (0, 0)}

    def tho(f):
        k = math.sin(f / 50 * 2 * math.pi)
        return ({"L": (76 - 1.5 * k, 0), "R": (76 - 1.5 * k, 0)}, {"L": -10, "R": -10}, thang, 0.9 * k)

    def lo_lung(f):
        # lo lung: hai chan so le dung dua, tay hoi dang giu thang bang (vong 48 khung)
        a = f / 48 * 2 * math.pi
        s, c = math.sin(a), math.cos(a)
        return ({"L": (56 + 6 * s, -6), "R": (56 + 6 * c, -6)}, {"L": -22 - 6 * c, "R": -22 + 6 * s},
                {"L": (-20 + 7 * s, 34 + 8 * c), "R": (2 - 7 * s, 18 - 8 * c)}, 2 + 1.5 * s)

    def bay_toi(f):
        # dang bay: tay xuoi ra sau, chan duoi keo theo, dap nhe (vong 24 khung)
        s = math.sin(f / 24 * 2 * math.pi)
        return ({"L": (66 + 3 * s, 38), "R": (66 - 3 * s, 38)}, {"L": -12, "R": -12},
                {"L": (14 + 7 * s, 20 + 6 * s), "R": (14 - 7 * s, 20 - 6 * s)}, 5)

    def lao(f):
        # lao xuong: hai tay vuon qua dau, chan khep duoi thang, co ngang len nhin duong bay (vong 24 khung)
        s = math.sin(f / 24 * 2 * math.pi)
        return ({"L": (-81 + 1.5 * s, -6), "R": (-81 - 1.5 * s, -6)}, {"L": -6, "R": -6},
                {"L": (5 + 3 * s, 8 + 3 * s), "R": (5 - 3 * s, 8 - 3 * s)}, -4, -28)

    return {
        "Dive": ghi("Dive", [(f, lao(f)) for f in range(0, 25, 3)]),
        "Hover": ghi("Hover", [(f, lo_lung(f)) for f in range(0, 49, 4)]),
        "Fly": ghi("Fly", [(f, bay_toi(f)) for f in range(0, 25, 3)]),
        "Idle": ghi("Idle", [(f, tho(f)) for f in range(0, 51, 5)]),
        # bay len: mot goi co cao, tay vung len
        "Jump": ghi("Jump", [(f, ({"L": (48, -35), "R": (60, 20)}, {"L": -55, "R": -40},
                                  {"L": (-55, 80), "R": (8, 35)}, 8)) for f in (0, 10)]),
        # roi xuong: hai chan gan duoi, tay dang ra giu thang bang
        "Fall": ghi("Fall", [(f, ({"L": (54, -14), "R": (54, -14)}, {"L": -25, "R": -25},
                                  {"L": (-22, 32), "R": (-6, 18)}, 3)) for f in (0, 10)]),
    }


def xuat(gioi):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    arm, con = dung(gioi)
    giu = {}
    for a in bpy.data.actions:
        n = a.name.split("|")[-1].split(".")[0]
        if n in ("Idle", "Walk", "Run"):
            giu[n] = a
    giu.update(dong_tac(arm, giu["Idle"]))
    ad = arm.animation_data
    for a in list(bpy.data.actions):
        if a not in giu.values():
            bpy.data.actions.remove(a)
    for n, a in giu.items():
        a.name = n
        tr = ad.nla_tracks.new()
        tr.name = n
        s = tr.strips.new(n, 0, a)
        if len(a.slots):
            s.action_slot = a.slots[0]
    # gop moi luoi (tru toc dai) thanh mot de bot lan ve
    gop = [o for o in con if o.type == "MESH" and not o.name.startswith("ToDai")]
    bpy.ops.object.select_all(action="DESELECT")
    for o in gop:
        o.select_set(True)
    chinh = next(o for o in gop if "Body" in o.name)
    bpy.context.view_layer.objects.active = chinh
    bpy.ops.object.join()
    chinh.name = "Nguoi"
    ra = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "public", "models", f"nv_{gioi}.glb")
    bpy.ops.export_scene.gltf(filepath=ra, export_format="GLB", export_animation_mode="NLA_TRACKS",
                              export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
                              export_draco_position_quantization=16)
    print("XUAT", gioi, os.path.getsize(ra))


thamso = sys.argv[sys.argv.index("--") + 1]
if thamso == "xuat":
    xuat("nam")
    xuat("nu")
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    xem_thu(thamso)
