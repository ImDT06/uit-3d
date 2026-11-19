import { useProgress } from "@react-three/drei";

// Man hinh tai mo hinh (dung chung moi che do)
export default function Loading() {
  const { progress, active } = useProgress();
  if (!active && progress >= 100) return null;
  return (
    <div className="loading">
      <div className="loading-title">UIT 3D</div>
      <div className="bar">
        <div style={{ width: `${progress}%` }} />
      </div>
      <div className="loading-text">Đang tải khuôn viên... {progress.toFixed(0)}%</div>
    </div>
  );
}

// Hien trong luc tai phan kham pha (vat ly, nhan vat) lan dau, thuong chi thoang qua
export function PreparingExplore() {
  return (
    <div className="loading loading-soft">
      <div className="loading-text">Đang chuẩn bị chế độ khám phá...</div>
    </div>
  );
}
