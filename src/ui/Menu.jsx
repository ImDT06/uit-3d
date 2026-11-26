import { useEffect, useState } from "react";
import { useGame } from "../game/store";
import { useSettings, ACTIONS, keyName } from "../game/settings";

function Row({ label, children }) {
  return (
    <label className="menu-row">
      <span>{label}</span>
      <div>{children}</div>
    </label>
  );
}

function SettingsTab() {
  const s = useSettings();
  return (
    <div className="menu-body">
      <h4>Camera & chuột</h4>
      <Row label={`Độ nhạy chuột · ${s.mouseSens.toFixed(1)}`}>
        <input type="range" min={0.2} max={3} step={0.1} value={s.mouseSens} onChange={(e) => s.set({ mouseSens: +e.target.value })} />
      </Row>
      <Row label="Đảo trục dọc (Y)">
        <input type="checkbox" checked={s.invertY} onChange={(e) => s.set({ invertY: e.target.checked })} />
      </Row>
      <Row label="Camera tự xoay ra sau lưng khi đi">
        <input type="checkbox" checked={s.camFollow} onChange={(e) => s.set({ camFollow: e.target.checked })} />
      </Row>
      <Row label={`Góc nhìn (FOV) · ${s.fov}°`}>
        <input type="range" min={45} max={90} step={1} value={s.fov} onChange={(e) => s.set({ fov: +e.target.value })} />
      </Row>

      <h4>Di chuyển</h4>
      <Row label="Kiểu chạy">
        <select value={s.holdToRun ? "hold" : "toggle"} onChange={(e) => s.set({ holdToRun: e.target.value === "hold" })}>
          <option value="toggle">Bấm để bật/tắt</option>
          <option value="hold">Giữ phím để chạy</option>
        </select>
      </Row>

      <h4>Âm thanh & đồ họa</h4>
      <Row label={`Âm lượng · ${Math.round(s.volume * 100)}%`}>
        <input type="range" min={0} max={1} step={0.05} value={s.volume} onChange={(e) => s.set({ volume: +e.target.value })} />
      </Row>
      <Row label="Chất lượng đồ họa">
        <select value={s.quality} onChange={(e) => s.set({ quality: e.target.value })}>
          <option value="auto">Tự động (theo máy)</option>
          <option value="low">Thấp</option>
          <option value="medium">Vừa</option>
          <option value="high">Cao</option>
        </select>
      </Row>
      <div className="menu-actions">
        <button className="ghost" onClick={() => s.reset()}>Khôi phục mặc định</button>
      </div>
    </div>
  );
}

function KeysTab() {
  const binds = useSettings((s) => s.binds);
  const setBind = useSettings((s) => s.setBind);
  const resetBinds = useSettings((s) => s.resetBinds);
  const [waiting, setWaiting] = useState(null);

  useEffect(() => {
    if (!waiting) return;
    window.__rebinding = true;
    const onKey = (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.code !== "Escape") setBind(waiting, e.code);
      setWaiting(null);
    };
    window.addEventListener("keydown", onKey, true);
    return () => {
      window.removeEventListener("keydown", onKey, true);
      setTimeout(() => (window.__rebinding = false), 0);
    };
  }, [waiting, setBind]);

  return (
    <div className="menu-body">
      <div className="keys">
        {ACTIONS.map((a) => (
          <div className="key-row" key={a.id}>
            <span>{a.label}</span>
            <button className={waiting === a.id ? "waiting" : ""} onClick={() => setWaiting(a.id)}>
              {waiting === a.id ? "Bấm phím mới…" : (binds[a.id] || []).map(keyName).join(" / ") || "—"}
            </button>
          </div>
        ))}
        <div className="key-row fixed"><span>Menu</span><button disabled>Esc</button></div>
        <div className="key-row fixed"><span>Xoay camera</span><button disabled>Giữ chuột phải</button></div>
        <div className="key-row fixed"><span>Zoom / góc nhìn thứ nhất</span><button disabled>Lăn chuột</button></div>
      </div>
      <p className="menu-note">Bấm vào ô phím rồi nhấn phím mới. Esc để hủy. Phím trùng sẽ tự bỏ khỏi hành động cũ.</p>
      <div className="menu-actions">
        <button className="ghost" onClick={resetBinds}>Khôi phục phím mặc định</button>
      </div>
    </div>
  );
}

function PadTab() {
  const rows = [
    ["Cần trái", "Đi"],
    ["Cần phải", "Xoay camera"],
    ["A / ✕", "Nhảy"],
    ["B / ○ hoặc bấm cần trái", "Bật/tắt chạy"],
    ["X / □", "Tương tác"],
    ["Y / △", "Đổi góc nhìn"],
    ["RB / R1", "Shift lock"],
    ["Back / Share", "Bản đồ"],
    ["LB / L1", "Bật/tắt bay (LT / L2: bay xuống)"],
    ["Start / Options", "Menu"],
  ];
  return (
    <div className="menu-body">
      <p className="menu-note">Cắm tay cầm Xbox / PlayStation rồi bấm một nút bất kỳ để trình duyệt nhận.</p>
      <div className="keys">
        {rows.map(([k, v]) => (
          <div className="key-row fixed" key={k}>
            <span>{v}</span>
            <button disabled>{k}</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Menu() {
  const open = useGame((s) => s.menuOpen);
  const setUi = useGame((s) => s.setUi);
  const restartTutorial = useGame((s) => s.restartTutorial);
  const spawn = useGame((s) => s.spawn);
  const teleportTo = useGame((s) => s.teleportTo);
  const [tab, setTab] = useState(null);
  useEffect(() => {
    if (!open) setTab(null);
  }, [open]);
  if (!open) return null;

  const close = () => setUi({ menuOpen: false });
  const tabs = { settings: "Cài đặt", keys: "Phím", pad: "Tay cầm" };

  return (
    <div className="menu-wrap">
      <div className="menu">
        {!tab ? (
          <>
            <div className="menu-title">Tạm dừng</div>
            <button className="primary" onClick={close}>Tiếp tục</button>
            <button onClick={() => setUi({ menuOpen: false, pickerOpen: true })}>Đổi nhân vật</button>
            <button onClick={() => setTab("settings")}>Cài đặt</button>
            <button onClick={() => setTab("keys")}>Phím điều khiển</button>
            <button onClick={() => setTab("pad")}>Tay cầm</button>
            <button onClick={() => { restartTutorial(); close(); }}>Xem lại hướng dẫn</button>
            <button onClick={() => { if (spawn) teleportTo(spawn); close(); }}>Về điểm xuất phát</button>
            <button onClick={() => useGame.getState().setMode("intro")}>Về trang chủ</button>
          </>
        ) : (
          <>
            <div className="menu-head">
              <button className="ghost" onClick={() => setTab(null)}>← Quay lại</button>
              <b>{tabs[tab]}</b>
            </div>
            {tab === "settings" && <SettingsTab />}
            {tab === "keys" && <KeysTab />}
            {tab === "pad" && <PadTab />}
          </>
        )}
      </div>
    </div>
  );
}
