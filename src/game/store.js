import { create } from "zustand";

// Thong so mac dinh cua nhan vat (admin co the chinh)
export const DEFAULT_TUNING = { walk: 4, run: 7, jump: 4 };

function loadTuning() {
  try {
    const saved = JSON.parse(localStorage.getItem("uit3d-tuning") || "null");
    return saved ? { ...DEFAULT_TUNING, ...saved } : { ...DEFAULT_TUNING };
  } catch {
    return { ...DEFAULT_TUNING };
  }
}

function loadFlag(key) {
  try {
    return localStorage.getItem(key) === "1";
  } catch {
    return false;
  }
}

// Vi tri + huong nhan vat cap nhat moi frame (khong dung state de tranh re-render)
// yaw: goc huong mat nhan vat (rad, 0 = +Z); camYaw: huong camera dang nhin
export const playerPos = { x: 0, y: 0, z: 0, yaw: 0, camYaw: 0, running: false };

// Trang thai chung cua game
// Che do: intro (trang chu, mo hinh thu nho) -> tour (tham quan tung khu) -> explore (di lai 3D)
// ?play trong URL thi vao thang che do kham pha
const startMode = new URLSearchParams(window.location.search).has("play") ? "explore" : "intro";

export const useGame = create((set, get) => ({
  mode: startMode,
  tourStep: 0,
  tourStops: [],          // [{ key, title, subtitle, description, image, cam, target, ring }] do Intro tao
  setMode: (mode, tourStep = 0) => {
    if (mode !== "explore" && document.pointerLockElement) document.exitPointerLock();
    set({ mode, tourStep, menuOpen: false, mapOpen: false, adminOpen: false, infoOpen: false, pickerOpen: false, flying: false });
  },
  setTourStep: (tourStep) => set({ tourStep }),
  setTourStops: (tourStops) => set({ tourStops }),

  spawn: null,            // [x, y, z] diem xuat phat
  buildings: [],          // [{ name, box: THREE.Box3, center: [x,y,z] }]
  camBlockers: [],        // mesh toa nha de camera khong xuyen qua
  currentZone: null,      // ten BLD_ dang dung gan
  visited: {},            // { BLD_A: true, ... }
  camGround: [],          // mesh mat dat, chan camera khi ngo len
  setWorld: (spawn, buildings, camBlockers = [], camGround = []) => set({ spawn, buildings, camBlockers, camGround }),
  zones: [],              // [{ name: "BLD_A", obj: "ZONE_A", inv: Matrix4, box: Box3, volume }] tu Blender
  items: [],              // [{ id: "ITEM_000", quest, pos: [x,y,z] }] tu Blender
  setGameplay: (zones, items) => set({ zones, items }),
  setZone: (name) =>
    set((s) =>
      s.currentZone === name
        ? s
        : {
            currentZone: name,
            infoOpen: false, // roi khu vuc thi dong the thong tin
            visited: name ? { ...s.visited, [name]: true } : s.visited,
          }
    ),

  // ---- Giao dien ----
  menuOpen: false,        // menu Esc (tam dung)
  mapOpen: false,         // ban do lon (M)
  infoOpen: false,        // the thong tin toa nha (E)
  adminOpen: false,
  pickerOpen: false,      // bang chon nhan vat
  setUi: (patch) => set(patch),
  anyOverlay: () => {
    const s = get();
    return s.menuOpen || s.mapOpen || s.adminOpen || s.pickerOpen;
  },

  // ---- Camera / dieu khien ----
  shiftLock: false,
  setShiftLock: (shiftLock) => set({ shiftLock }),
  viewMode: "third",      // third | first
  setViewMode: (viewMode) => set({ viewMode }),
  flying: false,          // che do bay
  runToggled: false,      // trang thai chay khi dung che do bam-de-bat/tat
  setRunToggled: (runToggled) => set({ runToggled }),

  // ---- Diem danh dau tren ban do ----
  waypoint: null,         // { x, z, label }
  setWaypoint: (waypoint) => set({ waypoint }),

  // ---- Huong dan lan dau ----
  tutorialDone: loadFlag("uit3d-tutorial-done"),
  tutorialSeen: {},       // { move, jump, camera, shiftLock, interact }
  tutorialEvent: (name) =>
    set((s) => (s.tutorialDone || s.tutorialSeen[name] ? s : { tutorialSeen: { ...s.tutorialSeen, [name]: true } })),
  finishTutorial: () => {
    try {
      localStorage.setItem("uit3d-tutorial-done", "1");
    } catch {}
    set({ tutorialDone: true });
  },
  restartTutorial: () => {
    try {
      localStorage.removeItem("uit3d-tutorial-done");
    } catch {}
    set({ tutorialDone: false, tutorialSeen: {} });
  },

  // ---- Admin / test ----
  tuning: loadTuning(),
  setTuning: (patch) =>
    set((s) => {
      const tuning = { ...s.tuning, ...patch };
      try {
        localStorage.setItem("uit3d-tuning", JSON.stringify(tuning));
      } catch {}
      return { tuning };
    }),
  physicsDebug: new URLSearchParams(window.location.search).has("debug"),
  setPhysicsDebug: (physicsDebug) => set({ physicsDebug }),
  teleport: null,         // { pos: [x,y,z], t } -> Player xu ly
  teleportTo: (pos) => set({ teleport: { pos, t: performance.now() } }),
  setVisited: (visited) => set({ visited }),
}));
