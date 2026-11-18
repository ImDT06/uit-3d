import { useEffect, useState } from "react";
import { useProgress } from "@react-three/drei";
import { Joystick, VirtualButton } from "ecctrl/input";
import { useGame } from "./store";
import { ZONES, zoneInfo } from "./zones";

export function Loading() {
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

function ZoneCard() {
  const zone = useGame((s) => s.currentZone);
  if (!zone) return null;
  const info = zoneInfo(zone);
  return (
    <div className="zone-card" key={zone}>
      {info.image && <img src={info.image} alt={info.title} />}
      <div className="zone-sub">{info.subtitle || "Khu vực"}</div>
      <div className="zone-title">{info.title}</div>
      {info.description && <p>{info.description}</p>}
    </div>
  );
}

function Progress() {
  const visited = useGame((s) => s.visited);
  const total = Object.keys(ZONES).length;
  const done = Object.keys(visited).filter((k) => ZONES[k]).length;
  return (
    <div className="progress">
      Đã khám phá <b>{done}</b>/{total} khu vực
    </div>
  );
}

function Help() {
  const [open, setOpen] = useState(true);
  useEffect(() => {
    const t = setTimeout(() => setOpen(false), 12000);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="help" onClick={() => setOpen(!open)}>
      {open ? (
        <>
          <b>Điều khiển</b>
          <div>W A S D / mũi tên: đi</div>
          <div>Shift: chạy · Space: nhảy</div>
          <div>Kéo chuột: xoay camera · Lăn chuột: zoom</div>
        </>
      ) : (
        <span>? Điều khiển</span>
      )}
    </div>
  );
}

const isTouch = typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches;

export default function Hud() {
  return (
    <>
      <Progress />
      <ZoneCard />
      {!isTouch && <Help />}
      {isTouch && (
        <>
          <Joystick id="move" />
          <VirtualButton id="jump" label="Nhảy" />
        </>
      )}
    </>
  );
}
