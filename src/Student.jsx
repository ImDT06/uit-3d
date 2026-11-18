import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

// Nhan vat sinh vien low-poly, dung bang khoi hinh hoc (khong can file model).
// Goc toa do = tam vien nhong va cham; ban chan o y = -1.0. Mat nhin ve +Z.
const C = {
  skin: "#f1c7a3",
  hair: "#2b211c",
  shirt: "#f4f6fb",
  pants: "#273a6b",
  shoe: "#1d1d22",
  bag: "#2f5bd3",
  bagStrap: "#1d3c94",
};

function useMats() {
  return useMemo(() => {
    const m = {};
    for (const [k, v] of Object.entries(C)) {
      m[k] = new THREE.MeshStandardMaterial({ color: v, flatShading: true, roughness: 0.8 });
    }
    return m;
  }, []);
}

function Limb({ refObj, position, size, mat, end, endMat, endSize }) {
  // nhom xoay quanh khop (vai / hong), chi treo xuong duoi
  return (
    <group ref={refObj} position={position}>
      <mesh castShadow position={[0, -size[1] / 2, 0]} material={mat}>
        <boxGeometry args={size} />
      </mesh>
      {end && (
        <mesh castShadow position={[0, -size[1] - endSize[1] / 2 + 0.02, end]} material={endMat}>
          <boxGeometry args={endSize} />
        </mesh>
      )}
    </group>
  );
}

export default function Student({ controller, hidden = false }) {
  const m = useMats();
  const root = useRef();
  const body = useRef();
  const legL = useRef();
  const legR = useRef();
  const armL = useRef();
  const armR = useRef();
  const phase = useRef(0);
  const air = useRef(0);

  useFrame((state, dt) => {
    const c = controller.current;
    if (!c || !legL.current) return;
    const d = Math.min(dt, 0.05);
    const speed = c.relativeVelOnPlane ? c.relativeVelOnPlane.length() : 0;
    const moving = speed > 0.3;
    const inAir = !c.isOnGround;

    // pha buoc chan theo toc do
    phase.current += d * (3 + speed * 1.6) * (moving ? 1 : 0);
    const amp = Math.min(speed / 5, 1) * 0.85;
    air.current = THREE.MathUtils.damp(air.current, inAir ? 1 : 0, 10, d);
    const s = Math.sin(phase.current);

    const walkLeg = s * amp;
    const walkArm = s * amp * 0.9;
    const a = air.current;
    const lerp = THREE.MathUtils.lerp;

    legL.current.rotation.x = lerp(walkLeg, -0.9, a);
    legR.current.rotation.x = lerp(-walkLeg, 0.35, a);
    armL.current.rotation.x = lerp(-walkArm, -2.4, a);
    armR.current.rotation.x = lerp(walkArm, -2.4, a);
    armL.current.rotation.z = lerp(0.06, 0.35, a);
    armR.current.rotation.z = lerp(-0.06, -0.35, a);

    // nhun nguoi khi di, tho nhe khi dung yen
    const t = state.clock.elapsedTime;
    const bob = moving ? Math.abs(Math.cos(phase.current)) * 0.05 * amp : Math.sin(t * 2) * 0.008;
    body.current.position.y = bob;
    body.current.rotation.x = THREE.MathUtils.damp(body.current.rotation.x, moving ? 0.08 * amp : 0, 8, d);

    // nghieng nguoi vao trong khi re (theo toc do quay quanh truc dung)
    const turn = c.currAngVel ? c.currAngVel.y : 0;
    const lean = THREE.MathUtils.clamp(-turn * speed * 0.025, -0.3, 0.3);
    root.current.rotation.z = THREE.MathUtils.damp(root.current.rotation.z, moving && !inAir ? lean : 0, 6, d);
  });

  return (
    <group ref={root} visible={!hidden}>
      <group ref={body}>
        {/* chan */}
        <Limb refObj={legL} position={[0.11, -0.16, 0]} size={[0.16, 0.74, 0.18]} mat={m.pants}
              end={0.04} endMat={m.shoe} endSize={[0.17, 0.1, 0.28]} />
        <Limb refObj={legR} position={[-0.11, -0.16, 0]} size={[0.16, 0.74, 0.18]} mat={m.pants}
              end={0.04} endMat={m.shoe} endSize={[0.17, 0.1, 0.28]} />

        {/* than: quan + ao */}
        <mesh castShadow position={[0, -0.1, 0]} material={m.pants}>
          <boxGeometry args={[0.42, 0.16, 0.24]} />
        </mesh>
        <mesh castShadow position={[0, 0.17, 0]} material={m.shirt}>
          <boxGeometry args={[0.46, 0.5, 0.26]} />
        </mesh>
        {/* co ao */}
        <mesh position={[0, 0.43, 0.02]} material={m.shirt}>
          <boxGeometry args={[0.22, 0.05, 0.2]} />
        </mesh>

        {/* tay */}
        <Limb refObj={armL} position={[0.3, 0.38, 0]} size={[0.12, 0.5, 0.14]} mat={m.shirt}
              end={0} endMat={m.skin} endSize={[0.11, 0.1, 0.11]} />
        <Limb refObj={armR} position={[-0.3, 0.38, 0]} size={[0.12, 0.5, 0.14]} mat={m.shirt}
              end={0} endMat={m.skin} endSize={[0.11, 0.1, 0.11]} />

        {/* dau */}
        <group position={[0, 0.66, 0]}>
          <mesh castShadow material={m.skin}>
            <icosahedronGeometry args={[0.2, 1]} />
          </mesh>
          {/* toc */}
          <mesh castShadow position={[0, 0.06, -0.03]} scale={[1.05, 0.8, 1.05]} material={m.hair}>
            <icosahedronGeometry args={[0.2, 1]} />
          </mesh>
          {/* mat */}
          <mesh position={[0.07, -0.01, 0.185]} material={m.hair}>
            <boxGeometry args={[0.04, 0.05, 0.02]} />
          </mesh>
          <mesh position={[-0.07, -0.01, 0.185]} material={m.hair}>
            <boxGeometry args={[0.04, 0.05, 0.02]} />
          </mesh>
        </group>

        {/* balo */}
        <mesh castShadow position={[0, 0.17, -0.22]} material={m.bag}>
          <boxGeometry args={[0.38, 0.44, 0.17]} />
        </mesh>
        <mesh castShadow position={[0, 0.06, -0.32]} material={m.bagStrap}>
          <boxGeometry args={[0.3, 0.16, 0.05]} />
        </mesh>
        <mesh position={[0.15, 0.22, 0.135]} material={m.bagStrap}>
          <boxGeometry args={[0.05, 0.46, 0.02]} />
        </mesh>
        <mesh position={[-0.15, 0.22, 0.135]} material={m.bagStrap}>
          <boxGeometry args={[0.05, 0.46, 0.02]} />
        </mesh>
      </group>
    </group>
  );
}
