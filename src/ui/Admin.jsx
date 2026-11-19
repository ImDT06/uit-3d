import { useEffect, useState } from "react";
import { useGame, playerPos, DEFAULT_TUNING } from "../game/store";
import { ZONES, zoneInfo } from "../data/zones";

// Bang admin de test: bat/tat bang phim ` (canh so 1)
// Chi co khi chay dev (npm run dev) hoac them ?admin vao URL
export const adminEnabled =
  import.meta.env.DEV || new URLSearchParams(window.location.search).has("admin");

function Slider({ label, value, min, max, step, onChange }) {
  return (
    <label className="admin-row">
      <span>{label}</span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(+e.target.value)} />
      <b>{value}</b>
    </label>
  );
}

function useFps() {
  const [fps, setFps] = useState(0);
  useEffect(() => {
    let frames = 0;
    let last = performance.now();
    let id;
    const loop = (t) => {
      frames++;
      if (t - last >= 500) {
        setFps(Math.round((frames * 1000) / (t - last)));
        frames = 0;
        last = t;
      }
      id = requestAnimationFrame(loop);
    };
    id = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(id);
  }, []);
  return fps;
}

function usePlayerPos() {
  const [p, setP] = useState(playerPos);
  useEffect(() => {
    const id = setInterval(() => setP({ ...playerPos }), 200);
    return () => clearInterval(id);
  }, []);
  return p;
}

function AdminPanel({ onClose }) {
  const tuning = useGame((s) => s.tuning);
  const setTuning = useGame((s) => s.setTuning);
  const buildings = useGame((s) => s.buildings);
  const spawn = useGame((s) => s.spawn);
  const teleportTo = useGame((s) => s.teleportTo);
  const physicsDebug = useGame((s) => s.physicsDebug);
  const setPhysicsDebug = useGame((s) => s.setPhysicsDebug);
  const setVisited = useGame((s) => s.setVisited);
  const fps = useFps();
  const p = usePlayerPos();
  const [target, setTarget] = useState("");
  const [copied, setCopied] = useState(false);

  const posText = `[${p.x.toFixed(2)}, ${p.y.toFixed(2)}, ${p.z.toFixed(2)}]`;

  const goBuilding = () => {
    const b = buildings.find((x) => x.name === target);
    if (!b) return;
    // dat nhan vat truoc mat toa nha (phia +z), cao hon mat dat mot chut
    const cx = (b.box.min.x + b.box.max.x) / 2;
    teleportTo([cx, b.box.min.y + 1.5, b.box.max.z + 4]);
  };

  const copyPos = async () => {
    try {
      await navigator.clipboard.writeText(posText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {}
  };

  return (
    <div className="admin" onKeyDown={(e) => e.stopPropagation()}>
      <div className="admin-head">
        <b>Admin</b>
        <span className="admin-fps">{fps} FPS</span>
        <button className="admin-x" onClick={onClose} title="Đóng (phím `)">×</button>
      </div>

      <div className="admin-sec">Nhân vật</div>
      <Slider label="Tốc độ đi" value={tuning.walk} min={1} max={30} step={0.5} onChange={(walk) => setTuning({ walk })} />
      <Slider label="Tốc độ chạy" value={tuning.run} min={1} max={60} step={0.5} onChange={(run) => setTuning({ run })} />
      <Slider label="Lực nhảy" value={tuning.jump} min={1} max={30} step={0.5} onChange={(jump) => setTuning({ jump })} />
      <div className="admin-btns">
        <button onClick={() => setTuning(DEFAULT_TUNING)}>Mặc định</button>
        <button onClick={() => setTuning({ walk: 12, run: 40, jump: 15 })}>Siêu tốc</button>
      </div>

      <div className="admin-sec">Dịch chuyển</div>
      <div className="admin-btns">
        <select value={target} onChange={(e) => setTarget(e.target.value)}>
          <option value="">-- Chọn tòa nhà --</option>
          {buildings.map((b) => (
            <option key={b.name} value={b.name}>
              {zoneInfo(b.name).title || b.name}
            </option>
          ))}
        </select>
        <button onClick={goBuilding} disabled={!target}>Đi</button>
      </div>
      <div className="admin-btns">
        <button onClick={() => spawn && teleportTo(spawn)}>Về điểm xuất phát</button>
      </div>
      <div className="admin-row">
        <span>Vị trí</span>
        <code>{posText}</code>
        <button onClick={copyPos}>{copied ? "Đã chép" : "Chép"}</button>
      </div>

      <div className="admin-sec">Khác</div>
      <label className="admin-check">
        <input type="checkbox" checked={physicsDebug} onChange={(e) => setPhysicsDebug(e.target.checked)} />
        Hiện khung va chạm
      </label>
      <div className="admin-btns">
        <button onClick={() => setVisited(Object.fromEntries(Object.keys(ZONES).map((k) => [k, true])))}>
          Mở khóa hết khu vực
        </button>
        <button onClick={() => setVisited({})}>Xóa tiến độ</button>
      </div>
    </div>
  );
}

export default function Admin() {
  const open = useGame((s) => s.adminOpen);
  const setUi = useGame((s) => s.setUi);
  const setOpen = (v) => setUi({ adminOpen: typeof v === "function" ? v(useGame.getState().adminOpen) : v });
  useEffect(() => {
    if (!adminEnabled) return;
    const onKey = (e) => {
      if (e.code !== "Backquote" || window.__rebinding) return;
      // mo bang admin thi Player tu nha chuot de bam duoc
      setUi({ adminOpen: !useGame.getState().adminOpen });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!adminEnabled) return null;
  if (!open)
    return (
      <button className="admin-toggle" onClick={() => setOpen(true)} title="Mở bảng admin (phím `)">
        ⚙
      </button>
    );
  return <AdminPanel onClose={() => setOpen(false)} />;
}
