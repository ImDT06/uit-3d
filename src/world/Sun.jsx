import { useEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { playerPos } from "../game/store";
import { LIGHT } from "./lighting";

const SUN = LIGHT.sun; // huong mat troi: vi tri den so voi diem duoc chieu
const CAMPUS_CENTER = [25, 0, 15]; // giua GND_Base (toa do three; Blender x -200..250, y -230..200)

// Mat troi + bong do.
// follow (che do kham pha): vung bong nho quanh nhan vat, di theo nhan vat -> cung kich thuoc shadow map
// ma bong sac hon nhieu lan. Khong follow (trang chu, tham quan): vung bong phu ca khuon vien.
// light (dien thoai): vung bong hep hon (bu anh bong nho), chi ve lai bong cach mot khung hinh
export default function Sun({ shadows, mapSize, follow, light: lite, color = LIGHT.sunColor, intensity = LIGHT.sunIntensity }) {
  const light = useRef();
  const scene = useThree((s) => s.scene);
  const R = follow ? (lite ? 45 : 60) : 260;
  const gl = useThree((s) => s.gl);
  const frame = useRef(0);

  useEffect(() => {
    if (!lite) return;
    gl.shadowMap.autoUpdate = false;
    return () => {
      gl.shadowMap.autoUpdate = true;
    };
  }, [gl, lite]);

  // target cua directionalLight phai nam trong scene thi moi cap nhat vi tri
  useEffect(() => {
    const t = light.current.target;
    scene.add(t);
    return () => scene.remove(t);
  }, [scene, follow, mapSize]);

  useFrame(() => {
    if (lite && frame.current++ % 2 === 0) gl.shadowMap.needsUpdate = true;
    const L = light.current;
    let [cx, , cz] = CAMPUS_CENTER;
    if (follow) {
      const step = ((2 * R) / mapSize) * 4; // lam tron theo o shadow map -> bong khong rung khi di
      cx = Math.round(playerPos.x / step) * step;
      cz = Math.round(playerPos.z / step) * step;
    }
    L.position.set(cx + SUN[0], SUN[1], cz + SUN[2]);
    L.target.position.set(cx, 0, cz);
    L.target.updateMatrixWorld();
  });

  return (
    <directionalLight
      key={`${mapSize}-${follow}-${R}`}
      ref={light}
      intensity={intensity}
      color={color}
      castShadow={shadows}
      shadow-mapSize={[mapSize, mapSize]}
      shadow-camera-left={-R}
      shadow-camera-right={R}
      shadow-camera-top={R}
      shadow-camera-bottom={-R}
      shadow-camera-near={10}
      shadow-camera-far={500}
      shadow-bias={-0.0002}
      shadow-normalBias={follow ? 0.03 : 0.3}
      shadow-radius={LIGHT.shadowRadius ?? 1} // mep bong mem
    />
  );
}
