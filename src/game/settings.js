import { create } from "zustand";

// Cac hanh dong co the gan phim. code theo KeyboardEvent.code
export const ACTIONS = [
  { id: "forward", label: "Đi tới", keys: ["KeyW", "ArrowUp"] },
  { id: "backward", label: "Đi lùi", keys: ["KeyS", "ArrowDown"] },
  { id: "leftward", label: "Sang trái", keys: ["KeyA", "ArrowLeft"] },
  { id: "rightward", label: "Sang phải", keys: ["KeyD", "ArrowRight"] },
  { id: "jump", label: "Nhảy", keys: ["Space"] },
  { id: "run", label: "Chạy", keys: ["KeyC"] },
  { id: "shiftLock", label: "Shift lock", keys: ["ShiftLeft", "ShiftRight"] },
  { id: "view", label: "Đổi góc nhìn", keys: ["KeyV"] },
  { id: "interact", label: "Tương tác", keys: ["KeyE"] },
  { id: "map", label: "Bản đồ", keys: ["KeyM"] },
];
// cac hanh dong giu phim (KeyboardControls); con lai la bam mot lan
export const HOLD_ACTIONS = ["forward", "backward", "leftward", "rightward", "jump", "run"];

export const DEFAULT_BINDS = Object.fromEntries(ACTIONS.map((a) => [a.id, a.keys]));

export const DEFAULT_SETTINGS = {
  mouseSens: 1,          // he so do nhay chuot / cam phai tay cam
  invertY: false,
  camFollow: true,       // camera tu xoay ve sau lung khi di
  holdToRun: false,      // false: bam phim chay de bat/tat; true: giu phim moi chay
  fov: 55,
  volume: 0.6,
  quality: "auto",       // auto | low | medium | high
  binds: DEFAULT_BINDS,
};

const KEY = "uit3d-settings";

function load() {
  try {
    const s = JSON.parse(localStorage.getItem(KEY) || "null");
    if (!s) return { ...DEFAULT_SETTINGS };
    return { ...DEFAULT_SETTINGS, ...s, binds: { ...DEFAULT_BINDS, ...(s.binds || {}) } };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

function save(s) {
  try {
    const { set, reset, setBind, resetBinds, ...data } = s;
    localStorage.setItem(KEY, JSON.stringify(data));
  } catch {}
}

export const useSettings = create((set, get) => ({
  ...load(),
  set: (patch) => {
    set(patch);
    save(get());
  },
  setBind: (id, code) => {
    // bo phim nay khoi hanh dong khac de tranh trung
    const binds = Object.fromEntries(
      Object.entries(get().binds).map(([k, v]) => [k, v.filter((c) => c !== code)])
    );
    binds[id] = [code];
    set({ binds });
    save(get());
  },
  resetBinds: () => {
    set({ binds: DEFAULT_BINDS });
    save(get());
  },
  reset: () => {
    set({ ...DEFAULT_SETTINGS });
    save(get());
  },
}));

// Ten phim de hien thi
export function keyName(code) {
  if (!code) return "—";
  if (code.startsWith("Key")) return code.slice(3);
  if (code.startsWith("Digit")) return code.slice(5);
  const names = {
    Space: "Space",
    ShiftLeft: "Shift",
    ShiftRight: "Shift phải",
    ControlLeft: "Ctrl",
    ControlRight: "Ctrl phải",
    AltLeft: "Alt",
    AltRight: "Alt phải",
    ArrowUp: "↑",
    ArrowDown: "↓",
    ArrowLeft: "←",
    ArrowRight: "→",
    Tab: "Tab",
    CapsLock: "Caps",
    Enter: "Enter",
    Backquote: "`",
  };
  return names[code] || code;
}

export function bindLabel(id) {
  const keys = useSettings.getState().binds[id] || [];
  return keys.length ? keys.map(keyName).filter((v, i, a) => a.indexOf(v) === i).slice(0, 2).join(" / ") : "—";
}
