import { useEffect, useMemo } from "react";
import { useGLTF, Html } from "@react-three/drei";
import { RigidBody, CylinderCollider, CuboidCollider, ConvexHullCollider } from "@react-three/rapier";
import { useGame } from "../game/store";
import { zoneInfo, LANDMARKS } from "../data/zones";
import { MODEL_URL, splitScene } from "./campusModel";

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
  const setGameplay = useGame((s) => s.setGameplay);
  const debug = useGame((s) => s.physicsDebug);
  const { deco, trees, buildings, camBlockers, camGround, walls, zones, items, solids, landmarks } = useMemo(() => splitScene(scene), [scene]);

  useEffect(() => {
    setGameplay(zones, items);
  }, [zones, items, setGameplay]);

  useEffect(() => {
    // object SPAWN (empty) trong glb thi dung lam diem xuat phat (vd ban thu MyUIT nguyen ban, khong co BLD_)
    const sp = scene.getObjectByName("SPAWN");
    const spawn = sp ? [sp.position.x, sp.position.y + 2, sp.position.z] : findSpawn(buildings.map((b) => b.box));
    setWorld(spawn, buildings, camBlockers, camGround);
  }, [scene, buildings, camBlockers, camGround, setWorld]);

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
            <CuboidCollider key={i} position={w.pos} rotation={w.rot} args={w.args} />
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
      {/* Nhan cong A / cong B */}
      {landmarks.map((l) => (
        <Html key={l.name} position={l.center} center distanceFactor={60} zIndexRange={[10, 0]}>
          <div className="label">{LANDMARKS[l.name]}</div>
        </Html>
      ))}
    </>
  );
}

