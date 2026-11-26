import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { useJoystickStore, useButtonStore } from "ecctrl/input";
import { useGame } from "../game/store";
import { doAction } from "../game/actions";

// Dieu khien cam ung kieu Roblox:
// - nua trai man hinh: joystick dong (cham dau thi can dieu khien hien o do, keo qua vien thi de keo theo)
// - goc phai duoi: nut nhay lon, nut chay + shift lock xep quanh
// - vuot nua phai: xoay camera (CameraControls tren canvas tu xu ly), hai ngon: zoom
// Gia tri ghi vao store cua ecctrl/input nen Player.jsx doc nhu cu (joysticks.move, buttons.jump/run).

const R = 52; // px: ban kinh keo toi da cua num
const DEAD = 0.12;

// ---- Phat hien man hinh cam ung (doi theo thiet bi dang dung, vd laptop cam ung) ----
const mq = (q) => typeof window !== "undefined" && window.matchMedia(q).matches;
let touchMode = mq("(pointer: coarse)") || (mq("(any-pointer: coarse)") && mq("(hover: none)"));
const subs = new Set();
const setTouchMode = (v) => {
  if (v === touchMode) return;
  touchMode = v;
  subs.forEach((f) => f());
};
if (typeof window !== "undefined") {
  window.addEventListener("pointerdown", (e) => e.pointerType === "touch" && setTouchMode(true), true);
  window.addEventListener("keydown", () => setTouchMode(false), true);
}
export function useTouchMode() {
  return useSyncExternalStore(
    (f) => (subs.add(f), () => subs.delete(f)),
    () => touchMode,
  );
}

function Thumbstick() {
  const zone = useRef(null);
  const base = useRef(null);
  const knob = useRef(null);
  const st = useRef({ id: null, cx: 0, cy: 0 });
  const [active, setActive] = useState(false);
  const [hint, setHint] = useState(true);
  const setJoystick = useJoystickStore((s) => s.setJoystick);
  const resetJoystick = useJoystickStore((s) => s.resetJoystick);

  useEffect(() => () => resetJoystick("move"), [resetJoystick]);

  const place = () => {
    const s = st.current;
    if (base.current) base.current.style.transform = `translate(${s.cx}px, ${s.cy}px)`;
  };

  const move = (x, y) => {
    const s = st.current;
    let dx = x - s.cx;
    let dy = y - s.cy;
    const d = Math.hypot(dx, dy);
    if (d > R) {
      // keo qua vien: de dieu khien di theo ngon tay (giong Roblox)
      const k = (d - R) / d;
      s.cx += dx * k;
      s.cy += dy * k;
      dx -= dx * k;
      dy -= dy * k;
      place();
    }
    if (knob.current) knob.current.style.transform = `translate(${dx}px, ${dy}px)`;
    let nx = dx / R;
    let ny = -dy / R;
    const m = Math.hypot(nx, ny);
    if (m < DEAD) nx = ny = 0;
    setJoystick(nx, ny, "move");
  };

  const down = (e) => {
    const s = st.current;
    if (s.id !== null) return;
    e.preventDefault();
    s.id = e.pointerId;
    const r = zone.current.getBoundingClientRect();
    // giu can dieu khien nam tron trong vung
    s.cx = Math.min(Math.max(e.clientX, r.left + R + 10), r.right - R - 10);
    s.cy = Math.min(Math.max(e.clientY, r.top + R + 10), r.bottom - R - 10);
    e.currentTarget.setPointerCapture(e.pointerId);
    place();
    setActive(true);
    setHint(false);
    move(e.clientX, e.clientY);
  };
  const up = (e) => {
    const s = st.current;
    if (s.id !== e.pointerId) return;
    s.id = null;
    if (knob.current) knob.current.style.transform = "";
    if (base.current) base.current.style.transform = "";
    setActive(false);
    resetJoystick("move");
  };

  return (
    <div
      ref={zone}
      className="tc-zone"
      onPointerDown={down}
      onPointerMove={(e) => st.current.id === e.pointerId && move(e.clientX, e.clientY)}
      onPointerUp={up}
      onPointerCancel={up}
      onLostPointerCapture={up}
      onContextMenu={(e) => e.preventDefault()}
    >
      <div ref={base} className={"tc-stick" + (active ? " on" : "")}>
        <div ref={knob} className="tc-knob" />
      </div>
      {hint && <div className="tc-hint">Giữ và kéo để đi</div>}
    </div>
  );
}

// Nut giu (nhay): bat/tat trong button store cua ecctrl
function HoldButton({ id, className, children, label }) {
  const setBtn = useButtonStore((s) => s.setButtonActive);
  const pid = useRef(null);
  const [on, setOn] = useState(false);
  useEffect(() => () => setBtn(id, false), [setBtn, id]);
  const press = (e) => {
    if (pid.current !== null) return;
    e.preventDefault();
    pid.current = e.pointerId;
    e.currentTarget.setPointerCapture(e.pointerId);
    setBtn(id, true);
    setOn(true);
  };
  const release = (e) => {
    if (pid.current !== e.pointerId) return;
    pid.current = null;
    setBtn(id, false);
    setOn(false);
  };
  return (
    <div
      className={`tc-btn ${className}${on ? " on" : ""}`}
      aria-label={label}
      onPointerDown={press}
      onPointerUp={release}
      onPointerCancel={release}
      onLostPointerCapture={release}
      onContextMenu={(e) => e.preventDefault()}
    >
      {children}
    </div>
  );
}

// Nut bat/tat (chay, shift lock): bam la doi, khong can giu
function ToggleButton({ on, onTap, className, children, label }) {
  return (
    <div
      className={`tc-btn ${className}${on ? " on" : ""}`}
      aria-label={label}
      onPointerDown={(e) => {
        e.preventDefault();
        onTap();
      }}
      onContextMenu={(e) => e.preventDefault()}
    >
      {children}
    </div>
  );
}

const Icon = ({ d, size = 30 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6"
    strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

export default function TouchControls() {
  const shiftLock = useGame((s) => s.shiftLock);
  const view = useGame((s) => s.viewMode);
  const [run, setRun] = useState(false);
  const setBtn = useButtonStore((s) => s.setButtonActive);
  useEffect(() => () => setBtn("run", false), [setBtn]);
  const toggleRun = () => {
    setRun(!run);
    setBtn("run", !run);
  };

  return (
    <>
      <Thumbstick />
      <div className="tc-right">
        <HoldButton id="jump" className="tc-jump" label="Nhảy">
          <Icon d="M5 15l7-7 7 7" size={40} />
        </HoldButton>
        <ToggleButton on={run} onTap={toggleRun} className="tc-run" label="Chạy">
          <span>🏃</span>
        </ToggleButton>
        {view !== "first" && (
          <ToggleButton on={shiftLock} onTap={() => doAction("shiftLock")} className="tc-lock" label="Shift lock">
            <Icon d="M7 11V8a5 5 0 0110 0v3M6 11h12v9H6z" size={22} />
          </ToggleButton>
        )}
      </div>
      <div className="touch-top">
        <button onClick={() => doAction("view")} aria-label="Đổi góc nhìn">👁</button>
        <button onClick={() => doAction("menu")} aria-label="Menu">☰</button>
      </div>
    </>
  );
}
