// Kieu anh sang tren web (hemi cao + mat troi nhe hon: cho ram/cho lom sau van thay ro mau tuong, giong ban MyUIT).
// Luu y: da tang hemi sau khi nuong (26/11), lan nuong sau can chinh PRESETS trong uit_lightbake.py cho khop.
// Phai khop PRESETS trong tools/blender/uit_lightbake.py (anh sang da nuong):
// sun = huong toi mat troi (three x,y,z) = Blender sun_dir (x,y,z) -> (x, z, -y).
// Mac dinh "sang" (mo hinh chinh nuong kieu nay); ?nang=trua / ?nang=chieu de xem thu (kem ?model=... cung kieu).
const PRESETS = {
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
export const LIGHT = PRESETS[pick] || PRESETS.sang;
