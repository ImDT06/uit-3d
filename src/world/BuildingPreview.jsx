// Che do xem rieng mot toa (?toa=C): chi hien BLD_<ten> + chi tiet, xoay/zoom bang chuot de duyet mo hinh
// truoc khi dua vao ban chung. Khong tai vat ly, khong nhan vat.
import { useLayoutEffect, useMemo } from "react";
import * as THREE from "three";
import { useThree } from "@react-three/fiber";
import { useGLTF, OrbitControls } from "@react-three/drei";
import { MODEL_URL, splitScene } from "./campusModel";

export const previewName = (() => {
  const v = new URLSearchParams(window.location.search).get("toa");
  if (v === null) return null;
  return v.startsWith("BLD_") ? v : "BLD_" + v;
})();

export default function BuildingPreview({ name }) {
  const { scene } = useGLTF(MODEL_URL);
  splitScene(scene);
  const target = scene.getObjectByName(name);

  const camera = useThree((s) => s.camera);
  const box = useMemo(() => (target ? new THREE.Box3().setFromObject(target) : null), [target]);

  useLayoutEffect(() => {
    scene.children.forEach((o) => (o.visible = o === target));
    if (!box) return;
    // dat camera cheo phia truoc-phai, nhin bao tron toa
    const c = box.getCenter(new THREE.Vector3());
    const r = box.getSize(new THREE.Vector3()).length() / 2;
    camera.position.set(c.x + r * 0.9, c.y + r * 0.5, c.z + r * 1.3);
  }, [scene, target, box, camera]);
  if (!target) return null;
  const c = box.getCenter(new THREE.Vector3());
  const r = box.getSize(new THREE.Vector3()).length() / 2;

  return (
    <>
      <primitive object={scene} />
      <mesh rotation-x={-Math.PI / 2} position={[c.x, box.min.y - 0.02, c.z]} receiveShadow>
        <circleGeometry args={[r * 1.6, 48]} />
        <meshStandardMaterial color="#9fbf8a" />
      </mesh>
      <OrbitControls
        makeDefault
        target={[c.x, c.y * 0.6, c.z]}
        maxPolarAngle={Math.PI / 2 - 0.02}
        minDistance={5}
        maxDistance={r * 5}
      />
    </>
  );
}
