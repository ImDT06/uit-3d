import { useEffect, useState } from "react";
import { Joystick, VirtualButton } from "ecctrl/input";
import { useGame } from "../game/store";
import { useSettings, bindLabel } from "../game/settings";
import { doAction } from "../game/actions";
import { ZONES, zoneInfo } from "../data/zones";
import { Minimap, BigMap } from "./MapView";
import Menu from "./Menu";
import Tutorial from "./Tutorial";

// The thong tin toa nha: mo bang phim tuong tac (E)
function ZoneCard() {
  const zone = useGame((s) => s.currentZone);
  const open = useGame((s) => s.infoOpen);
  const setUi = useGame((s) => s.setUi);
  if (!zone || !open) return null;
  const info = zoneInfo(zone);
  return (
    <div className="zone-card" key={zone}>
      <button className="zone-x" {...noFocus} onClick={() => setUi({ infoOpen: false })}>×</button>
      {info.image && <img src={info.image} alt={info.title} />}
      <div className="zone-sub">{info.subtitle || "Khu vực"}</div>
      <div className="zone-title">{info.title}</div>
      {info.description && <p>{info.description}</p>}
    </div>
  );
}

// Goi y "E - Xem thong tin" khi dung gan toa nha
function InteractPrompt() {
  const zone = useGame((s) => s.currentZone);
  const open = useGame((s) => s.infoOpen);
  useSettings((s) => s.binds);
  if (!zone || open) return null;
  return (
    <button className="interact" {...noFocus} onClick={() => doAction("interact")}>
      <kbd>{isTouch ? "Chạm" : bindLabel("interact")}</kbd> Xem thông tin <b>{zoneInfo(zone).title}</b>
    </button>
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

// Trang thai dang bat: chay, shift lock, goc nhin
function Status() {
  const run = useGame((s) => s.runToggled);
  const lock = useGame((s) => s.shiftLock);
  const view = useGame((s) => s.viewMode);
  const holdToRun = useSettings((s) => s.holdToRun);
  const chips = [];
  if (run && !holdToRun) chips.push("🏃 Đang chạy");
  if (view === "first") chips.push("👁 Góc nhìn thứ nhất");
  else if (lock) chips.push("🔒 Shift lock");
  if (!chips.length) return null;
  return (
    <div className="status">
      {chips.map((c) => (
        <span key={c}>{c}</span>
      ))}
    </div>
  );
}

function Crosshair() {
  const lock = useGame((s) => s.shiftLock);
  const view = useGame((s) => s.viewMode);
  if (!lock && view !== "first") return null;
  return <div className="crosshair" />;
}

function Help() {
  const [open, setOpen] = useState(false);
  const tutorialDone = useGame((s) => s.tutorialDone);
  const holdToRun = useSettings((s) => s.holdToRun);
  useSettings((s) => s.binds);
  useEffect(() => {
    if (!tutorialDone) setOpen(false);
  }, [tutorialDone]);
  const mv = ["forward", "leftward", "backward", "rightward"].map((a) => bindLabel(a).split(" / ")[0]).join(" ");
  return (
    <div className="help" onClick={() => setOpen(!open)}>
      {open ? (
        <>
          <b>Điều khiển</b>
          <div>{mv} / mũi tên: đi · {bindLabel("jump")}: nhảy</div>
          <div>{bindLabel("run")}: {holdToRun ? "giữ để chạy" : "bật/tắt chạy"} · gõ đúp {bindLabel("forward").split(" / ")[0]}: chạy</div>
          <div>Giữ chuột phải: xoay camera · Lăn chuột: zoom</div>
          <div>{bindLabel("shiftLock")}: shift lock · {bindLabel("view")}: đổi góc nhìn</div>
          <div>{bindLabel("interact")}: xem thông tin · {bindLabel("map")}: bản đồ · Esc: menu</div>
        </>
      ) : (
        <span>? Điều khiển</span>
      )}
    </div>
  );
}

// nut khong giu focus, tranh bam Space (nhay) lai kich hoat nut vua bam
const noFocus = { onMouseDown: (e) => e.preventDefault() };

const isTouch = typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches;

function TouchControls() {
  const btn = (bottom, right) => ({ position: "fixed", bottom, right, zIndex: 20 });
  return (
    <>
      <Joystick id="move" />
      <VirtualButton id="jump" label="Nhảy" buttonWrapperStyle={btn(40, 30)} />
      <VirtualButton id="run" label="Chạy" buttonWrapperStyle={btn(130, 100)} />
      <div className="touch-top">
        <button onClick={() => doAction("view")}>👁</button>
        <button onClick={() => doAction("menu")}>☰</button>
      </div>
    </>
  );
}

export default function Hud() {
  const overlay = useGame((s) => s.menuOpen || s.mapOpen);
  return (
    <>
      {!overlay && (
        <>
          <Progress />
          <Status />
          <Crosshair />
          <InteractPrompt />
          <ZoneCard />
          <Minimap />
          {!isTouch && <Help />}
          {!isTouch && <Tutorial />}
          {isTouch && <TouchControls />}
          {!isTouch && (
            <div className="corner-btns">
              <button {...noFocus} onClick={() => doAction("shiftLock")} title={`Shift lock (${bindLabel("shiftLock")})`}>🔒</button>
              <button {...noFocus} onClick={() => doAction("menu")} title="Menu (Esc)">☰</button>
            </div>
          )}
        </>
      )}
      <BigMap />
      <Menu />
    </>
  );
}
