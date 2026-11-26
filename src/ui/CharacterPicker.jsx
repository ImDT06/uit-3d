import { Suspense, useEffect, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { useGame } from "../game/store";
import { useSettings } from "../game/settings";
import Avatar from "../world/Avatar";

// Bang chon nhan vat: hien o lan dau vao kham pha, doi lai trong Menu. Lua chon luu trong cai dat.

function Turntable({ drag, children }) {
  const g = useRef();
  useFrame((_, dt) => {
    const d = drag.current;
    if (d.x === null) d.vel *= Math.exp(-4 * dt);
    else d.vel *= 0.8;
    d.angle += d.vel * dt;
    g.current.rotation.y = d.angle;
  });
  return (
    <group ref={g} position={[0, -0.9, 0]}>
      {children}
    </group>
  );
}

function Choice({ label, value, options, onChange }) {
  return (
    <div className="pick-group">
      <span>{label}</span>
      <div>
        {options.map(([v, text]) => (
          <button key={v} className={v === value ? "on" : ""} aria-pressed={v === value} onClick={() => onChange(v)}>
            {text}
          </button>
        ))}
      </div>
    </div>
  );
}

function Panel({ saved }) {
  const [pick, setPick] = useState(saved || { gender: "nam", hair: "ngan" });
  const drag = useRef({ x: null, angle: 0.35, vel: 0 });
  const down = (e) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    drag.current.x = e.clientX;
    drag.current.vel = 0;
  };
  const move = (e) => {
    const d = drag.current;
    if (d.x === null) return;
    const dx = e.clientX - d.x;
    d.x = e.clientX;
    d.angle += dx * 0.012;
    d.vel = dx * 0.4; // quan tinh khi tha tay
  };
  const up = () => (drag.current.x = null);
  const done = () => {
    useSettings.getState().set({ avatar: pick });
    useGame.getState().setUi({ pickerOpen: false });
  };

  return (
    <div className="pick-wrap">
      <div className="pick">
        <h3>Chọn nhân vật</h3>
        <div className="pick-view" onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}>
          <Canvas camera={{ position: [0, -0.03, 3.9], fov: 32 }} dpr={[1, 2]}>
            <hemisphereLight args={["#ffffff", "#8a93a8", 1.6]} />
            <directionalLight position={[2, 3, 4]} intensity={1.6} />
            <Suspense fallback={null}>
              <Turntable drag={drag}>
                <Avatar key={pick.gender} gender={pick.gender} hair={pick.hair} />
              </Turntable>
            </Suspense>
          </Canvas>
          <small>Kéo để xoay</small>
        </div>
        <div className="pick-side">
          <Choice label="Giới tính" value={pick.gender} options={[["nam", "Nam"], ["nu", "Nữ"]]}
            onChange={(gender) => setPick({ ...pick, gender })} />
          {pick.gender === "nu" && (
            <Choice label="Kiểu tóc" value={pick.hair} options={[["ngan", "Ngắn"], ["dai", "Dài"]]}
              onChange={(hair) => setPick({ ...pick, hair })} />
          )}
          <button className="pick-done" onClick={done}>{saved ? "Xong" : "Vào khám phá"}</button>
        </div>
      </div>
    </div>
  );
}

export default function CharacterPicker() {
  const mode = useGame((s) => s.mode);
  const open = useGame((s) => s.pickerOpen);
  const avatar = useSettings((s) => s.avatar);
  // lan dau vao kham pha: mo bang chon
  useEffect(() => {
    if (mode !== "explore" || avatar) return;
    if (document.pointerLockElement) document.exitPointerLock();
    useGame.getState().setUi({ pickerOpen: true });
  }, [mode, avatar]);
  return mode === "explore" && open ? <Panel saved={avatar} /> : null;
}
