// Kieu anh sang tren web (hemi cao + mat troi nhe hon: cho ram/cho lom sau van thay ro mau tuong, giong ban MyUIT).
// Luu y: da tang hemi sau khi nuong (26/11), lan nuong sau can chinh PRESETS trong uit_lightbake.py cho khop.
// Phai khop PRESETS trong tools/blender/uit_lightbake.py (anh sang da nuong):
// sun = huong toi mat troi (three x,y,z) = Blender sun_dir (x,y,z) -> (x, z, -y).
// Mac dinh "thap"; ?nang=tuoi / sang (kieu cu, khop ban nuong) / trua / chieu de xem thu.
const PRESETS = {
  // ?nang=tuoi: nang cao hon (~9h), bong ngan
  tuoi: {
    sun: [110, 130, 75],
    sunColor: "#ffefd2",
    sunIntensity: 2.15,
    hemi: ["#d9e8ff", "#d4bf9c", 1.6],
    skySun: [110, 70, 75],
    sky: { turbidity: 3, rayleigh: 0.8, mieCoefficient: 0.003, mieDirectionalG: 0.8 },
    shadowRadius: 2.5,
  },
  // mac dinh (chu du an chon): nang thap ~8h, am, bong dai; vung ram nang sang de khong bi xam
  thap: {
    sun: [140, 78, 85],
    sunColor: "#ffd9a0",
    sunIntensity: 2.6,
    hemi: ["#d3e0ff", "#d9b890", 1.65],
    skySun: [140, 38, 85],
    sky: { turbidity: 4, rayleigh: 1.1, mieCoefficient: 0.004, mieDirectionalG: 0.82 },
    shadowRadius: 2.5,
  },
  trua: {
    sun: [120, 160, 80],
    sunColor: "#ffffff",
    sunIntensity: 1.7,
    hemi: ["#ffffff", "#b5b9a8", 1.6],
    skySun: [120, 80, 60],
  },
  sang: {
    sun: [150, 80, 60],
    sunColor: "#ffdcae",
    sunIntensity: 1.9,
    hemi: ["#d6e4ff", "#b8b29c", 1.6],
    skySun: [150, 40, 60],
  },
  chieu: {
    sun: [-150, 50, 50],
    sunColor: "#ffb070",
    sunIntensity: 2.2,
    hemi: ["#c4d0ff", "#a8886a", 1.4],
    skySun: [-150, 25, 50],
  },
};

const pick = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("nang");
export const LIGHT = PRESETS[pick] || PRESETS.thap;
