import { Component, Suspense, lazy, useEffect, useMemo, useState } from "react";
import { NeutralToneMapping } from "three";
import { Canvas } from "@react-three/fiber";
import { KeyboardControls, PerformanceMonitor } from "@react-three/drei";
import { MODEL_URL } from "./world/campusModel";
import Sun from "./world/Sun";
import Atmosphere from "./world/Atmosphere";
import { LIGHT } from "./world/lighting";
import Loading, { PreparingExplore } from "./ui/Loading";
import FpsMeter, { fpsEnabled } from "./ui/FpsMeter";
import IntroScene from "./world/IntroScene";
import IntroUi from "./ui/IntroUi";
import BuildingPreview, { previewName } from "./world/BuildingPreview";
import PreviewUi from "./ui/PreviewUi";
import { useGame } from "./game/store";
import { useSettings, HOLD_ACTIONS } from "./game/settings";
import { useHotkeys } from "./game/actions";

// Che do kham pha (vat ly Rapier ~2 MB, nhan vat, HUD) tai rieng: trang chu mo nhanh hon.
// Tai truoc ngam khi dang o trang chu de bam "Vao kham pha" la vao ngay.
const loadExplore = () => import("./world/Explore");
const loadExploreUi = () => import("./ui/ExploreUi");
const Explore = lazy(loadExplore);
const ExploreUi = lazy(loadExploreUi);

// Muc chat luong do hoa: do phan giai + bong do
const QUALITY = {
  low: { dpr: 0.75, shadows: false, mapSize: 1024 },
  medium: { dpr: 1, shadows: true, mapSize: 2048 },
  high: { dpr: Math.min(window.devicePixelRatio || 1, 2), shadows: true, mapSize: 4096 },
};

// Hieu ung hinh anh (world/Effects.jsx): chi o chat luong Cao tren may co chuot; ?fx=0 tat, ?fx=1 ep bat
const fxParam = new URLSearchParams(window.location.search).get("fx");
const coarse = window.matchMedia("(pointer: coarse)").matches;
// Man hinh cam ung: anh bong nho hon (ve lai bong chiem phan lon khoi luong), che do Tu dong khong len muc Cao
const MOBILE_MAP = 1024;

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
  const mode = useGame((s) => s.mode);
  const explore = mode === "explore";
  const binds = useSettings((s) => s.binds);
  const quality = useSettings((s) => s.quality);
  const [autoLevel, setAutoLevel] = useState("medium");
  const level = quality === "auto" ? autoLevel : quality;
  const q = coarse ? { ...QUALITY[level], mapSize: Math.min(QUALITY[level].mapSize, level === "high" ? 2048 : MOBILE_MAP) } : QUALITY[level];
  const effects = fxParam ? fxParam === "1" : level === "high" && !coarse;
  useHotkeys();

  // o trang chu/tham quan: doi trang yen roi tai ngam phan kham pha
  useEffect(() => {
    if (explore || previewName) return;
    const t = setTimeout(() => {
      loadExplore();
      loadExploreUi();
    }, 2500);
    return () => clearTimeout(t);
  }, [explore]);

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
          // Neutral: giu mau vat lieu tuoi hon ACES (mac dinh cua R3F, lam mau xin, nga xam)
          gl={{ alpha: true, toneMapping: NeutralToneMapping }}
          onCreated={(state) => {
            if (import.meta.env.DEV) window.__uitR3f = state; // cho script kiem thu doc renderer.info
          }}
          className={`scene scene-${mode}`}
        >
          {/* che do Tu dong: may chay muot thi tang, giat thi giam chat luong */}
          {quality === "auto" && (
            <PerformanceMonitor
              onIncline={() => setAutoLevel((l) => (l === "low" || coarse ? "medium" : "high"))}
              onDecline={() => setAutoLevel((l) => (l === "high" ? "medium" : "low"))}
              flipflops={3}
            />
          )}
          {/* trang chu: nen trong suot (nen CSS phia sau), khong suong mu; vao tham quan thi troi/suong mu hien dan */}
          <Atmosphere on={mode !== "intro" || !!previewName} fog={!previewName} />
          <hemisphereLight args={LIGHT.hemi} />
          <Sun shadows={q.shadows} mapSize={q.mapSize} follow={explore} light={coarse} />
          <Suspense fallback={null}>
            {previewName ? <BuildingPreview name={previewName} /> : explore ? <Explore effects={effects} /> : <IntroScene />}
          </Suspense>
        </Canvas>
        {previewName ? (
          <PreviewUi name={previewName} />
        ) : explore ? (
          <Suspense fallback={<PreparingExplore />}>
            <ExploreUi />
          </Suspense>
        ) : (
          <IntroUi />
        )}
        <Loading />
        {fpsEnabled && <FpsMeter />}
      </KeyboardControls>
    </ModelErrorBoundary>
  );
}
