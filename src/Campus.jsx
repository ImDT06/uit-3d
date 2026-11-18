import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { useGLTF, Html } from "@react-three/drei";
import { RigidBody, CylinderCollider } from "@react-three/rapier";
import { useGame } from "./store";
import { zoneInfo } from "./zones";

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
function splitScene(scene) {
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
  const buildings = scene.children
    .filter((o) => o.name.startsWith("BLD_"))
    .map((o) => {
      const box = new THREE.Box3().setFromObject(o);
      const c = box.getCenter(new THREE.Vector3());
      return { name: o.name, box, center: [c.x, box.max.y + 3, c.z] };
    });
  // luoi chan camera (camera khong xuyen qua toa nha)
  const camBlockers = [];
  scene.children
    .filter((o) => o.name.startsWith("BLD_"))
    .forEach((o) => o.traverse((m) => m.isMesh && camBlockers.push(m)));
  scene.userData.split = { deco, trees, buildings, camBlockers };
  return scene.userData.split;
}

export default function Campus() {
  const { scene } = useGLTF(MODEL_URL);
  const setWorld = useGame((s) => s.setWorld);
  const { deco, trees, buildings, camBlockers } = useMemo(() => splitScene(scene), [scene]);

  useEffect(() => {
    setWorld(findSpawn(buildings.map((b) => b.box)), buildings, camBlockers);
  }, [buildings, camBlockers, setWorld]);

  return (
    <>
      {/* Toa nha, mat dat, loi di: va cham theo luoi tam giac */}
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
