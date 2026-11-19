// Thong tin tung khu vuc trong truong.
// Key = ten object trong Blender (BLD_...). Sua ten, mo ta, them anh tai day.
// image: dat file anh vao public/images/ roi ghi "/images/ten-file.jpg"
export const ZONES = {
  BLD_A: {
    title: "Tòa A",
    subtitle: "Thư viện · Hành chính",
    description: "Tòa nhà 3 tầng, nơi có thư viện trường.",
    image: null,
  },
  BLD_B: {
    title: "Tòa B",
    subtitle: "Tòa vòng cung",
    description: "Tòa nhà hình vòng cung, biểu tượng của UIT.",
    image: null,
  },
  BLD_C: {
    title: "Tòa C",
    subtitle: "Dãy phòng học",
    description: "Dãy nhà dài 3 tầng.",
    image: null,
  },
  BLD_D: { title: "Tòa D", subtitle: "", description: "", image: null },
  BLD_E: { title: "Tòa E", subtitle: "", description: "", image: null },
  BLD_CanTin: {
    title: "Căn tin",
    subtitle: "Ăn uống",
    description: "Căn tin chính của trường.",
    image: null,
  },
  BLD_CanTin2: { title: "Căn tin 2", subtitle: "Ăn uống", description: "", image: null },
  BLD_ChotBaoVe: { title: "Chốt bảo vệ", subtitle: "", description: "", image: null },
};

// Ten hien thi cho object khong co trong bang tren
export function zoneInfo(name) {
  return ZONES[name] || { title: name.replace(/^BLD_/, ""), subtitle: "", description: "", image: null };
}
