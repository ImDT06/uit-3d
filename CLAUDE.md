# UIT 3D

Website khám phá khuôn viên trường UIT (ĐH Công nghệ Thông tin, ĐHQG-HCM) bằng 3D, kiểu game thế giới mở:
đi lại trong trường, mỗi khu vực có thông tin, ảnh, nhiệm vụ, minigame và easter egg.

- Deploy: https://uit-3d-alpha.vercel.app (Vercel tự build khi push lên `main`)
- Trả lời và viết comment, nội dung giao diện bằng tiếng Việt.

## Quy tắc commit

- Commit chỉ đứng tên chủ dự án (ImDT06). **Không** thêm `Co-Authored-By`, không ghi tên Claude
  hay link session vào commit message, PR, hay code.
- Commit message ngắn gọn, tiếng Việt không dấu cũng được.

## Stack

- Vite + React 19 + React Three Fiber 9 + drei
- Vật lý: @react-three/rapier
- Nhân vật: `ecctrl` v2. Lưu ý: v2 **không** tự đọc bàn phím. Input được đưa vào bằng
  `ecctrl.current.setMovement({...})` mỗi frame (xem `src/Player.jsx`), camera dùng
  `EcctrlCameraControls` và tự `moveTo` theo `currPos`.
- State: zustand (`src/store.js`)

## Cấu trúc

- `src/Campus.jsx`: tải `public/models/uit_campus.glb`, va chạm trimesh, nhãn tên tòa nhà,
  tìm điểm xuất phát không nằm trong tòa nhà.
- `src/Player.jsx`: nhân vật, bàn phím + joystick, camera, phát hiện đang ở gần tòa nào.
- `src/Hud.jsx`: giao diện (thẻ khu vực, tiến độ khám phá, hướng dẫn, màn hình tải, joystick mobile).
- `src/zones.js`: tên, mô tả, ảnh từng khu vực. Key = tên object trong Blender.
- `src/store.js`: trạng thái game.

## Mô hình 3D

- Dựng trong Blender 5.3, file gốc `D:\uit3d\blender\uit_blockout.blend` (không nằm trong repo).
- Dữ liệu từ OpenStreetMap. Quy ước tên object:
  - `BLD_*` tòa nhà: `BLD_A`, `BLD_B`, `BLD_C`, `BLD_D`, `BLD_E`, `BLD_CanTin`, `BLD_CanTin2`,
    `BLD_ChotBaoVe`, `BLD_X2` (chưa rõ)
  - `GND_*` mặt đất, sân, cỏ; `PATH_*` lối đi; `REF_*` ảnh tham chiếu (không xuất ra web)
  - Dự kiến: `COL_*` collider riêng, `ZONE_*` vùng kích hoạt nhiệm vụ
- Chiều cao: số tầng x 3.5 m + 1 m. A, C: 3 tầng; D: 1; B: 9; E: 12 (B, E theo OSM, chưa xác nhận);
  căn tin 2; căn tin 2, chốt bảo vệ, X2: 1.
- Xuất ra web bằng script `uit_export.py` trong Blender → `public/models/uit_campus.glb` (nén Draco).
  Trục: Blender Z-up → glTF Y-up; 1 đơn vị = 1 m; gốc tọa độ = tâm khuôn viên.

## Lệnh

- `npm install` (lần đầu), `npm run dev` (chạy thử tại http://localhost:5173), `npm run build`
- Thêm `?debug` vào URL để xem khung va chạm.

## Việc tiếp theo (theo thứ tự)

1. Hệ thống nhiệm vụ + một nhiệm vụ mẫu (nhặt vật phẩm rải quanh trường), danh sách nhiệm vụ trên HUD.
2. Điền nội dung + ảnh cho từng khu vực trong `zones.js` (ảnh để ở `public/images/`).
3. Nhân vật có animation (Quaternius, CC0) thay viên nhộng.
4. Minigame theo khu vực (quiz thư viện, căn tin...), easter egg.
5. Collider riêng nhẹ hơn trimesh, chi tiết mô hình (cửa sổ, mái, cây), bake ánh sáng.
