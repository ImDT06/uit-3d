// Thong tin tung khu vuc trong truong.
// Key = ten object trong Blender (BLD_...). Sua ten, mo ta, them anh tai day.
// image: dat file anh vao public/images/ roi ghi "/images/ten-file.jpg"
export const ZONES = {
  BLD_A: {
    title: "Tòa A",
    subtitle: "Thư viện · Hành chính",
    description:
      "Tòa nhà 3 tầng, khối nhỏ 2 tầng phía bắc (sát góc đông bắc) là Thư viện trường. Tòa còn có khu hành chính và Data Center.",
    image: null,
  },
  BLD_B: {
    title: "Tòa B",
    subtitle: "Phòng học · Phòng máy",
    description:
      "Tòa nhà nhiều tầng hình vòng cung sơn xanh da trời, có các dải xanh đậm chạy ngang thân; mặt phía sân là những dải kính cao và bậc ngồi vòng cung. Có phòng học, phòng học lớn và phòng máy chất lượng cao.",
    image: null,
  },
  BLD_C: {
    title: "Tòa C",
    subtitle: "Phòng học · Phòng thực hành",
    description:
      "Dãy nhà 3 tầng mặt tiền xanh nhìn ra sân bóng, sảnh giữa có bảng tên trường và cột cờ. Có phòng học, phòng học chất lượng cao và phòng thực hành.",
    image: null,
  },
  BLD_D: { title: "Tòa D", subtitle: "Gần cổng B", description: "Dãy nhà một tầng tường trắng viền xanh, nằm ở cuối đường phía nam, gần cổng B.", image: null },
  BLD_E: {
    title: "Tòa E",
    subtitle: "Các khoa · Hội trường",
    description:
      "Tòa cao tầng mặt kính xanh, bảng tên trường trên nóc, cầu thang xoắn bên hông. Tầng 5–9 là các khoa: Khoa học Máy tính (tầng 5, có MMLab), Kỹ thuật Máy tính, Công nghệ Phần mềm, Mạng máy tính và Truyền thông, Hệ thống Thông tin. Tòa có hội trường.",
    image: null,
  },
  BLD_CanTin: {
    title: "Nhà ăn",
    subtitle: "Nhà dịch vụ · Cơm trưa",
    description: "Tòa 2 tầng mặt tiền cong, viền xanh, nhiều cửa kính. Nơi sinh viên ăn cơm.",
    image: null,
  },
  BLD_CanTin2: {
    title: "Căn tin",
    subtitle: "Bánh · Nước",
    description: "Dãy nhà mái tôn xanh nổi bật, bán bánh, nước và đồ ăn vặt. Đi qua đây là ra cổng B (cổng sau).",
    image: null,
  },
  BLD_ChotBaoVe: { title: "Chốt bảo vệ", subtitle: "", description: "", image: null },
};

// Nhan noi cho cac diem moc khong phai khu vuc (khong tinh vao "da kham pha x/y khu vuc").
// Key = ten object trong Blender. Ten cong theo Google Maps: cong chinh = Cong A (duong Han Thuyen), cong sau = Cong B.
export const LANDMARKS = {
  PROP_congA: "Cổng A", // cum cong lay tu ban MyUIT (chu UIT, hang co, san hoa van)
  GATE_back: "Cổng B",
  MARK_congA: "Cổng A", // diem danh dau trong ban cat tu MyUIT
  MARK_congB: "Cổng B",
};

// Ten hien thi cho object khong co trong bang tren
export function zoneInfo(name) {
  return ZONES[name] || { title: name.replace(/^BLD_/, ""), subtitle: "", description: "", image: null };
}
