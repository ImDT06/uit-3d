// Xu ly mo hinh khuon vien (khong dung vat ly): dung chung cho trang chu (IntroScene) va che do kham pha (Campus).
// Tach rieng de trang chu khong phai tai thu vien vat ly Rapier (~2 MB).
import * as THREE from "three";
import { useGLTF } from "@react-three/drei";

export const MODEL_URL = "/models/uit_campus.glb";

// Tach cay (TREE_*) ra nhom rieng: cay khong dung va cham luoi tam giac (nang),
// moi cay chi co mot tru va cham o than.
export function splitScene(scene) {
  if (scene.userData.split) return scene.userData.split;
  const deco = new THREE.Group();
  const trees = [];
  [...scene.children].forEach((o) => {
    if (o.name.startsWith("TREE_")) {
      deco.add(o); // tu dong go khoi scene
      trees.push({ key: o.name, x: o.position.x, z: o.position.z, s: o.scale.x });
    }
  });
  // Bong do: vat lieu trong glb deu 2 mat (doubleSided) nen mat dang duoc chieu sang tu in bong len chinh no
  // (vet lam tam tren tuong). shadowSide = BackSide: chi mat khuat sang ghi vao shadow map.
  // Mat phang (dat, loi di, kinh) khong do bong: het vet tren mat dat, bot viec cho GPU.
  const flat = (o) => {
    for (let p = o; p && p !== scene; p = p.parent) if (/^(GND_|PATH_|GATE_road)|_glass$/.test(p.name)) return true;
    return false;
  };
  const shadowMat = (m) => [m.material].flat().forEach((mat) => (mat.shadowSide = THREE.BackSide));
  scene.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = !flat(o);
    o.receiveShadow = true;
    shadowMat(o);
  });
  deco.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true;
    o.receiveShadow = false;
    shadowMat(o);
  });
  scene.updateMatrixWorld(true);

  // Du lieu gameplay dung trong Blender (empty, collection Gameplay):
  // ZONE_<toa>: hop vung kich hoat (hop don vi -1..1 da bien doi), key khu vuc = extras.zone hoac BLD_<toa>
  // ITEM_###: diem dat vat pham, extras.quest = ma nhiem vu
  const zones = [];
  const items = [];
  [...scene.children].forEach((o) => {
    if (o.name.startsWith("ZONE_")) {
      const box = new THREE.Box3(new THREE.Vector3(-1, -1, -1), new THREE.Vector3(1, 1, 1)).applyMatrix4(o.matrixWorld);
      const s = o.scale;
      zones.push({
        name: o.userData.zone || "BLD_" + o.name.slice(5),
        obj: o.name,
        inv: o.matrixWorld.clone().invert(),
        box,
        volume: s.x * s.y * s.z,
      });
      scene.remove(o);
    } else if (o.name.startsWith("ITEM_")) {
      items.push({ id: o.name, quest: o.userData.quest || null, pos: [o.position.x, o.position.y, o.position.z] });
      scene.remove(o);
    }
  });

  const buildings = scene.children
    .filter((o) => o.name.startsWith("BLD_"))
    .map((o) => {
      const box = new THREE.Box3().setFromObject(o);
      const c = box.getCenter(new THREE.Vector3());
      return { name: o.name, box, center: [c.x, box.max.y + 3, c.z] };
    });
  // Toa nha: khong dung trimesh (tuong mong, nhan vat co the bi day lot vao trong).
  // Thay bang khoi dac: moi tam giac mat day dung thanh lang tru cao bang toa -> ConvexHullCollider.
  const solids = [];
  const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _c = new THREE.Vector3();
  scene.children
    .filter((o) => o.name.startsWith("BLD_"))
    .map((o) => {
      // rapier chi xet to tien cua mesh: toa la mesh don (1 vat lieu) thi boc vao group
      if (!o.isMesh) return o;
      const g = new THREE.Group();
      g.name = o.name;
      scene.add(g);
      g.add(o);
      return g;
    })
    .forEach((bld) => {
      bld.userData.r3RapierType = "MeshCollider"; // rapier bo qua toa nay (ca DET_ con) khi tu tao trimesh
      const meshes = [];
      bld.traverse((m) => {
        if (!m.isMesh) return;
        let p = m;
        while (p && p !== bld) {
          if (p.name.startsWith("DET_")) return;
          p = p.parent;
        }
        meshes.push(m);
      });
      const box = new THREE.Box3();
      meshes.forEach((m) => box.expandByObject(m));
      const y0 = box.min.y - 0.5, eps = 0.05;
      // toa nhieu cap mai (vd B 9/7/5 tang): moi lang tru cao bang mat mai nam ngay tren no
      const roofs = [];
      meshes.forEach((m) => {
        const pos = m.geometry.attributes.position, idx = m.geometry.index;
        const n = idx ? idx.count : pos.count;
        for (let i = 0; i < n; i += 3) {
          const t = [0, 1, 2].map((k) => new THREE.Vector3().fromBufferAttribute(pos, idx ? idx.getX(i + k) : i + k).applyMatrix4(m.matrixWorld));
          if (t[0].y > box.min.y + 1 && Math.abs(t[0].y - t[1].y) < eps && Math.abs(t[0].y - t[2].y) < eps) roofs.push(t);
        }
      });
      const inTri = (x, z, [a, b, c]) => {
        const d1 = (x - b.x) * (a.z - b.z) - (a.x - b.x) * (z - b.z);
        const d2 = (x - c.x) * (b.z - c.z) - (b.x - c.x) * (z - c.z);
        const d3 = (x - a.x) * (c.z - a.z) - (c.x - a.x) * (z - a.z);
        return !((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0));
      };
      const roofAt = (x, z) => roofs.find((t) => inTri(x, z, t))?.[0].y ?? box.max.y;
      meshes.forEach((m) => {
        const pos = m.geometry.attributes.position;
        const idx = m.geometry.index;
        const n = idx ? idx.count : pos.count;
        for (let i = 0; i < n; i += 3) {
          const ia = idx ? idx.getX(i) : i, ib = idx ? idx.getX(i + 1) : i + 1, ic = idx ? idx.getX(i + 2) : i + 2;
          _a.fromBufferAttribute(pos, ia).applyMatrix4(m.matrixWorld);
          _b.fromBufferAttribute(pos, ib).applyMatrix4(m.matrixWorld);
          _c.fromBufferAttribute(pos, ic).applyMatrix4(m.matrixWorld);
          if ([_a, _b, _c].some((v) => Math.abs(v.y - box.min.y) > eps)) continue; // chi lay mat day
          const area = Math.abs((_b.x - _a.x) * (_c.z - _a.z) - (_c.x - _a.x) * (_b.z - _a.z)) / 2;
          if (area < 0.05) continue; // tam giac suy bien -> hull loi
          const y1 = roofAt((_a.x + _b.x + _c.x) / 3, (_a.z + _b.z + _c.z) / 3);
          const v = [];
          [_a, _b, _c].forEach((p) => v.push(p.x, y0, p.z, p.x, y1, p.z));
          solids.push({ key: bld.name + "_" + m.uuid.slice(0, 4) + "_" + i, verts: new Float32Array(v) });
        }
      });
    });

  // luoi chan camera (camera khong xuyen qua toa nha)
  const camBlockers = [];
  scene.children
    .filter((o) => o.name.startsWith("BLD_"))
    .forEach((o) => o.traverse((m) => m.isMesh && camBlockers.push(m)));
  // tuong bien vo hinh quanh mep mat dat (GND_Base), khong cho di ra ngoai truong
  const walls = [];
  const base = scene.getObjectByName("GND_Base");
  const bounds = base ? new THREE.Box3().setFromObject(base) : new THREE.Box3(new THREE.Vector3(-150, 0, -150), new THREE.Vector3(150, 0, 150));
  if (base) {
    const b = bounds;
    const H = 15, T = 1; // nua chieu cao, nua do day
    const cx = (b.min.x + b.max.x) / 2, cz = (b.min.z + b.max.z) / 2;
    const hx = (b.max.x - b.min.x) / 2 + T, hz = (b.max.z - b.min.z) / 2 + T;
    walls.push(
      { pos: [b.min.x - T, H, cz], args: [T, H, hz] },
      { pos: [b.max.x + T, H, cz], args: [T, H, hz] },
      { pos: [cx, H, b.min.z - T], args: [hx, H, T] },
      { pos: [cx, H, b.max.z + T], args: [hx, H, T] }
    );
  }
  scene.userData.split = { deco, trees, buildings, camBlockers, walls, zones, items, solids, bounds };
  return scene.userData.split;
}

useGLTF.preload(MODEL_URL);
