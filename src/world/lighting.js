// Kieu anh sang tren web. Phai khop PRESETS trong tools/blender/uit_lightbake.py (anh sang da nuong):
// sun = huong toi mat troi (three x,y,z) = Blender sun_dir (x,y,z) -> (x, z, -y).
// Mac dinh "sang" (mo hinh chinh nuong kieu nay); ?nang=trua / ?nang=chieu de xem thu (kem ?model=... cung kieu).
const PRESETS = {
  trua: {
    sun: [120, 160, 80],
    sunColor: "#ffffff",
    sunIntensity: 2,
    hemi: ["#ffffff", "#8a8f7a", 0.8],
    skySun: [120, 80, 60],
  },
  sang: {
    sun: [150, 80, 60],
    sunColor: "#ffdcae",
    sunIntensity: 2.3,
    hemi: ["#bcd4ff", "#86806a", 0.8],
    skySun: [150, 40, 60],
  },
  chieu: {
    sun: [-150, 50, 50],
    sunColor: "#ffb070",
    sunIntensity: 2.6,
    hemi: ["#a8b8ff", "#7a5a40", 0.7],
    skySun: [-150, 25, 50],
  },
};

const pick = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("nang");
export const LIGHT = PRESETS[pick] || PRESETS.sang;
