import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { useGLTF, Html } from "@react-three/drei";
import { RigidBody } from "@react-three/rapier";
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

export default function Campus() {
  const { scene } = useGLTF(MODEL_URL);
  const setWorld = useGame((s) => s.setWorld);

  const buildings = useMemo(() => {
    scene.updateMatrixWorld(true);
    const list = [];
    scene.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });
    scene.children.forEach((o) => {
      if (o.name.startsWith("BLD_")) {
        const box = new THREE.Box3().setFromObject(o);
        const c = box.getCenter(new THREE.Vector3());
        list.push({ name: o.name, box, center: [c.x, box.max.y + 3, c.z] });
      }
    });
    return list;
  }, [scene]);

  useEffect(() => {
    setWorld(findSpawn(buildings.map((b) => b.box)), buildings);
  }, [buildings, setWorld]);

  return (
    <>
      {/* Va cham: dung chinh mo hinh. Sau nay thay bang file collider rieng cho nhe hon */}
      <RigidBody type="fixed" colliders="trimesh">
        <primitive object={scene} />
      </RigidBody>

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
