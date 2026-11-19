// Thong tin tung khu vuc trong truong.
// Key = ten object trong Blender (BLD_...). Sua ten, mo ta, them anh tai day.
// image: dat file anh vao public/images/ roi ghi "/images/ten-file.jpg"
export const ZONES = {
  BLD_A: {
    title: "Tòa A",
    subtitle: "Thư viện · Hành chính",
    description: "Tòa nhà 3 tầng với hai mái vòm xanh ngọc, nơi có thư viện và Data Center của trường.",
    image: null,
  },
  BLD_B: {
    title: "Tòa B",
    subtitle: "Phòng học · Phòng máy",
    description:
      "Tòa nhà nhiều tầng hình vòng cung, tường trắng với các dải kính xanh chạy dọc thân. Có phòng học, phòng học lớn và phòng máy chất lượng cao.",
    image: null,
  },
  BLD_C: {
    title: "Tòa C",
    subtitle: "Phòng học · Phòng thực hành",
    description:
      "Dãy nhà 3 tầng mặt tiền xanh nhìn ra sân bóng, sảnh giữa có bảng tên trường và cột cờ. Có phòng học, phòng học chất lượng cao và phòng thực hành.",
    image: null,
  },
  BLD_D: { title: "Tòa D", subtitle: "", description: "", image: null },
  BLD_E: {
    title: "Tòa E",
    subtitle: "Các khoa · Hội trường",
    description:
      "Tòa cao tầng mặt kính xanh, bảng tên trường trên nóc, cầu thang xoắn bên hông. Tầng 5–9 là các khoa: Khoa học Máy tính (tầng 5, có MMLab), Kỹ thuật Máy tính, Công nghệ Phần mềm, Mạng máy tính và Truyền thông, Hệ thống Thông tin. Tòa có hội trường.",
    image: null,
  },
  BLD_CanTin: {
    title: "Nhà dịch vụ",
    subtitle: "Căn tin · Ăn uống",
    description: "Tòa 2 tầng mặt tiền cong, nhiều cửa kính. Sinh viên quen gọi là căn tin, nơi bán cơm.",
    image: null,
  },
  BLD_CanTin2: { title: "Căn tin 2", subtitle: "Ăn uống", description: "", image: null },
  BLD_ChotBaoVe: { title: "Chốt bảo vệ", subtitle: "", description: "", image: null },
};

// Ten hien thi cho object khong co trong bang tren
export function zoneInfo(name) {
  return ZONES[name] || { title: name.replace(/^BLD_/, ""), subtitle: "", description: "", image: null };
}
