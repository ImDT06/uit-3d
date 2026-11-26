// Xu ly mo hinh khuon vien (khong dung vat ly): dung chung cho trang chu (IntroScene) va che do kham pha (Campus).
// Tach rieng de trang chu khong phai tai thu vien vat ly Rapier (~2 MB).
import * as THREE from "three";
import { useGLTF } from "@react-three/drei";
import { LANDMARKS } from "../data/zones";
import { applyPalette } from "./palette";

// ?model=uit_campus_bakeB: xem thu file glb khac trong public/models (vd ban nuong anh sang dang duyet)
const altModel = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("model");
export const MODEL_URL = altModel && /^[\w-]+$/.test(altModel) ? `/models/${altModel}.glb` : "/models/uit_campus.glb";

// Tach cay (TREE_*) ra nhom rieng: cay khong dung va cham luoi tam giac (nang),
// moi cay chi co mot tru va cham o than.
export function splitScene(scene) {
  if (scene.userData.split) return scene.userData.split;
  const deco = new THREE.Group();
  const trees = [];
  [...scene.children].forEach((o) => {
    // TREE_*: cay trong tu dong (uit_detail.py), moi cay mot object.
    // CAY_*: cay lay tu ban MyUIT: CAY_myuit = mot mesh gop moi cay (chi hien thi, it lenh ve),
    // CAY_### = empty dat o goc tung cay (chi de dung tru va cham).
    if (o.name.startsWith("TREE_") || o.name.startsWith("CAY_")) {
      deco.add(o); // tu dong go khoi scene
      const isPoint = o.name.startsWith("CAY_") && !o.isMesh && o.children.length === 0;
      if (o.name.startsWith("TREE_") || isPoint) trees.push({ key: o.name, x: o.position.x, z: o.position.z, s: o.scale.x });
    }
  });
  // Bong do: vat lieu trong glb deu 2 mat (doubleSided) nen mat dang duoc chieu sang tu in bong len chinh no
  // (vet lam tam tren tuong). shadowSide = BackSide: chi mat khuat sang ghi vao shadow map.
  // Mat phang (dat, loi di, kinh, mang trang tri dan len tuong *_decal) khong do bong: het vet tren mat dat, bot viec cho GPU.
  const flat = (o) => {
    for (let p = o; p && p !== scene; p = p.parent) if (/^(GND_|PATH_|GATE_road)|_(glass|decal)$/.test(p.name)) return true;
    return false;
  };
  const shadowMat = (m) => [m.material].flat().forEach((mat) => (mat.shadowSide = THREE.BackSide));
  // Object da nuong anh sang trong Blender (uit_lightbake.py, extras.baked): anh da gom nang, bong, anh sang doi
  // -> hien thang mau anh, khong tinh den/bong lai (khong toneMapped: giu dung mau da canh trong Blender)
  const baked = (o) => {
    for (let p = o; p && p !== scene; p = p.parent) if (p.userData.baked) return true;
    return false;
  };
  scene.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = !flat(o);
    if (baked(o) && o.material.map) {
      const old = o.material;
      o.material = new THREE.MeshBasicMaterial({ map: old.map, side: old.side, toneMapped: false, name: old.name });
      o.receiveShadow = false;
    } else {
      o.receiveShadow = true;
    }
    shadowMat(o);
  });
  deco.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true;
    o.receiveShadow = false;
    shadowMat(o);
  });
  scene.updateMatrixWorld(true);

  // ban cat tu MyUIT (co toa trimesh): doi sang bang mau tuoi (palette.js)
  if (scene.children.some((o) => o.userData.trimesh)) applyPalette(scene);

  // COL_*: khoi chi de va cham (vd bit cua hong chieu nghi toa B), khong hien, khong do bong
  const colMat = new THREE.MeshBasicMaterial({ visible: false });
  scene.children
    .filter((o) => o.name.startsWith("COL_"))
    .forEach((o) => {
      o.material = colMat;
      o.castShadow = o.receiveShadow = false;
    });

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

  // VIS_<toa>: mo hinh hien thi dat vao mat bang BLD_<toa> (vd lay tu ban MyUIT). Khi co VIS_ con,
  // than BLD_ chi con lam khoi va cham + chan camera (an di, khong do bong); VIS_ thi khong dung de va cham.
  // VIS_<toa>_core (uit_vis_core.py): khoi loi dac lui sau mat tuong VIS_ -> hien thi + lam khoi va cham, chan camera
  // (khop voi tuong nhin thay, thay cho than BLD_ von lech vai met).
  const hidden = new THREE.MeshBasicMaterial({ visible: false });
  const isCore = (o) => /^VIS_.*_core$/.test(o.name);
  // loi an di (chi va cham): vo MyUIT cua toa nay da kin, hien loi se de len cua so/ban cong
  const HIDE_CORE = new Set(["VIS_B_core"]);
  const isVis = (o) => o.name.startsWith("VIS_") && !isCore(o);
  const underCore = (m, root) => {
    for (let p = m; p && p !== root; p = p.parent) if (isCore(p)) return true;
    return false;
  };
  scene.children
    .filter((o) => o.name.startsWith("BLD_") && o.children.some(isVis))
    .forEach((o) => {
      if (o.isMesh) o.material = hidden;
      else
        o.children.forEach(
          (m) =>
            m.isMesh &&
            !isVis(m) &&
            (!isCore(m) || HIDE_CORE.has(m.name)) &&
            !m.name.startsWith("DET_") &&
            (m.material = hidden),
        );
    });

  const buildings = scene.children
    .filter((o) => o.name.startsWith("BLD_"))
    .map((o) => {
      const box = new THREE.Box3().setFromObject(o);
      const c = box.getCenter(new THREE.Vector3());
      // outline: duong vien mat bang cho ban do (custom prop tu Blender, chi ban cat tu MyUIT co)
      let outline = null;
      if (o.userData.outline) {
        const loops = JSON.parse(o.userData.outline);
        outline = loops.map((l) => "M" + l.map((p) => p.join(" ")).join("L") + "Z").join("");
      }
      return { name: o.name, box, center: [c.x, box.max.y + 3, c.z], outline };
    });
  // Toa nha: khong dung trimesh (tuong mong, nhan vat co the bi day lot vao trong).
  // Thay bang khoi dac: moi tam giac mat day dung thanh lang tru cao bang toa -> ConvexHullCollider.
  const solids = [];
  const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _c = new THREE.Vector3();
  // BLD_ co custom prop trimesh (toa cat nguyen ban tu MyUIT, vo ho day): giu va cham luoi tam giac nhu mat dat,
  // khong dung khoi dac (camera van bi chan, xem camBlockers duoi)
  scene.children
    .filter((o) => o.name.startsWith("BLD_") && !o.userData.trimesh)
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
      const cores = [];
      bld.traverse((m) => m.isMesh && underCore(m, bld) && cores.push(m));
      if (cores.length) {
        // loi xep tang: moi tam giac mat day (huong xuong) dung lang tru toi mat mai gan nhat ngay tren no
        const ups = [], downs = [];
        const n_ = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
        cores.forEach((m) => {
          const pos = m.geometry.attributes.position, idx = m.geometry.index;
          const n = idx ? idx.count : pos.count;
          for (let i = 0; i < n; i += 3) {
            const t = [0, 1, 2].map((k) => new THREE.Vector3().fromBufferAttribute(pos, idx ? idx.getX(i + k) : i + k).applyMatrix4(m.matrixWorld));
            if (Math.abs(t[0].y - t[1].y) > 0.05 || Math.abs(t[0].y - t[2].y) > 0.05) continue;
            n_.crossVectors(e1.subVectors(t[1], t[0]), e2.subVectors(t[2], t[0]));
            (n_.y > 0 ? ups : downs).push(t);
          }
        });
        const inT = (x, z, [a, b, c]) => {
          const d1 = (x - b.x) * (a.z - b.z) - (a.x - b.x) * (z - b.z);
          const d2 = (x - c.x) * (b.z - c.z) - (b.x - c.x) * (z - c.z);
          const d3 = (x - a.x) * (c.z - a.z) - (c.x - a.x) * (z - a.z);
          return !((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0));
        };
        const yMin = Math.min(...downs.map((t) => t[0].y));
        downs.forEach((t, i) => {
          const area = Math.abs((t[1].x - t[0].x) * (t[2].z - t[0].z) - (t[2].x - t[0].x) * (t[1].z - t[0].z)) / 2;
          if (area < 0.05) return;
          const cx = (t[0].x + t[1].x + t[2].x) / 3, cz = (t[0].z + t[1].z + t[2].z) / 3, yb = t[0].y;
          let y1 = Infinity;
          ups.forEach((u) => u[0].y > yb + 0.05 && u[0].y < y1 && inT(cx, cz, u) && (y1 = u[0].y));
          if (!isFinite(y1)) return;
          const y0 = yb - yMin < 0.05 ? yb - 0.5 : yb;
          const v = [];
          t.forEach((p) => v.push(p.x, y0, p.z, p.x, y1, p.z));
          solids.push({ key: bld.name + "_core_" + i, verts: new Float32Array(v) });
        });
        return;
      }
      const meshes = [];
      bld.traverse((m) => {
        if (!m.isMesh) return;
        let p = m;
        while (p && p !== bld) {
          if (p.name.startsWith("DET_") || isVis(p)) return;
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
      const roofAt = (x, z) => {
        let y = -Infinity;
        roofs.forEach((t) => t[0].y > y && inTri(x, z, t) && (y = t[0].y));
        return isFinite(y) ? y : box.max.y;
      };
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
  // ban cat tu MyUIT (co toa trimesh): bac ngoi PODIUM_ va mai che loi di ROOF_ cung chan camera
  const cut = scene.children.some((o) => o.userData.trimesh);
  scene.children
    .filter((o) => o.name.startsWith("BLD_") || (cut && /^(PODIUM|ROOF)_/.test(o.name)))
    .forEach((o) => {
      // co loi VIS_*_core: chan camera bang loi (khop tuong nhin thay); khong thi bang than BLD_ (bo qua luoi VIS_ nang)
      const cores = [];
      o.traverse((m) => m.isMesh && underCore(m, o) && cores.push(m));
      if (cores.length) return camBlockers.push(...cores);
      o.traverse((m) => {
        if (!m.isMesh) return;
        for (let p = m; p && p !== o; p = p.parent) if (isVis(p)) return;
        camBlockers.push(m);
      });
    });
  // tuong bien vo hinh quanh mep mat dat (GND_Base), khong cho di ra ngoai truong
  const walls = [];
  const base = scene.getObjectByName("GND_Base");
  const bounds = base ? new THREE.Box3().setFromObject(base) : new THREE.Box3(new THREE.Vector3(-150, 0, -150), new THREE.Vector3(150, 0, 150));
  // ban cat tu MyUIT: nen la da giac loi om theo dat (hinh thoi) -> tuong bien va be sa ban theo cac canh cua no
  let edge = null;
  if (base?.isMesh && scene.children.some((o) => o.userData.trimesh)) {
    const pos = base.geometry.attributes.position, pts = new Map();
    for (let i = 0; i < pos.count; i++) {
      const p = new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(base.matrixWorld);
      pts.set(p.x.toFixed(1) + "," + p.z.toFixed(1), [p.x, p.z]);
    }
    const list = [...pts.values()];
    const mx = list.reduce((s, p) => s + p[0], 0) / list.length, mz = list.reduce((s, p) => s + p[1], 0) / list.length;
    edge = list.sort((a, b) => Math.atan2(a[1] - mz, a[0] - mx) - Math.atan2(b[1] - mz, b[0] - mx));
  }
  if (edge) {
    const H = 15, T = 1;
    edge.forEach(([x0, z0], i) => {
      const [x1, z1] = edge[(i + 1) % edge.length];
      const dx = x1 - x0, dz = z1 - z0, len = Math.hypot(dx, dz);
      // goc sap theo chieu tang cua atan2 nen phia ngoai la (dz, -dx)
      walls.push({
        pos: [(x0 + x1) / 2 + (dz / len) * T, H, (z0 + z1) / 2 - (dx / len) * T],
        rot: [0, -Math.atan2(dz, dx), 0],
        args: [len / 2 + T, H, T],
      });
    });
  } else if (base) {
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
  // diem moc co nhan noi (cong A, cong B...): ten object -> vi tri tren dinh
  const landmarks = Object.keys(LANDMARKS)
    .map((name) => scene.getObjectByName(name))
    .filter(Boolean)
    .map((o) => {
      // MARK_*: empty danh dau mot diem (khong co hinh) -> dung thang vi tri cua no
      if (o.name.startsWith("MARK_")) return { name: o.name, center: o.position.toArray() };
      const box = new THREE.Box3().setFromObject(o);
      const c = box.getCenter(new THREE.Vector3());
      return { name: o.name, center: [c.x, box.max.y + 2, c.z] };
    });
  scene.userData.split = { deco, trees, buildings, camBlockers, walls, zones, items, solids, bounds, landmarks, edge };
  return scene.userData.split;
}

useGLTF.preload(MODEL_URL);
