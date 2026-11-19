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
  `ecctrl.current.setMovement({...})` mỗi frame (xem `src/world/Player.jsx`), camera dùng
  `EcctrlCameraControls` và tự `moveTo` theo `currPos`.
- State: zustand (`src/game/store.js`)

## Cấu trúc

Chia theo vai trò; file mới đặt đúng nhóm, import bằng đường dẫn tương đối.

- `src/world/` (trong Canvas 3D):
  - `Campus.jsx`: tải `public/models/uit_campus.glb`, va chạm (tòa nhà khối đặc, còn lại trimesh), tường biên,
    đọc `ZONE_*`/`ITEM_*`, nhãn tên tòa, tìm điểm xuất phát. `splitScene()` dùng chung với `IntroScene`.
  - `Player.jsx`: điều khiển (bàn phím + joystick + tay cầm), camera (không xuyên tường), phát hiện khu vực.
  - `Student.jsx`: nhân vật sinh viên low-poly dựng bằng khối hình học, animation đi/chạy/nhảy
    tính bằng code theo vận tốc của ecctrl (không cần file model).
  - `Waypoint.jsx`: cột sáng đánh dấu điểm đến.
  - `IntroScene.jsx`: sa bàn trang chủ (tự xoay, bấm tòa để xem) + camera bay khi tham quan, danh sách điểm dừng.
- `src/ui/` (HTML phủ lên cảnh): `Hud.jsx` (thẻ khu vực, tiến độ, màn hình tải, joystick mobile), `Menu.jsx`,
  `MapView.jsx` (bản đồ nhỏ + lớn), `Tutorial.jsx`, `Admin.jsx` (phím Backquote, cạnh số 1), `IntroUi.jsx` (trang chủ + thẻ tham quan).
- `src/game/`: `store.js` (trạng thái), `settings.js` (cài đặt, phím), `actions.js` (phím tắt, chỉ chạy khi
  `mode === "explore"`), `sfx.js`.
- `src/data/zones.js`: tên, mô tả, ảnh từng khu vực. Key = tên object trong Blender. Thẻ tham quan dùng chung.
- `src/styles/*.css`: CSS theo phần. Thứ tự import trong `main.jsx` có ý nghĩa (`hud.css` sau `map.css`).
- `store.mode`: `intro` → `tour` → `explore`, dùng chung Canvas và mô hình (một object chỉ gắn vào một nơi,
  nên `IntroScene` và `Campus` không bao giờ mount cùng lúc). `?play` vào thẳng khám phá.
- `tools/blender/`: script Blender (xem README trong đó). Trong .blend các Text đã liên kết tới file ở đây.
- `.vscode/`: F5 chạy `npm run dev` rồi mở Chrome.

## Mô hình 3D

- Dựng trong Blender 5.3, file gốc `D:\uit3d\blender\uit_blockout.blend` (không nằm trong repo).
- Dữ liệu từ OpenStreetMap. Quy ước tên object:
  - `BLD_*` tòa nhà: `BLD_A`, `BLD_B`, `BLD_C`, `BLD_D`, `BLD_E`, `BLD_CanTin`, `BLD_CanTin2`,
    `BLD_ChotBaoVe`, `BLD_X2` (chưa rõ)
  - `DET_<tòa>_trim` / `DET_<tòa>_glass`: gờ sàn, lan can, cửa sổ (con của `BLD_*`, tạo bởi `uit_detail.py`)
  - `TREE_*` cây (collection Deco). Trên web cây không dùng va chạm trimesh, mỗi cây một CylinderCollider.
  - `GND_*` mặt đất, sân, cỏ; `PATH_*` lối đi; `REF_*` ảnh tham chiếu (không xuất ra web)
  - `ZONE_<tòa>` (empty hình hộp, collection Gameplay): vùng khu vực, đứng trong hộp = đang ở `BLD_<tòa>`
    (hoặc custom prop `zone`). `ITEM_###` (empty): điểm đặt vật phẩm, custom prop `quest`.
    Tạo bằng script `uit_gameplay.py` (chạy lại được), có thể kéo/sửa tay. Web đọc trong `Campus.jsx` → `store.zones/items`.
  - Mép `GND_Base` = biên khuôn viên, web dựng tường vô hình theo đó.
  - Dự kiến: `COL_*` collider riêng
- Chiều cao: số tầng x 3.5 m + 1 m. A, C: 3 tầng; D: 1; B: 9; E: 12 (B, E theo OSM, chưa xác nhận);
  căn tin 2; căn tin 2, chốt bảo vệ, X2: 1.
- Script dựng mô hình ở `tools/blender/` (import → cleanup → fix → detail → gameplay → export).
- Chi tiết tòa nhà + trồng cây + cổng chính: script `uit_detail.py` (chạy lại được, tự xóa chi tiết cũ).
  Kiểu riêng từng tòa trong bảng `STYLE` (A: tường trắng, mái cam, 2 vòm xanh ngọc; E: kính xanh liền,
  bảng tên trên mái). Cổng chính (`GATE_*`, collection Props) chỉnh vị trí qua biến `GATE`.
  Ảnh flycam (Kỷ yếu Sài Gòn) chỉ dùng làm mẫu dựng, không đưa lên web.
- Va chạm trên web: tòa nhà là khối đặc (mỗi tam giác mặt đáy dựng thành lăng trụ, `ConvexHullCollider`),
  không dùng trimesh vì tường mỏng làm nhân vật lọt vào trong. Mặt đất, lối đi, `GATE_*` vẫn dùng trimesh.
- Xuất ra web bằng script `uit_export.py` trong Blender → `public/models/uit_campus.glb` (nén Draco).
  Trục: Blender Z-up → glTF Y-up; 1 đơn vị = 1 m; gốc tọa độ = tâm khuôn viên.

## Lệnh

- `npm install` (lần đầu), `npm run dev` (chạy thử tại http://localhost:5173), `npm run build`
- Thêm `?debug` vào URL để xem khung va chạm.

## Việc tiếp theo (theo thứ tự)

0. Kiểm tra trang chủ + tham quan trên máy và điện thoại thật, commit, push để Vercel deploy.
1. Hệ thống nhiệm vụ: hiện vật phẩm tại các `ITEM_*` (đã có vị trí trong `store.items`), chạm là nhặt,
   danh sách nhiệm vụ trên HUD, lưu tiến độ localStorage. Nhiệm vụ mẫu: nhặt 12 vật phẩm; "khám phá đủ khu vực"
   chuyển từ bộ đếm `visited` thành nhiệm vụ.
2. Sửa lỗi + tối ưu: thử va chạm khối đặc trong game (sát tường, góc, nhảy lên mái), vệt bóng lấm tấm trên tường
   (shadow bias), FPS trên điện thoại, cảnh báo bundle > 500 kB (tách code), ảnh xem trước khi chia sẻ link (og:image).
3. Nội dung `src/data/zones.js`: mô tả cho E, D, căn tin 2, chốt bảo vệ, X2 (X2 chưa rõ là gì), ảnh ở `public/images/`.
   Thẻ tham quan lấy nội dung từ đây.
4. Minigame theo khu vực (quiz thư viện, căn tin...), easter egg.
5. Chi tiết từng tòa theo ảnh tự chụp (để ở `D:\uit3d\reference\<tòa>\`): C, B, căn tin, cổng sau, sân bóng;
   xác nhận vị trí cổng chính (`GATE`). Chưa làm tới khi có ảnh.
