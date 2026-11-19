import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { useGLTF, Html } from "@react-three/drei";
import { RigidBody, CylinderCollider, CuboidCollider, ConvexHullCollider } from "@react-three/rapier";
import { useGame } from "../game/store";
import { zoneInfo } from "../data/zones";

export const MODEL_URL = "/models/uit_campus.glb";

// Tim diem xuat phat khong nam trong toa nha nao, gan tam truong nhat
function findSpawn(boxes) {
  const free = (x, z) =>
    boxes.every(
      (b) => x < b.min.x - 3 || x > b.max.x + 3 || z < b.min.z - 3 || z > b.max.z + 3
    );
  for (let r = 0; r < 200; r += 2) {
    for (let a = 0; a < 360; a += 15) {
      const x = r * Math.cos((a * Math.PI) / 180);
      const z = r * Math.sin((a * Math.PI) / 180);
      if (free(x, z)) return [x, 4, z];
    }
  }
  return [0, 60, 0];
}

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
  scene.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
    }
  });
  deco.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = false;
    }
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
      const y0 = box.min.y - 0.5, y1 = box.max.y, eps = 0.05;
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

export default function Campus() {
  const { scene } = useGLTF(MODEL_URL);
  const setWorld = useGame((s) => s.setWorld);
  const setGameplay = useGame((s) => s.setGameplay);
  const debug = useGame((s) => s.physicsDebug);
  const { deco, trees, buildings, camBlockers, walls, zones, items, solids } = useMemo(() => splitScene(scene), [scene]);

  useEffect(() => {
    setGameplay(zones, items);
  }, [zones, items, setGameplay]);

  useEffect(() => {
    setWorld(findSpawn(buildings.map((b) => b.box)), buildings, camBlockers);
  }, [buildings, camBlockers, setWorld]);

  return (
    <>
      {/* Mat dat, loi di: va cham theo luoi tam giac (toa nha bi bo qua, xem duoi) */}
      <RigidBody type="fixed" colliders="trimesh">
        <primitive object={scene} />
      </RigidBody>

      {/* Cay: chi hien thi, va cham bang tru o than */}
      <primitive object={deco} />
      {trees.length > 0 && (
        <RigidBody type="fixed" colliders={false}>
          {trees.map((t) => (
            <CylinderCollider key={t.key} position={[t.x, 1.5, t.z]} args={[1.5, 0.35 * t.s]} />
          ))}
        </RigidBody>
      )}

      {/* Toa nha: khoi dac */}
      <RigidBody type="fixed" colliders={false}>
        {solids.map((c) => (
          <ConvexHullCollider key={c.key} args={[c.verts]} />
        ))}
      </RigidBody>

      {/* Tuong bien vo hinh */}
      {walls.length > 0 && (
        <RigidBody type="fixed" colliders={false}>
          {walls.map((w, i) => (
            <CuboidCollider key={i} position={w.pos} args={w.args} />
          ))}
        </RigidBody>
      )}

      {/* Che do ?debug: hien vung ZONE_ va diem ITEM_ */}
      {debug && zones.map((z) => (
        <box3Helper key={z.obj} args={[z.box, 0xffaa00]} />
      ))}
      {debug && items.map((it) => (
        <mesh key={it.id} position={it.pos}>
          <sphereGeometry args={[0.5, 12, 8]} />
          <meshBasicMaterial color="#ff3366" wireframe />
        </mesh>
      ))}

      {/* Nhan ten noi tren moi toa */}
      {buildings.map((b) => (
        <Html key={b.name} position={b.center} center distanceFactor={60} zIndexRange={[10, 0]}>
          <div className="label">{zoneInfo(b.name).title}</div>
        </Html>
      ))}
    </>
  );
}

useGLTF.preload(MODEL_URL);
