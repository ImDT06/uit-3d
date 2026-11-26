import { useEffect, useMemo, useRef } from "react";
import { useFrame, useGraph } from "@react-three/fiber";
import { useGLTF, useAnimations } from "@react-three/drei";
import { clone } from "three/examples/jsm/utils/SkeletonUtils.js";

// Mo hinh nhan vat (public/models/nv_nam.glb, nv_nu.glb, dung bang tools/blender/uit_nhanvat.py).
// Chan o y = 0, cao ~1,85 m, mat nhin ve +Z. Toc dai la object ToDai (chi ban nu).
// drive(actions, dt): moi frame chinh trong so cac dong tac; bo trong thi chi dung yen.
export default function Avatar({ gender = "nam", hair = "ngan", drive }) {
  const { scene, animations } = useGLTF(`${import.meta.env.BASE_URL}models/nv_${gender}.glb`);
  const model = useMemo(() => clone(scene), [scene]);
  const { nodes } = useGraph(model);
  const root = useRef();
  const { actions } = useAnimations(animations, root);

  useEffect(() => {
    model.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = true;
      o.frustumCulled = false; // luoi co xuong: hop bao tinh theo tu the goc, de bi cat nham
    });
  }, [model]);

  useEffect(() => {
    // toc dai co the la mot luoi hoac mot nhom luoi
    if (nodes.ToDai) nodes.ToDai.visible = hair === "dai";
  }, [nodes, hair]);

  useEffect(() => {
    // actions cua drei la getter: lay ra truoc, luc don dep thi bo nho dem cua no da bi xoa
    const list = Object.entries(actions);
    for (const [name, a] of list) {
      a.reset().play();
      a.setEffectiveWeight(name === "Idle" ? 1 : 0);
    }
    return () => list.forEach(([, a]) => a.stop());
  }, [actions]);

  useFrame((_, dt) => drive?.(actions, Math.min(dt, 0.05)));

  return (
    <group ref={root}>
      <primitive object={model} />
    </group>
  );
}
