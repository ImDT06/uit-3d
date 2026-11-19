import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useGame } from "../game/store";

// Cot sang danh dau diem dich tren ban do (nhin thay tu xa)
export default function Waypoint() {
  const wp = useGame((s) => s.waypoint);
  const ring = useRef();
  useFrame((state) => {
    if (!ring.current) return;
    const t = state.clock.elapsedTime;
    ring.current.scale.setScalar(1 + (t % 1.5) * 0.8);
    ring.current.material.opacity = 0.6 * (1 - (t % 1.5) / 1.5);
  });
  if (!wp) return null;
  return (
    <group position={[wp.x, 0, wp.z]}>
      <mesh position={[0, 30, 0]}>
        <cylinderGeometry args={[0.6, 0.6, 80, 16, 1, true]} />
        <meshBasicMaterial color="#ffd23f" transparent opacity={0.35} depthWrite={false} />
      </mesh>
      <mesh ref={ring} position={[0, 0.15, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.2, 1.6, 32]} />
        <meshBasicMaterial color="#ffd23f" transparent opacity={0.6} depthWrite={false} />
      </mesh>
    </group>
  );
}
