import { useEffect, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useKeyboardControls } from "@react-three/drei";
import { Ecctrl } from "ecctrl";
import { EcctrlCameraControls } from "ecctrl/camera";
import { useJoystickStore, useButtonStore } from "ecctrl/input";
import { useGame } from "./store";

const ZONE_MARGIN = 8; // m: dung cach toa nha bao nhieu thi tinh la "o gan"

// Nhan vat tam: vien nhong mau cam co "mui" de biet huong
function Character() {
  return (
    <group>
      <mesh castShadow position={[0, 0, 0]}>
        <capsuleGeometry args={[0.3, 1.0, 8, 16]} />
        <meshStandardMaterial color="#ff8a3d" />
      </mesh>
      <mesh castShadow position={[0, 0.35, 0.28]}>
        <boxGeometry args={[0.3, 0.12, 0.12]} />
        <meshStandardMaterial color="#222" />
      </mesh>
    </group>
  );
}

export default function Player() {
  const spawn = useGame((s) => s.spawn);
  const buildings = useGame((s) => s.buildings);
  const setZone = useGame((s) => s.setZone);
  const ecctrl = useRef(null);
  const cam = useRef(null);
  const [, getKeys] = useKeyboardControls();
  const lastZoneCheck = useRef(0);

  // dat camera sau lung nhan vat luc bat dau
  useEffect(() => {
    if (spawn && cam.current) {
      cam.current.setLookAt(spawn[0], spawn[1] + 6, spawn[2] + 12, spawn[0], spawn[1], spawn[2], false);
    }
  }, [spawn]);

  useFrame((state) => {
    const c = ecctrl.current;
    if (!c) return;

    // 1. Ban phim + joystick dien thoai -> nhan vat
    const k = getKeys();
    const joy = useJoystickStore.getState().joysticks.move;
    const btn = useButtonStore.getState().buttons;
    c.setMovement({
      forward: k.forward,
      backward: k.backward,
      leftward: k.leftward,
      rightward: k.rightward,
      run: k.run || !!btn.run,
      jump: k.jump || !!btn.jump,
      joystick: joy ? { x: joy.x, y: joy.y } : { x: 0, y: 0 },
    });

    // 2. Camera di theo nhan vat (chuot keo de xoay, lan chuot de zoom)
    const p = c.currPos;
    cam.current?.moveTo(p.x, p.y + 0.8, p.z, true);

    // 3. Roi khoi ban do -> dua ve cho cu
    if (p.y < -20 && spawn) {
      c.body.setTranslation({ x: spawn[0], y: spawn[1], z: spawn[2] }, true);
      c.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
    }

    // 4. Kiem tra dang o gan toa nao (5 lan/giay)
    if (state.clock.elapsedTime - lastZoneCheck.current > 0.2) {
      lastZoneCheck.current = state.clock.elapsedTime;
      let best = null;
      let bestD = ZONE_MARGIN;
      for (const b of buildings) {
        const dx = Math.max(b.box.min.x - p.x, 0, p.x - b.box.max.x);
        const dz = Math.max(b.box.min.z - p.z, 0, p.z - b.box.max.z);
        const d = Math.hypot(dx, dz);
        if (d < bestD) {
          bestD = d;
          best = b.name;
        }
      }
      setZone(best);
    }
  });

  if (!spawn) return null;

  return (
    <>
      <Ecctrl
        ref={ecctrl}
        position={spawn}
        capsuleHalfHeight={0.5}
        capsuleRadius={0.3}
        maxWalkVel={4}
        maxRunVel={9}
        jumpVel={5}
      >
        <Character />
      </Ecctrl>
      <EcctrlCameraControls
        ref={cam}
        makeDefault
        smoothTime={0.15}
        minDistance={3}
        maxDistance={40}
        maxPolarAngle={Math.PI * 0.48}
      />
    </>
  );
}
