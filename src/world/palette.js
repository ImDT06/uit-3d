// Bang mau tuoi (dang thu) cho ban cat tu MyUIT: doi mau theo ten vat lieu, khong sua file glb.
// ?mau=goc: xem mau goc cua MyUIT de so sanh.
const CHUNG = {
  Color_E08: "#a9d18e",           // co, tan cay
  G02_Spring_Lime: "#b4eaa6",     // mai, chan tuong xanh la
  M00_Soft_Cloud: "#f7f3e8",      // loi di, via, mai bang
  M03_Pewter_Shine: "#e6e2d9",
  M05_Graphite_Haze: "#c6c5c4",
  M06_Steel_Smoke: "#aeb0b8",     // duong nhua, bac toi
  M07_Charcoal_Gleam: "#939aa6",
  UIT_main_blue: "#2fc4f0",
  UIT_glasswindow_main: "#74b9c9",
  UIT_glasswindow_supporting: "#bfe8f0",
  B03_Apricot_Glow: "#ffb48c",    // mai ngoi, san
  Color_C08: "#cfa67e",           // than cay
};
// mau rieng tung toa (nhu ban cu: B tuong xanh da troi nhat, gian lam xanh duong)
const RIENG = {
  BLD_B: { UIT_suporting_blue: "#c4e4ff", FrontColor: "#eef7fd", UIT_main_blue: "#6aaae6", UIT_glasswindow_main: "#7cc3d6" },
};

// tu sang nhe (mau cong them) cho tuong o phia ram khong bi xam
const SANG = { UIT_suporting_blue: "#4c7ea6", UIT_main_blue: "#3a6890" };

const goc = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("mau") === "goc";

export function applyPalette(scene) {
  if (goc) return;
  const done = new Set();
  scene.children.forEach((top) => {
    const rieng = RIENG[top.name];
    const clones = new Map(); // vat lieu dung chung giua cac toa -> toa co mau rieng phai dung ban sao
    top.traverse((o) => {
      if (!o.isMesh) return;
      const name = o.material.name;
      if (rieng?.[name]) {
        if (!clones.has(o.material)) {
          const m = o.material.clone();
          m.color.set(rieng[name]);
          if (SANG[name]) m.emissive.set(SANG[name]);
          clones.set(o.material, m);
        }
        o.material = clones.get(o.material);
      } else if (CHUNG[name] && !done.has(o.material)) {
        o.material.color.set(CHUNG[name]);
        done.add(o.material);
      }
    });
  });
}
