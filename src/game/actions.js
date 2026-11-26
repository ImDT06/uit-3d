import { useEffect } from "react";
import { useGame } from "./store";
import { useSettings } from "./settings";
import { unlockAudio } from "./sfx";

// Hanh dong bam mot lan, dung chung cho ban phim, tay cam va nut cam ung
export function doAction(id) {
  const g = useGame.getState();
  if (g.mode !== "explore" || g.pickerOpen) return; // trang chu / tham quan co phim rieng; dang chon nhan vat thi bo qua
  switch (id) {
    case "menu":
      if (g.mapOpen) return g.setUi({ mapOpen: false });
      if (g.adminOpen) return g.setUi({ adminOpen: false });
      return g.setUi({ menuOpen: !g.menuOpen });
    case "map":
      if (g.menuOpen) return;
      return g.setUi({ mapOpen: !g.mapOpen });
    case "shiftLock":
      if (g.anyOverlay()) return;
      if (g.viewMode === "first") return; // goc nhin thu nhat da luon khoa chuot
      g.setShiftLock(!g.shiftLock);
      return g.tutorialEvent("shiftLock");
    case "view":
      if (g.anyOverlay()) return;
      return g.setViewMode(g.viewMode === "first" ? "third" : "first");
    case "interact":
      if (g.anyOverlay() || !g.currentZone) return;
      g.setUi({ infoOpen: !g.infoOpen });
      return g.tutorialEvent("interact");
    case "fly":
      if (g.anyOverlay()) return;
      return g.setUi({ flying: !g.flying });
    case "runToggle":
      if (g.anyOverlay()) return;
      return g.setRunToggled(!g.runToggled);
  }
}

const isTyping = (t) =>
  t instanceof HTMLInputElement || t instanceof HTMLSelectElement || t instanceof HTMLTextAreaElement;

// Lang nghe phim cho cac hanh dong bam mot lan
export function useHotkeys() {
  useEffect(() => {
    // tao AudioContext ton ~0,1 s: chi lam khi da vao kham pha (chi o do moi co tieng),
    // tranh dung hinh luc bam chuyen tu trang chu sang tham quan
    const unlock = () => useGame.getState().mode === "explore" && unlockAudio();
    const onKey = (e) => {
      unlock();
      if (e.repeat || isTyping(e.target) || window.__rebinding) return;
      if (e.code === "Escape") {
        // dang khoa chuot thi trinh duyet tu nha chuot -> Player mo menu
        if (!document.pointerLockElement) doAction("menu");
        return;
      }
      const { binds, holdToRun } = useSettings.getState();
      for (const id of ["shiftLock", "view", "interact", "map", "fly"]) {
        if (binds[id]?.includes(e.code)) {
          e.preventDefault();
          doAction(id);
          return;
        }
      }
      if (!holdToRun && binds.run?.includes(e.code)) doAction("runToggle");
      if (binds.jump?.includes(e.code)) e.preventDefault(); // khong cuon trang / bam nut dang focus
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("pointerdown", unlock);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("pointerdown", unlock);
    };
  }, []);
}
