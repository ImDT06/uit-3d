import { useEffect, useMemo, useRef, useState } from "react";
import { useGame, playerPos } from "../game/store";
import { zoneInfo } from "../data/zones";
import { bindLabel } from "../game/settings";

const DEG = 180 / Math.PI;

// Cap nhat vi tri nhan vat ~15 lan/giay cho ban do
function usePlayerSnapshot(fps = 15) {
  const [p, setP] = useState({ ...playerPos });
  useEffect(() => {
    const id = setInterval(() => setP({ ...playerPos }), 1000 / fps);
    return () => clearInterval(id);
  }, [fps]);
  return p;
}

// Khung bao toan ban do (gom cac toa nha + le)
function useBounds(buildings) {
  return useMemo(() => {
    if (!buildings.length) return { x: -100, z: -100, w: 200, h: 200 };
    let minX = Infinity, minZ = Infinity, maxX = -Infinity, maxZ = -Infinity;
    for (const b of buildings) {
      minX = Math.min(minX, b.box.min.x);
      minZ = Math.min(minZ, b.box.min.z);
      maxX = Math.max(maxX, b.box.max.x);
      maxZ = Math.max(maxZ, b.box.max.z);
    }
    const m = 30;
    return { x: minX - m, z: minZ - m, w: maxX - minX + 2 * m, h: maxZ - minZ + 2 * m };
  }, [buildings]);
}

function Buildings({ buildings, visited, current, labels, labelSize = 4 }) {
  return buildings.map((b) => {
    const w = b.box.max.x - b.box.min.x;
    const h = b.box.max.z - b.box.min.z;
    const cls = "map-bld" + (b.name === current ? " cur" : visited[b.name] ? " seen" : "");
    return (
      <g key={b.name}>
        <rect className={cls} x={b.box.min.x} y={b.box.min.z} width={w} height={h} rx={1.5} />
        {labels && (
          <text className="map-label" fontSize={labelSize} x={b.box.min.x + w / 2} y={b.box.min.z + h / 2}>
            {zoneInfo(b.name).title}
          </text>
        )}
      </g>
    );
  });
}

// Mui ten nhan vat; mac dinh chi len tren, xoay theo huong mat (yaw: 0 = +Z = xuong duoi ban do)
function Arrow({ x, z, yaw, size }) {
  return (
    <g transform={`translate(${x} ${z}) rotate(${180 - yaw * DEG}) scale(${size})`}>
      <path className="map-me" d="M0 -1.4 L1 1 L0 0.45 L-1 1 Z" />
    </g>
  );
}

function Pin({ x, z, size }) {
  return (
    <g transform={`translate(${x} ${z}) scale(${size})`}>
      <circle className="map-pin" r={1} />
      <circle className="map-pin-dot" r={0.35} />
    </g>
  );
}

const RADIUS = 55; // m hien thi tren ban do nho

export function Minimap() {
  const buildings = useGame((s) => s.buildings);
  const visited = useGame((s) => s.visited);
  const current = useGame((s) => s.currentZone);
  const waypoint = useGame((s) => s.waypoint);
  const setUi = useGame((s) => s.setUi);
  const p = usePlayerSnapshot();
  if (!buildings.length) return null;
  // xoay ban do de huong camera luon chi len tren
  const rot = p.camYaw * DEG - 180;
  const dist = waypoint ? Math.hypot(waypoint.x - p.x, waypoint.z - p.z) : 0;
  return (
    <div className="minimap" onClick={() => setUi({ mapOpen: true })} title={`Mở bản đồ (${bindLabel("map")})`}>
      <svg viewBox={`${p.x - RADIUS} ${p.z - RADIUS} ${RADIUS * 2} ${RADIUS * 2}`}>
        <g transform={`rotate(${rot} ${p.x} ${p.z})`}>
          <rect className="map-ground" x={p.x - RADIUS * 2} y={p.z - RADIUS * 2} width={RADIUS * 4} height={RADIUS * 4} />
          <Buildings buildings={buildings} visited={visited} current={current} />
          {waypoint && <Pin x={waypoint.x} z={waypoint.z} size={3} />}
          <Arrow x={p.x} z={p.z} yaw={p.yaw} size={5} />
        </g>
      </svg>
      <div className="minimap-n" style={{ transform: `rotate(${rot}deg) translateY(-62px) rotate(${-rot}deg)` }}>B</div>
      {waypoint && <div className="minimap-dist">{Math.round(dist)} m</div>}
    </div>
  );
}

export function BigMap() {
  const open = useGame((s) => s.mapOpen);
  const buildings = useGame((s) => s.buildings);
  const visited = useGame((s) => s.visited);
  const current = useGame((s) => s.currentZone);
  const waypoint = useGame((s) => s.waypoint);
  const setWaypoint = useGame((s) => s.setWaypoint);
  const setUi = useGame((s) => s.setUi);
  const b = useBounds(buildings);
  const svg = useRef(null);
  const p = usePlayerSnapshot(10);
  if (!open) return null;

  const toWorld = (e) => {
    const pt = svg.current.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const w = pt.matrixTransform(svg.current.getScreenCTM().inverse());
    return { x: w.x, z: w.y };
  };

  const onClick = (e) => {
    const w = toWorld(e);
    // bam vao toa nha -> danh dau truoc cua toa do
    const hit = buildings.find((bd) => w.x >= bd.box.min.x && w.x <= bd.box.max.x && w.z >= bd.box.min.z && w.z <= bd.box.max.z);
    if (hit) {
      const cx = (hit.box.min.x + hit.box.max.x) / 2;
      setWaypoint({ x: cx, z: hit.box.max.z + 3, label: zoneInfo(hit.name).title });
    } else {
      setWaypoint({ x: w.x, z: w.z, label: "Điểm đánh dấu" });
    }
  };

  const size = Math.max(b.w, b.h) / 70;
  return (
    <div className="bigmap-wrap" onClick={() => setUi({ mapOpen: false })}>
      <div className="bigmap" onClick={(e) => e.stopPropagation()}>
        <div className="bigmap-head">
          <b>Bản đồ khuôn viên</b>
          <span>Bấm vào bản đồ để đặt điểm đánh dấu · {bindLabel("map")} / Esc để đóng</span>
          <button onClick={() => setUi({ mapOpen: false })}>×</button>
        </div>
        <svg ref={svg} viewBox={`${b.x} ${b.z} ${b.w} ${b.h}`} onClick={onClick}>
          <rect className="map-ground" x={b.x} y={b.z} width={b.w} height={b.h} />
          <Buildings buildings={buildings} visited={visited} current={current} labels labelSize={size * 1.6} />
          {waypoint && <Pin x={waypoint.x} z={waypoint.z} size={size * 1.2} />}
          <Arrow x={p.x} z={p.z} yaw={p.yaw} size={size * 1.4} />
        </svg>
        <div className="bigmap-foot">
          {waypoint ? (
            <>
              Đang đánh dấu: <b>{waypoint.label}</b> · cách {Math.round(Math.hypot(waypoint.x - p.x, waypoint.z - p.z))} m
              <button onClick={() => setWaypoint(null)}>Bỏ đánh dấu</button>
            </>
          ) : (
            <span>Chưa có điểm đánh dấu</span>
          )}
        </div>
      </div>
    </div>
  );
}
