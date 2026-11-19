import { Component, Suspense, useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { KeyboardControls, Sky, PerformanceMonitor } from "@react-three/drei";
import { Physics } from "@react-three/rapier";
import Campus, { MODEL_URL } from "./world/Campus";
import Player from "./world/Player";
import Hud, { Loading } from "./ui/Hud";
import Admin from "./ui/Admin";
import Waypoint from "./world/Waypoint";
import IntroScene from "./world/IntroScene";
import IntroUi from "./ui/IntroUi";
import { useGame } from "./game/store";
import { useSettings, HOLD_ACTIONS } from "./game/settings";
import { useHotkeys } from "./game/actions";

// Muc chat luong do hoa: do phan giai + bong do
const QUALITY = {
  low: { dpr: 0.75, shadows: false, mapSize: 1024 },
  medium: { dpr: 1, shadows: true, mapSize: 2048 },
  high: { dpr: Math.min(window.devicePixelRatio || 1, 2), shadows: true, mapSize: 4096 },
};

// Bat loi khi chua co file mo hinh
class ModelErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      const msg = String(this.state.error?.message || this.state.error);
      if (/webgl/i.test(msg)) {
        return (
          <div className="error">
            <h2>Trình duyệt chưa bật đồ họa 3D</h2>
            <p>
              Trang này cần WebGL. Hãy bật <b>Use graphics acceleration when available</b> trong cài đặt trình
              duyệt (Settings → System), khởi động lại trình duyệt rồi tải lại trang. Nếu vẫn lỗi, thử Chrome
              hoặc Edge bản mới nhất.
            </p>
            <pre>{msg}</pre>
          </div>
        );
      }
      return (
        <div className="error">
          <h2>Không tải được mô hình</h2>
          <p>
            Không tìm thấy <code>public{MODEL_URL}</code>. Hãy chạy script <code>uit_export.py</code> trong
            Blender để xuất file, rồi tải lại trang.
          </p>
          <pre>{msg}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const debug = useGame((s) => s.physicsDebug);
  const mode = useGame((s) => s.mode);
  const explore = mode === "explore";
  const paused = useGame((s) => s.menuOpen || s.mapOpen);
  const binds = useSettings((s) => s.binds);
  const quality = useSettings((s) => s.quality);
  const [autoLevel, setAutoLevel] = useState("medium");
  const q = QUALITY[quality === "auto" ? autoLevel : quality];
  useHotkeys();

  // bang phim giu (di, nhay, chay) lay tu cai dat, doi phim la cap nhat ngay
  const keyboardMap = useMemo(() => HOLD_ACTIONS.map((name) => ({ name, keys: binds[name] || [] })), [binds]);

  return (
    <ModelErrorBoundary>
      <KeyboardControls map={keyboardMap}>
        <Canvas
          shadows
          dpr={q.dpr}
          camera={{ fov: 55, near: 0.1, far: 3000, position: [0, 30, 40] }}
          onContextMenu={(e) => e.preventDefault()}
          gl={{ alpha: true }}
          className={`scene scene-${mode}`}
        >
          {/* che do Tu dong: may chay muot thi tang, giat thi giam chat luong */}
          {quality === "auto" && (
            <PerformanceMonitor
              onIncline={() => setAutoLevel((l) => (l === "low" ? "medium" : "high"))}
              onDecline={() => setAutoLevel((l) => (l === "high" ? "medium" : "low"))}
              flipflops={3}
            />
          )}
          {/* trang chu: nen trong suot (nen CSS phia sau), khong suong mu de thay ca sa ban */}
          {mode !== "intro" && <color attach="background" args={["#bfe3ff"]} />}
          {mode !== "intro" && <fog attach="fog" args={["#bfe3ff", 150, 650]} />}
          {mode !== "intro" && <Sky sunPosition={[120, 80, 60]} />}
          <hemisphereLight args={["#ffffff", "#8a8f7a", 0.8]} />
          <directionalLight
            key={q.mapSize}
            position={[120, 160, 80]}
            intensity={2}
            castShadow={q.shadows}
            shadow-mapSize={[q.mapSize, q.mapSize]}
            shadow-camera-left={-250}
            shadow-camera-right={250}
            shadow-camera-top={250}
            shadow-camera-bottom={-250}
            shadow-camera-far={600}
            shadow-bias={-0.0005}
          />
          <Suspense fallback={null}>
            {explore ? (
              <>
                <Physics debug={debug} paused={paused}>
                  <Campus />
                  <Player />
                </Physics>
                <Waypoint />
              </>
            ) : (
              <IntroScene />
            )}
          </Suspense>
        </Canvas>
        {explore ? (
          <>
            <Hud />
            <Admin />
            <div className="fade-in" />
          </>
        ) : (
          <IntroUi />
        )}
        <Loading />
      </KeyboardControls>
    </ModelErrorBoundary>
  );
}
