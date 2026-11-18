import { Component, Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { KeyboardControls, Sky } from "@react-three/drei";
import { Physics } from "@react-three/rapier";
import Campus, { MODEL_URL } from "./Campus";
import Player from "./Player";
import Hud, { Loading } from "./Hud";

const keyboardMap = [
  { name: "forward", keys: ["ArrowUp", "KeyW"] },
  { name: "backward", keys: ["ArrowDown", "KeyS"] },
  { name: "leftward", keys: ["ArrowLeft", "KeyA"] },
  { name: "rightward", keys: ["ArrowRight", "KeyD"] },
  { name: "jump", keys: ["Space"] },
  { name: "run", keys: ["Shift"] },
];

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
  const debug = new URLSearchParams(window.location.search).has("debug");
  return (
    <ModelErrorBoundary>
      <KeyboardControls map={keyboardMap}>
        <Canvas shadows dpr={[1, 1.5]} gl={{ powerPreference: "high-performance", antialias: true }} camera={{ fov: 55, near: 0.1, far: 3000, position: [0, 30, 40] }}>
          <color attach="background" args={["#bfe3ff"]} />
          <fog attach="fog" args={["#bfe3ff", 150, 650]} />
          <Sky sunPosition={[120, 80, 60]} />
          <hemisphereLight args={["#ffffff", "#8a8f7a", 0.8]} />
          <directionalLight
            position={[120, 160, 80]}
            intensity={2}
            castShadow
            shadow-mapSize={[2048, 2048]}
            shadow-camera-left={-180}
            shadow-camera-right={180}
            shadow-camera-top={180}
            shadow-camera-bottom={-180}
            shadow-camera-far={600}
            shadow-bias={-0.0005}
          />
          <Suspense fallback={null}>
            <Physics debug={debug}>
              <Campus />
              <Player />
            </Physics>
          </Suspense>
        </Canvas>
        <Hud />
        <Loading />
      </KeyboardControls>
    </ModelErrorBoundary>
  );
}
