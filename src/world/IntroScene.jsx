import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { useFrame, useThree } from "@react-three/fiber";
import { useGLTF, CameraControls, Html } from "@react-three/drei";
import { MODEL_URL, splitScene } from "./campusModel";
import { useGame } from "../game/store";
import { zoneInfo } from "../data/zones";

// Thu tu cac toa trong chuyen tham quan (key = ten object Blender)
const TOUR = ["BLD_A", "BLD_E", "BLD_B", "BLD_C", "BLD_CanTin"];

// Cong chinh (toa do Blender trong uit_detail.py, bien GATE) doi sang three: (x, y) -> (x, -y)
const GATE_POS = new THREE.Vector3(-71.2, 0, -12.5);
const GATE_DIR = new THREE.Vector3(20, 0, 7).normalize();

const isWide = () => window.innerWidth > 900;

// Diem nhin toan canh (che do trang chu): xa, cao, nhin cheo -> mo hinh trong nhu sa ban thu nho
// k: lui camera xa them (man hinh doc hep ngang thi phai lui nhieu hon moi thay het)
function overview(bounds, k = 1) {
  const c = bounds.getCenter(new THREE.Vector3());
  const r = bounds.getSize(new THREE.Vector3()).length() / 2;
  return { cam: [c.x + r * 1.75 * k, r * 1.35 * k, c.z + r * 1.75 * k], target: [c.x, 0, c.z], r };
}

// Tao cac diem dung cua chuyen tham quan tu du lieu toa nha
function makeStops(buildings, bounds) {
  const c = bounds.getCenter(new THREE.Vector3());
  const ov = overview(bounds);
  const stops = [
    {
      key: "overview",
      title: "Toàn cảnh khuôn viên",
      subtitle: "Khu phố Tân Lập · Linh Trung · Thủ Đức",
      description:
        "Khuôn viên UIT nằm trong Khu đô thị ĐHQG-HCM. Chuyến tham quan sẽ đưa bạn qua cổng chính và các tòa nhà chính, sau đó bạn có thể tự do đi lại.",
      cam: [c.x - ov.r * 0.15, ov.r * 0.75, c.z + ov.r * 0.85],
      target: [c.x, 0, c.z],
    },
    {
      key: "gate",
      title: "Cổng chính",
      subtitle: "Lối vào",
      description: "Đường vào có dải bồn cây ở giữa, hai bên là bãi cỏ và hàng cây lớn. Bên trái là tòa A, bên phải là tòa E.",
      cam: GATE_POS.clone().addScaledVector(GATE_DIR, -32).setY(16).toArray(),
      target: GATE_POS.clone().addScaledVector(GATE_DIR, 22).setY(4).toArray(),
      ring: { x: GATE_POS.x + GATE_DIR.x * 8, z: GATE_POS.z + GATE_DIR.z * 8, r: 10 },
    },
  ];
  for (const key of TOUR) {
    const b = buildings.find((x) => x.name === key);
    if (!b) continue;
    const bc = b.box.getCenter(new THREE.Vector3());
    const size = b.box.getSize(new THREE.Vector3());
    const span = Math.max(size.x, size.z);
    // nhin tu phia ngoai khuon vien vao (huong tu tam truong ra toa), lech mot chut cho co chieu sau
    const dir = new THREE.Vector3(bc.x - c.x, 0, bc.z - c.z);
    if (dir.lengthSq() < 100) dir.set(1, 0, 1);
    dir.normalize().applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.35);
    const dist = span * 0.8 + size.y * 0.9 + 30;
    const info = zoneInfo(key);
    stops.push({
      key,
      ...info,
      cam: [bc.x + dir.x * dist, size.y * 0.7 + 22, bc.z + dir.z * dist],
      target: [bc.x, size.y * 0.35, bc.z],
      ring: { x: bc.x, z: bc.z, r: span / 2 + 5 },
    });
  }
  stops.push({
    key: "end",
    title: "Sẵn sàng khám phá",
    subtitle: "Đến lượt bạn",
    description:
      "Đi bộ quanh trường, lại gần mỗi tòa để xem thông tin, mở bản đồ để đánh dấu điểm đến. Còn nhiều khu vực khác đang chờ bạn tìm ra.",
    cam: ov.cam.map((v, i) => (i === 1 ? v * 0.6 : c.toArray()[i] + (v - c.toArray()[i]) * 0.55)),
    target: [c.x, 0, c.z],
  });
  return stops;
}

// Vong sang nhap nho duoi chan toa dang tham quan
function Ring({ x, z, r, visible }) {
  const ref = useRef();
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    if (!ref.current) return;
    const s = 1 + 0.04 * Math.sin(t * 3);
    ref.current.scale.set(s, s, 1);
    ref.current.material.opacity = 0.55 + 0.25 * Math.sin(t * 3);
  });
  return (
    <mesh ref={ref} position={[x, 0.35, z]} rotation-x={-Math.PI / 2} visible={visible}>
      <ringGeometry args={[r, r + 1.4, 72]} />
      <meshBasicMaterial color="#ffd23f" transparent depthWrite={false} />
    </mesh>
  );
}

// Tim toa BLD_ chua object bi tro chuot
function buildingOf(o) {
  while (o) {
    if (o.name?.startsWith("BLD_")) return o.name;
    o = o.parent;
  }
  return null;
}

// Canh 3D cua trang chu + tham quan: dung chung mo hinh voi che do kham pha
export default function IntroScene() {
  const { scene } = useGLTF(MODEL_URL);
  const { deco, buildings, bounds } = useMemo(() => splitScene(scene), [scene]);
  const mode = useGame((s) => s.mode);
  const step = useGame((s) => s.tourStep);
  const setMode = useGame((s) => s.setMode);
  const setTourStops = useGame((s) => s.setTourStops);
  const stops = useMemo(() => makeStops(buildings, bounds), [buildings, bounds]);
  const ctrl = useRef();
  const camera = useThree((s) => s.camera);
  const [hover, setHover] = useState(null);
  const dragging = useRef(false);
  const center = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());

  useEffect(() => setTourStops(stops), [stops, setTourStops]);

  // bien dich san shader cua moi thu trong canh (ke ca bau troi, vong sang dang an) khi o trang chu,
  // de luc bam vao tham quan khong bi dung hinh vi phai bien dich giua chung
  const gl = useThree((s) => s.gl);
  const scene3 = useThree((s) => s.scene);
  useEffect(() => {
    gl.compileAsync(scene3, camera).catch(() => {});
  }, [gl, scene3, camera]);

  // nhin tu xa: tang near de mat dat va lop co (cach nhau 10 cm) khong nhap nhay; tra lai khi vao kham pha
  useEffect(() => {
    const old = camera.near;
    camera.near = mode === "intro" ? 8 : 1;
    camera.updateProjectionMatrix();
    return () => {
      camera.near = old;
      camera.updateProjectionMatrix();
    };
  }, [camera, mode]);

  // dat camera theo che do / diem dung
  useEffect(() => {
    const c = ctrl.current;
    if (!c) return;
    if (mode === "intro") {
      const aspect = window.innerWidth / window.innerHeight;
      const ov = overview(bounds, aspect < 1 ? Math.min(2.2, 1.15 / aspect) : 1);
      c.setLookAt(...ov.cam, ...ov.target, true);
      // goc xoay ngang cong don sau nhieu vong (tu xoay, keo chuot): dua ve goc gan nhat de khong tua nguoc nhieu vong
      c.normalizeRotations();
      // may tinh: mo hinh lech phai nhuong cho chu; dien thoai: mo hinh o nua tren, chu o duoi
      c.setFocalOffset(isWide() ? -ov.r * 0.55 : 0, isWide() ? -ov.r * 0.05 : ov.r * 0.5, 0, true);
    } else {
      const s = stops[Math.min(step, stops.length - 1)];
      c.setFocalOffset(isWide() ? -18 : 0, 0, 0, true);
      c.setLookAt(...s.cam, ...s.target, true);
      // goc xoay ngang cong don sau nhieu vong (tu xoay, keo chuot): dua ve goc gan nhat de khong tua nguoc nhieu vong
      c.normalizeRotations();
    }
  }, [mode, step, stops, bounds]);

  // ong kinh hep o trang chu -> cam giac sa ban thu nho; rong hon khi tham quan
  useFrame((_, dt) => {
    const fov = mode === "intro" ? 32 : 50;
    if (Math.abs(camera.fov - fov) > 0.05) {
      camera.fov = THREE.MathUtils.damp(camera.fov, fov, 3, dt);
      camera.updateProjectionMatrix();
    }
    // trang chu: mo hinh tu xoay cham khi khong keo
    if (mode === "intro" && ctrl.current && !dragging.current) ctrl.current.rotate(dt * 0.07, 0, true);
  });

  useEffect(() => {
    document.body.style.cursor = hover ? "pointer" : "";
    return () => (document.body.style.cursor = "");
  }, [hover]);

  const openBuilding = (name) => {
    const idx = stops.findIndex((s) => s.key === name);
    if (idx >= 0) setMode("tour", idx);
  };

  const hoverB = hover && buildings.find((b) => b.name === hover);
  const ring = mode === "tour" ? stops[step]?.ring : null;

  return (
    <>
      <CameraControls
        ref={ctrl}
        makeDefault
        smoothTime={mode === "intro" ? 0.9 : 0.7}
        minDistance={40}
        maxDistance={1400}
        maxPolarAngle={Math.PI * 0.45}
        onStart={() => (dragging.current = true)}
        onEnd={() => (dragging.current = false)}
      />

      <group
        onPointerMove={(e) => setHover(buildingOf(e.object))}
        onPointerOut={() => setHover(null)}
        onClick={(e) => {
          const b = buildingOf(e.object);
          if (b && e.delta < 6) {
            e.stopPropagation();
            openBuilding(b);
          }
        }}
      >
        <primitive object={scene} />
        <primitive object={deco} />
      </group>

      {/* be sa ban duoi mat dat */}
      <mesh position={[center.x, -7.02, center.z]} receiveShadow>
        <boxGeometry args={[size.x + 0.02, 14, size.z + 0.02]} />
        <meshStandardMaterial color="#efe4d2" roughness={0.9} />
      </mesh>
      <mesh position={[center.x, -14.6, center.z]}>
        <boxGeometry args={[size.x + 14, 1.2, size.z + 14]} />
        <meshStandardMaterial color="#1d2b55" roughness={0.6} />
      </mesh>

      {/* luon gan (chi an/hien) de shader duoc bien dich san o trang chu */}
      <Ring x={ring?.x ?? 0} z={ring?.z ?? 0} r={ring?.r ?? 10} visible={!!ring} />

      {hoverB && (
        <Html position={hoverB.center} center zIndexRange={[20, 0]} style={{ pointerEvents: "none" }}>
          <div className="intro-tip">
            <b>{zoneInfo(hoverB.name).title}</b>
            {TOUR.includes(hoverB.name) && <span>Bấm để xem</span>}
          </div>
        </Html>
      )}
      {mode === "tour" && stops[step] && TOUR.includes(stops[step].key) && (
        <Html
          position={buildings.find((b) => b.name === stops[step].key)?.center || [0, 0, 0]}
          center
          zIndexRange={[20, 0]}
          style={{ pointerEvents: "none" }}
        >
          <div className="label">{stops[step].title}</div>
        </Html>
      )}
    </>
  );
}
